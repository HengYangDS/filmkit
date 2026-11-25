"""`filmkit verify`: every input and output of every standing record hashed, partial records
included, and the build refused unless every node of the table is fresh and passed and every
byte is accounted for (design decision 6 of record-every-run, 11 of build-a-film-by-its-verbs).

It refuses, each named in one line: bytes that no record of a declared writer accounts for,
which a writer the table does not know left, and a file whose size and time held while its
digest changed, which the plan's comparison by size and time cannot see, each with every node
whose record binds it; the nodes of the table without a record, together; and each other node
that is not fresh, stale with its reasons (a run that did not pass among them), behind, or
waiting with the gates that hold it. It writes nothing.

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
    """What `verify` found: its refusals, each in one line, and how many files it hashed."""

    refusals: tuple[str, ...]
    hashed: int


def unfinished(entry: plan.Entry) -> str:
    """A node that is not fresh, in one line: its state and why."""
    if entry.state == plan.WAITING:
        held = ", ".join(f"{gate} ({state})" for gate, state in entry.held.items())
        return f"{entry.key}: waiting for {held}"
    why = "; ".join(reason.text for reason in entry.reasons)
    return f"{entry.key}: {entry.state}" + (f": {why}" if why else "")


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
    if unrecorded:
        refusals.append(f"no record: {', '.join(unrecorded)}")
    refusals += [
        unfinished(e) for e in planned.entries if e.state != plan.FRESH and e.key not in unrecorded
    ]
    return Verified(tuple(refusals), planned.hashed)


def check(table: nodes.Table | None = None) -> Verified:
    """Verify, refusing with its lines where it refuses."""
    verified = verify(table)
    if verified.refusals:
        raise VerifyError("filmkit verify refuses: " + "; ".join(verified.refusals))
    return verified


def run(table: nodes.Table | None = None) -> int:
    """Print what `verify` found and return the command's exit status: 1 where it refuses."""
    verified = verify(table)
    for line in verified.refusals:
        print(f"refused: {line}")
    files = f"{verified.hashed} files hashed"
    if verified.refusals:
        print(f"filmkit verify refuses the build ({len(verified.refusals)} refusals); {files}")
        return 1
    print(
        f"filmkit verify passes: every node is fresh and passed, every byte accounted for; {files}"
    )
    return 0
