"""The plan: for the nodes asked for and every node upstream of them, each node's state and its
reasons, its host class as measured and as the table expects it, its last seconds and whether it
is ready, judged from the run records and the files as they stand. It runs nothing and writes
nothing (design decisions 5, 6 and 7 of record-every-run).

A node is `fresh` when its record judges fresh (`records.judge`: size and time first, the digest
where either differs), `stale` with each reason otherwise, and `behind` when it is fresh and a
node upstream is not. It is ready when every node upstream is fresh and every input of its way
exists. A node without a record is `unmeasured`, beside the class the table expects of it.

A path that several runs write is judged by decision 5: among the standing records that state it
as an output, a partial record among them, the one whose run ended last binds the file, which is
compared with that record alone. An earlier binding of the path holds through a later run of a
rewriter that follows its node and read the path as it stated it, or of a `replaces` writer, with
no order between the two, where that later binding holds itself: a chain of such runs reaches the
latest record. The input of a reader that a rewriter follows is such a binding. A writer's output
that no holding run carries is stale, replaced by an earlier writer's run. Bytes that the binding
record does not state, and bytes that a rewriter read after an earlier writer's run that no
declared writer's run between them wrote, are bytes that no declared writer accounts for, and
every node whose record binds the path through the writers is stale for them. A node whose
partial record ended after its record, with other outputs than that record states, is stale,
changed by a partial run (decision 8).

Each reason has a kind. `unaccounted` (bytes no record of a declared writer accounts for) and
`blind` (a file whose size and time held while its digest changed, which only `full` sees) are
the two that `filmkit verify` refuses; the others (`record`, `input`, `missing`, `order`,
`partial`) it lists.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from filmkit.graph import chain, nodes, records, runs
from filmkit.production import Edition

if TYPE_CHECKING:
    from collections.abc import Iterable

FRESH, STALE, BEHIND, UNMEASURED = "fresh", "stale", "behind", "unmeasured"
READS = "reads"
# The kinds of reason that `filmkit verify` refuses.
REFUSED = ("unaccounted", "blind")


@dataclass(frozen=True)
class Reason:
    """Why a node is stale: its kind, the words, and the path it concerns, if one."""

    kind: str
    text: str
    path: str | None = None


@dataclass
class Entry:
    """One node of one edition as the plan judged it."""

    key: str
    state: str
    reasons: list[Reason]
    host_class: str
    expected: str
    seconds: float | None
    ready: bool

    def stated(self) -> dict:
        """The entry as `filmkit plan --json` prints it."""
        return {
            "node": self.key,
            "state": self.state,
            "reasons": [reason.text for reason in self.reasons],
            "class": self.host_class,
            "expected": self.expected,
            "seconds": self.seconds,
            "ready": self.ready,
        }


@dataclass(frozen=True)
class Standing:
    """What stands for one node of one edition: its record and its partial record, each read or
    the reason it cannot be, and the way its inputs are judged by."""

    node: nodes.Node
    edition: Edition
    record: records.RunRecord | records.Unreadable | None
    partial: records.PartialRecord | None
    way: str

    @property
    def whole(self) -> records.RunRecord | None:
        return self.record if isinstance(self.record, records.RunRecord) else None


@dataclass(frozen=True)
class Binding:
    """A standing record that states a path several runs write: the node, the side and name it
    states the path under, the state, when its run ended, the writer's kind and the nodes a
    rewriter follows, and for a rewriter the path as it read it."""

    key: str
    node: str
    side: str
    name: str
    state: records.State
    end: datetime
    kind: str
    after: tuple[str, ...] = ()
    read: tuple[str, records.State] | None = None


@dataclass
class Settled:
    """What the judgment of the paths several runs write found: each node's reasons, and the
    files left out of each node's own judgment, by side and name."""

    reasons: dict[str, list[Reason]] = field(default_factory=lambda: defaultdict(list))
    settled: dict[str, set[tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))


@dataclass(frozen=True)
class Planned:
    """A plan: its entries in the derived order, and how many files it hashed."""

    entries: list[Entry]
    hashed: int


def found(path: Path) -> records.RunRecord | records.PartialRecord | records.Unreadable | None:
    """The record at a path, the reason it cannot be read, or None where none stands."""
    try:
        return records.read(path)
    except FileNotFoundError:
        return None
    except records.Unreadable as error:
        return error


def standing(table: nodes.Table, key: str) -> Standing:
    """A node's records as they stand, and the way its inputs are judged by: the recorded way."""
    node, edition = table.node(key)
    whole = found(records.place(node.name, edition.code))
    partial = found(records.place(node.name, edition.code, partial=True))
    if isinstance(whole, records.PartialRecord):
        whole = records.Unreadable(f"{records.place(node.name, edition.code)} is a partial record")
    recorded = whole.settings.get("way") if isinstance(whole, records.RunRecord) else None
    partial = partial if isinstance(partial, records.PartialRecord) else None
    return Standing(node, edition, whole, partial, node.way(edition, recorded))


def ended(record: records.RunRecord | records.PartialRecord) -> datetime:
    """When a record's run ended."""
    return datetime.fromisoformat(record.started_at) + timedelta(seconds=record.seconds)


def followed(table: nodes.Table) -> set[tuple[str, Path]]:
    """Each reader that a rewriter of a path follows, with the path: the reader's binding of it
    holds through that rewriter's later run."""
    pairs = set()
    for output, writers in table.shared.items():
        names = {writer.node for writer in writers}
        for writer in writers:
            if writer.kind != nodes.REWRITES:
                continue
            for code in table.nodes[writer.node].codes(table.codes):
                path = nodes.place(table.nodes[writer.node].outputs(Edition(code))[output])
                pairs |= {(nodes.key(a, code), path) for a in writer.after if a not in names}
    return pairs


def kind_of(table: nodes.Table, node: str, output: str) -> nodes.Writer:
    """A node's kind as a writer of an output: as `SHARED` declares it, else `replaces`."""
    declared = (w for w in table.shared.get(output, ()) if w.node == node)
    return next(declared, nodes.Writer(node, nodes.REPLACES))


def bound(table: nodes.Table, stand: dict[str, Standing]) -> dict[Path, list[Binding]]:
    """Each path by the standing records that state it as an output, and the inputs of the
    readers that a rewriter of it follows."""
    follows, paths = followed(table), defaultdict(list)
    for key, s in stand.items():
        writes = {nodes.place(p): n for n, p in s.node.outputs(s.edition).items()}
        reads = {nodes.place(p): n for n, p in s.node.inputs(s.edition, s.way).items()}
        for record in (s.whole, s.partial):
            if record is None:
                continue
            for path, name in writes.items():
                if name not in record.outputs:
                    continue
                partial = isinstance(record, records.PartialRecord)
                writer = nodes.Writer(s.node.name, nodes.REPLACES)
                writer = writer if partial else kind_of(table, s.node.name, name)
                taken = None if partial else reads.get(path)
                was = record.inputs.get(taken) if taken else None
                read = (taken, was) if was else None
                state, end = record.outputs[name], ended(record)
                paths[path].append(
                    Binding(key, s.node.name, "output", name, state, end, *writer[1:], read)
                )
        if s.whole is not None:
            for path, name in reads.items():
                if (key, path) in follows and name in s.whole.inputs:
                    state, end = s.whole.inputs[name], ended(s.whole)
                    paths[path].append(Binding(key, s.node.name, "input", name, state, end, READS))
    return paths


def carried(earlier: Binding, by: Binding) -> bool:
    """Whether a later run carries an earlier binding of a path: a rewriter that follows the
    earlier node and read the path as it stated it, or a `replaces` peer of a `replaces` writer."""
    if by.end <= earlier.end or by is earlier:
        return False
    if by.kind == nodes.REWRITES and earlier.node in by.after:
        return by.read is not None and by.read[1].sha256 == earlier.state.sha256
    return by.kind == earlier.kind == nodes.REPLACES and earlier.side == "output"


def holding(latest: Binding, binders: list[Binding], writers: list[Binding]) -> list[Binding]:
    """The bindings of a path that hold: the latest writer's, and each that a holding binding
    carries, so that a run whose own binding a later writer replaced carries nothing."""
    held = [latest]
    grew = True
    while grew:
        grew = False
        for b in binders:
            if all(b is not h for h in held) and any(carried(b, by) for by in held):
                held.append(b)
                grew = True
    return held


def unwritten(earlier: Binding, writers: list[Binding]) -> Binding | None:
    """The later run of a rewriter that follows an earlier writer and read other bytes than it
    wrote, where no declared writer's run between the two wrote the bytes the rewriter read: the
    bytes it read were written by no declared writer. None where there is no such run."""
    for by in writers:
        if by.end <= earlier.end or by.kind != nodes.REWRITES or earlier.node not in by.after:
            continue
        if by.read is None or by.read[1].sha256 == earlier.state.sha256:
            continue
        read = by.read[1].sha256
        if not any(earlier.end < c.end < by.end and c.state.sha256 == read for c in writers):
            return by
    return None


def settle(paths: dict[Path, list[Binding]], full: bool) -> Settled:
    """Judge each path that several standing records bind by decision 5."""
    out = Settled()
    for binders in paths.values():
        writers = [b for b in binders if b.side == "output"]
        if not writers or len(binders) < 2:
            continue
        latest = max(writers, key=lambda b: b.end)
        compared = records.compare("output", latest.name, latest.state, full=full)
        relative = latest.state.path
        for b in binders:
            out.settled[b.key].add((b.side, b.name))
            if b.read is not None:
                out.settled[b.key].add(("input", b.read[0]))
        unaccounted = []
        if compared.result == "missing":
            out.reasons[latest.key].append(
                Reason("missing", f"output {latest.name} missing: {relative}", relative)
            )
        elif compared.result == "blind":
            says = f"{relative} {records.SAYS['blind']}"
            for key in {b.key for b in binders}:
                out.reasons[key].append(Reason("blind", says, relative))
        elif compared.result == "changed":
            unaccounted.append(f"{relative} changed by no declared writer")
        before = {by.key for b in writers if (by := unwritten(b, writers)) is not None}
        unaccounted += [
            f"{relative} changed by no declared writer before the run of {key}"
            for key in sorted(before)
        ]
        for text in unaccounted:
            for key in {b.key for b in binders}:
                out.reasons[key].append(Reason("unaccounted", text, relative))
        if before:
            continue
        held = holding(latest, binders, writers)
        for b in binders:
            if any(b is h for h in held):
                continue
            if b.side == "input":
                out.settled[b.key].discard((b.side, b.name))
                continue
            later = sorted(c.key for c in writers if c.end > b.end and c.key != b.key)
            says = f"its output {b.name} replaced by an earlier writer's run ({', '.join(later)})"
            if not any(c.node in b.after for c in writers if c.end > b.end):
                says = f"its output {b.name} was changed before the run of {', '.join(later)}"
            out.reasons[b.key].append(Reason("order", says, relative))
    return out


def judged(
    s: Standing, settled: Settled, key: str, running: records.Engine, full: bool
) -> list[Reason]:
    """One node's reasons."""
    places = s.node.inputs(s.edition, s.way).items()
    declared = {name: records.below_root(nodes.place(path)) for name, path in places}
    judgment = records.judge(
        s.record,
        declared=declared,
        running=running,
        full=full,
        settled=frozenset(settled.settled.get(key, ())),
    )
    reasons = [Reason("record", text) for text in judgment.own]
    for compared in judgment.files:
        if compared.result not in records.SAYS:
            continue
        kind = compared.result if compared.result in ("missing", "blind") else compared.side
        kind = "unaccounted" if kind == "output" else kind
        text = f"{compared.side} {compared.name} {records.SAYS[compared.result]}: {compared.path}"
        reasons.append(Reason(kind, text, compared.path))
    if s.partial is not None and changed_by_part(s.partial, s.whole):
        reasons.append(Reason("partial", "changed by a partial run"))
    return reasons + settled.reasons.get(key, [])


def changed_by_part(partial: records.PartialRecord, whole: records.RunRecord | None) -> bool:
    """Whether a partial run changed the node: it ended after the node's record, and the outputs
    it left differ from the ones that record states. A stage written elsewhere, or made again
    from the same sources, leaves the node as its record states it."""
    if whole is None:
        return True
    if ended(partial) <= ended(whole):
        return False
    left = {name: state.sha256 for name, state in partial.outputs.items()}
    return left != {name: state.sha256 for name, state in whole.outputs.items()}


def wanted(table: nodes.Table, targets: Iterable[str]) -> set[str]:
    """The nodes asked for, `<node>:<code>` or `<node>:all`, and every node upstream of them;
    every node where none is asked for. An unknown target is refused, naming the nodes."""
    asked = set()
    for target in targets:
        name, _, code = target.rpartition(":")
        node = table.nodes.get(name)
        every = node.codes(table.codes) if node else table.codes
        keys = [nodes.key(name, c) for c in every] if code == "all" else [target]
        unknown = [k for k in keys if k not in table.edges]
        if unknown or not name:
            known = ", ".join(table.nodes)
            msg = (
                f"{target} names no node of the plan; its nodes are {known}, each as <node>:<code>"
            )
            raise ValueError(msg)
        asked |= set(keys)
    asked = asked or set(table.edges)
    return asked | {up for key in asked for up in table.upstream(key)}


def exists(path: object) -> bool:
    return os.path.lexists(nodes.place(path))


def plan(
    table: nodes.Table | None = None, targets: Iterable[str] = (), *, full: bool = False
) -> Planned:
    """The entries of the nodes asked for and every node upstream, in the derived order; each
    file that several records state is hashed once (`records.once`)."""
    table = table or chain.table()
    keys = wanted(table, targets)
    with records.once() as taken:
        entries = judge_all(table, keys, full)
    return Planned(entries, len(taken))


def judge_all(table: nodes.Table, keys: set[str], full: bool) -> list[Entry]:
    """Each node of `keys` judged, in the derived order."""
    stand = {key: standing(table, key) for key in table.order}
    settled = settle(bound(table, stand), full)
    states: dict[str, str] = {}
    engines = {gpu: records.engine(runs.pins(n)) for n in table.nodes.values() for gpu in [n.gpu]}
    entries = []
    for key in (k for k in table.order if k in keys):
        s = stand[key]
        reasons = judged(s, settled, key, engines[s.node.gpu], full)
        upstream = table.upstream(key)
        behind = any(states[up] != FRESH for up in table.edges[key])
        states[key] = STALE if reasons else BEHIND if behind else FRESH
        inputs = s.node.inputs(s.edition, s.way).values()
        ready = all(states[up] == FRESH for up in upstream) and all(map(exists, inputs))
        whole = s.whole
        entries.append(
            Entry(
                key,
                states[key],
                reasons,
                whole.host_class if whole else UNMEASURED,
                s.node.expected,
                whole.seconds if whole else None,
                ready,
            )
        )
    return entries
