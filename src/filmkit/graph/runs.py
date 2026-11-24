"""A node's run at the seam: opened by `filmkit.durations.run` when a command that names a node
starts, closed when it ends (design decision 2 of record-every-run).

The opening states the inputs of the run's way, each hashed only where its size or time differs
from the node's last record, records the way among the run's settings where the node has
several, starts the host measures (`filmkit.graph.host`) and names the node and edition in
`FILMKIT_NODE`, which every child inherits (`filmkit.graph.opens`). The close states the outputs,
takes the start, seconds, load, phases and settings from the duration record the same `Run` just
gave, and writes the node's run record, or for a run that is not the node's whole run a partial
record (design decision 8). The outcome is `pass` for a run that completed, `refuse` for one that
left with a line (a `SystemExit`) or was told that it failed, and `error` for any other exception,
each with the line it ended with. A command that does a node's work again opens that node's run
inside its own (`filmkit.durations.node`), where a refusal of the owner it names is `refuse`.

Opening or closing a node's run never stops or changes the command: a failure of either is named
in one line on standard error and the node's last record stands, which the outputs this run
writes then contradict, so the plan finds the node stale and `filmkit verify` refuses its bytes.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.graph import chain, host, nodes, opens, records
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from filmkit.durations import Run


def table() -> dict[str, nodes.Node]:
    """The chain's nodes by name."""
    return {node.name: node for node in chain.TABLE}


def pins(node: nodes.Node) -> dict[str, str]:
    """The model snapshots a node declares, each repository with its revision: model work's."""
    if not node.gpu:
        return {}
    from filmkit.narration import snapshots

    found = (snapshots.VOICE, snapshots.RECOGNIZER, snapshots.ALIGNER)
    return {snapshot.repo: snapshot.revision for snapshot in found}


def previous(node: str, code: str) -> records.RunRecord | None:
    """The node's last whole record, where one stands and can be read."""
    with contextlib.suppress(FileNotFoundError, records.Unreadable):
        found = records.read(records.place(node, code))
        return found if isinstance(found, records.RunRecord) else None
    return None


def stated(places: nodes.Places, known: dict[str, records.State]) -> dict[str, records.State]:
    """Each place that stands, by name, digests taken from `known` where they still hold."""
    found = {}
    for name, path in places.items():
        where = Path(path.path if isinstance(path, records.Folder) else path)
        if where.exists():
            found[name] = records.stated(path, known.get(name))
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

    def __init__(self, node: nodes.Node, code: str, run: Run, *, whole: bool, way: str | None):
        self.node, self.code, self.whole = node, code, whole
        edition = Edition(code)
        # What the seam reads itself is no access of the run, nor of a run it is nested in.
        with opens.quiet():
            self.before = previous(node.name, code)
            if len(node.ways) > 1:
                run.settings["way"] = node.way(edition, way)
            known = self.before.inputs if self.before else {}
            chosen = run.settings.get("way")
            self.inputs = stated(node.inputs(edition, chosen), known) if whole else {}
        self.label, self.outer = nodes.key(node.name, code), os.environ.get(opens.NODE)
        os.environ[opens.NODE] = self.label
        self.meter = host.start()

    def close(
        self,
        duration: dict,
        ended: BaseException | None,
        refusals: tuple[type[BaseException], ...] = (),
    ) -> None:
        """Write the node's record from the duration record of the same run, or for a node run
        inside another command from its own measurement (`filmkit.durations.node`)."""
        if self.outer is None:
            os.environ.pop(opens.NODE, None)
        else:
            os.environ[opens.NODE] = self.outer
        try:
            with opens.quiet():
                self.write(duration, ended, refusals)
        except Exception as error:
            # A failure of the seam is never the command's.
            unwritten(self.label, error)

    def write(
        self,
        duration: dict,
        ended: BaseException | None,
        refusals: tuple[type[BaseException], ...],
    ) -> None:
        """State the outputs and write the record."""
        measures = self.meter.stop()
        result, line = outcome(duration["completed"], ended, refusals)
        previous_class = self.before.host_class if self.before else None
        known = self.before.outputs if self.before else {}
        common = {
            "node": self.node.name,
            "edition": self.code,
            "engine": records.engine(pins(self.node)),
            "outputs": stated(self.node.outputs(Edition(self.code)), known),
            "outcome": result,
            "refusal": line,
            "measured": measures,
            "class": host.host_class(measures, gpu=self.node.gpu, previous=previous_class),
            **{key: duration[key] for key in records.FROM_DURATION},
        }
        if self.whole:
            records.write(records.RunRecord(**common, inputs=self.inputs))
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
    """The run of the node a command names, opened; None for a command that names none or an
    edition the node does not apply to, which writes its duration record alone, and for one
    whose opening failed, which is named (`unwritten`)."""
    node = table().get(command)
    if code is None or node is None or code not in node.codes(CODES):
        return None
    try:
        return NodeRun(node, code, run, whole=whole, way=way)
    except Exception as error:
        # A failure of the seam is never the command's.
        unwritten(nodes.key(node.name, code), error)
        return None


def own_places(code: str, command: str, arguments: list[str]) -> bool:
    """Whether every argument that names a place below the film's root lies in a place the node
    declares, so that the run is the node's whole run; a command that names no node is."""
    node = table().get(command)
    if node is None:
        return True
    edition = Edition(code)
    places = [*node.outputs(edition).values()]
    places += [p for way in node.ways.values() for p in way(edition).values()]
    declared = [nodes.place(p) for p in places]
    root = repository.ROOT.resolve()
    for argument in arguments:
        named = Path(os.path.normpath(repository.ROOT / argument)).resolve()
        if argument.startswith("-") or not ("/" in argument or named.exists()):
            continue
        if named == root or not named.is_relative_to(root):
            continue
        if not any(nodes.overlaps(named, place) for place in declared):
            return False
    return True
