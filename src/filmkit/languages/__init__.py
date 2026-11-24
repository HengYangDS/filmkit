"""The languages the engine builds an edition in, each declared once beside this module.

A film's editions are the languages its declaration names (`filmkit.film`), in its order; the
engine admits an edition whose code has a declaration here, `<code>.toml`, and refuses any other
in one line that names the languages it declares. Each declaration holds every value and choice
specific to its language: its tags and names, the scripts it writes and the language it reads
each other script in, whether spaces delimit its words, its unit of speech, how it marks number,
its captions, reading checks, how a transcript's Latin-script words are heard, stemmer, lead
words, register rules and player words. A behaviour that more than one language could share stays
once in code, named by its basis, and a declaration chooses it by that name; a declaration that
names a kind the engine does not hold, or that misses or adds a field, is refused when it loads,
naming the language and the field.

The classes of characters the engine reads, its scripts and its marks, stand once in
`scripts.json`, which this module and the Node audits (`scripts.mjs`) both read.
"""

from __future__ import annotations

import json
import re
import tomllib
from functools import cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

FOLDER = Path(__file__).parent
# The data file of the engine's classes of characters.
SCRIPTS_FILE = FOLDER / "scripts.json"
# The register's rules, one Vale rule file each (`filmkit.register`).
REGISTER_RULES = FOLDER.parent / "register/styles/register"

# The kinds of reading check a language may declare: its Han characters read by pypinyin's Mandarin
# readings, and its stress targets held to CMUdict's ARPAbet.
PINYIN_READINGS, CMUDICT_STRESS = "pinyin-readings", "cmudict-stress"
# A language's code: a BCP 47 primary subtag of two or three lowercase letters.
Code = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}$")]
Stated = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Word = Annotated[str, StringConstraints(pattern=r"^\S+$")]


class LanguageError(ValueError):
    """A language the engine holds no declaration for, or a declaration it cannot load."""


class Declared(BaseModel):
    """A declared table: every field is stated and known, and none changes after loading."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Counted(Declared):
    """A language that marks no grammatical number: a clause carries a term's number by one of
    its number words, or by a numeral of its numerals counting with one of its classifiers before
    the term, a lone `singular` stating one (`filmkit.concepts`)."""

    kind: Literal["counted-by-words"]
    words: tuple[Stated, ...] = Field(min_length=1)
    numerals: Stated
    classifiers: Stated
    singular: Stated


class Suffixed(Declared):
    """A language that marks number by inflection: a term's plural is the term with a suffix."""

    kind: Literal["plural-suffix"]
    suffixes: tuple[Word, ...] = Field(min_length=1)


class Captions(Declared):
    """How a language's captions are phrased (`filmkit.captions.phrasing`) and timed: the most
    characters a line holds, the most characters a second a cue is read at, or `none`, and the
    hold a script may declare, or `none` (`filmkit.captions.timing`)."""

    phrasing: Literal["full-width-punctuation", "english-grammar"]
    limit: Annotated[int, Field(gt=0)]
    reading_rate: Annotated[int, Field(gt=0)] | Literal["none"]
    hold: Literal["full-interval", "none"]


class PlayerWords(Declared):
    """The words of a language's player page and of its line on the entry page
    (`filmkit.delivery.player`)."""

    version: Stated
    versions: Stated
    viewing: Stated
    uhd: Stated
    captions: Stated
    captions_on: Stated
    captions_off: Stated
    track: Stated
    chapters: Stated
    transcript: Stated
    files: Stated
    film: Stated
    viewing_film: Stated
    uhd_film: Stated
    drawn: Stated
    undrawn: Stated
    downloads: Stated
    labelled: Stated
    to_download: Stated
    for_players: Stated
    script: Stated
    cover: Stated
    languages: Stated
    entry: Stated
    play_from: Stated
    unplayable: Stated


class Language(Declared):
    """One language's declaration, under its code.

    `tag` is its BCP 47 tag and `iso639_2` its ISO 639-2 code; `english_name` is the name the
    speech models take and `name` the one it shows itself by; `byline` follows the author and
    the name in a transcript, `{minutes}` standing for the runtime. `scripts` names the scripts
    it writes and `embedded` the language it reads each other script in, both by the scripts of
    `scripts.json`. `spaced` says whether spaces delimit its words; `unit` is what its speech is
    counted in. `readings` names its reading checks, `latin_heard` how a transcript's Latin-script
    words are heard, `stemmer` the stemmer that finds a label's words in other forms, or `none`,
    and `lead_words` the words a wrapped line other than the last may not end on. `rules`,
    declared as `register`, names the register's rules its words meet.
    """

    code: Code
    tag: Annotated[str, StringConstraints(pattern=r"^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8})*$")]
    iso639_2: Annotated[str, StringConstraints(pattern=r"^[a-z]{3}$")]
    english_name: Stated
    name: Stated
    byline: Annotated[str, StringConstraints(pattern=r"\{minutes\}")]
    scripts: tuple[str, ...] = Field(min_length=1)
    embedded: dict[str, Code]
    spaced: bool
    unit: Literal["characters", "words"]
    number: Annotated[Counted | Suffixed, Field(discriminator="kind")]
    captions: Captions
    readings: tuple[Literal["pinyin-readings", "cmudict-stress"], ...]
    latin_heard: Literal["letters", "cmudict-pronunciations"]
    stemmer: Literal["snowball-english", "none"]
    lead_words: tuple[Word, ...]
    # Declared as `register`, which would shadow the model class's own (ABCMeta's).
    rules: tuple[str, ...] = Field(min_length=1, alias="register")
    player: PlayerWords

    @field_validator("scripts")
    @classmethod
    def known_scripts(cls, scripts: tuple[str, ...]) -> tuple[str, ...]:
        """Refuse a script that `scripts.json` does not define, or one named twice."""
        unknown = [name for name in scripts if name not in classes()["scripts"]]
        if unknown or len(set(scripts)) != len(scripts):
            message = f"scripts names {', '.join(unknown) or 'a script twice'}: {script_names()}"
            raise ValueError(message)
        return scripts

    @field_validator("rules")
    @classmethod
    def known_rules(cls, rules: tuple[str, ...]) -> tuple[str, ...]:
        """Refuse a rule the register does not hold, or one named twice."""
        held = sorted(path.stem for path in REGISTER_RULES.glob("*.yml"))
        unknown = [rule for rule in rules if rule not in held]
        if unknown or len(set(rules)) != len(rules):
            message = (
                f"register names {', '.join(unknown) or 'a rule twice'}; the register holds "
                f"{', '.join(held)}"
            )
            raise ValueError(message)
        return rules

    @model_validator(mode="after")
    def other_scripts_embedded(self) -> Language:
        """Refuse an embedded script that the language writes itself or that is no script."""
        wrong = [name for name in self.embedded if name in self.scripts]
        wrong += [name for name in self.embedded if name not in classes()["scripts"]]
        if wrong:
            message = (
                f"embedded names {', '.join(wrong)}, which is no other script: {script_names()}"
            )
            raise ValueError(message)
        return self


def script_names() -> str:
    """The scripts `scripts.json` defines, as a refusal names them."""
    return "the scripts are " + ", ".join(classes()["scripts"])


@cache
def classes() -> dict[str, dict[str, dict]]:
    """The classes of `scripts.json`, by group (`scripts`, `marks`) and name."""
    data = json.loads(SCRIPTS_FILE.read_text(encoding="utf-8"))
    return {group: data[group] for group in ("scripts", "marks")}


def _entry(name: str) -> dict:
    """A class of `scripts.json` by its name, refused when the file holds none of that name."""
    for group in classes().values():
        if name in group:
            return group[name]
    message = f"scripts.json holds no class {name}"
    raise LanguageError(message)


def characters(name: str) -> str:
    """The characters a class of marks names, in the file's order."""
    entry = _entry(name)
    if "characters" not in entry:
        message = f"scripts.json defines {name} by its ranges, not by its characters"
        raise LanguageError(message)
    return entry["characters"]


def pattern(*names: str) -> str:
    """The body of a regular expression's character class that holds exactly the members of the
    named classes."""
    body = []
    for name in names:
        entry = _entry(name)
        if "of" in entry:
            body.append(pattern(*entry["of"]))
            continue
        if "characters" in entry:
            body += [re.escape(character) for character in entry["characters"]]
            continue
        for span in entry["ranges"]:
            first, last = (chr(int(point, 16)) for point in span.split("-"))
            body.append(
                re.escape(first) if first == last else f"{re.escape(first)}-{re.escape(last)}"
            )
    return "".join(body)


@cache
def compiled(*names: str) -> re.Pattern[str]:
    """A regular expression that matches one character of the named classes."""
    return re.compile(f"[{pattern(*names)}]")


def parse(code: str, data: dict) -> Language:
    """A language's declaration from its data, refused with its code and every failing field.
    Its code is its file's name, which the declaration does not state again."""
    if "code" in data:
        message = f"The language declaration {code}.toml states code; its file's name is its code"
        raise LanguageError(message)
    try:
        return Language.model_validate({**data, "code": code})
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in item['loc']) or 'the declaration'}: {item['msg']}"
            for item in error.errors()
        )
        message = f"The language declaration {code}.toml cannot load: {problems}"
        raise LanguageError(message) from None


def load(folder: Path = FOLDER) -> dict[str, Language]:
    """Every declaration of a folder, by code in the order of their names, refusing a
    declaration that does not load and an embedded language that no declaration holds."""
    found = {}
    for path in sorted(folder.glob("*.toml")):
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            message = f"The language declaration {path.name} cannot load: {error}"
            raise LanguageError(message) from None
        found[path.stem] = parse(path.stem, data)
    for language in found.values():
        missing = sorted(set(language.embedded.values()) - set(found))
        if missing:
            message = (
                f"The language declaration {language.code}.toml reads a script in "
                f"{', '.join(missing)}, which no declaration holds"
            )
            raise LanguageError(message)
    return found


# The languages the engine holds, by code. Tests add their own languages here.
LANGUAGES = load()


def language(code: str) -> Language:
    """The declaration of a language, refused in one line that names those the engine holds."""
    try:
        return LANGUAGES[code]
    except KeyError:
        message = unknown(code)
        raise LanguageError(message[0].upper() + message[1:]) from None


def checks(code: str, kind: str) -> bool:
    """Whether a language declares a kind of reading check."""
    return kind in language(code).readings


def names_embedded(code: str) -> bool:
    """Whether a language reads Latin script as another language (its `embedded`), so that every
    Latin word its narration says is a name: one its pronunciation lists among its embedded
    targets, and one recognition reads as a name and not by a reading of its own."""
    return "latin" in language(code).embedded


def named(english_name: str) -> Language:
    """The declared language that the speech models take by this name, as a contract keys its
    part, refused when no declaration takes it."""
    found = [held for held in LANGUAGES.values() if held.english_name == english_name]
    if len(found) != 1:
        message = f"No one language declaration takes the name {english_name!r}"
        raise LanguageError(message)
    return found[0]


def scripts_in(text: str) -> list[str]:
    """The scripts of `scripts.json` that a text holds a character of, in the file's order."""
    return [name for name in classes()["scripts"] if compiled(name).search(text)]


def written_in(text: str, code: str) -> Language | None:
    """The language a text of an edition is written in (design decision 5): the edition's own
    where the text holds a character of a script that language writes, else the language that
    it reads the text's script in, else none: such a text is matched exactly and wrapped by no
    language's rule."""
    edition, held = language(code), scripts_in(text)
    if any(script in edition.scripts for script in held):
        return edition
    embedded = [edition.embedded[script] for script in held if script in edition.embedded]
    return language(embedded[0]) if embedded else None


def read_in(text: str, code: str) -> list[Language]:
    """Every language whose words a text of an edition holds: the edition's own, and the language
    it reads each other script of the text in, in that order."""
    edition = language(code)
    found = [edition]
    for script in scripts_in(text):
        named = edition.embedded.get(script)
        if named is not None and language(named) not in found:
            found.append(language(named))
    return found


def model_names() -> list[str]:
    """Each declared language's name as the speech models take it, in the order of the codes."""
    return [LANGUAGES[code].english_name for code in sorted(LANGUAGES)]


def unknown(code: str) -> str:
    """Why a code is no language: the languages the engine declares, named."""
    return (
        f"the engine holds no language declaration for {code!r}; it declares "
        f"{', '.join(sorted(LANGUAGES))}"
    )
