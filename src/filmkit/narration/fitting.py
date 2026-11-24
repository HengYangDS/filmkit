"""Count a narration whose thoughts are settled: the runtime its edition gets.

`read` is asked by the convergence (`filmkit.narration.converge`) when its rounds end. It asks
the assembly's own count and nothing else: it selects the edition's recordings as
`produce select` does (`filmkit.narration.selection`) and counts them under the script's pause
policy as `produce fit` does (`filmkit.soundtrack.fit`). What it returns is the record's `fit`:

- `fits`, with the runtime the assembly would give, in whole seconds, and the seconds of the
  rounding's fraction that the gaps and the credits take, as counted: an edition lasts as long
  as its narration, so no count falls short of a runtime and no thought pause is named for one;
- `refused`, where the selection or the assembly refuses the edition, with that reason in one
  line: among them clips that cannot be designed, a file named by an absolute path that is
  missing or cannot be read, a recording that is no WAV, and a decode that fails, whatever its
  cause, with the decoder's own last error line;
- `failed`, where the count ends in a fault that is no refusal of its owners, such as a
  record that lacks a segment, or in an error that names no file by an absolute path, such
  as a decoder that is not installed (`of_the_host`): the fault keeps its traceback, and the
  record is ended first;
- not asked, with the reason: thoughts are unsettled, or the edition declares nothing to
  count: no performance recording with its alignment in the cast, or no pause policy in the
  script. Such an edition is not declared for the assembly yet, and its takes can still be
  judged.

`declared` refuses, before a run's first effect and in one line, a pause policy that the
assembly would refuse. A cast that declares `runtime_fit`, which nothing reads, never reaches
it: the loader refuses the film first (`filmkit.film.WITHDRAWN`).

The reading replaces no take and changes no pause policy and no tracked file. Below `build/` it
writes what those two commands write for the edition: the selection's two records and the
assembly's decode work files. It keeps nothing between runs: a run that is killed while it
counts leaves its record `running`, and the next run selects and counts again.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import wave
from pathlib import Path

import filmkit.repository as repository
import filmkit.soundtrack.fit as soundtrack_fit
from filmkit.narration.selection import select
from filmkit.production import Edition
from filmkit.soundtrack.policy import PausePolicyError, designed_pause_policy

FITS, REFUSED, FAILED = soundtrack_fit.FITS, "refused", "failed"
# What the record's fit states of a counted edition, as the dry run reports them.
COUNTED = ("runtime_seconds", "free_seconds", "credits_free_seconds")
UNSETTLED = "not asked: thoughts are unsettled"
NO_RECORDING = "not asked: the cast declares no performance recording with its alignment"
NO_POLICY = "not asked: the script declares no pause policy (voice_performance)"
# What reading the edition's files or decoding its recordings may fail with, beside the
# refusals that the count names: a file that is missing or cannot be read, a decoder that
# ends with an error or passes its deadline, and a recording that is no WAV or ends early.
# Answered as the edition's refusal, like those, unless the error is the host's
# (`refusal_of`).
UNREADABLE = (OSError, subprocess.SubprocessError, wave.Error, EOFError)
# What the reading answers of the count's owners: their refusals and the errors above.
ANSWERED = (*soundtrack_fit.REFUSALS, *UNREADABLE)


def of_the_host(error: Exception) -> bool:
    """Whether an error is the host's and no refusal of the edition: an `OSError` that names
    no file by an absolute path.

    Running a decoder that is not installed, or that may not be executed, raises for the
    command's bare name; an error may also name no file at all, or a descriptor. One that
    names a file by an absolute path, below the film's root or outside it, is the edition's
    refusal, in the system's words: `repository` opens the root joined with the path it is
    given, which is absolute wherever that path lies.
    """
    if not isinstance(error, OSError):
        return False
    try:
        return not Path(os.fsdecode(error.filename)).is_absolute()
    except TypeError:
        return True


def declared(code: str) -> None:
    """Refuse, before a run's first effect, what the count does not take: a pause policy in the
    script that the assembly refuses, which the judgment reads too."""
    performance = repository.read(Edition(code).script).get("voice_performance")
    try:
        if performance:
            designed_pause_policy(performance)
    except PausePolicyError as error:
        msg = f"{code}: the script's pause policy is refused: {one_line(error)}"
        raise SystemExit(msg) from None


def not_asked(why: str) -> dict:
    return {"asked": False, "why": why}


def asked() -> dict:
    """The head of the fit of an edition that was asked."""
    return {"asked": True}


def failed(fault: Exception) -> dict:
    """The fit of a count that ended in a fault, which its caller raises on."""
    words = f"{type(fault).__name__}: {one_line(fault)}"
    return asked() | {"verdict": FAILED, "fault": words}


def one_line(error: Exception) -> str:
    """A refusal's words in one line, the lines of a refusal that names several joined, and
    the error's kind where it has no words. A command that ended with an error is said with
    the last line it wrote as its error, where it wrote one: FFmpeg's own word of a recording
    that it cannot decode. A character that is not printable is a blank."""
    lines = [line.strip() for line in str(error).splitlines() if line.strip()]
    words = "; ".join(lines) or type(error).__name__
    written = error.stderr if isinstance(error, subprocess.CalledProcessError) else None
    if isinstance(written, bytes):
        written = written.decode(errors="replace")
    last = [line.strip() for line in (written or "").splitlines() if line.strip()][-1:]
    said = f"{words.removesuffix('.')}: {last[0]}" if last else words
    return "".join(character if character.isprintable() else " " for character in said)


def refusal_of(error: Exception) -> str:
    """What the count's owners refuse the edition with (`ANSWERED`), in one line; an error of
    the host is no refusal and is raised on."""
    if of_the_host(error):
        raise error
    return one_line(error)


def read(code: str) -> dict:
    """What the assembly's count says of the edition as its narration stands: the record's fit."""
    edition = Edition(code)
    declared = repository.read(edition.cast).get("performance_recording") or {}
    if not (declared.get("receipt") and declared.get("alignment")):
        return not_asked(NO_RECORDING)
    if not repository.read(edition.script).get("voice_performance"):
        return not_asked(NO_POLICY)
    found = asked()
    try:
        # The selection prints its own line, which is not among the convergence's reports.
        with contextlib.redirect_stdout(io.StringIO()):
            select(edition)
    except ANSWERED as error:
        return found | {"verdict": REFUSED, "refusal": f"the selection: {refusal_of(error)}"}
    try:
        line, refusal = soundtrack_fit.asked(edition)[0]
    except ANSWERED as error:
        return found | {"verdict": REFUSED, "refusal": f"the assembly: {refusal_of(error)}"}
    if refusal is not None:
        return found | {"verdict": REFUSED, "refusal": f"the assembly: {line['verdict']}"}
    return found | {key: line[key] for key in COUNTED} | {"verdict": FITS}


def summary(fit: dict) -> str:
    """The fit in a word for the command's report: its verdict, or why it was not asked."""
    return fit["verdict"] if fit["asked"] else fit["why"]


def said(code: str, fit: dict) -> str | None:
    """The one line that a settled edition is refused with, or None where nothing refuses it."""
    if not fit["asked"] or fit["verdict"] == FITS:
        return None
    if fit["verdict"] == REFUSED:
        return f"{code}: the settled narration is refused by {fit['refusal']}"
    return f"{code}: the count of the settled narration ended in a fault: {fit['fault']}"
