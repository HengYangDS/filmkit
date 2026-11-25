"""The `filmkit` console command, with two verbs (design decision 10 of record-every-run).

Usage: filmkit plan [TARGET...] [--json]
       filmkit verify

Run in a film's folder, where the engine finds the film. `plan` prints, for the nodes a target
names (`<node>:<code>` or `<node>:all`, every node where none is named) and every node upstream of
them, each node's state and reasons, its host class as measured and as expected, its last seconds
and whether it is ready (`filmkit.graph.plan`); it writes nothing. `verify` hashes every file a run
record states and exits 1 where it refuses (`filmkit.graph.verify`). A target that names no node
is refused in one line that names the nodes.
"""

from __future__ import annotations

import argparse
import json
import sys

from filmkit.graph import plan, verify


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filmkit", description="Plan and verify a film's build from its run records."
    )
    verbs = parser.add_subparsers(dest="verb", required=True, metavar="{plan,verify}")
    planning = verbs.add_parser(
        "plan",
        help="each node's state, reasons, class, last seconds and readiness; writes nothing",
    )
    planning.add_argument(
        "targets",
        nargs="*",
        metavar="TARGET",
        help="<node>:<code> or <node>:all, with every node upstream; every node where none",
    )
    planning.add_argument("--json", action="store_true", help="print the plan as JSON")
    verbs.add_parser(
        "verify",
        help="hash every file a run record states; exit 1 for bytes no declared writer "
        "accounts for and for a change that kept a file's size and time",
    )
    return parser


def line(entry: plan.Entry) -> str:
    """One node of the plan in words."""
    seconds = "no seconds" if entry.seconds is None else f"{entry.seconds:.1f} s"
    ready = "ready" if entry.ready else "not ready"
    measured = f"{entry.host_class} (expected {entry.expected})"
    text = f"{entry.key}: {entry.state}, {ready}, {measured}, {seconds}"
    return "\n".join([text, *(f"  {reason.text}" for reason in entry.reasons)])


def timed(entries: list[plan.Entry]) -> str:
    """The seconds of the listed nodes' last runs, summed, and their span from the first start to
    the last end; nothing where no listed node has a record."""
    spans = [entry.span for entry in entries if entry.span is not None]
    if not spans:
        return ""
    summed = sum(entry.seconds or 0.0 for entry in entries if entry.span is not None)
    first, last = min(start for start, _ in spans), max(end for _, end in spans)
    spanned = (last - first).total_seconds()
    return (
        f"{len(spans)} last runs: {summed:.1f} s summed, spanning {spanned:.1f} s "
        f"from {first.isoformat(timespec='seconds')} to {last.isoformat(timespec='seconds')}"
    )


def main(argv: list[str] | None = None) -> None:
    options = arguments().parse_args(argv)
    if options.verb == "verify":
        sys.exit(verify.run())
    try:
        planned = plan.plan(targets=options.targets)
    except ValueError as error:
        sys.exit(f"filmkit plan: {error}")
    if options.json:
        stated = [entry.stated() for entry in planned.entries]
        print(json.dumps({"nodes": stated, "hashed": planned.hashed}, indent=2))
        return
    for entry in planned.entries:
        print(line(entry))
    print("\n".join(filter(None, [timed(planned.entries), f"{planned.hashed} files hashed"])))


if __name__ == "__main__":
    main()
