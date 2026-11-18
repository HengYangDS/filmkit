"""Qualify the renderer: a second render of one stage must show what the first shows.

A derived uncaptioned picture (`filmkit.picture.derivation`) rests on one render, where a film's
build used to render each stage twice and compare the two. What that comparison guarded
against, a render that draws a fragment wrong for one frame, which only a twin shows, is proven
for the canvas a film installs by `qualify_renderer`: it renders
the edition's current captioned stage a second time, with the pictures' settings, to a work
file, and compares the two renders by the measure of a rendered pair
(`filmkit.picture.equivalence.compare_renders`) with no row left out, the caption band being
part of what must agree. The second render is drawn in another count of spans than the first,
in one process where the first was drawn in several, so a composition that carries state from
one frame to the next, which a span would start without, is seen by the digest over the whole
film. It passes when the two renders state one digest of their drawn frames
(`filmkit.picture.renderer`) and that comparison finds nothing: no sampled frame beyond
the encoders' noise, no one-frame fault, no lasting difference, and as many frames in each.

Two renders are not asked to encode alike: the digest binds the drawn frames, and the encoded
bytes are not compared. How many frames decode identically, and the lowest PSNR of any frame,
are recorded as facts that decide nothing, from one pass over both renders.

A native render reads no declared capture. The sample film's build runs the qualification, so
every engine release qualifies the canvas build it pins.

The record, build/evidence/editions/<code>/renderer-qualification.json, states what ran, not
what the engine pins: the canvas package, its version and the integrity the film's installed
packages record for it, the native library the second render's processes loaded and the text
renderer they ran, as that render's receipt names them, and `pinned_build`, whether that is the
build the engine pins. Two renders by different builds are not qualified as one: the first
render's receipt must name the same. It names both renders' SHA-256, spans, drawn digests and
frames, says whether the digests are alike, holds the comparison's report and findings, and the
frames that decode identically with the first that does not and the lowest PSNR of any frame. A
finding raises `PictureError` after the record is written, and the second render is kept beside
its receipt for inspection. A passing run removes it.

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
from filmkit.picture import renderer
from filmkit.picture.errors import PictureError
from filmkit.specification import FPS

if TYPE_CHECKING:
    from filmkit.production import Edition

# The second render and its receipt, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/renderer-qualification")


def build_of(drawn: dict) -> str:
    """A canvas build as a refusal names it: the package's integrity and the loaded library."""
    binary = drawn.get("binary") if isinstance(drawn.get("binary"), dict) else {}
    return (
        f"{drawn.get('package')} {drawn.get('version')} ({drawn.get('integrity')}) with the "
        f"native library {binary.get('sha256')} and {drawn.get('text_renderer')} text"
    )


def other_count(first: object) -> int:
    """The spans of a second render: one process where the first was drawn in several, two
    where it was drawn in one."""
    return 1 if isinstance(first, int) and first > 1 else 2


def qualify_renderer(edition: Edition, deadline: float = renderer.DEADLINE) -> dict:
    """Render the edition's captioned stage again and compare the two renders by the measure of a
    rendered pair; the record. The captioned picture must be valid as it stands."""
    renderer.require_renderer()
    with durations.phase("validation"):
        first_receipt = rendering.validate_picture(edition)
    # The record states one canvas for both renders. What the film installs now is asked before
    # the render, and what the second render loaded and ran after it.
    drew, installs = first_receipt["renderer"], renderer.installed()
    if any(drew.get(key) != value for key, value in installs.items()):
        msg = (
            f"The {edition.code} captioned picture's receipt names {drew.get('package')} "
            f"{drew.get('version')} ({drew.get('integrity')}), and the canvas the film installs "
            f"now is {installs['package']} {installs['version']} ({installs['integrity']}): a "
            "qualification compares two renders by one canvas; render the picture again"
        )
        raise PictureError(msg)
    rendered = edition.rendered(True)
    work = repository.ROOT / WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    again, receipt = work / rendered.file.name, work / "receipt.json"
    again.unlink(missing_ok=True)
    drawn_in = other_count(first_receipt.get("spans"))
    command = renderer.command(rendered.stage, again, FPS, drawn_in)
    with durations.phase("render"):
        second_receipt = renderer.record_render(
            command, rendered.stage, again, receipt, deadline, rendered.name
        )
    ran = second_receipt["renderer"]
    if renderer.build(ran) != renderer.build(drew):
        msg = (
            f"The {edition.code} captioned picture was drawn by {build_of(drew)}, and the second "
            f"render by {build_of(ran)}: a qualification compares two renders by one build; "
            "render the picture again"
        )
        raise PictureError(msg)
    compared = equivalence.compare_renders(rendered.file, again, work)
    frames, findings = compared["frames"], compared["findings"]
    # Two draws of one stage are the same frames, by the renderer's digest of what it drew.
    drawn = (first_receipt.get("drawn_sha256"), second_receipt.get("drawn_sha256"))
    if drawn[0] != drawn[1]:
        findings = [f"the two renders drew different frames ({drawn[0]}, {drawn[1]})", *findings]
    record = {
        "renderer": ran,
        "pinned_build": renderer.unqualified(second_receipt) is None,
        "drawn_alike": drawn[0] == drawn[1],
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
        "verdict": "refuse" if findings else "pass",
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
    """One render as the record names it: its SHA-256, its spans, the digest of its drawn frames
    and its frames."""
    return {
        "sha256": receipt["output_sha256"],
        "spans": receipt.get("spans"),
        "drawn_sha256": receipt.get("drawn_sha256"),
        "frames": frames,
    }
