"""Caption cue timing: word-bound cues, their declared edges and their reading time."""

import json
from itertools import pairwise
from pathlib import Path

import pytest

import filmkit.captions as captions
import filmkit.captions.timing as captions_timing
import filmkit.narration.spoken_units as spoken_units

# Real segments of both delivered timelines, with the cues the production timed for them.
SEGMENTS = json.loads((Path(__file__).parent / "cue-timing-segments.json").read_text())


def timeline(part: dict) -> dict:
    return {
        "caption_timing": part["caption_timing"],
        "segments": [
            {
                **segment,
                "words": [
                    {"text": text, "start": start, "end": end}
                    for text, start, end in segment["words"]
                ],
            }
            for segment in part["segments"]
        ],
    }


@pytest.mark.parametrize("code", ["zh", "en"])
def test_real_segments_time_their_cues_as_delivered(code):
    part = SEGMENTS[code]
    assert captions_timing.timed_caption_cues(timeline(part), code) == part["cues"]


def test_the_real_segments_cover_the_early_start_and_the_full_interval_hold():
    cues, leads = SEGMENTS["en"]["cues"], []
    for segment in SEGMENTS["en"]["segments"]:
        items = [
            {"text": text, "start_time": start, "end_time": end}
            for text, start, end in segment["words"]
        ]
        _, times = spoken_units.aligned_lookup(segment["text"], items)
        position = 0
        for cue in (cue for cue in cues if cue["segment"] == segment["id"]):
            leads.append(times[position][0] - cue["start"])
            position += len(spoken_units.units(cue["text"]))
    # A brief cue that ends a line starts before its first word, by at most 0.1 s.
    assert any(lead > 0 for lead in leads)
    assert max(leads) <= 0.1 + 1e-9
    # Every English cue holds until the next cue of its segment.
    assert all(a["end"] == b["start"] for a, b in pairwise(cues) if a["segment"] == b["segment"])


def segment(**changes) -> dict:
    words = [("甲", 1.0, 1.4), ("乙", 1.4, 1.8), ("丙", 2.4, 2.8), ("丁", 2.8, 3.2)]
    return {
        "id": "01",
        "text": "甲乙，丙丁。",
        "utterance_groups": ["甲乙，丙丁。"],
        "voice_start": 1.0,
        "voice_end": 3.3,
        "end": 5.0,
        "words": [{"text": text, "start": start, "end": end} for text, start, end in words],
        **changes,
    }


@pytest.mark.parametrize(
    ("caption_timing", "code", "message"),
    [
        (None, "zh", "requires a declared caption_timing policy"),
        ({"hold_mode": "full-interval"}, "zh", "full-interval for English"),
        ({"hold_mode": "sentence"}, "en", "full-interval for English"),
        ({"tail_seconds": 0.3}, "zh", "finite bounded seconds"),
        ({"short_cue_lead_seconds": True}, "zh", "finite bounded seconds"),
    ],
)
def test_cue_timing_requires_its_declared_bounded_policy(caption_timing, code, message):
    with pytest.raises(captions.CaptionError, match=message):
        captions_timing.timed_caption_cues(
            {"caption_timing": caption_timing, "segments": [segment()]}, code
        )


def test_a_cue_never_crosses_a_thought():
    policy = {"tail_seconds": 0.25}
    cues = captions_timing.timed_caption_cues(
        {"caption_timing": policy, "segments": [segment()]}, "zh"
    )
    assert [cue["text"] for cue in cues] == ["甲乙，丙丁。"]
    # A thought that ends at the comma would split the one line that both clauses fit.
    across = segment(utterance_groups=["甲乙，", "丙丁。"])
    with pytest.raises(captions.CaptionError, match="crosses a thought-group boundary: 01"):
        captions_timing.timed_caption_cues({"caption_timing": policy, "segments": [across]}, "zh")


def test_a_brief_line_that_ends_in_a_closing_quote_starts_early():
    words = [("甲", 1.0, 1.2), ("乙", 1.2, 1.4), ("丙", 1.4, 1.6), ("丁", 1.6, 1.8)]
    words += [("戊", 1.8, 2.0), ("己", 2.0, 2.2), ("庚", 2.6, 2.8), ("辛", 2.8, 3.0)]
    quoted = segment(
        text="甲乙丙丁戊己。“庚辛。”",
        utterance_groups=["甲乙丙丁戊己。“庚辛。”"],
        voice_end=3.1,
        words=[{"text": text, "start": start, "end": end} for text, start, end in words],
    )
    cues = captions_timing.timed_caption_cues(
        {"caption_timing": {"short_cue_lead_seconds": 0.1}, "segments": [quoted]}, "zh"
    )
    # The quote rides on the line its sentence ends, and that brief line takes its lead.
    assert [cue["text"] for cue in cues] == ["甲乙丙丁戊己。", "“庚辛。”"]
    assert cues[1]["start"] == pytest.approx(2.5)


def test_brief_captions_join_their_sentence_or_hold_for_reading():
    def cue(start, end, text, segment="01"):
        return {"start": start, "end": end, "text": text, "segment": segment}

    joined = captions_timing.steady_short_cues(
        [
            cue(0, 2.0, "不写“基本按时”，"),
            cue(2.0, 2.8, "这是信；"),
            cue(3.4, 5, "先说影响。"),
        ],
        33,
    )
    assert [c["text"] for c in joined] == ["不写“基本按时”，这是信；", "先说影响。"]
    assert (joined[0]["start"], joined[0]["end"]) == (0, 2.8)
    held = captions_timing.steady_short_cues(
        [
            cue(0, 2.0, "Report the state. "),
            cue(2.0, 2.7, "With the problem, "),
            cue(2.7, 5.0, "scope or completion condition missing, work is unframed. "),
        ],
        66,
    )
    # A brief cue with no quiet after it ends where the next cue's words begin.
    assert [c["text"] for c in held][1] == "With the problem, "
    assert held[1]["end"] == 2.7
    assert held[2]["start"] == 2.7
    apart = captions_timing.steady_short_cues(
        [cue(0, 2.0, "规则，"), cue(2.0, 2.8, "就退役。", "02")], 33
    )
    assert len(apart) == 2
    assert apart[1]["end"] - apart[1]["start"] < 1.0


def test_a_brief_caption_holds_into_the_quiet_without_moving_the_next_one():
    def cue(start, end, text):
        return {"start": start, "end": end, "text": text, "segment": "25"}

    held = captions_timing.steady_short_cues(
        [
            cue(0, 2.0, "信达雅要分开看。"),
            cue(2.0, 2.6, "也能行动。"),
            cue(3.4, 5.0, "雅，是用审美和修养。"),
        ],
        33,
    )
    assert [c["text"] for c in held][1] == "也能行动。"
    assert abs(held[1]["end"] - 3.0) < 1e-9
    assert held[2]["start"] == 3.4
    lent = captions_timing.steady_short_cues(
        [cue(2.0, 2.6, "也能行动。"), cue(2.75, 5.0, "雅，是用审美和修养。")], 33
    )
    # The next cue still starts on its first word: a brief cue only takes the quiet.
    assert lent[0]["end"] == 2.75
    assert lent[1]["start"] == 2.75


def cue_at(start, end, text, segment="08"):
    """An English caption cue of one segment."""
    return {"start": start, "end": end, "text": text, "segment": segment}


# A finished sentence, then "The inference is that the vendor": 32 characters shown for 1.12 s,
# 28.6 characters per second, whose sentence goes on 0.05 s later in 30 characters.
INFERENCE = [
    cue_at(0.0, 2.96, "The observation is that the first correction has disappeared. "),
    cue_at(2.96, 4.08, "The inference is that the vendor "),
    cue_at(4.13, 6.0, "can correct a value more than "),
    cue_at(6.0, 8.0, "once, so the remedy tells the records apart. "),
]


def test_a_fast_english_cue_joins_its_neighbour_in_its_sentence():
    paced = captions_timing.steady_short_cues(INFERENCE, 66, rate=25)
    # The sentence before it has ended, so it joins the next cue: 62 characters on one line.
    assert [cue["text"] for cue in paced] == [
        INFERENCE[0]["text"],
        "The inference is that the vendor can correct a value more than ",
        INFERENCE[3]["text"],
    ]
    assert len(paced[1]["text"].strip()) == 62
    assert (paced[1]["start"], paced[1]["end"]) == (2.96, 6.0)


def test_a_fast_english_cue_at_a_sentence_end_holds_to_the_rate():
    # 26 characters end their sentence after 0.9 s, and the next cue starts 0.6 s later.
    held = captions_timing.steady_short_cues(
        [
            cue_at(0.0, 2.0, "Each record keeps its source. "),
            cue_at(2.0, 2.9, "No one else may change it. "),
            cue_at(3.5, 5.5, "The review reads it back. "),
        ],
        66,
        rate=25,
    )
    assert [cue["text"] for cue in held][1] == "No one else may change it. "
    assert held[1]["start"] == 2.0
    assert held[1]["end"] == pytest.approx(3.04)
    assert held[2]["start"] == 3.5
    # 30 characters shown for 1.1 s with 0.04 s of quiet after them hold to the next cue's start.
    capped = captions_timing.steady_short_cues(
        [cue_at(0.0, 1.1, "And this one got it all wrong. "), cue_at(1.14, 3.0, "It goes back. ")],
        66,
        rate=25,
    )
    assert capped[0]["start"] == 0.0
    assert capped[0]["end"] == pytest.approx(1.14)
    assert capped[1]["start"] == 1.14


def test_an_english_cue_within_the_rate_is_unchanged():
    # 40 characters shown for 2 s read at 20 characters per second, and 30 shown for 1.2 s at 25.
    cues = [
        cue_at(0.0, 2.0, "Every change names the record it changes "),
        cue_at(2.0, 3.2, "And if it got something wrong, "),
        cue_at(3.2, 5.0, "the review sends it back. "),
    ]
    assert captions_timing.steady_short_cues(cues, 66, rate=25) == cues


def test_a_fast_cue_that_can_neither_join_nor_hold_is_recorded_at_its_rate():
    # 32 characters shown for 1.12 s; the next cue of its sentence starts as it ends, and the two
    # would make a line of 69 characters.
    cues = [
        cue_at(0.0, 2.96, "The observation is that the first correction has disappeared. "),
        cue_at(2.96, 4.08, "The inference is that the vendor "),
        cue_at(4.08, 6.0, "can correct a value more than once. "),
    ]
    paced = captions_timing.steady_short_cues(cues, 66, rate=25)
    assert paced == cues
    fields = captions_timing.caption_receipt_fields({"captions": paced}, "en")
    assert fields["captions_above_reading_rate"] == [
        {
            "segment": "08",
            "start": 2.96,
            "end": 4.08,
            "text": "The inference is that the vendor",
            "characters_per_second": 28.6,
        }
    ]


def test_paced_cues_keep_their_words_and_their_starts():
    cues = [
        *INFERENCE,
        cue_at(8.0, 8.9, "No one else may change it. "),
        cue_at(9.5, 11.0, "The review reads it back. "),
    ]
    paced = captions_timing.steady_short_cues(cues, 66, rate=25)
    assert len(paced) == len(cues) - 1
    assert "".join(cue["text"] for cue in paced) == "".join(cue["text"] for cue in cues)
    # Each paced cue starts where the first cue of its words started.
    starts, position = {}, 0
    for cue in cues:
        starts[position] = cue["start"]
        position += len(cue["text"])
    position = 0
    for cue in paced:
        assert cue["start"] == starts[position]
        position += len(cue["text"])


def one_segment(text, phrases, words):
    """A timeline of one segment that authors its cue phrases, each timed with no tail."""
    spoken = segment(
        text=text,
        utterance_groups=[text],
        caption_phrases=phrases,
        voice_start=0.0,
        voice_end=words[-1][2],
        words=[{"text": word, "start": start, "end": end} for word, start, end in words],
    )
    return {"caption_timing": {"tail_seconds": 0}, "segments": [spoken]}


def test_only_english_cues_are_held_to_the_reading_rate():
    # 37 characters spoken in 1.1 s before 0.9 s of quiet: the English cue holds to 1.48 s.
    words = [("Nothing", 0.0, 0.2), ("may", 0.2, 0.3), ("change", 0.3, 0.55), ("the", 0.55, 0.6)]
    words += [("source", 0.6, 0.85), ("record.", 0.85, 1.1), ("It", 2.0, 2.3), ("stays.", 2.3, 3.0)]
    english = one_segment(
        "Nothing may change the source record. It stays.",
        ["Nothing may change the source record. ", "It stays."],
        words,
    )
    cues = captions_timing.timed_caption_cues(english, "en")
    assert [(cue["start"], cue["end"]) for cue in cues] == [(0.0, pytest.approx(1.48)), (2.0, 3.0)]
    # 31 Chinese characters shown for 1.1 s keep their interval: Chinese cues have no rate.
    numbers = "一二三四五六七八九十" * 3
    spoken = [(ch, k * 1.1 / 30, (k + 1) * 1.1 / 30) for k, ch in enumerate(numbers)]
    chinese = one_segment(
        numbers + "。天地。",
        [numbers + "。", "天地。"],
        [*spoken, ("天", 2.0, 2.4), ("地", 2.4, 3.0)],
    )
    cues = captions_timing.timed_caption_cues(chinese, "zh")
    assert [(cue["start"], cue["end"]) for cue in cues] == [(0.0, pytest.approx(1.1)), (2.0, 3.0)]


@pytest.mark.parametrize(
    ("text", "display"),
    [
        (
            'An Agent hands back one sentence: "Done. All tests pass."',
            "An Agent hands back one sentence: “Done. All tests pass.”",
        ),
        ('"Deduplicate by date" fails, ', "“Deduplicate by date” fails, "),
        ('kept ("just in case")—"or not".', "kept (“just in case”)—“or not”."),
        ("the reviewer's notes", "the reviewer’s notes"),
    ],
)
def test_the_display_copy_sets_typographic_quotes(text, display):
    # Each mark becomes one character, so every cue keeps its offsets in the copy.
    assert captions_timing.typeset(text) == display
    assert len(display) == len(text)


def test_the_receipt_counts_the_cues_and_states_their_timing():
    # A Chinese edition has no reading rate, so no cue stands above one.
    fields = captions_timing.caption_receipt_fields({"captions": [{}, {}]}, "zh")
    assert fields == {
        "caption_count": 2,
        "caption_timing": captions_timing.CAPTION_TIMING,
        "captions_above_reading_rate": [],
    }
