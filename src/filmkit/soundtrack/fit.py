"""Tell, before an edition's soundtrack is assembled, how much of the runtime its narration leaves
for the designed gaps, under the script's pause policy and under variants of it.

`fit` runs the assembly's own steps (`filmkit.soundtrack.assembly`) up to the gap allocation. It
binds and decodes the edition's selected recordings once, writing nothing but the assembly's
decode work files, then designs the clips and allocates the gaps under the script's pause policy
and each declared variant, each on its own copy of the decoded recordings. It prints one JSON
line per policy, the script's first as `declared`: the speech with its thought pauses, the
designed gaps before the allocation, the closing quiet and the runtime left free, negative where
it is missing, all in seconds; the gaps that the allocation gives, as the assembly receipt
records them, or None where it refuses; and the verdict, `fits` or the allocation's refusal. A
policy whose clips or gaps cannot be designed, as `assemble` would refuse them for a pause, a
level or a recording, is reported with that refusal as its verdict and no measures. After
reporting every policy it refuses, with its own refusal, a script whose policy does not fit or
cannot be designed; a variant never decides the exit.

A variants file, named below the film's root or absolutely, is a JSON object that maps each
variant's name to the voice-performance fields it replaces, whole. Every variant is validated as
the assembly validates a pause policy before anything is decoded, and a field that the pause
policy does not read is refused. The fit judges no take: abrupt endings, pauses and terms stay
with `assemble`.

`asked` gives the same reports and refusals without printing or refusing, for a caller that
decides by them, and `thought_pause_to_fit` states, for an edition that misses its runtime, the
largest thought pause of the script's declared range under which it would fit: a reading of the
film's own lever, which changes nothing.

Usage: python -m filmkit.produce fit --language zh|en [--variants <file>]
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import filmkit.repository as repository
import filmkit.soundtrack.assembly as assembly
from filmkit.captions import CaptionError
from filmkit.narration.selection import SelectionError
from filmkit.narration.spoken_units import AlignmentError
from filmkit.narration.thought_groups import RetainedUtteranceError
from filmkit.soundtrack.level import LevelError
from filmkit.soundtrack.pauses import PauseError
from filmkit.soundtrack.policy import PausePolicyError, designed_pause_policy, segment_releases
from filmkit.specification import RATE

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from filmkit.production import Edition

# The name that the script's own pause policy is reported by, and the measures of a report.
DECLARED = "declared"
MEASURES = ("speech_seconds", "gap_seconds", "closing_seconds", "free_seconds", "gaps")


class VariantsError(ValueError):
    """A variants file that cannot be read or does not map variants to their fields."""


class ReadFields(dict):
    """A voice performance that keeps the name of each field read from it."""

    def __init__(self, fields: dict) -> None:
        super().__init__(fields)
        self.read: set[str] = set()

    def get(self, key: str, default: object = None) -> object:
        self.read.add(key)
        return super().get(key, default)

    def __getitem__(self, key: str) -> object:
        self.read.add(key)
        return super().__getitem__(key)


def read_variants(path: Path) -> dict[str, dict]:
    """The variants a file below the film's root, or at an absolute path, declares: each one's
    name and the voice-performance fields it replaces."""
    path = repository.ROOT / path
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        msg = f"The variants file {path} cannot be read: {error.strerror}"
        raise VariantsError(msg) from error
    try:
        variants = json.loads(text)
    except ValueError as error:
        msg = f"The variants file {path} is not JSON: {error}"
        raise VariantsError(msg) from error
    if not isinstance(variants, dict) or not all(isinstance(v, dict) for v in variants.values()):
        msg = (
            f"The variants file {path} must map each variant's name to the voice-performance "
            "fields it replaces"
        )
        raise VariantsError(msg)
    if DECLARED in variants:
        msg = (
            f"The variants file {path} names a variant {DECLARED}, which names the script's own "
            "policy"
        )
        raise VariantsError(msg)
    return variants


def policies(script: dict, variants: dict[str, dict]) -> dict[str, tuple[dict, dict]]:
    """The script's pause policy and each variant's, each with its releases by segment, refused
    as the assembly refuses a policy, naming the variant."""
    performance, segments = script.get("voice_performance", {}), script["segments"]
    policy = designed_pause_policy(performance)
    found = {DECLARED: (policy, segment_releases(policy, segments))}
    for name, fields in variants.items():
        merged = ReadFields({**performance, **fields})
        try:
            policy = designed_pause_policy(merged)
            found[name] = (policy, segment_releases(policy, segments))
        except PausePolicyError as error:
            msg = f"Variant {name}: {error}"
            raise PausePolicyError(msg) from error
        unread = sorted(set(fields) - merged.read)
        if unread:
            msg = f"Variant {name}: the pause policy reads no {', '.join(unread)}"
            raise PausePolicyError(msg)
    return found


def report(name: str, allocation: assembly.Allocation) -> dict:
    """The line that reports how the narration fits under one policy."""
    gaps = allocation.gaps
    return {
        "policy": name,
        "speech_seconds": allocation.speech / RATE,
        "gap_seconds": sum(allocation.designed) / RATE,
        "closing_seconds": allocation.closing / RATE,
        "free_seconds": allocation.free / RATE,
        "gaps": None if gaps is None else assembly.gap_seconds(allocation.kinds, gaps),
        "verdict": allocation.refusal or "fits",
    }


def measured(
    name: str, policy: dict, releases: dict, bound: tuple[list, dict, dict, dict]
) -> tuple[dict, Exception | None]:
    """The report of one policy on its own copy of the decoded recordings, and its refusal: the
    design's, where its pauses cannot be designed, or the allocation's."""
    segments, records, alignments, decoded = bound
    samples = {key: recording.copy() for key, recording in decoded.items()}
    try:
        clips = assembly.designed_clips(segments, records, alignments, samples, policy, releases)
        allocation = assembly.allocate(segments, clips, policy)
    except (PauseError, LevelError, assembly.AssemblyError) as error:
        return {"policy": name, **dict.fromkeys(MEASURES), "verdict": str(error)}, error
    refusal = None if allocation.refusal is None else PauseError(allocation.refusal)
    return report(name, allocation), refusal


def _bound(script: dict, edition: Edition) -> tuple[list, dict, dict, dict]:
    """The edition's selected recordings, bound to the script and decoded once."""
    segments = script["segments"]
    records, alignments = assembly.bound_recordings(script, edition)
    return segments, records, alignments, assembly.decode_recordings(edition, segments, records)


def _each(
    edition: Edition, variants: dict[str, dict] | None
) -> Iterator[tuple[dict, Exception | None]]:
    """Each policy's report with its refusal as it is measured, the script's own first."""
    script = repository.read(edition.script)
    designed = policies(script, variants or {})
    bound = _bound(script, edition)
    for name, (policy, releases) in designed.items():
        yield measured(name, policy, releases, bound)


# What reading an edition's fit may refuse: the binding of the selected recordings to the
# script and the design of a policy. A caller that decides answers them as the edition's,
# and the production command takes them among its own (`filmkit.produce.REFUSALS`).
REFUSALS = (
    SelectionError,
    RetainedUtteranceError,
    AlignmentError,
    assembly.AssemblyError,
    CaptionError,
    PausePolicyError,
    PauseError,
    LevelError,
)


def asked(
    edition: Edition, variants: dict[str, dict] | None = None
) -> list[tuple[dict, Exception | None]]:
    """Each policy's report with its refusal, the script's own first; nothing is printed, and
    no policy's refusal is raised."""
    return list(_each(edition, variants))


def fit(edition: Edition, variants: dict[str, dict] | None = None) -> list[dict]:
    """Report how the edition's narration fits its runtime under the script's pause policy and
    each variant, each as it is measured; refused where the script's own policy does not fit."""
    found = []
    for line, refusal in _each(edition, variants):
        print(json.dumps(line, ensure_ascii=False), flush=True)
        found.append((line, refusal))
    if found[0][1] is not None:
        raise found[0][1]
    return [line for line, _ in found]


# The step of the thought pauses that `thought_pause_to_fit` tries, in seconds.
PAUSE_STEP = 0.01
# The name under which the seconds that must stay free are stated: in that reading's answer,
# and wherever a caller declares or records them.
RESERVE = "reserve_seconds"


def thought_pause_to_fit(edition: Edition, reserve: float = 0.0) -> dict:
    """The largest declared-range thought pause that leaves `reserve` seconds free.

    The pauses tried run in steps of 0.01 s up from the least of the script's
    `thought_pause_range`, itself the first, to the last step that is not above its declared
    thought pause, each as the script's policy with that thought pause, on the recordings
    decoded once. A shorter pause leaves more of the runtime free, so the largest pause with
    room is found by halving. A pause whose design is refused leaves no count and is taken as
    room, so the halving may end on one, or on one the allocation refuses: the pauses under it
    are then tried one by one, down to the first that fits, and a refusal between two pauses
    that fit hides none. The pause named was counted, and so was the step above it, which has
    no room or is refused. The last step has none above it: where the declared pause lies
    between two steps, the last step lies under it, and the declared pause is not counted
    here. The reading changes no file but the assembly's decode work files.

    Returns:
        The declared pause, its range and the reserve, with `fits_at_seconds`: the pause, as it
        was counted, and the seconds it leaves free; or None with the pause tried last, the
        seconds it leaves free where they were counted, and the refusal of its design or its
        allocation where there is one.
    """
    script = repository.read(edition.script)
    performance = script.get("voice_performance", {})
    policy = designed_pause_policy(performance)
    declared, (least, most) = policy["pauses"]["thought"], policy["thought_range"]
    bound, found = _bound(script, edition), {}

    def tried(step: int) -> tuple[float, float | None, str | None]:
        if step not in found:
            pause = least if step == 0 else round(least + step * PAUSE_STEP, 6)
            pauses = {**performance["designed_pauses"], "thought": pause}
            try:
                variant = designed_pause_policy({**performance, "designed_pauses": pauses})
                releases = segment_releases(variant, script["segments"])
                line, refusal = measured(str(pause), variant, releases, bound)
            except PausePolicyError as error:
                line, refusal = {"free_seconds": None, "verdict": str(error)}, error
            found[step] = (
                pause,
                line["free_seconds"],
                None if refusal is None else line["verdict"],
            )
        return found[step]

    def room(step: int) -> bool:
        free = tried(step)[1]
        return free is None or free >= reserve

    said = {"declared_seconds": declared, "range_seconds": [least, most]}
    said[RESERVE] = reserve
    low, high = 0, int((declared - least) / PAUSE_STEP + 1e-9)
    while room(low) and low < high:
        middle = (low + high + 1) // 2
        low, high = (middle, high) if room(middle) else (low, middle - 1)
    for step in range(low, -1, -1):
        pause, free, refusal = tried(step)
        if free is not None and free >= reserve and refusal is None:
            return {**said, "fits_at_seconds": pause, "free_seconds": free}
    pause, free, refusal = tried(low)
    return {
        **said,
        "fits_at_seconds": None,
        "tried_seconds": pause,
        "free_seconds": free,
        "refusal": refusal,
    }
