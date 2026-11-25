"""The plan: for the nodes asked for and every node upstream of them, each node's state and its
reasons, its host class as measured and as the table expects it, its last seconds and whether it
is ready, judged from the run records and the files as they stand. It runs nothing and writes
nothing (design decisions 5, 6 and 7 of record-every-run).

A node is `stale` when its own record judges stale (`records.judge`: size and time first, the
digest where either differs), with each reason; `behind` when it is fresh by its own record and a
node upstream of it by a path is stale or behind, so that it will likely run when that node has;
`waiting` when it is fresh by its own record, nothing upstream of it by a path is stale or
behind, and a gate it waits for, directly or through a node upstream of it by a path, is not
fresh (design decision 4 of build-a-film-by-its-verbs); and `fresh` otherwise. A node that the
table declares a gate whose verdict depends only on what its record states (`Node.judges`),
stale only because its last run refused with nothing it reads changed since, and with every node
upstream of it by a path fresh, so that nothing will change what it reads before its turn, is
stale and not ready, and states that run's line (`Entry.standing`): run again, it would refuse
the same. The four are
judged in one pass over the order derived over paths and waits together, so every gate is judged
before every node that waits for it. A node is ready when every node upstream of it by a path is
fresh, every gate it waits for is fresh, and every input of its way exists; a waiting node names
each gate that holds it with that gate's state. A node without a record is `unmeasured`, beside
the class the table expects of it.

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

FRESH, STALE, BEHIND, WAITING, UNMEASURED = "fresh", "stale", "behind", "waiting", "unmeasured"
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
    # When the node's last whole run started and ended, where one is recorded.
    span: tuple[datetime, datetime] | None = None
    # The gates that hold the node, each with its state: none unless it is waiting.
    held: dict[str, str] = field(default_factory=dict)
    # The line its last run refused with, for a node whose refusal stands (`Node.judges`) where
    # that refusal alone makes it stale.
    standing: str | None = None

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
            "waits": [{"node": gate, "state": state} for gate, state in self.held.items()],
            "standing": self.standing,
        }


@dataclass(frozen=True)
class Standing:
    """What stands for one run of a node, of an edition or of the film: its record and its partial
    record, each read or the reason it cannot be, and the way its inputs are judged by."""

    node: nodes.Node
    edition: Edition | None
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
    rewriter follows, and for a rewriter the input's name, the digest it read and the digest its
    chain of runs first read (`records.RunRecord.carried`), the same where it carried none."""

    key: str
    node: str
    side: str
    name: str
    state: records.State
    end: datetime
    kind: str
    after: tuple[str, ...] = ()
    read: tuple[str, str, str] | None = None


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
    code = edition.code if edition else None
    whole = found(records.place(node.name, code))
    partial = found(records.place(node.name, code, partial=True))
    if isinstance(whole, records.PartialRecord):
        whole = records.Unreadable(f"{records.place(node.name, code)} is a partial record")
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
            rewriter = table.nodes[writer.node]
            for _, edition in rewriter.instances(table.codes):
                path = nodes.place(rewriter.outputs(edition)[output])
                code = edition.code if edition else None
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
                origin = record.carried.get(taken, was.sha256) if was else None
                read = (taken, was.sha256, origin) if was else None
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
        return by.read is not None and earlier.state.sha256 in by.read[1:]
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
        if by.read is None or earlier.state.sha256 in by.read[1:]:
            continue
        read = by.read[1]
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


# The target that names every node of the table but those `chain.NOT_IN_ALL` names.
ALL = "all"


def named(table: nodes.Table, target: str) -> list[str]:
    """The keys a target names: a node or a group of nodes (`Table.groups`), for one edition or
    for `all` of them, `<name>:<code>`; a film-wide node by its name alone; none where it names
    nothing of the table."""
    name, code = nodes.split(target)
    members = table.groups.get(name, (name,))
    found = []
    for member in members:
        node = table.nodes.get(member)
        if node is None:
            return []
        every = node.codes(table.codes)
        found += [nodes.key(member, c) for c in every] if code == ALL else [nodes.key(member, code)]
    return [key for key in found if key in table.edges] if name in table.groups else found


def unlisted(table: nodes.Table, targets: Iterable[str]) -> set[str]:
    """The nodes a plan judges and does not list: for `all`, those `chain.NOT_IN_ALL` names, which
    `filmkit narrate` runs, unless another target names them."""
    targets = list(targets)
    if ALL not in targets:
        return set()
    left = {k for k in table.edges if nodes.split(k)[0] in chain.NOT_IN_ALL}
    return left - {k for t in targets if t != ALL for k in named(table, t)}


def wanted(table: nodes.Table, targets: Iterable[str]) -> set[str]:
    """The nodes the targets name (`named`), or for `all` every node but those `chain.NOT_IN_ALL`
    names, and every node upstream of them by a path or by a wait, which the plan judges; every
    node where none is asked for. A target that names nothing is refused in one line, naming the
    groups and the nodes."""
    asked = set()
    for target in targets:
        if target == ALL:
            asked |= set(table.edges) - unlisted(table, [ALL])
            continue
        keys = named(table, target)
        if not keys or any(k not in table.edges for k in keys):
            groups = ", ".join(table.groups) or "none"
            msg = (
                f"{target} names no node or group of the plan; its groups are {groups}, each as "
                f"<group>:<code> or <group>:all; its nodes are {', '.join(table.nodes)}, each as "
                "<node>:<code> or <node>:all but a film-wide node, which is named alone; or all"
            )
            raise ValueError(msg)
        asked |= set(keys)
    asked = asked or set(table.edges)
    return asked | {up for key in asked for up in table.closure(key)}


def exists(path: object) -> bool:
    return os.path.lexists(records.file_of(path))


def plan(
    table: nodes.Table | None = None, targets: Iterable[str] = (), *, full: bool = False
) -> Planned:
    """The entries of the nodes asked for and every node upstream, in the derived order; each
    file that several records state is hashed once (`records.once`)."""
    table, targets = table or chain.table(), list(targets)
    keys, hidden = wanted(table, targets), unlisted(table, targets)
    with records.once() as taken:
        entries = [entry for entry in judge_all(table, keys, full) if entry.key not in hidden]
    return Planned(entries, len(taken))


def judge_all(table: nodes.Table, keys: set[str], full: bool) -> list[Entry]:
    """Each node of `keys` judged, in the derived order."""
    stand = {key: standing(table, key) for key in table.order}
    settled = settle(bound(table, stand), full)
    states: dict[str, str] = {}
    engines = {name: records.engine(runs.pins(node)) for name, node in table.nodes.items()}
    entries, held = [], {}
    for key in (k for k in table.order if k in keys):
        s = stand[key]
        reasons = judged(s, settled, key, engines[s.node.name], full)
        upstream = table.upstream(key)
        behind = any(states[up] in (STALE, BEHIND) for up in table.edges[key])
        # The gates that hold the node: its own that are not fresh, and those holding a node
        # upstream of it by a path.
        held[key] = {g: states[g] for g in sorted(table.waits.get(key, ())) if states[g] != FRESH}
        for up in table.edges[key]:
            held[key] |= held[up]
        states[key] = STALE if reasons else BEHIND if behind else WAITING if held[key] else FRESH
        inputs = s.node.inputs(s.edition, s.way).values()
        gates = all(states[g] == FRESH for g in table.waits.get(key, ()))
        whole = s.whole
        # A refused run's own reason is its outcome, which no other reason joins while nothing
        # it reads has changed; its refusal stands where the table says the node's does and no node
        # upstream of it will run first and change what it reads.
        quiet = all(states[up] == FRESH for up in upstream)
        refused = s.node.judges is not None and whole is not None and whole.outcome == "refuse"
        refusal = None
        if refused and len(reasons) == 1 and quiet:
            refusal = whole.refusal or f"{key}: its run refused"
        ready = quiet and gates and all(map(exists, inputs))
        ready = ready and refusal is None
        entries.append(
            Entry(
                key,
                states[key],
                reasons,
                whole.host_class if whole else UNMEASURED,
                s.node.expected,
                whole.seconds if whole else None,
                ready,
                (datetime.fromisoformat(whole.started_at), ended(whole)) if whole else None,
                held[key] if states[key] == WAITING else {},
                refusal,
            )
        )
    return entries
