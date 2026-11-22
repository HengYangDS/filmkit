"""The engine's renderer: a native canvas that draws a staged picture, with no browser.

This module owns what draws: the build the engine pins, what a film installs and what a render
loaded, the command, the spans, the run of a renderer and its receipt. The render commands and
the validation of a picture (`filmkit.picture.rendering`) call it; it imports neither.

A render runs the engine's Node module `native-canvas.mjs` from the film's copy of the engine's
tools (`filmkit.tools.stage_tools`) on a stage. The module runs the film's composition unchanged
on a canvas of the `@napi-rs/canvas` package the film's npm packages install, registers the
faces the stage's record names, sets the canvas's text renderer to the one the command names,
and pipes each frame to an x264 encoder with the pictures' encoding
(`filmkit.picture.encoding`). A picture is drawn in `SPANS` spans of whole groups of frames,
one process each, joined by stream copy, or in the count `SPANS_VARIABLE` names for a
measurement; a draft in one process.

A render receipt (`record_render`) states what ran, read when it runs and never the engine's
constants: the canvas package with its version and the integrity npm recorded when it installed
it (`installed`), the native library the renderer's processes loaded, by its path and SHA-256,
with the package that holds it (`drawn_by`), the text renderer the canvas ran, the operating
system, and the renderer's own report: the spans, the frames it gave its encoders and
`drawn_sha256`, a digest of every drawn frame's pixels. Two draws of one stage state the same
digest; their encoded bytes are not compared.

The engine pins one build: the version `RENDERER_VERSION` of the package with the integrity
`INTEGRITY` names, and the native library `BINARY_SHA256` names, which is the one the binary
package of Apple silicon holds. A film that installs another version is refused
(`require_renderer`); a picture whose receipt names another package, version or text renderer
does not validate (`require_receipt_renderer`); and a receipt whose render loaded another
library, on any host, is no render by the build a release qualifies (`unqualified`), so no
picture is derived from it. The canvas's loader takes the library `NAPI_RS_NATIVE_LIBRARY_PATH`
names before the package's own; a render is not given that variable.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import filmkit.child_processes as child_processes
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture import encoding
from filmkit.picture.errors import PictureError
from filmkit.repository import sha, write

# The canvas package that draws the pictures, its manifest below the film's npm packages, and
# the version the engine draws with.
RENDERER_NAME = "@napi-rs/canvas"
RENDERER_PACKAGE = Path(RENDERER_NAME) / "package.json"
# What the engine was released on states that package once (`filmkit.released`). An engine
# whose record does not state it fails there when this module is imported: the last line of the
# traceback names the record and the command that writes it.
RELEASED = released.npm_package(RENDERER_NAME)
RENDERER_VERSION = RELEASED["version"]
# The package that holds the native library on the one platform a release qualifies.
BINARY_PACKAGE = "@napi-rs/canvas-darwin-arm64"
# The integrity npm records for the pinned version of the canvas, as the record states it. The
# binary package's own integrity is the lock's alone: the engine pins that package's native
# library by its bytes, the SHA-256 below.
INTEGRITY = {RENDERER_NAME: RELEASED["integrity"]}
BINARY_SHA256 = "3300b17d4de4ad678e08f29d9016a8d16915afe4876c7097d292d48fd622ef70"
# What npm records of the packages it installed, below the film's npm packages.
INSTALLED = Path(".package-lock.json")
# The variable by which the canvas's loader takes another native library than its package's.
LIBRARY_VARIABLE = "NAPI_RS_NATIVE_LIBRARY_PATH"
# The canvas's text renderer: the host's own (CoreText on macOS), which draws text as the films'
# released pictures show it. The package's default, `portable`, draws the same labels lighter.
TEXT_RENDERER = "system"
# The engine's Node module that draws and encodes a stage, below the engine's tools.
MODULE = "picture/native-canvas.mjs"
# The spans a picture is drawn in, one process and one encoder each, unless SPANS_VARIABLE names
# another count for a measurement, and a draft's one. Four drew whole films of 36,000 to 90,000
# UHD frames in 139 to 350 s on a host of 18 cores (18 November 2026); eight drew 36,000 frames
# in 135.5 s, no faster for twice the processes. The count changes no frame: the digest of the
# drawn frames is the same for every count.
SPANS_VARIABLE = "FILMKIT_RENDER_SPANS"
SPANS = 4
DRAFT_SPANS = 1
# Seconds a render may take, and its process group has to exit after SIGTERM before SIGKILL.
DEADLINE = 10800
STOP_GRACE_SECONDS = 10


def held_json(path: Path) -> dict:
    """The JSON object a file holds, or none where it cannot be read or holds no object."""
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def recorded(name: str | None) -> dict:
    """What npm recorded when it installed a package below the film's npm packages."""
    packages = held_json(repository.node_modules() / INSTALLED).get("packages")
    entry = packages.get(f"node_modules/{name}") if isinstance(packages, dict) and name else None
    return entry if isinstance(entry, dict) else {}


def installed() -> dict:
    """The canvas a film installs: the package, the version its manifest states and the
    integrity npm recorded when it installed it. What the packages do not state is None."""
    manifest = held_json(repository.node_modules() / RENDERER_PACKAGE)
    return {
        "package": RENDERER_NAME,
        "version": manifest.get("version"),
        "integrity": recorded(RENDERER_NAME).get("integrity"),
    }


def require_renderer() -> None:
    """Refuse a film whose npm packages install another canvas version than the engine's."""
    version = installed()["version"]
    if version != RENDERER_VERSION:
        found = f"{RENDERER_NAME} {version}" if version else f"no {RENDERER_NAME}"
        msg = f"The film installs {found}; the engine draws with {RENDERER_NAME} {RENDERER_VERSION}"
        raise PictureError(msg)


def drawn_by(report: dict) -> dict:
    """The canvas of a render as its receipt names it: what the film installs, the text
    renderer the render's processes ran, and the native library they loaded: its path, its
    SHA-256, the package that holds it with the version that package's manifest states, and
    the integrity npm recorded for that package. What a render did not report is None."""
    loaded = report.get("binary") if isinstance(report.get("binary"), dict) else {}
    package = loaded.get("package")
    binary = {
        "package": package,
        "version": loaded.get("version"),
        "integrity": recorded(package).get("integrity"),
        "path": loaded.get("path"),
        "sha256": loaded.get("sha256"),
    }
    return {**installed(), "binary": binary, "text_renderer": report.get("text_renderer")}


def build(drawn: dict) -> dict:
    """A receipt's canvas without the place its library was loaded from: what two renders by
    one build state alike in any checkout."""
    binary = drawn.get("binary") if isinstance(drawn.get("binary"), dict) else {}
    return {**drawn, "binary": {key: value for key, value in binary.items() if key != "path"}}


def unqualified(receipt: dict) -> str | None:
    """Why a render's receipt does not show that the pinned canvas build drew its picture with
    the host's text renderer, or None when it names that build. The reason names what differs."""
    drawn = receipt.get("renderer")
    if not isinstance(drawn, dict):
        return "its receipt names no canvas"
    named = (drawn.get("package"), drawn.get("version"), drawn.get("integrity"))
    if named != (RENDERER_NAME, RENDERER_VERSION, INTEGRITY[RENDERER_NAME]):
        return (
            f"it was drawn by {named[0]} {named[1]} with the integrity {named[2]}, and the "
            f"engine pins {RENDERER_NAME} {RENDERER_VERSION} with {INTEGRITY[RENDERER_NAME]}"
        )
    binary = drawn.get("binary") if isinstance(drawn.get("binary"), dict) else {}
    if binary.get("sha256") != BINARY_SHA256:
        loaded = f"{binary.get('package')} {binary.get('version')}"
        return (
            f"its canvas loaded the native library of {loaded} with the SHA-256 "
            f"{binary.get('sha256')}, and the engine pins that of {BINARY_PACKAGE} "
            f"{RENDERER_VERSION}, {BINARY_SHA256}"
        )
    if drawn.get("text_renderer") != TEXT_RENDERER:
        return f"its text was drawn by the {drawn.get('text_renderer')} renderer"
    return None


def require_receipt_renderer(receipt: dict) -> None:
    """Refuse a receipt of another renderer than the engine's: one that names no canvas, as the
    receipt of a browser's render does, another package or version, or another text renderer."""
    drawn = receipt.get("renderer")
    drawn = drawn if isinstance(drawn, dict) else {}
    named = (drawn.get("package"), drawn.get("version"), drawn.get("text_renderer"))
    if named != (RENDERER_NAME, RENDERER_VERSION, TEXT_RENDERER):
        found = f"{named[0]} {named[1]} with {named[2]} text" if drawn else "no native canvas"
        msg = (
            f"The picture's receipt names {found}; the engine draws with {RENDERER_NAME} "
            f"{RENDERER_VERSION} with {TEXT_RENDERER} text: render the picture again"
        )
        raise PictureError(msg)


def operating_system() -> dict:
    """The host's operating system as a receipt states it: the text renderer is the host's."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "macos": platform.mac_ver()[0] or None,
    }


def spans() -> int:
    """The spans a picture is drawn in: `SPANS`, or what `SPANS_VARIABLE` names for a
    measurement, a positive whole number."""
    named = os.environ.get(SPANS_VARIABLE)
    if not named:
        return SPANS
    if not (named.isascii() and named.isdigit() and int(named) > 0):
        msg = f"{SPANS_VARIABLE} names {named!r}, which is no positive whole number of spans"
        raise PictureError(msg)
    return int(named)


def launcher() -> list[str]:
    """What starts the renderer: Node on the film's copy of the engine's module."""
    import filmkit.tools as tools

    node = shutil.which("node")
    if node is None:
        msg = "No node on PATH; render in the film's Mise environment"
        raise PictureError(msg)
    return [node, str(tools.stage_tools() / MODULE)]


def command(stage: Path, output: Path, fps: int, drawn_in: int) -> list[str]:
    """The renderer's command for a stage: the pictures' encoding at a frame rate, a group of
    frames for every `encoding.KEYFRAME_SECONDS`, the host's text renderer, drawn in `drawn_in`
    spans. The spans' folder and the report stand beside the stage, outside the edition's
    artifacts."""
    work = stage.with_name(stage.name + "-spans")
    return [
        *launcher(),
        "render",
        str(stage),
        "--output",
        str(output),
        "--fps",
        str(fps),
        "--group",
        str(encoding.KEYFRAME_SECONDS * fps),
        "--encoder",
        json.dumps(encoding.encoder(fps)),
        "--text-renderer",
        TEXT_RENDERER,
        "--spans",
        str(drawn_in),
        "--work",
        str(work),
        "--report",
        str(work.with_name(work.name + ".json")),
    ]


def stop_process_group(process: subprocess.Popen) -> None:
    """End a renderer that has not been reaped and the rest of its process group, and reap it:
    SIGTERM, then SIGKILL after the grace (`filmkit.child_processes.stop`, which holds a further
    signal until the group has ended)."""
    child_processes.stop([process], signal.SIGTERM, groups=True, seconds=STOP_GRACE_SECONDS)


def run_renderer(command: list[str], deadline: float) -> tuple[int | None, bool]:
    """Run the renderer to its exit or deadline: its exit status, and whether it timed out.

    The renderer runs in its own session with its input closed, so stopping it reaches every
    process it started, and without the variable that names another native library to the
    canvas's loader. Its end is waited for without reaping it, so that its number is still its
    own when what is left of its group is ended, which is done after every run: after a failed
    exit that is its remaining spans and encoders. A wait that is cut short by a request to
    end, an interrupt, SIGTERM or a hang-up, which is an exception while the renderer runs
    (`filmkit.child_processes`), stops the group before the cause propagates, undisturbed by a
    further request.
    """
    environment = {name: value for name, value in os.environ.items() if name != LIBRARY_VARIABLE}
    # From a first request to end until the renderer's group is ended, every further one is
    # dropped: each stop lies inside the block that takes the requests.
    with child_processes.terminable():
        process = None
        try:
            # A request that arrives while the renderer starts waits until it is held here.
            with child_processes.held():
                process = subprocess.Popen(
                    command,
                    cwd=repository.ROOT,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )
            timed_out = not child_processes.ended(process, deadline)
        except BaseException:
            if process is not None:
                stop_process_group(process)
            raise
        stop_process_group(process)
        return (None if timed_out else process.returncode), timed_out


def take_report(command: list[str]) -> dict:
    """The report a renderer command names, removed where it stands: the JSON object the
    renderer wrote, or none where the command names no report or the file holds none."""
    if "--report" not in command[:-1]:
        return {}
    path = Path(command[command.index("--report") + 1])
    report = held_json(path)
    path.unlink(missing_ok=True)
    return report


def record_render(
    command: list[str], page: Path, output: Path, receipt: Path, deadline: float, picture: str
) -> dict:
    """Run a renderer command on a stage to its exit or deadline and write its receipt; `page`
    is the page the stage holds, whose SHA-256 the receipt binds.

    The receipt names the picture, the command, the canvas that drew it with the native library
    and the text renderer its processes report, the operating system, and what else the
    renderer reports: the spans, the frames it gave its encoders and the digest of the drawn
    frames. A render that does not exit 0 within its deadline, that reports no drawn frames, or
    whose staged page changed meanwhile, raises `PictureError` after its receipt is written.
    """
    source = sha(page)
    # A report left by a run that was cut short is not this run's.
    take_report(command)
    started = datetime.now(UTC)
    exit_code, timed_out = run_renderer(command, deadline)
    report = take_report(command)
    record = {
        "picture": picture,
        "command": command,
        "renderer": drawn_by(report),
        "operating_system": operating_system(),
        "spans": report.get("spans"),
        "frames": report.get("frames"),
        "drawn_sha256": report.get("drawn_sha256"),
        "exit": exit_code,
        "timed_out": timed_out,
        "deadline_seconds": deadline,
        "started_at": started.isoformat(),
        "elapsed_seconds": (datetime.now(UTC) - started).total_seconds(),
        "source_sha256": source,
        "output_path": str(output),
        "output_sha256": sha(output) if output.is_file() else None,
    }
    write(receipt, record)
    print(json.dumps({key: record[key] for key in ("exit", "timed_out", "elapsed_seconds")}))
    if exit_code != 0 or timed_out or source != sha(page):
        msg = "Native picture render did not complete from the current stage"
        raise PictureError(msg)
    if not isinstance(record["drawn_sha256"], str):
        msg = "The renderer exited 0 and reported no drawn frames"
        raise PictureError(msg)
    return record
