"""A still scan's record, as its one reader takes it.

The scan (`filmkit.picture.still_scan`) writes a record of a film or of a draft. `answer` reads
both: it returns a record only when the record has the scan's shape (every field the scan writes,
of the scan's type, each listed run inside the film), binds the files it is asked about as they
stand, and the engine where one is named, states the rules it is handed, read the whole film and
agrees with itself. `NoAnswerError` says why otherwise, and no body of a record raises anything
else. A record is not sealed: it guards against a scan that was forgotten or is stale, not against
a consistent rewriting. This module holds no rule of the scan: the engine's rules, the frames a
whole film gives and the engine's version are handed to it.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import filmkit.repository as repository

if TYPE_CHECKING:
    from pathlib import Path

RUN = ("start", "end", "speech")
MEASURES = ("fine", "coarse")
# A float's noise in the difference of two times, which a run's speech may exceed its length by.
SLACK = 1e-6


class NoAnswerError(Exception):
    """Why a record does not answer: the words that follow "record" in a refusal."""


def number(value: object) -> bool:
    """Whether a value is a finite number, as every figure of a record is."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def runs(found: object, seconds: float | None = None) -> list[dict] | None:
    """Still runs as a record lists them, or None where it lists them in no form the scan
    writes: each with its start, end and speech in finite seconds, the run inside the film of
    `seconds` where they are given, and no more speech than its length."""
    if not isinstance(found, list):
        return None
    for run in found:
        if not (isinstance(run, dict) and all(number(run.get(key)) for key in RUN)):
            return None
        start, end, speech = (run[key] for key in RUN)
        inside = 0 <= start <= end <= (end if seconds is None else seconds)
        if not (inside and 0 <= speech <= end - start + SLACK):
            return None
    return found


def listed(record: object, seconds: float | None = None) -> list[dict] | None:
    """The fine measure's still runs as a record lists them (`runs`)."""
    fine = record.get("fine") if isinstance(record, dict) else None
    return runs(fine.get("runs"), seconds) if isinstance(fine, dict) else None


def at_limit(found: list[dict], limit: float) -> list[dict]:
    """The runs that carry at least `limit` seconds of speech."""
    return [run for run in found if run["speech"] >= limit]


def shaped(record: object, subjects: tuple[str, ...], seconds: float) -> bool:
    """Whether a record has the scan's shape: every field the scan writes, of the scan's type."""
    if not isinstance(record, dict):
        return False
    bound = all(
        isinstance(record.get(name), dict)
        and all(isinstance(record[name].get(key), str) for key in ("path", "sha256"))
        for name in subjects
    )
    measures = all(
        isinstance(record.get(name), dict)
        and isinstance(record[name].get("rule"), str)
        and runs(record[name].get("runs"), seconds) is not None
        for name in MEASURES
    )
    counts = all(count(record.get(key)) for key in ("fps", "frames", "phases"))
    frames = record.get("phase_frames")
    stated = isinstance(record.get("rules"), dict) and number(record.get("limit_seconds"))
    verdict = runs(record.get("over_limit"), seconds) is not None
    return (
        bound
        and measures
        and counts
        and isinstance(frames, list)
        and all(count(read) for read in frames)
        and stated
        and verdict
        and number(record.get("longest_fine_speech"))
    )


def stale_subjects(record: dict, current: dict[str, Path]) -> list[str]:
    """The names among `current` whose file a record of the scan's shape does not bind as it now
    stands. A record binds a file when it holds, under the file's name here, the SHA-256 of the
    file's bytes."""
    return [
        name for name, path in current.items() if record[name]["sha256"] != repository.sha(path)
    ]


def contradictions(record: dict, frames: list[int]) -> list[str]:
    """Where a record of the scan's shape that states the engine's rules disagrees with itself.

    A record states some things twice, for the readers that take one field: its limit, its rate,
    both rules' wording and the number of its phases beside its `rules`; its verdict as the runs
    it lists, its runs at the limit and its longest speech; and the frames it read, which must be
    the whole film's. The pairs must be equal."""
    rules, found = record["rules"], record["fine"]["runs"]
    said = {
        "its limit": record["limit_seconds"] == rules["limit_seconds"],
        "its rate": record["fps"] == rules["fps"],
        "its rules' wording": [record[name]["rule"] for name in MEASURES]
        == [rules[name] for name in MEASURES],
        "its phases": record["phases"] == len(rules["phases"]),
        "its runs at the limit": record["over_limit"] == at_limit(found, rules["limit_seconds"]),
        "its longest speech": record["longest_fine_speech"]
        == max((run["speech"] for run in found), default=0),
        "the frames it read": record["phase_frames"] == frames and record["frames"] in frames,
    }
    return [name for name, agrees in said.items() if not agrees]


def answer(
    path: Path,
    subjects: dict[str, Path],
    rules: dict,
    frames: list[int],
    engine: str | None = None,
) -> dict:
    """The record at `path`, where it answers for `subjects` as they stand.

    `NoAnswerError` says why it does not: it "cannot be read" (no JSON the reader can hold, or
    not the scan's shape for a film of these frames); it "binds another" file, or engine where
    `engine` names one; it "states other rules than the engine's", with both limits where the
    record's is a number other than the engine's; or it "cannot be trusted", naming where it
    contradicts itself (`contradictions`). A bound file that is missing raises
    `FileNotFoundError`, which is the caller's to name.
    """
    fields = (*subjects, *(("engine_version",) if engine is not None else ()))
    record = repository.read_entry(path, fields)
    if record is None or not shaped(record, tuple(subjects), max(frames) / rules["fps"]):
        raise NoAnswerError("cannot be read")
    stale = stale_subjects(record, subjects)
    if engine is not None and record["engine_version"] != engine:
        stale.append("engine")
    if stale:
        raise NoAnswerError(f"binds another {', '.join(stale)}")
    if record["rules"] != rules:
        written, ours = record["rules"].get("limit_seconds"), rules["limit_seconds"]
        limits = f": a limit of {written} s where the engine's is {ours} s"
        other = limits if number(written) and written != ours else ""
        raise NoAnswerError(f"states other rules than the engine's{other}")
    disagree = contradictions(record, frames)
    if disagree:
        reason = f"cannot be trusted, as it contradicts itself in {' and '.join(disagree)}"
        raise NoAnswerError(reason)
    return record
