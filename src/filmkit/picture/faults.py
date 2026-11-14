"""Find the one-frame faults of an edition's two rendered pictures, at every frame.

A render can draw a fragment of a text glyph wrong for exactly one frame, in only one of the two
pictures rendered from the same composition, between the frames that the sampled measures of
`filmkit.picture.equivalence` compare. `compare_pictures` therefore also scans both pictures at
every frame. One FFmpeg filter graph decodes each picture once, pairs their frames by number,
turns them into full-range grey and writes, for each pair, one plane that holds both scans:

- the twin comparison: the two pictures' absolute difference, each sample more than THRESHOLD
  levels apart marked and the marks averaged over cells of CELL pixels, so that Python reads a
  small plane of cells and counts each frame with a lit cell outside the caption band
  (`equivalence.excluded_rows`). A frame that differs between two that do not is a fault: both
  pictures are decoded again around it, and the one whose frame lies more than THRESHOLD levels
  from each of its own neighbouring frames, at a sample where the pictures differ, while those
  agree within TOLERANCE, holds it. A one-frame difference that no one picture holds alone, as
  where two encodes draw a moving edge apart, is refused only above NOISE_CEILING levels; the
  report keeps one within it as residue. A difference that lasts two frames or more is no render's
  fault, and is named by its frames. Beside those cells the plane holds the share of each cell's
  samples more than `slivers.LEVEL` levels apart, from which `filmkit.picture.slivers` measures
  each frame's densest block; a frame beyond its bound for edge slivers is judged like a frame
  with a lit cell, at that level, and the report keeps the slivers within the bound.
- the caption band: inside the band the pictures differ by design, so each picture's band rows,
  stacked under the cells, are judged by its own frames, two of them kept in hand. A sample more
  than THRESHOLD levels from both neighbouring frames while those agree within TOLERANCE is a
  fault of that picture. A caption that appears or leaves changes once, and a mark that moves
  changes in every frame, so its neighbours disagree; both pass.

Each fault holds its frame, its time, its box in picture pixels (left, top, right and bottom, the
last two exclusive), its peak, its picture and whether it is a residue. The peak is the largest
difference from the twin or, in the caption band, from the nearer neighbouring frame. A refusal
names the command that renders the faulty picture again. `repairable` reads from a refused
comparison record the faults that rendering one picture again may repair, by that picture, for
`filmkit.picture.repair`, and refuses a record that holds any other finding.
"""

from __future__ import annotations

import math
import subprocess
import threading
from functools import partial
from typing import TYPE_CHECKING

import numpy as np

import filmkit.picture.slivers as slivers
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# In levels of full-range grey: a sample more than THRESHOLD levels from its twin, or from both
# neighbouring frames, is a fault, and neighbouring frames within TOLERANCE levels agree. Between
# clean twins the largest difference measured over two whole delivered pairs was 78 levels, at the
# edge of a glyph, beside a moving edge's residue (NOISE_CEILING), and the faults found in sixteen
# pictures of three films reached 124 to 219.
THRESHOLD = 90
TOLERANCE = 30
# A one-frame difference that no one picture holds alone is refused only above NOISE_CEILING
# levels. Each of the nine render faults measured departs in one picture from its own neighbouring
# frames, which agree, by 124 to 219 levels; the largest difference found outside the faults was
# 93 levels at one sample of a moving mark, whose edge the DDWG film's two Chinese encodes of
# round 36 drew apart at frame 30306. 120 lies between them.
NOISE_CEILING = 120
# The side in pixels of the cells over which the twin comparison averages its marks. It divides
# the encoder's 16-pixel blocks, to which the caption band is widened, so the band leaves whole
# cells out.
CELL = 8
# How many faults and lasting differences the report lists, and how many one-frame differences
# outside the band it decodes again to judge; any beyond those are refused unjudged.
LISTED = 10
EXAMINED = 100
# Seconds the scan may take, and the decode of a fault's neighbouring frames.
DEADLINE = 7200
NEIGHBOURS_DEADLINE = 600
# Full-range grey: the luma, expanded from the encoder's range to 0-255.
GREY = "scale=out_range=full,format=gray"
# How every decode starts, and how it writes its frames: raw grey, one plane per frame.
DECODE = ["ffmpeg", "-v", "error", "-nostdin"]
RAW = ["-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"]
# The command that renders the captioned picture again; with --uncaptioned, the other one. And the
# command that renders again each picture that holds a fault, and compares the two again.
RENDER = "python -m filmkit.produce render-picture --language {code}"
REPAIR = "python -m filmkit.produce repair-pictures --language {code}"


def apart(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """How far apart two grey planes are, sample by sample, in levels."""
    return np.abs(np.subtract(a, b, dtype=np.int16))


def box_of(held: np.ndarray, left: int, top: int) -> list[int]:
    """The box of a mask's samples in picture pixels, from where the mask's plane stands."""
    rows, columns = np.nonzero(held)
    return [
        left + int(columns.min()),
        top + int(rows.min()),
        left + int(columns.max()) + 1,
        top + int(rows.max()) + 1,
    ]


def departs(frames: np.ndarray, index: int, where: np.ndarray, level: int = THRESHOLD) -> bool:
    """Whether frame `index` of consecutive grey frames lies, at a sample of `where`, more than
    `level` levels from each frame beside it, while two frames beside it agree within
    TOLERANCE."""
    beside = [frames[i] for i in (index - 1, index + 1) if 0 <= i < len(frames)]
    held = where.copy()
    for other in beside:
        held &= apart(frames[index], other) > level
    if len(beside) == 2:
        held &= apart(*beside) <= TOLERANCE
    return bool(held.any())


class Twin:
    """The frames whose cells differ outside the caption band, in runs of consecutive frames,
    each with the box of its lit cells."""

    def __init__(self, size: tuple[int, int], rows: tuple[int, int]) -> None:
        self.size = size
        self.shape = (-(-size[1] // CELL), -(-size[0] // CELL))
        # The rows of cells compared: all but those of the caption band.
        self.compared = np.ones(self.shape[0], dtype=bool)
        self.compared[rows[0] // CELL : -(-rows[1] // CELL)] = False
        self.frames = 0
        self.runs: list[dict] = []

    def add(self, frame: int, cells: np.ndarray) -> None:
        rows = np.flatnonzero(cells.any(axis=1) & self.compared)
        if not rows.size:
            return
        columns = np.flatnonzero(cells[rows].any(axis=0))
        box = [
            int(columns[0]) * CELL,
            int(rows[0]) * CELL,
            min(self.size[0], (int(columns[-1]) + 1) * CELL),
            min(self.size[1], (int(rows[-1]) + 1) * CELL),
        ]
        self.frames += 1
        if self.runs and self.runs[-1]["last"] == frame - 1:
            run = self.runs[-1]
            run["last"] = frame
            run["box"] = [*map(min, run["box"][:2], box[:2]), *map(max, run["box"][2:], box[2:])]
        else:
            self.runs.append({"first": frame, "last": frame, "box": box})


class Band:
    """One picture's caption band, frame by frame with two frames in hand: the samples of a frame
    more than THRESHOLD levels from both frames beside it while those agree within TOLERANCE."""

    def __init__(self, top: int) -> None:
        self.top = top
        self.before: np.ndarray | None = None
        self.current: np.ndarray | None = None
        # The samples of the current frame more than THRESHOLD levels from the one before it, or
        # None where none is.
        self.entering: np.ndarray | None = None
        self.changes: list[dict] = []

    def add(self, frame: int, after: np.ndarray) -> None:
        if self.current is not None:
            leaving = apart(self.current, after) > THRESHOLD
            moved = bool(leaving.any())
            if moved and self.entering is not None:
                self.judge(frame - 1, leaving, after)
            self.entering = leaving if moved else None
        self.before, self.current = self.current, after

    def judge(self, frame: int, leaving: np.ndarray, after: np.ndarray) -> None:
        """Record the current frame where it departs from both frames beside it, which agree."""
        held = self.entering & leaving & (apart(self.before, after) <= TOLERANCE)
        if held.any():
            nearer = np.minimum(apart(self.current, self.before), apart(self.current, after))
            peak = int(nearer[held].max())
            self.changes.append({"frame": frame, "box": box_of(held, 0, self.top), "peak": peak})


def scan_command(
    paths: list[Path], size: tuple[int, int], rows: tuple[int, int], fps: int
) -> list[str]:
    """The FFmpeg command that decodes both pictures once, pairs their frames by number and
    writes for each pair one grey plane: the twin comparison's cells beside the edge slivers'
    cells and, where the caption band has rows, those cells widened to the picture's width over
    each picture's band rows."""
    width, (top, bottom) = size[0], rows
    padded = [-(-side // CELL) * CELL for side in size]
    columns, cell_rows = padded[0] // CELL, padded[1] // CELL
    pad = f"pad={padded[0]}:{padded[1]}," if padded != list(size) else ""
    twin = [
        f"[a][b]blend=all_mode=difference:shortest=1,{pad}split[over0][over1]",
        *(
            f"[over{n}]lut=y='255*gt(val,{level})',scale={columns}:{cell_rows}:flags=area[cells{n}]"
            for n, level in enumerate((THRESHOLD, slivers.LEVEL))
        ),
    ]
    grey = [f"[{n}:v:0]setpts=N/({fps}*TB),{GREY}" for n in range(2)]
    if bottom > top:
        graph = [
            *(f"{chain},split[{name}][{name}all]" for chain, name in zip(grey, "ab", strict=True)),
            *twin,
            f"[cells0][cells1]hstack,pad={width}:{cell_rows}[cells]",
            *(f"[{name}all]crop={width}:{bottom - top}:0:{top}[{name}band]" for name in "ab"),
            "[cells][aband][bband]vstack=inputs=3:shortest=1[out]",
        ]
    else:
        graph = [f"{chain}[{name}]" for chain, name in zip(grey, "ab", strict=True)]
        graph += [*twin, "[cells0][cells1]hstack[out]"]
    inputs = [argument for path in paths for argument in ("-i", str(path))]
    return [*DECODE, *inputs, "-filter_complex", ";".join(graph), "-map", "[out]", *RAW]


def decode(
    command: list[str],
    length: int,
    log: Path,
    count: int,
    each: Callable[[int, np.ndarray], None],
) -> None:
    """Run a decode and hand `each` every frame's number and its plane of `length` bytes; refused
    unless the decode yields exactly `count` planes without a message within DEADLINE."""
    read = 0
    with log.open("wb") as error:
        process = subprocess.Popen(
            command,
            cwd=repository.ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=error,
        )
        deadline = threading.Timer(DEADLINE, process.kill)
        deadline.start()
        try:
            for frame in range(count):
                data = process.stdout.read(length)
                if len(data) != length:
                    break
                each(frame, np.frombuffer(data, dtype=np.uint8))
                read += 1
            extra = process.stdout.read(1)
        finally:
            process.stdout.close()
            process.wait()
            deadline.cancel()
    message = log.read_text(errors="replace").strip()
    if process.returncode or message or extra or read != count:
        msg = (
            f"Decoding both pictures at every frame gave {read} of their {count} frames"
            f"{': ' + message[:300] if message else ''}"
        )
        raise PictureError(msg)


def neighbouring(path: Path, first: int, count: int, box: list[int], fps: int) -> np.ndarray:
    """Frames `first` to `first + count - 1` of a picture as grey within a box, decoded after a
    seek to half a frame before the first, which a picture's validated cadence makes exact."""
    left, top, right, bottom = box
    seek = f"{max(0, first - 0.5) / fps:.6f}"
    crop = f"{GREY},crop={right - left}:{bottom - top}:{left}:{top}"
    command = [*DECODE, "-ss", seek, "-i", str(path), "-map", "0:v:0", "-frames:v", str(count)]
    command += ["-vf", crop, *RAW]
    shape = (count, bottom - top, right - left)
    failed = f"Decoding frames {first} to {first + count - 1} of {path.name}"
    try:
        done = subprocess.run(
            command,
            cwd=repository.ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=NEIGHBOURS_DEADLINE,
        )
    except subprocess.TimeoutExpired:
        msg = f"{failed} did not end within {NEIGHBOURS_DEADLINE} s"
        raise PictureError(msg) from None
    if done.returncode or done.stderr or len(done.stdout) != math.prod(shape):
        msg = f"{failed} failed: {done.stderr.decode(errors='replace').strip()[:300]}"
        raise PictureError(msg)
    return np.frombuffer(done.stdout, dtype=np.uint8).reshape(shape)


def twin_difference(pictures: dict[str, Path], fps: int, frame: int, box: list[int]) -> np.ndarray:
    """How far apart the two pictures are at one frame within a box, decoded again there."""
    return apart(*(neighbouring(path, frame, 1, box, fps)[0] for path in pictures.values()))


def fault(
    change: dict, fps: int, picture: str | None, *, caption_band: bool, residue: bool = False
) -> dict:
    """A fault as the report lists it."""
    frame = change["frame"]
    return {
        "frame": frame,
        "time": round(frame / fps, 3),
        "box": change["box"],
        "peak": change["peak"],
        "picture": picture,
        "caption_band": caption_band,
        "residue": residue,
    }


def attribute(
    pictures: dict[str, Path], run: dict, rows: tuple[int, int], count: int, fps: int
) -> dict:
    """A one-frame difference of the twin comparison as a fault, from both pictures decoded again
    around it within its cells: the box and peak of its samples more than THRESHOLD levels apart
    outside the caption band, and the picture whose frame departs from its own neighbouring
    frames there, or None where not exactly one does, in which case a peak within NOISE_CEILING
    is a residue. A frame beyond the bound for edge slivers is judged at its run's level within
    its blocks, keeps its samples and is no residue."""
    frame, cells, level = run["first"], run["box"], run.get("level", THRESHOLD)
    first = max(0, frame - 1)
    length = min(count - 1, frame + 1) - first + 1
    stacks = {
        name: neighbouring(path, first, length, cells, fps) for name, path in pictures.items()
    }
    index = frame - first
    difference = apart(*(stack[index] for stack in stacks.values()))
    differs = difference > level
    differs[max(0, rows[0] - cells[1]) : max(0, rows[1] - cells[1])] = False
    if not differs.any():
        msg = f"Frame {frame} differs at every frame's comparison but not when decoded again"
        raise PictureError(msg)
    holding = [name for name, stack in stacks.items() if departs(stack, index, differs, level)]
    peak = int(difference[differs].max())
    change = {"frame": frame, "box": box_of(differs, *cells[:2]), "peak": peak}
    picture = holding[0] if len(holding) == 1 else None
    dense = {"samples": run["samples"]} if "samples" in run else {}
    residue = not dense and picture is None and peak <= NOISE_CEILING
    return fault(change, fps, picture, caption_band=False, residue=residue) | dense


def scan(
    pictures: dict[str, Path],
    size: tuple[int, int],
    rows: tuple[int, int],
    count: int,
    fps: int,
    work: Path,
) -> dict:
    """Compare both pictures, named by `pictures`, at every frame outside the caption band `rows`,
    measure their edge slivers there, scan each one's band rows, and report what the record
    keeps."""
    width, height = size[0], rows[1] - rows[0]
    twin, blocks = Twin(size, rows), slivers.Blocks(size, rows, CELL)
    bands = {name: Band(rows[0]) for name in pictures} if height > 0 else {}
    columns = twin.shape[1]
    stride = width if bands else 2 * columns
    start = stride * twin.shape[0]

    def add(frame: int, plane: np.ndarray) -> None:
        cells = plane[:start].reshape(-1, stride)
        twin.add(frame, cells[:, :columns])
        blocks.add(frame, cells[:, columns : 2 * columns])
        for n, band in enumerate(bands.values()):
            rows_of_band = plane[start + n * width * height : start + (n + 1) * width * height]
            band.add(frame, rows_of_band.reshape(height, width))

    command = scan_command(list(pictures.values()), size, rows, fps)
    decode(command, start + len(bands) * width * height, work / "every-frame.log", count, add)
    runs = sorted([*twin.runs, *blocks.refused(twin.runs)], key=lambda run: run["first"])
    single = [run for run in runs if run["first"] == run["last"]]
    lasting = [run for run in runs if run["first"] < run["last"]]
    found = [attribute(pictures, run, rows, count, fps) for run in single[:EXAMINED]]
    found += [
        fault(change, fps, name, caption_band=True)
        for name, band in bands.items()
        for change in band.changes
    ]
    residues = sum(row["residue"] for row in found)
    changes = sum(len(band.changes) for band in bands.values())
    return {
        "frames": count,
        "threshold": THRESHOLD,
        "tolerance": TOLERANCE,
        "cell_pixels": CELL,
        "differing_frames": twin.frames,
        "lasting": lasting[:LISTED],
        "lasting_runs": len(lasting),
        "band_changes": {name: len(band.changes) for name, band in bands.items()},
        "faults": sorted(found, key=lambda row: (row["residue"], row["frame"]))[:LISTED],
        "fault_frames": len(single) + changes - residues,
        "residue_frames": residues,
        "slivers": blocks.report(fps, partial(twin_difference, pictures, fps)),
    }


def findings(report: dict, code: str) -> list[str]:
    """A report's findings: each one-frame fault that is no residue, with the command that renders
    its picture again, and each difference that lasts; one beyond the bound for edge slivers
    names its samples and the bound."""
    found = []
    faults = [row for row in report["faults"] if not row["residue"]]
    for row in faults:
        at = f"encoded frame {row['frame']} at {row['time']:.3f} s"
        where = "in the caption band" if row["caption_band"] else "outside the caption band"
        where += slivers.beyond(row)
        if row["picture"] is None:
            above = "" if "samples" in row else f", above a residue's ceiling of {NOISE_CEILING}"
            found.append(
                f"{at}: the pictures differ for one frame by {row['peak']} levels in box "
                f"{row['box']} {where}{above}, and no one picture alone departs from its "
                "neighbouring frames"
            )
            continue
        command = RENDER.format(code=code) + (
            " --uncaptioned" if row["picture"] == "uncaptioned" else ""
        )
        found.append(
            f"{at}: the {row['picture']} picture holds a one-frame fault of {row['peak']} levels "
            f"in box {row['box']} {where}; render it again with {command}"
        )
    hidden = report["fault_frames"] - len(faults)
    found += [f"encoded: {hidden} more one-frame differences"] if hidden > 0 else []
    found += [
        f"encoded frames {run['first']}-{run['last']}: the pictures differ by more than "
        f"{run.get('level', report['threshold'])} levels in box {run['box']} outside the caption "
        f"band{slivers.beyond(run)}"
        for run in report["lasting"]
    ]
    hidden = report["lasting_runs"] - len(report["lasting"])
    found += [f"encoded: {hidden} more runs of differing frames"] if hidden > 0 else []
    return found


def repairable(record: dict, code: str) -> dict[str, list[dict]]:
    """The one-frame faults of a comparison record by the picture that holds each; none where the
    record passed.

    Refused, naming each reason, where the record holds a finding that rendering one picture again
    cannot repair: composition instants that differ beyond their captions, a sampled frame beyond
    the encoders' noise where no one picture holds a fault outside the caption band, a difference
    that lasts two frames or more, a one-frame difference above a residue's ceiling that no one
    picture holds, or more differences than it lists. A fault outside the band that lands on a
    sampled frame fails that frame's measures too, so that frame alone stays repairable. The
    fields decide, never the findings' text.
    """
    if record.get("verdict") == "pass":
        return {}
    encoded, reasons, named = record["encoded"], [], {}
    every = encoded.get("every_frame", {})
    listed = [row for row in every.get("faults", []) if not row["residue"]]
    held = {row["frame"] for row in listed if row["picture"] and not row["caption_band"]}
    differing = record["composition"].get("differing_instants", 0)
    if differing:
        reasons.append(f"the compositions differ beyond their captions at {differing} instants")
    failing = encoded.get("failing", [])
    reasons += [
        f"sampled frame {row['frame']} differs beyond the encoders' noise without a one-frame "
        "fault of one picture there"
        for row in failing
        if row["frame"] not in held
    ]
    hidden = encoded.get("failing_frames", 0) - len(failing)
    sampled = f"{hidden} more sampled frames differ beyond the encoders' noise"
    reasons += [sampled] if hidden > 0 else []
    lasting = every.get("lasting", [])
    reasons += [
        f"the pictures differ over frames {run['first']}-{run['last']} in box {run['box']}"
        for run in lasting
    ]
    hidden = every.get("lasting_runs", 0) - len(lasting)
    reasons += [f"{hidden} more runs of frames differ"] if hidden > 0 else []
    for row in listed:
        if row["picture"] is None:
            reasons.append(
                f"frame {row['frame']} differs by {row['peak']} levels in box {row['box']} and "
                f"no one picture holds it; render both pictures again with "
                f"{RENDER.format(code=code)} and with --uncaptioned"
            )
        else:
            named.setdefault(row["picture"], []).append(row)
    hidden = every.get("fault_frames", 0) - len(listed)
    unlisted = f"{hidden} more one-frame differences are not listed with a picture"
    reasons += [unlisted] if hidden > 0 else []
    if reasons or not named:
        found = "; ".join(reasons) or "it names no fault of one picture"
        msg = f"The comparison record holds what rendering one picture again cannot repair: {found}"
        raise PictureError(msg)
    return named
