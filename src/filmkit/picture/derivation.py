"""Derive an edition's uncaptioned picture from its captioned one, and prove what that relies on.

A picture is derived only for a film that declares `DERIVING_CAPTURE`, and only from a captioned
picture that the canvas build the engine pins drew: a derived picture relies on the renderer
drawing a stage the same way every time, which the engine qualifies for that build at each
release (`filmkit.picture.qualification`). The declaration dates from the browser's renders,
of which the software capture was the one a release qualified; no render reads it now.
`uncaptioned_way` says which way an edition's uncaptioned picture is made and why: derived
under that declaration from a picture of the pinned build, and rendered from its own stage
under any other declaration, from any other build or when `--native` asks for it. Each receipt
carries that answer as `uncaptioned`, and the comparison record repeats it.

The uncaptioned picture is the captioned picture with the rows of its caption band painted in the
ground: `derive_uncaptioned` encodes every frame of the valid captioned picture once more with
x264, the band's rows replaced by the ground as the captioned picture itself holds it, read from
one of its frames in YUV, so no colour is converted. The rows are the band the composition report
names, widened as a comparison widens it (`filmkit.picture.equivalence.excluded_rows`).

A derivation proves four things, in work it does anyway:

- before it encodes, the band audit (`picture/band-audit.mjs`) runs the composition headlessly at
  every thirtieth of a second and refuses a caption paint that leaves the rows or any other paint
  that reaches them, and lists the stretches in which no caption is painted;
- while it encodes, the same decode measures the captioned picture's band at every frame of those
  stretches, less four frames at each end, and the derivation refuses unless the lowest and the
  highest sample of each plane stand within 3 levels of the ground (`filmkit.picture.ground`);
- the same decode measures, at every frame of the film, the edge rows of the painted rows, which
  no caption reaches (`filmkit.picture.ground`), against the same ground and tolerance, so a
  ground that changes while a caption shows is refused;
- the same decode hands the captioned picture's band rows of every frame, as grey planes, to
  the rule the comparison of a rendered pair applies to a caption band
  (`filmkit.picture.faults.Band`): a sample far from both neighbouring frames while those agree
  is a one-frame fault of the captioned picture, in the text every viewer reads. That rule
  needs no twin, so a derived pair, whose comparison decodes nothing, keeps it.

A refusal leaves no uncaptioned picture or receipt in place and names `--native`, which renders
the uncaptioned stage instead (`filmkit.picture.rendering.render_picture`); a one-frame fault in
the band is the captioned picture's own, and its refusal (`BandFault`) names the command that
renders that picture again. The receipt, at the
uncaptioned picture's own place, says `derived` and binds the captioned picture, its receipt, the
composition, the timeline and the engine, with the rows, the ground and the proofs; validation
reads either kind of receipt (`validate`, `validate_binding`), and `compare_derived` writes the
comparison record of a derived pair from the receipt, decoding no picture. Packaging asks
`film_source` which picture each film reads: the 1080p uncaptioned film of a derived pair is
painted and scaled from the captioned picture in one pass.

Usage: python -m filmkit.produce render-picture --language zh|en --uncaptioned [--native]
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.durations as durations
import filmkit.media as media
import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
import filmkit.picture.ground as ground_rows
import filmkit.picture.rendering as rendering
import filmkit.released as released
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.picture import renderer
from filmkit.picture.encoding import encoder
from filmkit.picture.errors import PictureError
from filmkit.picture.rendering import (
    COMPOSITION_SCRIPT,
    PICTURE_SIZE,
    require_receipt_picture,
    validate_picture,
)
from filmkit.specification import DURATION, FPS

if TYPE_CHECKING:
    from filmkit.production import Edition, Rendition

# The declared capture under which the uncaptioned picture is derived. It named the browser's
# capture a release qualified; a release now qualifies the pinned canvas build.
DERIVING_CAPTURE = "software"
# The work of a derivation, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/derivation")
ENCODER = encoder(FPS)  # the pictures' encoding, at the films' frame rate
# Seconds a derivation's encode may take.
DEADLINE = 7200
NATIVE = "render-picture --language {code} --uncaptioned --native"
# The proofs a derivation's receipt records, each with its verdict.
PROOFS = ("band_audit", "ground_check", "edge_check", "band_scan")


class BandFault(PictureError):
    """The captioned picture's caption band changes for one frame: a fault of that render, which
    no derivation repairs."""


def uncaptioned_way(edition: Edition | None = None, *, native: bool = False) -> dict:
    """How an uncaptioned picture is made, `derived` or `rendered`, and why: by the request, by
    the film's declared capture and, for an edition whose captioned picture is rendered, by the
    canvas its receipt names, since a release qualifies the pinned build alone."""
    declared = rendering.FILM.picture.capture
    qualified = f"{DERIVING_CAPTURE} capture, which the engine's release qualifies"
    if native:
        return {"way": "rendered", "reason": "a render of its own stage was asked for"}
    if declared != DERIVING_CAPTURE:
        reason = f"the film declares {declared} capture, and a picture is derived only under "
        return {"way": "rendered", "reason": reason + qualified}
    captioned = edition.rendered(True).receipt if edition else None
    drawn = repository.read(captioned) if captioned and captioned.is_file() else None
    why = renderer.unqualified(drawn) if drawn else None
    if why:
        reason = "the captioned picture is no render by the pinned build that the engine's release "
        return {"way": "rendered", "reason": f"{reason}qualifies: {why}"}
    return {"way": "derived", "reason": f"the film declares {qualified}"}


def render_uncaptioned(edition: Edition, deadline: float, *, asked: bool = False) -> dict:
    """Render the edition's uncaptioned picture from its own stage and state in its receipt why
    it is rendered and not derived; the receipt.

    Every render of an uncaptioned picture goes through here, the command's and a repair's, so
    every rendered receipt carries the statement and the comparison record after it. The reason
    is the film's capture, or, with `asked` or for a film whose pictures are otherwise derived,
    that a render was asked for: a rendered picture of such a film exists only because one was.
    """
    way = uncaptioned_way(edition, native=asked)
    if way["way"] == "derived":
        way = uncaptioned_way(native=True)
    rendering.render_picture(edition, deadline, captions=False)
    path = edition.rendered(False).receipt
    receipt = {**repository.read(path), "uncaptioned": way}
    repository.write(path, receipt)
    return receipt


def source_bindings(edition: Edition) -> dict:
    """What a derivation binds: the captioned picture and its receipt, the composition, the
    timeline and the engine."""
    captioned = edition.rendered(True)
    return {
        "source_sha256": repository.sha(captioned.file),
        "source_receipt_sha256": repository.sha(captioned.receipt),
        "composition_sha256": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": version(released.ENGINE),
    }


def band_audit(edition: Edition, rows: tuple[int, int], work: Path) -> dict:
    """Run the band audit on the painted rows, given in the composition's frame; its report.

    Refused, naming the first escape or intrusion and `--native`, unless the rows hold caption
    paints and nothing else at every instant.
    """
    scale = PICTURE_SIZE[1] / equivalence.COMPOSITION_HEIGHT
    report = work / "band-audit.json"
    painted_rows = [f"{row / scale:g}" for row in rows]
    arguments = [str(edition.timeline), *painted_rows, str(ground_rows.AUDIT_FPS)]
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


def band_crop(size: tuple[int, int], rows: tuple[int, int]) -> str:
    """The filter that keeps the band's rows of a picture of `size`."""
    return f"crop={size[0]}:{rows[1] - rows[0]}:0:{rows[0]}"


def painted(
    source: str, size: tuple[int, int], rows: tuple[int, int], ground: dict, out: str
) -> str:
    """The filter graph from the stream `source` to `out` that sets the band's rows to the ground:
    the rows are cropped, every sample of each plane set to the ground's, and laid back over."""
    paint = "lutyuv=" + ":".join(f"{name}={ground[name]}" for name in ground_rows.PLANES)
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
    edges: tuple[int, int] = (0, 0),
) -> list[str]:
    """The FFmpeg command of a derivation: one decode of the captioned picture feeds the encode,
    with the band's rows set to the ground, the measure of the band at the frames given, whose
    lowest and highest samples go to `stats`, a path without a colon or a quote, with `edges`
    the measure of the edge rows at every frame, which goes beside it (`edge_stats`), and the
    band's rows of every frame as grey planes on its standard output, for the band's one-frame
    scan (`filmkit.picture.ground.BandScan`)."""
    measured = any(edges)
    graph = (
        f"[0:v:0]split={4 if measured else 3}[picture][measure][scan]"
        f"{'[edge]' if measured else ''};"
        f"{painted('picture', size, rows, ground, 'derived')};"
        f"[measure]select='{ground_rows.selection(frames)}',{band_crop(size, rows)},signalstats,"
        f"metadata=mode=print:file={stats}[measured];"
        f"[scan]{ground_rows.BandScan(size, rows).filter}[band]"
    )
    if measured:
        graph += ";" + ground_rows.edge_filter("edge", size, rows, edges, edge_stats(stats))
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
        *(["-map", "[edges]", "-f", "null", os.devnull] if measured else []),
        "-map",
        "[band]",
        *faults.RAW,
    ]


def edge_stats(stats: Path) -> Path:
    """Where a derivation's decode writes the edge rows' measures, beside the band's."""
    return stats.with_name("edge-stats.txt")


def derive(
    source: Path,
    target: Path,
    size: tuple[int, int],
    rows: tuple[int, int],
    frames: list[tuple[int, int]],
    work: Path,
    deadline: float = DEADLINE,
    *,
    edges: tuple[int, int] = (0, 0),
    code: str | None = None,
) -> dict:
    """Derive `target` from `source` with the rows painted, in the work folder, and check what
    the same decode proves: the ground, the command, its seconds and the checks' results, the
    band's at the frames given, with `edges` the edge rows' at every frame, and the band's
    one-frame scan of the source at every frame (`filmkit.picture.ground`). `target` is written
    only once the checks passed; a refusal removes the work's picture. A one-frame change in the
    source's band is a `BandFault`, which names the captioned render of the edition `code`."""
    work.mkdir(parents=True, exist_ok=True)
    partial, stats = work / "derived.mp4", work / "band-stats.txt"
    for earlier in (partial, stats, edge_stats(stats)):
        earlier.unlink(missing_ok=True)
    with durations.phase("ground"):
        ground = ground_rows.read_ground(source, rows, size, frames[0][0])
    relative = Path(repository.relative(stats))
    command = derive_command(source, partial, size, rows, ground, frames, relative, edges)
    count = int(media.video_stream(media.probe(source))["nb_frames"])
    scan, run = ground_rows.BandScan(size, rows), durations.current()
    started = time.monotonic()
    try:
        with durations.phase("encode"):
            failed = "The derivation's encode failed after {read} of {count} frames"
            log = work / "derive.log"
            faults.decode(command, scan.length, log, count, scan.add, deadline, failed)
        seconds = time.monotonic() - started
        if run is not None:
            # The judging of the band's rows, which runs while the encode does.
            run.add("band-scan", scan.seconds)
        scanned = scan.report(count)
        if scanned["changes"]:
            found = "; ".join(ground_rows.band_findings(scanned, code))
            msg = f"The captioned picture's caption band changes for one frame: {found}"
            raise BandFault(msg)
        with durations.phase("ground-check"):
            check = ground_rows.ground_check(stats, frames, ground)
            edge = (
                ground_rows.edge_check(edge_stats(stats), ground, ground_rows.GROUND_TOLERANCE, FPS)
                if any(edges)
                else None
            )
    except (PictureError, subprocess.TimeoutExpired):
        partial.unlink(missing_ok=True)
        raise
    finally:
        stats.unlink(missing_ok=True)
        edge_stats(stats).unlink(missing_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial.replace(target)
    made = {"ground": ground, "command": command, "elapsed_seconds": seconds, "check": check}
    made["band_scan"] = scanned
    return made if edge is None else {**made, "edge_check": {"rows": list(edges), **edge}}


def require_derived_media(path: Path) -> None:
    """Refuse a derived picture that is not the whole film on the pictures' keyframe grid
    (`filmkit.picture.rendering.require_picture_media`)."""
    rendering.require_picture_media(path, "derived", DURATION, PICTURE_SIZE)


def derive_uncaptioned(edition: Edition, deadline: float = DEADLINE) -> dict:
    """Derive the edition's uncaptioned picture from its valid captioned picture and write its
    receipt; an earlier uncaptioned picture and receipt are removed first, so a refusal leaves
    none in place. Refused for a film whose declared capture is not the deriving one."""
    way = uncaptioned_way(edition)
    if way["way"] != "derived":
        msg = f"The {edition.code} uncaptioned picture is not derived: {way['reason']}"
        raise PictureError(msg)
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
    frames = ground_rows.free_frames(audit["free"])
    scale = PICTURE_SIZE[1] / equivalence.COMPOSITION_HEIGHT
    edges = ground_rows.edge_rows(rows, audit["caption_rows"], scale)
    unmeasured = ground_rows.unmeasured_sides(rows, edges, PICTURE_SIZE[1])
    if not frames or unmeasured:
        why = (
            "shows a caption at every instant, so its band's ground cannot be read"
            if not frames
            else f"leaves no row free of captions at {unmeasured} edge of the painted rows, "
            "beyond which the picture continues"
        )
        msg = f"The {edition.code} film {why}; render the uncaptioned picture with {native}"
        raise PictureError(msg)
    started = datetime.now(UTC)
    try:
        made = derive(
            captioned.file,
            rendered.file,
            PICTURE_SIZE,
            rows,
            frames,
            work,
            deadline,
            edges=edges,
            code=edition.code,
        )
    except BandFault:
        # The fault is the captioned picture's: its refusal names that render, not a native one.
        raise
    except PictureError as error:
        msg = f"{error}; render the uncaptioned picture with {native}"
        raise PictureError(msg) from error
    try:
        with durations.phase("media"):
            require_derived_media(rendered.file)
        if made["edge_check"]["frames"] != DURATION * FPS:
            msg = f"The edge rows were measured at {made['edge_check']['frames']} frames"
            raise PictureError(msg)
        if source_bindings(edition) != bound:
            msg = "The captioned picture, the composition or the timeline changed meanwhile"
            raise PictureError(msg)
    except (PictureError, media.MediaError):
        rendered.file.unlink(missing_ok=True)
        raise
    report = work / "band-audit.json"
    receipt = {
        "picture": rendered.name,
        "uncaptioned": way,
        "derived": {
            "from": captioned.name,
            **bound,
            "band": composition["band"],
            "rows": list(rows),
            "ground": made["ground"],
            "tolerance": ground_rows.GROUND_TOLERANCE,
            "band_audit": {
                "report": {"path": repository.relative(report), "sha256": repository.sha(report)},
                "instants": audit["instants"],
                "caption_instants": audit["caption_instants"],
                "stretches": len(audit["free"]),
                "verdict": audit["verdict"],
            },
            "ground_check": made["check"],
            "edge_check": made["edge_check"],
            "band_scan": made["band_scan"],
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
    picture, composition, timeline and engine, with its proofs passed; the captioned picture
    must itself be bound to its current stage."""
    rendered = edition.rendered(False)
    require_receipt_picture(receipt, rendered)
    derived = receipt["derived"]
    again = f"run render-picture --language {edition.code} --uncaptioned"
    declared = rendering.FILM.picture.capture
    if declared != DERIVING_CAPTURE:
        msg = (
            f"The {edition.code} uncaptioned picture is derived, and the film declares {declared} "
            f"capture, under which it is rendered; {again}"
        )
        raise PictureError(msg)
    # The picture it was derived from must itself stand: its stage, with the stylesheet, fonts,
    # template, script and soundtrack that stage binds, as a rendered uncaptioned picture's must.
    captioned = repository.read(edition.rendered(True).receipt)
    rendering.validate_picture_binding(edition, captioned)
    stale = [key for key, value in source_bindings(edition).items() if derived.get(key) != value]
    if stale:
        msg = f"The derived picture's receipt binds another {', '.join(stale)}; {again}"
        raise PictureError(msg)
    proofs = [derived.get(key, {}) for key in PROOFS]
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
        "uncaptioned": receipt.get("uncaptioned", {"way": "derived"}),
        "composition": {
            "report": {"path": repository.relative(report), "sha256": repository.sha(report)},
            **{key: value for key, value in composition.items() if key != "findings"},
        },
        "encoded": {
            "derived": {key: derived[key] for key in (*("rows", "ground", "tolerance"), *PROOFS)}
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
