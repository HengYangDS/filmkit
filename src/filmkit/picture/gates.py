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
hold the previous picture and the cues mostly drawn as labels are recorded. The frame audit also
judges every wrapped label at rest by the film's `[picture.wrapping]` rules, which it reads from
the file `FILMKIT_WRAPPING` names: each label that breaks one is gated unless one of the
edition's declared exceptions names its lines, which records it with the exception's reason,
and an exception whose lines no frame of the edition paints is gated as stale. The renderer's
browser computes a clockwise arc through a whole turn in single precision and can paint no ink
for one that starts off a whole number of turns: the frame audit lists each such stroked arc, by
its scene, line and each distinct start and end, and the `whole-turns` tool draws each start and
end once on a scratch canvas in that browser. A line whose turn paints no ink from one of its
starts is gated, and every other is recorded; each finding names the ellipse from 0 that paints
the turn from any start. A gated finding refuses with `PictureError`, after the record is
written, and so does an audit that fails or a composition or timeline that changes while it is
checked.
The motion audit follows every mark as a viewer sees it move, and each of its findings is gated
by its time, scene, marks and the line that drew it: a halt, start, race, pop or dash snap outside
a stage cut, a pop that a declared cut keeping its stage brings, and the jump of the marks a stage
cut keeps but moves whole. One of the edition's `[[picture.motion.exceptions]]` that names its
scene, its line or module and its kind records it with the exception's reason instead; an
exception that matches no finding of the edition is gated as stale.
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
from filmkit.film import FILM
from filmkit.picture import metrics, sync_audit, text_trace
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError, face_bindings

if TYPE_CHECKING:
    from filmkit.film import Motion, Wrapping
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
    # Balance as the reviews since round 29 measure it, on the full-size lit box of every frame:
    # build-ups, and still states that a stage cut or the next scene replaced.
    "off_centre_builds",
    "off_centre_finished",
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
# still states off centre that end within their stage, which are a settled composition or a
# build-up held while its next parts are still to come, as only the stage's intent tells.
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
# The variable that names the film's wrapping rules to the frame audit
# (frame-audit/typography/breaks.mjs).
WRAPPING_VARIABLE = "FILMKIT_WRAPPING"


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


def shown_lines(lines: tuple[str, ...]) -> str:
    """A label's lines as a finding names them, each quoted, top to bottom."""
    return " / ".join(json.dumps(line, ensure_ascii=False) for line in lines)


def wrapping_rules(wrapping: Wrapping) -> dict:
    """The rules the frame audit judges wrapped labels by: the declared shares and lead words."""
    return wrapping.model_dump(mode="json", include={"line_share", "last_share", "lead_words"})


def wrapping_findings(frame: dict, wrapping: Wrapping, code: str) -> tuple[list[str], list[str]]:
    """The gated and the recorded findings of an edition's wrapped labels.

    Each label at rest that breaks a rule is gated, by its scene, its lines, when it first
    stands at rest and each rule it breaks, unless one of the edition's exceptions names its
    lines, which records it with the exception's reason. An exception of the edition whose lines
    no frame paints is gated as stale.
    """
    declared = {e.lines: e.reason for e in wrapping.exceptions if e.edition == code}
    painted, gated, recorded = set(), [], []
    for scene, labels in sorted(frame.get("wrapped_labels", {}).items()):
        for label in labels:
            lines = tuple(label["lines"])
            painted.add(lines)
            if not label["breaks"]:
                continue
            named = (
                f"frame wrapped label {scene} {shown_lines(lines)} at rest {label['at']:.2f} s: "
                + "; ".join(label["breaks"])
            )
            if lines in declared:
                recorded.append(f"{named}; declared: {declared[lines]}")
            else:
                gated.append(named)
    gated += [
        f"frame wrapping exception {shown_lines(lines)} is stale: no frame of the edition paints it"
        for lines in declared
        if lines not in painted
    ]
    return gated, recorded


# The measure each kind of motion finding is gated as, and what it does, as a finding states it.
MOTION_GATES = {
    "halt": "motion_halts",
    "start": "motion_starts",
    "race": "motion_races",
    "pop": "motion_pops",
    "jump": "motion_jumps",
    "dash": "motion_dash_snaps",
}
MOTION_WORDS = {
    "halt": "falls from {speed} px/s to rest",
    "start": "sets off from rest at {speed} px/s",
    "race": "moves at {speed} px/s for {frames} frames",
    "pop": "at ink {level} {appears} within one frame",
    "jump": "jump {distance} px ({shift[0]}, {shift[1]}) beyond their motion as {marks} marks at a cut",
    "dash": "turns from {gaps[0]:.0%} to {gaps[1]:.0%} gap in its dash pattern within one frame",
}
# What a pop adds when a declared stage cut that keeps its stage brought it.
DECLARED_CUT = " at a declared cut that keeps its stage"


# The remedy for a whole turn the renderer's browser may paint without ink: the same ring as an
# ellipse from 0, its start the rotation.
WHOLE_TURN = "ellipse(x, y, r, r, start, 0, 2 * Math.PI)"


def turn_findings(draws: list[dict], painted: dict) -> tuple[list[str], list[str]]:
    """The gated and the recorded findings of the stroked whole turns the frame audit found, by
    the renderer's browser's draws of each of their distinct starts and ends.

    A line, a scene's line of film.js, is gated when the browser paints no ink for its turn from
    one of its starts, naming the frames of those starts, the first of them and how many fail, and
    when one of its starts was not drawn. Every other line is recorded with all its frames and its
    first start. Each finding names the ellipse that paints the turn from any start.
    """
    verdicts = {(turn["start"], turn["end"]): turn["paints"] for turn in painted["turns"]}
    lines: dict[tuple[str, str], list[dict]] = {}
    for drawn in draws:
        lines.setdefault((drawn["scene"], drawn["origin"]), []).append(drawn)
    gated, recorded = [], []
    for (scene, origin), drawn in lines.items():
        where = origin + (f" ({drawn[0]['module']})" if drawn[0]["module"] else "")
        undrawn = [d for d in drawn if (d["start"], d["end"]) not in verdicts]
        if undrawn:
            gated.append(
                f"frame vanishing_arcs {scene}: {len(undrawn)} starts of the whole turn drawn at"
                f" {where} were not drawn in the renderer's browser"
            )
            continue
        failing = [d for d in drawn if not verdicts[(d["start"], d["end"])]]
        shown = failing or drawn
        span = f"{min(d['from'] for d in shown):.2f}-{max(d['to'] for d in shown):.2f} s"
        start = min(shown, key=lambda d: d["from"])["start"]
        named = (
            f"{scene} {span}: a clockwise arc through a whole turn from {start:.4f} rad, drawn at"
            f" {where}, paints"
        )
        if failing:
            gated.append(
                f"frame vanishing_arcs {named} no ink in the renderer's browser from"
                f" {len(failing)} of its {len(drawn)} starts; draw it as {WHOLE_TURN}"
            )
        else:
            recorded.append(
                f"frame whole_turns {named} in the renderer's browser from each of its"
                f" {len(drawn)} starts; the ellipse draws it from any start: {WHOLE_TURN}"
            )
    return gated, recorded


def motion_finding(finding: dict) -> str:
    """A motion finding as the record names it: its kind, scene, time, marks and drawing line."""
    start, end = finding["start"], finding["end"]
    span = f"{start:.2f} s" if start == end else f"{start:.2f}-{end:.2f} s"
    texts = ", ".join(repr(text) for text in finding["texts"])
    marks = "/".join(finding["paints"]) + (f" {texts}" if texts else "")
    way = finding.get("way")
    words = MOTION_WORDS[finding["kind"]].format(
        **finding, appears="appears" if way == "in" else "vanishes"
    ) + (DECLARED_CUT if finding.get("declared_cut") else "")
    drawn = finding["origin"] + (f" ({finding['module']})" if finding["module"] else "")
    measure = MOTION_GATES[finding["kind"]]
    return f"{measure} {finding['scene']} {span}: {marks} {words}, drawn at {drawn}"


def motion_findings(motion: dict, policy: Motion, code: str) -> tuple[list[str], list[str]]:
    """The gated and the recorded motion findings of an edition.

    Each finding is gated unless one of the edition's exceptions names its scene, its kind and
    its line or module, which records it with the exception's reason. An exception of the
    edition that matches no finding is gated as stale.
    """
    exceptions = [e for e in policy.exceptions if e.edition == code]
    matched, gated, recorded = set(), [], []
    for finding in motion["followed"]["findings"]:
        named = motion_finding(finding)
        kept = next(
            (
                e
                for e in exceptions
                if (e.scene, e.kind) == (finding["scene"], finding["kind"])
                and e.source in (finding["origin"], finding["module"])
            ),
            None,
        )
        if kept is None:
            gated.append(named)
        else:
            matched.add(kept)
            recorded.append(f"{named}; declared: {kept.reason}")
    gated += [
        f"motion exception {e.kind} {e.scene} {e.source} is stale: no finding of the edition"
        " matches it"
        for e in exceptions
        if e not in matched
    ]
    return gated, recorded


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
    turns_path, painted_path = work / "turns.json", work / "whole-turns.json"
    faces = {metrics.VARIABLE: str(metrics.current_table())}
    wrapping = FILM.picture.wrapping
    rules = work / "wrapping.json"
    repository.write(rules, wrapping_rules(wrapping))
    traces = {"TRACE": str(trace), "TEXTS": str(texts_trace), "MARKS": str(marks)}
    traces["TURNS"] = str(turns_path)
    run_audit(
        "frame-audit",
        [timeline, f"{FRAME_STEP:.7f}"],
        frame_path,
        {**traces, WRAPPING_VARIABLE: str(rules), **faces},
    )
    # The browser draws each start and end of the whole turns once; a picture without one starts
    # no browser.
    draws = repository.read(turns_path)["draws"]
    if draws:
        run_audit("whole-turns", [str(turns_path)], painted_path)
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
    wrapped, declared = wrapping_findings(frame, wrapping, edition.code)
    moved, kept = motion_findings(motion, FILM.picture.motion, edition.code)
    turned, painting = turn_findings(draws, repository.read(painted_path)) if draws else ([], [])
    findings = gated_findings(frame, sync, motion) + turned + text_findings(texts)
    findings += wrapped + moved
    reports = [
        ("frame", frame_path),
        ("sync", sync_path),
        ("texts", texts_path),
        ("motion", motion_path),
    ]
    reports += [("whole_turns", painted_path)] if draws else []
    record = {
        **bound,
        "frames_checked": frame["frames_checked"],
        "reports": {
            name: {"path": repository.relative(path), "sha256": repository.sha(path)}
            for name, path in reports
        },
        "gated_findings": findings,
        "recorded_findings": recorded_findings(frame, sync) + painting + declared + kept,
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
