"""What the texts of every frame show, from the text trace that frame-audit.mjs writes.

The frame audit, given TEXTS=<file>, writes one row for each text of each frame it exercises,
whatever the text's role and whether or not a scene draws it: the time, the scene, the role, the
text's WCAG contrast against the film's ground with its opacity composited over the ground, the
opacity and the text, a placed name whole. Two measures read it:

- The opening title. Before the first word, at least one frame must show every word of the title
  the edition's script declares, in texts at reading contrast (3:1, as the sync audit reads a
  label). Words are compared as the sync audit compares a cue with its labels: each CJK character,
  or a run of other letters and digits with its apostrophes, lowercased; a text covers the title
  words it repeats as one run, so a title set on several lines or in parts, with " · " or a colon
  between them, is shown when its lines together repeat every word.
- The contrast of text at rest. A text that holds a letter or a digit and shows above 4% opacity,
  keyed by its scene, its role and its whole text, stands below 4.5:1 in a frame when any of its
  instances does. A run of such frames shorter than 0.7 s is a text entering or leaving the
  picture; a run of 0.7 s or more is a text at rest below 4.5:1.

`filmkit.picture.gates` refuses a picture that shows no title before its first word or that holds
a text at rest below 4.5:1.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, NamedTuple

from filmkit.picture.sync_audit import LEGIBLE_CONTRAST, repeated, words

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

# A text at rest stands at least at this contrast against the ground.
RESTING_CONTRAST = 4.5
# A text below that contrast for less than this many seconds is entering or leaving the picture.
FADE_SECONDS = 0.7
# A text shows when its opacity is above this, as the frame audit counts any paint above 4% as ink.
SHOWN_OPACITY = 0.04


class Text(NamedTuple):
    """One text of one sampled frame, as the text trace records it."""

    t: float
    scene: str
    role: str
    contrast: float
    alpha: float
    text: str


def trace_texts(lines: Iterable[str]) -> Iterator[Text]:
    """Each row of a text trace; a line with fewer than its six fields, such as a partial last
    line, is skipped."""
    for line in lines:
        parts = line.rstrip("\n").split("\t", 5)
        if len(parts) == 6:
            t, scene, role, contrast, alpha, text = parts
            yield Text(float(t), scene, role, float(contrast), float(alpha), text)


def first_word(timeline: dict) -> float:
    """When the first word is spoken: where the opening quiet ends."""
    return min(
        (word["start"] for segment in timeline["segments"] for word in segment["words"]),
        default=timeline.get("duration", 0),
    )


def opening_title(timeline: dict, texts: list[Text], step: float) -> dict:
    """Whether the frames before the first word show the declared title, and for how long.

    Reports the title, when its quiet ends, the seconds of frames that show every title word,
    from when to when they stand, and the title words no frame before the first word shows.
    """
    title, ends = timeline.get("title", ""), first_word(timeline)
    said = words(title)
    covered: dict[float, set[int]] = {}
    for row in texts:
        if row.t < ends and row.contrast >= LEGIBLE_CONTRAST:
            covered.setdefault(row.t, set()).update(repeated(said, words(row.text)))
    whole = sorted(t for t, places in covered.items() if said and len(places) == len(said))
    seen = set().union(*covered.values()) if covered else set()
    return {
        "title": title,
        "first_word": round(ends, 3),
        "shown_seconds": round(len(whole) * step, 2),
        "shown_from": whole[0] if whole else None,
        "shown_to": round(whole[-1] + step, 2) if whole else None,
        "missing_words": [word for index, word in enumerate(said) if index not in seen],
    }


def frame_index(t: float, step: float) -> int:
    return round(t / step)


def low_contrast(texts: list[Text], step: float) -> list[dict]:
    """The runs of 0.7 s or more in which a shown text stands below 4.5:1, longest first."""
    below: dict[tuple[str, str, str], dict[int, float]] = {}
    for row in texts:
        readable = any(ch.isalnum() for ch in row.text)
        if readable and row.alpha > SHOWN_OPACITY and row.contrast < RESTING_CONTRAST:
            frames = below.setdefault((row.scene, row.role, row.text), {})
            index = frame_index(row.t, step)
            frames[index] = min(frames.get(index, math.inf), row.contrast)
    runs = []
    for (scene, role, text), frames in below.items():
        order = sorted(frames)
        start = previous = order[0]
        for index in [*order[1:], None]:
            if index is not None and index == previous + 1:
                previous = index
                continue
            seconds = (previous - start + 1) * step
            if seconds >= FADE_SECONDS - 1e-6:
                runs.append(
                    {
                        "scene": scene,
                        "role": role,
                        "text": text,
                        "from": round(start * step, 2),
                        "to": round((previous + 1) * step, 2),
                        "seconds": round(seconds, 2),
                        "lowest": min(frames[k] for k in range(start, previous + 1)),
                    }
                )
            if index is not None:
                start = previous = index
    return sorted(runs, key=lambda run: (-run["seconds"], run["from"], run["text"]))


def report(timeline: dict, lines: Iterable[str], step: float) -> dict:
    """Both measures of a text trace sampled every `step` seconds."""
    texts = list(trace_texts(lines))
    return {
        "opening_title": opening_title(timeline, texts, step),
        "resting_contrast": RESTING_CONTRAST,
        "fade_seconds": FADE_SECONDS,
        "low_contrast": low_contrast(texts, step),
    }
