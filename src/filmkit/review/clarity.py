"""Voice clarity: the cepstral peak prominence of a soundtrack, its segments and its thoughts.

A breathy or hoarse voice spreads noise between its harmonics, which flattens the peak that its
pitch period raises in the cepstrum. The measure is the one the reviewers state, step by step:

1. FFmpeg decodes the soundtrack to 16 kHz mono 32-bit float.
2. It is cut into 1024-sample frames every 256 samples.
3. Each frame's energy is 10·log10 of the sum of its squared samples, and the frames within
   18 dB of the 95th percentile of those energies are kept, so pauses and breaths do not count.
4. Each kept frame, under a periodic Hann window, gives its power spectrum in dB, 10·log10|X|².
5. Its real cepstrum is the inverse real FFT of that spectrum, and over quefrency bins 40 to 266
   inclusive, pitch periods of 2.5 to 16.6 ms, the cepstrum's level is 20·log10|c|.
6. A least-squares straight line is fitted to that level over those bins; the frame's prominence
   is the level at the bin where it is highest minus the line's value at that bin.
7. The clarity is the median prominence over the kept frames.

The soundtrack has one threshold, step 3 applied once to every frame, and one frame grid, which
starts at its first sample. A frame's centre is its start plus 512 samples, and a segment's
clarity is the median over the kept frames whose centres lie from the segment's start to before
its end in the timeline, as the reviewers assign them, so every kept frame of the narration
belongs to one segment.

A thought, from its first aligned word's start to before its last one's end, keeps few frames,
and its median moves with where the grid falls. It is therefore measured on 16 grids, which
start 0, 16, ..., 240 samples into the soundtrack, each against the soundtrack's threshold, and
judged by the median of those 16 medians. Its record also states its value on the soundtrack's
own grid, the lowest and highest of the 16, its kept frames on the soundtrack's grid, and
whether they are fewer than 150, about 2.4 s of voice, which marks it short: a reader then
knows how far its value scatters.

A film may declare a floor for each edition in its declaration (`review.clarity_minimum_db`);
the measurement records each value, rounded to 0.01 dB, against it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import numpy as np

import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.review.support import thought_spans

if TYPE_CHECKING:
    from pathlib import Path

RATE = 16000
FRAME = 1024
HOP = 256
# The frames kept: within this many dB of this percentile of every frame's energy.
KEPT_WITHIN_DB = 18
KEPT_PERCENTILE = 95
# The quefrency bins searched for the pitch period's peak, both inclusive.
QUEFRENCIES = (40, 266)
# Added inside each logarithm, so a frame of digital silence keeps a finite level.
FLOOR = 1e-20
# Frames measured at once, which bounds the memory a long soundtrack needs.
CHUNK = 4096
# The grids a thought is measured on: each starts this many samples into the soundtrack.
PHASES = tuple(range(0, HOP, 16))
# A thought with fewer kept frames than this on the soundtrack's grid is marked short.
SHORT_FRAMES = 150
METHOD = (
    "FFmpeg decode to 16 kHz mono 32-bit float; 1024-sample frames every 256 samples; frame "
    "energy 10*log10 of the sum of squared samples; frames within 18 dB of the 95th percentile "
    "of those energies kept; periodic Hann window; power spectrum 10*log10|X|^2; real cepstrum "
    "the inverse real FFT of that spectrum; level 20*log10|c| over quefrency bins 40-266 "
    "inclusive; least-squares line over those bins; prominence the level at the highest bin "
    "minus the line at that bin; median over the kept frames; one threshold and one grid, "
    "from sample 0, for the whole soundtrack; a frame's centre is its start plus 512 samples; a "
    "segment's frames are the kept frames whose centres lie in [segment start, segment end) of "
    "the timeline; a thought's value is the median, over the 16 grids that start 0, 16, ..., "
    "240 samples in, of the medians over the frames at or above the soundtrack's threshold "
    "whose centres lie in [first word start, last word end), with its value on the "
    "soundtrack's grid, the lowest and highest of the 16 and its kept frames on the "
    "soundtrack's grid, fewer than 150 of which mark it short"
)


class Clarity(NamedTuple):
    """A signal's median cepstral peak prominence in dB, or None without a frame, and its frames."""

    median_db: float | None
    frames: int


class Frames(NamedTuple):
    """The kept frames of one grid: each one's centre in seconds and its prominence in dB."""

    centres: np.ndarray
    prominences: np.ndarray


def decode(path: Path) -> np.ndarray:
    """A soundtrack's samples as FFmpeg resamples it to 16 kHz mono 32-bit float."""
    command = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path)]
    command += ["-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"]
    return np.frombuffer(repository.run(command, timeout=600).stdout, dtype="<f4")


def frame_prominences(frames: np.ndarray) -> np.ndarray:
    """Each windowed frame's cepstral peak prominence in dB, by steps 4 to 6."""
    window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(FRAME) / FRAME)
    spectrum = 10 * np.log10(np.abs(np.fft.rfft(frames * window, axis=1)) ** 2 + FLOOR)
    cepstrum = np.fft.irfft(spectrum, n=FRAME, axis=1)
    low, high = QUEFRENCIES
    level = 20 * np.log10(np.abs(cepstrum[:, low : high + 1]) + FLOOR)
    bins = np.arange(low, high + 1, dtype=np.float64)
    centred = bins - bins.mean()
    slope = (level - level.mean(axis=1, keepdims=True)) @ centred / (centred @ centred)
    peak = np.argmax(level, axis=1)
    line = level.mean(axis=1) + slope * centred[peak]
    return level[np.arange(len(level)), peak] - line


def grid(samples: np.ndarray, phase: int = 0) -> np.ndarray:
    """The frames of the grid that starts `phase` samples in, as a view of the samples."""
    if len(samples) - phase < FRAME:
        return np.empty((0, FRAME))
    return np.lib.stride_tricks.sliding_window_view(samples[phase:], FRAME)[::HOP]


def energies(frames: np.ndarray) -> np.ndarray:
    """Each frame's energy in dB, by step 3."""
    chunks = [
        10 * np.log10(np.sum(frames[at : at + CHUNK] ** 2, axis=1) + FLOOR)
        for at in range(0, len(frames), CHUNK)
    ]
    return np.concatenate(chunks) if chunks else np.empty(0)


def threshold(samples: np.ndarray) -> float:
    """The energy in dB a kept frame reaches, by step 3 over every frame of the samples' grid."""
    energy = energies(grid(samples))
    if not len(energy):
        return float("inf")
    return float(np.percentile(energy, KEPT_PERCENTILE)) - KEPT_WITHIN_DB


def kept_frames(samples: np.ndarray, level: float, phase: int = 0) -> Frames:
    """The frames at or above an energy level on the grid that starts `phase` samples in."""
    frames = grid(samples, phase)
    kept = np.flatnonzero(energies(frames) >= level)
    chunks = [frame_prominences(frames[kept[at : at + CHUNK]]) for at in range(0, len(kept), CHUNK)]
    centres = (phase + kept * HOP + FRAME / 2) / RATE
    return Frames(centres, np.concatenate(chunks) if chunks else np.empty(0))


def within(frames: Frames, start: float = -np.inf, end: float = np.inf) -> Clarity:
    """The clarity over the kept frames whose centres lie in [start, end) seconds."""
    values = frames.prominences[(frames.centres >= start) & (frames.centres < end)]
    return Clarity(float(np.median(values)) if len(values) else None, len(values))


def prominence(samples: np.ndarray) -> Clarity:
    """The median cepstral peak prominence of 16 kHz samples over their loud frames."""
    samples = np.asarray(samples, dtype=np.float64)
    return within(kept_frames(samples, threshold(samples)))


def judged(clarity: Clarity, floor: float | None) -> dict:
    """A clarity rounded to 0.01 dB, its frames and whether it stands below the floor."""
    value = None if clarity.median_db is None else round(clarity.median_db, 2)
    below = None if floor is None or value is None else value < floor
    return {"cpp_db": value, "frames": clarity.frames, "below_floor": below}


def phased(phases: list[Clarity], floor: float | None) -> dict:
    """A thought's record from its clarity on each grid, the soundtrack's own first.

    Its value is the median of the grids' medians, judged against the floor; beside it stand
    its value and kept frames on the soundtrack's grid, the lowest and highest grid, and
    whether those frames are too few to hold its value still.
    """
    values = [clarity.median_db for clarity in phases if clarity.median_db is not None]
    median = float(np.median(values)) if values else None
    own = phases[0]
    return {
        **judged(Clarity(median, own.frames), floor),
        "grid_db": None if own.median_db is None else round(own.median_db, 2),
        "lowest_db": round(min(values), 2) if values else None,
        "highest_db": round(max(values), 2) if values else None,
        "short": own.frames < SHORT_FRAMES,
    }


def thought_rows(grids: list[Frames], timeline: dict, floor: float | None) -> list[dict]:
    """Every thought's record, named `segment.thought`, from the kept frames of each grid."""
    return [
        {
            "id": f"{segment['id']}.{number}",
            **phased([within(frames, start, end) for frames in grids], floor),
        }
        for segment in timeline["segments"]
        for number, (start, end) in enumerate(thought_spans(segment), 1)
    ]


def report(samples: np.ndarray, timeline: dict, floor: float | None) -> dict:
    """The clarity of 16 kHz samples, of each segment and of each thought, against a floor."""
    samples = np.asarray(samples, dtype=np.float64)
    level = threshold(samples)
    grids = [kept_frames(samples, level, phase) for phase in PHASES]
    segments = [
        {"id": segment["id"], **judged(within(grids[0], segment["start"], segment["end"]), floor)}
        for segment in timeline["segments"]
    ]
    thoughts = thought_rows(grids, timeline, floor)
    return {
        "soundtrack": judged(within(grids[0]), floor),
        "segments": segments,
        "segments_below_floor": [row["id"] for row in segments if row["below_floor"]],
        "thoughts": thoughts,
        "thoughts_below_floor": [row["id"] for row in thoughts if row["below_floor"]],
        "short_thoughts": [row["id"] for row in thoughts if row["short"]],
    }


def voice_clarity(code: str, soundtrack: Path, timeline: dict) -> dict:
    """An edition's clarity over its soundtrack, segments and thoughts, against its floor."""
    floor = (FILM.review.clarity_minimum_db or {}).get(code)
    return {"method": METHOD, "floor_db": floor, **report(decode(soundtrack), timeline, floor)}


def summary(clarity: dict) -> dict:
    """The soundtrack's clarity against its floor and what stands below it, as printed."""
    return {
        **clarity["soundtrack"],
        "floor_db": clarity["floor_db"],
        "segments_below_floor": clarity["segments_below_floor"],
        "thoughts_below_floor": clarity["thoughts_below_floor"],
    }
