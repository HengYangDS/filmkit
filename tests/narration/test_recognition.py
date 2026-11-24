"""Recognition units and their comparison: how a transcript is checked against its text."""

import pronounced
import pytest

import filmkit.narration.cmudict as narration_cmudict
import filmkit.narration.readings as narration_readings
import filmkit.narration.recognition as narration_recognition
from filmkit.film import NarrationTerm

# A term written for the tests, respelled for the narrator as `terms` describes it.
NAME = NarrationTerm(term="NAME", spoken="Naim", ipa="ˈneɪm")
# The edition's other Latin units, as a Chinese bench reads them from its script.
OTHERS = frozenset({"agent", "git", "github", "gitlab"})


def test_units_fold_case_and_drop_punctuation_in_both_languages():
    assert narration_recognition.recognition_units("数据，先看 Agent 的用途。") == [
        *"数据先看",
        "agent",
        *"的用途",
    ]
    assert narration_recognition.recognition_units("Don't cite ETHOS-2, please!") == [
        "don't",
        "cite",
        "ethos",
        "2",
        "please",
    ]


@pytest.mark.parametrize(
    ("heard", "phrase", "expected"),
    [
        ("先看这份数据的用途。", "数据的用途", True),
        ("先看数据，再看用途。", "数据的用途", False),
        ("Ask these questions for the INTENDED use.", "intended use", True),
        ("Use it as intended.", "intended use", False),
        ("Anything at all.", "", False),
    ],
)
def test_heard_phrase_needs_its_units_contiguous(heard, phrase, expected):
    assert narration_recognition.heard_phrase(heard, phrase) is expected


@pytest.mark.parametrize(
    ("expected", "observed", "distance"),
    [
        (["数", "据"], ["数", "据"], 0),
        (["数", "据"], ["数", "句"], 1),
        (["agent", "use"], ["agent"], 1),
        (["use"], ["intended", "use"], 1),
        ([], ["extra", "words"], 2),
        (["a", "b", "c"], ["c", "b", "a"], 2),
    ],
)
def test_unit_distance_counts_the_fewest_unit_edits(expected, observed, distance):
    assert narration_recognition.unit_distance(expected, observed) == distance


@pytest.mark.parametrize(
    ("text", "heard", "by_unit", "by_reading"),
    [
        # A homophone the recognizer wrote is what a listener heard.
        ("先在这里核对，再做决定。", "先再这里合对，再作决定。", 3, 0),
        # The particles are said alike, whichever is written, where the text says a particle.
        ("慢慢地说，说得清楚的人。", "慢慢的说，说的清楚地人。", 3, 0),
        # 地 in 土地 and in 地球 is no particle: another reading is another word.
        ("这片土地很大。", "这片土的很大。", 1, 1),
        ("地球是圆的。", "得球是圆地。", 2, 1),
        # Another tone is another reading, and a dropped or added unit stays a difference.
        ("买了一本书。", "卖了一本书。", 1, 1),
        ("把调度窗口提前。", "把调度窗口提。", 1, 1),
        # A Latin unit is its letters and digits: an apostrophe is the recognizer's spelling.
        ("Then the checks and the author's use.", "Then the check's and the authors use.", 2, 0),
        # Adjacent Latin units are joined where the other side writes them as one.
        ("A backtest may use them.", "A back test may use them.", 2, 0),
        ("Check in, then go on.", "Checkin, then go on.", 2, 0),
        # Another word stays another word, and a number said is not its digits.
        ("Changes and evidence.", "Changes in evidence.", 1, 1),
        ("Ten checks.", "10 checks.", 1, 1),
        ("先看 Agent 的用途。", "先看 Agents 地用途。", 2, 1),
        # A Latin unit and a Han character are never alike, whatever the character's reading.
        ("请告诉 me 吧。", "请告诉么吧。", 1, 1),
    ],
)
def test_units_differ_by_reading_only_where_a_listener_hears_a_difference(
    text, heard, by_unit, by_reading
):
    units = narration_recognition.recognition_units
    assert narration_recognition.unit_distance(units(text), units(heard)) == by_unit
    assert narration_recognition.reading_distance(text, heard) == by_reading


def test_a_declared_word_gives_its_characters_the_reading_the_film_declares():
    # The dictionary reads 重 in 重来 another way; a film that declares a reading is compared
    # by the one it declares, in the text and wherever the transcript holds the word.
    word = narration_readings.Word("重", ("chóng",), None)
    assert narration_recognition.reading_distance("重来一次。", "虫来一次。") == 1
    assert narration_recognition.reading_distance("重来一次。", "虫来一次。", [word]) == 0
    # A declared reading of 得 is no particle's: heard as 的, it is another word.
    must = narration_readings.Word("得", ("děi",), None)
    assert narration_recognition.reading_distance("你得去。", "你的去。") == 0
    assert narration_recognition.reading_distance("你得去。", "你的去。", [must]) == 1


def test_a_respelled_word_is_refused_where_the_text_holds_the_reading_it_respells_against():
    # The film respells 去重 as 去虫 because the narrator reads 重 there as zhòng; a transcript
    # that writes 去重 where the text holds 去众, said zhòng, holds another word.
    rule = {"display": "去重", "spoken": "去虫", "kind": "homophone"}
    words = narration_readings.compared_words({"normalization": [rule]})
    text, heard = "他要去众人那里。", "他要去重人那里。"
    assert narration_recognition.reading_distance(text, heard) == 0
    assert narration_recognition.reading_distance(text, heard, words) == 1


def by_reading(text: str, heard: str, names=None) -> int:
    """Differing units by reading: as today without `names`, else with the edition's names."""
    if names is None:
        return narration_recognition.reading_distance(text, heard)
    return narration_recognition.reading_distance(text, heard, (), names)


def test_a_declared_term_is_one_unit_under_its_display_and_spoken_forms():
    names = narration_recognition.Names((NAME,))
    said, possessive = "Naim is built for it.", "It is Naim's aim."
    passing = [
        (said, "Name is built for it.", 1),
        (said, "NAME is built for it.", 1),
        (said, "NaMe is built for it.", 1),
        (possessive, "It is Name's aim.", 1),
        # The text's curly apostrophe parts its units; the term's possessive joins them again.
        ("It is Naim’s aim.", "It is Name's aim.", 2),
    ]
    for text, heard, today in passing:
        assert (by_reading(text, heard), by_reading(text, heard, names)) == (today, 0), heard
    guards = [
        (said, "Nime is built for it.", 1),
        (said, "Nine is built for it.", 1),
        (said, "is built for it.", 1),
        (said, "Name Name is built for it.", 1),
        (said, "Na me is built for it.", 2),
        (possessive, "It is Name aim.", 1),
        ("Naim aims.", "Name's aims.", 1),
        (possessive, "It is Name' aim.", 1),
    ]
    for text, heard, after in guards:
        assert by_reading(text, heard, names) == after, heard


def test_units_with_the_same_letters_stay_alike_beside_a_declared_term():
    # `name's` says the term's possessive and `names` is no form of it; their letters are the
    # same, and the recognizer's apostrophe is no difference, term or no term.
    names = narration_recognition.Names((NAME,))
    text = "Their names are here."
    # A straight apostrophe keeps one unit; a curly one or a space parts it, and the parts join.
    for heard in ("Their name's are here.", "Their name’s are here.", "Their name s are here."):
        assert (by_reading(text, heard), by_reading(text, heard, names)) == (0, 0), heard
    chinese = narration_recognition.Names((NAME,), embedded=True, others=OTHERS)
    assert by_reading("那些 names 在这里。", "那些name's在这里。", chinese) == 0


def test_a_term_inside_a_compound_is_compared_by_its_letters():
    # The term line measures no occurrence inside a compound, so nothing would hold its sound:
    # there the comparison reads the letters, as for any other word, and fails closed.
    chinese = narration_recognition.Names((NAME,), embedded=True, others=OTHERS)
    assert by_reading("一种 Naim-based 的做法。", "一种Nime-based的做法。", chinese) == 1
    english = narration_recognition.Names((NAME,))
    assert by_reading("A Naim-based plan.", "A Name-based plan.", english) == 1
    # A whole word that says the term is the term, its curly possessive's parts included.
    assert by_reading("Naim 的做法。", "Nime的做法。", chinese) == 0
    assert by_reading("It is Naim’s aim.", "It is Name's aim.", chinese) == 0


def test_a_term_in_chinese_speech_is_alike_one_latin_unit_that_is_no_other_unit_of_the_edition():
    names = narration_recognition.Names((NAME,), embedded=True, others=OTHERS)
    text = "Naim 走的是另一条路。"
    for heard in ("Name走的是另一条路。", "Nime走的是另一条路。"):
        assert (by_reading(text, heard), by_reading(text, heard, names)) == (1, 0), heard
    refused = [
        ("Agent走的是另一条路。", 1),
        ("2024走的是另一条路。", 1),
        ("内姆走的是另一条路。", 2),
        ("走的是另一条路。", 1),
        ("Name Name走的是另一条路。", 1),
        ("Nime Nime走的是另一条路。", 1),
        ("Nime OK走的是另一条路。", 1),
        ("Ni me走的是另一条路。", 1),
        ("N I M E走的是另一条路。", 3),
        ("走的是Nime另一条路。", 2),
    ]
    for heard, after in refused:
        assert by_reading(text, heard, names) == after, heard
    assert by_reading("让 Naim Agent 接手。", "让NimeAgent接手。", names) == 1
    # Decided and stated: a word that is no Latin unit of the edition passes in the name's
    # place, and so does another of its names spelled otherwise than the script spells it.
    assert by_reading(text, "Python走的是另一条路。", names) == 0
    assert by_reading(text, "Agents走的是另一条路。", names) == 0
    # The comparison names each unit that stood for the term in other letters, and no other.
    compared = narration_recognition.compared
    assert compared(text, "Nime走的是另一条路。", (), names).stood_for == (("NAME", "nime"),)
    assert compared(text, "Name走的是另一条路。", (), names).stood_for == ()


def test_an_english_edition_gives_a_term_no_other_letters():
    # Built for the English edition, the comparison has no rule of other letters: in English
    # every word is Latin letters, and any word would pass in the name's place.
    texts = ["Naim is built for it.", "An Agent reads it."]
    names = narration_recognition.edition_names((NAME,), texts, embedded=False)
    assert names == narration_recognition.Names((NAME,))
    assert by_reading("Naim is built for it.", "Nime is built for it.", names) == 1
    assert by_reading("Naim 走的是另一条路。", "Nime走的是另一条路。", names) == 1


# The pronunciations of the fixture's lines (`pronounced`), as the pinned CMUdict states them.
SAID = narration_cmudict.parse(pronounced.RAW)


def heard(**readings) -> narration_recognition.Names:
    """An English edition's names: no term, its Latin units heard by the fixture's pronunciations
    and the readings its pronunciation declares by word, () for a word said by its letter names."""
    declared = {word: tuple(tuple(p.split()) for p in said) for word, said in readings.items()}
    return narration_recognition.Names(
        pronounced=narration_recognition.Pronunciations(SAID, declared)
    )


@pytest.mark.parametrize(
    ("text", "transcript", "by_unit", "by_reading"),
    [
        # Another spelling of the same word, and a homophone.
        ("It is labelled.", "It is labeled.", 1, 0),
        ("Their aim.", "There aim.", 1, 0),
        # A spelling that has the text's sound only as a later pronunciation: tears is first
        # the verb tear.
        ("Half tiers.", "Half tears.", 1, 1),
        # A word of another sound, and another word's weak form.
        ("An aim.", "And aim.", 1, 1),
        ("Or this.", "Are this.", 1, 1),
        # Secondary stress against none is the same sound; primary stress is kept.
        ("The catalogue.", "The catalog.", 1, 0),
        ("A tier.", "Uh tier.", 1, 1),
        # A word the dictionary does not hold is compared by its letters.
        ("The delivery's end.", "The delivery end.", 1, 1),
        # Each spelling whose first pronunciation is the text word's; "tew" says T UW1 only as
        # its second, so it differs.
        ("To go.", "Two go.", 1, 0),
        ("Too late.", "To late.", 1, 0),
        ("To go.", "Tew go.", 1, 1),
    ],
)
def test_english_words_are_also_compared_by_their_pronunciation(
    text, transcript, by_unit, by_reading
):
    units = narration_recognition.recognition_units
    assert narration_recognition.unit_distance(units(text), units(transcript)) == by_unit
    assert narration_recognition.reading_distance(text, transcript, (), heard()) == by_reading


def test_a_declared_reading_is_the_text_words_own():
    # CMUdict lists the past tense of read first; declared by its present tense alone, the word
    # is no longer heard in "red".
    assert narration_recognition.reading_distance("Read it.", "Red it.", (), heard()) == 0
    present = heard(read=("R IY1 D",))
    assert narration_recognition.reading_distance("Read it.", "Red it.", (), present) == 1
    both = heard(read=("R IY1 D", "R EH1 D"))
    assert narration_recognition.reading_distance("Read it.", "Red it.", (), both) == 0


def test_a_word_declared_by_letter_names_is_compared_by_its_letters():
    # CMUdict lists ai first as the word eye.
    assert narration_recognition.reading_distance("AI helps.", "I helps.", (), heard()) == 0
    letters = heard(ai=())
    for transcript in ("I helps.", "Eye helps."):
        assert narration_recognition.reading_distance("AI helps.", transcript, (), letters) == 1
    assert narration_recognition.reading_distance("AI helps.", "A I helps.", (), letters) == 0
    # Declared so, it gives no pronunciation on the transcript's side either.
    assert narration_recognition.reading_distance("Eye helps.", "AI helps.", (), letters) == 1
    # Its possessive and plural are the declared word's too, though CMUdict holds them as words.
    assert narration_recognition.reading_distance("AI's aim.", "Eyes aim.", (), heard()) == 0
    for text in ("AI's aim.", "AIs aim."):
        assert narration_recognition.reading_distance(text, "Eyes aim.", (), letters) == 1


def test_a_declared_term_is_held_to_its_form_and_not_to_its_pronunciation():
    git = NarrationTerm(term="Git", spoken="Git", ipa="ɡɪt")
    names = heard()._replace(terms=(git,))
    assert narration_recognition.reading_distance("Git runs.", "Get runs.", (), names) == 1
    (unit, _) = narration_recognition.read_units("Git runs.", (), names.terms, names.pronounced)
    assert (unit.term, unit.first, unit.readings) == ("Git", None, ())


def test_a_language_that_hears_its_latin_words_by_their_letters_reads_no_dictionary():
    assert narration_recognition.reading_distance("Their aim.", "There aim.") == 1
    chinese = narration_recognition.Names(embedded=True, others=OTHERS)
    assert by_reading("他们 their 目标。", "他们there目标。", chinese) == 1


@pytest.mark.usefixtures("test_languages")
def test_how_a_language_hears_a_transcripts_latin_words_is_its_declaration():
    asked = []

    def supplied():
        asked.append(True)
        return SAID

    english = narration_recognition.pronunciations_of("xb", supplied, {})
    assert english == narration_recognition.Pronunciations(SAID, {}) and asked == [True]
    names = narration_recognition.Names(pronounced=english)
    assert narration_recognition.reading_distance("Labelled.", "Labeled.", (), names) == 0
    assert narration_recognition.pronunciations_of("xa", supplied, {}) is None and asked == [True]
    chinese = narration_recognition.Names(pronounced=None)
    assert narration_recognition.reading_distance("Labelled.", "Labeled.", (), chinese) == 1
