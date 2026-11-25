"""The seam: a command's run measured, and a node's run recorded (design decisions 2 and 10 of
build-a-film-by-its-verbs, 2 of record-every-run).

A run measures one command on one edition (`Run`): when it started, the host's 1-minute load at
its start and at its end (`host_load`), its seconds, whether it completed, the seconds of each
phase and any setting its owner names as bearing on its time, such as the count of narration
processes. `run` opens it; the code that does the work names a phase with `phase`, wherever it
runs, and outside a run a phase measures nothing. Work on another thread adds its seconds to the
run it was given (`current`, `Run.add`). A run writes nothing of its own: its measurement is
stated in the run record of the node it is, and a command that is no node, such as the verifier
or the reproduction, prints its seconds where it states them.

A run of a command that names a node of the table opens that node's run. The opening states the
inputs of the run's way, each hashed only where its size or time differs from the node's last
record, records the way among the run's settings where the node has several, starts the host
measures (`filmkit.graph.host`) and names the node and edition in `FILMKIT_NODE`, which every
child inherits (`filmkit.graph.opens`). The close states the outputs, takes the start, seconds,
load, phases and settings from the same `Run`, and writes the node's run record, or for a run
that is not the node's whole run a partial record (design decision 8 of record-every-run). The
outcome is `pass` for a run that completed, `refuse` for one that left with a line (a
`SystemExit`) or was told that it failed, and `error` for any other exception, each with the
line it ended with. A command that does a node's work again opens that node's run inside its own
(`node`), where a refusal of the owner it names is `refuse`.

Opening or closing a node's run never stops or changes the command: a failure of either is named
in one line on standard error and the node's last record stands, which the outputs this run
writes then contradict, so the plan finds the node stale and `filmkit verify` refuses its bytes.
The node table is imported when a node's run opens, not with this module: the owners whose lists
the table reads import this module for its phases.
"""

from __future__ import annotations

import contextlib
import contextvars
import functools
import os
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import filmkit.child_processes as child_processes
from filmkit.graph import host, nodes, opens, records
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Iterator

# The key of the host's 1-minute load average at a command's two ends.
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

    def measured(self, *, completed: bool) -> dict:
        """The run as its node's record states it, its start and its seconds to the millisecond,
        with the host's load at its start and at this moment, its end."""
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
    """Measure the block as one command's run on an edition.

    The run completed only when the block ends without raising and without the run being told
    that it failed (`Run.fail`); the exception of one that raises propagates after the node's
    record is written. A command of an edition that names a node of the table, `node` or else
    the command itself, opens that node's run and writes its run record from this measurement,
    or a partial record where `whole` says the run is not the node's whole run; `way` names the
    way of a node of several that the caller was asked to take. With `record` False the run is
    measured and nothing is written, for a command asked to write nothing.
    """
    opened = Run(code, command)
    node_run = open_node(code, node or command, opened, whole=whole, way=way) if record else None
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
        if node_run is not None:
            node_run.close(opened.measured(completed=completed), ended)


@contextlib.contextmanager
def node(
    code: str | None,
    name: str,
    *,
    way: str | None = None,
    refusals: tuple[type[BaseException], ...] = (),
) -> Iterator[None]:
    """Open the run of a node whose work another command does again, nested in that command's
    run, and write the node's run record when the block ends (design decision 5 of
    record-every-run). The node's run measures its own seconds and load; the phases and settings
    the work names stay with the command's run. A refusal of the owner, an exception of
    `refusals`, is the node's outcome `refuse`, as the command's line would be."""
    measured = Run(code, name)
    node_run = open_node(code, name, measured, way=way)
    completed, ended = False, None
    try:
        yield
        completed = True
    except BaseException as error:
        ended = error
        raise
    finally:
        if node_run is not None:
            node_run.close(measured.measured(completed=completed), ended, refusals)


@contextlib.contextmanager
def phase(name: str) -> Iterator[None]:
    """Measure the block as a phase of the current run; outside a run, measure nothing."""
    opened = _RUN.get()
    if opened is None:
        yield
        return
    with opened.phase(name):
        yield


def table() -> dict[str, nodes.Node]:
    """The chain's nodes by name."""
    from filmkit.graph import chain

    return {node.name: node for node in chain.TABLE}


# The host's encoders a node may name among its tools, each by the name its record pins it under,
# with the command that states its version (design decision 13), from the host's programs.
ENCODERS = {
    tool.pinned: (program, *tool.version)
    for program, tool in child_processes.HOST_TOOLS.items()
    if tool.pinned
}
# What a pin states of an encoder the host does not have.
ABSENT = "absent"


@functools.cache
def encoder(tool: str) -> str:
    """The host's version of an encoder, the first line its command prints, or `ABSENT` where it
    cannot be run; asked once a process."""
    try:
        done = subprocess.run(
            ENCODERS[tool], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return ABSENT
    lines = done.stdout.splitlines()
    return lines[0].strip() if done.returncode == 0 and lines else ABSENT


def pins(node: nodes.Node) -> dict[str, str]:
    """What a node's records pin besides the engine: the model snapshots of model work, each
    repository with its revision, and the version of each encoder the node runs (`ENCODERS`), so
    that another snapshot or another encoder makes the node stale."""
    found = {tool: encoder(tool) for tool in node.tools if tool in ENCODERS}
    if not node.gpu:
        return found
    from filmkit.narration import snapshots

    models = (snapshots.VOICE, snapshots.RECOGNIZER, snapshots.ALIGNER)
    return {**{snapshot.repo: snapshot.revision for snapshot in models}, **found}


def previous(node: str, code: str | None) -> records.RunRecord | None:
    """The node's last whole record, where one stands and can be read."""
    with contextlib.suppress(FileNotFoundError, records.Unreadable):
        found = records.read(records.place(node, code))
        return found if isinstance(found, records.RunRecord) else None
    return None


def stated(places: nodes.Places, known: dict[str, records.State]) -> dict[str, records.State]:
    """Each place that stands, by name, digests taken from `known` where they still hold."""
    found = {}
    for name, path in places.items():
        if records.file_of(path).exists():
            found[name] = records.stated(path, known.get(name))
    return found


def carried(
    node: nodes.Node,
    edition: Edition,
    way: object,
    inputs: dict[str, records.State],
    before: records.RunRecord | None,
) -> dict[str, str]:
    """Each path the node rewrites that its run read as its own previous run wrote it, with the
    digest its chain of runs first read from another writer: carried from that run where it
    carried one, else that run's own input. Bytes the previous run did not write carry nothing,
    so a hand edit between two runs stays its own."""
    if before is None:
        return {}
    writes = {nodes.place(path): name for name, path in node.outputs(edition).items()}
    found = {}
    for name, path in node.inputs(edition, way).items():
        output = writes.get(nodes.place(path))
        if output is None or name not in inputs or name not in before.inputs:
            continue
        wrote = before.outputs.get(output)
        if wrote is not None and wrote.sha256 == inputs[name].sha256:
            found[name] = before.carried.get(name, before.inputs[name].sha256)
    return found


def outcome(
    completed: bool, ended: BaseException | None, refusals: tuple[type[BaseException], ...] = ()
) -> tuple[records.Outcome, str | None]:
    """How a run ended, and the line it ended with: a command's `SystemExit`, or for a node run
    inside another command one of its owner's `refusals`, is a refusal."""
    if completed:
        return "pass", None
    if isinstance(ended, SystemExit):
        code = ended.code
        return "refuse", code if isinstance(code, str) else f"exit status {code}"
    if refusals and isinstance(ended, refusals):
        return "refuse", str(ended)
    if ended is None:
        return "refuse", None
    return "error", f"{type(ended).__name__}: {ended}".rstrip(": ")


class NodeRun:
    """One open run of a node of an edition."""

    def __init__(
        self, node: nodes.Node, code: str | None, run: Run, *, whole: bool, way: str | None
    ):
        self.node, self.code, self.whole = node, code, whole
        self.edition = edition = None if code is None else Edition(code)
        # What the seam reads itself is no access of the run, nor of a run it is nested in.
        with opens.quiet():
            self.before = previous(node.name, code)
            if len(node.ways) > 1:
                run.settings["way"] = node.way(edition, way)
            known = self.before.inputs if self.before else {}
            chosen = run.settings.get("way")
            self.inputs = stated(node.inputs(edition, chosen), known) if whole else {}
            self.carried = carried(node, edition, chosen, self.inputs, self.before)
        self.label, self.outer = nodes.key(node.name, code), os.environ.get(opens.NODE)
        os.environ[opens.NODE] = self.label
        self.meter = host.start()

    def close(
        self,
        measured: dict,
        ended: BaseException | None,
        refusals: tuple[type[BaseException], ...] = (),
    ) -> None:
        """Write the node's record from the measurement of the same run, or for a node run
        inside another command from its own (`node`)."""
        if self.outer is None:
            os.environ.pop(opens.NODE, None)
        else:
            os.environ[opens.NODE] = self.outer
        try:
            with opens.quiet():
                self.write(measured, ended, refusals)
        except Exception as error:
            # A failure of the seam is never the command's.
            unwritten(self.label, error)

    def write(
        self,
        measured: dict,
        ended: BaseException | None,
        refusals: tuple[type[BaseException], ...],
    ) -> None:
        """State the outputs and write the record."""
        measures = self.meter.stop()
        result, line = outcome(measured["completed"], ended, refusals)
        previous_class = self.before.host_class if self.before else None
        known = self.before.outputs if self.before else {}
        common = {
            "node": self.node.name,
            "edition": self.code,
            "engine": records.engine(pins(self.node)),
            "outputs": stated(self.node.outputs(self.edition), known),
            "outcome": result,
            "refusal": line,
            "measured": measures,
            "class": host.host_class(measures, gpu=self.node.gpu, previous=previous_class),
            **{key: measured[key] for key in records.MEASURED},
        }
        if self.whole:
            records.write(records.RunRecord(**common, inputs=self.inputs, carried=self.carried))
        else:
            records.write(records.PartialRecord(**common))


def unwritten(label: str, error: Exception) -> None:
    """Name a node's run record that was not written, and why, on standard error."""
    print(
        f"filmkit: the run record of {label} was not written: {type(error).__name__}: {error}",
        file=sys.stderr,
    )


def open_node(
    code: str | None, command: str, run: Run, *, whole: bool = True, way: str | None = None
) -> NodeRun | None:
    """The run of the node a command names, opened: an edition's node for an edition it applies
    to, a film-wide node for no edition. None for a command that names no node or names one
    otherwise, which is measured and writes nothing, and for one whose opening failed, which is
    named (`unwritten`), the loading of the node table among it."""
    try:
        node = table().get(command)
    except Exception as error:
        # A failure of the seam is never the command's.
        unwritten(nodes.key(command, code), error)
        return None
    if node is None:
        return None
    film = node.per == nodes.FILM
    if film != (code is None) or not film and code not in node.codes(CODES):
        return None
    try:
        return NodeRun(node, code, run, whole=whole, way=way)
    except Exception as error:
        # A failure of the seam is never the command's.
        unwritten(nodes.key(node.name, code), error)
        return None
