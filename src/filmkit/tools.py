"""Run one of the engine's Node tools for the film the engine builds, with the film's packages.

The engine carries its Node tools as package data. A run copies every module, keeping its
folder, into build/runtime/tool-cache/filmkit/<version>/ below the film, replacing any copy whose
bytes differ from the package's, and runs the named tool from that copy with Node at the film's
root: its imports resolve from the film's npm packages and its paths from the film. The tools
check the film's picture and players, so each first refuses a renderer version other than the one
the engine renders with, and a browser check runs the browser that the renderer uses.

A refusal exits with status 1 and "<tool>: <reason>" on standard error; otherwise the command
exits with the tool's own status.

Usage: python -m filmkit.tools <tool> [arguments]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from importlib.metadata import version
from pathlib import Path

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError

# The engine's Node modules, which the package carries below this module's folder.
PACKAGE = Path(__file__).resolve().parent
# The tools a film runs by name, as paths below the package; the other modules are libraries
# that the tools import.
TOOLS = {
    "geometry-check": "picture/geometry-check.mjs",
    "frame-audit": "picture/frame-audit.mjs",
    "motion-audit": "picture/motion-audit.mjs",
    "player-check": "delivery/player-check.mjs",
}
# The copies, below the film's root, in a folder for each engine version.
CACHE = picture_rendering.TOOL_CACHE / "filmkit"


class ToolError(RuntimeError):
    """The film's tools cannot run."""


def stage_tools() -> Path:
    """Copy the engine's Node modules into the film's tool cache and return the copies' folder.

    A copy whose bytes equal the package's stays untouched; any other is replaced whole.
    """
    cache = repository.ROOT / CACHE / version("filmkit")
    for module in sorted(PACKAGE.rglob("*.mjs")):
        copy = cache / module.relative_to(PACKAGE)
        if copy.is_file() and copy.read_bytes() == module.read_bytes():
            continue
        copy.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=copy.parent, delete=False) as partial:
            partial.write(module.read_bytes())
        Path(partial.name).replace(copy)
    return cache


def run(tool: str, arguments: list[str]) -> int:
    """Run a tool from its copy at the film's root and return its exit status."""
    picture_rendering.require_renderer()
    node = shutil.which("node")
    if node is None:
        msg = "No node on PATH; run the tools in the film's Mise environment"
        raise ToolError(msg)
    script = stage_tools() / TOOLS[tool]
    environment = {**os.environ, "FILM_CHROMIUM_PATH": str(picture_rendering.browser_path())}
    completed = subprocess.run(
        [node, str(script), *arguments],
        cwd=repository.ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m filmkit.tools", description=__doc__.splitlines()[0]
    )
    parser.add_argument("tool", choices=sorted(TOOLS))
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="the tool's own arguments")
    options = parser.parse_args(argv)
    try:
        status = run(options.tool, options.arguments)
    except (PictureError, ToolError) as error:
        msg = f"{options.tool}: {error}"
        raise SystemExit(msg) from None
    raise SystemExit(status)


if __name__ == "__main__":
    main()
