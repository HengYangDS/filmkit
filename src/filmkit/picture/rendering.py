"""Stage, render and validate the picture against its recorded inputs.

A stage is one ignored workspace holding the renderer document, which inlines the edition's
timeline and the composition's script and style into the composition's template, beside the
copied timeline engine and fonts; its stage.json binds it to the current inputs. A render runs
the locked HyperFrames renderer on the complete UHD stage with the supplied browser, telemetry,
update checks and self-installs off, and records a receipt; validation binds the rendered
picture to that receipt, the stage and the current inputs. A stage, render or receipt that
differs from this contract raises `PictureError`, as does a film whose installed renderer is not
the version the engine renders with.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import signal
import subprocess
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.media as media
import filmkit.repository as repository
import filmkit.sources as sources
from filmkit.film import FILM
from filmkit.production import RENDITIONS
from filmkit.repository import content_sha, read, sha, write
from filmkit.specification import DURATION, FPS

if TYPE_CHECKING:
    from filmkit.production import Edition

# The composition that draws the picture, as a path below the repository root.
COMPOSITION = Path("picture")
# The composition's script, whose SHA-256 the packages and reviews record.
COMPOSITION_SCRIPT = COMPOSITION / "film.js"
# The renderer document's template and the style it inlines.
TEMPLATE = COMPOSITION / "index.html"
STYLE = COMPOSITION / "film.css"
SOURCE_MANIFEST = sources.MANIFEST
# The picture is rendered at the UHD master's frame; a stage may take either film's frame.
PICTURE_SIZE = (RENDITIONS["uhd"].width, RENDITIONS["uhd"].height)
STAGE_SIZES = {(rendition.width, rendition.height) for rendition in RENDITIONS.values()}
# The timeline engine a stage copies, below the film's npm packages.
TIMELINE_ENGINE = Path("gsap/dist/gsap.min.js")
# Seconds a renderer's process group has to exit after SIGTERM before SIGKILL ends it.
STOP_GRACE_SECONDS = 10
# The locked renderer's command and package manifest, below the film's npm packages, and the
# renderer version the engine renders with.
RENDERER = Path(".bin/hyperframes")
RENDERER_PACKAGE = Path("hyperframes/package.json")
RENDERER_VERSION = "0.9.6"
# The tools and models the supply task installs, below the repository root.
TOOL_CACHE = Path("build/runtime/tool-cache")
# The browser build that the locked renderer pins, as the supply task installs it, and the
# SHA-256 of its executable.
BROWSER = ("chrome-headless-shell", "152.0.7977.30")
BROWSER_EXECUTABLE = "chrome-headless-shell-mac-arm64/chrome-headless-shell"
BROWSER_SHA256 = "ed7c5c6aff7cc4dd88ee7746c0df97f08a454180b62b7063fc961ba42e10b6a1"


class PictureError(ValueError):
    """A stage, render or receipt differs from what the picture's contract requires."""


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


def picture_html(
    edition: Edition,
    duration: int,
    width: int,
    height: int,
    start: float,
    *,
    timeline: dict | None = None,
) -> str:
    """Derive the exact native renderer document from current authored inputs.

    The template's language, duration and frame are set before the timeline, style and
    script are inlined, so no substitution reaches inlined text.
    """
    data = dict(timeline) if timeline is not None else read(edition.timeline)
    data["render_offset"] = start
    data["edition"] = edition.code
    style = (repository.ROOT / STYLE).read_text(encoding="utf-8")
    script = (repository.ROOT / COMPOSITION_SCRIPT).read_text(encoding="utf-8")
    html = (repository.ROOT / TEMPLATE).read_text(encoding="utf-8")
    for old, new, count in (
        (
            '<html lang="zh-CN">',
            '<html lang="en">' if edition.code == "en" else '<html lang="zh-CN">',
            1,
        ),
        ('data-duration="1200"', f'data-duration="{duration}"', 2),
        ('data-width="1920"', f'data-width="{width}"', 1),
        ('data-height="1080"', f'data-height="{height}"', 1),
        ('content="width=1920, height=1080"', f'content="width={width}, height={height}"', 1),
        ('width="1920" height="1080"', f'width="{width}" height="{height}"', 1),
        ('<div id="film"', f'<div style="width:{width}px;height:{height}px" id="film"', 1),
        ("/* FILM_DATA */", "window.FILM=" + json.dumps(data, ensure_ascii=False) + ";", 1),
        ('<link rel="stylesheet" href="film.css">', "<style>" + style + "</style>", 1),
        ('<script src="film.js"></script>', "<script>" + script + "</script>", 1),
    ):
        html = substitute(html, old, new, count)
    return html


def require_renderer() -> None:
    """Refuse a film whose npm packages install another renderer version than the engine's."""
    manifest = repository.node_modules() / RENDERER_PACKAGE
    try:
        installed = json.loads(manifest.read_text())["version"]
    except (OSError, ValueError, KeyError, TypeError):
        installed = None
    if installed != RENDERER_VERSION:
        found = f"HyperFrames {installed}" if installed else "no HyperFrames"
        msg = f"The film installs {found}; the engine renders with HyperFrames {RENDERER_VERSION}"
        raise PictureError(msg)


def npm_package(path: Path) -> Path:
    """A file of the film's npm packages, as a path from the film's root."""
    return Path(os.path.relpath(repository.node_modules() / path, repository.ROOT))


def staged_members() -> tuple[tuple[str, Path], ...]:
    """The members a stage copies beside its document: each place in the stage and its source.

    Sources are paths from the film's root; the timeline engine's leaves the root when the
    film's npm packages lie above it. The declared fonts follow below fonts/, in their order.
    """
    return (
        ("film.js", COMPOSITION_SCRIPT),
        ("film.css", STYLE),
        ("gsap.min.js", npm_package(TIMELINE_ENGINE)),
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


def stage_picture(
    edition: Edition,
    output: Path | None,
    duration: int,
    width: int,
    height: int,
    start: float = 0,
) -> None:
    """Materialize the authored picture in one ignored native render workspace."""
    require_renderer()
    if (
        not 1 <= duration <= DURATION
        or not 0 <= start <= DURATION - duration
        or (width, height) not in STAGE_SIZES
    ):
        msg = "Picture must use the admitted frame and duration contract"
        raise PictureError(msg)
    target = (output or edition.picture_stage).resolve()
    if not target.is_relative_to(repository.ROOT / "build"):
        msg = "Derived renderer inputs belong to this repository's build owner"
        raise PictureError(msg)
    inputs, timeline = candidate_picture_inputs(edition)
    document = picture_html(edition, duration, width, height, start, timeline=timeline)
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(document, encoding="utf-8")
    members = [copy_member(target, path, source) for path, source in staged_members()]
    write(
        target / "stage.json",
        {
            "duration": duration,
            "start": start,
            "fps": FPS,
            "width": width,
            "height": height,
            "edition": edition.code,
            "script_sha256": inputs["script"]["sha256"],
            "template_sha256": sha(TEMPLATE),
            "timeline_sha256": inputs["timeline"]["sha256"],
            "inputs": inputs,
            "members": members,
        },
    )
    print(json.dumps({"stage": str(target), "members": len(members)}), flush=True)


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


def require_current_stage(edition: Edition, stage: Path) -> dict:
    """The stage's record, refused unless the stage holds the complete current UHD picture.

    The record must bind the current inputs, template and edition over the whole duration at
    the UHD frame; the staged document must be the one those sources derive now, and every
    copied member must match its record and its source.
    """
    record, document = stage / "stage.json", stage / "index.html"
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
        "script_sha256": inputs["script"]["sha256"],
        "template_sha256": sha(TEMPLATE),
        "timeline_sha256": inputs["timeline"]["sha256"],
        "inputs": inputs,
    }
    differing = [key for key, value in expected.items() if binding.get(key) != value]
    if differing:
        msg = f"The stage is not the complete current UHD picture: {', '.join(differing)} differ"
        raise PictureError(msg)
    derived = picture_html(edition, DURATION, *PICTURE_SIZE, 0, timeline=timeline)
    if document.read_bytes() != derived.encode("utf-8"):
        msg = "The staged document differs from the one the current sources derive"
        raise PictureError(msg)
    require_staged_members(binding.get("members"), stage)
    return binding


def require_completed_receipt(receipt: dict, stage: Path) -> None:
    """Refuse a receipt unless the renderer exited 0 within its deadline on the staged document."""
    document = stage / "index.html"
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
    if not (
        len(command) > 2
        and command[1] == "render"
        and recorded_at(command[2], stage, repository.ROOT)
        and recorded_at(output, picture, repository.ROOT)
        and recorded_at(receipt.get("output_path", ""), picture, repository.ROOT)
    ):
        msg = "The render receipt names another stage or picture"
        raise PictureError(msg)
    if not picture.is_file() or receipt.get("output_sha256") != sha(picture):
        msg = "The rendered picture differs from its receipt"
        raise PictureError(msg)


def stop_process_group(process: subprocess.Popen) -> None:
    """End a process and the rest of its group: SIGTERM, then SIGKILL after the grace."""
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    ends = time.monotonic() + STOP_GRACE_SECONDS
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=STOP_GRACE_SECONDS)
    while time.monotonic() < ends and group_exists(process.pid):
        time.sleep(0.05)
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def group_exists(group: int) -> bool:
    """Whether any process of a process group is still running."""
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return False
    return True


def supplied_browser() -> Path:
    """The executable of the browser build that the supply task installs."""
    product, version = BROWSER
    browsers = repository.ROOT / TOOL_CACHE / "browsers"
    return browsers / product / f"mac_arm-{version}" / BROWSER_EXECUTABLE


def browser_path() -> Path:
    """The browser renders and checks run: FILM_CHROMIUM_PATH, or the supplied build."""
    named = os.environ.get("FILM_CHROMIUM_PATH")
    return Path(named) if named else supplied_browser()


def renderer_environment() -> dict[str, str]:
    """The renderer's environment: the browser and a font cache of the repository's own.

    Telemetry, update checks and self-installs are off.
    """
    return {
        **os.environ,
        "HYPERFRAMES_NO_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
        "HYPERFRAMES_NO_UPDATE_CHECK": "1",
        "HYPERFRAMES_NO_AUTO_INSTALL": "1",
        "HYPERFRAMES_BROWSER_PATH": str(browser_path()),
        "HYPERFRAMES_FONT_CACHE_DIR": str(repository.ROOT / TOOL_CACHE / "hyperframes/fonts"),
    }


def run_renderer(command: list[str], deadline: float) -> tuple[int | None, bool]:
    """Run the renderer to its exit or deadline: its exit status, and whether it timed out.

    The renderer runs in its own session with its input closed, so stopping it reaches every
    process it started; a failed exit stops remaining workers, and an interrupted wait stops
    the group before the interruption propagates.
    """
    process = subprocess.Popen(
        command,
        cwd=repository.ROOT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=renderer_environment(),
    )
    try:
        exit_code = process.wait(timeout=deadline)
    except subprocess.TimeoutExpired:
        stop_process_group(process)
        return None, True
    except BaseException:
        stop_process_group(process)
        raise
    if exit_code != 0:
        stop_process_group(process)
    return exit_code, False


def require_passing_gates(edition: Edition) -> None:
    """Refuse a render unless check-picture passed the edition's current picture.

    The gate record (`filmkit.picture.gates`) must have passed and must name the current
    composition's and timeline's SHA-256 and the running engine version.
    """
    path = edition.picture_gates
    if not path.is_file():
        msg = f"The {edition.code} picture has no gate record; run check-picture"
        raise PictureError(msg)
    record = read(path)
    current = {
        "composition_sha256": sha(repository.ROOT / COMPOSITION_SCRIPT),
        "timeline_sha256": sha(edition.timeline),
        "engine_version": version("filmkit"),
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


def render_picture(edition: Edition, deadline: int) -> None:
    """Run the locked renderer on the complete current stage and record its receipt.

    The edition's picture must have passed check-picture as it stands. At the deadline the
    renderer's process group is sent SIGTERM and, after `STOP_GRACE_SECONDS`, SIGKILL. A
    render that does not exit 0 within its deadline, or whose stage changed meanwhile, raises
    `PictureError` after its receipt is written.
    """
    require_renderer()
    require_passing_gates(edition)
    stage = edition.picture_stage
    require_current_stage(edition, stage)
    picture = edition.picture
    command = [
        str(repository.node_modules() / RENDERER),
        "render",
        str(stage),
        "--output",
        str(picture),
        "--fps",
        str(FPS),
        "--quality",
        "looks",
        "--crf",
        "14",
        "--workers",
        "8",
        "--gpu",
        "--browser-gpu",
        "--no-low-memory-mode",
        "--experimental-fast-capture",
        "--strict",
    ]
    source = sha(stage / "index.html")
    started = datetime.now(UTC)
    exit_code, timed_out = run_renderer(command, deadline)
    receipt = {
        "command": command,
        "exit": exit_code,
        "timed_out": timed_out,
        "deadline_seconds": deadline,
        "started_at": started.isoformat(),
        "elapsed_seconds": (datetime.now(UTC) - started).total_seconds(),
        "source_sha256": source,
        "output_path": str(picture),
        "output_sha256": sha(picture) if picture.is_file() else None,
    }
    write(edition.render_receipt, receipt)
    print(json.dumps({key: receipt[key] for key in ("exit", "timed_out", "elapsed_seconds")}))
    if exit_code != 0 or timed_out or source != sha(stage / "index.html"):
        msg = "Native picture render did not complete from the current stage"
        raise PictureError(msg)


def recorded_at(recorded: str, current: Path, root: Path) -> bool:
    """Whether a path a receipt recorded names the current place below the root.

    Receipts keep the absolute paths of the checkout that ran their command, so a
    checkout restored elsewhere is compared by the place below its own root.
    """
    place = current.relative_to(root).parts
    return Path(recorded).parts[-len(place) :] == place


def validate_picture_binding(edition: Edition, receipt: dict) -> None:
    """Bind one complete native render to the exact staged current inputs."""
    stage = edition.picture_stage
    require_completed_receipt(receipt, stage)
    require_current_stage(edition, stage)
    require_receipt_places(receipt, stage, edition.picture)


def validate_picture(edition: Edition) -> dict:
    """Bind the complete native capture to its current authored input."""
    picture, frames = edition.picture, DURATION * FPS
    receipt = read(edition.render_receipt)
    validate_picture_binding(edition, receipt)
    media.require_video(
        media.probe(picture), frames=frames, fps=FPS, size=PICTURE_SIZE, duration=DURATION
    )
    media.video_cadence(picture, frames, FPS)
    return receipt
