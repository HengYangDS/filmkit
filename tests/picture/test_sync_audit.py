"""Exercise the sound-picture sync audit on a small timeline and label trace."""

import json
import re

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.picture.sync_audit as picture_sync_audit
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError


def timeline():
    words = [
        ("Test", 1.0, 1.3),
        ("the", 1.3, 1.5),
        ("judgment.", 1.5, 2.0),
        ("Solve", 4.0, 4.4),
        ("the", 4.4, 4.6),
        ("whole", 5.0, 5.5),
        ("problem.", 6.0, 6.5),
    ]
    segment = {
        "id": "01",
        "text": "Test the judgment. Solve the whole problem.",
        "utterance_groups": ["Test the judgment. ", "Solve the whole problem."],
        "words": [{"text": text, "start": a, "end": b} for text, a, b in words],
    }
    return {"segments": [segment]}


def line(t, label, contrast=4.0, scene="01"):
    return f"{t:.2f}\t{scene}\t{contrast:.2f}\t1.000\t{label}\n"


def frames(a, b, label, scene="01"):
    """One trace row per 0.1 s frame from a to b inclusive."""
    return [line(a + k / 10, label, scene=scene) for k in range(round((b - a) * 10) + 1)]


def test_labels_are_judged_against_their_spoken_clause():
    trace = [
        line(1.1, "Test the judgment"),
        line(0.4, " Solve the whole problem"),
        line(9.0, "Unspoken name"),
        line(1.2, "faint", contrast=2.0),
    ]
    report, judged = picture_sync_audit.audit(timeline(), trace)
    verdicts = {row["label"]: row["verdict"] for row in judged}
    assert verdicts == {
        "Test the judgment": "in-sync",
        "Solve the whole problem": "before-clause",
    }
    assert report["labels_judged"] == 2
    assert report["labels_unmatched"] == 1
    assert report["unmatched"] == [{"scene": "01", "label": "Unspoken name", "legible": 9.0}]
    assert report["far_from_words"] == []
    assert report["out_of_sync"] == 1
    assert report["by_scene"] == {"01": 1}


def test_a_label_shown_far_from_its_only_words_is_listed():
    report = picture_sync_audit.audit(timeline(), [line(12.5, "the judgment")])[0]
    assert report["labels_unmatched"] == 1
    assert report["unmatched"] == []
    assert report["out_of_sync"] == 0
    assert report["far_from_words"] == [
        {"scene": "01", "label": "the judgment", "legible": 12.5, "spoken": [1.3]}
    ]


def test_a_label_far_ahead_or_behind_its_words_is_out_of_sync():
    ahead = picture_sync_audit.audit(timeline(), [line(4.2, "problem")])[0]["findings"]
    late = picture_sync_audit.audit(timeline(), [line(3.0, "judgment")])[0]["findings"]
    assert [row["verdict"] for row in ahead + late] == [
        "ahead-in-clause",
        "after-words",
    ]


def scene(scene_id, *thoughts):
    """A timeline of one scene whose thoughts are each a list of words with their times."""
    texts = [" ".join(text for text, _, _ in thought) for thought in thoughts]
    groups = [text + " " for text in texts[:-1]] + texts[-1:]
    words = [{"text": text, "start": a, "end": b} for thought in thoughts for text, a, b in thought]
    segment = {"id": scene_id, "text": "".join(groups), "utterance_groups": groups, "words": words}
    return {"segments": [segment]}


# "available" said 0.19 s after the label "Availability" stands at 330.17 s, "availability" 8.43 s
# after it, in the next thought.
AVAILABLE = [("Data", 330.0, 330.18), ("is", 330.18, 330.36), ("available", 330.36, 330.9)]
AVAILABLE += [("when", 330.9, 331.1), ("it", 331.1, 331.2), ("is", 331.2, 331.3)]
AVAILABLE += [("needed.", 331.3, 331.8)]
AVAILABILITY = [("Availability", 338.6, 339.2), ("is", 339.2, 339.3), ("checked.", 339.3, 339.8)]


def test_an_english_label_is_judged_by_its_inflected_words_in_its_own_thought():
    film = scene("05", AVAILABLE, AVAILABILITY)
    report, judged = picture_sync_audit.audit(film, [line(330.17, "Availability", scene="05")])
    assert report["far_from_words"] == []
    assert judged == [
        {
            "scene": "05",
            "label": "Availability",
            "legible": 330.17,
            "spoken": 330.36,
            "spoken_end": 330.9,
            "clause_start": 330.0,
            "delta": -0.19,
            "occurrences": 1,
            "verdict": "in-sync",
            "match": "inflected",
        }
    ]


def test_an_exact_occurrence_within_8_s_still_judges_an_english_label():
    film = scene("05", AVAILABLE, AVAILABILITY)
    # Its words said 1.2 s after it stands judge it, as before.
    near = picture_sync_audit.audit(film, [line(337.4, "Availability", scene="05")])[1]
    assert [(row["spoken"], row["delta"], row["match"]) for row in near] == [(338.6, -1.2, "exact")]
    # They judge it within 8 s even where its own thought says the word in another form.
    within = picture_sync_audit.audit(film, [line(331.0, "Availability", scene="05")])[1]
    assert [(row["spoken"], row["verdict"], row["match"]) for row in within] == [
        (338.6, "before-clause", "exact")
    ]


def test_words_that_only_look_alike_do_not_match():
    # "Publish" stands over "public", whose stem differs; "Published" over "publish" matches.
    public = [("The", 10.0, 10.2), ("public", 10.2, 10.6), ("record", 10.6, 11.0)]
    public += [("is", 11.0, 11.1), ("read.", 11.1, 11.5)]
    publish = [("We", 20.0, 20.1), ("publish", 20.1, 20.5), ("it", 20.5, 20.6)]
    publish += [("daily.", 20.6, 21.0)]
    film = scene("09", public, publish)
    trace = [line(10.1, "Publish", scene="09"), line(20.0, "Published", scene="09")]
    report, judged = picture_sync_audit.audit(film, trace)
    assert report["far_from_words"] == [
        {"scene": "09", "label": "Publish", "legible": 10.1, "spoken": [20.1]}
    ]
    assert [(row["label"], row["spoken"], row["match"]) for row in judged] == [
        ("Published", 20.1, "inflected")
    ]


def test_an_inflected_match_outside_the_labels_thought_is_not_taken():
    records = [("Records", 332.5, 333.0), ("are", 333.0, 333.2), ("checked.", 333.2, 334.0)]
    late = [("Availability", 345.0, 345.6), ("matters.", 345.6, 346.2)]
    film = scene("05", AVAILABLE, records, late)
    # Standing in the second thought, the label is not judged by the first thought's "available".
    report, judged = picture_sync_audit.audit(film, [line(333.0, "Availability", scene="05")])
    assert judged == []
    assert report["far_from_words"] == [
        {"scene": "05", "label": "Availability", "legible": 333.0, "spoken": [345.0]}
    ]
    # Standing in the first thought, it is.
    first = picture_sync_audit.audit(film, [line(330.17, "Availability", scene="05")])[1]
    assert [(row["spoken"], row["match"]) for row in first] == [(330.36, "inflected")]


def test_chinese_labels_match_as_before():
    words = [("验收", 1.0, 1.4), ("标准。", 1.4, 1.8), ("可用", 4.0, 4.4), ("数据。", 4.4, 4.8)]
    film = scene("02", words[:2], words[2:])
    film["segments"][0]["text"] = "验收标准。可用数据。"
    film["segments"][0]["utterance_groups"] = ["验收标准。", "可用数据。"]
    trace = [line(1.1, "验收标准", scene="02"), line(4.2, "可用性", scene="02")]
    report, judged = picture_sync_audit.audit(film, trace)
    assert [(row["label"], row["spoken"], row["match"]) for row in judged] == [
        ("验收标准", 1.0, "exact")
    ]
    # No Chinese label is looked for by another form of its words.
    assert report["unmatched"] == [{"scene": "02", "label": "可用性", "legible": 4.2}]


# "Acceptance" said in three thoughts of one scene: at 214.4 s, 217.0 s and 330.4 s.
ACCEPTANCE = scene(
    "06",
    [("Acceptance", 214.4, 215.0), ("comes", 215.0, 215.3), ("first.", 215.3, 215.8)],
    [("Acceptance", 217.0, 217.6), ("is", 217.6, 217.7), ("checked.", 217.7, 218.2)],
    [("Then", 330.0, 330.2), ("acceptance", 330.4, 331.0), ("is", 331.0, 331.1)],
)


def test_a_label_shown_again_on_its_words_is_judged_at_each_appearance():
    # Legible from 214.2 s, illegible from 240.1 s, and legible again at 330.2 s on its words.
    trace = frames(214.2, 240.0, "Acceptance", "06") + frames(330.2, 332.0, "Acceptance", "06")
    report, judged = picture_sync_audit.audit(ACCEPTANCE, trace)
    assert [(row["legible"], row["spoken"], row["verdict"]) for row in judged] == [
        (214.2, 214.4, "in-sync"),
        (330.2, 330.4, "in-sync"),
    ]
    assert report["labels_judged"] == 2
    assert report["recalls"] == []


def test_a_label_shown_again_without_its_words_is_a_recall():
    # Legible on its words, illegible for 3 s, then legible again with its words not said again.
    label = "Solve the whole problem"
    trace = frames(4.0, 5.0, label) + frames(8.0, 9.0, label)
    report, judged = picture_sync_audit.audit(timeline(), trace)
    assert [(row["legible"], row["spoken"]) for row in judged] == [(4.0, 4.0)]
    assert report["recalls"] == [{"scene": "01", "label": label, "legible": 8.0}]
    assert report["far_from_words"] == []
    assert report["labels_unmatched"] == 0


def test_a_later_appearance_takes_the_nearest_words_no_earlier_one_took():
    # Shown again 3 s after it went, the label takes the words said 2 s before it, which the
    # first appearance left; shown a third time, it finds no words within 8 s.
    trace = frames(214.2, 216.0, "Acceptance", "06") + frames(219.0, 221.0, "Acceptance", "06")
    trace += frames(300.0, 302.0, "Acceptance", "06")
    report, judged = picture_sync_audit.audit(ACCEPTANCE, trace)
    assert [(row["legible"], row["spoken"]) for row in judged] == [(214.2, 214.4), (219.0, 217.0)]
    assert report["recalls"] == [{"scene": "06", "label": "Acceptance", "legible": 300.0}]


def test_a_label_faded_briefly_at_a_stage_cut_is_judged_once():
    # It fades for 0.4 s at a cut and stands again in its place while its words come again.
    trace = frames(214.2, 216.0, "Acceptance", "06") + frames(216.5, 218.0, "Acceptance", "06")
    report, judged = picture_sync_audit.audit(ACCEPTANCE, trace)
    assert [(row["legible"], row["spoken"]) for row in judged] == [(214.2, 214.4)]
    assert report["recalls"] == []


def test_speech_without_a_legible_name_for_over_a_second_is_reported():
    trace = frames(1.0, 2.0, "Test the judgment") + frames(5.8, 6.5, "Solve the whole problem")
    trace += [line(4.5, "faint", contrast=2.0), line(4.6, "17")]
    report = picture_sync_audit.continuity(timeline(), trace, step=0.1)
    assert report["unnamed_speech"] == [{"thought": "01.2", "from": 4.0, "to": 5.7}]
    named = frames(1.0, 2.0, "Test the judgment") + frames(5.0, 6.5, "Solve the whole problem")
    assert picture_sync_audit.continuity(timeline(), named, step=0.1)["unnamed_speech"] == []


def test_a_previous_picture_held_over_a_second_into_a_thought_is_reported():
    held = frames(1.0, 5.2, "Test the judgment") + frames(5.3, 6.5, "Solve the whole problem")
    assert picture_sync_audit.continuity(timeline(), held, step=0.1)["held_over"] == [
        {"thought": "01.2", "held": 1.3}
    ]
    cut = frames(1.0, 4.6, "Test the judgment") + frames(4.7, 6.5, "Solve the whole problem")
    assert picture_sync_audit.continuity(timeline(), cut, step=0.1)["held_over"] == []


def captioned(*cues):
    """The timeline with caption cues, each its start, end and text."""
    film = timeline()
    film["captions"] = [
        {"start": a, "end": b, "text": text, "segment": "01"} for a, b, text in cues
    ]
    return film


def test_a_cue_drawn_whole_as_one_label_is_a_whole_echo():
    # The label was drawn before the cue; it repeats the cue's words while the cue shows.
    film = captioned((4.0, 6.5, "Solve the whole problem."), (1.0, 2.0, "Test it."))
    trace = frames(3.0, 6.5, "Solve the whole problem") + frames(1.0, 2.0, "Test it")
    echoes = picture_sync_audit.continuity(film, trace, step=0.1)["caption_echoes"]
    # A cue of fewer than three words is not judged.
    assert echoes == [
        {
            "start": 4.0,
            "segment": "01",
            "text": "Solve the whole problem.",
            "whole": True,
            "quoted": False,
            "share": 1.0,
            "labels": ["Solve the whole problem"],
        }
    ]


def test_a_cue_that_is_one_quotation_is_not_a_whole_echo():
    # The narration reads out a document the picture shows: a label that holds the quotation's
    # words depicts the document, so the cue is listed at 100% and not as a whole echo. Two
    # quotations joined by other words are not one quotation.
    film = captioned(
        (4.0, 6.5, "“Solve the whole problem.”"),
        (7.0, 9.5, "“Solve it” and “test it”"),
    )
    trace = frames(3.0, 6.5, "Solve the whole problem") + frames(7.0, 9.5, "Solve it and test it")
    quoted, joined = picture_sync_audit.continuity(film, trace, step=0.1)["caption_echoes"]
    assert (quoted["whole"], quoted["quoted"], quoted["share"]) == (False, True, 1.0)
    assert (joined["whole"], joined["quoted"]) == (True, False)


def test_a_cue_mostly_drawn_as_labels_during_it_is_a_partial_echo():
    film = captioned((4.0, 6.5, "Solve the whole problem."))
    # Two labels drawn during the cue repeat all four words between them.
    parts = frames(4.1, 6.5, "Solve the") + frames(5.1, 6.5, "Whole problem")
    (echo,) = picture_sync_audit.continuity(film, parts, step=0.1)["caption_echoes"]
    assert (echo["whole"], echo["share"], echo["labels"]) == (
        False,
        1.0,
        ["Solve the", "Whole problem"],
    )
    # A label drawn before the cue counts only for a whole echo, and a label that holds more
    # than the cue's words repeats none of them as a label of its own.
    earlier = frames(3.0, 6.5, "Solve the whole") + frames(6.0, 6.5, "problem")
    longer = frames(4.1, 6.5, "Solve the whole problem today")
    for trace in (earlier, longer):
        assert picture_sync_audit.continuity(film, trace, step=0.1)["caption_echoes"] == []


def test_chinese_cues_are_compared_by_character():
    film = timeline()
    film["captions"] = [{"start": 4.0, "end": 6.5, "text": "一项正式变更，", "segment": "01"}]
    trace = frames(4.1, 6.5, "一项") + frames(4.5, 6.5, "正式变更")
    (echo,) = picture_sync_audit.continuity(film, trace, step=0.1)["caption_echoes"]
    assert (echo["whole"], echo["share"]) == (False, 1.0)


def mark(t, box, named, scene="01"):
    return f"{t:.2f}\t{scene}\t" + "\t".join(str(v) for v in box) + f"\t{int(named)}\n"


def test_a_mark_that_stands_before_its_name_is_reported_as_a_seat():
    samples = range(20)
    # A seat waits 1.2 s for its name; a mark named from its first frame and a mark named
    # after 0.5 s are not seats, nor is an illustration that is never named.
    marks = [mark(4.0 + k / 10, (300, 400, 340, 440), named=k >= 12) for k in samples]
    marks += [mark(4.0 + k / 10, (600, 400, 640, 440), named=True) for k in samples]
    marks += [mark(4.0 + k / 10, (900, 400, 940, 440), named=k >= 5) for k in samples]
    marks += [mark(4.0 + k / 10, (1200, 400, 1240, 440), named=False) for k in samples]
    assert picture_sync_audit.seats(timeline(), marks, step=0.1) == [
        {"thought": "01.2", "at": 4.0, "lag": 1.2, "box": [300, 400, 340, 440]}
    ]


def test_a_ruled_row_that_stands_before_its_name_is_reported_as_a_seat():
    # A ruled row has no height; it is still followed from frame to frame.
    rows = [mark(4.0 + k / 10, (300, 400, 900, 400), named=k >= 10) for k in range(20)]
    assert picture_sync_audit.seats(timeline(), rows, step=0.1) == [
        {"thought": "01.2", "at": 4.0, "lag": 1.0, "box": [300, 400, 900, 400]}
    ]


def test_parts_are_judged_on_their_own_and_reports_are_deterministic(tmp_path):
    trace = [line(1.1, "Test · Solve"), line(4.1, "Solve")]
    judged = picture_sync_audit.audit(timeline(), trace)[1]
    assert sorted(row["label"] for row in judged) == ["Solve", "Test"]
    timeline_path, trace_path = tmp_path / "timeline.json", tmp_path / "trace.tsv"
    marks_path = tmp_path / "marks.tsv"
    timeline_path.write_text(json.dumps(timeline()))
    trace_path.write_text("".join(trace))
    marks_path.write_text(mark(1.0, (300, 400, 340, 440), named=True))
    outputs = []
    for name in ("first.json", "second.json"):
        out = tmp_path / name
        picture_sync_audit.main(
            [
                str(timeline_path),
                str(trace_path),
                "--out",
                str(out),
                "--bind",
                str(timeline_path),
                "--marks",
                str(marks_path),
            ]
        )
        outputs.append(out.read_text())
    assert outputs[0] == outputs[1]
    written = json.loads(outputs[0])
    assert written["bound_timeline"] == {
        "path": str(timeline_path),
        "sha256": repository.sha(timeline_path),
    }
    # The trace comes from running the composition, so the report binds its script too.
    composition = repository.ROOT / picture_rendering.COMPOSITION_SCRIPT
    assert written["composition_sha256"] == repository.sha(composition)
    assert set(written["continuity"]) == {"unnamed_speech", "held_over", "seats", "caption_echoes"}


def test_words_that_do_not_cover_their_segment_text_are_refused():
    # Clause starts follow the text's stops, so the words must spell the whole text.
    uncovered = timeline()
    uncovered["segments"][0]["words"].pop()
    with pytest.raises(PictureError, match=re.escape("01: the aligned words do not cover")):
        picture_sync_audit.audit(uncovered, [line(1.1, "Test the judgment")])


def test_the_summary_keys_are_the_report_counts():
    report = picture_sync_audit.audit(timeline(), [line(4.2, "problem")])[0]
    assert picture_sync_audit.VERDICTS == ("before-clause", "ahead-in-clause", "after-words")
    assert {key: report[key] for key in picture_sync_audit.SUMMARY_KEYS} == {
        "tolerance": 0.3,
        "labels_judged": 1,
        "labels_unmatched": 0,
        "out_of_sync": 1,
        "before-clause": 0,
        "ahead-in-clause": 1,
        "after-words": 0,
    }
