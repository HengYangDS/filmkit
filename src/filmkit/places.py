"""Where an edition's files stand, each derived from its code and the film's file prefix (design
decision 1 of treat-languages-as-equals): the one place rule, which loads nothing, so that the
declaration's model (`filmkit.film`), its loader's refusals (`filmkit.declared_sources`) and the
table of withdrawn keys (`filmkit.withdrawn`) each read it."""

from __future__ import annotations

from typing import NamedTuple

# The files every edition's folder holds: its script and its cast.
SCRIPT, CAST = "film-script.json", "voice-reference.json"
# The recording every edition's reference derives from, one for the film.
IDENTITY = "assets/audio/narrator-identity.wav"


class Places(NamedTuple):
    """Where an edition's files stand: its folder below `content/`, its script, cast,
    pronunciation and readings there, its reference recording below `assets/audio/` and its cover
    below `assets/cover/`."""

    folder: str
    script: str
    cast: str
    pronunciation: str
    readings: str
    reference: str
    cover: str


def places(code: str, slug: str) -> Places:
    """An edition's places, from its code and the film's file prefix."""
    folder = f"content/{code}"
    return Places(
        folder,
        f"{folder}/{SCRIPT}",
        f"{folder}/{CAST}",
        f"{folder}/pronunciation.json",
        f"{folder}/readings.json",
        f"assets/audio/{code}/narration-reference.wav",
        f"assets/cover/{slug}-cover-{code}.png",
    )
