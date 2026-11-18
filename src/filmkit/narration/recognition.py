"""Recognition units: how a transcript is compared with the text it should hold.

Recognition compares units: each Han character, and each case-folded run of Latin letters,
digits and apostrophes, so punctuation and capitals in a transcript never count as
differences. A recording's unit error rate is the unit edit distance between its text and its
transcript over the text's unit count.

A recognizer writes what it hears in the characters and the spelling it finds likeliest, so
units are also compared by reading (`reading_distance`), as a listener hears them:

- two Han characters are alike when they are the same character, or have the same reading in
  their own context, tone kept. A character's reading is the one the film's pronunciation
  contract declares for the word it stands in, and otherwise the dictionary's reading in
  context (`filmkit.narration.readings`). Chinese holds many characters to a sound: a
  transcript that reads 再 where the text has 在 holds what a listener heard;
- 的, 地 and 得 are alike where the text says one of them as a particle: its reading there is
  the neutral `de`, or it stands as a word of its own in the dictionary's division of the text
  and under no declared word. 地 in 土地 and 得 under a declared reading are no particles;
- two Latin units are alike when their letters and digits are, so an apostrophe is no
  difference (`check's` for `checks`), and adjacent Latin units are joined where the other side
  writes them as one (`back test` for `backtest`): spelling and spacing are the recognizer's;
- a Latin unit and a Han character are never alike.

A number said and its digits (`ten`, `10`) stay different: neither the engine nor a film's
contract holds how a number is said.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, NamedTuple

import filmkit.narration.readings as readings

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

UNIT = re.compile(r"[\u4e00-\u9fff]|[a-z0-9']+")
HAN_UNIT = re.compile(r"[\u4e00-\u9fff]")
# The particles a speaker says alike, whichever the recognizer writes, and their reading.
PARTICLES = frozenset("的地得")
PARTICLE_READING = "de"
# The most adjacent Latin units that are joined to meet one unit of the other side.
JOINED = 3


class Read(NamedTuple):
    """A recognition unit as it is heard.

    A Han character has its reading; a Latin unit has its letters and digits. `particle` says
    that the text says 的, 地 or 得 as a particle at this place.
    """

    unit: str
    reading: str
    particle: bool = False

    @property
    def han(self) -> bool:
        return HAN_UNIT.fullmatch(self.unit) is not None


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


def read_units(text: str, words: Sequence[readings.Word] = ()) -> list[Read]:
    """Each recognition unit of a text as it is heard.

    A Han character under a declared word takes that word's reading, and any other the
    dictionary's reading in its context.
    """
    text = text.lower()
    declared, dictionary = readings.coverage(text, list(words)), readings.contextual(text)
    alone = {start for start, end in readings.segments(text) if end - start == 1}
    found = []
    for match in UNIT.finditer(text):
        unit, at = match.group(), match.start()
        if HAN_UNIT.fullmatch(unit) is None:
            found.append(Read(unit, unit.replace("'", "")))
            continue
        word, _start, offset = declared.get(at, (None, 0, 0))
        reading = dictionary.get(at, unit) if word is None else word.syllables[offset]
        particle = unit in PARTICLES and (
            reading == PARTICLE_READING or (word is None and at in alone)
        )
        found.append(Read(unit, reading, particle))
    return found


def alike(expected: Read, observed: Read) -> bool:
    """Whether a text's unit and a transcript's are the same to a listener."""
    if expected.han != observed.han:
        return False
    if not expected.han:
        return expected.reading == observed.reading
    return (
        expected.unit == observed.unit
        or expected.reading == observed.reading
        or (expected.particle and observed.unit in PARTICLES)
    )


def _joined(units: Sequence[Read], end: int, other: Read) -> list[int]:
    """Each count of Latin units ending at `end` whose letters and digits spell `other`."""
    if other.han:
        return []
    found, spelled = [], ""
    for count in range(1, min(JOINED, end) + 1):
        unit = units[end - count]
        if unit.han:
            break
        spelled = unit.reading + spelled
        if count > 1 and spelled == other.reading:
            found.append(count)
    return found


def reading_distance(expected: str, observed: str, words: Sequence[readings.Word] = ()) -> int:
    """The fewest unit edits between a text and a transcript, units compared by reading.

    Adjacent Latin units that one side writes as one are joined at no cost.
    """
    want, got = read_units(expected, words), read_units(observed, words)
    cost = [[0] * (len(got) + 1) for _ in range(len(want) + 1)]
    for i in range(len(want) + 1):
        for j in range(len(got) + 1):
            if not i or not j:
                cost[i][j] = i + j
                continue
            ways = [
                cost[i - 1][j] + 1,
                cost[i][j - 1] + 1,
                cost[i - 1][j - 1] + (not alike(want[i - 1], got[j - 1])),
            ]
            ways += [cost[i - count][j - 1] for count in _joined(want, i, got[j - 1])]
            ways += [cost[i - 1][j - count] for count in _joined(got, j, want[i - 1])]
            cost[i][j] = min(ways)
    return cost[-1][-1]
