"""Run one of the engine's Node tools for the film the engine builds, with the film's packages.

The engine carries its Node tools as package data. A run copies every module, keeping its
folder, into build/runtime/tool-cache/filmkit/<version>/ below the film, replacing any copy whose
bytes differ from the package's, and runs the named tool from that copy with Node at the film's
root: its imports resolve from the film's npm packages and its paths from the film. The tools
check the film's picture and players, so each first refuses a renderer version other than the one
the engine renders with, and a browser check runs the browser the supply installs. The frame,
motion and detail audits, the caption equivalence and the band audit measure text by the advance
widths of the film's declared faces (`filmkit.picture.metrics`), which a run names to them in
`FILMKIT_TEXT_METRICS` unless the caller names its own table.

A run waits for its tool. When the wait is cut short, as by an interrupt of the command, the
tool is asked to end (SIGTERM) and waited for, so that it ends what it started itself, as a tool
that drives a browser closes it, and it is killed only when it has not ended after
`STOP_SECONDS` (`filmkit.child_processes.stop`).

A refusal exits with status 1 and "<tool>: <reason>" on standard error; otherwise the command
exits with the tool's own status. The two checks that a film's build runs from the command line,
the geometry check and the cover check (`BUILD_RUNS`), write a duration record
(`filmkit.durations`) for the edition of this film that their arguments name, by its stage or
its folder of evidence or artifacts, so that they count in its build's time. No other run
writes one: an audit run by hand for a diagnosis is no command of a build.

Usage: python -m filmkit.tools <tool> [arguments]
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import shutil
import signal
import subprocess
import tempfile
from importlib.metadata import version
from pathlib import Path

import filmkit.child_processes as child_processes
import filmkit.durations as durations
import filmkit.picture.browser as picture_browser
import filmkit.picture.renderer as picture_renderer
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture import metrics
from filmkit.picture.errors import PictureError
from filmkit.production import CODES, STAGE

# The engine's Node modules, which the package carries below this module's folder.
PACKAGE = Path(__file__).resolve().parent
# The tools a film runs by name, as paths below the package; the other modules are libraries
# that the tools import.
TOOLS = {
    "geometry-check": "picture/geometry-check.mjs",
    "frame-audit": "picture/frame-audit.mjs",
    "motion-audit": "picture/motion-audit.mjs",
    "detail-audit": "picture/detail-audit.mjs",
    "caption-equivalence": "picture/caption-equivalence.mjs",
    "band-audit": "picture/band-audit.mjs",
    "player-check": "delivery/player-check.mjs",
    "whole-turns": "picture/whole-turns.mjs",
}
# The copies, below the film's root, in a folder for each engine version.
CACHE = picture_browser.TOOL_CACHE / released.ENGINE
# The runs a film's build makes from the command line, which alone write a duration record: the
# tool with the words its arguments begin with, and the record's name. Every other run, of
# another tool or of the player check in another mode, is taken for a run by hand.
BUILD_RUNS = {
    ("geometry-check",): "geometry-check",
    ("player-check", "cover"): "player-check-cover",
}
# Where a tool's argument names an edition: its stage, by the name `production.STAGE` gives it,
# or its folder of evidence or artifacts, by the last name `repository` gives each.
EDITION = "|".join(CODES)
STAGED = f"(?P<stage>{EDITION})".join(map(re.escape, STAGE.split("{code}")))
FOLDERS = "|".join(re.escape(place.name) for place in (repository.EVIDENCE, repository.ARTIFACTS))
EDITION_PLACE = re.compile(rf"(?:^|/)(?:{STAGED}[^/]*|(?:{FOLDERS})/(?P<folder>{EDITION}))(?=/|$)")
# Seconds a tool has to end, once the command's wait for it was cut short and it was asked to,
# before it is killed.
STOP_SECONDS = 20
# The tools that run the composition headlessly, which measure text by the film's declared faces.
MEASURING = ("frame-audit", "motion-audit", "detail-audit", "caption-equivalence", "band-audit")


class ToolError(RuntimeError):
    """The film's tools cannot run."""


class ToolFailed(Exception):
    """A tool exited with another status than 0, which its run's duration record states as not
    completed and the command passes on."""

    def __init__(self, status: int) -> None:
        super().__init__(status)
        self.status = status


def stage_tools() -> Path:
    """Copy the engine's Node modules into the film's tool cache and return the copies' folder.

    A copy whose bytes equal the package's stays untouched; any other is replaced whole.
    """
    cache = repository.ROOT / CACHE / version(released.ENGINE)
    for module in sorted(PACKAGE.rglob("*.mjs")):
        copy = cache / module.relative_to(PACKAGE)
        if copy.is_file() and copy.read_bytes() == module.read_bytes():
            continue
        copy.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=copy.parent, delete=False) as partial:
            partial.write(module.read_bytes())
        Path(partial.name).replace(copy)
    return cache


def run(
    tool: str,
    arguments: list[str],
    *,
    environment: dict | None = None,
    stdout: Path | None = None,
) -> int:
    """Run a tool from its copy at the film's root and return its exit status.

    `environment` adds variables to the tool's environment, and `stdout` names a file that
    receives the tool's standard output instead of the caller's. A tool that runs the
    composition headlessly is given the table of the film's declared faces unless the caller
    names one. A wait that is cut short asks the tool to end and waits for it, at most
    `STOP_SECONDS`, before what cut it short goes on. The run takes no request to end while it
    waits for its tool; while the tool starts and while it is being ended, a further request
    is deferred until the tool is held or has ended or been killed (`child_processes.held`).
    """
    picture_renderer.require_renderer()
    node = shutil.which("node")
    if node is None:
        msg = "No node on PATH; run the tools in the film's Mise environment"
        raise ToolError(msg)
    script = stage_tools() / TOOLS[tool]
    variables = {
        **os.environ,
        **(environment or {}),
        "FILM_CHROMIUM_PATH": str(picture_browser.browser_path()),
    }
    if tool in MEASURING and metrics.VARIABLE not in variables:
        variables[metrics.VARIABLE] = str(metrics.current_table())
    with contextlib.ExitStack() as stack:
        output = None if stdout is None else stack.enter_context(stdout.open("w"))
        tool_process = None
        try:
            # A request that arrives while the tool starts is acted on once the tool is held here.
            with child_processes.held():
                tool_process = subprocess.Popen(
                    [node, str(script), *arguments],
                    cwd=repository.ROOT,
                    env=variables,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                )
            return tool_process.wait()
        except BaseException:
            # The tool ends what it started, a browser it drives, from its own handling of the
            # request; it is killed only when that has not ended it.
            if tool_process is not None:
                child_processes.stop([tool_process], signal.SIGTERM, seconds=STOP_SECONDS)
            raise


def edition_of(arguments: list[str]) -> str | None:
    """The edition of this film a tool's arguments name: the one whose stage, evidence or
    artifacts folder their paths lie in, or None when they name none or both. A path is read
    from the film's root, where the tools run; one that leaves the root names no edition."""
    named = set()
    for argument in arguments:
        place = Path(os.path.normpath(repository.ROOT / argument))
        if place.is_relative_to(repository.ROOT):
            found = EDITION_PLACE.finditer(place.relative_to(repository.ROOT).as_posix())
            named |= {match["stage"] or match["folder"] for match in found}
    return named.pop() if len(named) == 1 else None


def recorded(tool: str, arguments: list[str]) -> tuple[str, str] | None:
    """The edition and the name of the duration record a run writes: for a run of `BUILD_RUNS`
    whose arguments name one edition of this film, and None for every other run."""
    words = (tool, *arguments)
    name = next((BUILD_RUNS[run] for run in BUILD_RUNS if words[: len(run)] == run), None)
    code = edition_of(arguments) if name else None
    return (code, name) if code and name else None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m filmkit.tools", description=__doc__.splitlines()[0]
    )
    parser.add_argument("tool", choices=sorted(TOOLS))
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="the tool's own arguments")
    options = parser.parse_args(argv)
    build_run = recorded(options.tool, options.arguments)
    code, name = build_run or (CODES[0], options.tool)
    try:
        # A check of an edition's build is recorded as a command of that build.
        with durations.run(code, name, record=build_run is not None):
            status = run(options.tool, options.arguments)
            if status != 0:
                raise ToolFailed(status)
    except ToolFailed as failed:
        raise SystemExit(failed.status) from None
    except (PictureError, ToolError) as error:
        msg = f"{options.tool}: {error}"
        raise SystemExit(msg) from None
    raise SystemExit(status)


if __name__ == "__main__":
    main()
