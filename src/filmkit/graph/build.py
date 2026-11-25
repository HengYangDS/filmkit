"""`filmkit build`: the targets made fresh from the run records, one node at a time (design
decision 3 of build-a-film-by-its-verbs).

A build takes the targets' closure, the nodes they name and every node upstream of them by a
path or by a wait (`plan.wanted`), and visits it in the order the table derives over both. At
each node's turn it judges the node again against the files as they stand (`plan.plan`), so
that a node behind only because a node upstream was stale is fresh again once that node has run
without changing its outputs, and a node held by a gate that ran again and passed is fresh by
its own inputs: neither is run. It runs a node, its owner's call (`Node.run`) in this process
inside the seam (`runs.run`), which writes the node's run record, only where the node is stale.
A node behind a refused or failed node, or waiting on a gate that did not pass, is not run;
nodes not downstream of it go on. A node with no run, the narration, is never run here.

The build ends with one line for each node that refused or failed and returns 1, and 0 where
every node of the closure is fresh. An interrupt or a request to end ends the running node as
any command ends (`child_processes.ending`) and runs no further node. It writes no tracked file
and takes no host ticket.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import filmkit.tools as tools
from filmkit.captions import CaptionError
from filmkit.delivery.packaging import PackagingError
from filmkit.graph import nodes, plan, runs
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
    pass, and each refusal or failure in one line."""

    ran: list[str] = field(default_factory=list)
    held: list[str] = field(default_factory=list)
    refused: list[str] = field(default_factory=list)

    @property
    def status(self) -> int:
        return 1 if self.refused or self.held else 0


def state(table: nodes.Table, key: str) -> plan.Entry:
    """A node as the plan judges it now, against the files as they stand."""
    (entry,) = [entry for entry in plan.plan(table, [key]).entries if entry.key == key]
    return entry


def run_node(table: nodes.Table, key: str) -> str | None:
    """Run one node's owner inside the seam; its refusal or failure in one line, or None."""
    node, edition = table.node(key)
    code = edition.code if edition else None
    try:
        with runs.run(code, node.name):
            try:
                node.run(edition)
            except REFUSALS as error:
                raise SystemExit(f"{key}: {error}") from None
    except SystemExit as ended:
        code = ended.code
        return code if isinstance(code, str) else f"{key}: exit status {code}"
    except Exception as error:
        return f"{key}: {type(error).__name__}: {error}".rstrip(": ")
    return None


def build(table: nodes.Table, targets: Iterable[str] = ()) -> Built:
    """Make the targets fresh: each stale node of their closure run in the derived order, a node
    downstream of one that refused or failed, or held by a gate that did not pass, left as it
    stands (`Built.held`)."""
    closure = plan.wanted(table, list(targets))
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
        refused = run_node(table, key)
        built.ran.append(key)
        if refused is not None:
            stopped.add(key)
            built.refused.append(refused)
    return built
