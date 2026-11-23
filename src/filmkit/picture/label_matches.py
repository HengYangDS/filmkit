"""Where a label's words are spoken in its scene: their exact occurrences and inflected ones.

A label's letters and digits, lowercased, are its units, and they occur exactly where its
scene's spoken units spell them. A label written in a language that declares a stemmer, as the
language registry reads the label in its edition (`languages.written_in`), is also found by
that stemmer's stems of its words, in order, among the words of one thought, so the English
"Availability" is found in "available" while "Publish" and "public" stay apart; English labels
of a Chinese edition are stemmed as English, since Chinese reads Latin script as English. Each
occurrence is its start, its end and the start of its clause; a clause opens after each stop of
the segment text. A segment whose
aligned words do not spell its text raises `PictureError`.
"""

from __future__ import annotations

import re
from itertools import accumulate

import snowballstemmer

import filmkit.languages as languages
import filmkit.narration.spoken_units as spoken_units
from filmkit.picture.rendering import PictureError

# Chinese commas close a clause; English commas mostly separate list items, so only
# stops and colons close one.
BOUNDARY = set(languages.characters("cue-boundaries"))
# A cue's and a label's words: each CJK character, or a run of other letters and digits with its
# apostrophes.
_CJK = languages.pattern("han")
_WORD = re.compile(rf"[{_CJK}]|[^\W_{_CJK}]+(?:['\u2019][^\W_{_CJK}]+)*")
# Each stemmer a language may declare, by its kind, as Snowball names its algorithm; it stems
# lowercase words.
STEMMERS = {"snowball-english": "english"}

# A scene's spoken units, each unit's start and end, and the unit its clause opens at.
SpokenIndex = tuple[str, list[float], list[float], list[int]]
# A spoken occurrence of a label's words: its start, its end and its clause's start, in seconds.
Occurrence = tuple[float, float, float]


def units(text: str) -> str:
    """A text's letters and digits, lowercased: the units labels and words are matched by."""
    return "".join(ch for ch in text if ch.isalnum()).lower()


def words(text: str) -> list[str]:
    """A text's words as a caption cue and a label are compared: lowercased, one apostrophe."""
    return [word.lower().replace("\u2019", "'") for word in _WORD.findall(text)]


def spoken_index(segment: dict) -> SpokenIndex:
    """A scene's normalized words, each unit's start and end, and its clause opening.

    A clause opens after each stop in the segment text, so the words must spell its text.
    """
    joined, starts, ends = [], [], []
    for word in segment["words"]:
        u = units(word["text"])
        joined.append(u)
        starts.extend([word["start"]] * len(u))
        ends.extend([word["end"]] * len(u))
    spoken = "".join(joined)
    opens, current, k = [], 0, 0
    for ch in segment.get("text", ""):
        if ch in BOUNDARY:
            current = k
        elif ch.isalnum():
            opens.append(current)
            k += 1
    if len(opens) != len(spoken) or spoken != units(segment.get("text", "")):
        msg = f"{segment['id']}: the aligned words do not cover the segment text"
        raise PictureError(msg)
    return spoken, starts, ends, opens


def occurrences(haystack: str, needle: str) -> list[int]:
    """Every start of `needle` in `haystack`, overlapping ones included."""
    found, at = [], haystack.find(needle)
    while at >= 0:
        found.append(at)
        at = haystack.find(needle, at + 1)
    return found


def exact_matches(index: SpokenIndex, needle: str) -> list[Occurrence]:
    """Every spoken occurrence of a label's units in its scene."""
    spoken, starts, ends, opens = index
    return [
        (starts[h], ends[h + len(needle) - 1], starts[opens[h]])
        for h in occurrences(spoken, needle)
    ]


def thought_words(segment: dict) -> list[tuple[int, int]]:
    """The first and last word of each thought of a segment.

    A segment without utterance groups is one thought.
    """
    groups = segment.get("utterance_groups", [segment["text"]])
    try:
        spans = spoken_units.thought_spans(segment["text"], segment["words"], groups)
    except spoken_units.AlignmentError as error:
        msg = f"{segment['id']}: {error}"
        raise PictureError(msg) from error
    return [(span.first, span.last) for span in spans]


def stemmer(label: str, code: str):
    """The stemmer of the language a label of an edition is written in, or None where that
    language declares none or the label is in no language the edition reads."""
    if not any(ch.isalpha() for ch in label):
        return None
    language = languages.written_in(label, code)
    kind = None if language is None else STEMMERS.get(language.stemmer)
    return None if kind is None else snowballstemmer.stemmer(kind)


def stems(text: str, stemming) -> list[str]:
    """The stems of a text's words by a stemmer."""
    return stemming.stemWords(words(text))


def inflected_matches(
    segment: dict, index: SpokenIndex, label: str, shown: float, stemming
) -> list[Occurrence]:
    """The occurrences of a label's words by their stems, in order, in the thought spoken at
    `shown`, or in the next thought when `shown` falls between thoughts."""
    spoken = segment["words"]
    thought = next(
        ((first, last) for first, last in thought_words(segment) if shown <= spoken[last]["end"]),
        None,
    )
    needle = stems(label, stemming)
    if thought is None or not needle:
        return []
    said = [
        (stem, k)
        for k in range(thought[0], thought[1] + 1)
        for stem in stems(spoken[k]["text"], stemming)
    ]
    # The unit each word begins at, whose clause the occurrence starts in.
    begins = list(accumulate((len(units(word["text"])) for word in spoken), initial=0))
    _, starts, _, opens = index
    n = len(needle)
    return [
        (
            spoken[said[i][1]]["start"],
            spoken[said[i + n - 1][1]]["end"],
            starts[opens[begins[said[i][1]]]],
        )
        for i in range(len(said) - n + 1)
        if [stem for stem, _ in said[i : i + n]] == needle
    ]
