"""The picture's fonts map every character the film draws with them.

The composition sets any text with a Chinese character in the Noto Sans CJK SC subsets, which hold
only the characters this film draws, and Latin-only text in the unmodified IBM Plex Sans.
"""

from collections.abc import Iterator

import pytest
from fontTools.ttLib import TTFont

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.captions.timing import typeset
from filmkit.film import FILM
from filmkit.production import CODES, Edition


def strings(value: object) -> Iterator[str]:
    """Every string in a parsed JSON value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def written(code: str) -> set[str]:
    """Every character of an edition's script as the picture sets it, without line breaks."""
    texts = strings(repository.read(Edition(code).script))
    return {char for text in texts for char in typeset(text)} - {"\n", "\t"}


def mapped(font: str) -> set[str]:
    """The characters a declared font maps to a glyph."""
    with TTFont(repository.ROOT / font, lazy=True) as face:
        return {chr(code) for code in face.getBestCmap()}


def declared(family: str) -> list[str]:
    """The declared picture fonts whose file names begin with a family's name."""
    fonts = [font for font in FILM.picture.fonts if font.rsplit("/", 1)[-1].startswith(family)]
    assert fonts, family
    return fonts


@pytest.mark.parametrize("font", declared("noto-sans-cjk-sc-subset"))
def test_each_chinese_subset_maps_every_character_of_the_scripts_and_the_composition(font):
    composition = repository.ROOT / picture_rendering.COMPOSITION_SCRIPT
    drawn = set(composition.read_text()).union(*(written(code) for code in CODES)) - {"\n"}
    assert sorted(drawn - mapped(font)) == []


@pytest.mark.parametrize("font", declared("ibm-plex-sans"))
def test_each_latin_font_maps_every_character_of_the_english_script(font):
    assert sorted(written("en") - mapped(font)) == []
