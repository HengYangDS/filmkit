"""Stage, render and validate an edition's two pictures against their recorded inputs.

A stage is one ignored workspace: the picture's data (film.json: the edition's timeline with its
render offset and edition), the composition's script and style, the declared fonts, and the document
that inlines the same data, script and style into the composition's template for the checks that
paint it in a browser; stage.json binds it to the current inputs. A render draws the complete UHD
stage with the engine's renderer (`filmkit.picture.renderer`), a native canvas with no browser, and
records a receipt; validation binds the picture to that receipt, the stage and the current inputs,
and refuses another renderer's picture. What differs raises `PictureError`, as does a film whose
installed canvas is not the engine's version. This module owns the stage, the render commands and
the validation; what draws is the renderer's, which imports nothing from here.

Each edition has two pictures (`production.Edition.rendered`), the captioned one and the
uncaptioned one, which is derived from the captioned one (`filmkit.picture.derivation`) unless
a native render is asked for; rendered, its data is the same timeline with no captions, drawn
with the same settings to its own stage, file and receipt. Each stage record and receipt names
its picture; one that names none is the captioned picture's.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.media as media
import filmkit.released as released
import filmkit.repository as repository
import filmkit.sources as sources
from filmkit.film import FILM
from filmkit.picture import encoding, faces, renderer, template
from filmkit.picture.errors import PictureError
from filmkit.production import RENDITIONS, STAGE_PAGE, STAGE_RECORD
from filmkit.repository import content_sha, read, sha, write
from filmkit.specification import DURATION, FPS

if TYPE_CHECKING:
    from filmkit.production import Edition, Rendered

# The composition that draws the picture, as a path below the repository root.
COMPOSITION = Path("picture")
# The composition's script, whose SHA-256 the packages and reviews record.
COMPOSITION_SCRIPT = COMPOSITION / "film.js"
# The renderer document's template and the style it inlines.
TEMPLATE = Path(template.TEMPLATE)
STYLE = COMPOSITION / template.STYLESHEET
SOURCE_MANIFEST = sources.MANIFEST
# The picture is rendered at the UHD master's frame; a stage may take either film's frame.
PICTURE_SIZE = RENDITIONS["uhd"].size
STAGE_SIZES = {rendition.size for rendition in RENDITIONS.values()}
# The picture's data as the stage holds it for the renderer: what the document inlines.
DATA = "film.json"


def read_bound(path: str | Path) -> tuple[dict, str]:
    """A JSON file's value and the SHA-256 of the exact bytes it was read from."""
    data = (repository.ROOT / path).read_bytes()
    return json.loads(data), content_sha(data)


def below_root(path: str | Path) -> str:
    """A path as the stage records it: below the repository root, or as given when relative."""
    return str(Path(path).relative_to(repository.ROOT)) if Path(path).is_absolute() else str(path)


def follows_script(timeline: dict, script: dict) -> bool:
    """Whether a timeline keeps its script's declarations and each segment's authored fields."""
    segments = timeline.get("segments", [])
    return (
        all(
            timeline.get(key) == value
            for key, value in script.items()
            if key not in {"segments", "timing_state"}
        )
        and len(segments) == len(script["segments"])
        and all(
            all(actual.get(key) == value for key, value in source.items())
            for source, actual in zip(script["segments"], segments, strict=True)
        )
    )


def candidate_picture_inputs(edition: Edition) -> tuple[dict, dict]:
    """Bind a reviewable current render without claiming artistic acceptance.

    Returns each input's path and SHA-256, and the timeline parsed from the bytes its hash
    binds; each JSON input is read once. The timeline must keep its script's authored fields
    and the soundtrack must be the one its assembly records for that script.
    """
    script, script_sha256 = read_bound(edition.script)
    timeline, timeline_sha256 = read_bound(edition.timeline)
    if not follows_script(timeline, script):
        msg = "Current candidate timeline differs from its authored script"
        raise PictureError(msg)
    assembly, assembly_sha256 = read_bound(edition.audio_assembly)
    soundtrack_sha256 = sha(edition.soundtrack)
    if (
        assembly.get("script_sha256") != script_sha256
        or assembly.get("soundtrack_sha256") != soundtrack_sha256
    ):
        msg = "Current candidate soundtrack differs from its native assembly"
        raise PictureError(msg)
    bound = {
        "source_manifest": (SOURCE_MANIFEST, sha(SOURCE_MANIFEST)),
        "script": (edition.script, script_sha256),
        "timeline": (edition.timeline, timeline_sha256),
        "assembly": (edition.audio_assembly, assembly_sha256),
        "soundtrack": (edition.soundtrack, soundtrack_sha256),
    }
    inputs = {
        key: {"path": below_root(path), "sha256": digest} for key, (path, digest) in bound.items()
    }
    return inputs, timeline


def substitute(html: str, old: str, new: str, count: int = 1) -> str:
    """Replace a template pattern, refused unless it occurs exactly `count` times."""
    found = html.count(old)
    if found != count:
        msg = f"The picture template holds {old!r} {found} times, not {count}"
        raise PictureError(msg)
    return html.replace(old, new)


def film_data(
    edition: Edition, start: float, *, timeline: dict | None = None, captions: bool = True
) -> str:
    """The picture's data as JSON, the document's `window.FILM`: the timeline with its render
    offset and edition, and with `captions` False no captions."""
    data = dict(timeline) if timeline is not None else read(edition.timeline)
    data["render_offset"] = start
    data["edition"] = edition.code
    if not captions:
        data["captions"] = []
    return json.dumps(data, ensure_ascii=False)


def language(edition: Edition) -> str:
    """The language tag an edition's picture is drawn in, in the document and on the canvas."""
    return "en" if edition.code == "en" else "zh-CN"


def declared_faces() -> list[dict]:
    """The faces the film's stylesheet declares from its declared fonts
    (`filmkit.picture.faces.held`): what the audits measure and the renderer registers."""
    style = (repository.ROOT / STYLE).read_text(encoding="utf-8")
    return faces.held(style, list(FILM.picture.fonts))


def picture_html(
    edition: Edition,
    duration: int,
    width: int,
    height: int,
    start: float,
    *,
    timeline: dict | None = None,
    captions: bool = True,
) -> str:
    """Derive the exact picture document from current authored inputs.

    The template's language, duration and frame are set before the data, style and script are
    inlined, so no substitution reaches inlined text. The uncaptioned picture's document, with
    `captions` False, inlines the timeline with no captions.
    """
    data = film_data(edition, start, timeline=timeline, captions=captions)
    style = (repository.ROOT / STYLE).read_text(encoding="utf-8")
    script = (repository.ROOT / COMPOSITION_SCRIPT).read_text(encoding="utf-8")
    html = (repository.ROOT / TEMPLATE).read_text(encoding="utf-8")
    # One text for each anchor of the template, in the anchors' order (`template.ANCHORS`).
    texts = (
        f'<html lang="{language(edition)}">',
        f'data-duration="{duration}"',
        f'data-width="{width}"',
        f'data-height="{height}"',
        f'content="width={width}, height={height}"',
        f'width="{width}" height="{height}"',
        f'<div style="width:{width}px;height:{height}px" id="film"',
        "window.FILM=" + data + ";",
        "<style>" + style + "</style>",
        "<script>" + script + "</script>",
    )
    for (old, count), new in zip(template.ANCHORS, texts, strict=True):
        html = substitute(html, old, new, count)
    return html


def staged_members() -> tuple[tuple[str, Path], ...]:
    """The members a stage copies beside its data and document: each place in the stage and its
    source, a path from the film's root. The declared fonts follow below fonts/, in their order."""
    return (
        ("film.js", COMPOSITION_SCRIPT),
        ("film.css", STYLE),
        *((f"fonts/{Path(font).name}", Path(font)) for font in FILM.picture.fonts),
    )


def copy_member(stage: Path, path: str, source: Path) -> dict:
    """Copy one member into the stage and bind its copy to its source by SHA-256."""
    destination = stage / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repository.ROOT / source, destination)
    digest = sha(destination)
    if digest != sha(source):
        msg = f"Staged member differs: {path}"
        raise PictureError(msg)
    return {"source": str(source), "path": path, "sha256": digest}


def staged_faces() -> list[dict]:
    """The declared faces as a stage record names them: each family with its file's place."""
    return [{"family": face["family"], "path": face["path"]} for face in declared_faces()]


def stage_picture(
    edition: Edition,
    output: Path | None,
    duration: int,
    width: int,
    height: int,
    start: float = 0,
    *,
    captions: bool = True,
) -> None:
    """Materialize the authored picture, or with `captions` False the uncaptioned one, in one
    ignored native render workspace: its own stage unless `output` names another. The record
    names the faces the renderer registers, each family with its font's place in the stage, and
    the language the picture is drawn in."""
    renderer.require_renderer()
    if (
        not 1 <= duration <= DURATION
        or not 0 <= start <= DURATION - duration
        or (width, height) not in STAGE_SIZES
    ):
        msg = "Picture must use the admitted frame and duration contract"
        raise PictureError(msg)
    rendered = edition.rendered(captions)
    target = (output or rendered.stage).resolve()
    if not target.is_relative_to(repository.ROOT / "build"):
        msg = "Derived renderer inputs belong to this repository's build owner"
        raise PictureError(msg)
    inputs, timeline = candidate_picture_inputs(edition)
    drawn_with = staged_faces()
    document = picture_html(
        edition, duration, width, height, start, timeline=timeline, captions=captions
    )
    data = film_data(edition, start, timeline=timeline, captions=captions)
    target.mkdir(parents=True, exist_ok=True)
    (target / STAGE_PAGE).write_text(document, encoding="utf-8")
    (target / DATA).write_text(data, encoding="utf-8")
    members = [copy_member(target, path, source) for path, source in staged_members()]
    write(
        target / STAGE_RECORD,
        {
            "duration": duration,
            "start": start,
            "fps": FPS,
            "width": width,
            "height": height,
            "edition": edition.code,
            "language": language(edition),
            "faces": drawn_with,
            "picture": rendered.name,
            "script_sha256": inputs["script"]["sha256"],
            "template_sha256": sha(TEMPLATE),
            "timeline_sha256": inputs["timeline"]["sha256"],
            "inputs": inputs,
            "members": members,
        },
    )
    staged = {"stage": str(target), "picture": rendered.name, "members": len(members)}
    print(json.dumps(staged), flush=True)


def require_staged_members(members: object, stage: Path) -> None:
    """Refuse a stage unless it copies exactly the declared members, each as recorded."""
    declared = [(path, str(source)) for path, source in staged_members()]
    if (
        not isinstance(members, list)
        or [(member.get("path"), member.get("source")) for member in members] != declared
    ):
        msg = "The stage does not record exactly the declared members"
        raise PictureError(msg)
    for member in members:
        copy, source = stage / member["path"], repository.ROOT / member["source"]
        if not (
            copy.is_file() and source.is_file() and sha(copy) == sha(source) == member["sha256"]
        ):
            msg = f"Staged member differs from its record or source: {member['path']}"
            raise PictureError(msg)


def require_current_stage(edition: Edition, stage: Path, *, captions: bool = True) -> dict:
    """The stage's record, refused unless the stage holds the complete current UHD picture.

    The record must bind the current inputs, template, edition and picture, captioned or with
    `captions` False uncaptioned, over the whole duration at the UHD frame; the staged document
    and data must be the ones those sources derive now, and every copied member must match its
    record and its source.
    """
    record, document = stage / STAGE_RECORD, stage / STAGE_PAGE
    if not record.is_file() or not document.is_file():
        msg = f"No staged picture document and record in {repository.relative(stage)}"
        raise PictureError(msg)
    binding = read(record)
    inputs, timeline = candidate_picture_inputs(edition)
    expected = {
        "duration": DURATION,
        "start": 0,
        "fps": FPS,
        "width": PICTURE_SIZE[0],
        "height": PICTURE_SIZE[1],
        "edition": edition.code,
        "language": language(edition),
        "faces": staged_faces(),
        "script_sha256": inputs["script"]["sha256"],
        "template_sha256": sha(TEMPLATE),
        "timeline_sha256": inputs["timeline"]["sha256"],
        "inputs": inputs,
    }
    differing = [key for key, value in expected.items() if binding.get(key) != value]
    if recorded_picture(binding) != edition.rendered(captions).name:
        differing.append("picture")
    if differing:
        msg = f"The stage is not the complete current UHD picture: {', '.join(differing)} differ"
        raise PictureError(msg)
    derived = picture_html(
        edition, DURATION, *PICTURE_SIZE, 0, timeline=timeline, captions=captions
    )
    if document.read_bytes() != derived.encode("utf-8"):
        msg = "The staged document differs from the one the current sources derive"
        raise PictureError(msg)
    data, held = film_data(edition, 0, timeline=timeline, captions=captions), stage / DATA
    if not held.is_file() or held.read_bytes() != data.encode("utf-8"):
        msg = "The stage's picture data differs from what the current sources derive"
        raise PictureError(msg)
    require_staged_members(binding.get("members"), stage)
    return binding


def recorded_picture(record: dict) -> str:
    """The picture a stage record or receipt names; one that names none is the captioned one."""
    return record.get("picture", "captioned")


def require_completed_receipt(receipt: dict, stage: Path) -> None:
    """Refuse a receipt unless the renderer exited 0 within its deadline on the staged document."""
    document = stage / STAGE_PAGE
    if (
        receipt.get("exit") != 0
        or receipt.get("timed_out", True)
        or not document.is_file()
        or receipt.get("source_sha256") != sha(document)
    ):
        msg = "The render receipt records no completed render of the staged document"
        raise PictureError(msg)


def require_receipt_places(receipt: dict, stage: Path, picture: Path) -> None:
    """Refuse a receipt unless it rendered this stage to this picture, whose bytes it records."""
    command = receipt.get("command") or []
    output = command[command.index("--output") + 1] if "--output" in command[:-1] else ""
    staged = command[command.index("render") + 1] if "render" in command[:-1] else ""
    if not (
        recorded_at(staged, stage, repository.ROOT)
        and recorded_at(output, picture, repository.ROOT)
        and recorded_at(receipt.get("output_path", ""), picture, repository.ROOT)
    ):
        msg = "The render receipt names another stage or picture"
        raise PictureError(msg)
    if not picture.is_file() or receipt.get("output_sha256") != sha(picture):
        msg = "The rendered picture differs from its receipt"
        raise PictureError(msg)


def face_bindings() -> dict:
    """The stylesheet's and each declared font's SHA-256, from which the audits measure text."""
    return {
        "stylesheet_sha256": sha(repository.ROOT / STYLE),
        "fonts_sha256": {font: sha(repository.ROOT / font) for font in FILM.picture.fonts},
    }


def require_passing_gates(edition: Edition) -> None:
    """Refuse a render unless check-picture passed the edition's current picture.

    The gate record (`filmkit.picture.gates`) must have passed and must name the current
    composition's, timeline's, stylesheet's and declared fonts' SHA-256 and the running engine
    version.
    """
    path = edition.picture_gates
    if not path.is_file():
        msg = f"The {edition.code} picture has no gate record; run check-picture"
        raise PictureError(msg)
    record = read(path)
    current = {
        "composition_sha256": sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": sha(edition.timeline),
        "engine_version": released.version(),
        **face_bindings(),
    }
    stale = [key for key, value in current.items() if record.get(key) != value]
    if stale:
        msg = (
            f"The {edition.code} picture gate record binds another {', '.join(stale)}; "
            "run check-picture"
        )
        raise PictureError(msg)
    if record.get("verdict") != "pass":
        msg = f"The {edition.code} picture gate record did not pass; run check-picture"
        raise PictureError(msg)


def render_picture(edition: Edition, deadline: int, *, captions: bool = True) -> None:
    """Run the engine's renderer on the complete current stage and record its receipt.

    With `captions` False it renders the uncaptioned picture, from its own stage to its own file
    and receipt, with the same settings. The edition's picture must have passed check-picture as
    it stands. At the deadline the renderer's process group is sent SIGTERM and, after
    `renderer.STOP_GRACE_SECONDS`, SIGKILL. A render that does not exit 0 within its deadline, or
    whose stage changed meanwhile, raises `PictureError` after its receipt is written.
    """
    renderer.require_renderer()
    require_passing_gates(edition)
    rendered = edition.rendered(captions)
    require_current_stage(edition, rendered.stage, captions=captions)
    command = renderer.command(rendered.stage, rendered.file, FPS, renderer.spans())
    renderer.record_render(
        command, rendered.page, rendered.file, rendered.receipt, deadline, rendered.name
    )


def recorded_at(recorded: str, current: Path, root: Path) -> bool:
    """Whether a path a receipt recorded names the current place below the root.

    Receipts keep the absolute paths of the checkout that ran their command, so a
    checkout restored elsewhere is compared by the place below its own root.
    """
    place = current.relative_to(root).parts
    return Path(recorded).parts[-len(place) :] == place


def require_receipt_picture(receipt: dict, rendered: Rendered) -> None:
    """Refuse a receipt that names another picture than the one it is read for."""
    if recorded_picture(receipt) != rendered.name:
        held = recorded_picture(receipt)
        msg = f"The render receipt holds the {held} picture, not the {rendered.name}"
        raise PictureError(msg)


def validate_picture_binding(edition: Edition, receipt: dict, *, captions: bool = True) -> None:
    """Bind one complete native render, of the captioned picture or with `captions` False of the
    uncaptioned one, to the exact staged current inputs and the engine's renderer; a derived
    uncaptioned picture is bound by its derivation's receipt (`filmkit.picture.derivation`)."""
    if not captions and isinstance(receipt.get("derived"), dict):
        from filmkit.picture import derivation

        return derivation.validate_binding(edition, receipt)
    rendered = edition.rendered(captions)
    require_receipt_picture(receipt, rendered)
    # A receipt that names no canvas is another renderer's; one that names a canvas is asked
    # first whether its render completed, since a render that failed reports no text renderer.
    if not isinstance(receipt.get("renderer"), dict):
        renderer.require_receipt_renderer(receipt)
    require_completed_receipt(receipt, rendered.stage)
    renderer.require_receipt_renderer(receipt)
    require_current_stage(edition, rendered.stage, captions=captions)
    require_receipt_places(receipt, rendered.stage, rendered.file)


def validate_picture(edition: Edition, *, captions: bool = True) -> dict:
    """Bind the complete rendered picture, captioned or with `captions` False uncaptioned, to its
    current authored input; a derived uncaptioned picture to its derivation's receipt."""
    rendered = edition.rendered(captions)
    receipt = read(rendered.receipt)
    if not captions and isinstance(receipt.get("derived"), dict):
        from filmkit.picture import derivation

        return derivation.validate(edition, receipt)
    validate_picture_binding(edition, receipt, captions=captions)
    require_picture_media(rendered.file, "rendered")
    return receipt


def require_picture_media(
    path: Path, made: str, duration: int = DURATION, size: tuple[int, int] = PICTURE_SIZE
) -> None:
    """Refuse a picture, `made` rendered or derived, that is not the whole film at the pictures'
    frame, rate and size with a keyframe at every `encoding.KEYFRAME_SECONDS` and nowhere else."""
    frames = duration * FPS
    media.require_video(media.probe(path), frames=frames, fps=FPS, size=size, duration=duration)
    keyframes = media.video_cadence(path, frames, FPS)["keyframes"]
    if keyframes != list(range(0, frames, encoding.KEYFRAME_SECONDS * FPS)):
        grid = f"{encoding.KEYFRAME_SECONDS} s grid"
        msg = f"The {made} picture's keyframes leave the {grid}: {path.name}"
        raise PictureError(msg)
