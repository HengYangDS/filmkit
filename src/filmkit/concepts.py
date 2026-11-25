"""A film's concept contract and the check that keeps the film's words to it.

A film may name a concept contract in its declaration. The contract states, once, what each
concept the films name means in the canonical source, quoting the passage of a document the
source manifest pins, and which words each edition uses for it: one rendering, the forms the
narration may also use, and the counterexamples it must not use.

The check reads every edition's script, the film's caption terms, its entry page and its picture
sources. Each segment declares the concepts it states; every edition of a segment declares the
same ones, and each appears in that segment's narration by its rendering or a form. No
counterexample appears in any narration, title, caption term, release synopsis, comment or
description, the summary the edition's player shows, the text the entry page shows, or picture
source; the engine renders the rest of the player. The words a viewer meets outside the
picture are gathered once (`places`), for this check and the register check (`filmkit.register`).
With a local clone of the source repository, named by `FILM_SOURCE_CHECKOUT`, each quotation
must be in its document at the pinned commit; without one the quotations are reported as not
checked. Every failure is reported at once, and thoughts are numbered from 1 within their segment.

A Latin-script word keeps its base form in Chinese, so Chinese words must carry its number. Each
Chinese thought pairs with the English thought of its segment and index when the segment has as
many thoughts in each, and otherwise with the whole English segment. Where that
counterpart names such a word only by its plural, each Chinese clause that says the word holds a
number word, or a numeral with its classifier before the word, other than a lone 一 (`counted`).
The contract's optional [number] table declares more number words and reasoned exceptions, each
a thought and term; an exception that excuses nothing is stale.

`filmkit check` asks it among the film's sources (`filmkit.check`).
"""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from html.parser import HTMLParser
from typing import Annotated, NamedTuple

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

import filmkit.languages as languages
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
# The film's entry page, one page of every edition and so one place for all of them; the elements
# whose content a page does not show, whose end tags HTML requires; the block elements, which
# alone end a run of text, every other element, known or not, being read as inline; and the
# attributes whose words a viewer meets.
ENTRY = "entry page"
UNSHOWN = frozenset({"script", "style", "template"})
BLOCK = frozenset(
    "address article aside blockquote body caption dd details dialog div dl dt fieldset"
    " figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html legend li main"
    " menu nav noscript ol optgroup option p pre section summary table tbody td tfoot th thead"
    " title tr ul".split()
)
LABELS = ("alt", "title", "aria-label")
# A ruby's reading, an annotation of the text it stands beside: no text of the run. Its end tag
# may be left out, so a reading ends at its own end, at the next reading, at its ruby's end or at
# a block.
READING = frozenset({"rt", "rp"})
# A lowercase name of words joined by hyphens.
Id = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Words = Annotated[str, StringConstraints(min_length=1)]
# Words that hold more than spaces, kept without their outer spaces.
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# The full-width marks that bound a clause.
CLAUSE_MARKS = languages.compiled("clause-marks")
# A Latin-script word, which a language that marks no number says in its base form whatever its
# number, as Chinese narration does.
LATIN_WORD = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]+(?![A-Za-z0-9])")


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
    """One concept sense: its source term and passage, its essence and each edition's words,
    declared under the edition's code (`zh = { rendering = … }`)."""

    id: Id
    term: Words
    essence: Words
    source: Passage
    renderings: dict[str, Rendering]

    @model_validator(mode="before")
    @classmethod
    def renderings_by_code(cls, data: object) -> object:
        """Gather every key beside the concept's own fields as an edition's rendering."""
        if not isinstance(data, dict):
            return data
        own = {"id", "term", "essence", "source"}
        renderings = {key: value for key, value in data.items() if key not in own}
        return {**{key: data[key] for key in own if key in data}, "renderings": renderings}

    def words(self, code: str) -> Rendering:
        """The concept's words in one edition."""
        return self.renderings[code]


class NumberException(Declared):
    """A Chinese thought whose Latin-script term may stand without a number word, and why."""

    thought: Words
    term: Words
    reason: Text


class Number(Declared):
    """The number words a film adds to those its languages declare (`filmkit.languages`), and its
    reasoned exceptions."""

    words: tuple[Text, ...] = ()
    exceptions: tuple[NumberException, ...] = ()


class Contract(Declared):
    """The concepts a film names, and how its editions whose languages mark no number carry the
    number of Latin-script words."""

    concept: tuple[Concept, ...] = Field(min_length=1)
    number: Number = Number()


class Place(NamedTuple):
    """Words a viewer meets, and where: an edition's title, thought or caption term, or a file."""

    where: str
    text: str


class Shown(HTMLParser):
    """The words a page shows, a run at a time: each run of its text, which a block element ends
    and no other element does, with a space where a `br` stands in either spelling, and each
    label a viewer meets. Only script, style and template content is left out: what `hidden`
    hides counts as shown, since a reading that guesses where an element whose end tag is left
    out ends would hide what follows it. A ruby's reading (`rt`, `rp`) is no text of its run."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.left_out, self.run, self.reading = 0, [], False
        self.runs: list[str] = []

    def end_run(self) -> None:
        text = "".join(self.run)
        if text.strip():
            self.runs.append(text)
        self.run = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in UNSHOWN or self.left_out:
            self.left_out += tag in UNSHOWN
            return
        self.reading = tag in READING or (self.reading and tag not in BLOCK)
        if tag == "br":
            self.run.append(" ")
        elif tag in BLOCK:
            self.end_run()
        held = {name: value or "" for name, value in attrs}
        self.runs += [held[name] for name in LABELS if held.get(name, "").strip()]

    def handle_endtag(self, tag: str) -> None:
        if tag in UNSHOWN:
            self.left_out = max(0, self.left_out - 1)
        elif not self.left_out:
            self.reading = self.reading and tag not in {*READING, "ruby", *BLOCK}
            if tag in BLOCK:
                self.end_run()

    def handle_data(self, data: str) -> None:
        if not self.left_out and not self.reading:
            self.run.append(data)

    def close(self) -> None:
        super().close()
        self.end_run()


class Unnumbered(NamedTuple):
    """A clause of an edition whose language marks no number, as Chinese, that says a Latin-script
    term with no number word, where another edition, whose language marks it, names the term only
    by its plural: the pair of editions, the thought, the term, the plural and the clause."""

    edition: str
    other: str
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
        failures += [
            f"Concept {concept.id} has no rendering for the edition {code}, which the film declares"
            for code in CODES
            if code not in concept.renderings
        ]
        failures += [
            f"Concept {concept.id} renders the edition {code}, which the film does not declare"
            for code in concept.renderings
            if code not in CODES
        ]
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
    """Where a phrase occurs: anywhere in a language whose words spaces do not delimit, as
    Chinese, and as whole words ignoring case in one whose words they delimit, as English."""
    if not languages.language(code).spaced:
        pattern, flags = re.escape(phrase), 0
    else:
        pattern, flags = rf"(?<![A-Za-z0-9]){re.escape(phrase)}(?![A-Za-z0-9])", re.IGNORECASE
    return [match.start() for match in re.finditer(pattern, text, flags)]


def places(scripts: dict[str, dict] | None = None) -> dict[str, list[Place]]:
    """The words a viewer meets outside the picture, by edition, from the editions' scripts
    (read unless given), and under `ENTRY` the entry page's: one page for every edition, each
    run of its shown text and each of its labels a place of that one name."""
    if scripts is None:
        scripts = {code: repository.read(Edition(code).script) for code in CODES}
    gathered = {code: edition_places(code, script) for code, script in scripts.items()}
    try:
        page = (repository.ROOT / FILM.entry).read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        message = f"The entry page {FILM.entry} is no UTF-8 text: byte {error.start} cannot be read"
        raise ConceptError(message) from None
    shown = Shown()
    shown.feed(page)
    shown.close()
    gathered[ENTRY] = [Place(ENTRY, run) for run in shown.runs]
    return gathered


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
    terms = FILM.editions[code].caption_terms
    places += [Place(f"{code} caption term {term!r}", term) for term in terms]
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
    """Check each segment's declared concepts: known, alike in every edition, and stated."""
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
    # Each edition's concepts of a segment against the first declared edition's.
    first, *others = declared
    for segment_id in sorted({key for segments in declared.values() for key in segments}):
        sets = {code: set(declared[code].get(segment_id, ())) for code in declared}
        for code in others:
            differing = sorted(sets[first] ^ sets[code])
            if differing:
                failures.append(
                    f"{segment_id} declares different concepts in {first} and {code}: "
                    + ", ".join(differing)
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
    """Each counterexample in an edition's words, or in the words every edition shares (the entry
    page, the picture), with where it occurs."""
    shared = [place for name, held in places.items() if name not in CODES for place in held]
    failures = []
    for concept in contract.concept:
        for code in CODES:
            for phrase in concept.words(code).avoid:
                for place in places[code] + shared:
                    failures += [
                        f"{place.where} at {position}: {phrase!r}, a counterexample of {concept.id}"
                        for position in found(place.text, phrase, code)
                    ]
    return failures


def plural(term: str, text: str, suffixes: tuple[str, ...]) -> str | None:
    """The plural, the term with one of a language's suffixes, by which text names a term it never
    says itself. Each is a whole word in its own case."""

    def said(word: str) -> bool:
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text) is not None

    if said(term):
        return None
    return next((form for form in (f"{term}{s}" for s in suffixes) if said(form)), None)


def counted(clause: str, term: str, words: tuple[str, ...], number: languages.Counted) -> bool:
    """Whether a clause of a language that marks no number carries the number of a term it says.

    One of the language's number words or a declared word carries it anywhere in the clause, and
    a numeral of the language's numerals counting with one of its classifiers only before the
    term, since a count after the term counts another thing; a lone singular numeral with its
    classifier states one and carries no plural.
    """
    numerals = re.escape(number.numerals)
    count = re.compile(f"(?<![{numerals}])([{numerals}]+)[{re.escape(number.classifiers)}]")
    said = max(match.start() for match in LATIN_WORD.finditer(clause) if match[0] == term)
    if any(found[1] != number.singular for found in count.finditer(clause[:said])):
        return True
    return any(word in clause for word in (*number.words, *words))


def unnumbered(scripts: dict[str, dict], words: tuple[str, ...]) -> list[Unnumbered]:
    """Each clause of an edition whose language marks no number that says a Latin-script term its
    counterpart in an edition whose language marks number names only by its plural, and holds no
    number word: every such pair of editions, in the declared order."""
    numbers = {code: languages.language(code).number for code in scripts}
    clauses = []
    for code, other in ((c, o) for c in scripts for o in scripts if c != o):
        counted_by, marked_by = numbers[code], numbers[other]
        if counted_by.kind != "counted-by-words" or marked_by.kind != "plural-suffix":
            continue
        others = {segment["id"]: authored_groups(segment) for segment in scripts[other]["segments"]}
        for segment in scripts[code]["segments"]:
            counterparts = others.get(segment["id"])
            if counterparts is None:
                continue
            thoughts = authored_groups(segment)
            for index, thought in enumerate(thoughts, 1):
                counterpart = (
                    counterparts[index - 1]
                    if len(counterparts) == len(thoughts)
                    else " ".join(counterparts)
                )
                for term in dict.fromkeys(LATIN_WORD.findall(thought)):
                    form = plural(term, counterpart, marked_by.suffixes)
                    clauses += [
                        Unnumbered(
                            code, other, f"{segment['id']}.{index}", term, form, part.strip()
                        )
                        for part in CLAUSE_MARKS.split(thought)
                        if form
                        and term in LATIN_WORD.findall(part)
                        and not counted(part, term, words, counted_by)
                    ]
    return clauses


def number_parity(number: Number, scripts: dict[str, dict]) -> list[str]:
    """Each unnumbered clause that no exception excuses, and each stale exception."""
    clauses = unnumbered(scripts, number.words)
    excused = {(exception.thought, exception.term) for exception in number.exceptions}
    failures = [
        f"{item.edition} {item.thought}: {item.term!r} in {item.clause!r} carries no number word, "
        f"where the {languages.language(item.other).english_name} says {item.plural!r}"
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
    failures += declarations(contract, scripts)
    failures += counterexamples(contract, {**places(scripts), "picture": picture_places()})
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
