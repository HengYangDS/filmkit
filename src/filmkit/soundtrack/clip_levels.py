"""The level gains of an edition's clips: segments within their chapter, chapters within the film.

A clip is one segment's shaped recording with the loudness of its leveled thoughts. Its
segment gain brings it within the declared tolerance of its chapter's median thought, and its
chapter's gain brings the chapter within the declared tolerance of the film's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from filmkit.soundtrack.level import chapter_level_gains, segment_level_gains

if TYPE_CHECKING:
    from filmkit.soundtrack.assembly import Clip


def _peak(clip: Clip) -> float:
    """A clip's peak as a fraction of full scale."""
    return float(np.abs(clip.samples.astype(np.int32)).max(initial=0)) / 32768


def leveled_thoughts(clip: Clip) -> list[float]:
    """The loudness of a clip's measured thoughts as the clip now holds them."""
    return [
        level["loudness_lufs"] + level["gain_db"] + clip.level_gain_db + clip.segment_gain_db
        for level in clip.thought_levels
        if level["loudness_lufs"] is not None
    ]


def segment_gains(clips: list[Clip], tolerance_db: float | None) -> dict[str, float]:
    """The static gain of each segment, from its leveled thoughts, its chapter's and its peak.

    Each segment's leveled thoughts are brought within the declared tolerance of its
    chapter's median thought by one static gain, so two neighbouring segments of a chapter
    stand no farther apart than their thoughts and this tolerance allow.
    """
    return segment_level_gains(
        {clip.segment["id"]: leveled_thoughts(clip) for clip in clips},
        {clip.segment["id"]: clip.segment["chapter"] for clip in clips},
        {clip.segment["id"]: _peak(clip) for clip in clips},
        tolerance_db,
    )


def chapter_gains(clips: list[Clip], tolerance_db: float | None) -> dict[str, float]:
    """The static gain of each chapter, from its leveled thoughts and its peak.

    Each chapter's leveled thoughts are brought within the declared tolerance of the
    film's median thought by one static gain, so no chapter, the coda included, stands
    louder or softer than the film.
    """
    levels: dict[str, list[float]] = {}
    peaks: dict[str, float] = {}
    for clip in clips:
        chapter = clip.segment["chapter"]
        levels.setdefault(chapter, []).extend(leveled_thoughts(clip))
        peaks[chapter] = max(peaks.get(chapter, 0.0), _peak(clip))
    return chapter_level_gains(levels, peaks, tolerance_db)
