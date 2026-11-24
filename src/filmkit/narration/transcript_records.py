"""Where each narration recording's transcript is cached.

A transcript is cached under its recording's waveform and the identity of the recognizer that
heard it, so a recording heard again by another recognizer never reuses or replaces it. The
transcription caches records here, under the build directory, in a folder for each language.
"""

import json
from pathlib import Path

import filmkit.repository as repository

CACHE = "build/evidence/transcript-records"


def transcript_record(language: str, record_id: str, wav_sha256: str, identity: dict) -> Path:
    """Where one recording's transcript by a recognizer of this identity is cached."""
    key = repository.content_sha(json.dumps(identity, sort_keys=True))
    name = f"{record_id}-{wav_sha256[:12]}-{key[:12]}.json"
    return repository.ROOT / CACHE / language.lower() / name
