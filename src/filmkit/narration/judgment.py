"""Judge a take of one thought by every line the film holds for a take.

A take is one recording of one thought: the take a narration receipt holds, or a candidate
generated beside it. `measured` takes its measures once, with the functions the assembly and
the gates use: how it begins (`take_edges.opening`) and ends (`take_edges.ending`), the phrase
ends it cuts (`take_edges.phrase_ends` at the aligned phrase joins), its unmarked pauses
against the film's flow limits (`flow.take_flow`), the first vowel of every declared term
it says against the term's reference (`terms.take_terms`), and how its transcript differs
from its text, by unit and by reading (`recognition`). `judge` adds its clarity, where the film
declares a floor for the edition, and its verdict on each line:

  length   it is longer than the second under which the engine refuses a recording
           (`group_generation.too_short`);
  ending   it ends naturally, or the film's pause contract declares a release for the
           thought's join (`take_edges.kept_ending`, which the assembly asks too);
  phrase   it cuts no phrase end; a take whose alignment misses its text fails here;
  opening  a thought that opens its recording (`take_edges.opens_recording`) begins in quiet,
           as the assembly begins its clip;
  pause    it holds no unmarked pause above its limit that the film does not keep;
  terms    every declared term it says is said within its reference's bounds;
  units    its transcript holds its text: no unit differs by reading (`UNIT_LIMIT`);
  clarity  it reads at or above the film's line for a single thought
           (`review.clarity.under_its_line`, which `filmkit.preflight` asks too). A film that
           declares a floor and no line for a single thought has its takes' clarity recorded
           and not judged.

Every limit but `UNIT_LIMIT` is the film's declaration or the engine's constant in the module
named. A take is refused when a line fails, and `failed` names every failing line at once.

Two lines are measured on another basis than the gates that judge the bound take later, and a
caller that binds a take asks those gates too (`gate_refused`): a take is aligned alone with
its spoken text and its pauses are measured against its own speech, where the selection aligns
the segment with its display text; and a take's clarity is the voice-clarity measure
(`filmkit.review.clarity`) on the whole take, over the 16 frame grids a thought is measured
on, against the take's own loudness threshold, where the sound gate measures the thought from
its first word to before its last on the assembled soundtrack against the soundtrack's
threshold. `margin` therefore orders a choice.

`choose` picks among takes: of those no line refuses, the one with the widest margin, then the
quietest ending, then the lowest seed. A take's margin is its narrowest distance from a line
that has one, each as a share of that line: its clarity above the line it is judged by, or
above the edition's floor where a single thought has no line, and its unmarked pause nearest
its limit below that limit.
"""

from __future__ import annotations

import dataclasses
import math
import wave
from typing import TYPE_CHECKING

import numpy as np
from mlx_audio.audio_io import write
from mlx_audio.stt.utils import load_model

import filmkit.narration.flow as flow
import filmkit.narration.readings as readings
import filmkit.narration.selection as selection
import filmkit.narration.terms as terms
import filmkit.repository as repository
import filmkit.review.clarity as clarity
from filmkit.film import FILM
from filmkit.narration.alignment import verify_aligner
from filmkit.narration.group_generation import too_short
from filmkit.narration.narrate import ALIGNER
from filmkit.narration.pronunciation import pronunciation_contract
from filmkit.narration.recognition import (
    NO_NAMES,
    Names,
    reading_distance,
    recognition_units,
    unit_distance,
)
from filmkit.narration.retakes import thought_text
from filmkit.narration.run_on import run_on_cut, thought_bounds
from filmkit.narration.selection import validate_voice_record
from filmkit.narration.spoken_units import AlignmentError, phrase_joins
from filmkit.narration.take_edges import (
    ending,
    kept_ending,
    opening,
    opens_recording,
    phrase_ends,
)
from filmkit.narration.thought_groups import validate_group_inputs
from filmkit.narration.transcription import load_asr, transcribe
from filmkit.production import Edition
from filmkit.soundtrack.policy import designed_pause_policy, segment_releases

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

LINES = ("length", "ending", "phrase", "opening", "pause", "terms", "units", "clarity")
# The units of a take's transcript that may differ from its text by reading. A take says its
# text: by reading, a homophone, a spelling and a spacing of the recognizer's are no differences
# (`filmkit.narration.recognition`), so a unit that still differs is a word a listener hears as
# another, and no person hears a take before a convergence binds it. Measured on the stored
# first takes of a whole film on 18 November 2026: no Chinese thought of 46 and one or two
# English of 46 differ, a number written in digits and a word heard as another.
UNIT_LIMIT = 0
# What a refusal says of each line.
SAID = {
    "length": "is no longer than the second under which the engine refuses a recording",
    "ending": "ends abruptly where its join declares no release",
    "phrase": "cuts a phrase end, or its alignment misses its text",
    "opening": "opens its recording in sound",
    "pause": "holds an unmarked pause above its limit",
    "terms": "says a declared term beyond its reference's bounds",
    "units": "is heard to say other words than its text",
    "clarity": "reads under its clarity line",
    "gate-pause": "holds an unmarked pause above its limit as the selection measures its segment",
    "gate-terms": "says a declared term beyond its bounds as the selection measures its segment",
}
# What a record says of the selection's gates when the narration's alignment is not at hand.
GATE_NOT_ASKED = "not asked: no alignment of the receipt's recordings stands beside it"
NOT_OPENING = "not judged: the thought does not open its recording"
NO_FLOOR = "not judged: the film declares no clarity floor for the edition"
NO_FRAMES = "not judged: the take keeps no frame to measure"
# What `filmkit.preflight` says of thoughts under the floor in a film without a thought line.
NO_THOUGHT_LINE = clarity.NO_THOUGHT_LINE


@dataclasses.dataclass(frozen=True)
class Bench:
    """What every take of an edition is measured with.

    The recognizer, the pinned aligner with its identity, each declared term's reference vowel,
    the Chinese words a transcript is compared by (`readings.compared_words`), the film's flow
    limits, and the names a transcript's Latin units are read by (`recognition.Names`).
    """

    code: str
    language: str
    asr: object
    aligner: dict
    standards: list
    words: tuple = ()
    flow: object = None
    names: Names = NO_NAMES


@dataclasses.dataclass(frozen=True)
class Held:
    """What a film holds a take to beyond its measures.

    The releases its pause contract declares by thought join, the edition's clarity floor, the
    line no kept thought may read under, and the thoughts the film keeps between the two.
    """

    releases: dict
    floor: float | None = None
    line: float | None = None
    kept: frozenset = frozenset()


def load_aligner() -> dict:
    """Load the pinned forced aligner, which locates each take's phrase ends and run-on cut.

    Returns:
        The aligner's model and its verified identity.
    """
    folder = repository.ROOT / ALIGNER
    return {"identity": verify_aligner(folder), "model": load_model(str(folder))}


def bench(code: str, references: list, *, asr, aligner: dict, film=None) -> Bench:
    """The edition's bench, its term standards measured on the receipt's reference takes."""
    film = film or FILM
    edition = Edition(code)
    script = repository.read(edition.script)
    words = ()
    if code == "zh" and script.get("pronunciation_contract"):
        contract, _ = pronunciation_contract(script, edition.language)
        words = readings.compared_words(contract)
    measured_standards = standards(code, references, aligner, edition.language)
    names = Names(tuple(film.narration.terms))
    return Bench(
        code, edition.language, asr, aligner, measured_standards, words, film.narration.flow, names
    )


def held(code: str, script: dict, film=None) -> Held:
    """What the film holds the edition's takes to: its declared releases and clarity lines."""
    # A script that names no pause contract declares no release. The assembly refuses such a
    # film, so its takes are never joined; they can still be judged, each by its own ending.
    performance = script.get("voice_performance")
    releases = (
        segment_releases(designed_pause_policy(performance), script["segments"])
        if performance
        else {}
    )
    return Held(releases, *clarity.thought_lines(code, film=film or FILM))


def studio(
    code: str, records: list[dict], *, models: tuple | None = None, film=None
) -> tuple[Bench, Held]:
    """The bench and the held lines of an edition whose receipt holds `records`.

    The receipt's term references are read before any model loads; `models`, a recognizer and
    an aligner already loaded, are used in place of loading them again.
    """
    film = film or FILM
    references = terms.receipt_references(code, film.narration.terms, records)
    lines = held(code, repository.read(Edition(code).script), film)
    asr, aligner = models or (load_asr(), load_aligner())
    return bench(code, references, asr=asr, aligner=aligner, film=film), lines


def thoughts(records: list[dict]) -> Iterator[tuple[dict, dict]]:
    """Each thought take of a receipt's records, with its segment's record."""
    for record in records:
        for child in record.get("utterance_groups", {}).get("records", []):
            yield record, child


def holds_script(script: dict, records: list[dict]) -> None:
    """Refuse a receipt that does not hold exactly the script's thoughts, by segment and place."""
    scripted = {
        (segment["id"], index)
        for segment in script["segments"]
        for index, _ in enumerate(segment.get("utterance_groups") or [segment["text"]], 1)
    }
    held = {(record["id"], child["index"]) for record, child in thoughts(records)}
    if scripted != held:
        lacking = sorted(f"{segment}.{index}" for segment, index in scripted - held)
        beyond = sorted(f"{segment}.{index}" for segment, index in held - scripted)
        msg = "The receipt does not hold the script's thoughts: " + "; ".join(
            f"{said} {', '.join(names)}"
            for said, names in (("it lacks", lacking), ("the script lacks", beyond))
            if names
        )
        raise ValueError(msg)


def checked(script: dict, cast: dict, records: list[dict], targets: dict) -> list[tuple]:
    """The receipt's target thoughts, each checked against the script, its recording and cast.

    Returns:
        Each target's record, thought, and what `targets` holds for it.
    """
    found = [
        (record, child, targets[record["id"], child["index"]])
        for record, child in thoughts(records)
        if (record["id"], child["index"]) in targets
    ]
    if len(found) != len(targets):
        msg = "Every target must name a thought of the receipt"
        raise ValueError(msg)
    for record, child, _ in found:
        if thought_text(script, record["id"], child["index"]) != child["text"]:
            msg = (
                f"{record['id']}.{child['index']}: the receipt does not hold the "
                "current thought; narrate the segment first"
            )
            raise ValueError(msg)
    sections = {segment["id"]: segment for segment in script["segments"]}
    for record in {record["id"]: record for record, _, _ in found}.values():
        validate_group_inputs(record, root=repository.ROOT, section=sections[record["id"]])
        validate_voice_record(record, cast)
    return found


def standards(code: str, references: list, aligner: dict, language: str) -> list:
    """Each declared term's reference vowel, measured on the receipt's thought take that says it."""
    found_standards = []
    for term, forms, reference, child in references:
        path = repository.ROOT / child["path"]
        found = aligner["model"].generate(str(path), text=child["spoken_text"], language=language)
        words = terms.said_after(
            flow.timed([dataclasses.asdict(item) for item in found.items]), forms
        )
        vowel = None
        if len(words) > reference.index:
            word, after = words[reference.index]
            vowel = terms.first_vowel(flow.Recording.read(path), word["start"], word["end"], after)
        if vowel is None:
            msg = f"{code}: the {term.term} reference {reference} shows no two formants on its take"
            raise terms.TermError(msg)
        found_standards.append(terms.Standard(term, forms, reference, vowel))
    return found_standards


def measured(path: Path, thought: str, spoken_text: str, bench: Bench) -> dict:
    """A written take's waveform hash, its opening, ending and phrase ends, and what was heard.

    The take's alignment places its first item for the opening and its phrase ends, and gives
    its flow and the terms it says; its transcript is compared with its text by unit and by
    reading.
    """
    with wave.open(str(path)) as source:
        rate = source.getframerate()
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    heard = transcribe(bench.asr, path, bench.language)
    found = bench.aligner["model"].generate(str(path), text=spoken_text, language=bench.language)
    items = [dataclasses.asdict(item) for item in found.items]
    words, recording = flow.timed(items), flow.Recording.of(pcm, rate)
    return {
        "path": str(path.relative_to(repository.ROOT)),
        "wav_sha256": repository.sha(path),
        **opening(pcm, rate, items[0]["start_time"] if items else None),
        **ending(pcm, rate),
        "phrase_stops": _phrase_stops(pcm, rate, items, spoken_text),
        "heard": heard,
        "differing_units": unit_distance(recognition_units(spoken_text), recognition_units(heard)),
        "differing_units_by_reading": reading_distance(
            spoken_text, heard, bench.words, bench.names
        ),
        **flow.take_flow(bench.code, thought, spoken_text, words, recording, bench.flow),
        **terms.take_terms(bench.standards, words, recording, thought),
        "short": too_short(len(pcm), rate),
    }


def _phrase_stops(pcm, rate: int, items: list[dict], spoken_text: str):
    """The take's phrase ends that it cuts, or None when its alignment misses its text."""
    try:
        joins = phrase_joins(spoken_text, items, [spoken_text])
    except AlignmentError:
        return None
    ends = [round(items[join.left]["end_time"] * rate) for join in joins]
    return [end for end in phrase_ends(pcm, rate, ends) if end["stops"]]


def run_on_measured(
    path: Path, audio: np.ndarray, rate: int, run_on: str, thought: str, spoken_text: str, bench
) -> dict:
    """A run-on take cut in the quiet after its thought, measured as a take of the thought.

    The whole take is retained beside the cut one, and its alignment locates the thought. A
    take without heard quiet before its next words is measured whole and does not end naturally.
    """
    whole = path.with_name(f"{path.stem}-run-on.wav")
    write(str(whole), audio, rate)
    return run_on_judged(whole, path, rate, run_on, thought, spoken_text, bench)


def run_on_judged(
    whole: Path, path: Path, rate: int, run_on: str, thought: str, spoken_text: str, bench
) -> dict:
    """A retained whole run-on take, located, cut into `path` and measured."""
    with wave.open(str(whole)) as source:
        pcm = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    items = bench.aligner["model"].generate(
        str(whole), text=spoken_text + run_on, language=bench.language
    )
    taken = {
        "run_on_take": {
            "path": str(whole.relative_to(repository.ROOT)),
            "wav_sha256": repository.sha(whole),
        },
    }
    try:
        bounds = thought_bounds(
            [dataclasses.asdict(item) for item in items.items], spoken_text, run_on
        )
    except AlignmentError:
        # The thought cannot be found in the take: no cut, and its phrase ends are not known.
        take = measured(whole, thought, spoken_text, bench)
        return {**take, **taken, "natural": False, "phrase_stops": None, "run_on": None}
    cut = run_on_cut(pcm, rate, *bounds)
    taken |= {"thought_end": bounds[0], "next_start": bounds[1]}
    if cut is None:
        take = measured(whole, thought, spoken_text, bench)
        return {**take, **taken, "natural": False, "run_on": None}
    write(str(path), pcm[:cut], rate)
    return {
        **measured(path, thought, spoken_text, bench),
        **taken,
        "run_on": {"spoken_text": run_on, "cut_sample": cut},
    }


def take_clarity(path: Path, floor: float | None) -> dict | None:
    """A take's clarity over the 16 grids of a thought, or None where the film has no floor."""
    if floor is None:
        return None
    samples = np.asarray(clarity.decode(path), dtype=np.float64)
    level = clarity.threshold(samples)
    grids = [clarity.kept_frames(samples, level, phase) for phase in clarity.PHASES]
    return clarity.phased([clarity.within(frames) for frames in grids], floor)


def clarity_line(voice: dict | None, thought: str, held: Held) -> dict:
    """The clarity line of one thought's take: judged only where the film declares a line."""
    if voice is None:
        return {"passes": None, "why": NO_FLOOR}
    if held.line is None:
        return {"passes": None, "why": NO_THOUGHT_LINE, "floor_db": held.floor}
    lines = clarity.ThoughtLines(held.floor, held.line, held.kept)
    said = {"line_db": clarity.held_to(thought, lines), "floor_db": held.floor}
    if voice["cpp_db"] is None:
        return {"passes": None, "why": NO_FRAMES, **said}
    return {"passes": not clarity.under_its_line(voice["cpp_db"], thought, lines), **said}


def judge(take: dict, segment: str, index: int, held: Held) -> dict:
    """A measured take with its clarity, its verdict on every line and the lines it fails."""
    voice = take_clarity(repository.ROOT / take["path"], held.floor)
    # A run-on take that found no quiet to be cut in holds the next words: no release keeps it.
    released = index in held.releases.get(segment, {}) and take.get("run_on", True) is not None
    by_reading = take["differing_units_by_reading"]
    lines = {
        "length": {"passes": not take["short"]},
        "ending": {
            "passes": kept_ending(released, lambda: take["natural"]),
            "release_declared": released,
        },
        "phrase": {"passes": take["phrase_stops"] == []},
        "opening": {"passes": bool(take["clip_opens_quiet"])}
        if opens_recording(index)
        else {"passes": None, "why": NOT_OPENING},
        "pause": {"passes": bool(take["fluent"])},
        "terms": {"passes": bool(take["terms_pass"])},
        "units": {"passes": by_reading <= UNIT_LIMIT, "limit": UNIT_LIMIT},
        "clarity": clarity_line(voice, f"{segment}.{index}", held),
    }
    failed = [line for line in LINES if lines[line]["passes"] is False]
    return {**take, "clarity": voice, "lines": lines, "failed": failed}


def judge_thoughts(records: list[dict], bench: Bench, held: Held) -> list[dict]:
    """Every thought take of a receipt, measured and judged, in narration order."""
    rows = []
    for record, child in thoughts(records):
        name = f"{record['id']}.{child['index']}"
        take = measured(repository.ROOT / child["path"], name, child["spoken_text"], bench)
        rows.append(
            {
                "thought": name,
                "segment": record["id"],
                "index": child["index"],
                "seed": child["seed"],
                "spoken_sha256": repository.content_sha(child["spoken_text"]),
                **({"run_on_bound": child["run_on"]} if "run_on" in child else {}),
                **judge(take, record["id"], child["index"], held),
            }
        )
    return rows


def margin(take: dict) -> float:
    """A judged take's narrowest margin, as a share of its line; infinite where none has one."""
    found = []
    voice, line = take.get("clarity"), take["lines"]["clarity"]
    against = line.get("line_db", line.get("floor_db"))
    if voice is not None and voice["cpp_db"] is not None and against:
        found.append((voice["cpp_db"] - against) / against)
    pause = take.get("nearest_unmarked_pause")
    if pause is not None and pause["limit_s"]:
        found.append((pause["limit_s"] - pause["pause_s"]) / pause["limit_s"])
    return min(found, default=math.inf)


def choose(takes: list[dict]) -> dict | None:
    """The take to bind among judged takes, or None when a line refuses each."""
    accepted = [take for take in takes if not take["failed"]]
    return min(
        accepted,
        key=lambda take: (-margin(take), take["end_ratio"], take["seed"]),
        default=None,
    )


def refusal(rows: list[dict]) -> list[str]:
    """One line for each refused thought, naming every line it fails."""
    return [
        f"  {row['thought']}: " + "; ".join(f"{line}: it {SAID[line]}" for line in row["failed"])
        for row in rows
        if row["failed"]
    ]


def gate_refused(code: str, script: dict, records: list[dict], aligned: dict, film=None) -> dict:
    """The thoughts the selection's gates refuse on the narration's own alignment, by name.

    `aligned` holds each segment's alignment record by id. The pauses and the declared terms
    are judged as `filmkit.narration.selection` judges them before it binds the recordings,
    each segment aligned with its display text and measured against its own speech: the basis
    a bound take is held to, which a take judged alone cannot give.
    """
    film = film or FILM
    edition = Edition(code)
    by_id = {record["id"]: record for record in records}
    ordered = [by_id[segment["id"]] for segment in script["segments"]]
    narrated = selection.narrated(script, ordered, aligned)
    found = [boundary for item in narrated for boundary in flow.boundaries(item)]
    refused: dict[str, list[str]] = {}
    for row in flow.judge(code, found, film.narration.flow).refused:
        refused.setdefault(row["thought"], []).append("pause")
    for record in terms.records(edition.code, film.narration.terms, narrated):
        for occurrence in record["occurrences"]:
            if not occurrence["passes"]:
                refused.setdefault(occurrence["thought"], []).append("terms")
    return {name: sorted(set(lines)) for name, lines in refused.items()}


def with_gates(rows: list[dict], gate: dict | None) -> list[dict]:
    """Each judged thought with what the selection's gates refuse of it, or that none was asked."""
    for row in rows:
        row["gate"] = GATE_NOT_ASKED if gate is None else gate.get(row["thought"], [])
        if gate is not None:
            row["failed"] = row["failed"] + [f"gate-{line}" for line in row["gate"]]
    return rows
