"""The motion an edition's reviewers read, from the motion report its picture gate judged.

`check-picture` follows every mark of the edition's picture as a viewer sees it move and gates
its halts, starts, races, pops, jumps, dash snaps and stretches over the pace line
(`filmkit.picture.gates`). The review's
measurement reports that same judgment, so reviewers judge motion from measurement rather than
from contact sheets: the counts of each kind of event, the findings and how many of them the
film declares, the fastest glide and flow of each scene and of the edition, and every finding
with its time, scene and drawing line. The gate record must be bound to the current composition
and timeline, the report must be the one the record binds, and it must judge every kind.

`bound_report` is the one reader of a report through the gate's record: the measurement reads
the gate's sync report by it as this module reads the motion report.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.picture.gates import MOTION_GATES as GATED
from filmkit.picture.rendering import COMPOSITION_SCRIPT
from filmkit.review import ReviewError

if TYPE_CHECKING:
    from filmkit.production import Edition

METHOD = (
    "every mark followed as a viewer sees it move, at 30 fps in 1080p px/s, by check-picture's "
    "motion audit; halts and starts change between rest (< 1.5 px/s) and 60 px/s within one "
    "frame, races reach 900 px/s, pops are firm marks appearing or vanishing within one frame "
    "and dash snaps strokes whose gaps step by a quarter of their dash pattern within one frame, "
    "all outside stage cuts, and a declared cut that keeps its stage excuses only the marks it "
    "takes away; jumps are the firm marks a stage cut keeps but moves whole by one shift of 8 px "
    "or more beyond their own motion, holding half the scene's firm ink; each finding is a run of "
    "frames of one kind, scene and line; a pace is a stretch of consecutive frames in which marks "
    "of one scene move over 450 px/s, a stage with the marks it carries and those moving within "
    "it counted once, by its fastest mark"
)
KINDS = ("halts", "starts", "races", "pops", "jumps", "dash_snaps", "paces")
# The prefixes of the gate record's motion findings.
MOTION_GATES = tuple(f"{name} " for name in GATED.values())


def bound_report(edition: Edition, name: str) -> tuple[dict, dict]:
    """The edition's gate record and the report of that name it binds, `motion` or `sync`.

    Refused unless the record binds the current composition and timeline and the report is the
    one it binds. An edition that was never gated, a record that binds no such report and a
    report cleared from the gate's work folder each refuse in one line that names the command
    to run.
    """
    code = edition.code
    if not edition.picture_gates.is_file():
        where = repository.relative(edition.picture_gates)
        msg = f"{code}: missing {where}, the picture gate record; run check-picture"
        raise ReviewError(msg)
    record = repository.read(edition.picture_gates)
    current = {
        "composition": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline": repository.sha(edition.timeline),
    }
    for input_name, sha in current.items():
        if record.get(f"{input_name}_sha256") != sha:
            msg = f"{code}: the picture gate record is not bound to the current {input_name}"
            raise ReviewError(msg)
    bound = record.get("reports", {}).get(name)
    if bound is None:
        msg = f"{code}: the picture gate record binds no {name} report; run check-picture again"
        raise ReviewError(msg)
    report = repository.ROOT / bound["path"]
    if not report.is_file():
        msg = (
            f"{code}: missing {bound['path']}, the {name} report its gate record binds; "
            "run check-picture again"
        )
        raise ReviewError(msg)
    if repository.sha(report) != bound["sha256"]:
        msg = f"{code}: the {name} report differs from the one its gate record binds"
        raise ReviewError(msg)
    return record, repository.read(report)


def picture_motion(edition: Edition) -> dict:
    """The edition's motion: its counts, findings, declared findings, speeds and events."""
    record, report = bound_report(edition, "motion")
    followed = report.get("followed")
    if followed is None:
        msg = f"{edition.code}: the motion report follows no marks; run check-picture again"
        raise ReviewError(msg)
    unjudged = [kind.replace("_", " ") for kind in KINDS if kind not in followed]
    if unjudged:
        msg = (
            f"{edition.code}: the motion report judges no {' or '.join(unjudged)};"
            " run check-picture again"
        )
        raise ReviewError(msg)
    largest = {}
    for scene, kinds in followed["speeds"].items():
        for kind, best in kinds.items():
            if kind not in largest or best["speed"] > largest[kind]["speed"]:
                largest[kind] = {**best, "scene": scene}
    return {
        "method": METHOD,
        "counts": {kind: len(followed[kind]) for kind in KINDS},
        "findings": len(followed["findings"]),
        "declared": sum(row.startswith(MOTION_GATES) for row in record["recorded_findings"]),
        "speeds": followed["speeds"],
        "largest": largest,
        "events": followed["findings"],
    }
