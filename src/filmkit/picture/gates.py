"""The picture's gate before a render: the headless audits of an edition's picture and their record.

`check_picture` runs, from the film's root, the frame audit over every frame of the edition's
timeline at one thirtieth of a second with its label and mark traces, the sync audit on those
traces, and the motion audit at 30 frames per second. Their reports go to
build/runtime/work/picture-gates/<code>/. The edition's gate record binds the SHA-256 of the
composition and of the timeline, the engine version and the frames the frame audit checked; it
holds each report's SHA-256 and every gated finding, and passes only when there is none. A
gated finding refuses with `PictureError`, after the record is written, and so does an audit that
fails or a composition or timeline that changes while it is checked. `render-picture` reads the
record before it starts the renderer (`filmkit.picture.rendering.require_passing_gates`).

Usage: python -m filmkit.produce check-picture --language zh|en
"""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.picture import sync_audit
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError

if TYPE_CHECKING:
    from filmkit.production import Edition

# The frame audit's findings that refuse a render. The DDWG reviews turned each into a rule
# that a delivered film keeps.
FRAME_GATES = (
    "errors",
    "overlaps",
    "outside_safe_area",
    "graphic_collisions",
    "empty_during_speech",
    "blank_between_scenes",
    "bare_frames",
    "dim_frames",
    "faint_first_words",
    "thin_during_speech",
    "shapes_outside_action_safe",
    "name_load",
    "unplaced_labels",
    "type_sizes",
    "dot_joins",
    "lists_leaving_early",
    "lists_leaving_dimmed",
    "off_balance",
    "off_centre",
    "off_centre_runs",
    "sparse_runs",
    "thin_lit",
    "thin_runs",
    "underfilled_containers",
    "faint_clutter",
)
# Seconds a still picture may hold under speech: the reviewers' limit for a held picture.
STILL_LIMIT = 3.5
# The frame audit's sampling step and the motion audit's frame rate.
FRAME_STEP = 1 / 30
MOTION_FPS = 30
# The audits' reports, in a folder for each edition below the film's root.
WORK = Path("build/runtime/work/picture-gates")


def gated_findings(frame: dict, sync: dict, motion: dict) -> list[str]:
    """Every gated finding of the three reports, each named by its audit and measure."""
    findings = [
        f"frame {key}: {json.dumps(frame[key], ensure_ascii=False)}"
        for key in FRAME_GATES
        if frame.get(key)
    ]
    findings += [
        f"sync {row['scene']} {row['label']}: {row['verdict']} at {row['legible']:.2f} s"
        for row in sync["findings"]
    ]
    findings += [
        f"motion still {run['start']:.2f}-{run['end']:.2f} s ({run['seconds']} s)"
        for run in motion["still"]
        if run["seconds"] > STILL_LIMIT
    ]
    return findings


def current_bindings(edition: Edition) -> dict:
    """The inputs a gate record binds: the composition, the timeline and the engine version."""
    return {
        "composition_sha256": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": version("filmkit"),
    }


def run_audit(tool: str, arguments: list[str], out: Path, environment: dict | None = None) -> None:
    """Run one of the engine's Node audits, its standard output written to `out`."""
    status = tools.run(tool, arguments, environment=environment, stdout=out)
    if status != 0:
        msg = f"The {tool} exited with status {status}; its report is {repository.relative(out)}"
        raise PictureError(msg)


def check_picture(edition: Edition) -> dict:
    """Audit the edition's current picture, write its gate record and refuse a gated finding."""
    work = repository.ROOT / WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    bound = current_bindings(edition)
    timeline = str(edition.timeline)
    frame_path, trace, marks = work / "frame.json", work / "trace.tsv", work / "marks.tsv"
    sync_path, motion_path = work / "sync.json", work / "motion.json"
    run_audit(
        "frame-audit",
        [timeline, f"{FRAME_STEP:.7f}"],
        frame_path,
        {"TRACE": str(trace), "MARKS": str(marks)},
    )
    run_audit(
        "motion-audit",
        [timeline, str(MOTION_FPS), "--out", str(motion_path)],
        work / "motion-summary.json",
    )
    sync = sync_audit.full_report(repository.read(edition.timeline), trace, marks, FRAME_STEP)
    repository.write(sync_path, sync)
    if current_bindings(edition) != bound:
        msg = "The composition or the timeline changed while it was checked"
        raise PictureError(msg)
    frame, motion = repository.read(frame_path), repository.read(motion_path)
    findings = gated_findings(frame, sync, motion)
    record = {
        **bound,
        "frames_checked": frame["frames_checked"],
        "reports": {
            name: {"path": repository.relative(path), "sha256": repository.sha(path)}
            for name, path in (("frame", frame_path), ("sync", sync_path), ("motion", motion_path))
        },
        "gated_findings": findings,
        "verdict": "refuse" if findings else "pass",
    }
    repository.write(edition.picture_gates, record)
    print(json.dumps({key: record[key] for key in ("verdict", "frames_checked")}))
    if findings:
        msg = f"The {edition.code} picture has {len(findings)} gated findings: " + "; ".join(
            findings
        )
        raise PictureError(msg)
    return record
