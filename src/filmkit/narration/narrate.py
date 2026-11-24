"""Narrate, align and transcribe one edition through the production CLIs.

Runs the synthesis, alignment and transcription commands of `filmkit.narration` from
the repository root on the edition's ear-first evidence. With --ids only those segments
are narrated, into a receipt, alignment and transcript named after them, such as
narration-receipt-06-07.json, alignment-06-07.json and asr-06-07.json.

Before any speech model loads, and with --dry-run too, the edition must pass the concept
check (`filmkit.concepts`), the register check (`filmkit.register`), its readings check
(`filmkit.narration.readings`) and the check of what every edition's picture reads of its
scripts' anchors (`filmkit.picture.anchor_reads`); a refusal stops the run and names every failure.

Usage: python -m filmkit.narration.narrate
    --language <code> [--ids 06,07] [--dry-run | --skip-generation]
--dry-run prints the narration plan without writing; --skip-generation aligns and
transcribes the existing receipt. Each step runs under this tool's interpreter, and none
outlives a narration that is interrupted, asked to end (SIGTERM) or hung up on. A run that is
not a dry run writes its duration record, each step a phase (`filmkit.durations`). A run that
narrates is recorded as `narrate`, the record an edition's build starts from, and one that only
checks, with --skip-generation, as `narrate-checks`, so that it neither replaces the narration's
record nor moves the build's start; with --ids either name ends with the segments, as the
receipt's does. The record of a run that narrates states how many processes the synthesis may
use (`filmkit.narration.processes`), which `FILMKIT_NARRATION_PROCESSES` names; a value that is
no count is refused before any step.
"""

import argparse
import enum
import json
import sys
import time

import filmkit.child_processes as child_processes
import filmkit.concepts as concepts
import filmkit.durations as durations
import filmkit.register as register
import filmkit.repository as repository
from filmkit.narration import anchors, processes, readings
from filmkit.narration.snapshots import ALIGNER as ALIGNER_SNAPSHOT
from filmkit.picture import anchor_reads
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


def gate(code: str) -> dict:
    """Refuse an edition whose words depart from the concept contract or the formal register, or
    leave a reading open, and a film whose scripts break an anchor's rule or do not mark what its
    picture reads.

    Returns:
        The concept check's, the register check's and the edition's readings check's reports,
        and the scenes the check of what the pictures read could not judge.
    """
    try:
        checked = {
            "concepts": concepts.check(),
            "register": register.check(),
            "readings": readings.check(code),
        }
        checked["picture_reads"] = anchor_reads.check()
    except (
        concepts.ConceptError,
        register.RegisterError,
        readings.ReadingError,
        anchors.AnchorError,
    ) as error:
        message = f"Narration refused before synthesis:\n{error}"
        raise SystemExit(message) from None
    return checked


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
    if scope is not Scope.CHECKS:
        checked = {"edition": options.language, "gate": gate(options.language)}
        print(json.dumps(checked, ensure_ascii=False), flush=True)
    stopped = "The narration was stopped by {request}; its running step was ended with it"
    with child_processes.ending(stopped):
        narrate(options.language, options.ids, scope)


def narrate(code: str, ids: str, scope: Scope) -> None:
    """Run the scope's steps; a run that is not a dry run writes its duration record."""
    if scope is Scope.PLAN:
        run_steps(code, ids, scope)
        return
    try:
        count = processes.count()
    except processes.ProcessesError as error:
        raise SystemExit(str(error)) from None
    with durations.run(code, record_name(scope, ids)) as run:
        if scope is Scope.ALL:
            run.settings["narration_processes"] = count
        run_steps(code, ids, scope)


def record_name(scope: Scope, ids: str = "") -> str:
    """The name of a run's duration record: `narrate` for a run that narrates, `narrate-checks`
    for one that only aligns and transcribes, and after either the segments --ids names."""
    name = "narrate-checks" if scope is Scope.CHECKS else durations.BUILD_START
    return name + (f"-{ids.replace(',', '-')}" if ids else "")


def run_steps(code: str, ids: str, scope: Scope) -> None:
    """Run the scope's steps in order, each a phase of the current run, and print its seconds.
    A step that fails raises; a narration that is interrupted or asked to end ends its running
    step first (`filmkit.child_processes.run`), and the synthesis in turn its own children."""
    for name, command in steps(code, ids, scope):
        started = time.monotonic()
        with durations.phase(name):
            child_processes.run(command, cwd=repository.ROOT)
        seconds = round(time.monotonic() - started, 1)
        print(json.dumps({"edition": code, "step": name, "seconds": seconds}), flush=True)


if __name__ == "__main__":
    main()
