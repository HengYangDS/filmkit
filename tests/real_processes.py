"""Real child processes in the tests: scripts that report when they are ready, what a test reads
of them, and their end whatever the test does.

A test of signals never signals the pytest process: the scenario runs in a process of its own,
started here, and the test signals that. A test waits for what a process reports, a line on its
standard output or a note it writes whole, and never for a fixed time. Every process started
through `Processes`, and every process a note names, is killed when the test is over, also when
an assertion failed; a process a note named is known by its number and the time it started, so
that a number the kernel has since given to another process is left alone. The `processes`
fixture fails a test that has not ended within its
deadline instead of letting it stall a run (`tests/conftest.py`, `deadline`). A module whose
tests start real processes asks for the fixture for every test.
"""

from __future__ import annotations

import contextlib
import json
import os
import select
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

# What a script puts first to write a note: its process id and the facts given, as one file that
# appears whole.
NOTE = """
import json, os, pathlib

def note(name, **facts):
    folder = pathlib.Path(os.environ["NOTES"])
    partial = folder / f".{name}.{os.getpid()}"
    partial.write_text(json.dumps({"pid": os.getpid(), **facts}))
    partial.replace(folder / f"{name}.json")
"""


@contextlib.contextmanager
def deadline(seconds: float):
    """Fail the block with `TimeoutError` when it has not ended within the seconds, by the
    process's alarm timer, so that a wait that hangs fails where it stands."""

    def expired(_number, _frame):
        message = f"the test did not end within {seconds} s"
        raise TimeoutError(message)

    earlier = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, earlier)


def alive(pid: int) -> bool:
    """Whether a process still runs; one that ended and awaits its parent's wait does not."""
    listed = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    return bool(listed.stdout.strip()) and not listed.stdout.strip().startswith("Z")


def started_at(pid: int) -> str:
    """When the process of that number started, as `ps` words it; empty when there is none."""
    listed = subprocess.run(
        ["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    return listed.stdout.strip()


def wait_for(condition, seconds: float = 10.0) -> bool:
    """Whether the condition came to hold within the seconds, looked at every 20 ms."""
    ends = time.monotonic() + seconds
    while time.monotonic() < ends:
        if condition():
            return True
        time.sleep(0.02)
    return bool(condition())


def gone(pids: list[int], seconds: float = 10.0) -> bool:
    """Whether every one of the processes has ended within the seconds."""
    return wait_for(lambda: not any(alive(pid) for pid in pids), seconds)


def twice(pid: int, first: int, second: int, microseconds: int) -> None:
    """Send a process two signals, the second the given microseconds after the first; a process
    that has ended by then gets none."""
    os.kill(pid, first)
    until = time.perf_counter_ns() + microseconds * 1000
    while time.perf_counter_ns() < until:
        pass
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, second)


class Processes:
    """The processes a test starts and the notes they write, below the test's own folder."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.notes = folder / "notes"
        self.notes.mkdir(parents=True, exist_ok=True)
        self.started: list[subprocess.Popen] = []
        # Each process a note named, with when it started as first seen.
        self.named: dict[int, str] = {}

    def script(self, name: str, text: str) -> Path:
        """Write a Python script, which can write notes, and return its path."""
        path = self.folder / f"{name}.py"
        path.write_text(textwrap.dedent(NOTE) + textwrap.dedent(text))
        return path

    def python(self, script: Path, *arguments: str, session: bool = False, **variables: str):
        """Start a script with its output and input piped, in a session of its own if asked."""
        environment = {**os.environ, "NOTES": str(self.notes), **variables}
        return self.start(
            [sys.executable, "-B", str(script), *arguments],
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=session,
        )

    def start(self, command: list[str], **options) -> subprocess.Popen:
        """Start a process that the test's end will kill if it still runs."""
        process = subprocess.Popen(command, **options)
        self.started.append(process)
        return process

    def line(self, process: subprocess.Popen, seconds: float = 20.0) -> str:
        """The next line a process writes to its standard output, waited for at most the seconds."""
        ready, _, _ = select.select([process.stdout], [], [], seconds)
        assert ready, f"the process wrote no line within {seconds} s"
        return process.stdout.readline().rstrip("\n")

    def noted(self, name: str, seconds: float = 20.0) -> dict:
        """The note of that name, waited for at most the seconds."""
        path = self.notes / f"{name}.json"
        assert wait_for(path.is_file, seconds), f"no note {name} within {seconds} s"
        self.pids()
        return json.loads(path.read_text())

    def pids(self) -> list[int]:
        """Every process id the notes name; each is remembered with when it started."""
        notes = [json.loads(path.read_text()) for path in sorted(self.notes.glob("*.json"))]
        found = [value for note in notes for value in note.values() if type(value) is int]
        for pid in found:
            if pid not in self.named:
                self.named[pid] = started_at(pid)
        return found

    def kill(self, pid: int) -> None:
        """Kill a process a note named."""
        os.kill(pid, signal.SIGKILL)

    def forget(self) -> None:
        """Set the notes aside, for a next run under the same names; what they named is still
        killed at the end."""
        self.pids()
        for note in self.notes.glob("*.json"):
            note.unlink()

    def end(self) -> None:
        """Kill what still runs of the processes started here and of those the notes named. A
        named one is killed only while its number is still its own: the process of that number
        started when the named one did."""
        self.pids()
        for pid, when in self.named.items():
            if when and started_at(pid) == when and alive(pid):
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGKILL)
        for process in self.started:
            if process.poll() is None:
                process.kill()
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            process.wait()
