"""Recognition units: how a transcript is compared with the text it should hold.

Recognition compares units: each Han character, and each case-folded run of Latin letters,
digits and apostrophes, so punctuation and capitals in a transcript never count as
differences. A recording's unit error rate is the unit edit distance between its text and its
transcript over the text's unit count.

A recognizer writes what it hears in the characters and the spelling it finds likeliest, so
units are also compared by reading (`reading_distance`), as a listener hears them:

- two Han characters are alike when they are the same character, or have the same reading in
  their own context, tone kept. A character's reading is the one the film's pronunciation
  contract declares for the word it stands in, or the reading of a word's spoken form where a
  `homophone` rule respells the word (`readings.compared_words`), and otherwise the
  dictionary's reading in context (`filmkit.narration.readings`). Chinese holds many
  characters to a sound: a transcript that reads 再 where the text has 在 holds what a listener
  heard;
- 的, 地 and 得 are alike where the text says one of them as a particle: its reading there is
  the neutral `de`, or it stands as a word of its own in the dictionary's division of the text
  and under no declared word. 地 in 土地 and 得 under a declared reading are no particles;
- two Latin units are alike when their letters and digits are, so an apostrophe is no
  difference (`check's` for `checks`), and adjacent Latin units are joined where the other side
  writes them as one (`back test` for `backtest`): spelling and spacing are the recognizer's;
- a Latin unit that says a term the film declares, its display form or its spoken form in any
  case, reads as that term, its possessive kept (`terms.said_form`): a respelling is how the
  narrator is told the name, and a recognizer writes the name in its own spelling;
- in the Chinese edition, a declared term is also alike one Latin unit of other letters that
  holds a letter and is no other Latin unit of the edition's script (`stands_for`): in Chinese
  speech a recognizer has no steady spelling for a foreign name, and the term line holds how
  it was said. A repeat, a trailing Latin word, digits, a Han word, another of the edition's
  names as the script spells it and a missing unit still differ; another word that is no Latin
  unit of the edition, and one of its names spelled otherwise, do not;
- a Latin unit and a Han character are never alike.

A number said and its digits (`ten`, `10`) stay different: neither the engine nor a film's
contract holds how a number is said.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, NamedTuple

import filmkit.languages as languages
import filmkit.narration.readings as readings
import filmkit.narration.terms as terms

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from filmkit.film import NarrationTerm

UNIT = re.compile(f"[{languages.pattern('han')}]|[a-z0-9']+")
HAN_UNIT = languages.compiled("han")
LETTER = re.compile(r"[a-z]")
# The particles a speaker says alike, whichever the recognizer writes, and their reading.
PARTICLES = frozenset("的地得")
PARTICLE_READING = "de"
# The most adjacent Latin units that are joined to meet one unit of the other side.
JOINED = 3


class Read(NamedTuple):
    """A recognition unit as it is heard.

    A Han character has its reading; a Latin unit has its letters and digits, or, where it says
    a declared term, `term` names the term and the reading is the letters of its spoken form,
    with an `s` for a possessive. `particle` says that the text says 的, 地 or 得 as a particle
    at this place.
    """

    unit: str
    reading: str
    particle: bool = False
    term: str | None = None

    @property
    def han(self) -> bool:
        return HAN_UNIT.fullmatch(self.unit) is not None


class Names(NamedTuple):
    """What an edition's Latin units are read by beside their letters: the terms the film
    declares (`filmkit.narration.terms`) and, in an edition whose language reads Latin script as
    another (`embedded`, `filmkit.languages.names_embedded`), the other Latin units its script
    says, by their letters and digits (`others`)."""

    terms: tuple[NarrationTerm, ...] = ()
    embedded: bool = False
    others: frozenset[str] = frozenset()


NO_NAMES = Names()


class Compared(NamedTuple):
    """A text and a transcript compared by reading: the fewest unit edits, and on one cheapest
    alignment each declared term and the transcript's unit of other letters that stood for it."""

    distance: int
    stood_for: tuple[tuple[str, str], ...] = ()


def recognition_units(text: str) -> list[str]:
    """Han characters and case-folded words of Latin letters, digits and apostrophes."""
    return UNIT.findall(text.lower())


def heard_phrase(heard: str, phrase: str) -> bool:
    """Whether a transcript holds the phrase's units contiguously and in order."""
    wanted, observed = recognition_units(phrase), recognition_units(heard)
    return bool(wanted) and any(
        observed[i : i + len(wanted)] == wanted for i in range(len(observed) - len(wanted) + 1)
    )


def unit_distance(
    expected: Sequence, observed: Sequence, alike: Callable[[object, object], bool] | None = None
) -> int:
    """The fewest unit insertions, deletions and substitutions between two sequences.

    Two units are the same when they are equal, or when `alike` says so.
    """
    row = list(range(len(observed) + 1))
    for i, want in enumerate(expected, 1):
        diagonal, row[0] = row[0], i
        for j, got in enumerate(observed, 1):
            differs = want != got if alike is None else not alike(want, got)
            diagonal, row[j] = (
                row[j],
                min(row[j] + 1, row[j - 1] + 1, diagonal + differs),
            )
    return row[-1]


def _latin(unit: str, word: str, declared: Sequence[NarrationTerm]) -> Read:
    """A Latin unit as it is heard: as the declared term it says where its whole `word` says it
    too (`terms.unit_says`), its possessive kept, or by its letters and digits."""
    for term in declared:
        said = terms.unit_says(unit, word, terms.spoken_forms(term))
        if said is not None:
            letters = "".join(recognition_units(term.spoken)).replace("'", "")
            return Read(unit, letters + ("s" if said[1] else ""), term=term.term)
    return Read(unit, unit.replace("'", ""))


def read_units(
    text: str, words: Sequence[readings.Word] = (), declared: Sequence[NarrationTerm] = ()
) -> list[Read]:
    """Each recognition unit of a text as it is heard.

    A Han character under a declared word takes that word's reading, and any other the
    dictionary's reading in its context. A Latin unit that says a declared term reads as it.
    """
    text = text.lower()
    covered, dictionary = readings.coverage(text, list(words)), readings.contextual(text)
    alone = {start for start, end in readings.segments(text) if end - start == 1}
    latin_words = [(w.start(), w.end(), w.group()) for w in terms.LATIN_WORD.finditer(text)]
    found = []
    for match in UNIT.finditer(text):
        unit, at = match.group(), match.start()
        if HAN_UNIT.fullmatch(unit) is None:
            letter = at + len(unit) - len(unit.lstrip("'"))
            word = next((w for start, end, w in latin_words if start <= letter < end), unit)
            found.append(_latin(unit, word, declared))
            continue
        word, _start, offset = covered.get(at, (None, 0, 0))
        reading = dictionary.get(at, unit) if word is None else word.syllables[offset]
        particle = unit in PARTICLES and (
            reading == PARTICLE_READING or (word is None and at in alone)
        )
        found.append(Read(unit, reading, particle))
    return found


def _letters(unit: Read) -> str:
    """A Latin unit's own letters and digits, whatever term it says."""
    return unit.unit.replace("'", "")


def alike(expected: Read, observed: Read) -> bool:
    """Whether a text's unit and a transcript's are the same to a listener."""
    if expected.han != observed.han:
        return False
    if not expected.han:
        # Units of the same letters and digits are alike whatever term either says.
        return _letters(expected) == _letters(observed) or expected.reading == observed.reading
    return (
        expected.unit == observed.unit
        or expected.reading == observed.reading
        or (expected.particle and observed.unit in PARTICLES)
    )


def _joined(units: Sequence[Read], end: int, other: Read) -> list[int]:
    """Each count of Latin units ending at `end` whose letters and digits spell `other`.

    The units are spelled by their readings and by their own letters, and either may meet
    either of `other`'s, so a term declared beside a word parts no two of the same letters.
    """
    if other.han:
        return []
    found, by_reading, by_letters = [], "", ""
    targets = {_letters(other), other.reading}
    for count in range(1, min(JOINED, end) + 1):
        unit = units[end - count]
        if unit.han:
            break
        by_reading = unit.reading + by_reading
        by_letters = _letters(unit) + by_letters
        if count > 1 and {by_reading, by_letters} & targets:
            found.append(count)
    return found


def edition_names(
    declared: Sequence[NarrationTerm], texts: Sequence[str], *, embedded: bool
) -> Names:
    """An edition's names: its declared terms and, where `embedded`, the Latin units its spoken
    texts say that say no term, by their letters and digits. They are recognition units, so a word
    such as `Node.js` gives two."""
    declared = tuple(declared)
    if not embedded:
        return Names(declared)
    others = {
        unit.reading
        for text in texts
        for unit in read_units(text, (), declared)
        if not unit.han and unit.term is None
    }
    return Names(declared, True, frozenset(others))


def stands_for(expected: Read, observed: Read, names: Names) -> bool:
    """Whether, in speech of a language that reads Latin script as another, a transcript's unit
    may stand for the text's declared term: a Latin unit that holds a letter, says no term and is
    no other Latin unit of the edition.

    A recognizer has no steady spelling for a foreign name in Chinese speech; how the term was
    said there is the term line's to judge (`filmkit.narration.terms`).
    """
    return (
        names.embedded
        and expected.term is not None
        and not observed.han
        and observed.term is None
        and LETTER.search(observed.reading) is not None
        and observed.reading not in names.others
    )


def _ways(want, got, i: int, j: int, cost: list[list[int]], names: Names) -> list[tuple]:
    """Each way into cell (i, j) of the cost table: its cost, the cell it leaves, and whether a
    unit of other letters stands there for a term. A way that holds both units alike comes
    first, so one cheapest alignment names such a unit only where nothing else is cheaper."""
    expected, observed = want[i - 1], got[j - 1]
    ways = [(cost[i - 1][j - 1] + (not alike(expected, observed)), i - 1, j - 1, False)]
    if stands_for(expected, observed, names):
        ways.append((cost[i - 1][j - 1], i - 1, j - 1, True))
    ways += [(cost[i - n][j - 1], i - n, j - 1, False) for n in _joined(want, i, observed)]
    ways += [(cost[i - 1][j - n], i - 1, j - n, False) for n in _joined(got, j, expected)]
    return [*ways, (cost[i - 1][j] + 1, i - 1, j, False), (cost[i][j - 1] + 1, i, j - 1, False)]


def compared(
    expected: str, observed: str, words: Sequence[readings.Word] = (), names: Names = NO_NAMES
) -> Compared:
    """A text and a transcript compared unit by unit, by reading (`reading_distance`)."""
    want = read_units(expected, words, names.terms)
    got = read_units(observed, words, names.terms)
    cost = [[0] * (len(got) + 1) for _ in range(len(want) + 1)]
    for i in range(len(want) + 1):
        for j in range(len(got) + 1):
            if not i or not j:
                cost[i][j] = i + j
                continue
            cost[i][j] = min(way[0] for way in _ways(want, got, i, j, cost, names))
    stood, i, j = [], len(want), len(got)
    while i and j:
        _, before_i, before_j, standing = next(
            way for way in _ways(want, got, i, j, cost, names) if way[0] == cost[i][j]
        )
        if standing:
            stood.append((want[i - 1].term, got[j - 1].unit))
        i, j = before_i, before_j
    return Compared(cost[-1][-1], tuple(reversed(stood)))


def reading_distance(
    expected: str, observed: str, words: Sequence[readings.Word] = (), names: Names = NO_NAMES
) -> int:
    """The fewest unit edits between a text and a transcript, units compared by reading.

    Adjacent Latin units that one side writes as one are joined at no cost, and in the Chinese
    edition one Latin unit of other letters may stand for a declared term (`stands_for`).
    `words` are the Chinese words compared by their readings, and `names` the edition's names.
    """
    return compared(expected, observed, words, names).distance
