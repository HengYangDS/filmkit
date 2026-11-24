"""What the loader reads of the sources a film's declaration names, beside the declaration itself.

`filmkit.film.read` asks these as the declaration loads, so each is refused beside the
declaration's other problems, before any work, each in one line that says what to write instead.
The review prompt may cite no field the engine no longer fills, `{other}` or `{other_language}`,
and may name no edition's files by their path or the declared codes grouped in braces, which
`{editions}` and `{others}` state for every edition (`filmkit.review.prompts`). The entry page
must keep its rule (`filmkit.delivery.entry`). No place of the film may declare a key the engine
has withdrawn (`filmkit.withdrawn`), read where the declaration names an edition's files
and where their code derives them (`filmkit.film.places`).
"""

from __future__ import annotations

import json
import re
import string
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import filmkit.withdrawn as withdrawn

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


def entry_problems(root: Path, declared: dict) -> list[str]:
    """Each fault of the declared entry page against its rule (`filmkit.delivery.entry`), for the
    declared editions whose languages the engine declares; none where the page is not named or
    cannot be read, which the declaration's other problems name."""
    import filmkit.delivery.entry as entry
    import filmkit.languages as languages

    page, editions = declared.get("entry"), declared.get("editions")
    if not isinstance(page, str) or not isinstance(editions, dict):
        return []
    try:
        text = (root / page).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    tags = {code: languages.LANGUAGES[code].tag for code in editions if code in languages.LANGUAGES}
    return entry.problems(text, tags, page)


def _json(path: Path) -> object:
    """A JSON file's value, or None where it cannot be read as JSON: a file that is missing or
    malformed is a problem of the declaration or of the step that reads it, not of this one."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def _held(where: str, value: object, kind: str) -> list[str]:
    """Each withdrawn key of a kind (`filmkit.withdrawn`) that a value holds, named where."""
    if not isinstance(value, dict):
        return []
    return [
        f"{where} declares {key}; {instead}"
        for key, instead in withdrawn.keys(kind).items()
        if key in value
    ]


def withdrawn_problems(root: Path, declared: dict, withdraw: bool = False) -> list[str]:
    """Each key of the one table of withdrawn keys (`filmkit.withdrawn`) that the declaration,
    its review table, an edition's table, script, its voice performance, segments, cast or
    pronunciation part declares,
    each in one line with what to do instead. An edition's files are read in the folder its
    declaration still names, and in the folder its code derives where it names none
    (`filmkit.film.places`), so a film that has not moved them and one that has are read alike.
    With `withdraw`, the declaration's, its review table's and the edition tables' withdrawn keys
    are then set aside, so that they hide none of its other fields' problems."""
    from filmkit.film import CAST, DECLARATION, SCRIPT, places

    found = _held(DECLARATION, declared, "declaration")
    found += _held(f"{DECLARATION} review", declared.get("review"), "review")
    editions = declared.get("editions")
    for code, table in (editions if isinstance(editions, dict) else {}).items():
        found += _held(f"{DECLARATION} editions.{code}", table, "edition")
        derived = places(code, str(declared.get("slug")))
        sources = table.get("sources") if isinstance(table, dict) else None
        folder = sources if isinstance(sources, str) else derived.folder
        script = _json(root / folder / SCRIPT)
        found += _held(f"{folder}/{SCRIPT}", script, "script")
        performance = script.get("voice_performance") if isinstance(script, dict) else None
        found += _held(f"{folder}/{SCRIPT} voice_performance", performance, "performance")
        segments = script.get("segments") if isinstance(script, dict) else None
        for segment in segments if isinstance(segments, list) else ():
            named = segment.get("id") if isinstance(segment, dict) else None
            found += _held(f"{folder}/{SCRIPT} segment {named}", segment, "segment")
        found += _held(f"{folder}/{CAST}", _json(root / folder / CAST), "cast")
        part = PurePosixPath(derived.pronunciation).name
        found += _held(f"{folder}/{part}", _json(root / folder / part), "part")
    if withdraw:
        tables = [(declared, "declaration"), (declared.get("review"), "review")]
        if isinstance(editions, dict):
            tables += [(table, "edition") for table in editions.values()]
        for value, kind in tables:
            for key in withdrawn.keys(kind) if isinstance(value, dict) else ():
                value.pop(key, None)
    return found
