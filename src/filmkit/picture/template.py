"""The picture template a film provides and what staging replaces in it.

Staging derives a picture's document from `picture/index.html` by replacing each anchor below,
which the template holds exactly as often as stated, and by inlining the film's one stylesheet
and one script (`filmkit.picture.rendering`). This module reads no declaration, so a template
can be asked before its film's declaration loads (`filmkit.check`).
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

# The template, and the stylesheet and the script staging inlines, as the template names them.
TEMPLATE = "picture/index.html"
STYLESHEET = "film.css"
SCRIPT = "film.js"
# The two tags staging replaces by the stylesheet and the script themselves.
INLINED = (f'<link rel="stylesheet" href="{STYLESHEET}">', f'<script src="{SCRIPT}"></script>')
# The root staging gives each edition's language tag: the template's root names no language.
LANGUAGE = '<html lang="und">'
# A root that names a language, as a template written for one edition opens.
ROOT = re.compile(r'<html lang="[^"]+">')
# Each text staging replaces, in the order it replaces them, and how often the template holds it.
ANCHORS: tuple[tuple[str, int], ...] = (
    (LANGUAGE, 1),
    ('data-duration="1200"', 1),
    ('data-width="1920"', 1),
    ('data-height="1080"', 1),
    ('content="width=1920, height=1080"', 1),
    ('width="1920" height="1080"', 1),
    ('<div id="film"', 1),
    ("/* FILM_DATA */", 1),
    (INLINED[0], 1),
    (INLINED[1], 1),
)


class Sources(HTMLParser):
    """The scripts and stylesheets a document names, as a browser reads its tags: a `script`
    with a `src`, and a `link` with an `href` whose `rel` names a stylesheet among its words.
    A comment names none."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.named: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        held = {name: value for name, value in attrs if value}
        if tag == "script" and "src" in held:
            self.named.append(held["src"])
        elif (
            tag == "link" and "href" in held and "stylesheet" in held.get("rel", "").lower().split()
        ):
            self.named.append(held["href"])

    handle_startendtag = handle_starttag


def sources(html: str) -> list[str]:
    """Each script and stylesheet a template names, in its order."""
    reader = Sources()
    reader.feed(html)
    reader.close()
    return reader.named


def problems(html: str) -> list[str]:
    """Every anchor a template does not hold as often as staging replaces it, each counted where
    staging would count it, a root that names one language's tag named with the anchor to write
    instead, and every script or stylesheet it names beside the two tags staging replaces: a
    second naming of the inlined stylesheet or script is one of them."""
    found, left = [], html
    for old, count in ANCHORS:
        held = left.count(old)
        named = ROOT.search(left) if old == LANGUAGE and not held else None
        if named:
            found.append(
                f"The picture template opens with {named[0]}, one language's tag; staging gives "
                f"each edition its own, in place of {LANGUAGE}, which the template holds once"
            )
        elif held != count:
            found.append(f"The picture template holds {old!r} {held} times, not {count}")
        left = left.replace(old, "")
    rest = html.replace(INLINED[0], "").replace(INLINED[1], "")
    other = sorted(set(sources(rest)))
    if other:
        found.append(
            f"The picture template loads {', '.join(other)}; staging inlines {STYLESHEET} and "
            f"{SCRIPT} and no other source"
        )
    return found
