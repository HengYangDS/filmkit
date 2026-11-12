"""Read a delivered film's keywords and authors back as Spotlight imports them.

Spotlight's importer, not the film, decides what a viewer finds. `mdimport -t -d2` test-imports a
file, storing nothing in the Spotlight index, and prints what it imported as an old-style property
list whose quoted strings escape each UTF-16 unit beyond ASCII as `\\Uxxxx` (`imported`, `parse`).
The QuickTime importer of macOS 27.2.1 splits the keywords value by its dominant script, as a test
on 2026-11-12 found: a mostly Chinese value only at its commas, keeping a space after a comma at
the start of the next keyword, and a mostly Latin value at its commas and at every space, so an
English phrase imports as its words. Packaging therefore joins the keywords with commas alone.

A film fails the readback with an imported keyword that has a space at either end, or with a
declared keyword holding a Han character that no imported keyword holds whole (`keyword_problems`).
A declared keyword without one that does not import whole was split into its words, which is the
importer's behaviour; the readback records it (`split_into_words`). A film also fails with any
authors but the declared author, once (`author_problems`): Spotlight lists the author of every
author-bearing QuickTime key, so a film whose Artist key also carried the author imported it twice,
and Finder showed it with "(2)". A host without `mdimport` has no readback.
"""

from __future__ import annotations

import re
import shutil
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.narration.pronunciation import HAN

if TYPE_CHECKING:
    from pathlib import Path

# The importer's attributes the readback reads, by the name it records them under.
ATTRIBUTES = {"keywords": "kMDItemKeywords", "authors": "kMDItemAuthors"}
# An array of the report by its attribute, and each of its strings, quoted or bare.
ARRAY = re.compile(r"^ *(\w+) = +\((.*?)\n *\);$", re.MULTILINE | re.DOTALL)
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"|([^\s",]+)')
# A quoted string's escapes: a UTF-16 unit in hexadecimal, or one of C's escapes.
ESCAPE = re.compile(r"\\(U[0-9A-Fa-f]{4}|.)", re.DOTALL)
C_ESCAPES = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v"}


def unescaped(text: str) -> str:
    """A quoted string's text, its escapes decoded and its UTF-16 surrogate pairs joined."""

    def character(match: re.Match[str]) -> str:
        code = match[1]
        return chr(int(code[1:], 16)) if code[0] == "U" else C_ESCAPES.get(code, code)

    units = ESCAPE.sub(character, text).encode("utf-16-le", "surrogatepass")
    return units.decode("utf-16-le", "surrogatepass")


def parse(report: str) -> dict[str, list[str]]:
    """The keywords and authors of an `mdimport -t -d2` report, none where it lists none."""
    arrays = {match[1]: match[2] for match in ARRAY.finditer(report)}
    return {
        name: [bare or unescaped(quoted) for quoted, bare in STRING.findall(arrays.get(key, ""))]
        for name, key in ATTRIBUTES.items()
    }


def imported(path: Path) -> dict[str, list[str]] | None:
    """The keywords and authors Spotlight imports from a file, or None where the host has no
    `mdimport`."""
    tool = shutil.which("mdimport")
    if tool is None:
        return None
    report = repository.run([tool, "-t", "-d2", str(path)])
    return parse(report.stdout.decode("utf-8"))


def keyword_problems(declared: list[str], keywords: list[str]) -> list[str]:
    """Why a film's imported keywords fail: one with a space at either end, or a declared keyword
    holding a Han character that no imported keyword holds whole."""
    whole = {keyword.strip() for keyword in keywords}
    return [
        *(f'"{k}" imports with a space at an end' for k in keywords if k != k.strip()),
        *(f'"{k}" does not import whole' for k in declared if re.search(HAN, k) and k not in whole),
    ]


def split_into_words(declared: list[str], keywords: list[str]) -> list[str]:
    """The declared keywords without a Han character that no imported keyword holds whole: the
    phrases the importer split into their words."""
    whole = {keyword.strip() for keyword in keywords}
    return [k for k in declared if not re.search(HAN, k) and k not in whole]


def author_problems(author: str, authors: list[str]) -> list[str]:
    """Why a film's imported authors fail: they are not the declared author, once. The problem
    names every author entry read."""
    if authors == [author]:
        return []
    read = ", ".join(f'"{entry}"' for entry in authors) or "none"
    return [f'the authors read are {read}, not "{author}" alone']
