"""The sound gate: the lines a soundtrack must hold before the picture follows it.

The review's measurement records a soundtrack's clarity and its delivered endings, and reviewers
hold lines on them: no segment under the clarity floor its film declares, no thought that ends
abruptly or is cut while voiced, no phrase that stops without a heard fall. A record that nothing
refuses lets a retake cross such a line and a reviewer find it one round later, after the picture
was rendered on it. `check-sound` takes the same measures from the assembled soundtrack and its
timeline, writes them with their verdict beside the edition's other records, bound to the
soundtrack and the timeline it judged, and refuses a gated finding.

The gate judges only the lines whose measures agree with the reviewers' on delivered films. A
measure that is recorded but not yet calibrated against them, such as the pace or level step
between thoughts, stays with the review's measurement.
"""

from __future__ import annotations

import json
from importlib.metadata import version
from typing import TYPE_CHECKING

import filmkit.repository as repository
import filmkit.review.clarity as clarity
import filmkit.review.endings as endings
from filmkit.soundtrack.assembly import AssemblyError

if TYPE_CHECKING:
    from filmkit.production import Edition


def clarity_findings(measured: dict) -> list[str]:
    """The soundtrack and each segment that read below the floor the film declares."""
    floor = measured["floor_db"]
    findings = []
    if measured["soundtrack"]["below_floor"]:
        value = measured["soundtrack"]["cpp_db"]
        findings.append(f"the soundtrack's clarity is {value} dB, below the declared {floor} dB")
    findings += [
        f"segment {row['id']}'s clarity is {row['cpp_db']} dB, below the declared {floor} dB"
        for row in measured["segments"]
        if row["below_floor"]
    ]
    return findings


def ending_findings(measured: dict) -> list[str]:
    """The thoughts that end abruptly or are cut while voiced, and the phrases that stop."""
    delivered = measured["delivered"]
    findings = [f"thought {name} ends abruptly as delivered" for name in delivered["abrupt"]]
    findings += [
        f"thought {name} is cut while voiced where its release begins"
        for name in delivered["cut_while_voiced"]
    ]
    findings += [
        f"thought {stop['thought']} stops at {stop['word']!r} ({stop['end']} s)"
        " without a heard fall"
        for stop in measured["phrase_endings"]["stopped"]
    ]
    return findings


def sound_findings(clarity_measured: dict, endings_measured: dict) -> list[str]:
    """Every gated finding of a soundtrack's measures, clarity first, in the film's order."""
    return clarity_findings(clarity_measured) + ending_findings(endings_measured)


def check_sound(edition: Edition) -> dict:
    """Measure the edition's assembled soundtrack, write its gate record and refuse a finding."""
    timeline = repository.read(edition.timeline)
    assembly = repository.read(edition.audio_assembly)
    bound = {
        "soundtrack_sha256": repository.sha(edition.soundtrack),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": version("filmkit"),
    }
    clarity_measured = clarity.voice_clarity(edition.code, edition.soundtrack, timeline)
    endings_measured = endings.endings(edition, timeline, assembly)
    findings = sound_findings(clarity_measured, endings_measured)
    record = {
        **bound,
        "clarity": clarity_measured,
        "endings": endings_measured,
        "gated_findings": findings,
        "verdict": "refuse" if findings else "pass",
    }
    repository.write(edition.sound_gates, record)
    print(json.dumps({"verdict": record["verdict"], "gated_findings": len(findings)}))
    if findings:
        noun = "finding" if len(findings) == 1 else "findings"
        msg = f"The {edition.code} soundtrack has {len(findings)} gated {noun}: " + "; ".join(
            findings
        )
        raise AssemblyError(msg)
    return record
