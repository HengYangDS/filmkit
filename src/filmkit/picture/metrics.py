"""The advance widths of the faces a film's picture declares, for the headless audits.

The composition measures its names in the browser with the faces `picture/film.css` declares; the
headless audits lay it out on a canvas stand-in. This module reads each `@font-face` rule whose
source is one of the film's declared fonts and records the face's units per em and the advance of
every character its character map holds, in em. A face's most frequent advance is recorded once as
its default, and only the other advances are listed, so a full CJK font's ideographs cost one
entry. The table names the stylesheet's and the fonts' SHA-256; the stand-in reads it from the file
that `FILMKIT_TEXT_METRICS` names (headless-composition.mjs).
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path, PurePosixPath

from fontTools.ttLib import TTFont

import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import STYLE, face_bindings

# The variable that names the table to the headless audits.
VARIABLE = "FILMKIT_TEXT_METRICS"
# Where the engine writes the table, below the film's root.
TABLE = Path("build/runtime/work/picture-gates/text-metrics.json")

FACE_RULE = re.compile(r"@font-face\s*\{([^}]*)\}")
FAMILY = re.compile(r"font-family\s*:\s*(['\"]?)([^;'\"]+)\1")
SOURCE = re.compile(r"src\s*:\s*url\(\s*(['\"]?)([^'\")]+)\1\s*\)")


def declared_faces() -> dict[str, str]:
    """Each family the stylesheet declares from one of the film's fonts, with that font's path.

    A rule whose first source is not a declared font, by its file name below fonts/, is left out:
    its family keeps the stand-in's estimate.
    """
    fonts = {PurePosixPath(font).name: font for font in FILM.picture.fonts}
    style = (repository.ROOT / STYLE).read_text(encoding="utf-8")
    faces = {}
    for rule in FACE_RULE.findall(style):
        family, source = FAMILY.search(rule), SOURCE.search(rule)
        if family and source and PurePosixPath(source.group(2)).name in fonts:
            faces[family.group(2).strip()] = fonts[PurePosixPath(source.group(2)).name]
    return faces


def face_advances(path: Path) -> dict:
    """A font's units per em, its most frequent advance and every other advance, in em."""
    with TTFont(path, lazy=True) as font:
        em = font["head"].unitsPerEm
        hmtx = font["hmtx"]
        advances = {chr(code): hmtx[name][0] / em for code, name in font.getBestCmap().items()}
    default = Counter(advances.values()).most_common(1)[0][0] if advances else 0
    return {
        "units_per_em": em,
        "default": default,
        "advances": {char: value for char, value in sorted(advances.items()) if value != default},
        "mapped": "".join(sorted(advances)),
    }


def text_metrics() -> dict:
    """The table of the film's declared faces, with the digests of what it was read from."""
    return {
        **face_bindings(),
        "faces": {
            family: {"font": font, **face_advances(repository.ROOT / font)}
            for family, font in sorted(declared_faces().items())
        },
    }


def current_table() -> Path:
    """The table's file for the film's current stylesheet and fonts, written when it is missing
    or stale."""
    path = repository.ROOT / TABLE
    if path.is_file():
        recorded = repository.read(path)
        if {
            key: recorded.get(key) for key in ("stylesheet_sha256", "fonts_sha256")
        } == face_bindings():
            return path
    path.parent.mkdir(parents=True, exist_ok=True)
    repository.write(path, text_metrics())
    return path
