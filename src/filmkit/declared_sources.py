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
from filmkit.repository import ARTIFACTS, EVIDENCE

if TYPE_CHECKING:
    from pathlib import Path

# The prompt's fields the engine fills no longer, and the field that replaces each.
WITHDRAWN_FIELDS = {"other": "{others}", "other_language": "{others}"}


def _fields(line: str) -> set[str]:
    """The fields a line of a str.format template cites.

    Raises:
        ValueError: the line is no str.format template.
    """
    return {name for _, name, _, _ in string.Formatter().parse(line) if name}


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
    from filmkit.places import CAST, SCRIPT, places

    codes = "|".join(re.escape(code) for code in editions)
    slug = str(declared.get("slug"))
    folders = [places(code, slug).folder for code in editions]
    # Each edition's folders, and where its files stood: the folder the withdrawn `sources`
    # still names and the one above the editions' folders.
    named = [f"{folder}/" for folder in folders]
    named += [
        f"{root_folder.as_posix()}/{code}/"
        for root_folder in (ARTIFACTS, EVIDENCE)
        for code in editions
    ]
    former = {table.get("sources") for table in editions.values() if isinstance(table, dict)}
    former |= {PurePosixPath(folder).parent.as_posix() for folder in folders}
    named += [
        f"{folder}/{name}"
        for folder in sorted(f for f in former if isinstance(f, str))
        for name in (SCRIPT, CAST, NARRATION_COPY)
    ]
    grouped = re.compile(rf"\{{\{{?\s*(?:{codes})(?:\s*,\s*(?:{codes}))+\s*\}}\}}?")
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        where = f"{prompt}:{number}"
        try:
            cited = _fields(line)
        except ValueError as error:
            found.append(
                f"{where} is no str.format template ({error}); write each brace that is no field "
                "twice"
            )
            continue
        found += [
            f"{where} cites {{{field}}}, which the engine no longer fills; name every other edition"
            f" by {WITHDRAWN_FIELDS[field]}"
            for field in sorted(cited & set(WITHDRAWN_FIELDS))
        ]
        if any(place in line for place in named):
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


# The recording every edition's reference derives from, at the place the layout gives it.
IDENTITY = "assets/audio/narrator-identity.wav"
# A recording a cast's derivation cites, by its path below the film's root.
RECORDING = re.compile(r"assets/audio/[\w./-]+?\.wav")
# The files this release removes, each with what to do instead; and the narration's former copy,
# which stood in an edition's folder.
REMOVED = {
    "content/voice-performance.json": "split it by edition into content/<code>/pronunciation.json"
    " and the declaration's [pronunciation], then remove it",
    "content/review/readings.json": "move each edition's analyst readings into "
    "content/<code>/readings.json, then remove it",
}
NARRATION_COPY = "narration.md"


def _unreadable(root: Path, path: str) -> str | None:
    """Why a source that stands below a root cannot be read as JSON, or None."""
    try:
        json.loads((root / path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, ValueError) as error:
        return f"{path} cannot be read: {error}"
    return None


def placement_problems(root: Path, declared: dict) -> list[str]:
    """Each source of a film at a place this release retires, missing at the place its code
    derives, removed by this release or unreadable, each in one line that says what to do.

    An edition's script or cast that stands where the withdrawn `sources` still names, or in
    `content/` above the editions' folders, and its reference recording and cover where the
    cast's withdrawn `reference_audio` and the edition's withdrawn `cover` still name them, are
    named with their destinations and not as missing. A cast's derivation names the recording
    every reference derives from at `IDENTITY`, wherever the film holds one. It reads the
    declaration as declared, so a field's problem hides none of these.
    """
    from filmkit.film import CAST, DECLARATION, SCRIPT, edition_files, places

    editions = declared.get("editions")
    editions = editions if isinstance(editions, dict) else {}
    slug = str(declared.get("slug"))
    references = {places(code, slug).reference for code in editions}
    found, claimed, folders = [], set(), {"content"}
    for code, table in editions.items():
        table = table if isinstance(table, dict) else {}
        derived = places(code, slug)
        sources = table.get("sources")
        folders |= {derived.folder, *([sources] if isinstance(sources, str) else [])}
        # Each place the edition's file is missing from, with the old place it stands at.
        moved = {}
        old_folders = [
            f for f in (sources, "content") if isinstance(f, str) and f != derived.folder
        ]
        for name, place in ((SCRIPT, derived.script), (CAST, derived.cast)):
            olds = [f"{f}/{name}" for f in old_folders if (root / f / name).is_file()]
            olds = [old for old in olds if old not in claimed]
            if olds and not (root / place).is_file():
                claimed.add(olds[0])
                moved[place] = olds[0]
        cast_path = moved.get(derived.cast, derived.cast)
        cast = _json(root / cast_path)
        cast = cast if isinstance(cast, dict) else {}
        for old, place in (
            (table.get("cover"), derived.cover),
            (cast.get("reference_audio"), derived.reference),
        ):
            stands = isinstance(old, str) and old != place and (root / old).is_file()
            if stands and not (root / place).is_file():
                moved[place] = old
        found += [
            f"{old} is the {code} edition's file at its old place; move it to {place}"
            for place, old in moved.items()
        ]
        found += [
            f"{DECLARATION} names a missing file: editions.{code}: {place}"
            for place in edition_files(code, slug)
            if place not in moved and not (root / place).is_file()
        ]
        found += [
            problem
            for path in (*edition_files(code, slug)[:3], derived.readings, *moved.values())
            if path.endswith(".json") and (problem := _unreadable(root, path))
        ]
        cited = set(RECORDING.findall(json.dumps(cast.get("derivation", ""))))
        found += [
            f"{cast_path} derivation cites {path}; move the recording every reference derives "
            f"from to {IDENTITY} and cite it there"
            for path in sorted(cited - references - {IDENTITY})
        ]
        if (root / IDENTITY).is_file() and IDENTITY not in cited:
            found.append(
                f"{cast_path} has no derivation that names {IDENTITY}, the recording every "
                "reference derives from; record there how the reference was made from it"
            )
    found += [
        f"{path}: this release removes it; {instead}"
        for path, instead in REMOVED.items()
        if (root / path).is_file()
    ]
    found += [
        f"{folder}/{NARRATION_COPY}: this release removes it; the engine keeps no copy of the "
        "narration beside its script"
        for folder in sorted(folders)
        if (root / folder / NARRATION_COPY).is_file()
    ]
    if "pronunciation" not in declared:
        found.append(
            f"{DECLARATION} declares no [pronunciation]; declare there the schema "
            "version, control boundary and acceptance every edition's pronunciation shares"
        )
    return found
