"""The picture's gate before a render: the headless audits of an edition's picture and their record.

`check_picture` runs, from the film's root, the frame audit over every frame of the edition's
timeline at one thirtieth of a second with its label, text and mark traces, the sync audit on
those traces, the text measures of `filmkit.picture.text_trace`, and the motion audit at 30
frames per second, both audits measuring text by the advance widths of the film's declared faces
(`filmkit.picture.metrics`). Their reports go to build/runtime/work/picture-gates/<code>/. The
edition's gate record binds the SHA-256 of the composition, the timeline, the stylesheet and each
declared font, the engine version and the frames the frame audit checked; it holds each report's
SHA-256, every gated finding and every recorded finding, and passes only when there is no gated
one. Besides the labels out of sync, the sync audit's seats, its unnamed speech and its caption
cues drawn whole as one label are gated, and so are an opening that shows the declared title for
less than a second before the first word and every text at rest below 4.5:1; the thoughts that
hold the previous picture and the cues mostly drawn as labels are recorded. A gated finding
refuses with `PictureError`, after the record is written, and so does an audit that fails or a
composition or timeline that changes while it is checked.
`render-picture` reads the record before it starts the renderer
(`filmkit.picture.rendering.require_passing_gates`).

Usage: python -m filmkit.produce check-picture --language zh|en
"""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.picture import metrics, sync_audit, text_trace
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError, face_bindings

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
    # Balance as the reviews since round 29 measure it, on the full-size lit box of every frame.
    "off_centre_builds",
    "sparse_runs",
    "thin_lit",
    "thin_runs",
    "underfilled_containers",
    "faint_clutter",
    # How text lines up, from exact anchors, sizes and baselines and the widths of the film's
    # declared faces (frame-audit/typography/).
    "ragged_rows",
    "ragged_columns",
    "crammed_lines",
    "off_card_centre",
    "uneven_pitch",
    "touching_marks",
    "mixed_case",
)
# The frame audit's findings that the record lists for the reviewers and that refuse nothing: the
# still states off centre, which are a settled composition or a build-up held while its next
# parts are still to come, as only the stage's intent tells.
FRAME_RECORDED = ("off_centre_settled",)
# Seconds a still picture may hold under speech: the reviewers' limit for a held picture.
STILL_LIMIT = 3.5
# Seconds of the frames before the first word that show every word of the declared title.
TITLE_SECONDS = 1.0
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
    continuity = sync["continuity"]
    findings += [
        f"sync seat {row['thought']} at {row['at']:.2f} s: a mark waits {row['lag']:.2f} s"
        f" for its name at {row['box']}"
        for row in continuity["seats"]
    ]
    findings += [
        f"sync unnamed speech {row['thought']} {row['from']:.2f}-{row['to']:.2f} s"
        for row in continuity["unnamed_speech"]
    ]
    findings += [
        f"sync caption echo {row['start']:.2f} s: one label repeats {row['text']!r}"
        for row in continuity["caption_echoes"]
        if row["whole"]
    ]
    findings += [
        f"motion still {run['start']:.2f}-{run['end']:.2f} s ({run['seconds']} s)"
        for run in motion["still"]
        if run["seconds"] > STILL_LIMIT
    ]
    return findings


def text_findings(texts: dict) -> list[str]:
    """The text measures' gated findings: an opening that does not show the declared title for
    `TITLE_SECONDS`, and each text at rest below 4.5:1."""
    title, found = texts["opening_title"], []
    if title["shown_seconds"] < TITLE_SECONDS:
        missing = ", ".join(title["missing_words"])
        shown = (
            f"text title {title['title']!r} shown {title['shown_seconds']:.2f} s before the first"
            f" word at {title['first_word']:.2f} s"
        )
        found.append(f"{shown}; never shown: {missing}" if missing else shown)
    found += [
        f"text contrast {run['scene'] or run['role']} {run['text']!r} {run['from']:.2f}-"
        f"{run['to']:.2f} s at {run['lowest']:.2f}:1"
        for run in texts["low_contrast"]
    ]
    return found


def recorded_findings(frame: dict, sync: dict) -> list[str]:
    """The findings the record lists for the reviewers and that refuse nothing.

    They are the frame audit's recorded measures, the thoughts that hold the previous picture,
    since a deliberate index may stay while the first new name arrives, and the caption cues
    mostly drawn as labels, since labels may name the marks whose words a cue says, or a cue may
    quote what the picture shows.
    """
    found = [
        f"frame {key}: {json.dumps(frame[key], ensure_ascii=False)}"
        for key in FRAME_RECORDED
        if frame.get(key)
    ]
    continuity = sync["continuity"]
    found += [
        f"sync held over {row['thought']} {row['held']:.2f} s" for row in continuity["held_over"]
    ]
    found += [
        f"sync caption echo {row['start']:.2f} s: labels repeat {row['share']:.0%} of"
        f" {row['text']!r}" + (", a quotation the picture shows" if row.get("quoted") else "")
        for row in continuity["caption_echoes"]
        if not row["whole"]
    ]
    return found


def current_bindings(edition: Edition) -> dict:
    """The inputs a gate record binds: the composition, the timeline, the engine version, and the
    stylesheet and fonts from which the audits measure text."""
    return {
        "composition_sha256": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": version("filmkit"),
        **face_bindings(),
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
    texts_trace, texts_path = work / "texts.tsv", work / "texts.json"
    faces = {metrics.VARIABLE: str(metrics.current_table())}
    run_audit(
        "frame-audit",
        [timeline, f"{FRAME_STEP:.7f}"],
        frame_path,
        {"TRACE": str(trace), "TEXTS": str(texts_trace), "MARKS": str(marks), **faces},
    )
    run_audit(
        "motion-audit",
        [timeline, str(MOTION_FPS), "--out", str(motion_path)],
        work / "motion-summary.json",
        faces,
    )
    sync = sync_audit.full_report(repository.read(edition.timeline), trace, marks, FRAME_STEP)
    repository.write(sync_path, sync)
    lines = sync_audit.read_trace(texts_trace)
    texts = text_trace.report(repository.read(edition.timeline), lines, FRAME_STEP)
    repository.write(texts_path, texts)
    if current_bindings(edition) != bound:
        msg = "The composition or the timeline changed while it was checked"
        raise PictureError(msg)
    frame, motion = repository.read(frame_path), repository.read(motion_path)
    findings = gated_findings(frame, sync, motion) + text_findings(texts)
    record = {
        **bound,
        "frames_checked": frame["frames_checked"],
        "reports": {
            name: {"path": repository.relative(path), "sha256": repository.sha(path)}
            for name, path in (
                ("frame", frame_path),
                ("sync", sync_path),
                ("texts", texts_path),
                ("motion", motion_path),
            )
        },
        "gated_findings": findings,
        "recorded_findings": recorded_findings(frame, sync),
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
