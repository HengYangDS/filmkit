"""The delivery format of both editions: rates, levels, limits, tags and the credits' length that
the film's declaration states; each edition's runtime is its own timeline's
(`filmkit.production.Edition.runtime`)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import filmkit.film as film
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Callable


def declared(key: str, read: Callable[[Any], Any]) -> Any:
    """The value that both editions' scripts declare alike for a key, as `read` takes it."""
    scripts = [json.loads((repository.ROOT / Edition(code).script).read_text()) for code in CODES]
    values = {read(script[key]) for script in scripts}
    if len(values) != 1:
        message = f"The editions' scripts declare different {key} values: {sorted(values)}"
        raise ValueError(message)
    return values.pop()


RATE = 48000
# The frame rate the engine renders and encodes (`filmkit.film.FPS`); the H.264 levels below are set
# for it.
FPS: int = film.FPS
# The credits' length, which the film's declaration states once for both editions.
CREDITS_DURATION: int = FILM.credits_duration
# The films' author, artist and copyright holder, which the film's declaration states once.
AUTHOR: str = FILM.author
# The films' chapter count; each edition titles the chapters in its own language.
CHAPTERS: int = declared("chapters", len)
# Both editions play at one spoken-word level; a single gain reaches it without dynamics
# processing, and the true-peak ceiling caps that gain.
PROGRAM_LEVEL = {"integrated_lufs": -16.5, "true_peak_ceiling_dbtp": -1.0}
# The picture's chapter card is fully shown 0.15 s after its scene starts and holds
# until the voice begins, so a chapter marker lands on the card, past the previous
# running head.
CHAPTER_CARD_SHOWN = 0.25
# H.264 level_idc by picture height for 60 fps delivery.
H264_LEVELS = {2160: 52, 1080: 42}
