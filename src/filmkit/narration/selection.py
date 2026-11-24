"""Select the narration recordings and validate their voice, text, alignment and speech.

Selection refuses a recording whose voice, text or alignment differs from what binds it, an
unmarked pause above the film's limit (`narration.flow`), a declared term said unlike its
reference occurrence (`narration.terms`) and a record of the owner's hearing whose take is not
its thought's selected take (`narration.hearings.stale`), naming each before it writes anything.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.narration.flow as flow
import filmkit.narration.hearings as hearings
import filmkit.narration.terms as terms
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.narration.pronunciation import pronunciation, pronunciation_text
from filmkit.narration.thought_groups import validate_group_inputs
from filmkit.repository import read, sha, write

if TYPE_CHECKING:
    from filmkit.production import Edition


class SelectionError(ValueError):
    """A recording or alignment differs from the script, cast or receipt it must match."""


def require_reference(reference: str, sha256: str, owner: str) -> None:
    """Refuse unless the edition's reference recording at its place, `reference`
    (`filmkit.film.places`), holds the SHA-256 that `owner`, the cast or a take, records.

    No step opens the path a take recorded: a path is where a recording stood, and its digest
    is what it is. The SHA-256 is computed once for each state of the file, so a run that checks
    every recording of a cast reads the reference once.
    """
    path = repository.ROOT / reference
    status = path.stat()
    state = (status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns, status.st_ctime_ns)
    if not _reference_matches(path, sha256, state):
        msg = f"{reference}: the narrator reference differs from {owner}'s SHA-256"
        raise SelectionError(msg)


def validate_voice_record(record: dict, cast: dict, reference: str) -> None:
    """Bind a recording to the edition's narrator reference: the recording at its place,
    `reference`, holding the cast's SHA-256, and the cast's SHA-256, transcript and treatment
    as the recording records them. The path the recording records its reference at is not
    compared: a reference moved with its bytes keeps every take."""
    require_reference(reference, cast["reference_sha256"], "the cast")
    expected = {
        "reference_sha256": cast["reference_sha256"],
        "reference_text_sha256": repository.content_sha(cast["reference_text"]),
        "reference_treatment": cast.get("reference_treatment"),
    }
    if any(record.get(key) != value for key, value in expected.items()):
        msg = f"{record['id']}: the recording's narrator reference differs from the cast"
        raise SelectionError(msg)


@functools.lru_cache(maxsize=16)
def _reference_matches(path: Path, sha256: str, _state: tuple[int, ...]) -> bool:
    return sha(path) == sha256


def validate_aligned_recording(record: dict, aligned: dict) -> None:
    """Bind word timing to the exact selected paragraph and waveform."""
    if aligned.get("id") != record["id"]:
        msg = f"Selected alignment identity differs: {record['id']}"
        raise SelectionError(msg)
    if aligned.get("wav_sha256") != record["wav_sha256"]:
        msg = f"Selected alignment waveform differs: {record['id']}"
        raise SelectionError(msg)
    expected = repository.content_sha(record["text"])
    if record.get("text_sha256") != expected or aligned.get("text_sha256") != expected:
        msg = f"Selected alignment text differs: {record['id']}"
        raise SelectionError(msg)


def select(edition: Edition) -> None:
    """Bind the edition's recordings and alignment, where its narration writes them, to its
    current script."""
    from filmkit.narration.narrate import evidence_paths

    script = read(edition.script)
    cast = read(edition.cast)
    performance = evidence_paths(edition.code)
    if not (repository.ROOT / performance["receipt"]).is_file():
        msg = f"{performance['receipt']}: the edition has no narration receipt; narrate it first"
        raise SelectionError(msg)
    candidates = {record["id"]: record for record in read(performance["receipt"])["records"]}
    contract, _ = pronunciation(edition.code)
    records = []
    for segment in script["segments"]:
        record = dict(candidates[segment["id"]])
        _check_recording(record, segment, contract)
        record["path"] = _root_relative(record["path"])
        validate_voice_record(record, cast, edition.places.reference)
        records.append(record)
    alignment = read(performance["alignment"])
    aligned = {record["id"]: record for record in alignment["records"]}
    for record in records:
        validate_aligned_recording(record, aligned[record["id"]])
    refused = speech_refusals(edition, script, records, aligned)
    heard = [record for record in FILM.narration.heard if record.edition == edition.code]
    refused += hearings.stale(heard, records)
    if refused:
        raise SelectionError("\n".join(refused))
    write(
        edition.narration_selected,
        {
            "records": records,
            "script_sha256": sha(edition.script),
            "cast_sha256": sha(edition.cast),
            "selection": "Current paragraph text; original generation retained",
            "listening_acceptance": "Separate review required",
        },
    )
    write(edition.alignment_selected, alignment)
    print(json.dumps({"selected": len(records), "seconds": sum(r["duration"] for r in records)}))


def speech_refusals(
    edition: Edition, script: dict, records: list[dict], aligned: dict[str, dict]
) -> list[str]:
    """What the selected recordings say against the film's pause limits and declared terms.

    Each segment's recording is measured with its own speech median and its aligned words.
    """
    said = narrated(script, records, aligned)
    return flow.gate(edition.code, said, FILM.narration.flow) + terms.refusals(
        edition.code, FILM.narration.terms, said
    )


def narrated(script: dict, records: list[dict], aligned: dict[str, dict]) -> list[flow.Narrated]:
    """Each segment's recording as the gates measure it: its display text and aligned words."""
    return [
        flow.Narrated(
            segment["id"],
            segment["text"],
            segment.get("utterance_groups") or [segment["text"]],
            flow.timed(aligned[record["id"]]["items"]),
            flow.Recording.read(repository.ROOT / record["path"]),
        )
        for segment, record in zip(script["segments"], records, strict=True)
    ]


def _check_recording(record: dict, segment: dict, contract: dict) -> None:
    """Check a recording's text, speech, waveform and thoughts against the current segment."""
    if record["text"] != segment["text"]:
        msg = f"Recording text differs: {segment['id']}"
        raise SelectionError(msg)
    if record.get("spoken_text", record["text"]) != pronunciation_text(segment, contract):
        msg = f"Recording spoken text differs: {segment['id']}"
        raise SelectionError(msg)
    if sha(record["path"]) != record["wav_sha256"]:
        msg = f"Recording waveform differs: {segment['id']}"
        raise SelectionError(msg)
    validate_group_inputs(record, root=repository.ROOT, section=segment)


def _root_relative(path: str) -> str:
    """A recording's path relative to the production root, which must hold it."""
    source = Path(path)
    resolved = (repository.ROOT / source).resolve()
    if (not source.is_absolute() and ".." in source.parts) or not resolved.is_relative_to(
        repository.ROOT.resolve()
    ):
        msg = "Selected recording must belong to the production root"
        raise SelectionError(msg)
    return resolved.relative_to(repository.ROOT.resolve()).as_posix()
