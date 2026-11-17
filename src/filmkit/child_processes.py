"""End the child processes a command started when the command is asked to end, so that none
outlives it, and end the command itself with one line and the status a shell expects.

A command that starts children and waits for them ends them when its wait is cut short: by a
failure of its own, or by a request to end, which is an interrupt (SIGINT), a request to end
(SIGTERM) or a hang-up (SIGHUP), the last from a terminal that closes or a session that drops.
A signal the process ignores, as a hang-up under nohup, stays ignored.

Inside `terminable` the first request raises `Terminated` where the command stands, so that its
own handling ends its children. From that first arrival every further request is taken and
dropped: the command is ending, and a second signal, at whatever interval, neither ends it
early by its default action nor cuts the ending of its children short. `ending`, around a
command's whole run, then says in one line what stopped it and exits with 128 and the signal's
number, ignoring requests from there to the exit. Two different requests that both arrive
before the process has acted on either are handed to it lowest number first: it acts on that one.

Where a request must not interrupt, `held` defers the first one to the end of its block: while
a child starts, so that the request finds the child already among those to end, and while
children are being ended (`stop`), when the cause was not a request.

`stop` asks each child that still runs to end, by a signal to the child or, for a child that
leads a session of its own, to its whole process group, so that what the child started ends
with it; it waits for them and kills what has not ended after `STOP_SECONDS`.

`filmkit.picture.rendering` uses these for a renderer, `filmkit.narration.processes` for a
narration's shares, and `filmkit.narration.narrate` for each of its steps (`run`).

A process that is killed outright (SIGKILL) runs none of this, and its children outlive it. A
child that leads its own session is not reached by a signal to its parent's process group
either, so a caller that must end such a command asks it to end and waits.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# Seconds a child has to end after it is asked to, before it is killed.
STOP_SECONDS = 30
# Seconds between two looks at a child or a process group that is ending.
POLL_SECONDS = 0.05
# The signals that ask a command to end, with what each is called.
REQUESTS = {
    signal.SIGINT: "an interrupt",
    signal.SIGTERM: "a request to end (SIGTERM)",
    signal.SIGHUP: "a hang-up (SIGHUP)",
}


class Terminated(BaseException):
    """The command was asked to end, by the signal `number`, while it ran. `said` is what the
    code that ended the command's children says of it, where there is any."""

    def __init__(self, number: int, said: str = "") -> None:
        super().__init__(number, said)
        self.number, self.said = number, said

    @property
    def request(self) -> str:
        """What asked the command to end, in words."""
        return REQUESTS.get(self.number, f"signal {self.number}")

    @property
    def status(self) -> int:
        """The exit status a shell gives a command that this signal ended."""
        return 128 + self.number


class _Requests:
    """What the process knows of the requests to end it: how deep it stands in `terminable` and
    `held` blocks, the handlers that stood before, the request it acted on, one deferred in a
    `held` block, those dropped since, and whether it is leaving (`leave`)."""

    def __init__(self) -> None:
        self.depth, self.deferring = 0, 0
        self.earlier: dict[int, object] = {}
        self.acted: int | None = None
        self.deferred: int | None = None
        self.dropped: list[int] = []
        self.leaving = False


_REQUESTS = _Requests()


def receive(number: int, _frame: object = None) -> None:
    """Take a request to end, as the interpreter hands one over inside `terminable`: the first
    raises `Terminated`, or is deferred inside `held`; every later one is dropped."""
    if _REQUESTS.acted is not None or _REQUESTS.deferred is not None:
        _REQUESTS.dropped.append(number)
    elif _REQUESTS.deferring:
        _REQUESTS.deferred = number
    else:
        _REQUESTS.acted = number
        raise Terminated(number)


@contextlib.contextmanager
def terminable() -> Iterator[None]:
    """Take the requests to end that the process does not ignore, for the block: the first
    raises `Terminated` in it, and from then on every further one is dropped, to the end of the
    outermost such block, so that the block's own handling ends its children undisturbed. A
    block inside another adds nothing. Outside the main thread, where a process sets no
    handler, the block runs as it is."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    if _REQUESTS.depth == 0:
        _REQUESTS.acted, _REQUESTS.deferred, _REQUESTS.dropped = None, None, []
        for number in REQUESTS:
            if signal.getsignal(number) not in (signal.SIG_IGN, receive):
                _REQUESTS.earlier[number] = signal.signal(number, receive)
    _REQUESTS.depth += 1
    try:
        yield
    finally:
        _REQUESTS.depth -= 1
        if _REQUESTS.depth == 0 and not _REQUESTS.leaving:
            for number, handler in _REQUESTS.earlier.items():
                signal.signal(number, signal.SIG_DFL if handler is None else handler)
            _REQUESTS.earlier.clear()


@contextlib.contextmanager
def held() -> Iterator[None]:
    """Defer a first request to end that arrives in the block to the block's end. Inside
    `terminable` it then raises `Terminated`; outside, it is raised again by the handler that
    stood before. Outside the main thread the block runs as it is."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    outermost, deferred = _REQUESTS.depth == 0, None
    try:
        with terminable():
            _REQUESTS.deferring += 1
            try:
                yield
            finally:
                _REQUESTS.deferring -= 1
                if not _REQUESTS.deferring:
                    deferred, _REQUESTS.deferred = _REQUESTS.deferred, None
                    if deferred is not None and not outermost:
                        _REQUESTS.acted = deferred
                        raise Terminated(deferred)
    finally:
        if outermost and deferred is not None:
            signal.raise_signal(deferred)


def leave(asked: Terminated, said: str) -> NoReturn:
    """End a command that was asked to end, once it has ended what it started: one line on
    standard error, what the code that ended the children said or else `said`, then the exit
    status a shell gives a command ended by that signal. Where the request was a signal's, every
    further one is ignored from here to the exit, the interpreter's own shutdown included, so
    that the status is that one."""
    print(asked.said or said, file=sys.stderr, flush=True)
    if _REQUESTS.acted is not None and threading.current_thread() is threading.main_thread():
        _REQUESTS.leaving = True
        for number in _REQUESTS.earlier:
            signal.signal(number, signal.SIG_IGN)
    raise SystemExit(asked.status)


@contextlib.contextmanager
def ending(said: str) -> Iterator[None]:
    """A command's whole run. A request to end that arrives in it is raised where the command
    stands (`terminable`); once it has unwound the command, ending what the command started,
    the command leaves (`leave`) with `said`, in which `{request}` stands for what asked."""
    with terminable():
        try:
            yield
        except Terminated as asked:
            leave(asked, said.format(request=asked.request))


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
    both signals go to its whole process group, the wait is for the group, and a child that has
    ended while processes of its group still run, such as a renderer's workers, counts as
    running. A first request to end that arrives meanwhile is deferred until every child has
    ended (`held`)."""
    with held():
        running = [
            child
            for child in children
            if child.poll() is None or (groups and group_exists(child.pid))
        ]
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
            time.sleep(POLL_SECONDS)
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
        # A request that arrives while the child starts is acted on once the child is held here.
        with held():
            child = subprocess.Popen(command, cwd=cwd)
        status = child.wait()
    except BaseException:
        if child is not None:
            stop([child], signal.SIGTERM, seconds=2 * STOP_SECONDS)
        raise
    if status != 0:
        raise subprocess.CalledProcessError(status, command)
