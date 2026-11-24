"""How a node table is stated and loaded: its nodes, the edges derived from the paths each reads
and writes, and the order from the standard library's `graphlib`. The engine's own table is
`filmkit.graph.chain`.

A node is one of today's chain commands for one edition (design decision 1 of record-every-run),
named as its duration record names it. Each of its ways states its inputs as a function of an
edition that returns paths by name, and its outputs likewise; a folder names its members by a
pattern (`records.Folder`).

A path that several nodes write is declared in the table's shared paths with each writer and its
kind: one that
`rewrites` it after the writers it names, or one that `replaces` it whole (design decision 5).
The edges follow: a node that reads a path comes after each node that writes it, a rewriter
after the writers it names, and replacers of one path have no edge between them. Loading a
table refuses a cycle, naming its nodes, a path that two nodes write with no declaration,
naming the path and the nodes, and a node whose places bind one name to two places, naming the
name: a union of `Places` refuses it, so that no place is lost under another's name.
"""

from __future__ import annotations

import contextlib
import contextvars
import graphlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import filmkit.repository as repository
from filmkit.graph.records import Folder, HostClass
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

# The kinds of a writer of a path that several nodes write (design decision 5).
REWRITES, REPLACES = "rewrites", "replaces"
# While it holds, a place that a table names only where it stands is named as if it stood, so
# that the check of each run's opens can ask which absent files a node would read.
_AS_IF_STANDING: contextvars.ContextVar[bool] = contextvars.ContextVar("as_if", default=False)


@dataclass(frozen=True)
class Node:
    """One command of an edition's build chain: its ways, each with its inputs, its outputs,
    the host class it is expected to measure at, and whether it is model work. A node of several
    ways takes `default_way` where no run says which; `tools` names the tools it starts whose
    reads are seen only through their arguments; `editions`, given the film's editions in their
    declared order, names those the node applies to, every one by default."""

    name: str
    ways: dict[str, Callable[[Edition], Places]]
    outputs: Callable[[Edition], Places]
    expected: HostClass
    gpu: bool = False
    default_way: Callable[[Edition], str] | None = None
    tools: tuple[str, ...] = ()
    editions: Callable[[tuple[str, ...]], tuple[str, ...]] | None = None

    def codes(self, codes: tuple[str, ...]) -> tuple[str, ...]:
        """The editions, of the film's, that the node applies to."""
        return tuple(self.editions(codes)) if self.editions else tuple(codes)

    def way(self, edition: Edition, recorded: object = None) -> str:
        """The way a run took, or else the way the node takes by default."""
        if isinstance(recorded, str) and recorded in self.ways:
            return recorded
        return self.default_way(edition) if self.default_way else next(iter(self.ways))

    def inputs(self, edition: Edition, way: object = None) -> Places:
        """The inputs of a way, by default the node's own."""
        return self.ways[self.way(edition, way)](edition)


class Writer(NamedTuple):
    """A node that writes a path several nodes write, its kind, and for a rewriter the writers
    it follows."""

    node: str
    kind: str
    after: tuple[str, ...] = ()


class TableError(ValueError):
    """A node table that cannot be ordered, leaves a writer undeclared or binds one name of a
    node's places to two places."""


class Places(dict[str, "Path | Folder"]):
    """A node's places by name; a union that binds one name to two places is refused."""

    def __or__(self, other: dict) -> Places:
        return Places(joined(self, other))

    def __ror__(self, other: dict) -> Places:
        return Places(joined(other, self))

    def __ior__(self, other: dict) -> Places:  # type: ignore[override]
        self.update(joined(self, other))
        return self


def joined(first: dict, second: dict) -> dict:
    """Two sets of places in one, refused where a name stands for two places."""
    clash = sorted(n for n in first.keys() & second.keys() if place(first[n]) != place(second[n]))
    if clash:
        raise TableError(f"a node's places bind {', '.join(clash)} to two places each")
    return {**first, **second}


def key(node: str, code: str) -> str:
    """A node of one edition, as the plan names it: `<node>:<code>`."""
    return f"{node}:{code}"


def place(path: Path | Folder) -> Path:
    """The file or folder a declared path names, resolved."""
    return Path(path.path if isinstance(path, Folder) else path).resolve()


def overlaps(a: Path, b: Path) -> bool:
    """Whether two resolved places name one file or one holds the other, compared by their names
    (`Path.is_relative_to` compares them part by part, many times slower)."""
    first, second = f"{a}{os.sep}", f"{b}{os.sep}"
    return first.startswith(second) or second.startswith(first)


@dataclass(frozen=True)
class Table:
    """A loaded table: its nodes by name, its declared writers by output name, its editions,
    each node's predecessors by key and the derived order."""

    nodes: dict[str, Node]
    shared: dict[str, tuple[Writer, ...]]
    codes: tuple[str, ...]
    edges: dict[str, frozenset[str]]
    order: tuple[str, ...]

    def node(self, named: str) -> tuple[Node, Edition]:
        """A node of an edition by its key."""
        name, code = named.rsplit(":", 1)
        return self.nodes[name], Edition(code)

    def upstream(self, named: str) -> set[str]:
        """Every node before one, transitively."""
        found, pending = set(), list(self.edges[named])
        while pending:
            before = pending.pop()
            if before not in found:
                found.add(before)
                pending.extend(self.edges[before])
        return found


def written(nodes: dict[str, Node], codes: Iterable[str]) -> dict[Path, list[tuple[str, str]]]:
    """Each output path of every node of every edition, with the keys and output names that
    write it."""
    found: dict[Path, list[tuple[str, str]]] = {}
    for node in nodes.values():
        for code in node.codes(tuple(codes)):
            for name, path in node.outputs(Edition(code)).items():
                found.setdefault(place(path), []).append((key(node.name, code), name))
    return found


def undeclared(paths: dict[Path, list[tuple[str, str]]], shared: dict) -> list[str]:
    """Each path two nodes write that `shared` does not declare with exactly those writers."""
    refused = []
    for path, by in paths.items():
        if len(by) < 2:
            continue
        names = {name for _, name in by}
        nodes = sorted({named.rsplit(":", 1)[0] for named, _ in by})
        declared = len(names) == 1 and {w.node for w in shared.get(next(iter(names)), ())}
        if declared != set(nodes):
            keys = ", ".join(sorted(named for named, _ in by))
            refused.append(f"{repository.relative(path)} is written by {keys} with no declaration")
    return refused


def follows(writer: str, output: str, other: str, shared: dict) -> bool:
    """Whether a declared rewriter of an output comes after another node: one it names."""
    return any(w.node == writer and other in w.after for w in shared.get(output, ()))


def edges(nodes: dict[str, Node], shared: dict, codes: tuple[str, ...]) -> dict[str, set[str]]:
    """Each node's predecessors: the writers of each path it reads, but a rewriter that names
    the reader among those it follows, and for a rewriter the nodes it names; replacers of one
    path have no edge between them."""
    paths = written(nodes, codes)
    before: dict[str, set[str]] = {
        key(node.name, c): set() for node in nodes.values() for c in node.codes(codes)
    }
    for node in nodes.values():
        for code in node.codes(codes):
            reader, edition = key(node.name, code), Edition(code)
            reads = {place(p) for way in node.ways.values() for p in way(edition).values()}
            for out, by in paths.items():
                if not any(overlaps(read, out) for read in reads):
                    continue
                for named, output in by:
                    writer = named.rsplit(":", 1)[0]
                    if writer == node.name or follows(writer, output, node.name, shared):
                        continue
                    before[reader].add(named)
    for by in paths.values():
        for named, output in by:
            name, code = named.rsplit(":", 1)
            for writer in shared.get(output, ()):
                if writer.node == name and writer.kind == REWRITES:
                    before[named].update(
                        k for after in writer.after if (k := key(after, code)) in before
                    )
    return before


def load(nodes: Iterable[Node], shared: dict, codes: tuple[str, ...] = CODES) -> Table:
    """Load a table: refused for a path two nodes write with no declaration, naming it and its
    writers, and for a cycle, naming its nodes."""
    named = {node.name: node for node in nodes}
    refused = undeclared(written(named, codes), shared)
    if refused:
        raise TableError("; ".join(refused))
    before = edges(named, shared, codes)
    sorter = graphlib.TopologicalSorter(before)
    try:
        order = tuple(sorter.static_order())
    except graphlib.CycleError as error:
        cycle = " -> ".join(error.args[1])
        raise TableError(f"the node table has a cycle: {cycle}") from None
    frozen = {name: frozenset(found) for name, found in before.items()}
    return Table(named, dict(shared), tuple(codes), frozen, order)


def stands(path: Path) -> bool:
    """Whether a place that a table names only where it stands is named: it stands, or
    `as_if_standing` holds."""
    return _AS_IF_STANDING.get() or path.is_file()


@contextlib.contextmanager
def as_if_standing() -> Iterator[None]:
    """Name every place that a table names only where it stands, while the block runs."""
    token = _AS_IF_STANDING.set(True)
    try:
        yield
    finally:
        _AS_IF_STANDING.reset(token)
