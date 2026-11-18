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

The record, convergence.json beside the receipt, binds the receipt, the script and the cast it
was made from and states the rounds and takes asked for. It holds for each thought that was
ever refused the take it had, every candidate with its request, its measures and the lines it
failed, each choice, and the take it has now. A thought that is still refused after its
candidates is named there as not narratable as written: no line is lowered for it, and the
text or the film's declarations are its owner's to change. A thought first refused by the
last narration, when no round is left, is named as refused with no candidate tried. The
command then exits 1 and names each such thought with what each candidate failed.

A run that changes nothing is a no-op: with nothing missing and nothing refused it narrates
nothing and leaves the cast as it is, and a candidate whose recording a former run left in
build/runtime/work/convergence/<language>/ under the same request is judged again from it and
not generated again. A request to end follows the engine's rules (`filmkit.child_processes`):
the running narration is ended first, and the record, which says `running` from the run's
first effect on, names no thought as unsettled. A narration ended between two thoughts is
taken up by the next run, which narrates what the cast holds. One ended inside a thought
leaves that thought's request started and unresolved, which the engine refuses to replay; the
next run names the file and stops until it is inspected and removed. The command writes no
duration record of its own; each narration it starts writes the narration's.

Usage: python -m filmkit.narration.converge --language zh|en [--rounds 2] [--takes 3]
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time

import filmkit.child_processes as child_processes
import filmkit.narration.candidates as candidates
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


def own_receipt(code: str) -> str:
    """The receipt the convergence narrates into, which the cast must not declare elsewhere."""
    declared, own = judge.receipt_of(code), evidence_paths(code)["receipt"]
    if declared != own:
        msg = (
            f"{code}: the cast declares the receipt {declared}, and a convergence narrates "
            f"into {own}"
        )
        raise SystemExit(msg)
    return own


def narration_due(code: str) -> bool:
    """Whether the receipt lacks a recording of the cast as it stands, or a check's output."""
    edition, paths = Edition(code), evidence_paths(code)
    sources = ["--script", edition.script, "--cast", edition.cast, "--folder", paths["folder"]]
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


def entries(code: str, rows: list[dict]) -> dict[str, dict]:
    """A former record's entries for thoughts whose spoken text still stands."""
    path = Edition(code).ear_first / RECORD
    spoken = {row["thought"]: row["spoken_sha256"] for row in rows}
    former = repository.read(path)["thoughts"] if path.is_file() else []
    return {
        entry["thought"]: entry
        for entry in former
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
    for record, child, row in judgment.checked(script, cast, records, refused):
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


def write_record(code: str, found: dict, rows: list[dict], asked: dict, *, ended: bool) -> dict:
    """Write the convergence record as the thoughts stand; only an ended run names the unsettled."""
    final = {row["thought"]: row for row in rows}
    unsettled = {}
    for name, row in final.items():
        if not row["failed"] and name not in found:
            continue
        entry = entry_of(found, row)
        entry["final"] = {"seed": row["seed"], "failed": row["failed"]}
        entry["settled"] = not row["failed"]
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
    }
    repository.write(Edition(code).ear_first / RECORD, record)
    return record


def begin(code: str, asked: dict) -> None:
    """Say that a run is under way before its first effect: no thought is unsettled by it yet."""
    path = Edition(code).ear_first / RECORD
    former = repository.read(path) if path.is_file() else {"edition": code, "thoughts": []}
    repository.write(path, {**former, "state": "running", "asked": asked, "unsettled": {}})


def converge(code: str, *, rounds: int = 2, takes: int = 3) -> dict:
    """Run the rounds and the run-on round, and return the record the run ends with."""
    own_receipt(code)
    left = leftovers(code)
    if left:
        raise SystemExit(UNRESOLVED.format(code=code, files="\n".join(f"  {f}" for f in left)))
    asked = {"rounds": rounds, "takes": takes}
    begin(code, asked)
    if narration_due(code):
        narrate(code)
    session = Session(code)
    state = session.judge()
    found = entries(code, state[1])
    settled = {"first take": sum(1 for row in state[1] if not row["failed"])}
    for number in [*range(1, rounds + 1), RUN_ON]:
        if not any(row["failed"] for row in state[1]):
            break
        count = rounds if number == RUN_ON else number - 1
        ks = range(FIRST + count * takes, FIRST + (count + 1) * takes)
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
        settled[name] = sum(1 for row in state[1] if not row["failed"])
    record = write_record(code, found, state[1], asked, ended=True)
    counts = {
        "thoughts": len(state[1]),
        "settled_after": settled,
        "takes_generated": session.generated,
        "takes_found": session.reused,
        "unsettled": {name: verdict["failed"] for name, verdict in record["unsettled"].items()},
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Narrate an edition until its takes are accepted.")
    parser.add_argument("--language", choices=CODES, required=True)
    parser.add_argument("--rounds", type=int, default=2, help="Rounds of candidates")
    parser.add_argument("--takes", type=int, default=3, help="Candidates a refused thought a round")
    options = parser.parse_args(argv)
    if options.rounds < 0 or options.takes < 1:
        parser.error("--rounds is 0 or more and --takes is 1 or more")
    stopped = "The convergence was stopped by {request}; what it was running was ended with it"
    with child_processes.ending(stopped):
        record = converge(options.language, rounds=options.rounds, takes=options.takes)
    if record["unsettled"]:
        raise SystemExit(said(options.language, record))


if __name__ == "__main__":
    main()
