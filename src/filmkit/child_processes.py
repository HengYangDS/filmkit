"""End the child processes a command started when the command is asked to end, so that none
outlives it, and end the command itself with one line and the status a shell expects.

A command that starts children and waits for them ends them when its wait is cut short: by a
failure of its own, or by a request to end, which is an interrupt (SIGINT), a request to end
(SIGTERM) or a hang-up (SIGHUP), the last from a terminal that closes or a session that drops.
A signal the process ignores, as a hang-up under nohup, stays ignored.

The requests are taken only where the command holds children that must be ended in order: the
blocks of `terminable`, which are a renderer's run, a narration's processes and a step of
`narrate` (`run`). Inside such a block the first request raises `Terminated` where the command
stands, so that its own handling ends its children. From that first arrival every further
request is taken and dropped, also after the block, to the command's exit: the command is
ending, and a second signal, at whatever interval, neither ends it early by its default action
nor cuts the ending of its children short. Two different requests that both arrive before the
process has acted on either are handed to it lowest number first: it acts on that one.

Everywhere else a request has its usual effect, as in a command that knows nothing of this
module: SIGTERM and a hang-up end the process by their default action, and an interrupt raises
`KeyboardInterrupt` in the main thread. A process that a signal ends so runs nothing more: what
it had started runs on, a check's audits to their end, and what it would have written at its
end, its duration record among it, is not written. A wait for a tool that an interrupt cuts
short asks the tool to end and waits for it before the interrupt goes on (`filmkit.tools.run`,
by `stop`), so that the tool ends what it started, a browser among it, whether or not the
interrupt reached the tool itself; a further request in that time is deferred, as in any stop,
until the tool has ended or been killed. The audits that a check runs side by side are waited for in
threads of their own, which no interrupt reaches: one that reached the command alone leaves
them running to their end.

`ending`, around the whole run of `filmkit build` and of the synthesis and around the steps of
`narrate`, sets no handler. It words the exit
of a command that was asked to end where it stood in such a block, or that was interrupted
anywhere inside it: one line
that says what stopped it, then, after SIGTERM or a hang-up, the exit status 128 and the
signal's number, and after an interrupt the interrupt itself, by which the process then dies,
so that a shell that ran the command in a script ends the script and reports 130. A line that
cannot be written, since the terminal that hung up is gone, that its stream does not take
within `SAY_SECONDS`, as a full pipe that nobody reads, or whose stream the command was started
without, is dropped and changes neither.

Where a request must not interrupt, `held` defers the first one to the end of its block: while
a child starts, so that the request finds the child already among those to end, while a child
is looked at (`exit_status`), since that look cannot be cut anywhere, and while children are
being ended (`stop`), when the cause was not a request.

`stop` asks each child that has not been reaped to end, by a signal to the child or, for a
child that leads a session of its own, to its whole process group, so that what the child
started ends with it; it waits for them and kills what has not ended after `STOP_SECONDS`. A
child is reaped only once that is done, and one that was reaped before is never signalled: a
reaped child's number is no longer its own, and the kernel may have given it to another process
since. `ended` waits for a child's end without reaping it, so that a caller can still have the
group it leads ended.

`filmkit.picture.rendering` uses these for a renderer, `filmkit.narration.processes` for a
narration's shares, and `filmkit.narration.narrate` for each of its steps (`run`).

A process that is killed outright (SIGKILL) runs none of this, and its children outlive it. A
child that leads its own session is not reached by a signal to its parent's process group
either, so a caller that must end such a command asks it to end and waits.

A command's exit status says how it ended (design decision 19 of build-a-film-by-its-verbs):
`FINISHED` where it did what it was asked, `REFUSED` where the film or a gate said no, in one
line, and `UNFINISHED` where it could not finish, by an exception, or by a cause outside the
film's sources that one line names (`UnfinishedError`): a tool the host lacks, or no film where
the command runs; a request to end exits with the status that names it, as above.
"""

from __future__ import annotations

import contextlib
import errno
import os
import select
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING, NamedTuple, NoReturn

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# Seconds a child has to end after it is asked to, before it is killed.
STOP_SECONDS = 30
# Seconds between two looks at a child or a process group that is ending.
POLL_SECONDS = 0.05
# Seconds a command's last line waits for a stream that takes no write, before it is dropped.
SAY_SECONDS = 1
# The signals that ask a command to end, with what each is called.
REQUESTS = {
    signal.SIGINT: "an interrupt",
    signal.SIGTERM: "a request to end (SIGTERM)",
    signal.SIGHUP: "a hang-up (SIGHUP)",
}
# A command's exit statuses: it finished, it refused, or it could not finish.
FINISHED, REFUSED, UNFINISHED = 0, 1, 2


class UnfinishedError(RuntimeError):
    """The command cannot finish for a cause outside the film's sources, which its one line names:
    no refusal of the film's, and its status is `UNFINISHED`."""


class MissingToolError(UnfinishedError):
    """A tool the engine runs is not on this host as its owner installs it, so the command
    cannot finish."""


class HostTool(NamedTuple):
    """A program of the host that the engine starts by name: how Homebrew installs it and, for an
    encoder whose version a node's record pins, the name it is pinned by and the arguments that
    print that version (`filmkit.graph.runs.ENCODERS`)."""

    install: str
    pinned: str | None = None
    version: tuple[str, ...] = ()


# The host's programs that the engine starts by name (design decision 13 of
# build-a-film-by-its-verbs for the encoders' pins).
HOST_TOOLS = {
    "ffmpeg": HostTool("brew install ffmpeg", "FFmpeg", ("-version",)),
    "ffprobe": HostTool("brew install ffmpeg", "ffprobe", ("-version",)),
    "exiftool": HostTool("brew install exiftool", "ExifTool", ("-ver",)),
    "rsync": HostTool("brew install rsync"),
}


def absent(program: str) -> MissingToolError:
    """The host lacks one of `HOST_TOOLS`: named in one line with how Homebrew installs it."""
    install = HOST_TOOLS[program].install
    return MissingToolError(f"No {program} on the path; install it as Homebrew does: {install}")


def required(program: str) -> str:
    """The path of one of `HOST_TOOLS` on the host, or its absence (`absent`)."""
    found = shutil.which(program)
    if found is None:
        raise absent(program)
    return found


def unfinished(error: BaseException) -> UnfinishedError | None:
    """What an error says the command could not finish for, in one line: an `UnfinishedError`, as
    a tool the host lacks or a command run outside any film, or the `FileNotFoundError` that
    starting one of `HOST_TOOLS` raises where it is not on the path; None for any other error."""
    if isinstance(error, UnfinishedError):
        return error
    named = error.filename if isinstance(error, FileNotFoundError) else None
    return absent(named) if named in HOST_TOOLS else None


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
    `held` block, and those dropped since."""

    def __init__(self) -> None:
        self.depth, self.deferring = 0, 0
        self.earlier: dict[int, object] = {}
        self.acted: int | None = None
        self.deferred: int | None = None
        self.dropped: list[int] = []


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
    raises `Terminated` in it, and from then on every further one is dropped, so that the
    block's own handling ends its children undisturbed. A block inside another adds nothing.

    The outermost block that ends with no request acted on puts back the handlers that stood
    before. One that ends after a request leaves them taken: the command is ending, and a
    further request between the block and the command's exit is dropped as one inside it is
    (`leave` ends the command; `restore` is for a caller that goes on). Outside the main thread,
    where a process sets no handler, the block runs as it is."""
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    if _REQUESTS.depth == 0 and _REQUESTS.acted is None:
        _REQUESTS.deferred, _REQUESTS.dropped = None, []
        for number in REQUESTS:
            if signal.getsignal(number) not in (signal.SIG_IGN, receive):
                _REQUESTS.earlier[number] = signal.signal(number, receive)
    _REQUESTS.depth += 1
    try:
        yield
    finally:
        _REQUESTS.depth -= 1
        if _REQUESTS.depth == 0 and _REQUESTS.acted is None:
            _put_back()


def _put_back() -> None:
    """Put back the handlers that stood before the outermost block took the requests."""
    for number, handler in _REQUESTS.earlier.items():
        signal.signal(number, signal.SIG_DFL if handler is None else handler)
    _REQUESTS.earlier.clear()


def restore() -> None:
    """Forget a request that was acted on and put back the handlers that stood before it: for a
    caller that handled `Terminated` itself and goes on, as a test in its own process does. A
    command that was asked to end leaves instead (`leave`)."""
    if threading.current_thread() is threading.main_thread() and _REQUESTS.depth == 0:
        _put_back()
        _REQUESTS.acted, _REQUESTS.deferred, _REQUESTS.dropped = None, None, []


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


def _takes_a_write(stream: object) -> bool:
    """Whether a stream's descriptor takes a write within `SAY_SECONDS`. A stream that has no
    descriptor, or whose descriptor cannot be asked, is written as it is."""
    try:
        return bool(select.select([], [stream.fileno()], [], SAY_SECONDS)[1])
    except (OSError, ValueError, AttributeError):
        return True


def _waiting_pipe(stream: object) -> int | None:
    """The descriptor of a stream that is a pipe or a socket and waits on a write it has no
    room for; None for a stream of another kind, for one that does not wait, and for one that
    has no descriptor or whose descriptor cannot be asked."""
    try:
        descriptor = stream.fileno()
        mode = os.fstat(descriptor).st_mode
        waits = (stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)) and os.get_blocking(descriptor)
    except (OSError, ValueError, AttributeError):
        return None
    return descriptor if waits else None


def _say(line: str) -> None:
    """Write a command's last line to standard error and flush what standard output holds,
    without waiting for a reader: the command is ending and ignores every request by now. A
    stream the command was started without is passed over. A stream that takes no write within
    `SAY_SECONDS`, as a full pipe that nobody reads, or that cannot be written, as one on a
    terminal that has hung up, is pointed at the null device, so that what it still holds
    drains there and the interpreter's own flush at its exit neither waits nor fails and
    changes the exit status; the line to such a stream is dropped. A pipe or a socket is written
    without waiting, and set to wait again at once, since the setting is shared with whoever
    else holds it: one with less room than the stream holds takes what fits, and the rest is
    dropped the same way. One case remains: a stream of another kind that takes a write and has
    less room than it holds waits."""
    for stream, text in ((sys.stderr, f"{line}\n"), (sys.stdout, "")):
        if stream is None:
            continue
        try:
            if not _takes_a_write(stream):
                raise BlockingIOError
            pipe = _waiting_pipe(stream)
            if pipe is not None:
                os.set_blocking(pipe, False)
            try:
                stream.write(text)
                stream.flush()
            finally:
                if pipe is not None:
                    os.set_blocking(pipe, True)
        except (OSError, ValueError):
            with contextlib.suppress(OSError, ValueError, AttributeError):
                descriptor = stream.fileno()
                null = os.open(os.devnull, os.O_WRONLY)
                # Where the stream's own descriptor was closed, the null device was given its
                # number and is the stream's by that; closing it would close the stream again.
                if null != descriptor:
                    try:
                        os.dup2(null, descriptor)
                    finally:
                        os.close(null)
                stream.flush()


def leave(asked: Terminated, said: str, *, interrupted: bool = False) -> NoReturn:
    """End a command that was asked to end, once it has ended what it started.

    Where the request was a signal's, one taken in a block of `terminable` or an interrupt
    that reached the command elsewhere (`interrupted`), every further request is ignored
    first, from here to the exit, the interpreter's own shutdown included. Then one line on
    standard error, what the code that ended the children said or else `said`; that it cannot
    be written changes nothing. Then the exit a shell expects: after SIGTERM or a hang-up the
    status 128 and the signal's number; after an interrupt the process dies by the interrupt
    itself, its default action put back, since a shell ends a script on an interrupt only when
    the command it waited for died by it, and reports 130 for one that did. Where the
    interrupt was ignored before, where the request was no signal's, and outside the main
    thread, the command exits with the status alone.
    """
    main = threading.current_thread() is threading.main_thread()
    signalled = main and (interrupted or _REQUESTS.acted is not None)
    ignored = set()
    if signalled:
        for number in REQUESTS:
            if signal.signal(number, signal.SIG_IGN) is signal.SIG_IGN:
                ignored.add(number)
    _say(asked.said or said)
    if signalled and asked.number == signal.SIGINT and signal.SIGINT not in ignored:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.raise_signal(signal.SIGINT)
    raise SystemExit(asked.status)


@contextlib.contextmanager
def ending(said: str) -> Iterator[None]:
    """A command's whole run. It takes no request itself: where the command holds children, a
    block of `terminable` does, and the request is raised there; elsewhere SIGTERM and a
    hang-up end the process and an interrupt raises `KeyboardInterrupt`. Once a request taken in
    such a block, or an interrupt from anywhere, has unwound the command, ending what the
    command started, the command leaves (`leave`) with `said`, in which `{request}` stands for
    what asked."""
    try:
        yield
    except Terminated as asked:
        leave(asked, said.format(request=asked.request))
    except KeyboardInterrupt:
        asked = Terminated(signal.SIGINT)
        leave(asked, said.format(request=asked.request), interrupted=True)


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


def ended(child: subprocess.Popen, seconds: float | None = None) -> bool:
    """Wait until a child has ended, at most `seconds`, without reaping it: whether it ended.

    A child that has ended and is not reaped keeps its number, and with it the number of the
    process group it leads, so what is left of that group can still be ended by the number with
    no risk of reaching another process (`stop`). The wait is the kernel's own for a process's
    end: a kernel queue where there is one, as on macOS, and `waitid` elsewhere.
    """
    if child.returncode is not None:
        return True
    if not hasattr(select, "kqueue"):
        ends = None if seconds is None else time.monotonic() + seconds
        look = os.WEXITED | os.WNOWAIT | os.WNOHANG
        while os.waitid(os.P_PID, child.pid, look) is None:
            if ends is not None and time.monotonic() >= ends:
                return False
            time.sleep(POLL_SECONDS)
        return True
    queue = select.kqueue()
    try:
        exits = select.kevent(
            child.pid,
            filter=select.KQ_FILTER_PROC,
            flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
            fflags=select.KQ_NOTE_EXIT,
        )
        events = queue.control([exits], 1, seconds)
    except ProcessLookupError:
        return True
    finally:
        queue.close()
    if not events:
        return False
    # With room for an event, a registration that fails comes back as one flagged an error:
    # for a child that has ended already, "no such process", which is its end; any other error
    # says nothing of the child and is raised.
    failed = events[0].flags & select.KQ_EV_ERROR
    if failed and events[0].data != errno.ESRCH:
        raise OSError(events[0].data, os.strerror(events[0].data))
    return True


def stop(
    children: list[subprocess.Popen],
    asking: int = signal.SIGINT,
    *,
    groups: bool = False,
    seconds: float | None = None,
) -> None:
    """Ask the children that have not been reaped to end and wait for them; kill what has not
    ended after `seconds`, `STOP_SECONDS` unless given, and reap each one last. A child that was
    reaped before the call is left out: its number may be another process's by now.

    With `groups` each child leads a session of its own: both signals go to its whole process
    group, also where the child itself has ended and waits to be reaped while processes it
    started run on, as a renderer's workers do, and the wait is for the group. The child is
    reaped only when its group has ended or been killed, so the number that is signalled is the
    child's own throughout. A child whose end cannot be waited for (`ended` raises) is looked at
    until the grace is over (`_outlasts`) and killed only if it still runs then. On a kernel
    that counts an ended child that is not reaped as a
    member of its group, which macOS does not, the wait for a group runs its full time. A first
    request to end that arrives meanwhile is deferred until every child has ended (`held`)."""
    with held():
        running = [child for child in children if child.returncode is None]
        for child in running:
            send(child, asking, group=groups)
        ends = time.monotonic() + (STOP_SECONDS if seconds is None else seconds)
        for child in running:
            try:
                late = not ended(child, max(0.0, ends - time.monotonic()))
            except OSError:
                # The wait itself failed and says nothing of the child: it is looked at instead.
                late = _outlasts(child, ends, group=groups)
            while groups and not late and time.monotonic() < ends and group_exists(child.pid):
                time.sleep(POLL_SECONDS)
            if late or (groups and group_exists(child.pid)):
                send(child, signal.SIGKILL, group=groups)
            child.wait()


def _outlasts(child: subprocess.Popen, ends: float, *, group: bool) -> bool:
    """Whether a child that was asked to end still runs when its grace is over, looked at every
    `POLL_SECONDS` where its end cannot be waited for. A child that leads a group is not reaped
    here: its group is asked for by its number, which is the child's own until the caller reaps
    it. A child alone is reaped as soon as it has ended, and is not signalled after that."""
    while time.monotonic() < ends:
        ended_by_now = not group_exists(child.pid) if group else child.poll() is not None
        if ended_by_now:
            return False
        time.sleep(POLL_SECONDS)
    return True


def exit_status(child: subprocess.Popen) -> int | None:
    """A child's exit status, or None while it runs, looked at with a request deferred (`held`).

    Inside a block of `terminable` a request is raised wherever the command stands, and
    `Popen.poll` cannot be cut anywhere: it takes the child's lock and only then guards it, so a
    request raised between the two leaves the lock taken, and the wait that ends a stop then
    waits for that lock for ever, in a command whose children have ended and that takes no
    further request. A block that takes requests therefore looks at a child through this, and
    otherwise only sleeps or waits (`ended`, `Popen.wait` without a timeout), which a request
    may cut."""
    with held():
        return child.poll()


def run(command: list[str], *, cwd: Path, seconds: float = 2 * STOP_SECONDS) -> None:
    """Run one child to its end, taking the requests to end while it runs (`terminable`). A
    wait that is cut short, by a request or by a failure, asks the child to end (SIGTERM) and
    waits `seconds` for it before the cause goes on: twice as long as the child may itself
    wait for its own children, unless the caller names a longer wait for a child whose
    children run children of their own. An exit other than 0 raises
    `subprocess.CalledProcessError`, as `subprocess.run` does with `check`."""
    child = None
    with terminable():
        try:
            # A request that arrives while the child starts is acted on once it is held here.
            with held():
                child = subprocess.Popen(command, cwd=cwd)
            status = child.wait()
        except BaseException:
            if child is not None:
                stop([child], signal.SIGTERM, seconds=seconds)
            raise
    if status != 0:
        raise subprocess.CalledProcessError(status, command)
