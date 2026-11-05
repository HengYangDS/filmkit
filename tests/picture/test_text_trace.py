"""The text trace's measures: the title the opening shows, and the contrast of text at rest."""

import pytest

from filmkit.picture import text_trace

STEP = 1 / 30


def rows(text, start, seconds, *, contrast=15.6, alpha=1.0, scene="", role="title"):
    """Trace lines of one text shown from `start` for `seconds` at one contrast and opacity."""
    return [
        f"{start + k * STEP:.2f}\t{scene}\t{role}\t{contrast:.3f}\t{alpha:.3f}\t{text}\n"
        for k in range(round(seconds / STEP))
    ]


def timeline(title, first_word=3.0):
    return {"title": title, "segments": [{"words": [{"start": first_word, "end": first_word + 1}]}]}


def opening(title, lines, first_word=3.0):
    texts = list(text_trace.trace_texts(lines))
    return text_trace.opening_title(timeline(title, first_word), texts, STEP)


def test_a_title_set_in_parts_on_two_lines_is_shown():
    lines = rows("Sample Reel", 0.0, 2.0) + rows("From Sources to Film", 0.0, 2.0)
    lines += rows("Yang HENG", 0.0, 2.0)
    assert opening("Sample Reel · From Sources to Film", lines) == {
        "title": "Sample Reel · From Sources to Film",
        "first_word": 3.0,
        "shown_seconds": 2.0,
        "shown_from": 0.0,
        "shown_to": 2.0,
        "missing_words": [],
    }
    # A Chinese title is compared character by character, and a colon or " · " separates nothing.
    lines = rows("数据部门工作指南", 0.0, 1.5) + rows("精华版", 0.0, 1.5) + rows("DDWG", 0.0, 1.5)
    assert opening("DDWG · 数据部门工作指南 · 精华版", lines)["shown_seconds"] == 1.5
    lines = rows("Data Department Work Guidelines", 0, 1) + rows("The Essentials", 0, 1)
    lines += rows("DDWG", 0, 1)
    shown = opening("DDWG · Data Department Work Guidelines: The Essentials", lines)
    assert (shown["shown_seconds"], shown["missing_words"]) == (1.0, [])


def test_an_opening_without_its_title_names_the_words_it_never_shows():
    # Only the chip of an illustrative case before the first word, and the title after it.
    lines = rows("Illustrative", 0.0, 3.0, role="marker") + rows("ETHOS", 3.0, 1.0)
    shown = opening("ETHOS · Evidence-grounded Trust", lines)
    assert shown["shown_seconds"] == 0.0 and shown["shown_from"] is None
    assert shown["missing_words"] == ["ethos", "evidence", "grounded", "trust"]
    # A title below reading contrast, or on a line that adds other words, is not shown.
    lines = rows("ETHOS", 0.0, 2.0, contrast=2.5) + rows("Evidence-grounded Trust Today", 0.0, 2.0)
    assert opening("ETHOS · Evidence-grounded Trust", lines)["shown_seconds"] == 0.0
    # Part of the title is shown, the rest never.
    shown = opening("ETHOS · Evidence-grounded Trust", rows("ETHOS", 0.0, 2.0))
    assert shown["missing_words"] == ["evidence", "grounded", "trust"]


def test_a_text_held_below_its_contrast_for_seven_tenths_of_a_second_is_at_rest():
    lines = rows("Soundtrack", 1.0, 1.0, contrast=3.34, alpha=0.58, scene="02", role="label")
    lines += rows("Soundtrack", 1.0, 1.0, contrast=6.0, scene="02", role="label")
    lines += rows("Captions", 4.0, 0.7, contrast=4.2, scene="02", role="label")
    lines += rows("Picture", 6.0, 0.6, contrast=2.0, scene="02", role="label")
    runs = text_trace.low_contrast(list(text_trace.trace_texts(lines)), STEP)
    assert runs == [
        {
            "scene": "02",
            "role": "label",
            "text": "Soundtrack",
            "from": 1.0,
            "to": 2.0,
            "seconds": 1.0,
            "lowest": 3.34,
        },
        {
            "scene": "02",
            "role": "label",
            "text": "Captions",
            "from": 4.0,
            "to": 4.7,
            "seconds": 0.7,
            "lowest": 4.2,
        },
    ]


@pytest.mark.parametrize(
    "lines",
    [
        # A fade that crosses 4.5:1 in 0.6 s, twice with a legible stretch between.
        rows("Films", 1.0, 0.6, contrast=2.0) + rows("Films", 2.0, 0.6, contrast=2.0),
        # A text shown at 4% opacity or less is not shown at all.
        rows("Films", 1.0, 2.0, contrast=1.1, alpha=0.04),
        # A mark without a letter or a digit is a graphic, not a text to read.
        rows("→", 1.0, 2.0, contrast=2.0),
        # A text at 4.5:1 is at its floor.
        rows("Films", 1.0, 2.0, contrast=4.5),
    ],
)
def test_fades_marks_and_texts_at_the_floor_are_not_at_rest_below_it(lines):
    assert text_trace.low_contrast(list(text_trace.trace_texts(lines)), STEP) == []


def test_the_report_reads_a_trace_and_skips_a_partial_line():
    lines = rows("示例影片", 0.0, 2.0) + rows("音轨", 3.0, 1.0, contrast=3.0, scene="02")
    report = text_trace.report(timeline("示例影片"), [*lines, "4.00\t02\tlabel"], STEP)
    assert report["opening_title"]["shown_seconds"] == 2.0
    assert report["resting_contrast"] == 4.5 and report["fade_seconds"] == 0.7
    assert [(run["text"], run["seconds"]) for run in report["low_contrast"]] == [("音轨", 1.0)]
    # A timeline without a word has no opening quiet.
    assert text_trace.first_word({"segments": [], "duration": 60}) == 60
