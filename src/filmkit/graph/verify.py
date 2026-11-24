"""`filmkit verify`: every input and output of every standing record hashed, partial records
included, and a refusal only where the plan's shortcut cannot be trusted (design decision 6 of
record-every-run).

It refuses for two things only, each named with its path and every node whose record binds it:
bytes that no record of a declared writer accounts for, which a writer the table does not know
left, and a file whose size and time held while its digest changed, which the plan's comparison
by size and time cannot see. Every other node that is stale or behind is listed and refuses
nothing: no command refuses on staleness in this release, and each owner keeps refusing what it
refuses. Nodes without a record are listed together, so that a build made before this release
verifies as it did. It writes nothing.

A review round's preparation and a release's record run `check` before they write anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from filmkit.graph import nodes, plan

# What a refusal says of a path, by the kind of reason it refuses.
SAYS = {
    "unaccounted": "its bytes are accounted for by no record of a declared writer",
    "blind": "it changed while keeping its size and time",
}


class VerifyError(ValueError):
    """Bytes that no record accounts for, or a change that kept a file's size and time."""


@dataclass(frozen=True)
class Verified:
    """What `verify` found: its refusals, the nodes it lists, and how many files it hashed."""

    refusals: tuple[str, ...]
    listed: tuple[str, ...]
    hashed: int


def verify(table: nodes.Table | None = None) -> Verified:
    """Hash every file every standing record states, and judge the build by decision 6."""
    planned = plan.plan(table, full=True)
    refused = dict.fromkeys(
        (reason.kind, reason.path)
        for entry in planned.entries
        for reason in entry.reasons
        if reason.kind in plan.REFUSED and reason.path
    )
    refusals = []
    for kind, path in refused:
        binders = {e.key for e in planned.entries for r in e.reasons if r.path == path}
        refusals.append(f"{path}: {SAYS[kind]}; it is bound by {', '.join(sorted(binders))}")
    unrecorded = [e.key for e in planned.entries if [r.text for r in e.reasons] == ["no record"]]
    listed = [
        f"{e.key}: {e.state}" + (": " + "; ".join(r.text for r in e.reasons) if e.reasons else "")
        for e in planned.entries
        if e.state != plan.FRESH and e.key not in unrecorded
    ]
    if unrecorded:
        listed.append(f"no record: {', '.join(unrecorded)}")
    return Verified(tuple(refusals), tuple(listed), planned.hashed)


def check(table: nodes.Table | None = None) -> Verified:
    """Verify, refusing with its lines where it refuses."""
    verified = verify(table)
    if verified.refusals:
        raise VerifyError("filmkit verify refuses: " + "; ".join(verified.refusals))
    return verified


def run(table: nodes.Table | None = None) -> int:
    """Print what `verify` found and return the command's exit status: 1 where it refuses."""
    verified = verify(table)
    for line in verified.listed:
        print(line)
    for line in verified.refusals:
        print(f"refused: {line}")
    files = f"{verified.hashed} files hashed"
    if verified.refusals:
        print(f"filmkit verify refuses {len(verified.refusals)} files; {files}")
        return 1
    print(f"filmkit verify passes: every file a record states is accounted for; {files}")
    return 0
