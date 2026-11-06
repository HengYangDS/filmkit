"""Whether each declared Latin-script term is spelled alike for the narrator and said alike.

A film declares in `[[narration.terms]]` each Latin-script term its narration says: the `term`,
the one `spoken` form that every language's normalization in the pronunciation contract must give
it, its pronunciation in `ipa`, and, for each edition that says it, a `reference` occurrence, by
`thought` and by `index`, its place from 0 among the term's occurrences in that thought, whose
take a person heard correct:

    [[narration.terms]]
    term = "NAME"
    spoken = "Naim"
    ipa = "ˈneɪm"
    reference = { zh = { thought = "01.6", index = 0 }, en = { thought = "03.7", index = 0 } }

The declaration lives in the film, not in the contract, whose SHA-256 binds every recording.

A narrator given two spellings of a term may say it two ways, so the readings check, which runs
before any narration, refuses a language whose normalization gives a declared term another spoken
form, or none (spelling parity). It also refuses a term an edition says without a reference, a
reference the edition's text does not hold, and a reference of an edition that never says the
term.

An aligned or written word says the term when, without a trailing possessive, it is the term or
its spoken form, in any case. Each occurrence's first vowel is the median first and second formant
of its voiced frames up to 32 % of the way into its aligned word, from up to one aligner frame
(80 ms) before the word's aligned start but never before the previous word's aligned end: the
pinned aligner places word boundaries on 80 ms frames and may leave the first vowel of a word that
begins with one unassigned after the word before it ("The Eethos mark" leaves its /iː/ between
"The" and ETHOS). The recording is low-passed and decimated to about 11 kHz and read in 25 ms
windows every 10 ms, the windows of at least 0.35 of the span's highest RMS are voiced, and a
voiced window's formants are the resonances of its order-12 LPC model, after 0.97 pre-emphasis
and a Hamming window, that lie between 200 Hz and 4 kHz and are narrower than 400 Hz, the lowest
two being F1 and F2. An occurrence is said unlike
its reference where its F1 exceeds 1.5 times the reference's or its F2 falls below 0.85 times:
an open vowel raises F1 and lowers F2, and the reference is the narrator's own, so no absolute
vowel target needs a calibration for each narrator. Each occurrence records both ratios.
Selection and assembly refuse an occurrence said unlike its reference, naming the occurrence and
both measurements, and a reference the narration does not hold; an audition prefers a take whose
occurrences are said like the reference.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from filmkit.narration.spoken_units import thought_spans
from filmkit.soundtrack.quiet import FRAME_SECONDS

if TYPE_CHECKING:
    from filmkit.film import NarrationTerm, TermReference
    from filmkit.narration.flow import Narrated, Recording

LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:['’.-][A-Za-z0-9]+)*")
POSSESSIVE = re.compile(r"['’]s$", re.IGNORECASE)
# The marks an aligned word may carry around its letters.
EDGE_MARKS = "\"'“”‘’()（）[]，。；：！？、,.;:!?"
# The first-vowel measure: the decimated rate and its filter, the share of the word, the window,
# the voicing share, the LPC model and the resonances that count as formants.
VOWEL_RATE = 11025
VOWEL_TAPS = 101
FIRST_SHARE = 0.32
WINDOW_SECONDS = 0.025
VOICED_SHARE = 0.35
LPC_ORDER = 12
PRE_EMPHASIS = 0.97
FORMANT_RANGE_HZ = (200, 4000)
BANDWIDTH_HZ = 400
# The frame on which the pinned aligner places word boundaries, which the first-vowel window may
# reach back over before a word's aligned start.
ALIGNER_FRAME_SECONDS = 0.08
# An occurrence is said like its reference while its F1 is at most this many times the
# reference's and its F2 at least this many times.
F1_RATIO = 1.5
F2_RATIO = 0.85


class TermError(ValueError):
    """A narration receipt or take does not hold a declared term's reference occurrence."""


def named(reference: TermReference) -> str:
    """A reference occurrence as the records name it: its thought and its index there."""
    return f"{reference.thought} #{reference.index}"


def spoken_forms(term: NarrationTerm) -> frozenset[str]:
    """The term and its declared spoken form, casefolded."""
    return frozenset({term.term.casefold(), term.spoken.casefold()})


def says(word: str, forms: frozenset[str]) -> bool:
    """Whether a word says a term: one of its forms, or that form's possessive."""
    return POSSESSIVE.sub("", word.strip(EDGE_MARKS)).casefold() in forms


def parity_failures(terms: tuple[NarrationTerm, ...], languages: dict, contract: str) -> list[str]:
    """Each language whose normalization gives a declared term another spoken form, or none.

    `languages` holds the pronunciation contract's languages by name, and `contract` names its
    file.
    """
    failures = []
    for term in terms:
        for language, declared in languages.items():
            forms = sorted(
                {
                    rule["spoken"]
                    for rule in declared.get("normalization", [])
                    if rule.get("display", "").casefold() == term.term.casefold()
                }
            )
            if forms == [term.spoken]:
                continue
            given = f"the spoken form {', '.join(forms)}" if forms else "no spoken form"
            failures.append(
                f"{contract}: the {language} normalization gives {term.term} {given}; the film "
                f"declares {term.spoken} in [[narration.terms]]"
            )
    return failures


def declaration_failures(
    terms: tuple[NarrationTerm, ...], thoughts: list[tuple[str, str]], code: str
) -> list[str]:
    """What an edition's text leaves without a reference, or stale, in the declared terms.

    `thoughts` holds each thought's name and text in narration order.
    """
    failures = []
    for term in terms:
        forms = spoken_forms(term)
        said = {
            where: sum(says(match.group(), forms) for match in LATIN_WORD.finditer(text))
            for where, text in thoughts
        }
        places = [where for where, count in said.items() if count]
        reference = term.reference.get(code)
        if reference is None and places:
            failures.append(
                f"{code}: {term.term} is said in {', '.join(places)} but declares no {code} "
                "reference occurrence"
            )
        elif reference is not None and not places:
            failures.append(
                f"{code}: {term.term} declares a reference for {code}, but the narration never "
                "says it"
            )
        elif reference is not None and said.get(reference.thought, 0) <= reference.index:
            failures.append(
                f"{code}: the {term.term} reference {named(reference)} is not in the narration; "
                f"{reference.thought} says it {said.get(reference.thought, 0)} times"
            )
    return failures


@dataclass(frozen=True)
class Vowel:
    """A first vowel's median F1 and F2, and the voiced frames they are the median of."""

    f1_hz: float
    f2_hz: float
    frames: int

    def ratios(self, reference: Vowel) -> tuple[float, float]:
        """This vowel's F1 and F2 as multiples of a reference vowel's."""
        return self.f1_hz / reference.f1_hz, self.f2_hz / reference.f2_hz

    def like(self, reference: Vowel) -> bool:
        """Whether this vowel is said like a reference: no more open, by F1 and by F2."""
        first, second = self.ratios(reference)
        return first <= F1_RATIO and second >= F2_RATIO

    def record(self, reference: Vowel | None = None) -> dict:
        """The vowel as a record states it, in whole hertz, with its ratios to a reference."""
        measured = {"f1_hz": round(self.f1_hz), "f2_hz": round(self.f2_hz), "frames": self.frames}
        if reference is None:
            return measured
        first, second = self.ratios(reference)
        return measured | {"f1_ratio": round(first, 3), "f2_ratio": round(second, 3)}


def lpc(frame: np.ndarray, order: int) -> np.ndarray | None:
    """The LPC polynomial of a frame by the autocorrelation method, or None where it is unstable."""
    size = len(frame)
    autocorrelation = np.correlate(frame, frame, mode="full")[size - 1 : size + order]
    model = np.zeros(order + 1)
    model[0] = 1.0
    error = autocorrelation[0]
    if error <= 0:
        return None
    for i in range(1, order + 1):
        reflection = -(autocorrelation[i] + model[1:i] @ autocorrelation[i - 1 : 0 : -1]) / error
        model[1 : i + 1] = model[1 : i + 1] + reflection * model[i - 1 :: -1][:i]
        error *= 1 - reflection * reflection
        if error <= 0:
            return None
    return model


def formants(frame: np.ndarray, rate: float) -> list[float]:
    """The resonances of a frame that count as formants, in Hz from the lowest."""
    emphasized = np.append(frame[0], frame[1:] - PRE_EMPHASIS * frame[:-1]) * np.hamming(len(frame))
    model = lpc(emphasized, LPC_ORDER)
    if model is None:
        return []
    found = []
    for root in np.roots(model):
        if np.imag(root) <= 0:
            continue
        hertz = float(np.angle(root) * rate / (2 * np.pi))
        bandwidth = float(-0.5 * rate / np.pi * np.log(abs(root)))
        if FORMANT_RANGE_HZ[0] < hertz < FORMANT_RANGE_HZ[1] and bandwidth < BANDWIDTH_HZ:
            found.append(hertz)
    return sorted(found)


def first_vowel(
    recording: Recording, start: float, end: float, after: float | None = None
) -> Vowel | None:
    """The first vowel of a word aligned from `start` to `end`.

    The window ends `FIRST_SHARE` of the way into the word. Given `after`, the aligned end of the
    word before it, the window begins up to `ALIGNER_FRAME_SECONDS` before `start`, never before
    `after`; without it the window begins at `start`. None where no voiced frame shows two
    formants.
    """
    step = max(1, round(recording.rate / VOWEL_RATE))
    rate = recording.rate / step
    hop, size = int(FRAME_SECONDS * rate), int(WINDOW_SECONDS * rate)
    opening = start if after is None else min(start, max(after, start - ALIGNER_FRAME_SECONDS, 0.0))
    begin, stop = int(opening * rate), int((start + FIRST_SHARE * (end - start)) * rate)
    starts = range(begin, max(begin + 1, stop - size), hop)
    available = len(recording.mono) // step
    samples = recording.lowpassed(
        VOWEL_TAPS, step, begin * step, min(starts[-1] + size, available) * step
    )
    frames = [samples[at - begin : at - begin + size] for at in starts]
    frames = [frame for frame in frames if len(frame) == size]
    if not frames:
        return None
    levels = [float(np.sqrt(np.mean(frame**2))) for frame in frames]
    first, second = [], []
    for frame, level in zip(frames, levels, strict=True):
        if level < VOICED_SHARE * max(levels):
            continue
        found = formants(frame, rate)
        if len(found) >= 2:
            first.append(found[0])
            second.append(found[1])
    if not first:
        return None
    return Vowel(float(np.median(first)), float(np.median(second)), len(first))


@dataclass(frozen=True)
class Occurrence:
    """A word that says a term: its thought, its place among them, where it is aligned, the
    aligned end of the word before it, if any, and the recording that speaks it."""

    thought: str
    index: int
    word: str
    start: float
    end: float
    after: float | None
    recording: Recording

    def vowel(self) -> Vowel | None:
        """The occurrence's first vowel."""
        return first_vowel(self.recording, self.start, self.end, self.after)


def said_in(words: list[dict], forms: frozenset[str]) -> list[dict]:
    """The words that say a term, in order."""
    return [word for word, _ in said_after(words, forms)]


def said_after(words: list[dict], forms: frozenset[str]) -> list[tuple[dict, float | None]]:
    """The words that say a term, in order, each with the end of the word before it, if any."""
    return [
        (word, words[i - 1]["end"] if i else None)
        for i, word in enumerate(words)
        if says(word["text"], forms)
    ]


def occurrences(item: Narrated, forms: frozenset[str]) -> list[Occurrence]:
    """Each occurrence of a term in a segment, numbered within its thought."""
    found = []
    for number, span in enumerate(thought_spans(item.text, item.words, item.groups)):
        words = [
            (item.words[i], item.words[i - 1]["end"] if i else None)
            for i in range(span.first, span.last + 1)
            if says(item.words[i]["text"], forms)
        ]
        found += [
            Occurrence(
                item.label(number),
                index,
                word["text"],
                word["start"],
                word["end"],
                after,
                item.recording,
            )
            for index, (word, after) in enumerate(words)
        ]
    return found


def outside(code: str, term: str, heard: Occurrence, vowel: Vowel | None, kept: tuple) -> str:
    """The refusal of an occurrence said unlike its reference, with both measurements.

    `kept` holds the reference and its vowel.
    """
    reference, standard = kept
    place = f"{code} {heard.thought} {term} #{heard.index} at {heard.start:.2f} s"
    against = (
        f"the reference {named(reference)}, F1 {standard.f1_hz:.0f} Hz and F2 "
        f"{standard.f2_hz:.0f} Hz"
    )
    if vowel is None:
        return f"{place}: its first vowel shows no two formants to compare with {against}"
    first, second = vowel.ratios(standard)
    return (
        f"{place}: its first vowel measures F1 {vowel.f1_hz:.0f} Hz and F2 {vowel.f2_hz:.0f} Hz, "
        f"{first:.2f} and {second:.2f} times those of {against}; an occurrence may reach "
        f"{F1_RATIO} times its F1 and {F2_RATIO} times its F2"
    )


def term_record(code: str, term: NarrationTerm, narrated: list[Narrated]) -> dict:
    """A term's reference and occurrences on an edition's narration, and every failure.

    Each occurrence records its first vowel, its ratios to the reference's and whether it is
    said like the reference.
    """
    forms = spoken_forms(term)
    found = [occurrence for item in narrated for occurrence in occurrences(item, forms)]
    record = {"term": term.term, "spoken": term.spoken, "ipa": term.ipa, "reference": None}
    record["occurrences"] = []
    reference = term.reference.get(code)
    if reference is None:
        failures = [
            f"{code}: {term.term} is said {len(found)} times but declares no {code} reference "
            "occurrence"
        ]
        return record | {"failures": failures if found else []}
    heard = next(
        (o for o in found if (o.thought, o.index) == (reference.thought, reference.index)), None
    )
    standard = heard.vowel() if heard else None
    if standard is None:
        reason = "is not in the narration" if heard is None else "shows no two formants"
        failure = f"{code}: the {term.term} reference {named(reference)} {reason}"
        return record | {"failures": [failure]}
    record["reference"] = {
        **reference.model_dump(),
        "at": round(heard.start, 2),
        **standard.record(),
    }
    failures = []
    for occurrence in found:
        vowel = occurrence.vowel()
        passes = vowel is not None and vowel.like(standard)
        record["occurrences"].append(
            {
                "thought": occurrence.thought,
                "index": occurrence.index,
                "at": round(occurrence.start, 2),
                **(vowel.record(standard) if vowel else {}),
                "passes": passes,
            }
        )
        if not passes:
            failures.append(outside(code, term.term, occurrence, vowel, (reference, standard)))
    return record | {"failures": failures}


@dataclass(frozen=True)
class Standard:
    """A declared term's spoken forms, its reference occurrence and that occurrence's vowel."""

    term: NarrationTerm
    forms: frozenset[str]
    reference: TermReference
    vowel: Vowel


def receipt_references(
    code: str, terms: tuple[NarrationTerm, ...], records: list[dict]
) -> list[tuple[NarrationTerm, frozenset[str], TermReference, dict]]:
    """Each declared term's reference in a narration receipt, with the thought take that says it.

    A reference whose thought take the receipt does not hold, or whose spoken text does not say
    the term often enough, is refused.
    """
    found = []
    for term in terms:
        reference = term.reference.get(code)
        if reference is None:
            continue
        forms = spoken_forms(term)
        record = next((record for record in records if record["id"] == reference.segment), {})
        number = int(reference.thought.rsplit(".", 1)[1])
        child = next(
            (
                child
                for child in record.get("utterance_groups", {}).get("records", [])
                if child["index"] == number
            ),
            None,
        )
        said = (
            0
            if child is None
            else sum(
                says(word.group(), forms) for word in LATIN_WORD.finditer(child["spoken_text"])
            )
        )
        if said <= reference.index:
            msg = (
                f"{code}: the {term.term} reference {named(reference)} is not in the narration "
                "receipt"
            )
            raise TermError(msg)
        found.append((term, forms, reference, child))
    return found


def take_terms(standards: list[Standard], words: list[dict], recording: Recording) -> dict:
    """Each occurrence of a declared term in a take of one thought, and whether all pass."""
    found = []
    for standard in standards:
        for index, (word, after) in enumerate(said_after(words, standard.forms)):
            vowel = first_vowel(recording, word["start"], word["end"], after)
            found.append(
                {
                    "term": standard.term.term,
                    "index": index,
                    "at": round(word["start"], 2),
                    **(vowel.record(standard.vowel) if vowel else {}),
                    "passes": vowel is not None and vowel.like(standard.vowel),
                }
            )
    return {"term_occurrences": found, "terms_pass": all(row["passes"] for row in found)}


def records(code: str, terms: tuple[NarrationTerm, ...], narrated: list[Narrated]) -> list[dict]:
    """Each declared term's record on an edition's narration."""
    return [term_record(code, term, narrated) for term in terms]


def refusals(code: str, terms: tuple[NarrationTerm, ...], narrated: list[Narrated]) -> list[str]:
    """What the gates refuse of the declared terms on an edition's narration."""
    return [failure for record in records(code, terms, narrated) for failure in record["failures"]]
