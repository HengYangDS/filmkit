"""Each edition's sentences, as the review judges them: one by one, as a viewer hears them."""

import pytest

import filmkit.review.sentences as review_sentences
from filmkit.review import ReviewError


def segment(segment_id, groups, words):
    """A timeline segment of these thoughts, its words aligned 0.2 s apart from 10 s."""
    timed = [
        {"text": word, "start": round(10 + 0.2 * k, 2), "end": round(10.18 + 0.2 * k, 2)}
        for k, word in enumerate(words)
    ]
    return {"id": segment_id, "text": "".join(groups), "utterance_groups": groups, "words": timed}


def test_a_chinese_thought_of_two_sentences_is_split_at_its_marks():
    groups = ["构建时，先录下旁白！再拼成音轨。", "这些步骤都不联网？"]
    words = list("构建时先录下旁白再拼成音轨这些步骤都不联网")
    found = review_sentences.sentences({"segments": [segment("02", groups, words)]}, "zh")
    assert found == [
        {"id": "02.1.1", "text": "构建时，先录下旁白！", "start": 10.0, "end": 11.58},
        {"id": "02.1.2", "text": "再拼成音轨。", "start": 11.6, "end": 12.58},
        {"id": "02.2.1", "text": "这些步骤都不联网？", "start": 12.6, "end": 14.18},
    ]


def test_an_english_quotation_stays_whole_and_its_closing_quote_ends_the_sentence():
    groups = [
        "The Agent writes, “Done. All tests pass.” Is it done? ",
        "It is not, she said. Nobody checked.",
    ]
    words = (
        "The Agent writes Done All tests pass Is it done It is not she said Nobody checked"
    ).split()
    found = review_sentences.sentences({"segments": [segment("05", groups, words)]}, "en")
    assert [(row["id"], row["text"]) for row in found] == [
        ("05.1.1", "The Agent writes, “Done. All tests pass.”"),
        ("05.1.2", "Is it done?"),
        ("05.2.1", "It is not, she said."),
        ("05.2.2", "Nobody checked."),
    ]
    # Each sentence runs from its first aligned word to its last.
    assert (found[0]["start"], found[0]["end"]) == (10.0, 11.38)
    assert (found[3]["start"], found[3]["end"]) == (13.0, 13.38)


def test_a_quotation_in_straight_quotes_stays_whole_and_an_apostrophe_opens_none():
    # A script may write quotation marks straight; a straight double quote opens a quotation and
    # the next one closes it, and an apostrophe inside a word is no quotation mark.
    groups = ["An Agent's note reads: \"Done. All tests pass.\" It is the job's only record."]
    words = "An Agent's note reads Done All tests pass It is the job's only record".split()
    found = review_sentences.sentences({"segments": [segment("01", groups, words)]}, "en")
    assert [row["text"] for row in found] == [
        'An Agent\'s note reads: "Done. All tests pass."',
        "It is the job's only record.",
    ]


def test_a_thought_without_a_closing_mark_is_one_sentence():
    groups = ["Then it renders every frame", " and packages the films"]
    words = "Then it renders every frame and packages the films".split()
    found = review_sentences.sentences({"segments": [segment("03", groups, words)]}, "en")
    assert [(row["id"], row["text"]) for row in found] == [
        ("03.1.1", "Then it renders every frame"),
        ("03.2.1", "and packages the films"),
    ]


def test_words_that_do_not_cover_the_text_are_refused_by_segment():
    broken = segment("04", ["核对完成。"], list("核对"))
    with pytest.raises(ReviewError, match="^04: "):
        review_sentences.sentences({"segments": [broken]}, "zh")
