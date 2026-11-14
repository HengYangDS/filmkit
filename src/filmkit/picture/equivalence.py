"""Prove that an edition's uncaptioned picture differs from its captioned one only by its captions.

`compare_pictures` runs once both pictures are rendered and valid
(`filmkit.picture.rendering.validate_picture`) and before packaging, which requires its passing
record (`require_equivalence`). It compares the pictures at two levels:

- the composition: the caption-equivalence tool (`picture/caption-equivalence.mjs`) runs the
  composition headlessly on the edition's timeline and on the same timeline with no captions, at
  every caption's start, middle and end and every half second, and requires each uncaptioned
  frame's paints to be the captioned frame's less its caption paints, the texts painted outside
  every scene that carry a cue's display text and that the frame's layout names as captions. Any
  other difference refuses the edition, so a film that paints anything else from its captions is
  refused. The tool reports the band of rows the caption paints cover.
- the encoded pictures: both rendered pictures are decoded at every half second and at every
  caption's start, middle and end frame, and compared outside the caption band, widened by
  `BAND_MARGIN` rows of the 1080-row frame on each side and out to the encoder's 16-pixel blocks.
  In each frame the mean absolute difference of every `TILE`-row square of the luma and chroma
  planes must stay within `TILE_LIMIT`, and the PSNR of all compared samples at or above
  `PSNR_FLOOR_DB`. The tile limit is the structural guard, which a missing label exceeds in its
  tile; the floor only has to catch a difference spread thinly across the whole frame, and lies
  below the encoders' noise at a keyframe of the films' denser pictures. Every frame of both
  pictures is then scanned for a fault that lasts one frame (`filmkit.picture.faults`): outside
  the band the two pictures are compared sample by sample, and inside it each picture against its
  own neighbouring frames. A fault names the picture that holds it, and the refusal the command
  that renders that picture again; a refusal whose every finding `repair-pictures` can repair
  (`faults.repairable`) names that command as its next step. The same scan measures the edge
  slivers (`filmkit.picture.slivers`): the samples more than 40 levels apart in each frame's
  densest 32-pixel block outside the band. The record keeps the one-frame transients and the
  slivers within the declared bound, and a frame beyond it is refused like a fault.

The record, build/evidence/editions/<code>/caption-equivalence.json, binds the composition, the
timeline, the engine version and both pictures' stage documents, files and receipts, and holds
each level's measures and its findings; a refusal raises `PictureError` after it is written.

Usage: python -m filmkit.produce compare-pictures --language zh|en
"""

from __future__ import annotations

import contextlib
import json
import math
import subprocess
import threading
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

import filmkit.picture.faults as faults
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.picture.rendering import (
    COMPOSITION_SCRIPT,
    PICTURE_SIZE,
    PictureError,
    validate_picture,
)
from filmkit.specification import DURATION, FPS

if TYPE_CHECKING:
    from filmkit.production import Edition

# The composition-level report and the work of a comparison, below the film's root.
WORK = Path("build/runtime/work/caption-equivalence")
# Seconds between the instants both levels sample beside every caption's start, middle and end.
STEP = 0.5
# The frame the composition draws in, whose rows the caption band is given in.
COMPOSITION_HEIGHT = 1080
# Rows of the 1080-row frame that widen the caption band on each side, and the encoder's block,
# in picture pixels, out to whose edges it is widened.
BAND_MARGIN = 24
BLOCK = 16
# The side of a compared tile in rows of the 1080-row frame, the largest mean absolute difference
# in 8-bit levels a tile may show, and the lowest PSNR in dB of a frame's compared samples. On the
# sample film the encoder's noise between the two pictures reached 1.51 levels and 60.2 dB at
# worst, and a picture missing one label outside the captions 17.2 and 24.8 levels in its tile.
# The sample's frames are sparse: the essentials film's pairs reached 53.69 and 54.78 dB, and the
# ETHOS film's Chinese pair fell to 49.76 dB at one of its 2,495 compared frames, frame 50580, a
# keyframe of both encodes (an I-frame every 12 frames), where the difference spread thinly over
# the whole content box, its largest tile 1.847 levels and its largest sample 47, while the frames
# around it measured about 72 and 62 dB and the composition-level comparison found no differing
# paint. The tile limit catches a missing label; the floor catches a diffuse difference across the
# frame, such as a uniform shift of 2 levels, which measures 42.1 dB, and passes that keyframe
# noise with a margin of 4.8 dB.
TILE = 32
TILE_LIMIT = 4.0
PSNR_FLOOR_DB = 45.0
# How many of the frames that differ most the record lists.
WORST = 10
# Seconds a picture's decode may take.
DECODE_DEADLINE = 7200


def picture_bindings(edition: Edition, captions: bool) -> dict:
    """What a record binds of one picture: its stage document, its file and its receipt."""
    rendered = edition.rendered(captions)
    return {
        "stage_sha256": repository.sha(rendered.stage / "index.html"),
        "picture_sha256": repository.sha(rendered.file),
        "receipt_sha256": repository.sha(rendered.receipt),
    }


def current_bindings(edition: Edition) -> dict:
    """The inputs a record binds: the composition, the timeline, the engine and both pictures."""
    return {
        "composition_sha256": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": version("filmkit"),
        "pictures": {
            name: picture_bindings(edition, captions)
            for name, captions in (("captioned", True), ("uncaptioned", False))
        },
    }


def composition_report(edition: Edition, work: Path) -> dict:
    """Run the caption-equivalence tool on the edition's timeline; its report."""
    report = work / "composition.json"
    status = tools.run("caption-equivalence", [str(edition.timeline), str(STEP)], stdout=report)
    if status != 0:
        msg = f"The caption-equivalence tool exited with status {status}"
        raise PictureError(msg)
    return repository.read(report)


def sampled_frames(timeline: dict) -> list[int]:
    """The frames the encoded level compares: every STEP seconds and every caption's start,
    middle and end frame, each once, in order."""
    last = DURATION * FPS - 1
    frames = set(range(0, last + 1, round(STEP * FPS)))
    for cue in timeline.get("captions", []):
        for t in (cue["start"], (cue["start"] + cue["end"]) / 2, cue["end"]):
            frames.add(min(last, max(0, math.floor(t * FPS))))
    return sorted(frames)


def excluded_rows(band: dict | None, height: int) -> tuple[int, int]:
    """The rows of a picture of `height` rows left out of the comparison: the caption band,
    widened by BAND_MARGIN on each side and out to BLOCK edges; none without a band."""
    if band is None:
        return (0, 0)
    scale = height / COMPOSITION_HEIGHT
    top = max(0, math.floor((band["top"] - BAND_MARGIN) * scale / BLOCK) * BLOCK)
    bottom = min(height, math.ceil((band["bottom"] + BAND_MARGIN) * scale / BLOCK) * BLOCK)
    return (top, bottom)


def selection(frames: list[int]) -> str:
    """An FFmpeg select expression true at exactly these frames: every STEP seconds by its
    remainder, and each other frame by its number, the sum balanced so that its depth stays
    logarithmic."""
    step = round(STEP * FPS)
    terms = [f"not(mod(n,{step}))", *(f"eq(n,{frame})" for frame in frames if frame % step)]
    while len(terms) > 1:
        paired = [f"({a}+{b})" for a, b in zip(terms[::2], terms[1::2], strict=False)]
        terms = paired + terms[len(paired) * 2 :]
    return terms[0]


def decode_command(path: Path, frames: list[int]) -> list[str]:
    """The FFmpeg command that decodes a picture's sampled frames as raw 8-bit 4:2:0 frames."""
    return [
        "ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-vf",
        f"select='{selection(frames)}'",
        "-fps_mode",
        "passthrough",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "yuv420p",
        "pipe:1",
    ]


def compare_decoded(
    edition: Edition, frames: list[int], rows: tuple[int, int], work: Path
) -> list[dict]:
    """Decode both pictures' sampled frames side by side and measure each pair; refused unless
    both decodes yield exactly the sampled frames without a message within the deadline."""
    size = PICTURE_SIZE
    length = size[0] * size[1] * 3 // 2
    paths = [edition.rendered(captions).file for captions in (True, False)]
    logs = [work / f"decode-{name}.log" for name in ("captioned", "uncaptioned")]
    measured = []
    with contextlib.ExitStack() as stack:
        errors = [stack.enter_context(log.open("wb")) for log in logs]
        processes = [
            subprocess.Popen(
                decode_command(path, frames),
                cwd=repository.ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=error,
            )
            for path, error in zip(paths, errors, strict=True)
        ]
        deadline = threading.Timer(DECODE_DEADLINE, lambda: [p.kill() for p in processes])
        deadline.start()
        try:
            for frame in frames:
                pair = [process.stdout.read(length) for process in processes]
                if any(len(data) != length for data in pair):
                    break
                a, b = (np.frombuffer(data, dtype=np.uint8) for data in pair)
                measured.append({"frame": frame, **frame_measures(a, b, size, rows)})
            extra = [process.stdout.read(1) for process in processes]
        finally:
            for process in processes:
                process.stdout.close()
                process.wait()
            deadline.cancel()
    messages = [log.read_text(errors="replace").strip() for log in logs]
    if (
        any(process.returncode for process in processes)
        or any(messages)
        or any(extra)
        or len(measured) != len(frames)
    ):
        shown = "; ".join(message[:300] for message in messages if message)
        msg = (
            f"Decoding both pictures gave {len(measured)} of their {len(frames)} sampled "
            f"frames{': ' + shown if shown else ''}"
        )
        raise PictureError(msg)
    return measured


def planes(frame: np.ndarray, size: tuple[int, int]) -> list[np.ndarray]:
    """A 4:2:0 frame's luma and two chroma planes."""
    width, height = size
    luma = width * height
    return [
        frame[:luma].reshape(height, width),
        frame[luma : luma * 5 // 4].reshape(height // 2, width // 2),
        frame[luma * 5 // 4 :].reshape(height // 2, width // 2),
    ]


def largest_tile(difference: np.ndarray, tile: int) -> float:
    """The largest mean absolute difference over the tiles of side `tile` that cover a region;
    the tiles at its right and bottom edges hold the pixels that are left."""
    if not difference.size:
        return 0.0
    rows, columns = range(0, difference.shape[0], tile), range(0, difference.shape[1], tile)
    sums = np.add.reduceat(np.add.reduceat(difference, rows, axis=0), columns, axis=1)
    heights = np.diff([*rows, difference.shape[0]])
    widths = np.diff([*columns, difference.shape[1]])
    return float((sums / np.outer(heights, widths)).max())


def frame_measures(
    captioned: np.ndarray, uncaptioned: np.ndarray, size: tuple[int, int], rows: tuple[int, int]
) -> dict:
    """One frame's measures outside the excluded rows: the largest tile difference of any plane,
    the PSNR of all compared samples, None where they are identical, and the largest sample
    difference."""
    tile = round(TILE * size[1] / COMPOSITION_HEIGHT)
    largest, squared, count, peak = 0.0, 0.0, 0, 0
    for scale, a, b in zip(
        (1, 2, 2), planes(captioned, size), planes(uncaptioned, size), strict=True
    ):
        top, bottom = rows[0] // scale, rows[1] // scale
        for region in (slice(0, top), slice(bottom, a.shape[0])):
            difference = np.abs(a[region].astype(np.int32) - b[region].astype(np.int32))
            largest = max(largest, largest_tile(difference, max(1, tile // scale)))
            squared += float(np.square(difference, dtype=np.float64).sum())
            count += difference.size
            peak = max(peak, int(difference.max(initial=0)))
    mse = squared / count if count else 0.0
    psnr = None if mse == 0 else round(10 * math.log10(255**2 / mse), 2)
    return {"largest_tile": round(largest, 3), "psnr_db": psnr, "largest_sample": peak}


def differs(measures: dict) -> bool:
    """Whether a frame's measures exceed the encoder's noise."""
    psnr = measures["psnr_db"]
    return measures["largest_tile"] > TILE_LIMIT or (psnr is not None and psnr < PSNR_FLOOR_DB)


def encoded_report(edition: Edition, timeline: dict, band: dict | None, work: Path) -> dict:
    """Compare both rendered pictures, decoded at the sampled frames, outside the caption band."""
    frames = sampled_frames(timeline)
    rows = excluded_rows(band, PICTURE_SIZE[1])
    measured = compare_decoded(edition, frames, rows, work)
    failing = [m for m in measured if differs(m)]
    worst = sorted(measured, key=lambda m: (-m["largest_tile"], m["psnr_db"] or math.inf))[:WORST]
    finite = [m["psnr_db"] for m in measured if m["psnr_db"] is not None]
    return {
        "frames": len(measured),
        "excluded_rows": list(rows),
        "tile_pixels": round(TILE * PICTURE_SIZE[1] / COMPOSITION_HEIGHT),
        "tile_limit": TILE_LIMIT,
        "psnr_floor_db": PSNR_FLOOR_DB,
        "largest_tile": max((m["largest_tile"] for m in measured), default=0.0),
        "lowest_psnr_db": min(finite, default=None),
        "identical_frames": len(measured) - len(finite),
        "largest_sample": max((m["largest_sample"] for m in measured), default=0),
        "worst": worst,
        "failing": failing[:WORST],
        "failing_frames": len(failing),
    }


def findings_of(composition: dict, encoded: dict | None, code: str) -> list[str]:
    """The record's findings: each composition instant that differs beyond its captions, the
    sampled encoded frames that differ beyond the encoder's noise, and the one-frame faults and
    lasting differences that the scan of every frame found (`faults.findings`)."""
    found = [
        f"composition at {row['time']:.3f} s: the captioned frame paints "
        f"{json.dumps(row['captioned'], ensure_ascii=False)}, the uncaptioned frame "
        f"{json.dumps(row['uncaptioned'], ensure_ascii=False)}"
        for row in composition["findings"]
    ]
    hidden = composition["differing_instants"] - len(composition["findings"])
    found += [f"composition: {hidden} more instants differ"] if hidden > 0 else []
    if encoded is not None:
        found += [
            f"encoded frame {row['frame']}: tile difference {row['largest_tile']} levels, "
            f"PSNR {row['psnr_db']} dB outside the caption band"
            for row in encoded["failing"]
        ]
        hidden = encoded["failing_frames"] - len(encoded["failing"])
        found += [f"encoded: {hidden} more frames differ"] if hidden > 0 else []
        found += faults.findings(encoded["every_frame"], code)
    return found


def next_step(record: dict, code: str) -> str:
    """The clause that names `repair-pictures` as a refused record's next step where the repair
    accepts the record, and nothing where it would refuse it."""
    try:
        faults.repairable(record, code)
    except PictureError:
        return ""
    return f"; next: {faults.REPAIR.format(code=code)}"


def compare_pictures(edition: Edition) -> dict:
    """Compare the edition's two pictures at both levels, write the record and refuse a finding."""
    for captions in (True, False):
        validate_picture(edition, captions=captions)
    work = repository.ROOT / WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    bound = current_bindings(edition)
    timeline = repository.read(edition.timeline)
    composition = composition_report(edition, work)
    encoded = None
    if composition["differing_instants"] == 0:
        encoded = encoded_report(edition, timeline, composition["band"], work)
        files = {r.name: r.file for r in (edition.rendered(True), edition.rendered(False))}
        rows, frames = tuple(encoded["excluded_rows"]), DURATION * FPS
        encoded["every_frame"] = faults.scan(files, PICTURE_SIZE, rows, frames, FPS, work)
    if current_bindings(edition) != bound:
        msg = "A picture, the composition or the timeline changed while they were compared"
        raise PictureError(msg)
    findings = findings_of(composition, encoded, edition.code)
    report = work / "composition.json"
    record = {
        **bound,
        "composition": {
            "report": {"path": repository.relative(report), "sha256": repository.sha(report)},
            **{key: value for key, value in composition.items() if key != "findings"},
        },
        "encoded": encoded or {"not_compared": "the compositions differ beyond their captions"},
        "findings": findings,
        "verdict": "refuse" if findings else "pass",
    }
    repository.write(edition.caption_equivalence, record)
    print(json.dumps({"verdict": record["verdict"], "findings": len(findings)}))
    if findings:
        msg = f"The {edition.code} pictures differ beyond their captions: " + "; ".join(findings)
        raise PictureError(msg + next_step(record, edition.code))
    return record


def require_equivalence(edition: Edition) -> dict:
    """The edition's passing equivalence record, refused unless it binds the current pictures,
    composition, timeline and engine."""
    path = edition.caption_equivalence
    if not path.is_file():
        msg = f"The {edition.code} pictures have no equivalence record; run compare-pictures"
        raise PictureError(msg)
    record = repository.read(path)
    current = current_bindings(edition)
    stale = [key for key, value in current.items() if record.get(key) != value]
    if stale:
        msg = (
            f"The {edition.code} equivalence record binds another {', '.join(stale)}; "
            "run compare-pictures"
        )
        raise PictureError(msg)
    if record.get("verdict") != "pass":
        msg = f"The {edition.code} equivalence record did not pass; run compare-pictures"
        raise PictureError(msg)
    return record
