"""Measure a picture's rows against the ground: the measures a derivation's decode writes, and the
edge rows that hold no caption.

A derivation (`filmkit.picture.derivation`) paints the caption band's rows with one ground. At a
frame without a caption the whole band can be compared with that ground. At a frame that shows a
caption only the rows no caption reaches can: the painted rows are the band widened by a margin,
so their outermost rows, the edge rows, lie outside every caption paint the band audit saw.
`free_frames` and `ground_check` serve the first measure, `read_ground` the ground itself;
`edge_rows` says how many of them each side has, up to `EDGE_ROWS`; `edge_filter` crops them out
of every frame in the derivation's own decode; `edge_check` refuses a frame at which they stand
farther from the ground than the tolerance. A ground that changes while a caption shows, a scene
with a ground of its own or a fade laid over the whole frame, is caught there, as is a plate
under a caption that is taller than the band.

Not proven by either check: a change of the ground confined to the rows a caption covers, at
frames that show the caption. The derived picture would paint over it.
"""

from __future__ import annotations

import math
import re
import subprocess
from typing import TYPE_CHECKING

import numpy as np

import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.specification import FPS

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# The frames a second at which the band audit runs the composition: the frame audit's own step.
AUDIT_FPS = 30
# Frames left out at each end of a stretch without a caption: two steps of the band audit.
EDGE_FRAMES = 2 * FPS // AUDIT_FPS
# The most a sample may depart from the ground, in 8-bit levels, in the band at a frame without a
# caption and in the edge rows at any frame. A caption or a mark departs by tens to hundreds of
# levels; the encoder's ripple in a flat band reached 2 levels below busy synthetic content and
# none on a film's span of 7,200 frames (17 November 2026).
GROUND_TOLERANCE = 3
# The rows measured at each side of the painted rows, at most, in picture pixels: one encoder
# block.
EDGE_ROWS = 16
PLANES = ("y", "u", "v")
_FRAME = re.compile(r"frame:\d+\s.*pts_time:(\S+)")
_EXTREME = re.compile(r"lavfi\.signalstats\.([YUV])(?:MIN|MAX)=(\d+)")


def departures(stats: Path, ground: dict, fps: int) -> Iterator[tuple[int, int]]:
    """Each measured frame of a stats file, in its order, and how far the lowest or the highest
    sample of any plane of the measured rows stands from the ground, in levels.

    The file is read line by line, since a whole film's edge rows fill tens of megabytes. A
    frame without its time or without all six extremes is refused as not readable.
    """

    def departure(frame: int, held: list[tuple[str, str]]) -> tuple[int, int]:
        if len(held) != 6:
            msg = f"The measure of frame {frame} is not readable"
            raise PictureError(msg)
        return frame, max(abs(int(value) - ground[plane.lower()]) for plane, value in held)

    frame, held = None, []
    with stats.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if line.startswith("frame:"):
                if frame is not None:
                    yield departure(frame, held)
                timed = _FRAME.match(line)
                if timed is None:
                    msg = f"A measure after frame {frame} names no time"
                    raise PictureError(msg)
                frame, held = round(float(timed[1]) * fps), []
            else:
                held += _EXTREME.findall(line)
    if frame is not None:
        yield departure(frame, held)


def edge_rows(rows: tuple[int, int], caption: list[float], scale: float) -> tuple[int, int]:
    """How many rows at the top and at the bottom of the painted rows are measured at every
    frame: those between the painted rows' edge and the caption paints, an even count of at most
    `EDGE_ROWS`. `caption` holds the first and the last row any caption paint reached, in the
    composition's frame, which `scale` brings to the picture's."""
    top = math.floor(caption[0] * scale) - rows[0]
    bottom = rows[1] - math.ceil(caption[1] * scale)
    return tuple(max(0, min(EDGE_ROWS, free // 2 * 2)) for free in (top, bottom))


def edge_filter(
    source: str, size: tuple[int, int], rows: tuple[int, int], edges: tuple[int, int], stats: Path
) -> str:
    """The filter graph from the stream `source` to `[edges]` that measures the edge rows of every
    frame: the top and the bottom edge, stacked where both exist, their lowest and highest samples
    printed to `stats`, a path without a colon or a quote."""
    top, bottom = edges
    crops = [
        f"crop={size[0]}:{count}:0:{at}"
        for count, at in ((top, rows[0]), (bottom, rows[1] - bottom))
        if count
    ]
    measure = f"signalstats,metadata=mode=print:file={stats}[edges]"
    if len(crops) == 1:
        return f"[{source}]{crops[0]},{measure}"
    return (
        f"[{source}]split=2[edgetop][edgebottom];[edgetop]{crops[0]}[top];"
        f"[edgebottom]{crops[1]}[bottom];[top][bottom]vstack=inputs=2,{measure}"
    )


def edge_check(stats: Path, ground: dict, tolerance: int, fps: int) -> dict:
    """Read the edge rows' measures and refuse a frame that departs from the ground.

    Every frame from the first must be measured, in order. Returns the frames checked and the
    largest departure.
    """
    count, largest, worst = 0, 0, None
    for frame, departure in departures(stats, ground, fps):
        if frame != count:
            msg = f"The edge rows were measured at frame {frame} where frame {count} was due"
            raise PictureError(msg)
        count += 1
        if departure > largest:
            largest, worst = departure, frame
    if largest > tolerance:
        msg = (
            "The captioned picture shows another ground at the edge of the painted rows, where "
            f"no caption stands, at frame {worst}: a sample stands {largest} levels from the "
            "band's ground"
        )
        raise PictureError(msg)
    return {"frames": count, "largest_departure": largest, "verdict": "pass"}


def free_frames(stretches: list[list[float]], fps: int = FPS) -> list[tuple[int, int]]:
    """The frames the ground check reads: each stretch without a caption as its first and last
    frame, less `EDGE_FRAMES` at each end; a stretch too short to keep a frame is left out."""
    kept = []
    for first, last in stretches:
        a, b = round(first * fps) + EDGE_FRAMES, round(last * fps) - EDGE_FRAMES
        if b >= a:
            kept.append((a, b))
    return kept


def selection(frames: list[tuple[int, int]]) -> str:
    """An FFmpeg select expression true inside these runs of frames, the sum balanced so that its
    depth stays logarithmic."""
    terms = [f"between(n,{a},{b})" for a, b in frames]
    while len(terms) > 1:
        paired = [f"({a}+{b})" for a, b in zip(terms[::2], terms[1::2], strict=False)]
        terms = paired + terms[len(paired) * 2 :]
    return terms[0]


def read_ground(source: Path, rows: tuple[int, int], size: tuple[int, int], frame: int) -> dict:
    """The ground of the band: the median sample of each plane of the picture's rows at a frame
    without a caption."""
    width, height = size[0], rows[1] - rows[0]
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-ss",
        f"{frame / FPS:.6f}",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-frames:v",
        "1",
        "-vf",
        f"crop={width}:{height}:0:{rows[0]}",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "yuv420p",
        "pipe:1",
    ]
    try:
        data = np.frombuffer(repository.run(command, timeout=600).stdout, dtype=np.uint8)
    except subprocess.CalledProcessError as error:
        said = error.stderr.decode(errors="replace")[:600]
        msg = f"Reading the band of frame {frame} failed: {said}"
        raise PictureError(msg) from error
    luma = width * height
    if data.size != luma * 3 // 2:
        msg = f"Reading the band of frame {frame} gave {data.size} of {luma * 3 // 2} samples"
        raise PictureError(msg)
    planes = (data[:luma], data[luma : luma * 5 // 4], data[luma * 5 // 4 :])
    return {name: int(np.median(plane)) for name, plane in zip(PLANES, planes, strict=True)}


def ground_check(stats: Path, frames: list[tuple[int, int]], ground: dict, fps: int = FPS) -> dict:
    """Read the band's measures and refuse a frame that departs from the ground.

    Every frame of the runs given must be measured, and the lowest and the highest sample of each
    plane must stand within `GROUND_TOLERANCE` levels of the ground. Returns the frames checked
    and the largest departure.
    """
    expected = [frame for a, b in frames for frame in range(a, b + 1)]
    blocks = sum(1 for line in stats.open(errors="replace") if line.startswith("frame:"))
    if blocks != len(expected):
        msg = f"The band was measured at {blocks} of its {len(expected)} frames"
        raise PictureError(msg)
    largest, worst = 0, None
    measured = departures(stats, ground, fps)
    for frame, (at, departure) in zip(expected, measured, strict=True):
        if at != frame:
            msg = f"The band's measure of frame {frame} is not readable"
            raise PictureError(msg)
        if departure > largest:
            largest, worst = departure, frame
    if largest > GROUND_TOLERANCE:
        msg = (
            f"The captioned picture's band is not the ground at frame {worst}, a frame without a "
            f"caption: a sample stands {largest} levels from the ground"
        )
        raise PictureError(msg)
    return {"frames": len(expected), "largest_departure": largest, "verdict": "pass"}
