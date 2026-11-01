"""A film's concept contract and the check that keeps the film's words to it.

A film may name a concept contract in its declaration. The contract states, once, what each
concept the films name means in the canonical source, quoting the passage of a document the
source manifest pins, and which words each edition uses for it: one rendering, the forms the
narration may also use, and the counterexamples it must not use.

The check reads both editions' scripts, the film's caption terms and its picture sources. Each
segment declares the concepts it states; both editions of a segment declare the same ones, and
each appears in that segment's narration by its rendering or a form. No counterexample appears
in any narration, title, caption term or picture source. With a local clone of the source
repository, named by `FILM_SOURCE_CHECKOUT`, each quotation must be in its document at the
pinned commit; without one the quotations are reported as not checked. Every failure is
reported at once, and thoughts are numbered from 1 within their segment.

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
# A lowercase name of words joined by hyphens.
Id = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Words = Annotated[str, StringConstraints(min_length=1)]


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


class Contract(Declared):
    """The concepts a film names."""

    concept: tuple[Concept, ...] = Field(min_length=1)


class Place(NamedTuple):
    """Words a viewer meets, and where: an edition's title, thought or caption term, or a file."""

    where: str
    text: str


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
    """The edition's words a viewer meets: its titles, its thoughts and its caption terms."""
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
