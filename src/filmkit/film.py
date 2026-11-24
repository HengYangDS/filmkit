"""The film the engine builds: its declaration in `content/film.toml`, checked before any work.

The engine takes every film-specific value from this declaration and the files it names; each
edition's script declares the edition's title, author, language, frame rate and chapters, the
declaration states the credits' length once, and each edition lasts as long as its narration.
A declaration that is malformed, incomplete or names a missing file is refused with
each failing field. A cover is the exception: the engine paints it from the staged picture, so
a new film names its covers before they exist, and packaging requires them.
"""

from __future__ import annotations

import itertools
import tomllib
import unicodedata
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

import filmkit.declared_sources as declared_sources
import filmkit.languages as languages
import filmkit.repository as repository
from filmkit.places import CAST, SCRIPT, places

if TYPE_CHECKING:
    from pathlib import Path

DECLARATION = repository.DECLARATION
# The declaration's key that states the credits' length, once for every edition: the field
# `Film.credits_duration`, which a script no longer declares.
CREDITS = "credits_duration"
# The frame rate the engine renders and encodes every film at.
FPS = 60
# The keys of a timeline's segment that the engine derives from its chapter (`timeline_values`).
CHAPTER_VALUES = ("chapter_index", "chapter_title")
EDITION_FILES = (SCRIPT, CAST)


# The player template a sources folder once held; the engine renders each edition's player now.
PLAYER_TEMPLATE = "player.html"
# The key that named the delivery folder through 0.22.3, refused with the key that names it now.
RENAMED_FOLDER = "documents_folder"


# A lowercase name of words joined by hyphens.
Name = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
Floor = Annotated[int, Field(ge=0, le=100)]
# An edition's code: a BCP 47 primary subtag, which the film's `[editions.<code>]` tables declare
# and every exception and floor names (`Film.editions_declared`).
Code = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}$")]
# A voice-clarity floor in dB of cepstral peak prominence, and one for each edition.
ClarityFloor = Annotated[float, Field(gt=0, le=60)]
ClarityFloors = Annotated[dict[Code, ClarityFloor], Field(min_length=1)]
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
    """One edition: the summary its player shows under the film, and its caption terms. Its files
    stand at the places its code derives (`places`)."""

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
# A word a line of a language may not end on.
LeadWord = Annotated[str, StringConstraints(pattern=r"^\S+$")]


class WrappingException(Declared):
    """One wrapped label an edition keeps against the wrapping rules: its exact painted lines,
    top to bottom, and why they stay."""

    edition: Code
    lines: tuple[Stated, ...] = Field(min_length=2)
    reason: Stated


class Wrapping(Declared):
    """How the picture's wrapped labels break (`filmkit.picture.gates`).

    Among the lines of one size, a line other than the last spans at least `line_share` of the
    widest and the last at least `last_share`. `lead_words`, keyed by a language's code, adds the
    words a line of that language may not end on to those its declaration names
    (`filmkit.languages`). A label of an edition whose lines one of the edition's exceptions
    names is recorded with its reason instead of refused, and an exception that no frame of its
    edition paints is refused.
    """

    line_share: Share = 0.8
    last_share: Share = 0.6
    lead_words: dict[Code, tuple[LeadWord, ...]] = Field(default_factory=dict)
    exceptions: tuple[WrappingException, ...] = ()

    @field_validator("lead_words", mode="before")
    @classmethod
    def keyed_by_language(cls, words: object) -> object:
        """Refuse the former flat list, which named no language its words are lead words of."""
        if isinstance(words, list | tuple):
            message = (
                "picture.wrapping.lead_words is a list; key it by the language its words lead "
                f"in, as lead_words = {{ en = {list(words)!r} }}"
            )
            raise ValueError(message)
        return words

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

    edition: Code
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

    edition: Code
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

    `capture` is `fast`, the default, `screenshot` or `software`. It named how a browser
    captured the frames while a browser drew them. No render reads it now: the engine draws on
    a native canvas (`filmkit.picture.renderer`). It decides only how the uncaptioned picture is
    made: derived from the captioned one under `software`, rendered from its own stage under
    the others (`filmkit.picture.derivation.uncaptioned_way`).
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
# The severity of a finding that no review may hold, the one severity the engine names.
MATERIAL = "material"


# A thought by its segment and its number from 1, as "05.4".
ThoughtName = Annotated[str, StringConstraints(pattern=r"^[^.\s]+\.[1-9][0-9]*$")]


class ClarityException(Declared):
    """One thought of an edition that the film keeps under its clarity floor, and why."""

    edition: Code
    thought: ThoughtName
    reason: Stated


class Review(Declared):
    """The reviewer prompt, the verifier's floors and the scored dimensions.

    The dimensions keep their record order. The clarity floors, one for each edition,
    are what the review's measurement records each voice's clarity against (`review.clarity`).
    The floor holds for a soundtrack and its segments. A single thought varies about its segment,
    so a film may keep a thought under the floor by a `clarity_exceptions` entry, and with
    `clarity_thought_margin_db` states the line no kept thought may read under, the floor less
    that margin (`filmkit.preflight`). A margin of zero holds every thought to the floor
    itself, and such a film keeps none.
    The levels, 信, 达 and 雅 when the film declares them, each hold some of the dimensions,
    every dimension in exactly one; a review then passes level by level (`review.record`).
    `accepted_severities` lists the severities a review's findings may have, as the film's
    prompt defines them: a finding of any other severity, or of none, refuses the review, and an
    empty list accepts no finding. The list never holds `material`, in any letter case, and
    names no severity twice. A film that does not declare it keeps the engine's one rule, that
    no material finding remains.
    """

    prompt: str
    overall_minimum: Floor
    dimension_minimum: Floor
    dimensions: dict[str, str] = Field(min_length=1)
    clarity_minimum_db: ClarityFloors | None = None
    clarity_thought_margin_db: Annotated[float, Field(ge=0, le=6)] | None = None
    clarity_exceptions: tuple[ClarityException, ...] = ()
    levels: dict[LevelName, Level] | None = None
    accepted_severities: tuple[Stated, ...] | None = None

    @field_validator("accepted_severities")
    @classmethod
    def no_material_finding_accepted(
        cls, severities: tuple[str, ...] | None
    ) -> tuple[str, ...] | None:
        """Refuse a list that holds `material`, however it is cased, or one severity twice."""
        named = severities or ()
        if any(name.casefold() == MATERIAL for name in named):
            message = (
                f"no review may hold a {MATERIAL} finding, so the list never holds `{MATERIAL}`"
            )
            raise ValueError(message)
        twice = [name for name in dict.fromkeys(named) if named.count(name) > 1]
        if twice:
            message = f"review.accepted_severities names {', '.join(twice)} twice"
            raise ValueError(message)
        return severities

    @model_validator(mode="after")
    def thoughts_judged_against_a_declared_line(self) -> Review:
        """Refuse a thought line without the floors it is taken from, declared thoughts without
        that line or with a line that is the floor, and a thought declared twice in one edition."""
        if self.clarity_thought_margin_db is not None and self.clarity_minimum_db is None:
            message = "review.clarity_thought_margin_db needs review.clarity_minimum_db"
            raise ValueError(message)
        if self.clarity_exceptions and self.clarity_thought_margin_db is None:
            message = "review.clarity_exceptions needs review.clarity_thought_margin_db"
            raise ValueError(message)
        if self.clarity_exceptions and self.clarity_thought_margin_db == 0:
            message = (
                "review.clarity_exceptions keeps thoughts under the floor, and a "
                "review.clarity_thought_margin_db of 0 holds every thought to the floor: no "
                "thought can stand between the floor and itself"
            )
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

    edition: Code
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
    reference: dict[Code, TermReference] = Field(default_factory=dict)


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

    edition: Code
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


def form_key(place: str, form: str) -> tuple[str, str]:
    """A form at a place as the register check compares it: its letter case set aside."""
    return place, form.casefold()


class RegisterException(Declared):
    """One form the film keeps at one place against the register check (`filmkit.register`):
    the place as the check names it, the form as the check matched it, the text the form stands
    within there (a standard word or a quotation, holding the form and a letter or a digit beyond
    it), and why. The check excuses exactly the form's error-level occurrences that lie inside
    that text."""

    place: Stated
    form: Stated
    within: Stated
    reason: Stated

    @model_validator(mode="after")
    def within_holds_the_form(self) -> RegisterException:
        """Refuse a text that does not hold the form, or adds to it no letter or digit: a form
        and a mark (吧。) would keep the form wherever the mark follows it."""
        form, within = self.form.casefold(), self.within.casefold()
        at = within.find(form)
        beyond = within[:at] + within[at + len(form) :] if at >= 0 else ""
        if not any(unicodedata.category(character)[0] in "LN" for character in beyond):
            message = (
                f"{self.within!r} is no text the form stands within: it must hold {self.form!r}"
                " and a letter or a digit beyond it"
            )
            raise ValueError(message)
        return self

    @property
    def key(self) -> tuple[str, str]:
        """The form the exception keeps: its place and its form in any letter case."""
        return form_key(self.place, self.form)


class Register(Declared):
    """The forms the film keeps against the engine's register style, each within a text at one
    place.

    The forms are the engine's and the film adds none. An exception answers the error-level
    occurrences of its form that lie inside its text at its place; every other occurrence is
    refused, and an exception whose place does not hold its text is stale (`filmkit.register`).
    A warning stays the reviewers' to read and no exception removes it.
    """

    exceptions: tuple[RegisterException, ...] = ()

    @field_validator("exceptions")
    @classmethod
    def distinct_texts(
        cls, exceptions: tuple[RegisterException, ...]
    ) -> tuple[RegisterException, ...]:
        """Refuse two exceptions of one form within one text at one place, and two of one form at
        one place of which one text holds the other, which adds nothing."""
        keys = {(*e.key, e.within.casefold()) for e in exceptions}
        if len(keys) != len(exceptions):
            message = "two exceptions name the same form within one text at one place"
            raise ValueError(message)
        for first, second in itertools.combinations(exceptions, 2):
            texts = (first.within.casefold(), second.within.casefold())
            if first.key == second.key and (texts[0] in texts[1] or texts[1] in texts[0]):
                message = (
                    f"two exceptions of {first.form!r} at {first.place} name {first.within!r} and"
                    f" {second.within!r}, and one holds the other"
                )
                raise ValueError(message)
        return exceptions


class PronunciationSource(Declared):
    """A source that pronunciation targets cite: its id, and what the film records of it."""

    id: Stated
    provider: str | None = None
    families: tuple[str, ...] = ()
    qualification: str | None = None
    url: str | None = None
    bytes: int | None = None
    sha256: str | None = None


class Pronunciation(Declared):
    """What every edition's pronunciation shares, which binds no recording: the schema version
    the readings check holds the film to, the boundary of what its targets control, the criteria
    a listening accepts a reading by, and the sources that more than one edition's targets cite.
    Each edition's normalization, targets, own sources and status stand in its folder
    (`filmkit.narration.pronunciation`)."""

    schema_version: int
    control_boundary: Stated
    acceptance: tuple[Stated, ...] = Field(min_length=1)
    sources: tuple[PronunciationSource, ...] = ()


class Film(Declared):
    """A film: its file prefix, delivery folder, entry page, sources, the length of its credits,
    its editions, fonts, player colours and review.

    Its editions are the languages its `[editions.<code>]` tables name, in their order, one or
    more, each a language the engine declares (`filmkit.languages`); every exception, floor and
    term reference names one of them. A film may name a concept contract, which
    `filmkit.concepts` checks its narration against, and keep forms against its register
    (`filmkit.register`).
    """

    slug: Name
    delivery_folder: Name
    # The films' author, artist and copyright holder, stated once for every edition.
    author: Stated
    entry: str
    source_manifest: str
    # The credits' length in whole seconds, stated once: every edition draws them from one
    # composition, and each edition's assembly lays them out after its narration.
    credits_duration: Annotated[int, Field(strict=True, ge=0)]
    concepts: str | None = None
    editions: dict[Code, EditionDeclaration] = Field(min_length=1)
    picture: Picture
    player: Player
    review: Review
    pronunciation: Pronunciation | None = None
    narration: Narration = Field(default_factory=Narration)
    captions: Captions = Field(default_factory=Captions)
    # Declared as [register]: `register` would shadow the model class's own (ABCMeta's).
    formal_register: Register = Field(default_factory=Register, alias="register")

    @model_validator(mode="after")
    def editions_declared(self) -> Film:
        """Refuse an exception, a floor or a term reference that names an edition the film does
        not declare, and clarity floors without one for each declared edition."""
        named = {
            "picture.wrapping.exceptions": [e.edition for e in self.picture.wrapping.exceptions],
            "picture.motion.exceptions": [e.edition for e in self.picture.motion.exceptions],
            "picture.detail.exceptions": [e.edition for e in self.picture.detail.exceptions],
            "review.clarity_exceptions": [e.edition for e in self.review.clarity_exceptions],
            "review.clarity_minimum_db": list(self.review.clarity_minimum_db or {}),
            "narration.flow.exceptions": [e.edition for e in self.narration.flow.exceptions],
            "narration.terms": [code for t in self.narration.terms for code in t.reference],
            "captions.rate_exceptions": [e.edition for e in self.captions.rate_exceptions],
        }
        declared = ", ".join(self.editions)
        problems = [
            f"{field} names the edition {code}, which the film does not declare; it declares "
            f"{declared}"
            for field, codes in named.items()
            for code in dict.fromkeys(codes)
            if code not in self.editions
        ]
        floors = self.review.clarity_minimum_db
        problems += [
            f"review.clarity_minimum_db states no floor for {code}"
            for code in self.editions
            if floors is not None and code not in floors
        ]
        if problems:
            raise ValueError("; ".join(problems))
        return self


def timeline_values(script: dict, film: Film) -> dict:
    """A script with what the engine derives for its timeline (decision 10 of
    treat-languages-as-equals): the film's `author`, the engine's `fps` and each segment's
    `chapter_index` and `chapter_title`, from the script's `chapters` through the segment's
    `chapter`. A value the script still states is replaced, so nothing reads it; it loads nothing.

    Raises:
        ValueError: a segment names a chapter that the script's chapters do not hold.
    """
    chapters = {
        chapter["id"]: (index, chapter["title"])
        for index, chapter in enumerate(script.get("chapters", []))
    }
    unheld = [s["id"] for s in script["segments"] if s.get("chapter") not in chapters]
    if unheld:
        message = f"The script's chapters hold no chapter of segment {', '.join(unheld)}"
        raise ValueError(message)
    segments = [
        {**s, **dict(zip(CHAPTER_VALUES, chapters[s["chapter"]], strict=True))}
        for s in script["segments"]
    ]
    return {**script, "author": film.author, "fps": FPS, "segments": segments}


def edition_files(code: str, slug: str) -> tuple[str, ...]:
    """The files every edition holds at the places its code derives: its script, cast and
    pronunciation, and its reference recording."""
    edition = places(code, slug)
    return edition.script, edition.cast, edition.pronunciation, edition.reference


def named_files(film: Film, *, editions: bool = True) -> list[tuple[str, str]]:
    """Each file the declaration names or, unless `editions` is false, its editions derive (their
    script, cast, pronunciation and reference recording), except the covers, with the field that
    names it or the edition's table."""
    named = [
        ("entry", film.entry),
        ("source_manifest", film.source_manifest),
        ("review.prompt", film.review.prompt),
    ]
    for code in film.editions if editions else ():
        named += [(f"editions.{code}", path) for path in edition_files(code, film.slug)]
    named += [("picture.fonts", font) for font in film.picture.fonts]
    if film.concepts is not None:
        named.append(("concepts", film.concepts))
    return named


def copied_players(root: Path, film: Film) -> str | None:
    """Why a film's sources may not hold player pages of their own, naming each one and the
    declarations that replace it, or None when they hold none."""
    folders = [places(code, film.slug).folder for code in film.editions]
    pages = [
        f"{folder}/{PLAYER_TEMPLATE}"
        for folder in folders
        if (root / folder / PLAYER_TEMPLATE).is_file()
    ]
    if not pages:
        return None
    return (
        f"The engine renders each edition's player and reads no {', '.join(pages)}: declare "
        "the words each player shows as editions.<code>.summary and its colours in [player] "
        f"in {DECLARATION}, then remove the page"
    )


def read(root: Path) -> tuple[Film | None, list[str]]:
    """The declaration below a root and every problem it holds, the film None unless its fields
    load.

    A key renamed since 0.22.3 is a problem, and the fields are then judged as if it carried its
    new name, so the rename hides no other field; a withdrawn key of the declaration or of an
    edition's table is a problem, and the fields are judged as if it were absent. A declaration
    that states no `credits_duration` is refused in one line that says to declare it there; its
    other fields are judged as if it stated one, so that absence hides no other field, and the
    film is not loaded: the credits are never defaulted. The files the declaration names or its
    editions derive, and a player page left in an edition's folder, are judged only once the
    fields load.
    """
    try:
        declared = tomllib.loads((root / DECLARATION).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        return None, [f"{DECLARATION} is not a film declaration: {error}"]
    found = []
    if RENAMED_FOLDER in declared:
        found.append(
            f"{DECLARATION} declares {RENAMED_FOLDER}; the key is delivery_folder, the name "
            "of the film's folder below the delivery root, which is no longer ~/Documents"
        )
        renamed = declared.pop(RENAMED_FOLDER)
        declared.setdefault("delivery_folder", renamed)
    # An edition whose language the engine does not declare is named, and set aside so that its
    # absence hides no other field; the film is then not loaded.
    editions = declared.get("editions")
    unknown = (
        [code for code in editions if code not in languages.LANGUAGES]
        if isinstance(editions, dict)
        else []
    )
    for code in unknown:
        found.append(f"{DECLARATION} declares editions.{code}: {languages.unknown(code)}")
        editions.pop(code)
    found += declared_sources.placement_problems(root, declared)
    found += declared_sources.withdrawn_problems(root, declared, withdraw=True)
    found += declared_sources.prompt_problems(root, declared)
    found += declared_sources.entry_problems(root, declared)
    undeclared = CREDITS not in declared
    if undeclared:
        found.append(
            f"{DECLARATION} declares no {CREDITS}; declare the credits' length there once, in "
            "whole seconds"
        )
        declared[CREDITS] = 0
    try:
        film = Film.model_validate(declared)
    except ValidationError as error:
        return None, [*found, f"{DECLARATION} is not a film declaration: {error}"]
    # Each edition's files were judged before the fields (`declared_sources.placement_problems`).
    named = named_files(film, editions=False)
    missing = [f"{field}: {path}" for field, path in named if not (root / path).is_file()]
    if missing:
        found.append(f"{DECLARATION} names missing files: {'; '.join(missing)}")
    copied = copied_players(root, film)
    if copied:
        found.append(copied)
    return (None if undeclared or unknown else film), found


def problems(root: Path) -> list[str]:
    """Every problem of the declaration below a root; none when it loads."""
    return read(root)[1]


def load(root: Path) -> Film:
    """Read and check the declaration below a root, refusing it with every problem it holds."""
    film, found = read(root)
    if found or film is None:
        raise FilmError("\n".join(found))
    return film


def __getattr__(name: str) -> Film:
    """`FILM`, the film at the engine's root, loaded when a module first asks for it: a command
    that reports a declaration's problems imports this module before the declaration loads."""
    if name != "FILM":
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    film = load(repository.ROOT)
    globals()["FILM"] = film
    return film
