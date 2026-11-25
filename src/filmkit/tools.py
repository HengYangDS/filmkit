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

Inside `outside_the_film` the modules are copied into a temporary folder outside the film instead,
beside a link to the film's npm packages, so that a run writes nothing below the film's root, as
`filmkit check --read-only` asks.

A run waits for its tool. When the wait is cut short, as by an interrupt of the command, the
tool is asked to end (SIGTERM) and waited for, so that it ends what it started itself, as a tool
that drives a browser closes it, and it is killed only when it has not ended after
`STOP_SECONDS` (`filmkit.child_processes.stop`).

The nodes that run a tool, the geometry check and the cover check, call `run` with the arguments
their edition derives (`filmkit.graph.chain`); the engine's other modules call it as they need.
The module has no command line.
"""

from __future__ import annotations

import contextlib
import contextvars
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

import filmkit.child_processes as child_processes
import filmkit.picture.browser as picture_browser
import filmkit.picture.renderer as picture_renderer
import filmkit.released as released
import filmkit.repository as repository
from filmkit.graph import opens
from filmkit.picture import metrics

# The engine's Node modules, which the package carries below this module's folder, and the data
# they read beside themselves: the classes of characters (`filmkit.languages`).
PACKAGE = Path(__file__).resolve().parent
COPIED = ("**/*.mjs", "languages/scripts.json")
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
    "anchor-reads": "picture/anchor-reads.mjs",
}
# The copies, below the film's root, in a folder for each engine version.
CACHE = picture_browser.TOOL_CACHE / released.ENGINE
# Seconds a tool has to end, once the command's wait for it was cut short and it was asked to,
# before it is killed.
STOP_SECONDS = 20
# The tools that run the composition headlessly, which measure text by the film's declared faces.
MEASURING = ("frame-audit", "motion-audit", "detail-audit", "caption-equivalence", "band-audit")


class ToolError(RuntimeError):
    """A tool refused the film, in its own words or by its exit status; a tool the host lacks
    is `child_processes.MissingToolError`."""


# The folder the tools are copied into while `outside_the_film` holds.
_OUTSIDE: contextvars.ContextVar[Path | None] = contextvars.ContextVar("outside", default=None)


@contextlib.contextmanager
def outside_the_film():
    """Copy the tools into a temporary folder outside the film while the block runs, beside a
    link to the film's npm packages, from which their imports resolve; the folder is removed
    after it."""
    with tempfile.TemporaryDirectory(prefix="filmkit-tools-") as folder:
        (Path(folder) / "node_modules").symlink_to(repository.node_modules())
        token = _OUTSIDE.set(Path(folder) / "tools")
        try:
            yield
        finally:
            _OUTSIDE.reset(token)


def stage_tools() -> Path:
    """Copy the engine's Node modules and the data they read into the film's tool cache, or into
    the folder `outside_the_film` holds, and return the copies' folder.

    A copy whose bytes equal the package's stays untouched; any other is replaced whole.
    """
    cache = _OUTSIDE.get() or repository.ROOT / CACHE / released.version()
    for module in sorted({path for named in COPIED for path in PACKAGE.glob(named)}):
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
        raise child_processes.MissingToolError(msg)
    script = stage_tools() / TOOLS[tool]
    variables = {
        **os.environ,
        **(environment or {}),
        "FILM_CHROMIUM_PATH": str(picture_browser.browser_path()),
        **opens.node_options(),
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


if __name__ == "__main__":
    from filmkit.retired import refuse

    refuse(__spec__.name)
