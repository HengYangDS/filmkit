"""The pause heard at each word boundary, the flow limits, and the steps between thoughts."""

import numpy as np
import pytest

import filmkit.narration.flow as flow
from filmkit.film import Flow, FlowException
from filmkit.narration.spoken_units import AlignmentError

RATE = 24000


def voiced(spans, seconds, *, rate=RATE, hz=200.0, amplitude=0.3):
    """Mono samples voicing a tone over each (start, end) span and silent elsewhere."""
    mono = np.zeros(round(seconds * rate))
    for start, end in spans:
        span = np.arange(round(start * rate), round(end * rate))
        mono[span] = amplitude * np.sin(2 * np.pi * hz * span / rate)
    return mono


def segment(groups, words, mono=None, *, rate=RATE, name="05"):
    """A segment of thoughts whose words (text, start, end) are voiced by `mono` or by tones."""
    if mono is None:
        mono = voiced([(start, end) for _, start, end in words], words[-1][2] + 0.3, rate=rate)
    return flow.Narrated(
        name,
        "".join(groups),
        list(groups),
        [{"text": text, "start": start, "end": end} for text, start, end in words],
        flow.Recording(np.asarray(mono, dtype=np.float32), rate),
    )


# 0.49 s of quiet between 的 and Agent, and 0.34 s at a comma.
SWITCH = segment(
    ["换成可以替换的 Agent 来做。", "先看数据，再决定。"],
    [
        ("换", 0.2, 0.4),
        ("成", 0.4, 0.6),
        ("可", 0.6, 0.8),
        ("以", 0.8, 1.0),
        ("替", 1.0, 1.2),
        ("换", 1.2, 1.4),
        ("的", 1.4, 1.6),
        ("Agent", 2.09, 2.49),
        ("来", 2.49, 2.69),
        ("做", 2.69, 2.89),
        ("先", 3.4, 3.6),
        ("看", 3.6, 3.8),
        ("数", 3.8, 4.0),
        ("据", 4.0, 4.2),
        ("再", 4.54, 4.74),
        ("决", 4.74, 4.94),
        ("定", 4.94, 5.14),
    ],
)
# 0.36 s between two clauses the text leaves unmarked.
CLAUSES = segment(
    ["We commit and check. ", "Then we ship."],
    [
        ("We", 0.2, 0.4),
        ("commit", 0.4, 0.8),
        ("and", 1.16, 1.36),
        ("check", 1.36, 1.8),
        ("Then", 2.3, 2.5),
        ("we", 2.5, 2.7),
        ("ship", 2.7, 3.1),
    ],
    name="08",
)


def heard(narrated) -> dict:
    return {(b.left, b.right): b for b in flow.boundaries(narrated)}


def test_a_pause_at_a_script_switch_is_heard_with_no_mark():
    found = heard(SWITCH)
    assert found["的", "Agent"] == flow.Boundary("05.1", "的", "Agent", 1.6, 0.49, "", True)
    # Speech that runs on holds no pause: inside a word, as 换成, or where the script switches.
    assert found["Agent", "来"].pause_s == found["换", "成"].pause_s == 0.0
    assert found["Agent", "来"].switch and not found["换", "成"].switch
    # The quiet between thoughts is heard at their join, which a sentence end marks.
    assert (found["做", "先"].thought, found["做", "先"].marks) == ("05.1", "。")


def test_a_pause_at_a_comma_is_heard_with_its_mark():
    pause = heard(SWITCH)["据", "再"]
    assert (pause.thought, pause.pause_s, pause.marks, pause.switch) == ("05.2", 0.34, "，", False)
    assert flow.limit(pause, Flow()) is None


def test_a_quotation_mark_is_not_a_pause_of_its_own():
    words = [("说", 0.2, 0.4), ("Agent", 0.7, 1.1), ("就", 1.1, 1.3), ("好", 1.3, 1.5)]
    quoted = segment(["说“Agent”就好。"], words)
    assert flow.gate("zh", [quoted], Flow()) == [
        "zh 05.1: a 0.30 s pause between 说 and Agent, where the text holds only “ and the script "
        "switches, exceeds its 0.20 s limit"
    ]


def test_quiet_is_heard_against_the_speech_median():
    words = [("先", 0.2, 0.4), ("看", 0.6, 0.8)]
    mono = voiced([(0.2, 0.4), (0.6, 0.8)], 1.1)
    # A stretch 20 dB below the speech is still voice; 30 dB below, it is heard as quiet.
    for below, pause in ((20, 0.0), (30, 0.2)):
        between = voiced([(0.4, 0.6)], 1.1, amplitude=0.3 * 10 ** (-below / 20))
        assert flow.boundaries(segment(["先看。"], words, mono + between))[0].pause_s == pause


def test_words_meet_their_text_across_hyphens_apostrophes_and_marks():
    words = [("Crossrole", 0.2, 0.7), ("checks", 0.7, 1.0), ("the", 1.2, 1.3)]
    words += [("Agent's", 1.3, 1.7), ("work", 1.7, 2.0)]
    narrated = segment(["Cross-role checks, the Agent's work."], words)
    found = flow.boundaries(narrated)
    assert [(b.left, b.right, b.marks) for b in found] == [
        ("Crossrole", "checks", ""),
        ("checks", "the", ","),
        ("the", "Agent's", ""),
        ("Agent's", "work", ""),
    ]
    # Words that do not cover their text are refused with their segment.
    narrated.words.pop()
    with pytest.raises(AlignmentError, match="^05: Alignment does not cover exact text"):
        flow.boundaries(narrated)


def test_aligned_items_become_timed_words():
    item = {"text": "data", "start_time": 0.5, "end_time": 0.9}
    assert flow.timed([item]) == [{"text": "data", "start": 0.5, "end": 0.9}]


def keep(code, thought, left, right):
    return FlowException(edition=code, thought=thought, left=left, right=right, reason="Kept.")


def test_an_unmarked_pause_above_its_limit_is_refused_by_name():
    found = flow.boundaries(SWITCH)
    assert flow.refusals("zh", flow.judge("zh", found, Flow())) == [
        "zh 05.1: a 0.49 s pause between 的 and Agent, where the text has no mark and the "
        "script switches, exceeds its 0.20 s limit"
    ]
    # A clause pause the text leaves unmarked stays within 0.4 s, and is listed for listening.
    judged = flow.judge("en", flow.boundaries(CLAUSES), Flow())
    assert (judged.refused, [(row["left"], row["right"]) for row in judged.listen]) == (
        [],
        [("commit", "and")],
    )
    # A film may declare other limits.
    assert flow.judge("en", flow.boundaries(CLAUSES), Flow(unmarked_limit_s=0.3)).refused


def test_an_exception_keeps_its_boundary_and_a_stale_one_is_refused():
    found = flow.boundaries(SWITCH)
    kept = keep("zh", "05.1", "的", "agent")
    judged = flow.judge("zh", found, Flow(exceptions=(kept, keep("en", "05.1", "a", "b"))))
    assert (judged.refused, judged.stale) == ([], [])
    assert [(row["left"], row["pause_s"], row["reason"]) for row in judged.declared] == [
        ("的", 0.49, "Kept.")
    ]
    stale = Flow(exceptions=(kept, keep("zh", "05.2", "看", "定")))
    assert flow.gate("zh", [SWITCH], stale) == [
        "zh: the [narration.flow] exception 05.2 between 看 and 定 matches no boundary of the "
        "narration"
    ]
    # Part of a narration, such as one take, judges no exception stale.
    assert flow.judge("zh", found, stale, whole=False).stale == []


def test_a_take_records_its_longest_unmarked_pause_and_whether_it_is_fluent():
    words, recording = CLAUSES.words[:4], CLAUSES.recording
    take = flow.take_flow("en", "08.1", "We commit and check. ", words, recording, Flow())
    assert take == {
        "longest_unmarked_pause": {
            "thought": "08.1",
            "left": "commit",
            "right": "and",
            "at": 0.8,
            "pause_s": 0.36,
            "marks": "",
            "switch": False,
            "limit_s": 0.4,
        },
        "fluent": True,
    }
    strict = Flow(unmarked_limit_s=0.3)
    halting = flow.take_flow("en", "08.1", "We commit and check. ", words, recording, strict)
    assert halting["fluent"] is False
    assert flow.take_flow("en", "08.1", "Other words.", words, recording, Flow())["fluent"] is False


def test_the_flow_record_summarizes_pauses_by_their_marks():
    record = flow.flow_record("zh", [SWITCH], Flow())
    assert record["boundaries"] == 16
    assert record["unmarked_pause_seconds"]["switch"] == {
        "count": 2,
        "median": 0.24,
        "p99": 0.49,
        "max": 0.49,
    }
    assert record["marked_pause_seconds"]["，"] == {
        "count": 1,
        "median": 0.34,
        "p99": 0.34,
        "max": 0.34,
    }
    assert [row["left"] for row in record["above_limit"]] == ["的"]


def thought(start: float, words: int, *, hz: float = 200.0, amplitude: float = 0.1):
    """One second of a tone from `start`, aligned as `words` words of "ta"."""
    rate = 48000
    span = np.arange(round(start * rate), round((start + 1) * rate))
    tone = amplitude * np.sin(2 * np.pi * hz * (span - span[0]) / rate)
    step = 1 / words
    aligned = [("ta", start + k * step, start + (k + 1) * step) for k in range(words)]
    return span, tone, aligned


def test_continuity_steps_measure_rate_pitch_and_level_between_thoughts():
    # Each step changes one measure: 3 semitones up, then 2 dB louder, then twice the
    # syllables in the same voiced second. A thought in the next segment is not compared.
    plans = [
        (0.5, 4, 200.0, 0.1),
        (2.0, 4, 200.0 * 2 ** (3 / 12), 0.1),
        (3.5, 4, 200.0 * 2 ** (3 / 12), 0.1 * 10 ** (2 / 20)),
        (5.0, 8, 200.0 * 2 ** (3 / 12), 0.1 * 10 ** (2 / 20)),
        (6.5, 4, 100.0, 0.05),
    ]
    mono, segments = np.zeros(8 * 48000), []
    for start, words, hz, amplitude in plans:
        span, tone, aligned = thought(start, words, hz=hz, amplitude=amplitude)
        mono[span] = tone
        segments.append(aligned)
    recording = flow.Recording(mono.astype(np.float32), 48000)
    groups = [" ".join(["Ta"] * len(words)) + ". " for words in segments]
    first = flow.Narrated(
        "01",
        "".join(groups[:4]),
        groups[:4],
        [{"text": t, "start": a, "end": b} for words in segments[:4] for t, a, b in words],
        recording,
    )
    second = flow.Narrated(
        "02",
        groups[4],
        groups[4:],
        [{"text": t, "start": a, "end": b} for t, a, b in segments[4]],
        recording,
    )
    record = flow.continuity_record("en", [first, second])
    assert record["thoughts"] == 5
    steps = {step["thoughts"]: step for step in record["steps"]}
    assert list(steps) == ["01.1>01.2", "01.2>01.3", "01.3>01.4"]
    assert steps["01.1>01.2"]["pitch_semitones"] == pytest.approx(3.0, abs=0.15)
    assert steps["01.2>01.3"]["level_db"] == pytest.approx(2.0, abs=0.05)
    assert steps["01.3>01.4"]["rate_ratio"] == 2.0
    assert (steps["01.2>01.3"]["rate_ratio"], steps["01.3>01.4"]["pitch_semitones"]) == (1.0, 0.0)
    largest = record["largest"]
    assert [step["thoughts"] for step in largest["rate_ratio"]][:1] == ["01.3>01.4"]
    assert [step["thoughts"] for step in largest["pitch_semitones"]] == ["01.1>01.2"]
    assert [step["thoughts"] for step in largest["level_db"]][:1] == ["01.2>01.3"]
    # The listening plan hears the largest steps and the pauses within their limits.
    assert flow.listening("en", [first, second], Flow()) == {"pauses": [], "steps": largest}
    moments = flow.listening("en", [CLAUSES, first, second], Flow())
    assert [(row["left"], row["pause_s"]) for row in moments["pauses"]] == [("commit", 0.36)]


def test_syllables_count_chinese_characters_and_latin_vowel_groups():
    assert flow.syllables("换成 Agent 来做。", "zh") == 6
    assert flow.syllables("Agents review the data.", "en") == 7
