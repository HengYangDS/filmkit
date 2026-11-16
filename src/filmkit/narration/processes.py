"""Narrate an edition's segments in several processes of the speech model at once.

A segment's takes depend on its own request alone: every thought is generated from its own text,
seed and settings, and written to files named by its own fingerprint. So the segments that a
narration has to generate can be divided among processes without changing a byte. The synthesis
(`filmkit.narration.synthesis`) plans as it always has; when more than one segment is to be
generated and the count is over one, `narrate` here divides those segments among the processes,
the longest spoken text first to the least loaded, and starts for each one child of the synthesis
itself, `--ids <its segments>`, which writes a receipt of its own in a work folder that no other
step reads. When all have ended, the synthesis takes its ordinary path, in which it finds every
segment retained, loads no model and writes the one receipt in segment order.

The count is `DEFAULT` unless `VARIABLE` names another; 1 keeps the single process. A child is
given the count 1, so it never divides again. A child that fails does not stop the others; once
all have ended the narration is refused, naming each failed child, its segments, its exit status,
its log and the last line it wrote, which holds the refusal an unresolved take raises. What a
failed child left behind is then judged by the next run as an interrupted run's always was.

Measured on four segments of a film on 17 November 2026: one process 99.8 s, two 55.3 s, four
55.2 s, since the longest segment bounds the run; all takes equal, byte for byte, to the takes of
their fingerprints that the film delivered.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import filmkit.repository as repository

# The variable that names how many processes narrate an edition, and the count without it.
VARIABLE = "FILMKIT_NARRATION_PROCESSES"
DEFAULT = 2
# The children's receipts and logs, below the film's root, in a folder for each receipt.
WORK = Path("build/runtime/work/narration-processes")


class ProcessesError(ValueError):
    """The count of narration processes is no count, or a narration process failed."""


def count() -> int:
    """How many processes narrate: what `VARIABLE` names, a positive whole number, or `DEFAULT`."""
    named = os.environ.get(VARIABLE)
    if not named:
        return DEFAULT
    if not (named.isascii() and named.isdigit() and int(named) > 0):
        msg = f"{VARIABLE} names {named!r}, which is no positive whole number of processes"
        raise ProcessesError(msg)
    return int(named)


def divide(segments: list[tuple[str, int]], processes: int) -> list[list[str]]:
    """Divide segments, each an id and the length of its spoken text, among at most `processes`
    shares of about equal length: the longest first, each to the share that holds the least, an
    earlier share on a tie. Each share keeps the segments' own order, and no share is empty."""
    shares: list[list[int]] = [[] for _ in range(min(processes, len(segments)))]
    loads = [0] * len(shares)
    longest_first = sorted(range(len(segments)), key=lambda index: (-segments[index][1], index))
    for index in longest_first:
        least = loads.index(min(loads))
        shares[least].append(index)
        loads[least] += segments[index][1]
    return [[segments[index][0] for index in sorted(share)] for share in shares]


def work_folder(receipt: Path) -> Path:
    """The folder of the children that narrate for a receipt, named after the receipt's place."""
    place = Path(repository.relative(receipt)).with_suffix("")
    return repository.ROOT / WORK / "-".join(place.parts[-6:])


def child_command(sources: tuple[str, str, str], ids: list[str], receipt: Path) -> list[str]:
    """One child's command: the synthesis itself on the given script, cast and folder, for these
    segments, into a receipt of its own."""
    script, cast, folder = sources
    command = [sys.executable, "-B", "-m", "filmkit.narration.synthesis"]
    command += ["--script", script, "--cast", cast, "--folder", folder]
    return [*command, "--receipt", repository.relative(receipt), "--ids", ",".join(ids)]


def start(command: list[str], log: Path) -> subprocess.Popen:
    """Start one child at the film's root as a single narration process, its output in `log`."""
    environment = {**os.environ, VARIABLE: "1", repository.ROOT_VARIABLE: str(repository.ROOT)}
    with log.open("wb") as output:
        return subprocess.Popen(
            command,
            cwd=repository.ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
        )


def last_line(log: Path) -> str:
    """The last line a child wrote, or nothing when it wrote none."""
    lines = log.read_text(errors="replace").splitlines() if log.is_file() else []
    return next((line.strip()[:300] for line in reversed(lines) if line.strip()), "")


def narrate(sources: tuple[str, str, str], shares: list[list[str]], receipt: Path) -> list[dict]:
    """Narrate each share of segments in a child of its own, all at once, and wait for all.

    Returns each child's segments, exit status and seconds. Refused, once all have ended, when
    any failed; the work folder then stays, with every child's log. A run that passes removes it.
    """
    work = work_folder(receipt)
    work.mkdir(parents=True, exist_ok=True)
    for earlier in work.iterdir():
        earlier.unlink()
    started = time.monotonic()
    children = []
    for number, ids in enumerate(shares, 1):
        own, log = work / f"process-{number}.json", work / f"process-{number}.log"
        children.append((ids, log, start(child_command(sources, ids, own), log)))
    ended = []
    for ids, log, child in children:
        status = child.wait()
        seconds = round(time.monotonic() - started, 1)
        ended.append({"ids": ids, "exit": status, "seconds": seconds, "log": log})
    failed = [
        f"segments {', '.join(child['ids'])} exited {child['exit']} "
        f"({repository.relative(child['log'])}: {last_line(child['log'])})"
        for child in ended
        if child["exit"] != 0
    ]
    if failed:
        msg = "A narration process failed: " + "; ".join(failed)
        raise ProcessesError(msg)
    for left in work.iterdir():
        left.unlink()
    work.rmdir()
    return [{key: child[key] for key in ("ids", "exit", "seconds")} for child in ended]
