"""Read the faces a film's stylesheet declares: the one reader for the audits and the renderer.

The composition names families; `picture/film.css` binds each to a font file by an `@font-face`
rule. The browser that paints the cover and the geometry check parses the stylesheet itself; the
canvas that draws the film (`filmkit.picture.renderer`) and the audits' text table
(`filmkit.picture.metrics`) are given the faces this module reads, so both take every family from
the same file. The reader takes the rules it can hold a canvas to and refuses the rest by name: a
rule it left out would be drawn in a font of the host, and no gate would see it.

A rule is read when it declares one family and one source, `url(<file>)` with or without a
`format(...)`, and beside them only `font-weight`, `font-style` or `font-display`. Those three
choose nothing where every family names one file, so two rules may not declare one family. A
source list, a `local(...)` source, a `unicode-range` or any other descriptor is refused: the
canvas registers one file under one family and follows none of them.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from filmkit.picture.errors import PictureError

COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
NAMED = re.compile(r"@font-face", re.IGNORECASE)
RULE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.IGNORECASE)
SOURCE = re.compile(
    r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)(?:\s*format\(\s*(['\"]?)[\w-]+\3\s*\))?", re.IGNORECASE
)
# Descriptors that choose nothing where each family names one file.
CARRIED = {"font-weight", "font-style", "font-display"}


def shown(rule: str) -> str:
    """A rule's text on one line, as a refusal names it."""
    return "@font-face{" + " ".join(rule.split()) + "}"


def rules(stylesheet: str) -> list[tuple[str, str]]:
    """Each face a stylesheet declares, in its order: the family and the source's path as
    written. A rule this reader does not hold a canvas to raises `PictureError`."""
    style = COMMENT.sub(" ", stylesheet)
    bodies = RULE.findall(style)
    if len(bodies) != len(NAMED.findall(style)):
        msg = "The stylesheet holds an @font-face rule that is not one block of declarations"
        raise PictureError(msg)
    faces: list[tuple[str, str]] = []
    for body in bodies:
        declared: dict[str, str] = {}
        for declaration in filter(None, (part.strip() for part in body.split(";"))):
            name, colon, value = declaration.partition(":")
            name = name.strip().lower()
            if not colon or name in declared:
                msg = f"The face rule {shown(body)} declares {name or 'nothing'} twice or badly"
                raise PictureError(msg)
            declared[name] = value.strip()
        other = sorted(set(declared) - CARRIED - {"font-family", "src"})
        source = SOURCE.fullmatch(declared.get("src", ""))
        family = declared.get("font-family", "").strip("'\" ")
        if other or not source or not family:
            why = (
                f"declares {', '.join(other)}, which the canvas does not follow"
                if other
                else "does not declare one family and one source, url(<file>)"
            )
            msg = f"The face rule {shown(body)} {why}"
            raise PictureError(msg)
        if family in {held for held, _ in faces}:
            msg = f"Two face rules declare the family {family}; the canvas takes one file a family"
            raise PictureError(msg)
        faces.append((family, source.group(2).strip()))
    return faces


def held(stylesheet: str, fonts: list[str]) -> list[dict]:
    """The faces of a stylesheet bound to a film's declared fonts: each family with the font it
    names, `font`, and that font's place in a stage, `path` (fonts/<file name>).

    Refused unless every rule names a declared font by fonts/<file name> and every declared
    font is named by a rule: a stage holds exactly the declared fonts, and each is drawn with.
    """
    declared = {f"fonts/{PurePosixPath(font).name}": font for font in fonts}
    faces = []
    for family, source in rules(stylesheet):
        if source not in declared:
            msg = (
                f"The face {family} names {source}, which is none of the film's declared fonts "
                f"({', '.join(declared) or 'none'})"
            )
            raise PictureError(msg)
        faces.append({"family": family, "path": source, "font": declared[source]})
    unnamed = sorted(set(declared) - {face["path"] for face in faces})
    if unnamed:
        msg = f"No face rule names the declared font {', '.join(unnamed)}"
        raise PictureError(msg)
    return faces
