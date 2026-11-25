"""The host class of a node's run, measured as the host's rules measure it.

Host rule 3 of the shared rules' section "Host admission" counts a build light only when two
measures both stay at two cores or under: its CPU time, user and system with every descendant
included, over its wall time is at most 2.0; and the summed `%cpu` of its process tree, sampled
by `ps` every five seconds, has no two consecutive samples above 200 %. One that measures over
two cores by either is heavy from then on, and model work on the GPU is heavy whatever cores it
uses (rule 2). A run measures both here: the CPU time from `resource.getrusage` of the process
and its waited-for children at its two ends, and the samples from a daemon thread that reads
`ps -A -o pid=,ppid=,%cpu=`. The class is `gpu` for a node that declares model work, else
`heavy` where this run or the node's previous record measured heavy, else `light`. The engine
takes no ticket and tells the host's keeper nothing; a session reads the measures from the
record.
"""

from __future__ import annotations

import os
import resource
import subprocess
import threading
import time

from filmkit.graph.records import HostClass, Measured

# Host rule 3: at most this many cores, by CPU time over wall time and by a sample's `%cpu`.
LIGHT_CORES = 2.0
# Host rule 3: the process tree is sampled every this many seconds, and this many consecutive
# samples above two cores make a run heavy.
SAMPLE_SECONDS = 5.0
CONSECUTIVE = 2
# Host rule 7: consecutive heavy commands share one ticket only while every one is measured and
# their last run times sum to at most this many seconds; a command never measured enters alone.
SHARED_TICKET_SECONDS = 1800
# The sampler's command, which lists every process with its parent and its `%cpu`.
PS = ("/bin/ps", "-A", "-o", "pid=,ppid=,%cpu=")


def cpu_seconds() -> float:
    """The user and system seconds of this process and its waited-for children so far."""
    own, children = (
        resource.getrusage(who) for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
    )
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def tree_percent(listing: str, root: int) -> float:
    """The summed `%cpu` of a process and its descendants in a `ps` listing of
    `pid ppid %cpu` lines; 0 where the process is not listed."""
    rows = {}
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) == 3:
            rows[int(fields[0])] = (int(fields[1]), float(fields[2]))
    if root not in rows:
        return 0.0
    tree, grown = {root}, True
    while grown:
        found = {pid for pid, (parent, _) in rows.items() if parent in tree} - tree
        tree |= found
        grown = bool(found)
    return sum(rows[pid][1] for pid in tree)


def longest_above(samples: list[float]) -> int:
    """The longest run of consecutive samples above two cores."""
    longest = current = 0
    for percent in samples:
        current = current + 1 if percent > LIGHT_CORES * 100 else 0
        longest = max(longest, current)
    return longest


def measured(cpu: float, wall: float, samples: list[float]) -> Measured:
    """The raw measures of a run from its CPU seconds, its wall seconds and its samples."""
    return Measured(
        cpu_seconds=round(cpu, 3),
        cpu_per_wall=round(cpu / wall, 3) if wall > 0 else 0.0,
        samples=len(samples),
        above=longest_above(samples),
    )


def host_class(measures: Measured, *, gpu: bool, previous: HostClass | None) -> HostClass:
    """The class a run gives its node: `gpu` for model work, `heavy` where this run or the
    node's previous record measured heavy, `light` otherwise."""
    if gpu:
        return "gpu"
    over = measures.cpu_per_wall > LIGHT_CORES or measures.above >= CONSECUTIVE
    return "heavy" if over or previous == "heavy" else "light"


class Meter:
    """One run's measures, from `start` to `stop`."""

    def __init__(self) -> None:
        self.samples: list[float] = []
        self._cpu, self._wall = cpu_seconds(), time.monotonic()
        self._stopped = threading.Event()
        self._thread = threading.Thread(
            target=self._sample, name="filmkit-host-sampler", daemon=True
        )
        self._thread.start()

    def _sample(self) -> None:
        while not self._stopped.wait(SAMPLE_SECONDS):
            try:
                listed = subprocess.run(
                    PS, capture_output=True, text=True, check=True, timeout=SAMPLE_SECONDS
                ).stdout
            except (OSError, subprocess.SubprocessError):
                continue
            self.samples.append(tree_percent(listed, os.getpid()))

    def stop(self) -> Measured:
        """End the sampling and return the run's measures."""
        self._stopped.set()
        self._thread.join(timeout=SAMPLE_SECONDS)
        return measured(cpu_seconds() - self._cpu, time.monotonic() - self._wall, self.samples)


def start() -> Meter:
    """Begin measuring a run."""
    return Meter()
