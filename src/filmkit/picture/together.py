"""Make both editions' pictures with one command: `render-picture --language all`.

Each edition's picture is made by a child of its own, `python -m filmkit.produce render-picture
--language <code>` with the options given, so each writes its own receipt and its own duration
record and refuses as it does alone. The two captioned pictures, and the two uncaptioned ones
where they are rendered (with `--native`, or for a film of another capture than software),
render side by side: the renderer runs one render at a time
for a user account, so exactly those two children are given the renderer's own switch,
`HYPERFRAMES_RENDER_LOCK=off`, which each receipt records. Two derivations run in a row, since one
already uses every core. On a span of 7,200 UHD frames two renders at once took 172.3 s where two
in sequence took 228 to 236 s at sixteen workers, every frame identical, and sixteen workers each
gained nothing over eight each (17 November 2026), so each child keeps the host's worker count.

A child that fails does not stop the other. Once both have ended, the command refuses, naming
each edition whose picture was not made and its exit status.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time

import filmkit.picture.rendering as rendering
import filmkit.repository as repository
from filmkit.picture.derivation import uncaptioned_way
from filmkit.picture.rendering import PictureError
from filmkit.production import CODES

# Seconds a child has to stop its renderer after an interrupt before it is killed.
STOP_SECONDS = 30


def child_command(
    code: str, *, uncaptioned: bool, native: bool, deadline: float | None
) -> list[str]:
    """One edition's command: the production command's own action with the options given."""
    command = [sys.executable, "-B", "-m", "filmkit.produce", "render-picture", "--language", code]
    command += ["--uncaptioned"] if uncaptioned else []
    command += ["--native"] if native else []
    return command + ([] if deadline is None else ["--deadline", str(deadline)])


def side_by_side(*, uncaptioned: bool, native: bool) -> bool:
    """Whether the two pictures are rendered, and so made at once; derivations run in a row. The
    uncaptioned pictures are rendered when `--native` asks for it or the film's capture is not
    the deriving one (`filmkit.picture.derivation.uncaptioned_way`)."""
    return not uncaptioned or uncaptioned_way(native=native)["way"] == "rendered"


def stop(children: list[subprocess.Popen]) -> None:
    """Interrupt the children that still run, so that each stops its renderer, and wait."""
    for child in children:
        if child.poll() is None:
            child.send_signal(signal.SIGINT)
    for child in children:
        try:
            child.wait(timeout=STOP_SECONDS)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def render_all(
    *, uncaptioned: bool = False, native: bool = False, deadline: float | None = None
) -> dict[str, int]:
    """Make both editions' captioned pictures, or their uncaptioned ones: each edition's exit
    status. Refused, once both children have ended, when either did not exit 0."""
    together = side_by_side(uncaptioned=uncaptioned, native=native)
    environment = {**os.environ, repository.ROOT_VARIABLE: str(repository.ROOT)}
    if together:
        environment[rendering.RENDER_LOCK] = "off"
    started = time.monotonic()
    children: list[subprocess.Popen] = []
    exits: dict[str, int] = {}
    try:
        for code in CODES:
            command = child_command(code, uncaptioned=uncaptioned, native=native, deadline=deadline)
            child = subprocess.Popen(
                command, cwd=repository.ROOT, env=environment, stdin=subprocess.DEVNULL
            )
            children.append(child)
            if not together:
                exits[code] = child.wait()
        for code, child in zip(CODES, children, strict=True):
            exits[code] = child.wait()
    except BaseException:
        stop(children)
        raise
    report = {"pictures": "uncaptioned" if uncaptioned else "captioned", "side_by_side": together}
    print(json.dumps({**report, "exits": exits, "seconds": round(time.monotonic() - started, 1)}))
    failed = [f"{code} (exit {status})" for code, status in exits.items() if status != 0]
    if failed:
        msg = f"Not every edition's {report['pictures']} picture was made: {', '.join(failed)}"
        raise PictureError(msg)
    return exits
