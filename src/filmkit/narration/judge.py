"""Judge every thought of an edition's narration by the lines the film holds for a take.

The command reads the edition's current narration receipt, the one its cast declares, checks
that it holds exactly the script's thoughts, each with its current text and bound recording,
and measures and judges each thought's take (`filmkit.narration.judgment`). Where the
narration's alignment of those recordings stands beside the receipt, it also asks the
selection's gates about each segment as they will measure it, and a thought they refuse is
refused here (`gate-pause`, `gate-terms`). It generates nothing and changes no input. Its
record, judgment.json beside the receipt, holds every thought's measures, its verdict on each
line and the lines it fails, states the clarity lines the film declares, and binds the receipt,
the script and the cast it was made from by their digests; judging unchanged takes again writes
the same record.

A thought is refused when a line fails. The command then exits 1 and names every refused
thought with every line it fails, at once.

Usage: python -m filmkit.narration.judge --language zh|en
"""

from __future__ import annotations

import argparse
import json

import filmkit.narration.judgment as judgment
import filmkit.repository as repository
from filmkit.narration.narrate import evidence_paths
from filmkit.narration.receipts import bound_records
from filmkit.production import CODES, Edition

RECORD = "judgment.json"


def receipt_of(code: str) -> str:
    """The edition's narration receipt, where the narration writes it."""
    return evidence_paths(code)["receipt"]


def alignment_of(code: str) -> str:
    """The alignment of the edition's receipt, where the narration writes it."""
    return evidence_paths(code)["alignment"]


def gate_of(code: str, records: list[dict]) -> dict | None:
    """What the selection's gates refuse of the receipt's recordings, by thought.

    Returns:
        The refused lines of each refused thought, or None when the alignment beside the
        receipt is not of its recordings and the gates cannot be asked.
    """
    path = repository.ROOT / alignment_of(code)
    if not path.is_file():
        return None
    aligned = {row["id"]: row for row in repository.read(path)["records"]}
    recorded = {record["id"]: record["wav_sha256"] for record in records}
    if {name: row.get("wav_sha256") for name, row in aligned.items()} != recorded:
        return None
    script = repository.read(Edition(code).script)
    return judgment.gate_refused(code, script, records, aligned)


def bound(code: str) -> dict:
    """The digests of what an edition's record was made from: its receipt, script and cast."""
    edition = Edition(code)
    files = {"receipt": receipt_of(code), "script": edition.script, "cast": edition.cast}
    return {f"{name}_sha256": repository.sha(path) for name, path in files.items()}


def current(code: str) -> list[dict]:
    """The records of the edition's receipt, which must hold the script's thoughts as they stand."""
    edition = Edition(code)
    records = bound_records(receipt_of(code), edition.language)
    script, cast = repository.read(edition.script), repository.read(edition.cast)
    judgment.holds_script(script, records)
    every = {(record["id"], child["index"]): None for record, child in judgment.thoughts(records)}
    judgment.checked(script, cast, records, every, Edition(code).places.reference)
    return records


def judged(code: str, records: list[dict], bench, held) -> dict:
    """The edition's judgment record, written beside its receipt."""
    gate = gate_of(code, records)
    rows = judgment.with_gates(judgment.judge_thoughts(records, bench, held), gate)
    record = {
        "edition": code,
        "receipt": receipt_of(code),
        "bound": bound(code),
        "aligner": bench.aligner["identity"],
        "clarity": {
            "floor_db": held.floor,
            "thought_line_db": held.line,
            "kept": sorted(held.kept),
        },
        "unit_limit": judgment.UNIT_LIMIT,
        "gates": "asked" if gate is not None else judgment.GATE_NOT_ASKED,
        "thoughts": rows,
        "refused": {row["thought"]: row["failed"] for row in rows if row["failed"]},
    }
    repository.write(Edition(code).ear_first / RECORD, record)
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Judge every thought of an edition's narration.")
    parser.add_argument("--language", choices=CODES, required=True)
    code = parser.parse_args(argv).language
    records = current(code)
    record = judged(code, records, *judgment.studio(code, records))
    rows = record["thoughts"]
    summary = {
        "edition": code,
        "thoughts": len(rows),
        "refused": len(record["refused"]),
        "differing_by_reading": sum(1 for row in rows if row["differing_units_by_reading"]),
        "record": repository.relative(Edition(code).ear_first / RECORD),
    }
    print(json.dumps(summary), flush=True)
    if record["refused"]:
        refused = f"{code}: {len(record['refused'])} of {len(rows)} thoughts are refused"
        raise SystemExit("\n".join([refused, *judgment.refusal(rows)]))


if __name__ == "__main__":
    main()
