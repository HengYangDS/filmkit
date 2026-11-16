"""Record how long each command took, beside the edition's evidence, and print a build's records.

A run measures one command on one edition. `run` opens it and writes its record when it ends,
whether the command completed or was refused or failed: the command, when it started, its
seconds, whether it completed, and the seconds of each phase. The code that does the work names
a phase with `phase`, wherever it runs; outside a run a phase measures nothing. Work on another
thread adds its seconds to the run it was given (`current`, `Run.add`).

A record is build/evidence/editions/<code>/durations/<command>.json, the latest run of that
command. It binds nothing and no record binds it: a duration differs from run to run, so it never
stands in a record whose SHA-256 another record holds, and running a check again on unchanged
inputs leaves that check's own record byte for byte as it was.

Usage: python -m filmkit.durations [--language zh|en|all] [--json]
Prints each selected edition's records in the order their commands started, each with its
phases, and the sum of the seconds of the commands that completed.
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import json
import threading
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# The folder of an edition's duration records, below its evidence.
FOLDER = "durations"


class Run:
    """One command's run on one edition: when it started and the seconds of its phases."""

    def __init__(self, code: str, command: str) -> None:
        self.code, self.command = code, command
        self.started_at = datetime.now(UTC)
        self.phases: dict[str, float] = {}
        self._started = time.monotonic()
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        """The run's record, below its edition's evidence."""
        return Edition(self.code).evidence / FOLDER / f"{self.command}.json"

    def add(self, name: str, seconds: float) -> None:
        """Add seconds to a phase; a phase named again holds the sum."""
        with self._lock:
            self.phases[name] = self.phases.get(name, 0.0) + seconds

    @contextlib.contextmanager
    def phase(self, name: str) -> Iterator[None]:
        """Measure the block as one phase, also when it raises."""
        started = time.monotonic()
        try:
            yield
        finally:
            self.add(name, time.monotonic() - started)

    def record(self, *, completed: bool) -> dict:
        """The run as its record states it, seconds to the millisecond."""
        return {
            "command": self.command,
            "edition": self.code,
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "seconds": round(time.monotonic() - self._started, 3),
            "completed": completed,
            "phases": {name: round(seconds, 3) for name, seconds in self.phases.items()},
        }


_RUN: contextvars.ContextVar[Run | None] = contextvars.ContextVar("filmkit_run", default=None)


def current() -> Run | None:
    """The run the calling code works in, or None outside any."""
    return _RUN.get()


@contextlib.contextmanager
def run(code: str, command: str) -> Iterator[Run]:
    """Measure the block as one command's run on an edition and write its record at the end.

    The record says that the command completed only when the block ends without raising; the
    exception of one that does not propagates after the record is written.
    """
    opened = Run(code, command)
    token = _RUN.set(opened)
    completed = False
    try:
        yield opened
        completed = True
    finally:
        _RUN.reset(token)
        repository.write(opened.path, opened.record(completed=completed))


@contextlib.contextmanager
def phase(name: str) -> Iterator[None]:
    """Measure the block as a phase of the current run; outside a run, measure nothing."""
    opened = _RUN.get()
    if opened is None:
        yield
        return
    with opened.phase(name):
        yield


def records(code: str) -> list[dict]:
    """An edition's duration records in the order their commands started."""
    folder = Edition(code).evidence / FOLDER
    found = [repository.read(path) for path in sorted(folder.glob("*.json"))]
    return sorted(found, key=lambda record: (record["started_at"], record["command"]))


def lines(code: str, found: list[dict]) -> list[str]:
    """An edition's records as the command prints them, with the sum of the completed ones."""
    if not found:
        return [f"{code}: no duration record"]
    width = max(len(record["command"]) for record in found)
    listed = [f"{code}:"]
    for record in found:
        phases = ", ".join(f"{name} {seconds:.1f}" for name, seconds in record["phases"].items())
        state = "" if record["completed"] else "  not completed"
        listed.append(
            f"  {record['started_at']}  {record['command']:<{width}}  "
            f"{record['seconds']:>9.1f} s{state}{'  (' + phases + ')' if phases else ''}"
        )
    total = sum(record["seconds"] for record in found if record["completed"])
    return [*listed, f"  sum of the completed commands: {total:.1f} s"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m filmkit.durations", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--language", choices=(*CODES, "all"), default="all")
    parser.add_argument("--json", action="store_true", help="print the records themselves")
    options = parser.parse_args(argv)
    codes = CODES if options.language == "all" else (options.language,)
    found = {code: records(code) for code in codes}
    if options.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return
    for code in codes:
        print("\n".join(lines(code, found[code])))


if __name__ == "__main__":
    main()
