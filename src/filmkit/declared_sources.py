"""What the loader reads of the sources a film's declaration names, beside the declaration itself.

`filmkit.film.read` asks these as the declaration loads, so each is refused beside the
declaration's other problems, before any work, each in one line that says what to write instead.
The review prompt may cite no field the engine no longer fills, `{other}` or `{other_language}`,
and may name no edition's files by their path or the declared codes grouped in braces, which
`{editions}` and `{others}` state for every edition (`filmkit.review.prompts`).
"""

from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# The prompt's fields the engine fills no longer, and the field that replaces each.
WITHDRAWN_FIELDS = {"other": "{others}", "other_language": "{others}"}


def _fields(line: str) -> set[str]:
    """The fields a line of a str.format template cites; none for a line that is no template."""
    try:
        return {name for _, name, _, _ in string.Formatter().parse(line) if name}
    except ValueError:
        return set()


def prompt_problems(root: Path, declared: dict) -> list[str]:
    """Each line of the review prompt that cites a withdrawn field, names an edition's files by
    their path or groups the declared codes in braces, with its number and the field to use.

    It reads the declaration as declared, so that its other problems hide none of these; a prompt
    that is not named, cannot be read or is no text is the declaration's other problems' to name.
    """
    review, editions = declared.get("review"), declared.get("editions")
    prompt = review.get("prompt") if isinstance(review, dict) else None
    if not isinstance(prompt, str) or not isinstance(editions, dict) or not editions:
        return []
    try:
        text = (root / prompt).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    codes = "|".join(re.escape(code) for code in editions)
    places = [f"build/artifacts/film/{code}/" for code in editions]
    places += [f"build/evidence/editions/{code}/" for code in editions]
    places += [f"content/{code}/" for code in editions]
    places += [
        f"{table['sources']}/{name}"
        for table in editions.values()
        if isinstance(table, dict) and isinstance(table.get("sources"), str)
        for name in ("film-script.json", "voice-reference.json")
    ]
    grouped = re.compile(rf"\{{\{{?\s*(?:{codes})(?:\s*,\s*(?:{codes}))+\s*\}}\}}?")
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        where = f"{prompt}:{number}"
        found += [
            f"{where} cites {{{field}}}, which the engine no longer fills; name the other editions"
            f" by {WITHDRAWN_FIELDS[field]}"
            for field in sorted(_fields(line) & set(WITHDRAWN_FIELDS))
        ]
        if any(place in line for place in places):
            found.append(
                f"{where} names an edition's files by their path; name every edition's files by "
                "{editions}"
            )
        if grouped.search(line):
            found.append(
                f"{where} groups the editions' codes in braces; name every edition's files by "
                "{editions}"
            )
    return found
