"""Narrate, align and transcribe one edition through the production CLIs.

Runs the synthesis, alignment and transcription commands of `filmkit.narration` from
the repository root on the edition's ear-first evidence. With --ids only those segments
are narrated, into a receipt, alignment and transcript named after them, such as
narration-receipt-06-07.json, alignment-06-07.json and asr-06-07.json.

The film's sources are checked by the film-wide node `check` (`filmkit.check`), not here.

Usage: python -m filmkit.narration.narrate
    --language <code> [--ids 06,07] [--dry-run | --skip-generation]
--dry-run prints the narration plan without writing; --skip-generation aligns and
transcribes the existing receipt. Each step runs under this tool's interpreter, and none
outlives a narration that is interrupted, asked to end (SIGTERM) or hung up on. A run that is
not a dry run is a run of the node `narrate`, each step a phase (`filmkit.graph.runs`): one that
narrates the whole edition writes the node's run record, and one of chosen segments (--ids) or
of its checks alone (--skip-generation) a partial record, which never makes the node fresh. The
record of a run that narrates states how many processes the synthesis may use
(`filmkit.narration.processes`), which `FILMKIT_NARRATION_PROCESSES` names; a value that is no
count is refused before any step.
"""

import argparse
import enum
import json
import sys
import time

import filmkit.child_processes as child_processes
import filmkit.graph.runs as seam
import filmkit.repository as repository
from filmkit.narration import processes
from filmkit.narration.snapshots import ALIGNER as ALIGNER_SNAPSHOT
from filmkit.production import CODES, Edition

ALIGNER = ALIGNER_SNAPSHOT.folder


class Scope(enum.Enum):
    """The steps a run takes: every step, the narration plan alone, or the checks alone."""

    ALL = "all"
    PLAN = "plan"
    CHECKS = "checks"


def evidence_paths(code: str, ids: str = "") -> dict[str, str]:
    """The edition's recordings folder and its receipt, alignment and transcript."""
    base = Edition(code).ear_first.relative_to(repository.ROOT).as_posix()
    suffix = f"-{ids.replace(',', '-')}" if ids else ""
    return {
        "folder": f"{base}/recordings",
        "receipt": f"{base}/narration-receipt{suffix}.json",
        "alignment": f"{base}/alignment{suffix}.json",
        "asr": f"{base}/asr{suffix}.json",
    }


def steps(code: str, ids: str = "", scope: Scope = Scope.ALL) -> list[tuple[str, list[str]]]:
    """The edition's named commands in order, each run from the repository root."""
    edition, paths = Edition(code), evidence_paths(code, ids)
    python = [sys.executable, "-B"]
    narration = [
        *python,
        "-m",
        "filmkit.narration.synthesis",
        "--language",
        code,
        "--script",
        edition.script,
        "--cast",
        edition.cast,
        "--folder",
        paths["folder"],
        "--receipt",
        paths["receipt"],
    ]
    if ids:
        narration += ["--ids", ids]
    if scope is Scope.PLAN:
        return [("narration", [*narration, "--dry-run"])]
    receipt, language = paths["receipt"], edition.language
    checks = [
        (
            "alignment",
            [
                *python,
                "-m",
                "filmkit.narration.alignment",
                "--model",
                ALIGNER,
                "--receipt",
                receipt,
                "--output",
                paths["alignment"],
                "--language",
                language,
            ],
        ),
        (
            "transcription",
            [
                *python,
                "-m",
                "filmkit.narration.transcription",
                "--receipt",
                receipt,
                "--output",
                paths["asr"],
                "--language",
                language,
            ],
        ),
    ]
    return checks if scope is Scope.CHECKS else [("narration", narration), *checks]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Narrate, align and transcribe one edition.")
    parser.add_argument("--language", choices=CODES, required=True)
    parser.add_argument("--ids", default="", help="Comma-separated segment ids")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print the narration plan only")
    mode.add_argument(
        "--skip-generation",
        action="store_true",
        help="Align and transcribe the existing receipt",
    )
    options = parser.parse_args(argv)
    scope = Scope.ALL
    if options.dry_run:
        scope = Scope.PLAN
    elif options.skip_generation:
        scope = Scope.CHECKS
    stopped = "The narration was stopped by {request}; its running step was ended with it"
    with child_processes.ending(stopped):
        narrate(options.language, options.ids, scope)


def narrate(code: str, ids: str, scope: Scope) -> None:
    """Run the scope's steps; a run that is not a dry run writes the node's run record or its
    partial record."""
    if scope is Scope.PLAN:
        run_steps(code, ids, scope)
        return
    try:
        count = processes.count()
    except processes.ProcessesError as error:
        raise SystemExit(str(error)) from None
    # A narration of chosen segments or of its checks alone is a run of part of the node.
    whole = scope is Scope.ALL and not ids
    with seam.run(code, "narrate", whole=whole) as run:
        if scope is Scope.ALL:
            run.settings["narration_processes"] = count
        run_steps(code, ids, scope)


def run_steps(code: str, ids: str, scope: Scope) -> None:
    """Run the scope's steps in order, each a phase of the current run, and print its seconds.
    A step that fails raises; a narration that is interrupted or asked to end ends its running
    step first (`filmkit.child_processes.run`), and the synthesis in turn its own children."""
    for name, command in steps(code, ids, scope):
        started = time.monotonic()
        with seam.phase(name):
            child_processes.run(command, cwd=repository.ROOT)
        seconds = round(time.monotonic() - started, 1)
        print(json.dumps({"edition": code, "step": name, "seconds": seconds}), flush=True)


if __name__ == "__main__":
    main()
