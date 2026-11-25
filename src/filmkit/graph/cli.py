"""The `filmkit` console command (design decision 10 of record-every-run, 17 of
build-a-film-by-its-verbs).

Usage: filmkit check [--read-only]
       filmkit plan [TARGET...] [--json]
       filmkit verify [--technical-only] [--release]

Run in a film's folder, where the engine finds the film. `check` asks every question of the
film's sources at once (`filmkit.check`) as the run of the film-wide node `check`, which writes
its record, its verdict and each edition's occurrence plan; with `--read-only` it prints each
finding and writes no file. Either exits 1 where a question found anything. `plan` prints, for
the nodes a target
names (`<node>:<code>` or `<node>:all`, every node where none is named) and every node upstream of
them, each node's state and reasons, its host class as measured and as expected, its last seconds
and whether it is ready (`filmkit.graph.plan`); it writes nothing. `verify` hashes every file a run
record states and exits 1 where it refuses (`filmkit.graph.verify`); only once the records pass,
`--technical-only` runs the verifier's technical checks of each edition's delivered films, which
decode them (`filmkit.delivery.verification`), and `--release` compares the build with the
published release (`filmkit.delivery.reproduction`). `verify` writes nothing in any mode. A target
that names no node is refused in one line that names the nodes.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from filmkit.graph import plan


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filmkit", description="Plan and verify a film's build from its run records."
    )
    verbs = parser.add_subparsers(dest="verb", required=True, metavar="{check,plan,verify}")
    checking = verbs.add_parser(
        "check", help="ask every question of the film's sources at once; exit 1 on a finding"
    )
    checking.add_argument(
        "--read-only", action="store_true", help="print the findings and write no file"
    )
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
    verifying = verbs.add_parser(
        "verify",
        help="hash every file a run record states and judge every node; exit 1 for a node that "
        "is not fresh and passed and for bytes no declared writer accounts for; writes nothing",
    )
    verifying.add_argument(
        "--technical-only",
        action="store_true",
        help="then decode and check each edition's delivered films, the review aside",
    )
    verifying.add_argument(
        "--release",
        action="store_true",
        help="then compare the build with the published release under the reproduction standard",
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


def checked(read_only: bool) -> int:
    """`filmkit check`: the node's run, which records it, or with `read_only` the findings
    printed and no file written; the exit status, 1 where a question found anything. The
    declaration is read before the node table loads, so that its problems are findings."""
    import filmkit.check as source_check
    import filmkit.repository as repository

    if read_only:
        verdict = source_check.asked(repository.ROOT, write=False)
        for name, texts in verdict["findings"].items():
            print("\n".join(f"{name}: {text}" for text in texts), end="\n" if texts else "")
        count = sum(map(len, verdict["findings"].values()))
        if count:
            print(f"filmkit check refuses the sources: {count} finding{'s' * (count != 1)}")
            return 1
    else:
        from filmkit.graph import runs

        source_check.loaded(repository.ROOT)
        with runs.run(None, "check"):
            source_check.run()
    print("filmkit check passes: no question of the film's sources found anything")
    return 0


def verified(technical: bool, release: bool) -> int:
    """`filmkit verify`: the records, and once they pass, with `technical` the verifier's
    technical checks of each edition's delivered films and with `release` the comparison with the
    published release, each refusing in its own words; a refusal of the records stops before any
    film is decoded, and nothing is written."""
    from filmkit.graph import verify

    status = verify.run()
    if status == 0 and technical:
        import filmkit.delivery.verification as delivery_verification

        delivery_verification.verify_editions(technical_only=True)
    if status == 0 and release:
        import filmkit.delivery.reproduction as reproduction

        reproduction.judge(reproduction.compared())
    return status


def main(argv: list[str] | None = None) -> None:
    options = arguments().parse_args(argv)
    if options.verb == "check":
        sys.exit(checked(options.read_only))
    if options.verb == "verify":
        sys.exit(verified(options.technical_only, options.release))
    from filmkit.graph import plan

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
