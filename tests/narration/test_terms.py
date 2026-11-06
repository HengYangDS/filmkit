"""Declared Latin-script terms: their spelling for the narrator, and how each occurrence sounds."""

import numpy as np
import pytest

import filmkit.narration.flow as flow
import filmkit.narration.terms as terms
from filmkit.film import NarrationTerm

# Two vowels by their four formants and bandwidths in Hz: /iː/ as in "ether" and /ɛ/ as in "ever".
CLOSE = ((280, 70), (2700, 120), (3300, 200), (3900, 250))
OPEN = ((620, 80), (1950, 120), (2700, 200), (3600, 250))


def recursive(signal: np.ndarray, first: float, second: float = 0.0) -> np.ndarray:
    """A signal through a recursive filter of one or two poles."""
    out = np.zeros_like(signal)
    for i in range(len(signal)):
        out[i] = (
            signal[i] + first * (out[i - 1] if i else 0) + second * (out[i - 2] if i > 1 else 0)
        )
    return out


def vowel(formants, seconds: float, rate: int, f0: float = 120.0) -> np.ndarray:
    """A voiced vowel: a falling pulse train at f0 through a resonator for each formant."""
    pulses = np.zeros(round(seconds * rate))
    pulses[:: round(rate / f0)] = 1.0
    voice = recursive(pulses - pulses.mean(), 0.97)
    for formant, bandwidth in formants:
        radius = np.exp(-np.pi * bandwidth / rate)
        voice = recursive(voice, 2 * radius * np.cos(2 * np.pi * formant / rate), -radius * radius)
    edge = round(0.02 * rate)
    voice[:edge] *= np.linspace(0, 1, edge)
    voice[-edge:] *= np.linspace(1, 0, edge)
    return 0.3 * voice / np.abs(voice).max()


def recording(vowels, rate: int) -> flow.Recording:
    """0.1 s of quiet, then each vowel of 0.4 s followed by 0.1 s of quiet."""
    pieces = [np.zeros(rate // 10)]
    for formants in vowels:
        pieces += [vowel(formants, 0.4, rate), np.zeros(rate // 10)]
    return flow.Recording(np.concatenate(pieces).astype(np.float32), rate)


@pytest.mark.parametrize("rate", [24000, 48000])
def test_the_first_vowel_separates_a_close_vowel_from_an_open_one(rate):
    spoken = recording([CLOSE, OPEN], rate)
    close, wide = terms.first_vowel(spoken, 0.1, 0.5), terms.first_vowel(spoken, 0.6, 1.0)
    assert 240 < close.f1_hz < 330 and 2550 < close.f2_hz < 2850
    assert 560 < wide.f1_hz < 680 and 1850 < wide.f2_hz < 2050
    assert close.frames == wide.frames == 11
    assert close.like(close) and not wide.like(close)
    # The bounds are one-sided: a closer vowel than its reference is said like it.
    assert close.like(wide)
    # A word aligned into quiet and past the recording's end shows no vowel.
    assert terms.first_vowel(spoken, 1.05, 2.0) is None


def laid(pieces, rate: int = 48000) -> flow.Recording:
    """A recording of pieces in order: each a vowel's formants, or None for quiet, and seconds."""
    parts = [
        vowel(formants, seconds, rate) if formants else np.zeros(round(seconds * rate))
        for formants, seconds in pieces
    ]
    return flow.Recording(np.concatenate(parts).astype(np.float32), rate)


def test_the_first_vowel_reaches_back_over_one_aligner_frame_but_not_into_the_word_before():
    reference = terms.first_vowel(recording([CLOSE], 48000), 0.1, 0.5)
    # "The Eethos mark": the aligner ends "The" at 0.30 s and starts the term at 0.40 s, leaving
    # its close first vowel unassigned; a quiet /θ/ and the open second vowel follow.
    late = laid([(None, 0.1), (CLOSE, 0.2), (CLOSE, 0.1), (None, 0.03), (OPEN, 0.17), (None, 0.1)])
    assert not terms.first_vowel(late, 0.40, 0.64).like(reference)
    assert terms.first_vowel(late, 0.40, 0.64, after=0.30).like(reference)
    # An open word before a close one: reaching back past its aligned end at 0.38 s would measure
    # its vowel, so the window begins there.
    before = laid([(None, 0.1), (OPEN, 0.28), (None, 0.02), (CLOSE, 0.4), (None, 0.1)])
    assert terms.first_vowel(before, 0.40, 0.60, after=0.38).like(reference)
    assert not terms.first_vowel(before, 0.40, 0.60, after=0.0).like(reference)
    # A word aligned from its true start keeps its window: the word before ends where it begins.
    unmoved = terms.first_vowel(before, 0.40, 0.60, after=0.40)
    assert unmoved == terms.first_vowel(before, 0.40, 0.60)


def test_an_occurrence_aligned_late_after_the_word_before_is_said_like_its_reference():
    words = [
        ("Say", 0.0, 0.1),
        ("ETHER", 0.1, 0.5),
        ("now", 0.5, 0.6),
        ("The", 0.6, 0.8),
        ("ETHER", 0.9, 1.14),
        ("mark", 1.14, 1.2),
    ]
    late = flow.Narrated(
        "03",
        "Say ETHER now. The ETHER mark.",
        ["Say ETHER now. ", "The ETHER mark."],
        [{"text": text, "start": start, "end": end} for text, start, end in words],
        laid(
            [
                (None, 0.1),
                (CLOSE, 0.4),
                (None, 0.1),
                (CLOSE, 0.2),
                (CLOSE, 0.1),
                (None, 0.03),
                (OPEN, 0.17),
                (None, 0.1),
            ]
        ),
    )
    record = terms.term_record("en", TERM, [late])
    assert [(row["thought"], row["passes"]) for row in record["occurrences"]] == [
        ("03.1", True),
        ("03.2", True),
    ]
    assert record["failures"] == []
    assert not terms.first_vowel(late.recording, 0.9, 1.14).like(
        terms.first_vowel(late.recording, 0.1, 0.5)
    )


def test_an_occurrence_is_said_unlike_its_reference_beyond_its_ratios():
    reference = terms.Vowel(250.0, 2800.0, 6)
    assert terms.Vowel(375.0, 2381.0, 6).like(reference)
    assert not terms.Vowel(376.0, 2800.0, 6).like(reference)
    assert not terms.Vowel(250.0, 2379.0, 6).like(reference)
    assert terms.Vowel(707.0, 2042.0, 8).record(reference) == {
        "f1_hz": 707,
        "f2_hz": 2042,
        "frames": 8,
        "f1_ratio": 2.828,
        "f2_ratio": 0.729,
    }


def spoken_segment(rate=48000):
    """A segment saying ETHER three times, the second time with an open first vowel."""
    words = [
        ("Say", 0.0, 0.1),
        ("ETHER", 0.1, 0.5),
        ("now", 0.5, 0.6),
        ("ETHER", 0.6, 1.0),
        ("and", 1.0, 1.05),
        ("ETHER's", 1.1, 1.5),
        ("end", 1.5, 1.6),
    ]
    return flow.Narrated(
        "03",
        "Say ETHER now. ETHER and ETHER's end.",
        ["Say ETHER now. ", "ETHER and ETHER's end."],
        [{"text": text, "start": start, "end": end} for text, start, end in words],
        recording([CLOSE, OPEN, CLOSE], rate),
    )


TERM = NarrationTerm(
    term="ETHER", spoken="Eether", ipa="ˈiːθər", reference={"en": {"thought": "03.1", "index": 0}}
)


def test_an_occurrence_said_unlike_its_reference_is_refused_by_name():
    narrated = spoken_segment()
    record = terms.term_record("en", TERM, [narrated])
    assert record["reference"] | {"f1_hz": 0, "f2_hz": 0, "frames": 0} == {
        "thought": "03.1",
        "index": 0,
        "at": 0.1,
        "f1_hz": 0,
        "f2_hz": 0,
        "frames": 0,
    }
    assert [(row["thought"], row["index"], row["passes"]) for row in record["occurrences"]] == [
        ("03.1", 0, True),
        ("03.2", 0, False),
        ("03.2", 1, True),
    ]
    standard = terms.first_vowel(narrated.recording, 0.1, 0.5)
    opened = terms.first_vowel(narrated.recording, 0.6, 1.0)
    first, second = opened.ratios(standard)
    assert record["occurrences"][1]["f1_ratio"] == round(first, 3) and first > terms.F1_RATIO
    assert record["failures"] == [
        f"en 03.2 ETHER #0 at 0.60 s: its first vowel measures F1 {opened.f1_hz:.0f} Hz and F2 "
        f"{opened.f2_hz:.0f} Hz, {first:.2f} and {second:.2f} times those of the reference "
        f"03.1 #0, F1 {standard.f1_hz:.0f} Hz and F2 {standard.f2_hz:.0f} Hz; an occurrence may "
        "reach 1.5 times its F1 and 0.85 times its F2"
    ]
    assert terms.refusals("en", (TERM,), [narrated]) == record["failures"]


def test_a_stale_or_missing_reference_is_refused():
    stale = NarrationTerm.model_validate(
        {**TERM.model_dump(), "reference": {"en": {"thought": "03.1", "index": 1}}}
    )
    assert terms.term_record("en", stale, [spoken_segment()])["failures"] == [
        "en: the ETHER reference 03.1 #1 is not in the narration"
    ]
    unreferenced = NarrationTerm.model_validate({**TERM.model_dump(), "reference": {}})
    assert terms.term_record("en", unreferenced, [spoken_segment()])["failures"] == [
        "en: ETHER is said 3 times but declares no en reference occurrence"
    ]


def test_a_term_is_said_by_its_spoken_form_and_possessives():
    forms = terms.spoken_forms(TERM)
    assert forms == {"ether", "eether"}
    assert all(terms.says(word, forms) for word in ("ETHER", "Eether", "ether's", "ETHER’s,"))
    assert not any(terms.says(word, forms) for word in ("Ethernet", "the"))


def test_every_language_gives_a_term_its_declared_spoken_form():
    def rule(display, spoken):
        return {"display": display, "spoken": spoken, "kind": "english-name"}

    languages = {
        "Chinese": {"normalization": [rule("ETHER", "Eether")]},
        "English": {"normalization": [rule("ETHER", "Ether")]},
    }
    assert terms.parity_failures((TERM,), languages, "contract.json") == [
        "contract.json: the English normalization gives ETHER the spoken form Ether; the film "
        "declares Eether in [[narration.terms]]"
    ]
    languages["English"]["normalization"] = [rule("ether", "Eether")]
    assert terms.parity_failures((TERM,), languages, "contract.json") == []
    languages["Chinese"]["normalization"] = []
    assert terms.parity_failures((TERM,), languages, "contract.json") == [
        "contract.json: the Chinese normalization gives ETHER no spoken form; the film declares "
        "Eether in [[narration.terms]]"
    ]


def test_the_text_holds_each_declared_reference():
    thoughts = [("03.1", "Say Eether now. "), ("03.2", "Eether and Eether's end.")]
    assert terms.declaration_failures((TERM,), thoughts, "en") == []
    assert terms.declaration_failures((TERM,), thoughts, "zh") == [
        "zh: ETHER is said in 03.1, 03.2 but declares no zh reference occurrence"
    ]
    moved = NarrationTerm.model_validate(
        {**TERM.model_dump(), "reference": {"en": {"thought": "03.2", "index": 2}}}
    )
    assert terms.declaration_failures((moved,), thoughts, "en") == [
        "en: the ETHER reference 03.2 #2 is not in the narration; 03.2 says it 2 times"
    ]
    assert terms.declaration_failures((TERM,), [("03.1", "Say it.")], "en") == [
        "en: ETHER declares a reference for en, but the narration never says it"
    ]


def test_a_receipt_holds_each_reference_take_and_a_take_says_its_terms():
    child = {"index": 1, "spoken_text": "Say Eether now. ", "path": "take.wav"}
    records = [{"id": "03", "utterance_groups": {"records": [child]}}]
    ((term, forms, reference, take),) = terms.receipt_references("en", (TERM,), records)
    assert (term, terms.named(reference), take) == (TERM, "03.1 #0", child)
    assert terms.receipt_references("zh", (TERM,), records) == []
    with pytest.raises(terms.TermError, match="ETHER reference 03.1 #0 is not in the narration"):
        terms.receipt_references("en", (TERM,), [{"id": "03"}])
    spoken = spoken_segment(24000)
    standard = terms.Standard(term, forms, reference, terms.first_vowel(spoken.recording, 0.1, 0.5))
    said = terms.take_terms([standard], spoken.words, spoken.recording)
    assert [
        (row["index"], row["f1_ratio"] == 1.0, row["passes"]) for row in said["term_occurrences"]
    ] == [
        (0, True, True),
        (1, False, False),
        (2, True, True),
    ]
    assert said["terms_pass"] is False
