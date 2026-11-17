"""Qualify the renderer: a second render of one stage must show what the first shows.

A derived uncaptioned picture (`filmkit.picture.derivation`) rests on one render, where a film's
build used to render each stage twice and compare the two. What that comparison guarded
against, a render that draws a fragment wrong for one frame, which only a twin shows, is proven
for the renderer, the browser and the capture a film installs by `qualify_renderer`: it renders
the edition's current captioned stage a second time, with the pictures' settings, to a work
file, and compares the two renders by the measure of a rendered pair
(`filmkit.picture.equivalence.compare_renders`) with no row left out, the caption band being
part of what must agree. It passes when that comparison finds nothing: no sampled frame beyond
the encoders' noise, no one-frame fault, no lasting difference, and as many frames in each.

Two renders are not asked to decode alike. The renderer's hardware encode of one stage varies
from run to run when the encoder is shared, on frames that are given to it alike, so identical
decoded frames would refuse a whole film or a busy host for the encoder's variation and say
nothing of the renderer's drawing. How many frames do decode identically, and the lowest PSNR of
any frame, are recorded as facts that decide nothing, from one pass over both renders.

It runs under whatever capture the film declares, and its record names that capture. The sample
film declares software capture, the one under which uncaptioned pictures are derived, and its
build runs the qualification, so every engine release qualifies the renderer supply it pins for
that capture.

The record, build/evidence/editions/<code>/renderer-qualification.json, states what ran, not
what the engine pins: the renderer's version as the film's npm packages install it, the browser
executable the renders ran with its SHA-256 and, when those are the pinned build's bytes, that
build's name, and the capture. It names both renders' SHA-256, worker counts and frames, holds
the comparison's report and findings, and the frames that decode identically with the first
that does not and the lowest PSNR of any frame. A finding raises `PictureError` after the record
is written, and the second render is kept beside its receipt for inspection. A passing run
removes it.

Usage: python -m filmkit.produce qualify-renderer --language zh|en
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.durations as durations
import filmkit.picture.equivalence as equivalence
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
from filmkit.picture import browser
from filmkit.picture.rendering import PictureError
from filmkit.specification import FPS

if TYPE_CHECKING:
    from filmkit.production import Edition

# The second render and its receipt, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/renderer-qualification")


def supply() -> dict:
    """The renderer and the browser a render runs now: the installed package's version, and the
    executable with its SHA-256 and the pinned build's name when it holds that build's bytes.
    Refused for another renderer version than the engine's, or where no browser stands."""
    rendering.require_renderer()
    manifest = repository.node_modules() / rendering.RENDERER_PACKAGE
    installed = json.loads(manifest.read_text())
    drawn_by = browser.identity()
    if drawn_by["sha256"] is None:
        msg = f"No browser at {rendering.browser_path()}; run python -m filmkit.supply"
        raise PictureError(msg)
    return {
        "renderer": {"package": installed["name"], "version": installed["version"]},
        "browser": drawn_by,
    }


def qualify_renderer(edition: Edition, deadline: float = rendering.DEADLINE) -> dict:
    """Render the edition's captioned stage again and compare the two renders by the measure of a
    rendered pair; the record. The captioned picture must be valid as it stands."""
    ran = supply()
    with durations.phase("validation"):
        first_receipt = rendering.validate_picture(edition)
    # The record states one browser for both renders, so the first was drawn by the one that
    # runs now: two builds are not qualified as one.
    drew, runs = first_receipt.get("browser"), ran["browser"]
    if not isinstance(drew, dict) or drew.get("sha256") != runs["sha256"]:
        first = (
            f"{drew.get('executable')} (SHA-256 {drew.get('sha256')})"
            if isinstance(drew, dict)
            else "no browser"
        )
        msg = (
            f"The {edition.code} captioned picture's receipt names {first}, and the browser "
            f"that runs now is {runs['executable']} (SHA-256 {runs['sha256']}): a "
            "qualification compares two renders by one browser; render the picture again"
        )
        raise PictureError(msg)
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
    compared = equivalence.compare_renders(rendered.file, again, work)
    frames, findings = compared["frames"], compared["findings"]
    record = {
        **ran,
        "capture": second_receipt.get("capture"),
        "stage_sha256": repository.sha(rendered.stage / "index.html"),
        "first": render_of(rendered.file, first_receipt, frames["first"]),
        "second": render_of(again, second_receipt, frames["second"]),
        "comparison": compared["comparison"],
        # What decides nothing: the frames that decode identically, the first that does not, and
        # the lowest PSNR of any frame.
        **{key: compared[key] for key in equivalence.DECODED},
        # Why those were not measured, when the pass that measures them failed.
        "psnr_unmeasured": compared["psnr_unmeasured"],
        "findings": findings,
        "verdict": compared["verdict"],
    }
    repository.write(edition.renderer_qualification, record)
    shown = {"verdict": record["verdict"], "findings": findings}
    print(json.dumps(shown | {key: record[key] for key in ("identical_frames", "lowest_psnr_db")}))
    if findings:
        more = f" and {len(findings) - 1} more findings" if len(findings) > 1 else ""
        msg = (
            f"Two renders of the {edition.code} captioned stage do not show the same: "
            f"{findings[0]}{more}; the second render is kept in {repository.relative(work)}"
        )
        raise PictureError(msg)
    again.unlink()
    return record


def render_of(path: Path, receipt: dict, frames: int) -> dict:
    """One render as the record names it: its SHA-256, its worker count and its frames."""
    return {"sha256": receipt["output_sha256"], "workers": receipt.get("workers"), "frames": frames}
