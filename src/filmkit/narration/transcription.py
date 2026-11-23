"""Transcribe a narration receipt's recordings with the pinned, supplied ASR model.

Each recording's unit error rate is the edit distance between the recognition units of its
text and of its transcript over the text's unit count. Recognition is a proxy for
pronunciation, not certification or listening. Each recording's transcript is cached under its
waveform, the language and the recognizer's identity: its hub repository and revision, its
weights' SHA-256 and the versions of the libraries that run it, `mlx-audio` and `mlx`. Every
run checks the supplied recognizer against its pins first, which reads the weights, so a run
that reuses every transcript still proves that the recognizer its cache names is the one
supplied; the model is loaded only when a recording misses its cache. A cached entry that
cannot be read as a transcript is a miss: the recording is transcribed again and the entry
replaced. The error rate is taken anew from the text.

Usage: python -m filmkit.narration.transcription
    --receipt FILE --output FILE --language NAME
NAME is the edition's language as the speech models take it, its declaration's `english_name`
(`filmkit.languages`).
Paths are relative to the repository root. Every recording must still match the
SHA-256, text and language its receipt records.
"""

import argparse
import json
from importlib.metadata import version
from pathlib import Path

from mlx_audio.stt.utils import load_model

import filmkit.languages as languages
import filmkit.repository as repository
from filmkit.narration.receipts import bound_records
from filmkit.narration.recognition import recognition_units, unit_distance
from filmkit.narration.snapshots import RECOGNIZER

# The libraries that run the recognizer, as a cached transcript records them, since another
# version of either may hear a recording otherwise: the speech library, and the array library
# that does its arithmetic, which the lock pins apart from it.
LIBRARIES = {name: version(name) for name in ("mlx-audio", "mlx")}
SCOPE = "Automatic transcription proxy; not pronunciation certification or listening."
# The cached transcripts, below the film's root, in a folder for each language.
CACHE = "build/evidence/transcript-records"


def recognizer() -> dict:
    """Check the supplied recognizer against its pins and return its identity: its hub
    repository and revision, its weights' SHA-256 and the versions of the speech library and of
    the array library under it.

    The check reads the weights, and is made on every run, also on one that finds every
    transcript cached and loads no model.
    """
    RECOGNIZER.verify()
    return {
        "repo": RECOGNIZER.repo,
        "revision": RECOGNIZER.revision,
        "weights_sha256": RECOGNIZER.weights["model.safetensors"],
        "libraries": dict(LIBRARIES),
    }


def transcript_record(language: str, record_id: str, wav_sha256: str, identity: dict) -> Path:
    """Where one recording's transcript by a recognizer of this identity is cached."""
    key = repository.content_sha(json.dumps(identity, sort_keys=True))
    name = f"{record_id}-{wav_sha256[:12]}-{key[:12]}.json"
    return repository.ROOT / CACHE / language.lower() / name


def cached_transcript(record: dict, language: str, identity: dict) -> str | None:
    """A recording's cached transcript, or None without one. An entry that cannot be read as a
    transcript is none either, and never silently: one line says so, and the transcript made
    again replaces it. That is an entry that is no JSON object, that lacks its text or one of
    the fields that bind it to its recording, recognizer and language, or whose text is no
    text. A cache that binds another recording, recognizer or language than its place names
    is refused."""
    path = transcript_record(language, record["id"], record["wav_sha256"], identity)
    if not path.exists():
        return None
    cached = repository.read_entry(path, ("wav_sha256", "recognizer", "language", "heard"))
    if cached is None or not isinstance(cached["heard"], str):
        unreadable = {"id": record["id"], "cache": repository.UNREADABLE_ENTRY}
        print(json.dumps({**unreadable, "entry": repository.relative(path)}), flush=True)
        return None
    bound = {"wav_sha256": record["wav_sha256"], "recognizer": identity, "language": language}
    if any(cached.get(key) != value for key, value in bound.items()):
        msg = "Cached transcript binding differs"
        raise ValueError(msg)
    return cached["heard"]


def load_recognizer():
    """Load the supplied ASR snapshot, which the caller has checked, downloading nothing."""
    return load_model(str(repository.ROOT / RECOGNIZER.folder))


def load_asr():
    """Load the pinned ASR snapshot once it is checked, without downloading anything."""
    RECOGNIZER.verify()
    return load_recognizer()


def transcribe(model, path: Path, language: str) -> str:
    """The model's transcript of one recording."""
    return model.generate(str(path), language=language).text


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Transcribe a narration receipt's recordings.")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--language", choices=languages.model_names(), required=True)
    options = parser.parse_args(argv)
    records = bound_records(options.receipt, options.language)
    identity = recognizer()
    model = None
    results = []
    for record in records:
        heard = cached_transcript(record, options.language, identity)
        if heard is None:
            model = model or load_recognizer()
            heard = transcribe(model, repository.ROOT / record["path"], options.language)
            repository.write(
                transcript_record(options.language, record["id"], record["wav_sha256"], identity),
                {
                    "id": record["id"],
                    "wav_sha256": record["wav_sha256"],
                    "recognizer": identity,
                    "language": options.language,
                    "heard": heard,
                },
            )
        expected = recognition_units(record["text"])
        rate = round(unit_distance(expected, recognition_units(heard)) / max(1, len(expected)), 4)
        results.append(
            {
                "id": record["id"],
                "path": record["path"],
                "wav_sha256": record["wav_sha256"],
                "heard": heard,
                "unit_error_rate": rate,
            }
        )
        print(json.dumps({"id": record["id"], "unit_error_rate": rate}), flush=True)
    repository.write(
        options.output,
        {
            "model": identity["repo"],
            "revision": identity["revision"],
            "language": options.language,
            "scope": SCOPE,
            "records": results,
        },
    )


if __name__ == "__main__":
    main()
