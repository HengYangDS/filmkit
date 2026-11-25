"""`filmkit build`: the targets made fresh from the run records, one node at a time (design
decision 3 of build-a-film-by-its-verbs).

A build takes the targets' closure, the nodes they name and every node upstream of them by a
path or by a wait (`plan.wanted`), and visits it in the order the table derives over both. At
each node's turn it judges the node again against the files as they stand (`plan.plan`), so
that a node behind only because a node upstream was stale is fresh again once that node has run
without changing its outputs, and a node held by a gate that ran again and passed is fresh by
its own inputs: neither is run. It runs a node, its owner's call (`Node.run`) in this process
inside the seam (`runs.run`), which writes the node's run record, only where the node is stale,
and not where its last run refused with nothing it reads changed since (`plan.Entry.refused`):
that refusal stands as the node's, in its own line. A node behind a refused or failed node, or
waiting on a gate that did not pass, is not run; nodes not downstream of it go on. A node with
no run, the narration, is never run here.

Before it runs anything it schedules the closure as the host's rules ask (design decision 5;
`refusals`): it refuses a closure that holds a stale narration, naming `filmkit narrate`; one
that holds heavy work that will run while light work that can run now is stale, naming the
light `filmkit build` to run first, outside any ticket; a node whose refusal stands, and every
node downstream of it, is no work that will run; and one whose heavy work that will run
has more than one name, unless every such node is measured and their last seconds sum to at most
`host.SHARED_TICKET_SECONDS`, printing the invocations to run in order, one ticket each. Heavy
work that will run is a heavy or GPU node, by its measured class or else the class the table
expects, that is stale or behind; a waiting node is never counted. A closure with no heavy work
that will run is a light invocation, which runs outside any ticket.

The build ends with one line for each node that refused or failed. It returns 2 where a node
failed, an exception of its owner that is no refusal, whose traceback it prints, or a tool the
host lacks; else 1 where a node refused or was held; and 0 where every node of the closure is
fresh (design decision 19). An interrupt or a request to end ends the running node as any
command ends (`child_processes.ending`) and runs no further node. It writes no tracked file and
takes no host ticket.
"""

from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import filmkit.child_processes as child_processes
import filmkit.tools as tools
from filmkit.captions import CaptionError
from filmkit.delivery.packaging import PackagingError
from filmkit.graph import build_command, host, narrate_command, nodes, plan, records, runs
from filmkit.media import MediaError
from filmkit.narration.anchors import AnchorError
from filmkit.picture.errors import PictureError
from filmkit.production import UnassembledError
from filmkit.review import ReviewError
from filmkit.soundtrack.fit import REFUSALS as FIT_REFUSALS

if TYPE_CHECKING:
    from collections.abc import Iterable

# The refusals of the nodes' owners, each a node's refusal in one line; any other exception is
# the node's failure.
REFUSALS = (
    *FIT_REFUSALS,
    CaptionError,
    PictureError,
    tools.ToolError,
    MediaError,
    PackagingError,
    ReviewError,
    UnassembledError,
    AnchorError,
)


@dataclass
class Built:
    """What a build did: the nodes it ran, those it left for a node before them that did not
    pass, and each refusal and each failure in one line."""

    ran: list[str] = field(default_factory=list)
    held: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def status(self) -> int:
        """The command's exit status: a failure first, then a refusal or a node held."""
        if self.failed:
            return child_processes.UNFINISHED
        held = self.refused or self.held
        return child_processes.REFUSED if held else child_processes.FINISHED


def state(table: nodes.Table, key: str) -> plan.Entry:
    """A node as the plan judges it now, against the files as they stand."""
    (entry,) = [entry for entry in plan.plan(table, [key]).entries if entry.key == key]
    return entry


def run_node(table: nodes.Table, key: str) -> tuple[int, str | None]:
    """Run one node's owner inside the seam: the exit status its run ends with, and its refusal
    or failure in one line, or None where it passed. An owner's refusal (`REFUSALS`, or a
    command's line) is `REFUSED`; any other exception is `UNFINISHED`, a tool the host lacks in
    its own words and any other with its traceback printed, and its record's outcome is
    `error`."""
    node, edition = table.node(key)
    code = edition.code if edition else None
    try:
        with runs.run(code, node.name):
            try:
                node.run(edition)
            except REFUSALS as error:
                raise SystemExit(f"{key}: {error}") from None
    except SystemExit as ended:
        status = ended.code
        if isinstance(status, str):
            return child_processes.REFUSED, status
        status = child_processes.REFUSED if status is None else status
        return status, f"{key}: exit status {status}"
    except Exception as error:
        tool = child_processes.missing(error)
        if tool is not None:
            return child_processes.UNFINISHED, f"{key}: {tool}"
        traceback.print_exc(file=sys.stderr)
        return child_processes.UNFINISHED, f"{key}: {type(error).__name__}: {error}".rstrip(": ")
    return child_processes.FINISHED, None


def standing(key: str, line: str) -> str:
    """The line of a refusal that stands, which the build does not run again: the node's own
    line, named by its key, and why it was not run."""
    named = line if line.startswith(f"{key}: ") else f"{key}: {line}"
    return f"{named} (its last run's refusal; nothing it reads has changed, so it was not run)"


def heavy(entry: plan.Entry) -> bool:
    """Whether a node is heavy or GPU work: by its measured class, or else the one expected."""
    measured = entry.host_class != plan.UNMEASURED
    return (entry.host_class if measured else entry.expected) in ("heavy", "gpu")


def stands(table: nodes.Table, entries: list[plan.Entry]) -> list[plan.Entry]:
    """The nodes whose refusal stands, which no build runs again; the narration's, which no build
    runs, is the narration's to answer."""
    return [e for e in entries if e.refused is not None and table.node(e.key)[0].run is not None]


def will_run(table: nodes.Table, entries: list[plan.Entry]) -> list[plan.Entry]:
    """The work a build of the closure will run, as the plan judged it: each node stale or behind,
    but a node whose refusal stands and every node downstream of it."""
    standing_keys = {entry.key for entry in stands(table, entries)}
    return [
        entry
        for entry in entries
        if entry.state in (plan.STALE, plan.BEHIND)
        and entry.key not in standing_keys
        and not table.closure(entry.key) & standing_keys
    ]


def refusals(table: nodes.Table, entries: list[plan.Entry]) -> list[str]:
    """Why a closure, as the plan judged it, must not run as one invocation, each in one line and
    naming what to run instead; none where it may (design decision 5)."""
    run = will_run(table, entries)
    found = [
        f"{entry.key} is stale and narration is no build's: "
        f"{narrate_command(nodes.split(entry.key)[1])}"
        for entry in run
        if table.node(entry.key)[0].run is None
    ]
    weighty = [entry for entry in run if heavy(entry)]
    first = {e.key for e in weighty}
    light = [
        entry.key for entry in run if not heavy(entry) and not table.closure(entry.key) & first
    ]
    if weighty and light:
        found.append(
            f"light work can run now and runs first, outside any ticket: {build_command(light)}"
        )
    if found:
        return found
    names = list(dict.fromkeys(nodes.split(entry.key)[0] for entry in weighty))
    measured = all(e.host_class != plan.UNMEASURED and e.seconds is not None for e in weighty)
    if len(names) < 2 or measured and sum(e.seconds for e in weighty) <= host.SHARED_TICKET_SECONDS:
        return []
    invocations = []
    for name in names:
        kind = [e for e in weighty if nodes.split(e.key)[0] == name]
        classes = "/".join(
            sorted({e.host_class if e.host_class != plan.UNMEASURED else e.expected for e in kind})
        )
        known = all(e.host_class != plan.UNMEASURED and e.seconds is not None for e in kind)
        last = f"{sum(e.seconds for e in kind):.1f} s" if known else "unmeasured"
        invocations.append(f"{build_command(e.key for e in kind)} ({classes}, {last})")
    return [
        f"heavy work of {len(names)} kinds that will run takes one ticket each, in this order: "
        + "; ".join(invocations)
    ]


def build(table: nodes.Table, targets: Iterable[str] = ()) -> Built:
    """Make the targets fresh: each stale node of their closure run in the derived order, a node
    downstream of one that refused or failed, or held by a gate that did not pass, left as it
    stands (`Built.held`); nothing runs where the closure must be scheduled otherwise
    (`refusals`)."""
    closure = plan.wanted(table, list(targets))
    with records.once():
        refused = refusals(table, plan.judge_all(table, closure, False))
    if refused:
        return Built(refused=refused)
    built, stopped = Built(), set()
    for key in (k for k in table.order if k in closure):
        node, _ = table.node(key)
        if table.closure(key) & stopped:
            stopped.add(key)
            built.held.append(key)
            continue
        if node.run is None:
            continue
        entry = state(table, key)
        if entry.state == plan.FRESH:
            continue
        if entry.state != plan.STALE:
            stopped.add(key)
            built.held.append(key)
            continue
        if entry.refused is not None:
            stopped.add(key)
            built.refused.append(standing(key, entry.refused))
            continue
        status, said = run_node(table, key)
        built.ran.append(key)
        if said is not None:
            stopped.add(key)
            unfinished = status >= child_processes.UNFINISHED
            (built.failed if unfinished else built.refused).append(said)
    return built
