"""Candidate takes of a thought: their seeds, their files, their generation and their binding.

A candidate is a take of one thought's spoken text from another seed than the narration used,
synthesized through the narration's own native path and sampling (`group_generation`): the
segment's seed + k * STRIDE, k counted from FIRST. `filmkit.narration.audition` generates
candidates for the thoughts a person names and `filmkit.narration.converge` for the thoughts
a line refuses; both measure them with `filmkit.narration.judgment` and bind a chosen seed into
the cast's retakes with `bind`.

A candidate is what its request makes it: `request_sha256` is the fingerprint of the thought's
spoken text and run-on, its reference, its sampling, its seed, and the model and libraries
that synthesize it. A recording a former run left is the same candidate only under the same
fingerprint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mlx_audio.audio_io import write

import filmkit.narration.group_generation as group_generation
import filmkit.narration.judgment as judgment
import filmkit.repository as repository
from filmkit.narration.pronunciation import pronunciation_contract
from filmkit.narration.retakes import bind_proposals
from filmkit.narration.transcription import LIBRARIES
from filmkit.narration.voice_model import request_fingerprint
from filmkit.production import Edition

if TYPE_CHECKING:
    from pathlib import Path

STRIDE = 7919
# The first seed multiple a candidate is generated at.
FIRST = 11
# What of a thought's receipt decides a candidate's audio, beside its seed and run-on.
REQUEST = (
    "spoken_text",
    "reference_sha256",
    "reference_text",
    "language",
    "temperature",
    "max_tokens",
    "icl_repetition_penalty",
    "model",
    "revision",
    "decoder",
)


def seed_at(record: dict, k: int) -> int:
    """The seed of a segment's k-th candidate."""
    return record["seed"] + k * STRIDE


def file_stem(record: dict, child: dict, seed: int) -> str:
    """The file stem of a thought's candidate at a seed."""
    return f"{record['id']}-{child['index']:02d}-{seed}"


def request_sha256(child: dict, seed: int, run_on: str | None) -> str:
    """The fingerprint of what makes a candidate's audio."""
    request = {key: child.get(key) for key in REQUEST}
    return request_fingerprint({**request, "seed": seed, "run_on": run_on, "libraries": LIBRARIES})


def taken(model, path: Path, child: dict, thought: str, seed: int, run_on: str | None, bench):
    """Generate a thought's candidate at `path` and measure it.

    A candidate with a run-on is narrated on into it, retained whole beside its file and cut
    in the quiet after its thought (`judgment.run_on_measured`).
    """
    audio, _ = group_generation.synthesize(
        model,
        child["spoken_text"] + (run_on or ""),
        repository.ROOT / child["reference_audio"],
        child["reference_text"],
        child,
        seed,
    )
    rate, spoken = model.sample_rate, child["spoken_text"]
    if run_on is None:
        write(str(path), audio, rate)
        return judgment.measured(path, thought, spoken, bench)
    return judgment.run_on_measured(path, audio, rate, run_on, thought, spoken, bench)


def bind(code: str, rows: list[dict], *, dry_run: bool = False) -> tuple[list[str], list[str]]:
    """Bind proposals into the edition's cast, writing it unless a dry run.

    Returns:
        The bound "segment.index=seed" entries and the thoughts without a proposal.
    """
    edition = Edition(code)
    script, cast = repository.read(edition.script), repository.read(edition.cast)
    contract, _ = pronunciation_contract(script, edition.language)
    cast, bound, skipped = bind_proposals(script, cast, rows, contract)
    if not dry_run:
        repository.write(edition.cast, cast)
    return bound, skipped
