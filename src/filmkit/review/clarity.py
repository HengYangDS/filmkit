"""Voice clarity: the cepstral peak prominence of a soundtrack and of each segment's voice.

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

A segment's clarity takes the same steps on its voice alone, from its first word's start to its
last word's end in the timeline. A film may declare a floor for each edition in its declaration
(`review.clarity_minimum_db`); the measurement records each value, rounded to 0.01 dB, against
it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import numpy as np

import filmkit.repository as repository
from filmkit.film import FILM

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
METHOD = (
    "FFmpeg decode to 16 kHz mono 32-bit float; 1024-sample frames every 256 samples; frame "
    "energy 10*log10 of the sum of squared samples; frames within 18 dB of the 95th percentile "
    "of those energies kept; periodic Hann window; power spectrum 10*log10|X|^2; real cepstrum "
    "the inverse real FFT of that spectrum; level 20*log10|c| over quefrency bins 40-266 "
    "inclusive; least-squares line over those bins; prominence the level at the highest bin "
    "minus the line at that bin; median over the kept frames"
)


class Clarity(NamedTuple):
    """A signal's median cepstral peak prominence in dB, or None without a frame, and its frames."""

    median_db: float | None
    frames: int


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


def prominence(samples: np.ndarray) -> Clarity:
    """The median cepstral peak prominence of 16 kHz samples over their loud frames."""
    samples = np.asarray(samples, dtype=np.float64)
    if len(samples) < FRAME:
        return Clarity(None, 0)
    frames = np.lib.stride_tricks.sliding_window_view(samples, FRAME)[::HOP]
    energy = np.concatenate(
        [
            10 * np.log10(np.sum(frames[at : at + CHUNK] ** 2, axis=1) + FLOOR)
            for at in range(0, len(frames), CHUNK)
        ]
    )
    kept = np.flatnonzero(energy >= np.percentile(energy, KEPT_PERCENTILE) - KEPT_WITHIN_DB)
    values = np.concatenate(
        [frame_prominences(frames[kept[at : at + CHUNK]]) for at in range(0, len(kept), CHUNK)]
    )
    return Clarity(float(np.median(values)), len(kept))


def judged(clarity: Clarity, floor: float | None) -> dict:
    """A clarity rounded to 0.01 dB, its frames and whether it stands below the floor."""
    value = None if clarity.median_db is None else round(clarity.median_db, 2)
    below = None if floor is None or value is None else value < floor
    return {"cpp_db": value, "frames": clarity.frames, "below_floor": below}


def voice_clarity(code: str, soundtrack: Path, timeline: dict) -> dict:
    """An edition's clarity over its soundtrack and each segment's voice, against its floor."""
    floors = FILM.review.clarity_minimum_db or {}
    floor = floors.get(code)
    samples = decode(soundtrack)
    segments = []
    for segment in timeline["segments"]:
        words = segment["words"]
        start, end = (round(seconds * RATE) for seconds in (words[0]["start"], words[-1]["end"]))
        segments.append({"id": segment["id"], **judged(prominence(samples[start:end]), floor)})
    return {
        "method": METHOD,
        "floor_db": floor,
        "soundtrack": judged(prominence(samples), floor),
        "segments": segments,
        "segments_below_floor": [row["id"] for row in segments if row["below_floor"]],
    }


def summary(clarity: dict) -> dict:
    """The soundtrack's clarity against its floor and the segments below it, as printed."""
    return {
        **clarity["soundtrack"],
        "floor_db": clarity["floor_db"],
        "segments_below_floor": clarity["segments_below_floor"],
    }
