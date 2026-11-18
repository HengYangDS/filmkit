"""What the tests of a narration's convergence share: its thoughts, seeds, records and checks.

The module loads the convergence and with it the speech runtime, so only the test modules
that are collected where that runtime loads import it; the fixtures that use it import it
when they are asked for (`conftest.py`: `studio`, `engine`).
"""

import json

import filmkit.narration.converge as narration_converge
import filmkit.repository as repository
from filmkit.production import Edition

RATE = 24000
THOUGHTS = ("First thought.", " Second thought.")
SEED = 1


def seed_of(k: int) -> int:
    return SEED + k * narration_converge.STRIDE


def write_checks(code: str, records: list[dict], words) -> None:
    """Write the two checks' outputs of a receipt's recordings, the segment's words as placed."""
    paths = narration_converge.evidence_paths(code)
    rows = [
        {"id": record["id"], "wav_sha256": record["wav_sha256"], "path": record["path"]}
        for record in records
    ]
    items = [
        [{"text": text, "start_time": start, "end_time": end} for text, start, end in words(record)]
        for record in records
    ]
    aligned = [
        {**row, "text_sha256": record["text_sha256"], "items": placed}
        for row, record, placed in zip(rows, records, items, strict=True)
    ]
    repository.write(paths["alignment"], {"records": aligned})
    repository.write(paths["asr"], {"records": [{**row, "heard": ""} for row in rows]})


def placed(record: dict, *, gap: float = 0.0) -> list[tuple[str, float, float]]:
    """A segment's words, 0.4 s each from 0.15 s into each thought; `gap` parts the last two."""
    found = []
    for child in record["utterance_groups"]["records"]:
        start = child["start_sample"] / RATE + 0.15
        names = child["text"].replace(".", "").split()
        for number, word in enumerate(names):
            late = gap if number == len(names) - 1 and child["index"] == 2 else 0.0
            found.append((word, start + 0.4 * number + late, start + 0.4 * number + 0.4 + late))
    return found


def record_of(code: str = "en") -> dict:
    return repository.read(Edition(code).ear_first / narration_converge.RECORD)


def counts(capsys) -> dict:
    return json.loads(capsys.readouterr().out.splitlines()[-1])


def thought_of(index: int) -> dict:
    """A thought's record in the edition's receipt."""
    receipt = repository.read(narration_converge.evidence_paths("en")["receipt"])
    return receipt["records"][0]["utterance_groups"]["records"][index - 1]
