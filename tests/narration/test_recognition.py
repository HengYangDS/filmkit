"""Recognition units and their comparison: how a transcript is checked against its text."""

import pytest

import filmkit.narration.readings as narration_readings
import filmkit.narration.recognition as narration_recognition


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
