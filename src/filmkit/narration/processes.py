"""Narrate an edition's segments in several processes of the speech model at once.

A segment's takes depend on its own request alone: every thought is generated from its own text,
seed and settings, and written to files named by its own fingerprint. So the segments that a
narration has to generate can be divided among processes without changing a byte. The synthesis
(`filmkit.narration.synthesis`) plans as it always has; when more than one segment is to be
generated and the count is over one, `narrate` here divides those segments among the processes,
the longest spoken text first to the least loaded, and starts for each one child of the synthesis
itself, `--ids <its segments>`, which writes a receipt of its own in a work folder that no other
step reads. When all have ended, the synthesis takes its ordinary path, in which it finds every
segment retained, loads no model and writes the one receipt in segment order. The work folder
of a receipt is cleared when a synthesis for that receipt begins and kept when it ends, so the
children's logs can be read after a run that passed as after one that failed.

The count comes from the host's memory, one process for every 16 GB up to three (`host_count`),
unless `VARIABLE` names another; 1 keeps the single process. A child is given the count 1, so it
never divides again. A child that fails does not stop the others; once
all have ended the narration is refused, naming each failed child, its segments, its exit status,
its log and the last five lines it wrote, among which the refusal an unresolved take raises
stands. What a failed child left behind is then judged by the next run as an interrupted run's
always was.

No child outlives the narration. Each leads a session of its own, and when the narration's wait
is cut short, by an interrupt, by a request to end (SIGTERM), by a hang-up (SIGHUP) or by a
failure of its own, such as a child that cannot be started, it ends every child's process group
(`filmkit.child_processes`) and refuses, naming what cut it short. A child holds a speech model
of several gigabytes and the GPU; one left running would narrate to the end of its share beside
the next run's children.

Measured on the eight segments of a film's English edition, 511 s of speech, on a host of 128 GB
on 17 November 2026, the arms back to back: one process 180.7 and 176.1 s, two 153.6 and 143.8
s, three 117.2 s, four 126.2 s; all 64 takes equal, byte for byte, to the film's own. One process
left the GPU a quarter idle; more filled it, and each take slowed as they shared it. Three and
four processes were measured once each, on that one host.
"""

from __future__ import annotations

import functools
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import filmkit.child_processes as child_processes
import filmkit.repository as repository

# The variable that names how many processes narrate an edition. Without it the count comes from
# the host: one process for every `MEMORY_FOR_EACH` bytes of its memory, at least one and at most
# `MOST`. A process holds about 4.6 GB at its peak, and the host needs the rest for everything
# else it runs; three is where the gain stopped on the one host measured.
VARIABLE = "FILMKIT_NARRATION_PROCESSES"
MEMORY_FOR_EACH = 16 * 1024**3
MOST = 3
# The children's receipts and logs, below the film's root, in a folder for each receipt.
WORK = Path("build/runtime/work/narration-processes")
# Seconds between two looks at the children that still run.
POLL_SECONDS = 0.1
# How many of a failed child's last lines its refusal quotes.
QUOTED_LINES = 5


class ProcessesError(ValueError):
    """The count of narration processes is no count, a narration process failed, or the narration
    was stopped while its processes ran."""


@functools.cache
def host_memory() -> int | None:
    """The host's memory in bytes, read once by the standard library, or None where it cannot
    be read."""
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return None


def host_count() -> int:
    """How many processes the host narrates in: one for every `MEMORY_FOR_EACH` bytes of its
    memory, at least one and at most `MOST`; one where its memory cannot be read."""
    return max(1, min(MOST, (host_memory() or 0) // MEMORY_FOR_EACH))


def count() -> int:
    """How many processes narrate: what `VARIABLE` names, a positive whole number, or else the
    host's count (`host_count`)."""
    named = os.environ.get(VARIABLE)
    if not named:
        return host_count()
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
    """The folder of the children that narrate for a receipt, named after the receipt's whole
    path from the film's root, so that no two receipts share one. The synthesis refuses a
    receipt outside the root before it comes here."""
    place = receipt.relative_to(repository.ROOT).with_suffix("")
    return repository.ROOT / WORK / "-".join(place.parts)


def clear_work(receipt: Path) -> None:
    """Remove the work folder an earlier run for this receipt left: its children's logs and
    receipts. Every run of the synthesis for a receipt does this first, whether it divides or
    narrates in its own process, and leaves its own work after it, so a failed run's logs can be
    read until the next run and no child's receipt of an earlier run stands beside a later one."""
    work = work_folder(receipt)
    if work.is_dir():
        shutil.rmtree(work)


def child_command(sources: tuple[str, str, str, str], ids: list[str], receipt: Path) -> list[str]:
    """One child's command: the synthesis itself on the given edition, script, cast and folder,
    for these segments, into a receipt of its own."""
    code, script, cast, folder = sources
    command = [sys.executable, "-B", "-m", "filmkit.narration.synthesis", "--language", code]
    command += ["--script", script, "--cast", cast, "--folder", folder]
    return [*command, "--receipt", repository.relative(receipt), "--ids", ",".join(ids)]


def start(command: list[str], log: Path) -> subprocess.Popen:
    """Start one child at the film's root as a single narration process that leads a session of
    its own, so that its whole process group can be ended, its output in `log`."""
    environment = {**os.environ, VARIABLE: "1", repository.ROOT_VARIABLE: str(repository.ROOT)}
    with log.open("wb") as output:
        return subprocess.Popen(
            command,
            cwd=repository.ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def last_lines(log: Path) -> str:
    """The last `QUOTED_LINES` lines a child wrote that are not empty, in their order and joined
    by bars, or nothing when it wrote none. The exception that ended a child is seldom its very
    last line: what a library prints as the process ends stands after it."""
    lines = log.read_text(errors="replace").splitlines() if log.is_file() else []
    written = [line.strip()[:300] for line in lines if line.strip()]
    return " | ".join(written[-QUOTED_LINES:])


def wait_for_all(
    children: list[tuple[list[str], Path, subprocess.Popen]], started: float
) -> list[dict]:
    """Wait for every child and return each one's number, segments, exit status, log and
    seconds: the seconds from the narration's start to the moment that child was found ended,
    whichever child ended first. Each look at a child defers a request to end until the look
    is over (`child_processes.exit_status`); between two looks a request cuts the wait."""
    ended: dict[int, dict] = {}
    while len(ended) < len(children):
        for number, (ids, log, child) in enumerate(children):
            if number in ended:
                continue
            if (status := child_processes.exit_status(child)) is not None:
                seconds = round(time.monotonic() - started, 1)
                ended[number] = {"number": number + 1, "ids": ids, "exit": status}
                ended[number] |= {"seconds": seconds, "log": log}
        if len(ended) < len(children):
            time.sleep(POLL_SECONDS)
    return [ended[number] for number in range(len(children))]


def cut_short(error: BaseException) -> str:
    """What cut a narration's wait for its children short, as its refusal names it."""
    if isinstance(error, child_processes.Terminated):
        return error.request
    return f"{type(error).__name__}: {error}"


def narrate(sources: tuple[str, str, str], shares: list[list[str]], receipt: Path) -> list[dict]:
    """Narrate each share of segments in a child of its own, all at once, and wait for all.

    Returns each child's number, segments, exit status and seconds. Refused, once all have
    ended, when any failed. The work folder, which the synthesis cleared when it began
    (`clear_work`), stays after the run, pass or fail, with every child's log and receipt. A
    wait that is cut short ends every child's process group and refuses, naming the cause: a
    request to end goes on as `Terminated` with that refusal, anything else as `ProcessesError`.
    """
    work = work_folder(receipt)
    work.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    children: list[tuple[list[str], Path, subprocess.Popen]] = []
    # From a first request to end until the children are ended, every further one is dropped:
    # the stop lies inside the block that takes the requests.
    with child_processes.terminable():
        try:
            for number, ids in enumerate(shares, 1):
                own, log = work / f"process-{number}.json", work / f"process-{number}.log"
                # A request that arrives while a child starts waits until the child is held here.
                with child_processes.held():
                    children.append((ids, log, start(child_command(sources, ids, own), log)))
            ended = wait_for_all(children, started)
        except BaseException as error:
            # A child that has ended was reaped by the wait: its number is not signalled.
            running = [child for *_, child in children if child.returncode is None]
            child_processes.stop(running, signal.SIGTERM, groups=True)
            msg = (
                f"The narration was stopped by {cut_short(error)}; every narration process it "
                f"had started ({len(children)}) was ended with it; their logs are in "
                f"{repository.relative(work)}"
            )
            if isinstance(error, child_processes.Terminated):
                # Still a request to end, now with what the narration says of it.
                raise child_processes.Terminated(error.number, msg) from None
            raise ProcessesError(msg) from error
    failed = [
        f"segments {', '.join(child['ids'])} exited {child['exit']} "
        f"({repository.relative(child['log'])}: {last_lines(child['log'])})"
        for child in ended
        if child["exit"] != 0
    ]
    if failed:
        msg = "A narration process failed: " + "; ".join(failed)
        raise ProcessesError(msg)
    return [{key: child[key] for key in ("number", "ids", "exit", "seconds")} for child in ended]
