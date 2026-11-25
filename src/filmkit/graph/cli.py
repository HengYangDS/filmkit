"""The `filmkit` console command: a film's build by its verbs (design decision 10 of
record-every-run, 17 of build-a-film-by-its-verbs).

Usage: filmkit supply
       filmkit check [--read-only]
       filmkit edit --edits FILE [--dry-run]
       filmkit narrate [--edition CODE|all] [--rounds N] [--takes N]
       filmkit plan [TARGET...] [--json]
       filmkit build [TARGET...]
       filmkit verify [--technical-only] [--release]
       filmkit review prepare|record|set-aside ...
       filmkit deliver [--to DIR] [--dry-run]
       filmkit release [--replace] [--dry-run]

Run in a film's folder, where the engine finds the film. Each verb calls the owner of what it
does:

- `supply` installs the browser build, the dictionary and the speech models the engine pins,
  the one step that reaches the network (`filmkit.supply`).
- `check` asks every question of the film's sources at once (`filmkit.check`) as the run of the
  film-wide node `check`, which writes its record, its verdict and each edition's occurrence
  plan; with `--read-only` it prints each finding and writes no file. Either exits 1 where a
  question found anything.
- `edit` applies an edits file's exact edits to the scripts and casts, or with `--dry-run`
  reports them (`filmkit.narration.script_edits`).
- `narrate` converges each edition asked, every one by default
  (`filmkit.narration.converge`): the GPU work that no build runs. It is refused, before any
  model loads, while the plan calls an edition's narration not ready, as while the source check
  is stale or refused; the convergence's record states its seconds and phases.
- `plan` prints, for the nodes a target names (`<node>:<code>`, `<node>:all`, a group, or `all`;
  every node where none is named) and every node upstream of them, each node's state and
  reasons, its host class as measured and as expected, its last seconds and whether it is ready
  (`filmkit.graph.plan`); it writes nothing.
- `build` makes the targets fresh, `all` where none is named (`filmkit.graph.build`): it prints
  each node it ran and those it held, and each refusal on standard error.
- `verify` hashes every file a run record states and exits 1 where it refuses
  (`filmkit.graph.verify`); only once the records pass, `--technical-only` runs the verifier's
  technical checks of each edition's delivered films, which decode them
  (`filmkit.delivery.verification`), and `--release` compares the build with the published
  release (`filmkit.delivery.reproduction`). It writes nothing in any mode.
- `review` prepares, records or sets aside a review round (`filmkit.review.round`).
- `deliver` asks the records, then each edition's films and recorded review, before it fills the
  film's delivery folder or the one `--to` names, or with `--dry-run` plans the copy
  (`filmkit.delivery.folder`).
- `release` records the release of the reviewed, delivered build and stages its assets, its
  sources from the declaration (`filmkit.delivery.release`).

A refusal is one line on standard error, and the command exits 1, a declaration that the loader
refuses among them (`declaration_refused`). A command that cannot finish exits 2: a tool the
host lacks is named in one line, any other exception printed with its traceback; an interrupted
one exits with the status that names its request (design decision 19). A target that names no
node is refused in one line that names the nodes.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import TYPE_CHECKING

import filmkit.child_processes as child_processes

if TYPE_CHECKING:
    from filmkit.graph import plan


# The review's commands, whose options `filmkit.review.round` states.
REVIEW_COMMANDS = ("prepare", "record", "set-aside")


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filmkit", description="Build a film from its sources, verb by verb."
    )
    verbs = parser.add_subparsers(dest="verb", required=True, metavar="VERB")
    verbs.add_parser(
        "supply",
        help="install the browser build, the dictionary and the models the engine pins",
    )
    checking = verbs.add_parser(
        "check", help="ask every question of the film's sources at once; exit 1 on a finding"
    )
    checking.add_argument(
        "--read-only", action="store_true", help="print the findings and write no file"
    )
    editing = verbs.add_parser("edit", help="apply exact edits to the scripts and casts")
    editing.add_argument("--edits", required=True, metavar="FILE", help="the edits file, JSON")
    editing.add_argument("--dry-run", action="store_true", help="report the edits, write nothing")
    narrating = verbs.add_parser(
        "narrate", help="narrate each edition asked until its takes are accepted"
    )
    narrating.add_argument(
        "--edition", default="all", metavar="CODE|all", help="the edition, or every one (all)"
    )
    narrating.add_argument("--rounds", type=int, default=2, help="rounds of candidates")
    narrating.add_argument(
        "--takes", type=int, default=3, help="candidates for a refused thought in a round"
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
    building = verbs.add_parser("build", help="make the targets fresh from the run records")
    building.add_argument(
        "targets", nargs="*", metavar="TARGET", help="as plan takes them; all where none"
    )
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
    reviewing = verbs.add_parser("review", help="prepare, record or set aside a review round")
    reviewing.add_argument("command", choices=REVIEW_COMMANDS)
    reviewing.add_argument(
        "options", nargs=argparse.REMAINDER, help="the command's options; --help lists them"
    )
    delivering = verbs.add_parser(
        "deliver", help="fill the film's delivery folder once the build verifies"
    )
    delivering.add_argument("--to", metavar="DIR", help="another folder to fill")
    delivering.add_argument("--dry-run", action="store_true", help="plan the copy only")
    releasing = verbs.add_parser(
        "release", help="record the release of the delivered build and stage its assets"
    )
    releasing.add_argument(
        "--replace", action="store_true", help="replace a release folder that holds other bytes"
    )
    releasing.add_argument("--dry-run", action="store_true", help="print the record only")
    return parser


def line(entry: plan.Entry) -> str:
    """One node of the plan in words."""
    seconds = "no seconds" if entry.seconds is None else f"{entry.seconds:.1f} s"
    ready = "ready" if entry.ready else "not ready"
    measured = f"{entry.host_class} (expected {entry.expected})"
    text = f"{entry.key}: {entry.state}, {ready}, {measured}, {seconds}"
    stands = [f"  its refusal stands, so no build runs it: {entry.standing}"] * bool(entry.standing)
    return "\n".join([text, *(f"  {reason.text}" for reason in entry.reasons), *stands])


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
    declaration is read before the node table loads: where the loader finds a problem in it, the
    check refuses as the read-only mode does and writes nothing, since no node table loads."""
    import filmkit.check as source_check
    import filmkit.repository as repository

    if read_only or source_check.loaded(repository.ROOT):
        verdict = source_check.asked(repository.ROOT, write=False)
        for name, texts in verdict["findings"].items():
            print("\n".join(f"{name}: {text}" for text in texts), end="\n" if texts else "")
        count = sum(map(len, verdict["findings"].values()))
        if count:
            refused = f"filmkit check refuses the sources: {count} finding{'s' * (count != 1)}"
            print(refused, file=sys.stderr)
            return 1
    else:
        from filmkit.graph import runs

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


def supplied() -> int:
    """`filmkit supply`: what was supplied, or the refusal of what differs from its pin."""
    import filmkit.supply as supply

    try:
        report = supply.supply()
    except supply.SupplyError as error:
        sys.exit(str(error))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def edited(edits: str, dry_run: bool) -> int:
    """`filmkit edit`: the edits applied, or reported, or the refusal of one that does not
    apply."""
    import filmkit.repository as repository
    from filmkit.narration import script_edits

    try:
        report = script_edits.apply_edits(repository.read(edits), dry_run=dry_run)
    except (OSError, ValueError) as error:
        sys.exit(f"filmkit edit: {error}")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


def editions(asked: str) -> tuple[str, ...]:
    """The editions a verb is asked for: one the film declares, or every one for `all`."""
    from filmkit.production import CODES

    if asked == "all":
        return CODES
    if asked not in CODES:
        sys.exit(f"The film declares no edition {asked}: it declares {', '.join(CODES)}, or all")
    return (asked,)


def narrated(asked: str, rounds: int, takes: int) -> int:
    """`filmkit narrate`: refused, before any model loads, while the plan calls an edition's
    narration not ready; else each edition asked converged in turn, as one run each, narrated
    once where the plan calls its node stale, and every edition's refusal, in lines, once all
    have run."""
    if rounds < 0 or takes < 1:
        sys.exit("filmkit narrate: --rounds is 0 or more and --takes is 1 or more")
    from filmkit.narration import narrate

    codes = editions(asked)
    judged = {code: narrate.judged(code) for code in codes}
    refusals = [line for line, _ in judged.values() if line]
    if refusals:
        sys.exit("\n".join(refusals))
    from filmkit.narration import converge

    with child_processes.ending(converge.STOPPED):
        refused = [
            converge.converged(code, rounds=rounds, takes=takes, stale=judged[code][1])
            for code in codes
        ]
    if any(refused):
        sys.exit("\n".join(filter(None, refused)))
    return 0


def built(targets: list[str]) -> int:
    """`filmkit build`: each node it ran and held, each refusal and failure on standard error,
    and the build's status (`build.Built.status`)."""
    from filmkit.graph import build, chain

    stopped = "The build was stopped by {request}; the node it was running was ended with it"
    with child_processes.ending(stopped):
        try:
            done = build.build(chain.table(), targets or ["all"])
        except ValueError as error:
            sys.exit(f"filmkit build: {error}")
    for key in done.ran:
        print(f"ran {key}")
    if done.held:
        print(f"held, behind a node that did not pass: {' '.join(done.held)}")
    for said in (*done.refused, *done.failed):
        print(said, file=sys.stderr)
    return done.status


def delivered(to: str | None, dry_run: bool) -> int:
    """`filmkit deliver`: the records, then each edition's films and recorded review, asked
    before anything is copied or planned; then the delivery, or its plan."""
    import filmkit.delivery.folder as delivery_folder
    import filmkit.delivery.verification as delivery_verification
    import filmkit.repository as repository
    from filmkit.graph import verify
    from filmkit.production import UnassembledError

    try:
        verify.check()
    except verify.VerifyError as error:
        sys.exit(str(error))
    for _ in delivery_verification.qualified(technical_only=False):
        pass
    try:
        folder, rule = delivery_folder.delivery_destination(to)
        report = delivery_folder.deliver(repository.ROOT, folder, dry_run=dry_run, rule=rule)
    except (delivery_folder.DeliveryRefusedError, UnassembledError) as error:
        sys.exit(str(error))
    if dry_run:
        print(json.dumps(report, ensure_ascii=False))
        return 0
    summary = {key: report[key] for key in ("destination", "destination_rule")}
    summary |= {key: report[key] for key in ("all_match", "predecessors")}
    print(json.dumps({"members": len(report["members"]), **summary}, ensure_ascii=False))
    return 0


def released(replace: bool, dry_run: bool) -> int:
    """`filmkit release`: the record written and its assets staged, or the first refusal."""
    import filmkit.delivery.release as release
    from filmkit.delivery.reproduction import ReproductionError

    try:
        release.write(replace=replace, dry_run=dry_run)
    except ReproductionError as error:
        sys.exit(str(error))
    return 0


def main(argv: list[str] | None = None) -> None:
    """Run the verb asked and exit with the status that says how it ended
    (`child_processes.FINISHED`, `REFUSED`, `UNFINISHED`)."""
    options = arguments().parse_args(argv)
    try:
        status = ran(options)
    except Exception as error:
        refused = declaration_refused(error)
        if refused is not None:
            print(refused, file=sys.stderr)
            sys.exit(child_processes.REFUSED)
        tool = child_processes.missing(error)
        if tool is not None:
            print(tool, file=sys.stderr)
        else:
            traceback.print_exc(file=sys.stderr)
        sys.exit(child_processes.UNFINISHED)
    if status:
        sys.exit(status)


def declaration_refused(error: Exception) -> str | None:
    """The loader's refusal of the film's declaration (`filmkit.film.FilmError`), its problems
    in one line; None for any other error. The loader's module stands loaded once it raised one,
    and is not imported here, since loading it outside a film is itself refused."""
    loader = sys.modules.get("filmkit.film")
    if loader is None or not isinstance(error, loader.FilmError):
        return None
    return "; ".join(line for line in str(error).splitlines() if line)


def ran(options: argparse.Namespace) -> int:
    """Run the verb the options name: its status, where it returns one."""
    verb = options.verb
    if verb == "review":
        from filmkit.review import round as review_round

        review_round.run([options.command, *options.options], prog="filmkit review")
        return child_processes.FINISHED
    done = {
        "supply": supplied,
        "check": lambda: checked(options.read_only),
        "edit": lambda: edited(options.edits, options.dry_run),
        "narrate": lambda: narrated(options.edition, options.rounds, options.takes),
        "build": lambda: built(options.targets),
        "verify": lambda: verified(options.technical_only, options.release),
        "deliver": lambda: delivered(options.to, options.dry_run),
        "release": lambda: released(options.replace, options.dry_run),
    }.get(verb)
    if done is not None:
        return done()
    from filmkit.graph import plan

    try:
        planned = plan.plan(targets=options.targets)
    except ValueError as error:
        sys.exit(f"filmkit plan: {error}")
    if options.json:
        stated = [entry.stated() for entry in planned.entries]
        print(json.dumps({"nodes": stated, "hashed": planned.hashed}, indent=2))
        return child_processes.FINISHED
    for entry in planned.entries:
        print(line(entry))
    print("\n".join(filter(None, [timed(planned.entries), f"{planned.hashed} files hashed"])))
    return child_processes.FINISHED


if __name__ == "__main__":
    from filmkit.retired import refuse

    refuse(__spec__.name)
