"""Narrate a script's segments thought by thought with the pinned reference-voice model.

Each segment is narrated as its authored thoughts under the cast's narrator, seed, temperature
and retakes. Its recording and receipt are named by the fingerprint of its request, so a
segment whose recording and receipt still match the request is reused. A recording that an
interrupted run left unresolved is refused, except an attempt that started and wrote nothing,
which is generated again. Every segment is checked before the model loads. When more than one
segment is to be generated, they are narrated in several processes at once, as many as the
host's memory gives, up to three, unless `FILMKIT_NARRATION_PROCESSES` names another count
(`filmkit.narration.processes`), and the receipt is then written from the retained recordings
as after any other run.

Usage: python -m filmkit.narration.synthesis --language CODE --script FILE --cast FILE
    --folder DIR --receipt FILE [--ids 06,07] [--dry-run]
CODE names the edition, whose language the text and the reference must be in
(`pronunciation.validate_language_reference`), whose name the speech model takes, and whose
reference recording stands at the place the code derives (`filmkit.film.places`). With
--ids only those segments are narrated, and their records replace theirs in an existing receipt.
--dry-run prints each segment's plan: its fingerprint, its recording path and whether
it would be reused, generated or refused. Paths are relative to the repository root, and a
recordings folder or a receipt outside it is refused before anything is read or written.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from mlx_audio.audio_io import write

import filmkit.child_processes as child_processes
import filmkit.repository as repository
from filmkit.narration import processes
from filmkit.narration.group_generation import generate_native_groups, load_voice_model
from filmkit.narration.pronunciation import (
    native_utterance_plan,
    pronunciation_contract,
    pronunciation_text,
    validate_language_reference,
)
from filmkit.narration.retakes import segment_take
from filmkit.narration.thought_groups import (
    RetainedUtteranceError,
    cast_speech,
    group_settings,
    parent_request,
    validate_group_inputs,
)
from filmkit.narration.voice_model import request_fingerprint

SCOPE = (
    "Synthetic narrator based only on selected synthetic reference; "
    "no real-person imitation; pronunciation/timing acceptance "
    "remains required"
)


@dataclass(frozen=True)
class Request:
    """One run's narration: the cast, the contract, the chosen segments and their places."""

    cast: dict
    # The edition's reference recording, at the place its code derives (`filmkit.film.places`).
    reference: str
    language: str
    contract: dict
    contract_path: str
    contract_sha256: str
    segments: list[dict]
    folder: Path
    receipt: Path
    merge: bool
    dry_run: bool
    # The edition's code, the script, the cast and the recordings' folder as the command named
    # them.
    sources: tuple[str, str, str, str] = ("", "", "", "")


@dataclass(frozen=True)
class Job:
    """One segment's recording: its thoughts, speech settings and the request that names it."""

    segment: dict
    plan: list[dict]
    speech: dict
    contract_path: str
    fingerprint: str
    path: Path

    @property
    def receipt(self) -> Path:
        return self.path.with_suffix(".json")

    @property
    def attempt(self) -> Path:
        return self.path.with_suffix(".request.json")


def main(argv: list[str] | None = None) -> None:
    """Narrate as the command line asks. A request to end while the narration's processes run,
    an interrupt, SIGTERM or a hang-up, ends them first and then the command, with one line
    (`filmkit.child_processes.ending`)."""
    with child_processes.ending("The narration was stopped by {request}"):
        narrate(argv)


def narrate(argv: list[str] | None = None) -> None:
    """Plan the chosen segments, narrate those to generate and write the receipt."""
    request = load_request(argv)
    jobs = speech_plan(request)
    if request.dry_run:
        for job in jobs:
            print(json.dumps(_planned(job, request), ensure_ascii=False))
        return
    # What an earlier run for this receipt left of its processes goes before anything else.
    processes.clear_work(request.receipt)
    retained = [reuse_or_refuse(job) for job in jobs]
    pending = [job for job, record in zip(jobs, retained, strict=True) if record is None]
    made_by: dict[str, int] = {}
    if len(pending) > 1 and processes.count() > 1:
        retained, made_by = narrated_in_processes(request, jobs, pending)
    model = load_voice_model() if any(record is None for record in retained) else None
    records = [
        _narrated(model, job, record, made_by.get(job.segment["id"]))
        for job, record in zip(jobs, retained, strict=True)
    ]
    write_receipt(request.receipt, records, merge=request.merge)


def narrated_in_processes(
    request: Request, jobs: list[Job], pending: list[Job]
) -> tuple[list[dict], dict[str, int]]:
    """Narrate the segments still to generate in several processes at once
    (`filmkit.narration.processes`). Returns every job's retained record, which each must then
    have, a process that ended well without its segment's recording being refused, and for each
    segment generated in this run the number of the process that generated it."""
    lengths = [(job.segment["id"], len(job.segment["spoken_text"])) for job in pending]
    shares = processes.divide(lengths, processes.count())
    for child in processes.narrate(request.sources, shares, request.receipt):
        print(json.dumps({"process": child}), flush=True)
    retained = [reuse_or_refuse(job) for job in jobs]
    missing = [job.segment["id"] for job, record in zip(jobs, retained, strict=True) if not record]
    if missing:
        msg = f"The narration processes ended without the recordings of {', '.join(missing)}"
        raise RetainedUtteranceError(msg)
    made_by = {segment: number for number, ids in enumerate(shares, 1) for segment in ids}
    return retained, made_by


def load_request(argv: list[str] | None = None) -> Request:
    """Read the command line, the script, the cast and the contract, checking them first."""
    parser = argparse.ArgumentParser(
        description="Narrate a script's segments with the reference-voice model."
    )
    parser.add_argument("--language", required=True, help="The edition's code")
    parser.add_argument("--script", required=True)
    parser.add_argument("--cast", required=True)
    parser.add_argument("--folder", required=True, help="Folder of the recordings")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--ids", default="", help="Comma-separated segment ids")
    parser.add_argument("--dry-run", action="store_true", help="Print each segment's plan only")
    options = parser.parse_args(argv)
    folder = below_root("--folder", options.folder)
    receipt = below_root("--receipt", options.receipt, file=True)
    script = repository.read(options.script)
    cast = repository.read(options.cast)
    # The film is read here, when a request is, and not as the module loads: a command that
    # stands in for the narration imports it with no film below its root.
    from filmkit.film import FILM, places

    reference = places(options.language, FILM.slug).reference
    _check_cast(cast, reference)
    segments = _chosen(script["segments"], options.ids)
    language = validate_language_reference({**script, "segments": segments}, cast, options.language)
    contract, contract_sha256 = pronunciation_contract(script, language)
    return Request(
        cast=cast,
        reference=reference,
        language=language,
        contract=contract,
        contract_path=script["pronunciation_contract"],
        contract_sha256=contract_sha256,
        segments=[
            {**segment, "spoken_text": pronunciation_text(segment, contract)}
            for segment in segments
        ],
        folder=folder,
        receipt=receipt,
        merge=bool(options.ids),
        dry_run=options.dry_run,
        sources=(options.language, options.script, options.cast, options.folder),
    )


def below_root(option: str, named: str, *, file: bool = False) -> Path:
    """A place the command names for what it writes, as a path below the film's root, refused
    unless it lies below the root: every record names its recordings from the root, and the
    work of a narration's processes is filed by the receipt's path from it.

    A place is inside when its normalised path lies below the root as the engine spells it, as
    a folder linked into the root does, or when its resolved path lies below the resolved root,
    as an absolute path does that spells the root another way (macOS's /tmp is /private/tmp).
    The root itself is no place for either, a folder none for a receipt (`file`) and a file
    none for the recordings.
    """
    root = Path(os.path.normpath(repository.ROOT))
    place = Path(os.path.normpath(root / named))
    if not place.is_relative_to(root):
        resolved, whole = place.resolve(), root.resolve()
        if not resolved.is_relative_to(whole):
            msg = f"{option} names {named}, which lies outside the film's root {root}"
            raise ValueError(msg)
        place = root / resolved.relative_to(whole)
    kind = "file" if file else "folder"
    if place == root:
        msg = f"{option} names {named!r}, which is the film's root itself, not a {kind} below it"
        raise ValueError(msg)
    if file and (named.endswith("/") or place.is_dir()):
        msg = f"{option} names {named}, which is a folder; the receipt is a file below the root"
        raise ValueError(msg)
    if not file and place.exists() and not place.is_dir():
        msg = f"{option} names {named}, which is a file; the recordings lie in a folder"
        raise ValueError(msg)
    return place


def _check_cast(cast: dict, reference: str) -> None:
    """Refuse a cast that does not condition the narrator on its exact reference: the recording
    at `reference` and the cast's transcript."""
    if cast.get("reference_mode", "icl") != "icl" or not cast.get("reference_text"):
        msg = "A cast conditions the narrator in ICL mode on its reference transcript"
        raise ValueError(msg)
    if repository.sha(reference) != cast["reference_sha256"]:
        msg = "Reference identity changed"
        raise RuntimeError(msg)
    # mlx-audio raises ICL penalties to 1.5 (read in 0.6.6); a cast may declare a lower one.
    penalty = cast.get("icl_repetition_penalty")
    if penalty is not None and (type(penalty) is not float or not 1 <= penalty < 1.5):
        msg = "A declared ICL repetition penalty must be in [1, 1.5)"
        raise ValueError(msg)


def _chosen(segments: list[dict], ids: str) -> list[dict]:
    """The segments that comma-separated ids name, or every segment without ids."""
    if not ids:
        return segments
    wanted = set(ids.split(","))
    chosen = [segment for segment in segments if segment["id"] in wanted]
    if wanted != {segment["id"] for segment in chosen}:
        msg = "Unknown section ID"
        raise ValueError(msg)
    return chosen


def speech_plan(request: Request) -> list[Job]:
    """Each chosen segment's job: its thoughts and take, and the request that names it."""
    jobs = []
    for segment in request.segments:
        thoughts = native_utterance_plan(segment, request.contract)
        seed, temperature, plan = segment_take(segment, request.cast, thoughts)
        speech = cast_speech(
            request.cast,
            reference=request.reference,
            language=request.language,
            contract_sha256=request.contract_sha256,
            seed=seed,
            temperature=temperature,
        )
        fingerprint = request_fingerprint(
            parent_request(segment["text"], segment["spoken_text"], speech, plan)
        )
        path = request.folder / f"{segment['id']}-{fingerprint[:12]}.wav"
        jobs.append(Job(segment, plan, speech, request.contract_path, fingerprint, path))
    return jobs


def reuse_or_refuse(job: Job) -> dict | None:
    """The retained record of a job whose recording is complete and still bound to it.

    Returns:
        The retained record, or None when the job is to be generated: nothing is retained,
        or its attempt started and wrote nothing.

    Raises:
        RetainedUtteranceError: A retained recording, receipt or attempt differs from the
            job's request, so its exact effect needs inspection before any replay.
    """
    if job.path.exists() and job.receipt.exists():
        record = repository.read(job.receipt)
        if record.get("reference_treatment") != job.speech["reference_treatment"]:
            msg = "Reference treatment differs from retained receipt"
            raise RetainedUtteranceError(msg)
        if (
            record.get("fingerprint") != job.fingerprint
            or record["text_sha256"] != repository.content_sha(job.segment["text"])
            or record["wav_sha256"] != repository.sha(job.path)
        ):
            msg = "Existing audio does not match retained input"
            raise RetainedUtteranceError(msg)
        validate_group_inputs(record, root=repository.ROOT, section=job.segment)
        return record
    if job.path.exists() or job.receipt.exists() or (job.attempt.exists() and not _started(job)):
        msg = "An unresolved recording exists; inspect its exact effect before replay"
        raise RetainedUtteranceError(msg)
    return None


def _started(job: Job) -> bool:
    """Whether the job's attempt started this exact request and wrote nothing else."""
    attempt = repository.read(job.attempt)
    return attempt.get("fingerprint") == job.fingerprint and attempt.get("state") == "started"


def record_segment(model, job: Job) -> dict:
    """Narrate one segment's thoughts, join and retain them, and return its record."""
    started = time.monotonic()
    segment, speech = job.segment, job.speech
    text_sha256 = repository.content_sha(segment["text"])
    repository.write(
        job.attempt,
        {
            "id": segment["id"],
            "state": "started",
            "fingerprint": job.fingerprint,
            "text_sha256": text_sha256,
            "reference_sha256": speech["reference_sha256"],
        },
    )
    audio, chunks, groups = generate_native_groups(
        model, job.plan, job.path, group_settings(job.fingerprint, speech)
    )
    if not np.isfinite(audio).all() or len(audio) <= model.sample_rate:
        msg = "Invalid generated narration"
        raise RuntimeError(msg)
    write(str(job.path), audio, model.sample_rate)
    penalty = speech.get("icl_repetition_penalty")
    record = {
        "id": segment["id"],
        "path": str(job.path.relative_to(repository.ROOT)),
        "text": segment["text"],
        "spoken_text": segment["spoken_text"],
        "text_sha256": text_sha256,
        "model": speech["model"],
        "revision": speech["revision"],
        "reference_sha256": speech["reference_sha256"],
        "reference_mode": "icl",
        "duration": len(audio) / model.sample_rate,
        "sample_rate": model.sample_rate,
        "elapsed": time.monotonic() - started,
        "wav_sha256": repository.sha(job.path),
        "scope": SCOPE,
        "fingerprint": job.fingerprint,
        "decoder": speech["decoder"],
        "stream": speech["stream"],
        "chunks": chunks,
        "seed": speech["seed"],
        "temperature": speech["temperature"],
        "reference_text_sha256": repository.content_sha(speech["reference_text"]),
        "language": speech["language"],
        "reference_audio": speech["reference_audio"],
        "pronunciation_contract": job.contract_path,
        "pronunciation_contract_sha256": speech["pronunciation_contract_sha256"],
        "reference_treatment": speech["reference_treatment"],
        "post_pitch_transform": False,
        "post_tempo_transform": False,
        **({} if penalty is None else {"icl_repetition_penalty": penalty}),
        "utterance_groups": groups,
    }
    validate_group_inputs(record, root=repository.ROOT, section=segment)
    repository.write(job.receipt, record)
    repository.write(
        job.attempt,
        {
            "id": segment["id"],
            "state": "received",
            "fingerprint": job.fingerprint,
            "wav_sha256": record["wav_sha256"],
        },
    )
    return record


def _narrated(model, job: Job, retained: dict | None, process: int | None = None) -> dict:
    """The job's retained record, or the record of its new recording, reported as it lands. A
    retained recording is reported as reused, or as generated, with the process's number, when
    one of this run's processes generated it."""
    if retained is not None:
        made = {"state": "reused"}
        if process is not None:
            made = {"state": "generated", "process": process}
        report = {"id": job.segment["id"], **made, "duration": retained["duration"]}
        print(json.dumps(report), flush=True)
        return retained
    record = record_segment(model, job)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return record


def _planned(job: Job, request: Request) -> dict:
    """A dry run's line for one job: its request, its recording and what a run would do."""
    try:
        state, refusal = ("reuse" if reuse_or_refuse(job) else "generate"), None
    except RetainedUtteranceError as error:
        state, refusal = "refuse", str(error)
    speech = job.speech
    return {
        "id": job.segment["id"],
        "state": state,
        "fingerprint": job.fingerprint,
        "path": str(job.path.relative_to(repository.ROOT)),
        "text": job.segment["text"],
        "spoken_text": job.segment["spoken_text"],
        "reference": str(repository.ROOT / speech["reference_audio"]),
        "reference_sha256": speech["reference_sha256"],
        "reference_text_sha256": repository.content_sha(speech["reference_text"]),
        "decoder": speech["decoder"],
        "stream": speech["stream"],
        "language": speech["language"],
        "pronunciation_contract": job.contract_path,
        "pronunciation_contract_sha256": speech["pronunciation_contract_sha256"],
        "seed": speech["seed"],
        "temperature": speech["temperature"],
        "folder": str(request.folder),
        "receipt": str(request.receipt),
        "utterance_plan": job.plan,
        **({} if refusal is None else {"refusal": refusal}),
    }


def write_receipt(path: Path, records: list[dict], *, merge: bool) -> None:
    """Write the run's records, merged with a receipt's other records when only some ran."""
    if merge and path.exists():
        replaced = {record["id"] for record in records}
        previous = [
            record for record in repository.read(path)["records"] if record["id"] not in replaced
        ]
        records = sorted([*previous, *records], key=lambda record: record["id"])
    repository.write(path, {"records": records})


if __name__ == "__main__":
    main()
