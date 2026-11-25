"""Narrate an edition until every thought holds a take that the film's lines accept.

The command needs no targets file, no phrase and no seed from a person:

1. It narrates what is missing (`filmkit.narration.narrate`): nothing, when the receipt holds
   every segment's recording for the cast as it stands and both checks' outputs are of it.
2. It judges every thought's take by every line the film holds for a take
   (`filmkit.narration.judgment`), and asks the selection's own gates about the narration as
   they will measure it (`filmkit.narration.judge`).
3. For each refused thought it generates --takes candidates a round, at the audition's seeds
   (`filmkit.narration.candidates`: the segment's seed + k * 7919, k counted on from 11 across
   the rounds), judges each by the same lines, and chooses among those no line refuses the
   one with the widest margin (`judgment.choose`). It binds the choices into the cast's
   retakes as `audition apply` does, narrates again and judges again. A segment's request
   names its thoughts' seeds, so that narration generates each segment that holds a retaken
   thought whole and reuses every other; a thought the gates then refuse goes to the next
   round. It does so for --rounds rounds, or until none is refused.
4. For what is still refused it tries one round of run-on takes: the thought narrated on into
   the thought that follows it and cut in the quiet between them (`narration.run_on`).
5. When no thought is refused or waits for the ear it counts the settled edition by the
   assembly's own count (`filmkit.narration.fitting`): it selects the recordings and counts them
   as the node `select` and `python -m filmkit.soundtrack.fit` do, replaces no take and changes
   no pause policy. An edition lasts as long as its narration, so the count states its runtime
   and never misses one.

A thought whose take reads under its clarity line, with no hearing of that take that settles it,
is for the owner's ear (`judgment.for_the_ear`): it is refused by no line, so it gets no candidate,
and it is not settled; the convergence names it with its take's path, audio SHA-256, clarity and
line, records it apart (`for_the_ear`) and exits 1 while it waits.

The record, convergence.json beside the receipt, binds the receipt, the script and the cast it
was made from and states the rounds and takes asked for. It holds for each thought that was
ever refused the take it had, every candidate with its request, its measures and the lines it
failed, each choice, and the take it has now. A thought that is still refused after its
candidates is named there as not narratable as written: no line is lowered for it, and the
text or the film's declarations are its owner's to change. A thought first refused by the
last narration, when no round is left, is named as refused with no candidate tried. The
command then exits 1 and names each such thought with what each candidate failed. The record
of an ended run holds its `fit`: the runtime the count gives and the seconds of the rounding's
fraction that the gaps and the credits take, or why the count was not asked. The command also
exits 1, with one line, for a settled edition that the selection or the assembly refuses, with
that reason. A fault of the count that is no refusal keeps its traceback, after the record is
ended with it. A cast that declares `runtime_fit`, which nothing reads, is refused with the
film as the engine loads (`filmkit.withdrawn`), before the command runs.

A run that changes nothing is a no-op: with nothing missing and nothing refused it narrates
nothing and leaves the cast as it is, and a candidate whose recording a former run left in
build/runtime/work/convergence/<language>/ under the same request is judged again from it and
not generated again. A request to end follows the engine's rules (`filmkit.child_processes`):
the running narration is ended first, and the record, which says `running` from the run's
first effect on, names no thought as unsettled. A narration ended between two thoughts is
taken up by the next run, which narrates what the cast holds. One ended inside a thought
leaves that thought's request started and unresolved, which the engine refuses to replay; the
next run names the file and stops until it is inspected and removed. When it ends, the record
states the run's measurement (`run`, from `filmkit.graph.runs`): its start, its seconds, the host's
load at both ends, and the seconds of its narrations, its judgments, its candidates and its count
of the runtime as phases, and that it completed only where the edition ends settled and is not
refused. A run that is refused before its first effect writes nothing (`admitted`). Each
narration it starts writes the narration's own run record.

Usage: python -m filmkit.narration.converge --language <code> [--rounds 2] [--takes 3]
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time

import filmkit.child_processes as child_processes
import filmkit.graph.runs as seam
import filmkit.narration.candidates as candidates
import filmkit.narration.fitting as fitting
import filmkit.narration.group_generation as group_generation
import filmkit.narration.judge as judge
import filmkit.narration.judgment as judgment
import filmkit.narration.synthesis as synthesis
import filmkit.repository as repository
from filmkit.narration.candidates import FIRST, STRIDE, bind
from filmkit.narration.narrate import evidence_paths
from filmkit.narration.run_on import following_spoken_text
from filmkit.production import CODES, Edition

WORK = "build/runtime/work/convergence"
RECORD = "convergence.json"
# The command's name in its measurement, which names no node of the table, and the record's key
# that states the measurement.
COMMAND, MEASURED = "converge", "run"
RUN_ON = "run-on"
NOT_NARRATABLE = "not narratable as written"
UNTRIED = "refused by the last narration, with no round left: no candidate was tried"
CARRIED = ("run_on", "thought_end", "next_start", "run_on_take")
UNRESOLVED = (
    "{code}: a narration was ended inside a thought and left its request started, which the "
    "engine refuses to replay (Unresolved native utterance; inspect before replay). Inspect "
    "and remove what it left, then run the command again:\n{files}"
)

__all__ = ["FIRST", "STRIDE", "converge", "main"]


def narration_due(code: str) -> bool:
    """Whether the receipt lacks a recording of the cast as it stands, or a check's output."""
    edition, paths = Edition(code), evidence_paths(code)
    sources = ["--language", code, "--script", edition.script, "--cast", edition.cast]
    sources += ["--folder", paths["folder"]]
    jobs = synthesis.speech_plan(synthesis.load_request([*sources, "--receipt", paths["receipt"]]))
    if any(synthesis.reuse_or_refuse(job) is None for job in jobs):
        return True
    if not all(
        (repository.ROOT / paths[name]).is_file() for name in ("receipt", "alignment", "asr")
    ):
        return True
    records = repository.read(paths["receipt"])["records"]
    if {record["id"]: record.get("fingerprint") for record in records} != {
        job.segment["id"]: job.fingerprint for job in jobs
    }:
        return True
    # Each check's output must be of the receipt's recordings: a narration ended after its
    # synthesis leaves the outputs of the recordings before.
    recorded = {record["id"]: record["wav_sha256"] for record in records}
    return any(
        {row["id"]: row.get("wav_sha256") for row in repository.read(paths[name])["records"]}
        != recorded
        for name in ("alignment", "asr")
    )


def leftovers(code: str) -> list[str]:
    """The thought requests a narration left started: asked for and never received.

    A thought's request stands in its segment's own folder of recordings. A segment's attempt,
    beside that folder, may stand started: the engine takes such a segment up again.
    """
    folder = repository.ROOT / evidence_paths(code)["folder"]
    return sorted(
        repository.relative(request)
        for request in folder.glob("*/*.request.json")
        if repository.read(request).get("state") == "started"
    )


def narrate(code: str) -> None:
    """Narrate the edition as a child: it generates what the receipt lacks and checks it.

    The narration waits for its synthesis, which waits for its model processes, so a request
    to end gives the narration twice the time it may itself wait before anything is killed.
    """
    started = time.monotonic()
    command = [sys.executable, "-B", "-m", "filmkit.narration.narrate", "--language", code]
    with seam.phase("narration"):
        child_processes.run(command, cwd=repository.ROOT, seconds=4 * child_processes.STOP_SECONDS)
    report(code, step="narration", seconds=round(time.monotonic() - started, 1))


def report(code: str, **said: object) -> None:
    print(json.dumps({"edition": code, **said}, ensure_ascii=False), flush=True)


class Session:
    """One run's models and counts: each model loaded when needed and let go before a narration."""

    def __init__(self, code: str) -> None:
        self.code, self.voice, self.models = code, None, None
        self.generated = self.reused = 0
        self.folder = repository.ROOT / WORK / code

    def release(self) -> None:
        """Let every model go: a narration starts processes that each load their own."""
        self.voice = self.models = None
        gc.collect()

    def judge(self) -> tuple[list[dict], list[dict], judgment.Bench, judgment.Held]:
        """Judge the current receipt's thoughts; the term standards follow its takes."""
        started = time.monotonic()
        with seam.phase("judgment"):
            records = judge.current(self.code)
            bench, held = judgment.studio(self.code, records, models=self.models)
            self.models = (bench.asr, bench.aligner)
            rows = judge.judged(self.code, records, bench, held)["thoughts"]
        refused = sum(1 for row in rows if row["failed"])
        report(
            self.code, step="judge", refused=refused, seconds=round(time.monotonic() - started, 1)
        )
        return records, rows, bench, held

    def candidate(self, record, child, k, run_on, known, bench, held) -> dict:
        """One candidate of a thought at the k-th seed, generated or found, and judged."""
        seed = candidates.seed_at(record, k)
        name = candidates.file_stem(record, child, seed) + ("-on" if run_on else "")
        path, thought = self.folder / f"{name}.wav", f"{record['id']}.{child['index']}"
        kind = "plain" if run_on is None else RUN_ON
        request = candidates.request_sha256(child, seed, run_on)
        stored = known.get((seed, kind))
        if stored and stored.get("request_sha256") != request:
            stored = None
        # A run-on take that found no cut was measured whole, and its record names that file.
        kept = stored and repository.ROOT / stored["path"]
        if kept and kept.is_file() and repository.sha(kept) == stored["wav_sha256"]:
            self.reused += 1
            take = {
                **judgment.measured(kept, thought, child["spoken_text"], bench),
                **{key: stored[key] for key in CARRIED if key in stored},
            }
        else:
            self.voice = self.voice or group_generation.load_voice_model()
            self.folder.mkdir(parents=True, exist_ok=True)
            take = candidates.taken(self.voice, path, child, thought, seed, run_on, bench)
            self.generated += 1
        if run_on is not None and take["run_on"] is None:
            take["natural"] = False
        row = {"seed": seed, "k": k, "kind": kind, "request_sha256": request}
        row |= judgment.judge(take, record["id"], child["index"], held)
        spread = judgment.margin(row)
        row["margin"] = None if spread == float("inf") else round(spread, 4)
        report(self.code, thought=thought, seed=seed, kind=kind, failed=row["failed"])
        return row


def settled(row: dict) -> bool:
    """Whether a judged thought is settled: no line refuses it and it waits for no ear."""
    return not row["failed"] and not judgment.for_the_ear(row)


def entries(former: dict, rows: list[dict]) -> dict[str, dict]:
    """The entries of the record that a former run left (`left`, its one reader) for thoughts
    whose spoken text still stands. An entry that lacks its thought or its spoken text, or
    names its thought by a list or an object, raises `KeyError` or `TypeError`, which `left`
    asks for before a run opens."""
    spoken = {row["thought"]: row["spoken_sha256"] for row in rows}
    return {
        entry["thought"]: entry
        for entry in former["thoughts"]
        if spoken.get(entry["thought"]) == entry["spoken_sha256"]
    }


def entry_of(found: dict, row: dict) -> dict:
    """The record's entry of a refused thought, begun with the take it had when first refused."""
    first = {"seed": row["seed"], "failed": row["failed"]}
    if "run_on_bound" in row:
        first["run_on"] = row["run_on_bound"]
    return found.setdefault(
        row["thought"],
        {
            "thought": row["thought"],
            "spoken_sha256": row["spoken_sha256"],
            "first": first,
            "candidates": [],
            "chosen": [],
        },
    )


def round_of(session, state, found, number, ks, *, run_on: bool) -> list[dict]:
    """Candidates for every refused thought in one round, and the proposals of its choices."""
    records, rows, bench, held = state
    refused = {(row["segment"], row["index"]): row for row in rows if row["failed"]}
    edition = Edition(session.code)
    script, cast = repository.read(edition.script), repository.read(edition.cast)
    proposals = []
    checked = judgment.checked(script, cast, records, refused, edition.places.reference)
    for record, child, row in checked:
        entry = entry_of(found, row)
        following = None
        if run_on:
            try:
                following = following_spoken_text(records, record["id"], child["index"])
            except ValueError as error:
                entry["no_run_on"] = str(error)
                continue
        known = {(take["seed"], take["kind"]): take for take in entry["candidates"]}
        takes = [
            session.candidate(record, child, k, following, known, bench, held)
            for k in ks
            if candidates.seed_at(record, k) != child["seed"]
        ]
        fresh = {(take["seed"], take["kind"]) for take in takes}
        entry["candidates"] = [
            take for take in entry["candidates"] if (take["seed"], take["kind"]) not in fresh
        ] + [{"round": number, **take} for take in takes]
        choice = judgment.choose(takes)
        if choice is None:
            continue
        # Every choice that was bound stays in the record, a former run's too.
        chosen = {"round": number, "seed": choice["seed"], "kind": choice["kind"]}
        if chosen not in entry["chosen"]:
            entry["chosen"].append(chosen)
        proposals.append(
            {
                "segment": record["id"],
                "index": child["index"],
                "text": child["text"],
                "spoken_text": child["spoken_text"],
                "proposed_seed": choice["seed"],
                **({"proposed_run_on": choice["run_on"]} if run_on else {}),
            }
        )
    return proposals


def write_record(
    code: str, found: dict, rows: list[dict], asked: dict, *, ended: bool, fit: dict | None = None
) -> dict:
    """Write the convergence record as the thoughts stand; only an ended run names the unsettled
    and holds `fit`, what the count said of the settled edition."""
    final = {row["thought"]: row for row in rows}
    unsettled = {}
    for name, row in final.items():
        if not row["failed"] and name not in found:
            continue
        entry = entry_of(found, row)
        entry["final"] = {"seed": row["seed"], "failed": row["failed"]}
        entry["settled"] = settled(row)
        if row["failed"] and ended:
            tried = entry["candidates"] or "no_run_on" in entry
            unsettled[name] = {
                "failed": row["failed"],
                "verdict": NOT_NARRATABLE if tried else UNTRIED,
            }
    record = {
        "edition": code,
        "state": "ended" if ended else "running",
        "asked": asked,
        "bound": judge.bound(code),
        "thoughts": [found[name] for name in final if name in found],
        "unsettled": unsettled,
        "for_the_ear": judgment.ear(rows),
        **({"fit": fit} if fit else {}),
    }
    repository.write(Edition(code).ear_first / RECORD, record)
    return record


def left(code: str) -> dict:
    """The record that a former run left, or the one a first run begins from: the record's one
    reader. Refused in one line where what stands in the record's place, a folder included, is
    no JSON object with its thoughts, or holds thoughts that the run cannot take up.

    What the run can take up is asked of the run's own reader of those thoughts (`entries`),
    with no thought of this run to compare: it reads every entry's thought and spoken text all
    the same, so this check states no shape of an entry beside the reader.
    """
    path = Edition(code).ear_first / RECORD
    if not path.exists():
        return {"edition": code, "thoughts": []}
    former = repository.read_entry(path, ("thoughts",))
    taken = former is not None
    if taken:
        try:
            entries(former, [])
        except (KeyError, TypeError):
            taken = False
    if not taken:
        msg = (
            f"{code}: the record that a former run left cannot be read: "
            f"{repository.relative(path)} is no JSON object whose thoughts each name their "
            "thought and its spoken text; inspect and remove it, then run the command again"
        )
        raise SystemExit(msg)
    return former


def begin(code: str, asked: dict, former: dict) -> None:
    """Say that a run is under way before its first effect: no thought is unsettled by it yet.
    `former` is the record that a former run left (`left`)."""
    # A former run's fit and measurement are not this run's: nothing of the count is kept
    # between runs.
    former.pop("fit", None)
    former.pop(MEASURED, None)
    record = {**former, "state": "running", "asked": asked, "unsettled": {}}
    repository.write(Edition(code).ear_first / RECORD, record)


def admitted(code: str) -> dict:
    """What refuses a run before its first effect, each in its own words; then what a run takes
    from these checks: the record that a former run left. The script's pause policy can be
    read (`fitting.declared`), the pronunciations the edition's Latin units are heard by are in
    place (`judgment.pronunciations`), no narration left a request started, and the former
    record can be read (`left`).

    The command asks this before it opens its run (`main`), so that such a refusal writes
    nothing and leaves the record of the convergence that narrated the standing build.
    """
    fitting.declared(code)
    judgment.pronunciations(code)
    started = leftovers(code)
    if started:
        files = "\n".join(f"  {file}" for file in started)
        raise SystemExit(UNRESOLVED.format(code=code, files=files))
    return left(code)


def converge(code: str, former: dict, *, rounds: int = 2, takes: int = 3) -> dict:
    """Run the rounds and the run-on round, ask the count, and return the record the run ends
    with. `former` is what the checks gave the caller (`admitted`)."""
    asked = {"rounds": rounds, "takes": takes}
    begin(code, asked, former)
    if narration_due(code):
        narrate(code)
    session = Session(code)
    state = session.judge()
    found = entries(former, state[1])
    counted = {"first take": sum(1 for row in state[1] if settled(row))}
    for number in [*range(1, rounds + 1), RUN_ON]:
        if not any(row["failed"] for row in state[1]):
            break
        count = rounds if number == RUN_ON else number - 1
        ks = range(FIRST + count * takes, FIRST + (count + 1) * takes)
        with seam.phase("candidates"):
            proposals = round_of(session, state, found, number, ks, run_on=number == RUN_ON)
        # The candidates are recorded before a narration that a request to end may cut short.
        write_record(code, found, state[1], asked, ended=False)
        if proposals:
            bound, _ = bind(code, proposals)
            report(code, step="bind", round=number, bound=bound)
            session.release()
            narrate(code)
            state = session.judge()
        name = RUN_ON if number == RUN_ON else f"round {number}"
        counted[name] = sum(1 for row in state[1] if settled(row))
    if any(row["failed"] for row in state[1]):
        fit = fitting.not_asked(fitting.UNSETTLED)
    elif judgment.ear(state[1]):
        fit = fitting.not_asked(fitting.FOR_THE_EAR)
    else:
        try:
            with seam.phase("count"):
                fit = fitting.read(code)
        except Exception as fault:
            # A fault of the count is no refusal and keeps its traceback; the record of the
            # thoughts, which are settled, is ended first.
            write_record(code, found, state[1], asked, ended=True, fit=fitting.failed(fault))
            raise
    record = write_record(code, found, state[1], asked, ended=True, fit=fit)
    counts = {
        "thoughts": len(state[1]),
        "settled_after": counted,
        "takes_generated": session.generated,
        "takes_found": session.reused,
        "unsettled": {name: verdict["failed"] for name, verdict in record["unsettled"].items()},
        "for_the_ear": list(record["for_the_ear"]),
        "fit": fitting.summary(fit),
        **{key: fit[key] for key in fitting.COUNTED if key in fit},
    }
    report(code, step="converge", rounds=rounds, takes=takes, **counts)
    return record


def said(code: str, record: dict) -> str:
    """What an unsettled edition is refused with: each thought, and what each candidate failed."""
    found = {entry["thought"]: entry for entry in record["thoughts"]}
    lines = [f"{code}: {len(record['unsettled'])} thoughts are unsettled"]
    for name, verdict in record["unsettled"].items():
        entry = found.get(name, {})
        lines.append(
            f"  {name}: {verdict['verdict']}; its take fails {', '.join(verdict['failed'])}"
        )
        lines += [
            f"    {take['kind']} candidate {take['seed']}: "
            + (f"fails {', '.join(take['failed'])}" if take["failed"] else "accepted when judged")
            for take in entry.get("candidates", [])
        ]
        if "no_run_on" in entry:
            lines.append(f"    no run-on candidate: {entry['no_run_on']}")
    return "\n".join(lines)


def stamp(code: str, record: dict, measured: dict) -> None:
    """Write the record the run ended with again, stating the run's measurement: its start, its
    seconds, the load at both ends, its phases and whether it completed."""
    kept = ("started_at", "seconds", seam.LOAD, "completed", "phases")
    record = {**record, MEASURED: {key: measured[key] for key in kept}}
    repository.write(Edition(code).ear_first / RECORD, record)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Narrate an edition until its takes are accepted.")
    parser.add_argument("--language", choices=CODES, required=True)
    parser.add_argument("--rounds", type=int, default=2, help="Rounds of candidates")
    parser.add_argument("--takes", type=int, default=3, help="Candidates a refused thought a round")
    options = parser.parse_args(argv)
    if options.rounds < 0 or options.takes < 1:
        parser.error("--rounds is 0 or more and --takes is 1 or more")
    code = options.language
    stopped = "The convergence was stopped by {request}; what it was running was ended with it"
    # The run is measured inside the block that answers a request to end; an edition that ends
    # unsettled or refused is a run that did not complete, and a run that a request or a fault
    # ends states no measurement.
    with child_processes.ending(stopped):
        former = admitted(code)
        with seam.run(code, COMMAND) as run:
            record = converge(code, former, rounds=options.rounds, takes=options.takes)
            unsettled = record["unsettled"]
            refused = said(code, record) if unsettled else fitting.said(code, record["fit"])
            # The thoughts the last judgment judged, which it records beside the receipt.
            judged = len(repository.read(Edition(code).ear_first / judge.RECORD)["thoughts"])
            ear = judgment.waiting(code, record["for_the_ear"], judged)
            refused = "\n".join(filter(None, [refused, *ear]))
            if refused:
                run.fail()
            stamp(code, record, run.measured(completed=not refused))
    if refused:
        raise SystemExit(refused)


if __name__ == "__main__":
    main()
