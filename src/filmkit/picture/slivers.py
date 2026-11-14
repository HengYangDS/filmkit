"""Measure the edge slivers of an edition's two rendered pictures, at every frame.

Two captures of one composition can draw the anti-aliased edge of a mark slightly apart, most
often while the mark moves or draws on: along that edge the pictures then lie some tens of levels
apart in a row or column of samples one or two wide, an edge sliver. The fault scan's own
threshold (`filmkit.picture.faults`), a sample more than 90 levels apart, passes it by design,
and a mean over a tile or a frame does not show it. A mark of low contrast that one picture lacks
for a frame hides the same way. The scan of every frame therefore also writes, for each cell, the
share of its samples more than LEVEL levels apart, and `Blocks` keeps of each frame the block
measure: the most such samples that any square of BLOCK pixels outside the caption band holds,
with that block. From that one series, which follows the measure of the reviewers who found the
slivers, come:

- the one-frame transients: the frames whose measure exceeds that of both frames beside them by
  JUMP samples or more while those agree within AGREEMENT, where the pictures part for one frame;
- the slivers: the runs of frames whose measure reaches NOTED samples, joined over a gap of one
  frame. The record counts them and lists the LISTED largest, each with its frames, its time,
  its block, its samples and its level, the largest difference in that block at its densest
  frame, for which both pictures are decoded again there;
- the frames beyond the bound: a frame whose densest block holds more than BOUND such samples is
  refused. The fault scan judges those frames as it does its own: one frame alone is decoded
  again with its neighbours and names the picture that holds it, which `repair-pictures` renders
  again, and frames that follow one another are a difference that lasts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

# In levels of full-range grey: a sample counts where the pictures lie more than LEVEL apart, in
# squares of BLOCK picture pixels. The DDWG film's reviewers measure the same on its 3840x2160
# masters (rounds 37 to 40, sliver.py and its pass): the samples more than 40 levels apart in the
# densest 32x32 block outside the caption band. In fifteen windows of 366 frames of the delivered
# English masters this module's series lay within 0.25 samples of theirs, which rounds each
# cell's share to a byte, and named the same blocks, one-frame events and runs.
LEVEL = 40
BLOCK = 32
# A frame is noted from NOTED samples, one more than a row one sample wide across a block, and
# noted frames at most JOINED frames apart are one sliver, as the reviewers list their runs.
NOTED = 33
JOINED = 2
# A one-frame transient exceeds both frames beside it by JUMP samples or more while those agree
# within AGREEMENT: the reviewers' rule for a frame in which one master alone departs.
JUMP = 12
AGREEMENT = 6
# The most samples more than LEVEL levels apart that one block may hold: three rows across it.
# The reviewers accepted the delivered DDWG film with a note, nothing being visible at 1:1 (EN38-6,
# EN40-13). Over every frame of its English masters their measure reached 64 in rounds 39 and 40,
# at frames 76515 to 76519, two rows of a rail that draws on, 42 to 48 levels apart, then 50, 46
# and 44 at frames 57811, 44544 and 63744, at marks in motion, in 13 runs from NOTED; in round 38
# it reached 44. The slivers' levels reached 55. Of the Chinese masters only seventeen windows of
# 258 frames were measured, where the zh reviewer counted the most cells: 64 at frames 76875 to
# 76878, the same rail, and at most 32 elsewhere. What is no sliver measures more: between two
# frames of one master a label that moves one step 190 (frame 44545) and a cut 586 or 1,024
# (frames 33974 and 94), and the strokes of one 64x64 area drawn 61 levels dimmer for one frame
# 251. 96 lies half way from the largest sliver to a stroke four samples wide across a block, 128.
BOUND = 96
# How many slivers the record lists.
LISTED = 10


def beyond(row: dict) -> str:
    """The clause of a finding that names the samples of a frame or run beyond the bound, and
    the bound; nothing for a finding of the fault scan's own threshold."""
    if "samples" not in row:
        return ""
    return (
        f", at {row['samples']} samples of one block where at most {BOUND} may lie more than "
        f"{LEVEL} levels apart"
    )


def transients(samples: Sequence[int]) -> list[int]:
    """The frames of a block measure's series that exceed both frames beside them by JUMP or
    more while those two agree within AGREEMENT."""
    series = np.asarray(samples, dtype=np.int64)
    if series.size < 3:
        return []
    before, at, after = series[:-2], series[1:-1], series[2:]
    held = (at - np.maximum(before, after) >= JUMP) & (np.abs(before - after) <= AGREEMENT)
    return (np.flatnonzero(held) + 1).tolist()


def runs(frames: Sequence[int], gap: int) -> list[tuple[int, int]]:
    """Ascending frames as the first and last frame of each run of frames at most `gap` apart."""
    found: list[tuple[int, int]] = []
    for frame in frames:
        if found and frame - found[-1][1] <= gap:
            found[-1] = (found[-1][0], frame)
        else:
            found.append((frame, frame))
    return found


class Blocks:
    """The block measure of every frame in order: the samples of its densest block and that
    block's index, and for a frame beyond the bound the box of its blocks beyond it."""

    def __init__(self, size: tuple[int, int], rows: tuple[int, int], cell: int) -> None:
        self.size, self.rows, self.cell = size, rows, cell
        shape = (-(-size[1] // cell), -(-size[0] // cell))
        # The rows of cells compared: all but those of the caption band.
        self.compared = np.ones(shape[0], dtype=bool)
        self.compared[rows[0] // cell : -(-rows[1] // cell)] = False
        # The cells at which the blocks start, down and across.
        step = BLOCK // cell
        self.starts = (list(range(0, shape[0], step)), list(range(0, shape[1], step)))
        self.samples: list[int] = []
        self.densest: list[int] = []
        self.beyond: dict[int, list[int]] = {}

    def box(self, index: int) -> list[int]:
        """A block's box in picture pixels; the last of a row or column ends with the picture."""
        row, column = divmod(index, len(self.starts[1]))
        left, top = column * BLOCK, row * BLOCK
        return [left, top, min(self.size[0], left + BLOCK), min(self.size[1], top + BLOCK)]

    def add(self, frame: int, cells: np.ndarray) -> None:
        """Take the next frame's cells: for each, the share of its samples more than LEVEL levels
        apart as a byte, which gives its samples back within the scaler's rounding."""
        counted = cells[self.compared]
        if not counted.any():
            self.samples.append(0)
            self.densest.append(0)
            return
        counts = np.zeros(cells.shape, dtype=np.int64)
        counts[self.compared] = np.rint(counted * (self.cell**2 / 255))
        down, across = self.starts
        blocks = np.add.reduceat(np.add.reduceat(counts, down, axis=0), across, axis=1)
        index = int(blocks.argmax())
        self.samples.append(int(blocks.flat[index]))
        self.densest.append(index)
        over = np.flatnonzero(blocks > BOUND)
        if over.size:
            boxes = [self.box(int(block)) for block in over]
            self.beyond[frame] = [
                *(min(box[n] for box in boxes) for n in (0, 1)),
                *(max(box[n] for box in boxes) for n in (2, 3)),
            ]

    def events(self) -> list[dict]:
        """The slivers in order: each run of noted frames with its densest frame, that frame's
        samples and whether it is a one-frame transient."""
        noted = [frame for frame, samples in enumerate(self.samples) if samples >= NOTED]
        passing = set(transients(self.samples))
        found = []
        for first, last in runs(noted, JOINED):
            frame = max(range(first, last + 1), key=lambda n: (self.samples[n], -n))
            found.append(
                {
                    "first": first,
                    "last": last,
                    "frames": last - first + 1,
                    "frame": frame,
                    "samples": self.samples[frame],
                    "transient": frame in passing,
                }
            )
        return found

    def refused(self, held: list[dict]) -> list[dict]:
        """The frames beyond the bound as the fault scan's runs of consecutive frames, each with
        the box of its blocks beyond the bound, its most samples and the level they exceed; the
        frames of `held`, runs that the fault scan already judges, are left out."""
        known = {frame for run in held for frame in range(run["first"], run["last"] + 1)}
        found = []
        for first, last in runs(sorted(set(self.beyond) - known), 1):
            boxes = [self.beyond[frame] for frame in range(first, last + 1)]
            box = [
                *(min(box[n] for box in boxes) for n in (0, 1)),
                *(max(box[n] for box in boxes) for n in (2, 3)),
            ]
            samples = max(self.samples[first : last + 1])
            found.append(
                {"first": first, "last": last, "box": box, "samples": samples, "level": LEVEL}
            )
        return found

    def level(self, difference: np.ndarray, box: list[int]) -> int:
        """The largest of a block's differences outside the caption band's rows."""
        compared = np.ones(difference.shape[0], dtype=bool)
        compared[max(0, self.rows[0] - box[1]) : max(0, self.rows[1] - box[1])] = False
        return int(difference[compared].max(initial=0))

    def report(self, fps: int, difference: Callable[[int, list[int]], np.ndarray]) -> dict:
        """What the record keeps: the measure's terms, its largest value, the one-frame
        transients, the slivers counted and the LISTED largest listed, each with the level that
        `difference`, the pictures' difference at a frame within a box, shows in its block."""
        found = self.events()
        listed = sorted(found, key=lambda event: (-event["samples"], event["first"]))[:LISTED]
        for event in listed:
            block = self.box(self.densest[event["frame"]])
            event["time"] = round(event["first"] / fps, 3)
            event["block"] = block
            event["level"] = self.level(difference(event["frame"], block), block)
        return {
            "level": LEVEL,
            "block_pixels": BLOCK,
            "bound": BOUND,
            "noted_from": NOTED,
            "jump": JUMP,
            "agreement": AGREEMENT,
            "largest": max(self.samples, default=0),
            "transient_frames": len(transients(self.samples)),
            "events": listed,
            "event_runs": len(found),
            "frames_beyond_the_bound": len(self.beyond),
        }
