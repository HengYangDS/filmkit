"""Qualify the renderer: two renders of one stage must decode to the same frames.

A derived uncaptioned picture (`filmkit.picture.derivation`) relies on the renderer drawing a
stage the same way every time, which a film's build no longer proves by rendering each stage
twice. `qualify_renderer` proves it for the renderer, the browser and the capture a film
installs: it renders the edition's current captioned stage a second time, with the pictures'
settings, to a work file, decodes both renders completely and requires every frame of the second
to equal the first's. It runs under whatever capture the film declares, and its record names
that capture. The sample film declares software capture, the one under which uncaptioned pictures
are derived, and its build runs the qualification, so every engine release qualifies the renderer
supply it pins for that capture.

The record, build/evidence/editions/<code>/renderer-qualification.json, names the renderer's
version, the capture, both renders' SHA-256 and worker counts, the frames compared and the first
frame that differs, if any; a difference raises `PictureError` after it is written, and the
second render is kept beside its receipt for inspection. A passing run removes it.

Usage: python -m filmkit.produce qualify-renderer --language zh|en
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.durations as durations
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.specification import FPS

if TYPE_CHECKING:
    from filmkit.production import Edition

# The second render and its receipt, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/renderer-qualification")
# Seconds a picture's complete decode may take.
DECODE_DEADLINE = 7200


def frame_digests(path: Path) -> list[str]:
    """The MD5 of every decoded frame of a picture's video stream, in presentation order."""
    command = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-map", "0:v:0"]
    listed = repository.run([*command, "-f", "framemd5", "-"], timeout=DECODE_DEADLINE).stdout
    rows = [line for line in listed.decode().splitlines() if line and not line.startswith("#")]
    return [row.rsplit(",", 1)[1].strip() for row in rows]


def qualify_renderer(edition: Edition, deadline: float = rendering.DEADLINE) -> dict:
    """Render the edition's captioned stage again and compare every decoded frame with the
    picture's; the record. The captioned picture must be valid as it stands."""
    with durations.phase("validation"):
        first_receipt = rendering.validate_picture(edition)
    rendered = edition.rendered(True)
    work = repository.ROOT / WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    again, receipt = work / rendered.file.name, work / "receipt.json"
    again.unlink(missing_ok=True)
    command = rendering.renderer_command(rendered.stage, again, FPS, "looks")
    with durations.phase("render"):
        second_receipt = rendering.record_render(
            command, rendered.stage, again, receipt, deadline, rendered.name
        )
    with durations.phase("decode"), ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(frame_digests, (rendered.file, again))
    pairs = enumerate(zip(first, second, strict=False))
    differing = [frame for frame, (ours, theirs) in pairs if ours != theirs]
    identical = not differing and len(first) == len(second) and bool(first)
    record = {
        "renderer_version": rendering.RENDERER_VERSION,
        "browser": list(rendering.BROWSER),
        "capture": second_receipt.get("capture"),
        "stage_sha256": repository.sha(rendered.stage / "index.html"),
        "first": render_of(rendered.file, first_receipt, len(first)),
        "second": render_of(again, second_receipt, len(second)),
        "differing_frames": len(differing),
        "first_differing_frame": differing[0] if differing else None,
        "verdict": "pass" if identical else "refuse",
    }
    repository.write(edition.renderer_qualification, record)
    print(json.dumps({key: record[key] for key in ("verdict", "differing_frames")}))
    if not identical:
        where = (
            f"frame {differing[0]} is the first of {len(differing)} that differ"
            if differing
            else f"the renders hold {len(first)} and {len(second)} frames"
        )
        msg = (
            f"Two renders of the {edition.code} captioned stage do not decode alike: {where}; "
            f"the second render is kept in {repository.relative(work)}"
        )
        raise PictureError(msg)
    again.unlink()
    return record


def render_of(path: Path, receipt: dict, frames: int) -> dict:
    """One render as the record names it: its SHA-256, its worker count and its frames."""
    return {"sha256": receipt["output_sha256"], "workers": receipt.get("workers"), "frames": frames}
