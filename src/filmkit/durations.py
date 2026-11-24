"""Record how long each command took, beside the edition's evidence, and print a build's records.

A run measures one command on one edition. `run` opens it and writes its record when it ends,
whether the command completed or was refused or failed: the command, when it started, its
seconds, whether it completed, the seconds of each phase, and any setting that bears on its time,
such as the count of narration processes. The code that does the work names
a phase with `phase`, wherever it runs; outside a run a phase measures nothing. Work on another
thread adds its seconds to the run it was given (`current`, `Run.add`).

A record also states the host's 1-minute load average at the command's start and at its end
(`host_load`), so that a slower command can be read against a busier host. No check reads it. A
host that states no load average leaves both as null, and a record of an earlier engine holds
none; the command prints nothing of the host for either.

A record is build/evidence/editions/<code>/durations/<command>.json, the latest run of that
command. It binds nothing and no record binds it: a duration differs from run to run, so it never
stands in a record whose SHA-256 another record holds, and running a check again on unchanged
inputs leaves that check's own record byte for byte as it was.

A folder keeps the latest run of every command ever run there, so the sum the command prints is
a build's only once it says which records it covers. An edition's build begins with its latest
whole narration, the record `narrate`, which a narration of chosen segments and a check-only
narration do not write: the sum covers the commands that completed and started at or after
that, and `--since` names another start, for a build that keeps its narration or narrates its
segments by the synthesis command itself, which writes no record. Records that started
earlier are listed, marked as earlier and left out, and the last line says what was summed.
A convergence (`filmkit.narration.converge`, the record `converge`) narrates an edition more
than once, each narration its child, and each replaces the record `narrate`. Where the latest
whole narration started within a convergence's run, the build begins with that convergence:
the sum counts the convergence, and the narration is listed as inside it and not added again.
A convergence that did not complete is not counted, and its narration then is.
A command run twice in a build counts once, by its latest run. A sum adds each command's
seconds, so two commands that ran at the same time, such as several editions' renders, count in
full.
The time of the build is therefore the last line's first figure: the seconds during which at
least one counted command of the selected editions was running, which counts such commands once
and the waits between commands not at all. For commands run in a row the two figures are equal.

The two checks a film's build runs from the command line for an edition, the geometry check
and the cover check (`filmkit.tools`), the verifier and the reproduction write records too, the
last two unless they are asked to be read-only.

Usage: python -m filmkit.durations [--language <code>|all] [--since <time>] [--json]
Prints each selected edition's records in the order their commands started, each with the
host's load, its phases and settings, the sum of the seconds of the completed commands of its
build, and last the time of the build with the range of the load its commands state.
"""

from __future__ import annotations

import argparse
import contextlib
import contextvars
import json
import os
import threading
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# The folder of an edition's duration records, below its evidence.
FOLDER = "durations"
# The command whose latest record marks where an edition's build began: its whole narration. A
# narration of chosen segments is a retake within some build, and a check-only narration, which
# generates nothing, runs at any point of one; each writes a record of another name
# (`filmkit.narration.narrate.record_name`).
BUILD_START = "narrate"
# The command that runs an edition's whole narrations as its children, with its judgments and
# its candidates between them (`filmkit.narration.converge`): a build whose narration started
# within its run began with it.
CONVERGENCE = "converge"
# The record's key for the host's 1-minute load average at a command's two ends.
LOAD, ENDS = "load_1m", ("start", "end")


def host_load() -> float | None:
    """The host's 1-minute load average to two decimals, or None on a host that states none:
    one without `os.getloadavg`, or one whose load average cannot be read."""
    try:
        return round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        return None


class Run:
    """One command's run on one edition: when it started, the host's load then, the seconds of
    its phases, and the settings its owner names as bearing on its time."""

    def __init__(self, code: str | None, command: str) -> None:
        self.code, self.command = code, command
        self.started_at = datetime.now(UTC)
        self.load_at_start = host_load()
        self.phases: dict[str, float] = {}
        self.settings: dict[str, object] = {}
        self.failed = False
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

    def fail(self) -> None:
        """Say that the command did not complete, for one whose block ends without raising and
        whose verdict is still no pass, such as a comparison that reports before it refuses."""
        self.failed = True

    @contextlib.contextmanager
    def phase(self, name: str) -> Iterator[None]:
        """Measure the block as one phase, also when it raises."""
        started = time.monotonic()
        try:
            yield
        finally:
            self.add(name, time.monotonic() - started)

    def record(self, *, completed: bool) -> dict:
        """The run as its record states it, its start and its seconds to the millisecond, with
        the host's load at its start and at this moment, its end."""
        return {
            "command": self.command,
            "edition": self.code,
            "started_at": self.started_at.isoformat(timespec="milliseconds"),
            "seconds": round(time.monotonic() - self._started, 3),
            LOAD: dict(zip(ENDS, (self.load_at_start, host_load()), strict=True)),
            "completed": completed,
            "phases": {name: round(seconds, 3) for name, seconds in self.phases.items()},
            "settings": dict(self.settings),
        }


_RUN: contextvars.ContextVar[Run | None] = contextvars.ContextVar("filmkit_run", default=None)


def current() -> Run | None:
    """The run the calling code works in, or None outside any."""
    return _RUN.get()


@contextlib.contextmanager
def run(
    code: str | None,
    command: str,
    *,
    record: bool = True,
    whole: bool = True,
    node: str | None = None,
    way: str | None = None,
) -> Iterator[Run]:
    """Measure the block as one command's run on an edition and write its record at the end.

    The record says that the command completed only when the block ends without raising and
    without the run being told that it failed (`Run.fail`); the exception of one that raises
    propagates after the record is written. With `record` False
    the run is measured and nothing is written, for a command asked to write nothing.

    A command of an edition that names a node of the build chain, `node` or else the command
    itself, also opens that node's run and writes its run record from the same measurement
    (`filmkit.graph.runs`), or a partial record where `whole` says the run is not the node's
    whole run; `way` names the way of a node of several that the caller was asked to take. The
    graph is imported here, when a run opens: the owners whose lists the node table reads
    import this module.
    """
    opened = Run(code, command)
    node_run = None
    if record:
        from filmkit.graph import runs

        node_run = runs.open_node(code, node or command, opened, whole=whole, way=way)
    token = _RUN.set(opened)
    completed, ended = False, None
    try:
        yield opened
        completed = not opened.failed
    except BaseException as error:
        ended = error
        raise
    finally:
        _RUN.reset(token)
        if record:
            stated = opened.record(completed=completed)
            repository.write(opened.path, stated)
            if node_run is not None:
                node_run.close(stated, ended)


@contextlib.contextmanager
def phase(name: str) -> Iterator[None]:
    """Measure the block as a phase of the current run; outside a run, measure nothing."""
    opened = _RUN.get()
    if opened is None:
        yield
        return
    with opened.phase(name):
        yield


def since(text: str) -> str:
    """A `--since` value, refused unless it is an ISO 8601 time with its offset."""
    try:
        aware = datetime.fromisoformat(text).tzinfo is not None
    except ValueError:
        aware = False
    if not aware:
        message = f"{text!r} is no ISO 8601 time with its offset, such as 2026-11-17T01:00:00+00:00"
        raise argparse.ArgumentTypeError(message)
    return text


def records(code: str) -> list[dict]:
    """An edition's duration records in the order their commands started."""
    folder = Edition(code).evidence / FOLDER
    found = [repository.read(path) for path in sorted(folder.glob("*.json"))]
    return sorted(
        found,
        key=lambda record: (datetime.fromisoformat(record["started_at"]), record["command"]),
    )


def narration(found: list[dict]) -> dict | None:
    """An edition's latest whole narration, the command `BUILD_START`; None where no such
    record stands."""
    whole = [record for record in found if record["command"] == BUILD_START]
    return max(whole, key=lambda record: datetime.fromisoformat(record["started_at"]), default=None)


def convergence(found: list[dict]) -> dict | None:
    """The convergence that ran an edition's latest whole narration: the command `CONVERGENCE`
    within whose run, its last second included, that narration started; None where the
    narration ran by itself, as it does after an earlier convergence."""
    whole = narration(found)
    if whole is None:
        return None
    at = datetime.fromisoformat(whole["started_at"])
    for record in found:
        began = datetime.fromisoformat(record["started_at"])
        ended = began + timedelta(seconds=record["seconds"])
        if record["command"] == CONVERGENCE and began <= at <= ended:
            return record
    return None


def build_start(found: list[dict]) -> str | None:
    """When an edition's build began: the start of its latest whole narration, or of the
    convergence that ran it; None where no whole narration is recorded."""
    first = convergence(found) or narration(found)
    return first and first["started_at"]


def inside(found: list[dict], since: str | None = None) -> dict | None:
    """The whole narration that a sum does not add again: the latest, where the convergence
    that ran it is itself counted, so completed and started no earlier than `since`."""
    ran = convergence(found)
    if ran is None or not ran["completed"] or earlier([ran], since)[0]:
        return None
    return narration(found)


def earlier(found: list[dict], start: str | None) -> list[bool]:
    """For each record, whether it started before the build did and so is no part of it."""
    if start is None:
        return [False] * len(found)
    began = datetime.fromisoformat(start)
    return [datetime.fromisoformat(record["started_at"]) < began for record in found]


# What a record's line says of a record that the sum leaves out (`states`).
INSIDE, EARLIER, NOT_COMPLETED = "inside the convergence", "earlier", "not completed"


def states(found: list[dict], since: str | None = None) -> list[str]:
    """Each record's state in its edition's build, which began at `since` or else at its latest
    whole narration or the convergence that ran it: `INSIDE` for the narration that a counted
    convergence ran (`inside`), `EARLIER` for a record that started before the build did,
    `NOT_COMPLETED` for a command that did not complete, and nothing for one the sum counts."""
    old, held = earlier(found, since or build_start(found)), inside(found, since)

    def state(record: dict, before: bool) -> str:
        if record is held:
            return INSIDE
        if before:
            return EARLIER
        return "" if record["completed"] else NOT_COMPLETED

    return [state(record, before) for record, before in zip(found, old, strict=True)]


def counted(found: list[dict], since: str | None = None) -> list[dict]:
    """The records an edition's sum covers: those of no state that leaves a record out
    (`states`)."""
    said = zip(found, states(found, since), strict=True)
    return [record for record, state in said if not state]


def running(found: list[dict]) -> float:
    """The seconds during which at least one of the commands ran, so that commands that ran at
    the same time count once."""
    spans = sorted(
        (datetime.fromisoformat(record["started_at"]).timestamp(), record["seconds"])
        for record in found
    )
    total, end = 0.0, float("-inf")
    for start, seconds in spans:
        total += max(0.0, start + seconds - max(start, end))
        end = max(end, start + seconds)
    return total


def stated_load(record: dict) -> list[float]:
    """The loads a record states, its start's before its end's: none for a record of an earlier
    engine or of a host that states no load average."""
    stated = record.get(LOAD) or {}
    return [stated[end] for end in ENDS if stated.get(end) is not None]


def load_text(record: dict) -> str:
    """A record's load as its line prints it, `load 6.5 to 33.8`: one figure where both ends
    print alike or only one is stated, and nothing where the record states none."""
    printed = dict.fromkeys(f"{load:.1f}" for load in stated_load(record))
    return "load " + " to ".join(printed) if printed else ""


def lines(code: str, found: list[dict], since: str | None = None) -> list[str]:
    """An edition's records as the command prints them, in the order they started, with the sum
    of the completed commands of its build: those that started at or after `since`, or else at or
    after its latest whole narration or the convergence that ran it. A record that started
    earlier is marked and left out, as is the narration inside a counted convergence, and the
    last line says what the sum covers."""
    if not found:
        return [f"{code}: no duration record"]
    start, said = since or build_start(found), states(found, since)
    width = max(len(record["command"]) for record in found)
    listed = [f"{code}:"]
    for record, state in zip(found, said, strict=True):
        phases = ", ".join(f"{name} {seconds:.1f}" for name, seconds in record["phases"].items())
        named = record.get("settings", {}).items()
        settings = ", ".join(f"{name} {value}" for name, value in named)
        load = load_text(record)
        listed.append(
            f"  {record['started_at']}  {record['command']:<{width}}  "
            f"{record['seconds']:>9.1f} s{'  ' + state if state else ''}"
            f"{'  ' + load if load else ''}"
            f"{'  (' + phases + ')' if phases else ''}"
            f"{'  [' + settings + ']' if settings else ''}"
        )
    if start is None:
        covered = "(no whole narration is recorded, so every record counts)"
    else:
        first = "convergence" if convergence(found) else "narration"
        covered = f"since {'' if since else f'the {first} started at '}{start}"
    old = said.count(EARLIER)
    left_out = f"; {old} earlier records are not counted" if old else ""
    summed = [record["seconds"] for record in counted(found, since)]
    total = f"  sum of the {len(summed)} commands completed {covered}: {sum(summed):.1f} s"
    return [*listed, total + left_out]


def load_range(found: list[dict]) -> str:
    """What the last line says of the host: the lowest and the highest load the counted commands
    state at their starts and ends, and how many of them state none; nothing where none does."""
    stated = [stated_load(record) for record in found]
    loads = [load for ends in stated for load in ends]
    if not loads:
        return ""
    silent = sum(1 for ends in stated if not ends)
    return (
        f"; the host's 1-minute load stood between {min(loads):.1f} and {max(loads):.1f} at "
        f"their starts and ends{f' ({silent} of them state none)' if silent else ''}"
    )


def build_time(found: list[dict]) -> str:
    """The last line: the time of the build, which is the seconds during which one of the counted
    commands was running, beside the sum of their seconds, which is more where two ran at once,
    and the range of the host's load the commands state."""
    added = sum(record["seconds"] for record in found)
    return (
        f"build: one of the {len(found)} counted commands was running for {running(found):.1f} s; "
        f"their seconds add up to {added:.1f} s (commands that ran at the same time count once "
        f"in the first figure){load_range(found)}"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m filmkit.durations", description=__doc__.splitlines()[0]
    )
    parser.add_argument("--language", choices=(*CODES, "all"), default="all")
    parser.add_argument("--json", action="store_true", help="print the records themselves")
    parser.add_argument(
        "--since",
        type=since,
        help="sum what started at or after this time, an ISO 8601 time with its offset",
    )
    options = parser.parse_args(argv)
    codes = CODES if options.language == "all" else (options.language,)
    found = {code: records(code) for code in codes}
    if options.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return
    for code in codes:
        print("\n".join(lines(code, found[code], options.since)))
    together = [record for code in codes for record in counted(found[code], options.since)]
    if together:
        print(build_time(together))


if __name__ == "__main__":
    main()
