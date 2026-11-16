"""Derive an edition's uncaptioned picture from its captioned one, and prove what that relies on.

The uncaptioned picture is the captioned picture with the rows of its caption band painted in the
ground: `derive_uncaptioned` encodes every frame of the valid captioned picture once more with
x264, the band's rows replaced by the ground as the captioned picture itself holds it, read from
one of its frames in YUV, so no colour is converted. The rows are the band the composition report
names, widened as a comparison widens it (`filmkit.picture.equivalence.excluded_rows`).

A derivation proves two things, in work it does anyway:

- before it encodes, the band audit (`picture/band-audit.mjs`) runs the composition headlessly at
  every thirtieth of a second and refuses a caption paint that leaves the rows or any other paint
  that reaches them, and lists the stretches in which no caption is painted;
- while it encodes, the same decode measures the captioned picture's band at every frame of those
  stretches, less `EDGE_FRAMES` at each end, and the derivation refuses unless the lowest and the
  highest sample of each plane stand within `GROUND_TOLERANCE` levels of the ground.

A refusal leaves no uncaptioned picture or receipt in place and names `--native`, which renders
the uncaptioned stage instead (`filmkit.picture.rendering.render_picture`). The receipt, at the
uncaptioned picture's own place, says `derived` and binds the captioned picture, its receipt, the
composition, the timeline and the engine, with the rows, the ground and both proofs; validation
reads either kind of receipt (`validate`, `validate_binding`), and `compare_derived` writes the
comparison record of a derived pair from the receipt, decoding no picture. Packaging asks
`film_source` which picture each film reads: the 1080p uncaptioned film of a derived pair is
painted and scaled from the captioned picture in one pass.

Usage: python -m filmkit.produce render-picture --language zh|en --uncaptioned [--native]
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

import filmkit.durations as durations
import filmkit.media as media
import filmkit.picture.equivalence as equivalence
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.picture.rendering import (
    COMPOSITION_SCRIPT,
    PICTURE_SIZE,
    PictureError,
    require_receipt_picture,
    validate_picture,
)
from filmkit.specification import DURATION, FPS

if TYPE_CHECKING:
    from filmkit.production import Edition, Rendition

# The work of a derivation, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/derivation")
# The frames a second at which the band audit runs the composition: the frame audit's own step.
AUDIT_FPS = 30
# Frames left out at each end of a stretch without a caption: two steps of the band audit.
EDGE_FRAMES = 2 * FPS // AUDIT_FPS
# The most a sample of the captioned band may depart from the ground, in 8-bit levels, at a frame
# without a caption. A caption or a mark departs by tens to hundreds of levels; the encoder's
# ripple in a flat band reached 2 levels below busy synthetic content and none on a film's span
# of 7,200 frames (17 November 2026).
GROUND_TOLERANCE = 3
# The derived picture's encoder: x264 at the rate factor the renderer encodes the pictures at,
# with a keyframe forced every KEYFRAME_SECONDS and none at a scene cut. On a span of 7,200 UHD
# frames this encode took 17.8 s where the native render took 141.2 s, and stood 59.0 dB on
# average from the native picture above the band (17 November 2026).
KEYFRAME_SECONDS = 2
ENCODER = (
    "-c:v",
    "libx264",
    "-preset",
    "veryfast",
    "-crf",
    "14",
    "-g",
    str(KEYFRAME_SECONDS * FPS),
    "-keyint_min",
    str(KEYFRAME_SECONDS * FPS),
    "-sc_threshold",
    "0",
    "-pix_fmt",
    "yuv420p",
)
# Seconds a derivation's encode may take.
DEADLINE = 7200
NATIVE = "render-picture --language {code} --uncaptioned --native"
PLANES = ("y", "u", "v")


def source_bindings(edition: Edition) -> dict:
    """What a derivation binds: the captioned picture and its receipt, the composition, the
    timeline and the engine."""
    captioned = edition.rendered(True)
    return {
        "source_sha256": repository.sha(captioned.file),
        "source_receipt_sha256": repository.sha(captioned.receipt),
        "composition_sha256": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": version("filmkit"),
    }


def band_audit(edition: Edition, rows: tuple[int, int], work: Path) -> dict:
    """Run the band audit on the painted rows, given in the composition's frame; its report.

    Refused, naming the first escape or intrusion and `--native`, unless the rows hold caption
    paints and nothing else at every instant.
    """
    scale = PICTURE_SIZE[1] / equivalence.COMPOSITION_HEIGHT
    report = work / "band-audit.json"
    arguments = [str(edition.timeline), *(f"{row / scale:g}" for row in rows), str(AUDIT_FPS)]
    status = tools.run("band-audit", arguments, stdout=report)
    try:
        audit = json.loads(report.read_text())
    except ValueError:
        msg = f"The band audit exited with status {status} and no report"
        raise PictureError(msg) from None
    if audit.get("verdict") != "pass" or status != 0:
        found = [f"a caption leaves the rows at {row['time']:.3f} s" for row in audit["escapes"]]
        found += [
            f"a {row['kind']} of scene {row['scene']} reaches the rows at {row['time']:.3f} s"
            for row in audit["intrusions"]
        ]
        shown = "; ".join(found[:3]) or f"the tool exited with status {status}"
        msg = (
            f"The {edition.code} caption band holds more than captions on the ground: {shown} "
            f"({audit.get('escaping_instants', 0)} instants with an escape, "
            f"{audit.get('intruding_instants', 0)} with an intrusion); render the uncaptioned "
            f"picture with {NATIVE.format(code=edition.code)}"
        )
        raise PictureError(msg)
    return audit


def free_frames(stretches: list[list[float]], fps: int = FPS) -> list[tuple[int, int]]:
    """The frames the ground check reads: each stretch without a caption as its first and last
    frame, less `EDGE_FRAMES` at each end; a stretch too short to keep a frame is left out."""
    kept = []
    for first, last in stretches:
        a, b = round(first * fps) + EDGE_FRAMES, round(last * fps) - EDGE_FRAMES
        if b >= a:
            kept.append((a, b))
    return kept


def selection(frames: list[tuple[int, int]]) -> str:
    """An FFmpeg select expression true inside these runs of frames, the sum balanced so that its
    depth stays logarithmic."""
    terms = [f"between(n,{a},{b})" for a, b in frames]
    while len(terms) > 1:
        paired = [f"({a}+{b})" for a, b in zip(terms[::2], terms[1::2], strict=False)]
        terms = paired + terms[len(paired) * 2 :]
    return terms[0]


def read_ground(source: Path, rows: tuple[int, int], size: tuple[int, int], frame: int) -> dict:
    """The ground of the band: the median sample of each plane of the picture's rows at a frame
    without a caption."""
    width, height = size[0], rows[1] - rows[0]
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-ss",
        f"{frame / FPS:.6f}",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-frames:v",
        "1",
        "-vf",
        f"crop={width}:{height}:0:{rows[0]}",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "yuv420p",
        "pipe:1",
    ]
    try:
        data = np.frombuffer(repository.run(command, timeout=600).stdout, dtype=np.uint8)
    except subprocess.CalledProcessError as error:
        said = error.stderr.decode(errors="replace")[:600]
        msg = f"Reading the band of frame {frame} failed: {said}"
        raise PictureError(msg) from error
    luma = width * height
    if data.size != luma * 3 // 2:
        msg = f"Reading the band of frame {frame} gave {data.size} of {luma * 3 // 2} samples"
        raise PictureError(msg)
    planes = (data[:luma], data[luma : luma * 5 // 4], data[luma * 5 // 4 :])
    return {name: int(np.median(plane)) for name, plane in zip(PLANES, planes, strict=True)}


def band_crop(size: tuple[int, int], rows: tuple[int, int]) -> str:
    """The filter that keeps the band's rows of a picture of `size`."""
    return f"crop={size[0]}:{rows[1] - rows[0]}:0:{rows[0]}"


def painted(
    source: str, size: tuple[int, int], rows: tuple[int, int], ground: dict, out: str
) -> str:
    """The filter graph from the stream `source` to `out` that sets the band's rows to the ground:
    the rows are cropped, every sample of each plane set to the ground's, and laid back over."""
    paint = "lutyuv=" + ":".join(f"{name}={ground[name]}" for name in PLANES)
    return (
        f"[{source}]split=2[main][strip];"
        f"[strip]{band_crop(size, rows)},{paint}[paint];"
        f"[main][paint]overlay=x=0:y={rows[0]}:format=yuv420[{out}]"
    )


def derive_command(
    source: Path,
    target: Path,
    size: tuple[int, int],
    rows: tuple[int, int],
    ground: dict,
    frames: list[tuple[int, int]],
    stats: Path,
) -> list[str]:
    """The FFmpeg command of a derivation: one decode of the captioned picture feeds the encode,
    with the band's rows set to the ground, and the measure of the band at the frames given,
    whose lowest and highest samples go to `stats`, a path without a colon or a quote."""
    graph = (
        "[0:v:0]split=2[picture][measure];"
        f"{painted('picture', size, rows, ground, 'derived')};"
        f"[measure]select='{selection(frames)}',{band_crop(size, rows)},signalstats,"
        f"metadata=mode=print:file={stats}[measured]"
    )
    return [
        "ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-filter_complex",
        graph,
        "-map",
        "[derived]",
        *ENCODER,
        str(target),
        "-map",
        "[measured]",
        "-f",
        "null",
        "-",
    ]


def ground_check(stats: Path, frames: list[tuple[int, int]], ground: dict, fps: int = FPS) -> dict:
    """Read the band's measures and refuse a frame that departs from the ground.

    Every frame of the runs given must be measured, and the lowest and the highest sample of each
    plane must stand within `GROUND_TOLERANCE` levels of the ground. Returns the frames checked
    and the largest departure.
    """
    expected = [frame for a, b in frames for frame in range(a, b + 1)]
    blocks = re.split(r"(?m)^frame:", stats.read_text())[1:]
    if len(blocks) != len(expected):
        msg = f"The band was measured at {len(blocks)} of its {len(expected)} frames"
        raise PictureError(msg)
    largest, worst = 0, None
    for frame, block in zip(expected, blocks, strict=True):
        timed = re.search(r"pts_time:(\S+)", block)
        held = re.findall(r"signalstats\.([YUV])(?:MIN|MAX)=(\d+)", block)
        if timed is None or round(float(timed[1]) * fps) != frame or len(held) != 6:
            msg = f"The band's measure of frame {frame} is not readable"
            raise PictureError(msg)
        departure = max(abs(int(value) - ground[plane.lower()]) for plane, value in held)
        if departure > largest:
            largest, worst = departure, frame
    if largest > GROUND_TOLERANCE:
        msg = (
            f"The captioned picture's band is not the ground at frame {worst}, a frame without a "
            f"caption: a sample stands {largest} levels from the ground"
        )
        raise PictureError(msg)
    return {"frames": len(expected), "largest_departure": largest, "verdict": "pass"}


def derive(
    source: Path,
    target: Path,
    size: tuple[int, int],
    rows: tuple[int, int],
    frames: list[tuple[int, int]],
    work: Path,
    deadline: float = DEADLINE,
) -> dict:
    """Derive `target` from `source` with the rows painted, in the work folder, and check the
    ground: the ground, the command, its seconds and the check's result. `target` is written
    only once the check passed; a refusal removes the work's picture."""
    work.mkdir(parents=True, exist_ok=True)
    partial, stats = work / "derived.mp4", work / "band-stats.txt"
    for earlier in (partial, stats):
        earlier.unlink(missing_ok=True)
    with durations.phase("ground"):
        ground = read_ground(source, rows, size, frames[0][0])
    relative = Path(repository.relative(stats))
    command = derive_command(source, partial, size, rows, ground, frames, relative)
    started = time.monotonic()
    try:
        with durations.phase("encode"):
            encode = subprocess.run(
                command,
                cwd=repository.ROOT,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=deadline,
            )
        seconds = time.monotonic() - started
        if encode.returncode != 0 or encode.stderr:
            msg = f"The derivation's encode failed: {encode.stderr.decode(errors='replace')[:600]}"
            raise PictureError(msg)
        with durations.phase("ground-check"):
            check = ground_check(stats, frames, ground)
    except (PictureError, subprocess.TimeoutExpired):
        partial.unlink(missing_ok=True)
        raise
    finally:
        stats.unlink(missing_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial.replace(target)
    return {"ground": ground, "command": command, "elapsed_seconds": seconds, "check": check}


def require_derived_media(path: Path) -> None:
    """Refuse a derived picture that is not the whole film at the pictures' frame, rate and size,
    with a keyframe at every `KEYFRAME_SECONDS` and nowhere else."""
    frames = DURATION * FPS
    media.require_video(
        media.probe(path), frames=frames, fps=FPS, size=PICTURE_SIZE, duration=DURATION
    )
    keyframes = media.video_cadence(path, frames, FPS)["keyframes"]
    if keyframes != list(range(0, frames, KEYFRAME_SECONDS * FPS)):
        msg = f"The derived picture's keyframes leave the {KEYFRAME_SECONDS} s grid: {path.name}"
        raise PictureError(msg)


def derive_uncaptioned(edition: Edition, deadline: float = DEADLINE) -> dict:
    """Derive the edition's uncaptioned picture from its valid captioned picture and write its
    receipt; an earlier uncaptioned picture and receipt are removed first, so a refusal leaves
    none in place."""
    with durations.phase("validation"):
        validate_picture(edition)
    captioned, rendered = edition.rendered(True), edition.rendered(False)
    for earlier in (rendered.file, rendered.receipt):
        earlier.unlink(missing_ok=True)
    bound = source_bindings(edition)
    work = repository.ROOT / WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    with durations.phase("composition"):
        composition = equivalence.composition_report(edition, work)
    native = NATIVE.format(code=edition.code)
    if composition["differing_instants"] or composition["band"] is None:
        why = (
            "paints no caption"
            if composition["band"] is None
            else f"differs beyond its captions at {composition['differing_instants']} instants"
        )
        msg = f"The {edition.code} composition {why}; render the uncaptioned picture with {native}"
        raise PictureError(msg)
    rows = equivalence.excluded_rows(composition["band"], PICTURE_SIZE[1])
    with durations.phase("band-audit"):
        audit = band_audit(edition, rows, work)
    frames = free_frames(audit["free"])
    if not frames:
        msg = (
            f"The {edition.code} film shows a caption at every instant, so its band's ground "
            f"cannot be read; render the uncaptioned picture with {native}"
        )
        raise PictureError(msg)
    started = datetime.now(UTC)
    made = derive(captioned.file, rendered.file, PICTURE_SIZE, rows, frames, work, deadline)
    try:
        with durations.phase("media"):
            require_derived_media(rendered.file)
        if source_bindings(edition) != bound:
            msg = "The captioned picture, the composition or the timeline changed meanwhile"
            raise PictureError(msg)
    except (PictureError, media.MediaError):
        rendered.file.unlink(missing_ok=True)
        raise
    report = work / "band-audit.json"
    receipt = {
        "picture": rendered.name,
        "derived": {
            "from": captioned.name,
            **bound,
            "band": composition["band"],
            "rows": list(rows),
            "ground": made["ground"],
            "tolerance": GROUND_TOLERANCE,
            "band_audit": {
                "report": {"path": repository.relative(report), "sha256": repository.sha(report)},
                "instants": audit["instants"],
                "caption_instants": audit["caption_instants"],
                "stretches": len(audit["free"]),
                "verdict": audit["verdict"],
            },
            "ground_check": made["check"],
        },
        "command": made["command"],
        "exit": 0,
        "timed_out": False,
        "deadline_seconds": deadline,
        "started_at": started.isoformat(),
        "elapsed_seconds": made["elapsed_seconds"],
        "output_path": str(rendered.file),
        "output_sha256": repository.sha(rendered.file),
    }
    repository.write(rendered.receipt, receipt)
    print(json.dumps({"derived": rendered.file.name, "rows": list(rows), **made["check"]}))
    return receipt


def is_derived(receipt: dict) -> bool:
    """Whether a receipt of the uncaptioned picture is a derivation's."""
    return isinstance(receipt.get("derived"), dict)


def film_source(edition: Edition, rendition: Rendition) -> tuple[Path, str, tuple[str, ...]]:
    """The picture a delivered film reads, the stream it maps and its video options.

    A film copies or scales its own picture. The uncaptioned film that re-encodes, of a pair
    whose uncaptioned picture is derived, reads the captioned picture instead, painted as the
    derivation painted it and scaled in the same pass: one encode from the render, where scaling
    the derived picture would be two.
    """
    own = edition.rendered(rendition.captions)
    scaled = rendition.reencoded and "-filter:v:0" in rendition.video
    if rendition.captions or not scaled or not own.receipt.is_file():
        return own.file, "0:v:0", rendition.video
    receipt = repository.read(own.receipt)
    if not is_derived(receipt):
        return own.file, "0:v:0", rendition.video
    derived, at = receipt["derived"], rendition.video.index("-filter:v:0")
    paint = painted("0:v:0", PICTURE_SIZE, tuple(derived["rows"]), derived["ground"], "painted")
    graph = f"{paint};[painted]{rendition.video[at + 1]}[viewing]"
    rest = (*rendition.video[:at], *rendition.video[at + 2 :])
    return edition.rendered(True).file, "[viewing]", ("-filter_complex", graph, *rest)


def validate_binding(edition: Edition, receipt: dict) -> None:
    """Bind a derived uncaptioned picture to its receipt and the receipt to the current captioned
    picture, composition, timeline and engine, with both proofs passed."""
    rendered = edition.rendered(False)
    require_receipt_picture(receipt, rendered)
    derived = receipt["derived"]
    again = f"run render-picture --language {edition.code} --uncaptioned"
    stale = [key for key, value in source_bindings(edition).items() if derived.get(key) != value]
    if stale:
        msg = f"The derived picture's receipt binds another {', '.join(stale)}; {again}"
        raise PictureError(msg)
    proofs = (derived.get("band_audit", {}), derived.get("ground_check", {}))
    if (
        receipt.get("exit") != 0
        or receipt.get("timed_out", True)
        or any(proof.get("verdict") != "pass" for proof in proofs)
        or len(derived.get("rows", [])) != 2
    ):
        msg = f"The derived picture's receipt records no completed derivation; {again}"
        raise PictureError(msg)
    if not rendered.file.is_file() or receipt.get("output_sha256") != repository.sha(rendered.file):
        msg = f"The derived picture differs from its receipt; {again}"
        raise PictureError(msg)


def validate(edition: Edition, receipt: dict) -> dict:
    """Bind the derived uncaptioned picture to its receipt and check its media; the receipt."""
    validate_binding(edition, receipt)
    require_derived_media(edition.rendered(False).file)
    return receipt


def compare_derived(edition: Edition, receipt: dict) -> dict:
    """Write the comparison record of a derived pair from its derivation's receipt.

    The composition report must find no difference beyond the captions and name the band the
    derivation painted; no picture is decoded. A finding refuses after the record is written.
    """
    work = repository.ROOT / equivalence.WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    bound = equivalence.current_bindings(edition)
    with durations.phase("composition"):
        composition = equivalence.composition_report(edition, work)
    derived = receipt["derived"]
    findings = equivalence.findings_of(composition, None, edition.code)
    if not findings and composition["band"] != derived["band"]:
        findings.append(
            f"the derivation painted the band {derived['band']} and the composition reports "
            f"{composition['band']}; run render-picture --language {edition.code} --uncaptioned"
        )
    report = work / "composition.json"
    record = {
        **bound,
        "composition": {
            "report": {"path": repository.relative(report), "sha256": repository.sha(report)},
            **{key: value for key, value in composition.items() if key != "findings"},
        },
        "encoded": {
            "derived": {
                key: derived[key]
                for key in ("rows", "ground", "tolerance", "band_audit", "ground_check")
            }
        },
        "findings": findings,
        "verdict": "refuse" if findings else "pass",
    }
    repository.write(edition.caption_equivalence, record)
    print(json.dumps({"verdict": record["verdict"], "findings": len(findings), "derived": True}))
    if findings:
        msg = f"The {edition.code} derived pair is not current: " + "; ".join(findings)
        raise PictureError(msg)
    return record
