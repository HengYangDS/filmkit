"""Stop the child processes a command started, so that none outlives it.

A command that starts children and waits for them stops them when its wait is cut short: by an
interrupt, by a failure of its own, or by a request to end (SIGTERM), which `terminable` turns
into the exception `Terminated` while the children run. `filmkit.picture.together` does so for
two editions' pictures, `filmkit.narration.processes` for a narration's shares, and
`filmkit.narration.narrate` for each of its steps (`run`).

`stop` asks each child that still runs to end, by a signal to the child or, for a child that
leads a session of its own, to its whole process group, so that what the child started ends
with it. It waits for them and kills what has not ended after `STOP_SECONDS`. While it stops the
children, a further interrupt or request to end is held, so a second signal cannot leave half of
them running; it is raised once they have ended. A command holds signals the same way while it
starts a child (`held`), so that a signal which arrives in that moment finds the child already
among those it will stop.

A process that is killed outright (SIGKILL) runs none of this, and its children outlive it. A
child that leads its own session is not reached by a signal to its parent's process group
either, so a caller that must end such a command at once asks it to end first.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# Seconds a child has to end after it is asked to, before it is killed.
STOP_SECONDS = 30


class Terminated(BaseException):
    """The command was asked to end (SIGTERM) while it waited for its children."""


@contextlib.contextmanager
def terminable() -> Iterator[None]:
    """Raise `Terminated` in the block when the process is asked to end, so that the block's own
    handling stops its children. Outside the main thread, where a process sets no handler, the
    block runs as it is."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def asked(number: int, _frame: object) -> None:
        raise Terminated(number)

    earlier = signal.signal(signal.SIGTERM, asked)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_DFL if earlier is None else earlier)


@contextlib.contextmanager
def held() -> Iterator[None]:
    """Hold an interrupt or a request to end that arrives in the block and raise it after the
    block, by the handlers that stood before; outside the main thread the block runs as it is."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    arrived: list[int] = []
    numbers = (signal.SIGINT, signal.SIGTERM)
    earlier = {n: signal.signal(n, lambda number, _frame: arrived.append(number)) for n in numbers}
    try:
        yield
    finally:
        for number, handler in earlier.items():
            signal.signal(number, signal.SIG_DFL if handler is None else handler)
        for number in dict.fromkeys(arrived):
            signal.raise_signal(number)


# What signalling a process group raises when no process of it can take a signal any more: the
# group is gone, or, on macOS, it holds only processes that have ended and await their parent.
GONE = (ProcessLookupError, PermissionError)


def group_exists(group: int) -> bool:
    """Whether any process of a process group of this command's own still runs."""
    try:
        os.killpg(group, 0)
    except GONE:
        return False
    return True


def send(child: subprocess.Popen, number: int, *, group: bool) -> None:
    """Send a signal to a child, or to the process group it leads; one that has ended gets none."""
    with contextlib.suppress(*GONE):
        if group:
            os.killpg(child.pid, number)
        else:
            child.send_signal(number)


def stop(
    children: list[subprocess.Popen],
    asking: int = signal.SIGINT,
    *,
    groups: bool = False,
    seconds: float | None = None,
) -> None:
    """Ask the children that still run to end and wait for them; kill what has not ended after
    `seconds`, `STOP_SECONDS` unless given. With `groups` each child leads a session of its own:
    both signals go to its whole process group, and the wait is for the group. An interrupt or a
    request to end that arrives meanwhile is held until every child has ended."""
    with held():
        running = [child for child in children if child.poll() is None]
        for child in running:
            send(child, asking, group=groups)
        ends = time.monotonic() + (STOP_SECONDS if seconds is None else seconds)
        late = []
        for child in running:
            try:
                child.wait(timeout=max(0.0, ends - time.monotonic()))
            except subprocess.TimeoutExpired:
                late.append(child)
        while groups and time.monotonic() < ends and any(group_exists(c.pid) for c in running):
            time.sleep(0.05)
        for child in running:
            if any(child is other for other in late) or (groups and group_exists(child.pid)):
                send(child, signal.SIGKILL, group=groups)
            child.wait()


def run(command: list[str], *, cwd: Path) -> None:
    """Run one child to its end. A wait that is cut short asks the child to end (SIGTERM) and
    waits for it before the cause goes on, twice as long as the child may itself wait for its own
    children; an exit other than 0 raises `subprocess.CalledProcessError`, as `subprocess.run`
    does with `check`."""
    child = None
    try:
        # A signal that arrives while the child starts is acted on once the child is held here.
        with held():
            child = subprocess.Popen(command, cwd=cwd)
        status = child.wait()
    except BaseException:
        if child is not None:
            stop([child], signal.SIGTERM, seconds=2 * STOP_SECONDS)
        raise
    if status != 0:
        raise subprocess.CalledProcessError(status, command)
