"""A film's concept contract and the check that keeps the film's words to it.

A film may name a concept contract in its declaration. The contract states, once, what each
concept the films name means in the canonical source, quoting the passage of a document the
source manifest pins, and which words each edition uses for it: one rendering, the forms the
narration may also use, and the counterexamples it must not use.

The check reads both editions' scripts, the film's caption terms and its picture sources. Each
segment declares the concepts it states; both editions of a segment declare the same ones, and
each appears in that segment's narration by its rendering or a form. No counterexample appears
in any narration, title, caption term, release synopsis, comment or description, the summary
the edition's player shows, or picture source; the engine renders the rest of the player.
With a local clone of the source repository, named by `FILM_SOURCE_CHECKOUT`, each quotation
must be in its document at the pinned commit; without one the quotations are reported as not
checked. Every failure is reported at once, and thoughts are numbered from 1 within their segment.

A Latin-script word keeps its base form in Chinese, so Chinese words must carry its number. Each
Chinese thought pairs with the English thought of its segment and index when the segment has as
many thoughts in both editions, and otherwise with the whole English segment. Where that
counterpart names such a word only by its plural, each Chinese clause that says the word holds a
number word, or a numeral with its classifier before the word, other than a lone 一 (`counted`).
The contract's optional [number] table declares more number words and reasoned exceptions, each
a thought and term; an exception that excuses nothing is stale.

Usage: python -m filmkit.concepts
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from typing import Annotated, NamedTuple

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

import filmkit.repository as repository
import filmkit.sources as sources
from filmkit.film import FILM
from filmkit.narration.thought_groups import authored_groups
from filmkit.production import CODES, Edition

# The folder of picture sources, and the files below it that hold words a viewer may see.
PICTURE = "picture"
PICTURE_SUFFIXES = (".js", ".mjs", ".html", ".json")
# The release fields a viewer reads in a film's metadata, in the order they are checked.
RELEASE_PROSE = ("synopsis", "comment", "description")
# A lowercase name of words joined by hyphens.
Id = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Words = Annotated[str, StringConstraints(min_length=1)]
# Words that hold more than spaces, kept without their outer spaces.
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# The marks that bound a Chinese clause.
CLAUSE_MARKS = re.compile(r"[，。；：、？！]")
# A Latin-script word, which Chinese narration says in its base form whatever its number.
LATIN_WORD = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]+(?![A-Za-z0-9])")
# The words that carry a Chinese clause's number: each of these characters, a pronoun of a group
# and a count repeated for each member, and a numeral counting with a classifier. The numeral is
# the whole run before the classifier; a lone 一 states the singular.
NUMBER_WORDS = (*"们些多几各每众两俩双", "它们", "他们", "一个个")
SINGULAR = "一"
COUNTED = re.compile(
    r"(?<![一二三四五六七八九十百千万])([一二三四五六七八九十百千万]+)"
    r"[个位名种类款套件条项份张台部本次步层级组批群家支只句段篇章节门处所座轮遍场笔例]"
)


class ConceptError(ValueError):
    """The concept contract, or the film's words, depart from what the contract states."""


class Declared(BaseModel):
    """A declared table: every field is known, and none changes after loading."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Passage(Declared):
    """The pinned document that defines a concept, and the words that define it there."""

    path: Words
    quote: Words


class Rendering(Declared):
    """An edition's words for a concept: its rendering, other accepted forms, and refused ones."""

    rendering: Words
    forms: tuple[Words, ...] = ()
    avoid: tuple[Words, ...] = ()

    @property
    def accepted(self) -> tuple[str, ...]:
        """The words that state the concept: the rendering, then the forms."""
        return (self.rendering, *self.forms)


class Concept(Declared):
    """One concept sense: its source term and passage, its essence and each edition's words."""

    id: Id
    term: Words
    essence: Words
    source: Passage
    zh: Rendering
    en: Rendering

    def words(self, code: str) -> Rendering:
        """The concept's words in one edition."""
        return self.zh if code == "zh" else self.en


class NumberException(Declared):
    """A Chinese thought whose Latin-script term may stand without a number word, and why."""

    thought: Words
    term: Words
    reason: Text


class Number(Declared):
    """The number words a film adds to `NUMBER_WORDS`, and its reasoned exceptions."""

    words: tuple[Text, ...] = ()
    exceptions: tuple[NumberException, ...] = ()


class Contract(Declared):
    """The concepts a film names, and how its Chinese carries the number of Latin-script words."""

    concept: tuple[Concept, ...] = Field(min_length=1)
    number: Number = Number()


class Place(NamedTuple):
    """Words a viewer meets, and where: an edition's title, thought or caption term, or a file."""

    where: str
    text: str


class Unnumbered(NamedTuple):
    """A Chinese clause that says a Latin-script term with no number word, where the English
    names the term only by its plural."""

    thought: str
    term: str
    plural: str
    clause: str


def load(path: str, pinned: dict) -> Contract:
    """Read and check the contract at a path, refusing it with every failing entry."""
    try:
        text = (repository.ROOT / path).read_text(encoding="utf-8")
        contract = Contract.model_validate(tomllib.loads(text))
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as error:
        message = f"{path} is not a concept contract: {error}"
        raise ConceptError(message) from error
    members = {member["path"] for member in pinned["members"]}
    failures, seen = [], set()
    for concept in contract.concept:
        if concept.id in seen:
            failures.append(f"Concept {concept.id} is declared more than once")
        seen.add(concept.id)
        if concept.source.path not in members:
            failures.append(
                f"Concept {concept.id} cites {concept.source.path}, "
                "which the source manifest does not pin"
            )
    pairs = [(exception.thought, exception.term) for exception in contract.number.exceptions]
    failures += [
        f"Number exception {thought} {term} is declared more than once"
        for thought, term in dict.fromkeys(pair for pair in pairs if pairs.count(pair) > 1)
    ]
    if failures:
        raise ConceptError("\n".join(failures))
    return contract


def plain(text: str) -> str:
    """Text as quotations are compared: no Markdown emphasis or code marks, single spaces."""
    return " ".join(text.replace("*", "").replace("`", "").split())


def quotations(contract: Contract, pinned: dict) -> tuple[str, list[str]]:
    """Check each quotation in its document at the pinned commit of the named local clone.

    Returns:
        "verified", "refused" or "not_checked", and the failures.
    """
    checkout = os.environ.get(sources.CHECKOUT)
    if not checkout:
        return "not_checked", []
    commit, documents, failures = pinned["commit"], {}, []
    for concept in contract.concept:
        path = concept.source.path
        if path not in documents:
            shown = subprocess.run(
                ["git", "-C", checkout, "show", f"{commit}:{path}"],
                capture_output=True,
                check=False,
            )
            readable = shown.returncode == 0
            documents[path] = plain(shown.stdout.decode("utf-8", "replace")) if readable else None
        if documents[path] is None:
            failures.append(f"Concept {concept.id}: {path} cannot be read at {commit[:12]}")
        elif plain(concept.source.quote) not in documents[path]:
            failures.append(
                f"Concept {concept.id}: the quotation is not in {path} at {commit[:12]}"
            )
    return ("refused" if failures else "verified"), failures


def found(text: str, phrase: str, code: str) -> list[int]:
    """Where a phrase occurs: anywhere in Chinese, as whole words ignoring case in English."""
    if code == "zh":
        pattern, flags = re.escape(phrase), 0
    else:
        pattern, flags = rf"(?<![A-Za-z0-9]){re.escape(phrase)}(?![A-Za-z0-9])", re.IGNORECASE
    return [match.start() for match in re.finditer(pattern, text, flags)]


def edition_places(code: str, script: dict) -> list[Place]:
    """The edition's words a viewer meets: titles, thoughts, caption terms, release and player."""
    places = [Place(f"{code} title", script["title"])]
    places += [
        Place(f"{code} chapter {chapter['id']} title", chapter["title"])
        for chapter in script["chapters"]
    ]
    for segment in script["segments"]:
        places.append(Place(f"{code} {segment['id']} title", segment["title"]))
        places += [
            Place(f"{code} {segment['id']}.{index}", thought)
            for index, thought in enumerate(authored_groups(segment), 1)
        ]
    places += [Place(f"{code} caption term", term) for term in FILM.editions[code].caption_terms]
    release = script.get("release", {})
    places += [
        Place(f"{code} release {key}", release[key]) for key in RELEASE_PROSE if key in release
    ]
    # The engine renders the rest of each player page from these words and its own.
    places.append(Place(f"{code} player summary", FILM.editions[code].summary))
    return places


def picture_places() -> list[Place]:
    """Each line of the picture's text sources, outside installed packages."""
    folder = repository.ROOT / PICTURE
    places = []
    for path in sorted(folder.rglob("*")) if folder.is_dir() else ():
        if (
            path.suffix not in PICTURE_SUFFIXES
            or "node_modules" in path.parts
            or not path.is_file()
        ):
            continue
        name = path.relative_to(repository.ROOT).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        places += [Place(f"{name}:{number}", line) for number, line in enumerate(lines, 1)]
    return places


def declarations(contract: Contract, scripts: dict[str, dict]) -> list[str]:
    """Check each segment's declared concepts: known, alike in both editions, and stated."""
    concepts = {concept.id: concept for concept in contract.concept}
    declared = {
        code: {segment["id"]: tuple(segment.get("concepts", ())) for segment in script["segments"]}
        for code, script in scripts.items()
    }
    failures = []
    for code, segments in declared.items():
        for segment_id, ids in segments.items():
            failures += [
                f"{code} {segment_id} declares {concept_id}, which the contract does not hold"
                for concept_id in ids
                if concept_id not in concepts
            ]
    for segment_id in sorted({key for segments in declared.values() for key in segments}):
        sets = {code: set(declared[code].get(segment_id, ())) for code in declared}
        if len({frozenset(ids) for ids in sets.values()}) > 1:
            differing = sorted(set.union(*sets.values()) - set.intersection(*sets.values()))
            failures.append(
                f"{segment_id} declares different concepts in its editions: {', '.join(differing)}"
            )
    for code, script in scripts.items():
        for segment in script["segments"]:
            narration = "".join(authored_groups(segment))
            for concept_id in segment.get("concepts", ()):
                concept = concepts.get(concept_id)
                accepted = concept.words(code).accepted if concept else ()
                if concept and not any(found(narration, words, code) for words in accepted):
                    failures.append(
                        f"{code} {segment['id']} declares {concept_id} but says none of: "
                        + " | ".join(accepted)
                    )
    return failures


def counterexamples(contract: Contract, places: dict[str, list[Place]]) -> list[str]:
    """Each counterexample in an edition's words or the picture, with where it occurs."""
    failures = []
    for concept in contract.concept:
        for code in CODES:
            for phrase in concept.words(code).avoid:
                for place in places[code] + places["picture"]:
                    failures += [
                        f"{place.where} at {position}: {phrase!r}, a counterexample of {concept.id}"
                        for position in found(place.text, phrase, code)
                    ]
    return failures


def english_plural(term: str, text: str) -> str | None:
    """The plural, term+s or term+es, by which English text names a term it never says itself.

    Each is a whole word in its own case.
    """

    def said(word: str) -> bool:
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text) is not None

    if said(term):
        return None
    return next((plural for plural in (f"{term}s", f"{term}es") if said(plural)), None)


def counted(clause: str, term: str, words: tuple[str, ...]) -> bool:
    """Whether a Chinese clause carries the number of a term it says.

    A number word or a declared word carries it anywhere in the clause, and a numeral with its
    classifier only before the term, since a count after the term counts another thing; a lone
    一 with its classifier states the singular and carries no plural.
    """
    said = max(match.start() for match in LATIN_WORD.finditer(clause) if match[0] == term)
    if any(count[1] != SINGULAR for count in COUNTED.finditer(clause[:said])):
        return True
    return any(word in clause for word in (*NUMBER_WORDS, *words))


def unnumbered(scripts: dict[str, dict], words: tuple[str, ...]) -> list[Unnumbered]:
    """Each Chinese clause that says a Latin-script term its English counterpart names only by
    its plural, and holds no number word."""
    english = {segment["id"]: authored_groups(segment) for segment in scripts["en"]["segments"]}
    clauses = []
    for segment in scripts["zh"]["segments"]:
        others = english.get(segment["id"])
        if others is None:
            continue
        thoughts = authored_groups(segment)
        for index, thought in enumerate(thoughts, 1):
            counterpart = others[index - 1] if len(others) == len(thoughts) else " ".join(others)
            for term in dict.fromkeys(LATIN_WORD.findall(thought)):
                plural = english_plural(term, counterpart)
                clauses += [
                    Unnumbered(f"{segment['id']}.{index}", term, plural, clause.strip())
                    for clause in CLAUSE_MARKS.split(thought)
                    if plural
                    and term in LATIN_WORD.findall(clause)
                    and not counted(clause, term, words)
                ]
    return clauses


def number_parity(number: Number, scripts: dict[str, dict]) -> list[str]:
    """Each unnumbered Chinese clause that no exception excuses, and each stale exception."""
    clauses = unnumbered(scripts, number.words)
    excused = {(exception.thought, exception.term) for exception in number.exceptions}
    failures = [
        f"zh {item.thought}: {item.term!r} in {item.clause!r} carries no number word, where the "
        f"English says {item.plural!r}"
        for item in clauses
        if (item.thought, item.term) not in excused
    ]
    flagged = {(item.thought, item.term) for item in clauses}
    failures += [
        f"Number exception {exception.thought} {exception.term} is stale: it names no current "
        "occurrence"
        for exception in number.exceptions
        if (exception.thought, exception.term) not in flagged
    ]
    return failures


def check() -> dict:
    """Check the film's words against its concept contract, refusing every departure at once.

    Returns:
        The report: the contract, its concepts, the quotation status and the declarations.
    """
    if FILM.concepts is None:
        return {"contract": None, "status": "not_declared"}
    pinned = sources.manifest()
    contract = load(FILM.concepts, pinned)
    status, failures = quotations(contract, pinned)
    scripts = {code: repository.read(Edition(code).script) for code in CODES}
    places = {code: edition_places(code, script) for code, script in scripts.items()}
    places["picture"] = picture_places()
    failures += declarations(contract, scripts)
    failures += counterexamples(contract, places)
    failures += number_parity(contract.number, scripts)
    if failures:
        raise ConceptError("\n".join(failures))
    return {
        "contract": FILM.concepts,
        "contract_sha256": repository.sha(FILM.concepts),
        "concepts": len(contract.concept),
        "quotations": status,
        "declarations": sum(
            len(segment.get("concepts", ()))
            for script in scripts.values()
            for segment in script["segments"]
        ),
        "number_exceptions": len(contract.number.exceptions),
    }


def main() -> None:
    try:
        report = check()
    except ConceptError as error:
        message = f"concepts: {error}"
        raise SystemExit(message) from None
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
