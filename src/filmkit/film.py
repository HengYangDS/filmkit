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
    model_validator,
)

import filmkit.repository as repository

if TYPE_CHECKING:
    from pathlib import Path

DECLARATION = repository.DECLARATION
# The files every edition's sources folder holds.
EDITION_FILES = ("film-script.json", "voice-reference.json")
# The player template a sources folder once held; the engine renders each edition's player now.
PLAYER_TEMPLATE = "player.html"
# The key that named the delivery folder through 0.22.3, refused with the key that names it now.
RENAMED_FOLDER = "documents_folder"
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


class MotionException(Declared):
    """One motion finding an edition keeps against the motion gate: its scene, the composition's
    `source`, the line that drew it as `film.js:<line>` or its module, its kind and why it stays."""

    edition: Literal["zh", "en"]
    scene: Stated
    source: Annotated[str, StringConstraints(pattern=r"^(film\.js:[1-9][0-9]*|[^\s:]+\.m?js)$")]
    kind: Literal["halt", "start", "race", "pop", "jump", "dash", "pace"]
    reason: Stated


class Motion(Declared):
    """The motion findings the film keeps (`filmkit.picture.gates`).

    A finding of an edition that one of the edition's exceptions names by its scene, its line or
    module and its kind is recorded with the reason instead of refused, and an exception that no
    finding of its edition matches is refused.

    `pace_limit` is the fastest a glide or a flow may move, in px/s at 1080p, from the line of
    450 at which the motion audit records a stretch to under the 900 at which it calls a race.
    Reviews hold films of a calm register to 450 and have accepted faster glides in others, so
    the limit is the film's to declare: without one a stretch over 450 is recorded, with one a
    stretch whose peak exceeds it is refused.
    """

    exceptions: tuple[MotionException, ...] = ()
    pace_limit: Annotated[float, Field(ge=450, lt=900)] | None = None

    @field_validator("exceptions")
    @classmethod
    def distinct_findings(
        cls, exceptions: tuple[MotionException, ...]
    ) -> tuple[MotionException, ...]:
        """Refuse two exceptions of one motion."""
        keys = [(e.edition, e.scene, e.source, e.kind) for e in exceptions]
        if len(set(keys)) != len(keys):
            message = "two exceptions name the same motion of one edition"
            raise ValueError(message)
        return exceptions


class DetailException(Declared):
    """One finding of the detail audit an edition keeps: its kind, its scene, optionally the
    `source` that names it within the scene, and why it stays.

    The source is a rail's list for `rail`, the line that drew the call as `film.js:<line>` or
    its module for `ink_drop`, the text for `outside_pace`, the thought whose quiet holds the
    stroke for `part_drawn` and the side, `left` or `right`, for `off_centre_far`; without one
    the exception names every finding of its kind in the scene. A `racing_tip` is named by its
    scene alone, since the cue that keys a stroke moves with every fit of the runtime.
    """

    edition: Literal["zh", "en"]
    kind: Literal["ink_drop", "outside_pace", "part_drawn", "racing_tip", "rail", "off_centre_far"]
    scene: Stated
    source: Stated | None = None
    reason: Stated

    @model_validator(mode="after")
    def source_of_its_kind(self) -> DetailException:
        """Refuse a source that no finding of the kind can carry."""
        allowed = {"racing_tip": (None,), "off_centre_far": (None, "left", "right")}
        if self.source not in allowed.get(self.kind, (self.source,)):
            message = f"a {self.kind} exception cannot name the source {self.source!r}"
            raise ValueError(message)
        return self


class Detail(Declared):
    """The detail audit's findings the film keeps (`filmkit.picture.detail_gates`): a finding
    that an exception of its edition names is recorded with the reason instead of refused, and
    an exception that no finding of its edition matches is refused."""

    exceptions: tuple[DetailException, ...] = ()

    @field_validator("exceptions")
    @classmethod
    def distinct_findings(
        cls, exceptions: tuple[DetailException, ...]
    ) -> tuple[DetailException, ...]:
        """Refuse two exceptions of one finding."""
        keys = [(e.edition, e.kind, e.scene, e.source) for e in exceptions]
        if len(set(keys)) != len(keys):
            message = "two exceptions name the same detail finding of one edition"
            raise ValueError(message)
        return exceptions


class Picture(Declared):
    """The font files the picture stages below fonts/, in their order, how its wrapped labels
    break, the motion and the detail findings it keeps, whether it makes drafts, and how the
    renderer captures its frames.

    `drafts` says whether the film renders a 10 fps draft of each edition and scans it for still
    pictures (`filmkit.picture.draft`): `preflight` asks for that scan only of a film that
    declares them, since `check-picture` audits every frame.

    `capture` is `fast`, the default, which turns the renderer's fast capture on as earlier
    releases did; `screenshot`, which turns it off; or `software`, which draws the frames in the
    browser's software rasterizer instead of the host's GPU and captures them by screenshot
    (`filmkit.picture.rendering`).
    """

    fonts: tuple[str, ...] = Field(min_length=1)
    wrapping: Wrapping = Field(default_factory=Wrapping)
    motion: Motion = Field(default_factory=Motion)
    detail: Detail = Field(default_factory=Detail)
    drafts: bool = False
    capture: Literal["fast", "screenshot", "software"] = "fast"

    @field_validator("fonts")
    @classmethod
    def distinct_names(cls, fonts: tuple[str, ...]) -> tuple[str, ...]:
        """Refuse two fonts of one file name, which would stage as one file."""
        names = [PurePosixPath(font).name for font in fonts]
        if len(set(names)) != len(names):
            message = "fonts stage below fonts/ by file name, and these stage two fonts as one file"
            raise ValueError(message)
        return fonts


class Level(Declared):
    """One level of a film's review: what it asks of the whole film and the dimensions it holds."""

    asks: Stated
    dimensions: tuple[Stated, ...] = Field(min_length=1)


# The levels a film's review may declare, in the order a viewer meets them: faithful, conveyed,
# graceful.
LEVELS = ("信", "达", "雅")
LevelName = Literal["信", "达", "雅"]


# A thought by its segment and its number from 1, as "05.4".
ThoughtName = Annotated[str, StringConstraints(pattern=r"^[^.\s]+\.[1-9][0-9]*$")]


class ClarityException(Declared):
    """One thought of an edition that the film keeps under its clarity floor, and why."""

    edition: Literal["zh", "en"]
    thought: ThoughtName
    reason: Stated


class Review(Declared):
    """The reviewer prompt, the verifier's floors, the scored dimensions and the plan readings.

    The dimensions keep their record order. The readings file holds the listening plan's
    analyst readings; without one the plan adds none. The clarity floors, one for each edition,
    are what the review's measurement records each voice's clarity against (`review.clarity`).
    The floor holds for a soundtrack and its segments. A single thought varies about its segment,
    so a film may keep a thought under the floor by a `clarity_exceptions` entry, and with
    `clarity_thought_margin_db` states the line no kept thought may read under, the floor less
    that margin (`filmkit.preflight`).
    The levels, 信, 达 and 雅 when the film declares them, each hold some of the dimensions,
    every dimension in exactly one; a review then passes level by level (`review.record`).
    """

    prompt: str
    overall_minimum: Floor
    dimension_minimum: Floor
    dimensions: dict[str, str] = Field(min_length=1)
    readings: str | None = None
    clarity_minimum_db: ClarityFloors | None = None
    clarity_thought_margin_db: Annotated[float, Field(gt=0, le=6)] | None = None
    clarity_exceptions: tuple[ClarityException, ...] = ()
    levels: dict[LevelName, Level] | None = None

    @model_validator(mode="after")
    def thoughts_judged_against_a_declared_line(self) -> Review:
        """Refuse a thought line without the floors it is taken from, declared thoughts without
        that line, and a thought declared twice in one edition."""
        if self.clarity_thought_margin_db is not None and self.clarity_minimum_db is None:
            message = "review.clarity_thought_margin_db needs review.clarity_minimum_db"
            raise ValueError(message)
        if self.clarity_exceptions and self.clarity_thought_margin_db is None:
            message = "review.clarity_exceptions needs review.clarity_thought_margin_db"
            raise ValueError(message)
        names = [(e.edition, e.thought) for e in self.clarity_exceptions]
        if len(set(names)) != len(names):
            message = "review.clarity_exceptions names a thought of one edition twice"
            raise ValueError(message)
        return self

    @model_validator(mode="after")
    def every_dimension_in_one_level(self) -> Review:
        """Refuse levels that are not all three, or that miss, repeat or invent a dimension."""
        if self.levels is None:
            return self
        if tuple(self.levels) != LEVELS:
            message = f"review.levels declares {', '.join(LEVELS)} in this order"
            raise ValueError(message)
        held = [name for level in self.levels.values() for name in level.dimensions]
        problems = [f"{name} stands in no level" for name in self.dimensions if name not in held]
        problems += [
            f"{name} stands in two levels" for name in dict.fromkeys(held) if held.count(name) > 1
        ]
        problems += [
            f"{name} is no declared dimension" for name in held if name not in self.dimensions
        ]
        if problems:
            message = "review.levels: " + "; ".join(problems)
            raise ValueError(message)
        return self


# The longest heard pause a word boundary without a mark may hold, in seconds.
PauseLimit = Annotated[float, Field(gt=0, le=2)]
# A declared word or reason: text that holds more than whitespace.
FlowText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
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


class RateException(Declared):
    """One caption cue of an edition that the film keeps above the reading rate: its text as the
    assembly record states it, and why."""

    edition: Literal["zh", "en"]
    text: Stated
    reason: Stated


class Captions(Declared):
    """The caption cues above the reading rate that the film keeps (`filmkit.preflight`)."""

    rate_exceptions: tuple[RateException, ...] = ()

    @field_validator("rate_exceptions")
    @classmethod
    def distinct_cues(cls, cues: tuple[RateException, ...]) -> tuple[RateException, ...]:
        """Refuse two exceptions of one cue."""
        names = [(e.edition, e.text) for e in cues]
        if len(set(names)) != len(names):
            message = "captions.rate_exceptions names a cue of one edition twice"
            raise ValueError(message)
        return cues


class Film(Declared):
    """A bilingual film: its file prefix, delivery folder, entry page, sources, fonts, player
    colours and review.

    A film may name a concept contract, which `filmkit.concepts` checks its narration against.
    """

    slug: Name
    delivery_folder: Name
    entry: str
    source_manifest: str
    concepts: str | None = None
    editions: dict[Literal["zh", "en"], EditionDeclaration] = Field(min_length=2)
    picture: Picture
    player: Player
    review: Review
    narration: Narration = Field(default_factory=Narration)
    captions: Captions = Field(default_factory=Captions)


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
        declared = tomllib.loads((root / DECLARATION).read_text(encoding="utf-8"))
        if RENAMED_FOLDER in declared:
            message = (
                f"{DECLARATION} declares {RENAMED_FOLDER}; the key is delivery_folder, the name "
                "of the film's folder below the delivery root, which is no longer ~/Documents"
            )
            raise FilmError(message)
        film = Film.model_validate(declared)
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
