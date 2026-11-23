"""Tell, before an edition's soundtrack is assembled, the runtime its narration gives and how the
rounding's fraction is laid out, under the script's pause policy and under variants of it.

`fit` runs the assembly's own steps (`filmkit.soundtrack.assembly`) up to the gap allocation. It
binds and decodes the edition's selected recordings once, writing nothing but the assembly's
decode work files, then designs the clips and counts the runtime under the script's pause policy
and each declared variant, each on its own copy of the decoded recordings. It prints one JSON
line per policy, the script's first as `declared`: the speech with its thought pauses, the
designed gaps before the allocation and the closing quiet in seconds; the runtime the assembly
would give, in whole seconds; the seconds of the rounding's fraction that the gaps take beyond
their designs (`free_seconds`) and that the credits take beyond their declared length
(`credits_free_seconds`); the gaps as the assembly receipt records them; and the verdict, `fits`.
A policy whose clips or gaps cannot be designed, as `assemble` would refuse them for a pause, a
level or a recording, is reported with that refusal as its verdict and no measures. After
reporting every policy it refuses, with its own refusal, a script whose policy cannot be
designed; a variant never decides the exit, and a fraction the gaps cannot take is no refusal.

A variants file, named below the film's root or absolutely, is a JSON object that maps each
variant's name to the voice-performance fields it replaces, whole. Every variant is validated as
the assembly validates a pause policy before anything is decoded, and a field that the pause
policy does not read is refused. The fit judges no take: abrupt endings, pauses and terms stay
with `assemble`.

`asked` gives the same reports and refusals without printing or refusing, for a caller that
decides by them.

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

# The name that the script's own pause policy is reported by, the measures of a report, and the
# verdict of a policy whose clips and gaps are designed.
DECLARED = "declared"
MEASURES = (
    "speech_seconds",
    "gap_seconds",
    "closing_seconds",
    "runtime_seconds",
    "free_seconds",
    "credits_free_seconds",
    "gaps",
)
FITS = "fits"


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
    """The line that reports the runtime the narration gives under one policy, and how the
    rounding's fraction is laid out."""
    return {
        "policy": name,
        "speech_seconds": allocation.speech / RATE,
        "gap_seconds": sum(allocation.designed) / RATE,
        "closing_seconds": allocation.closing / RATE,
        "runtime_seconds": allocation.runtime,
        "free_seconds": allocation.free / RATE,
        "credits_free_seconds": allocation.credits_free / RATE,
        "gaps": assembly.gap_seconds(allocation.kinds, allocation.gaps),
        "verdict": FITS,
    }


def measured(
    name: str, policy: dict, releases: dict, bound: tuple[list, dict, dict, dict]
) -> tuple[dict, Exception | None]:
    """The report of one policy on its own copy of the decoded recordings, and the design's
    refusal where its clips or gaps cannot be designed."""
    segments, records, alignments, decoded = bound
    samples = {key: recording.copy() for key, recording in decoded.items()}
    try:
        clips = assembly.designed_clips(segments, records, alignments, samples, policy, releases)
        allocation = assembly.allocate(segments, clips, policy)
    except (PauseError, LevelError, assembly.AssemblyError) as error:
        return {"policy": name, **dict.fromkeys(MEASURES), "verdict": str(error)}, error
    return report(name, allocation), None


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
    """Report the runtime the edition's narration gives under the script's pause policy and each
    variant, each as it is measured; refused where the script's own policy cannot be designed."""
    found = []
    for line, refusal in _each(edition, variants):
        print(json.dumps(line, ensure_ascii=False), flush=True)
        found.append((line, refusal))
    if found[0][1] is not None:
        raise found[0][1]
    return [line for line, _ in found]
