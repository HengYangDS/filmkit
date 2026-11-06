"""The film the engine builds: its declaration in `content/film.toml`, checked before any work.

The engine takes every film-specific value from this declaration and the files it names; each
edition's script declares the edition's title, author, language, duration, frame rate and
chapters. A declaration that is malformed, incomplete or names a missing file is refused with
each failing field. A cover is the exception: the engine paints it from the staged picture, so
a new film names its covers before they exist, and packaging requires them.
"""

from __future__ import annotations

import tomllib
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
)

import filmkit.repository as repository

if TYPE_CHECKING:
    from pathlib import Path

DECLARATION = repository.DECLARATION
# The files every edition's sources folder holds.
EDITION_FILES = ("film-script.json", "voice-reference.json")
# The player template a sources folder once held; the engine renders each edition's player now.
PLAYER_TEMPLATE = "player.html"
# A lowercase name of words joined by hyphens.
Name = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Floor = Annotated[int, Field(ge=0, le=100)]
# A voice-clarity floor in dB of cepstral peak prominence, and one for each edition.
ClarityFloor = Annotated[float, Field(gt=0, le=60)]
ClarityFloors = Annotated[dict[Literal["zh", "en"], ClarityFloor], Field(min_length=2)]
# Declared words: text that holds more than whitespace, kept without its outer spaces.
Stated = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# A colour as CSS writes it in hexadecimal, #rrggbb.
Colour = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]


class FilmError(ValueError):
    """The film declaration is missing, invalid or names a missing file."""


class Declared(BaseModel):
    """A declared table: every field is known, and none changes after loading."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class EditionDeclaration(Declared):
    """One edition's folder of script and cast, its cover, the summary its player shows under the
    film, and its caption terms."""

    sources: str
    cover: str
    summary: Stated
    caption_terms: tuple[str, ...] = ()


class Player(Declared):
    """The colours of each edition's player page (`filmkit.delivery.player`): its ground, its
    text, its quieter text, its rules and outlines, and the accent of a chosen or focused
    control."""

    background: Colour
    text: Colour
    muted: Colour
    line: Colour
    accent: Colour


# A share of the widest line of one size in a wrapped label.
Share = Annotated[float, Field(gt=0, le=1)]
# A word an English line may not end on.
LeadWord = Annotated[str, StringConstraints(pattern=r"^\S+$")]


class WrappingException(Declared):
    """One wrapped label an edition keeps against the wrapping rules: its exact painted lines,
    top to bottom, and why they stay."""

    edition: Literal["zh", "en"]
    lines: tuple[Stated, ...] = Field(min_length=2)
    reason: Stated


class Wrapping(Declared):
    """How the picture's wrapped labels break (`filmkit.picture.gates`).

    Among the lines of one size, a line other than the last spans at least `line_share` of the
    widest and the last at least `last_share`. `lead_words` adds the words an English line may
    not end on to the engine's. A label of an edition whose lines one of the edition's exceptions
    names is recorded with its reason instead of refused, and an exception that no frame of its
    edition paints is refused.
    """

    line_share: Share = 0.8
    last_share: Share = 0.6
    lead_words: tuple[LeadWord, ...] = ()
    exceptions: tuple[WrappingException, ...] = ()

    @field_validator("exceptions")
    @classmethod
    def distinct_labels(
        cls, exceptions: tuple[WrappingException, ...]
    ) -> tuple[WrappingException, ...]:
        """Refuse two exceptions of one edition's label."""
        if len({(e.edition, e.lines) for e in exceptions}) != len(exceptions):
            message = "two exceptions name the same lines of one edition"
            raise ValueError(message)
        return exceptions


class Picture(Declared):
    """The font files the picture stages below fonts/, in their order, and how its wrapped labels
    break."""

    fonts: tuple[str, ...] = Field(min_length=1)
    wrapping: Wrapping = Field(default_factory=Wrapping)

    @field_validator("fonts")
    @classmethod
    def distinct_names(cls, fonts: tuple[str, ...]) -> tuple[str, ...]:
        """Refuse two fonts of one file name, which would stage as one file."""
        names = [PurePosixPath(font).name for font in fonts]
        if len(set(names)) != len(names):
            message = "fonts stage below fonts/ by file name, and these stage two fonts as one file"
            raise ValueError(message)
        return fonts


class Review(Declared):
    """The reviewer prompt, the verifier's floors, the scored dimensions and the plan readings.

    The dimensions keep their record order. The readings file holds the listening plan's
    analyst readings; without one the plan adds none. The clarity floors, one for each edition,
    are what the review's measurement records each voice's clarity against (`review.clarity`).
    """

    prompt: str
    overall_minimum: Floor
    dimension_minimum: Floor
    dimensions: dict[str, str] = Field(min_length=1)
    readings: str | None = None
    clarity_minimum_db: ClarityFloors | None = None


# The longest heard pause a word boundary without a mark may hold, in seconds.
PauseLimit = Annotated[float, Field(gt=0, le=2)]
# A declared word or reason: text that holds more than whitespace.
FlowText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# A thought by its segment and its number from 1, as "05.4".
ThoughtName = Annotated[str, StringConstraints(pattern=r"^[^.\s]+\.[1-9][0-9]*$")]
# A Latin-script word, which may hold an apostrophe, a period or a hyphen inside.
LatinWord = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9]*(?:['’.-][A-Za-z0-9]+)*$")
]


class FlowException(Declared):
    """One word boundary of an edition whose unmarked pause the film keeps above its limit.

    The boundary is named by its thought, "<segment>.<number>", and the aligned words on either
    side of it; the reason says why the pause stays.
    """

    edition: Literal["zh", "en"]
    thought: ThoughtName
    left: FlowText
    right: FlowText
    reason: FlowText


class Flow(Declared):
    """The longest pauses word boundaries without a mark may hold, and the film's exceptions.

    `switch_limit_s` holds where the words switch between Chinese characters and Latin letters
    or digits, and `unmarked_limit_s` elsewhere (`filmkit.narration.flow`).
    """

    switch_limit_s: PauseLimit = 0.2
    unmarked_limit_s: PauseLimit = 0.4
    exceptions: tuple[FlowException, ...] = ()

    @field_validator("exceptions")
    @classmethod
    def distinct_boundaries(
        cls, exceptions: tuple[FlowException, ...]
    ) -> tuple[FlowException, ...]:
        """Refuse two exceptions of one boundary."""
        keys = [(e.edition, e.thought, e.left.casefold(), e.right.casefold()) for e in exceptions]
        if len(set(keys)) != len(keys):
            message = "two exceptions name one boundary"
            raise ValueError(message)
        return exceptions


class TermReference(Declared):
    """The occurrence of a declared term in one edition whose take a person heard correct.

    `thought` names its thought, and `index` its place, from 0, among the term's occurrences in
    that thought.
    """

    thought: ThoughtName
    index: Annotated[int, Field(ge=0)]

    @property
    def segment(self) -> str:
        """The segment that holds the reference's thought."""
        return self.thought.rsplit(".", 1)[0]


class NarrationTerm(Declared):
    """A Latin-script term the narration says, the one form every language speaks, and how.

    Every language's normalization in the pronunciation contract must give the term its
    `spoken` form; `ipa` states its pronunciation, and `reference` holds, for each edition that
    says it, the occurrence that every other is measured against (`filmkit.narration.terms`).
    """

    term: LatinWord
    spoken: LatinWord
    ipa: FlowText
    reference: dict[Literal["zh", "en"], TermReference] = Field(default_factory=dict)


class Narration(Declared):
    """How the narration must flow and say its terms (`narration.flow`, `narration.terms`)."""

    flow: Flow = Field(default_factory=Flow)
    terms: tuple[NarrationTerm, ...] = ()

    @field_validator("terms")
    @classmethod
    def distinct_terms(cls, terms: tuple[NarrationTerm, ...]) -> tuple[NarrationTerm, ...]:
        """Refuse a term declared twice, in any case."""
        names = [term.term.casefold() for term in terms]
        if len(set(names)) != len(names):
            message = "a term is declared more than once"
            raise ValueError(message)
        return terms


class Film(Declared):
    """A bilingual film: its file prefix, delivery folder, entry page, sources, fonts, player
    colours and review.

    A film may name a concept contract, which `filmkit.concepts` checks its narration against.
    """

    slug: Name
    documents_folder: Name
    entry: str
    source_manifest: str
    concepts: str | None = None
    editions: dict[Literal["zh", "en"], EditionDeclaration] = Field(min_length=2)
    picture: Picture
    player: Player
    review: Review
    narration: Narration = Field(default_factory=Narration)


def named_files(film: Film) -> list[tuple[str, str]]:
    """Each file the declaration names except the covers, with the field that names it."""
    named = [
        ("entry", film.entry),
        ("source_manifest", film.source_manifest),
        ("review.prompt", film.review.prompt),
    ]
    for code, edition in film.editions.items():
        field = f"editions.{code}.sources"
        named += [(field, f"{edition.sources}/{name}") for name in EDITION_FILES]
    named += [("picture.fonts", font) for font in film.picture.fonts]
    if film.review.readings is not None:
        named.append(("review.readings", film.review.readings))
    if film.concepts is not None:
        named.append(("concepts", film.concepts))
    return named


def copied_players(root: Path, film: Film) -> str | None:
    """Why a film's sources may not hold player pages of their own, naming each one and the
    declarations that replace it, or None when they hold none."""
    pages = [
        f"{edition.sources}/{PLAYER_TEMPLATE}"
        for edition in film.editions.values()
        if (root / edition.sources / PLAYER_TEMPLATE).is_file()
    ]
    if not pages:
        return None
    return (
        f"The engine renders each edition's player and reads no {', '.join(pages)}: declare "
        "the words each player shows as editions.<code>.summary and its colours in [player] "
        f"in {DECLARATION}, then remove the page"
    )


def load(root: Path) -> Film:
    """Read and check the declaration below a root, refusing it with each failing field."""
    try:
        film = Film.model_validate(tomllib.loads((root / DECLARATION).read_text(encoding="utf-8")))
    except (OSError, tomllib.TOMLDecodeError, ValidationError) as error:
        message = f"{DECLARATION} is not a film declaration: {error}"
        raise FilmError(message) from error
    named = named_files(film)
    missing = [f"{field}: {path}" for field, path in named if not (root / path).is_file()]
    if missing:
        message = f"{DECLARATION} names missing files: {'; '.join(missing)}"
        raise FilmError(message)
    copied = copied_players(root, film)
    if copied:
        raise FilmError(copied)
    return film


FILM = load(repository.ROOT)
