"""Soundtrack assembly checks every selected recording against its script before mixing, and
counts the edition's runtime from its narration."""

import json
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import filmkit.narration.anchors as anchors
import filmkit.production as production
import filmkit.repository as repository
import filmkit.soundtrack.assembly as soundtrack_assembly
from filmkit.captions import CaptionError

REPOSITORY = repository.ROOT
RATE = 48000
# The timeline that the assembly wrote for the two chapters before any script marked an anchor.
GOLDEN = json.loads((Path(__file__).parent / "golden/two-chapters-timeline.json").read_text())


@pytest.fixture
def edition(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    performance = json.loads((REPOSITORY / "content/zh/film-script.json").read_text())[
        "voice_performance"
    ]

    def stage(script, recording, wav=b"RIFF"):
        (tmp_path / "content/zh").mkdir(parents=True, exist_ok=True)
        (tmp_path / "content/zh/film-script.json").write_text(json.dumps(script))
        (tmp_path / "take.wav").write_bytes(wav)
        evidence = production.Edition("zh").evidence
        evidence.mkdir(parents=True)
        (evidence / "narration-selected.json").write_text(json.dumps({"records": [recording]}))
        (evidence / "alignment-selected.json").write_text(json.dumps({"records": [{"id": "01"}]}))

    return performance, stage


def test_assembly_refuses_a_script_without_designed_pauses(edition):
    _, stage = edition
    stage({"segments": []}, {"id": "01"})
    with pytest.raises(ValueError, match="Assembly requires native speech with designed pauses"):
        soundtrack_assembly.assemble(production.Edition("zh"))


def test_assembly_refuses_a_recording_whose_text_differs(edition):
    performance, stage = edition
    script = {"voice_performance": performance, "segments": [{"id": "01", "text": "甲。"}]}
    stage(script, {"id": "01", "text": "乙。", "path": "take.wav", "wav_sha256": ""})
    with pytest.raises(ValueError, match="Selected recording text differs: 01"):
        soundtrack_assembly.assemble(production.Edition("zh"))


def test_assembly_refuses_a_recording_whose_waveform_differs(edition):
    performance, stage = edition
    script = {"voice_performance": performance, "segments": [{"id": "01", "text": "甲。"}]}
    stage(script, {"id": "01", "text": "甲。", "path": "take.wav", "wav_sha256": "0" * 64})
    with pytest.raises(ValueError, match="Selected recording waveform differs: 01"):
        soundtrack_assembly.assemble(production.Edition("zh"))


@pytest.mark.ffmpeg
def test_assembly_lays_out_each_recording_with_its_own_level_and_exact_samples(two_chapters):
    soundtrack_assembly.assemble(two_chapters)
    receipt = json.loads(two_chapters.audio_assembly.read_text())
    timeline = json.loads(two_chapters.timeline.read_text())
    records = receipt["records"]
    # Each record carries its own declared level gain.
    assert [record["level_gain_db"] for record in records] == [1.0, 0]
    # The quieter chapter is raised and the louder one lowered towards the film's level.
    assert records[0]["chapter_gain_db"] > 0 > records[1]["chapter_gain_db"]
    # Without a declared segment tolerance no segment has a gain of its own.
    assert receipt["designed_pause_policy"]["segment_level_tolerance"] is None
    assert [record["segment_gain_db"] for record in records] == [0.0, 0.0]
    gaps = [round(gap["seconds"] * RATE) for gap in receipt["gaps"]]
    assert [gap["kind"] for gap in receipt["gaps"]] == ["opening", "chapter"]
    assert records[0]["start_sample"] == gaps[0]
    assert records[1]["start_sample"] == gaps[0] + records[0]["frames"] + gaps[1]
    # The runtime is the count, the speech with its thought pauses, the designed gaps, the
    # closing quiet and the declared four seconds of credits, rounded up to a whole second; the
    # gaps, which have room, take the whole fraction, and the credits keep their length.
    closing, speech = round(receipt["closing_seconds"] * RATE), sum(r["frames"] for r in records)
    designed = round(3.0 * RATE) + round(3.4 * RATE)
    count = speech + designed + closing + 4 * RATE
    runtime = receipt["duration"]
    assert (type(runtime), runtime, timeline["duration"]) == (int, -(-count // RATE), runtime)
    assert sum(gaps) - designed == runtime * RATE - count
    assert receipt["credits_duration"] == timeline["credits_duration"] == 4
    # The credits as laid out are seconds with a fraction, also where they keep their length.
    assert type(timeline["credits_duration"]) is type(receipt["credits_duration"]) is float
    assert sum(gaps) + speech + closing + 4 * RATE == runtime * RATE
    assert receipt["samples_per_channel"] == runtime * RATE
    # What the assembly writes beside and over the script's keys is what every comparison of a
    # timeline with its script leaves out.
    script = repository.read(two_chapters.script)
    written = {key for key, value in timeline.items() if script.get(key) != value}
    assert written == production.ASSEMBLED
    assert timeline["segments"][-1]["end"] == runtime - 4
    # Each gap keeps its declared pause and stays within its limit.
    assert round(3.0 * RATE) <= gaps[0] <= round(9.0 * RATE)
    assert round(3.4 * RATE) <= gaps[1] <= round(9.0 * RATE)
    # One designed pause at each thought join, from the native quiet heard there.
    pauses = [record["designed_thought_pauses"] for record in records]
    assert [len(designed) for designed in pauses] == [1, 1]
    assert all(designed[0]["designed_quiet_seconds"] == 0.45 for designed in pauses)
    # Takes that begin and meet in quiet release no onset, at a join or where a clip begins.
    assert [designed[0]["released_onset_samples"] for designed in pauses] == [0, 0]
    assert [record["boundary_fades"]["released_onset_samples"] for record in records] == [0, 0]
    # The timeline places each voice where its samples are, with its words inside it.
    for segment, record in zip(timeline["segments"], records, strict=True):
        assert segment["voice_start"] == record["start_sample"] / RATE
        assert segment["voice_end"] == (record["start_sample"] + record["frames"]) / RATE
        assert all(
            segment["voice_start"] <= word["start"] <= word["end"] <= segment["voice_end"]
            for word in segment["words"]
        )
    with wave.open(str(two_chapters.soundtrack)) as audio:
        assert (audio.getnchannels(), audio.getframerate()) == (2, RATE)
        pcm = np.frombuffer(audio.readframes(audio.getnframes()), "<i2").reshape(-1, 2)
    assert len(pcm) == runtime * RATE
    assert not pcm[: records[0]["start_sample"]].any()
    assert not pcm[records[1]["start_sample"] + records[1]["frames"] :].any()
    # Both receipt writers give the caption fields the same place.
    assert list(receipt)[-4:] == [
        "caption_count",
        "alignment_limits",
        "caption_timing",
        "captions_above_reading_rate",
    ]
    assert receipt["caption_count"] == len(timeline["captions"]) == 4
    assert receipt["captions_above_reading_rate"] == []


# Two segments of one chapter: an opening gap, then a paragraph gap.
SEGMENTS = [
    {"id": "01", "chapter": "a", "text": "一二三。"},
    {"id": "02", "chapter": "a", "text": "四五六。"},
]


def allocated(designed_policy, monkeypatch, *, count: float, room: float):
    """The allocation of a narration whose speech with its thought pauses, designed gaps and
    closing quiet come to `count` seconds, with 3 s of credits, where the paragraph gap has
    `room` seconds up to its range's top and the opening gap none; and its clip's speech."""
    monkeypatch.setattr(soundtrack_assembly, "CREDITS_DURATION", 3)
    limits = {"opening": 3.0, "paragraph": 5.5, "chapter": 3.4}
    policy = designed_policy(designed_pause_limits=limits, paragraph_pause_range=[1.2, 1.6 + room])
    speech = round(count * RATE) - round(3.0 * RATE) - round(1.6 * RATE) - round(2.6 * RATE)
    clip = SimpleNamespace(samples=range(speech))
    return soundtrack_assembly.allocate(SEGMENTS, [clip], policy), speech


@pytest.mark.parametrize(
    ("count", "room", "runtime", "gaps", "credits"),
    [
        # The fraction of 0.86 s goes to the gaps, whose ranges have room for 2.40 s.
        (1472.14, 2.4, 1476, 0.86, 3.0),
        # The gaps take the 0.30 s they have room for, the credits the other 0.56 s.
        (1472.14, 0.3, 1476, 0.3, 3.56),
        # Every gap with a weight stands at its range's top: the credits take it all.
        (1472.14, 0.0, 1476, 0.0, 3.86),
        # A count of whole seconds leaves no fraction.
        (597.0, 2.4, 600, 0.0, 3.0),
    ],
)
def test_the_runtime_is_the_count_rounded_up_and_its_fraction_goes_to_gaps_then_credits(
    designed_policy, monkeypatch, count, room, runtime, gaps, credits
):
    allocation, speech = allocated(designed_policy, monkeypatch, count=count, room=room)
    assert (type(allocation.runtime), allocation.runtime) == (int, runtime)
    assert (allocation.free, allocation.credits) == (round(gaps * RATE), round(credits * RATE))
    assert allocation.credits_free == round((credits - 3) * RATE)
    # The laid-out parts fill the runtime to the sample. That the thought pauses keep their
    # designs is read on a laid-out soundtrack, by
    # `test_assembly_lays_out_each_recording_with_its_own_level_and_exact_samples`.
    laid = sum(allocation.gaps) + speech + allocation.closing + allocation.credits
    assert laid == runtime * RATE


class Decoded(Exception):
    """The assembly passed its checks of the bound recordings and began to decode them."""


def decoding(*_):
    raise Decoded


def write_take(path, *, cut: bool) -> None:
    """Write a mono thought take: half a second of tone that dies away or is cut, then quiet."""
    tone = 6000 * np.sin(2 * np.pi * 220 * np.arange(round(0.5 * RATE)) / RATE)
    if not cut:
        tail = round(0.2 * RATE)
        tone[-tail:] *= np.exp(-np.arange(tail) / (0.015 * RATE))
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(
            np.rint(np.concatenate([tone, np.zeros(round(0.3 * RATE))])).astype("<i2")
        )


def bind_thought_takes(edition, cut=()) -> None:
    """Bind two thought takes to each selected recording; the named thoughts are cut."""
    selected = json.loads(edition.narration_selected.read_text())
    for record in selected["records"]:
        groups = []
        for index in (1, 2):
            path = repository.ROOT / f"take-{record['id']}-{index}.wav"
            write_take(path, cut=f"{record['id']}.{index}" in cut)
            groups.append({"index": index, "path": path.name})
        record["utterance_groups"] = {"records": groups}
    edition.narration_selected.write_text(json.dumps(selected, ensure_ascii=False))


def test_assembly_refuses_thought_takes_cut_inside_their_last_syllable(two_chapters, monkeypatch):
    bind_thought_takes(two_chapters, cut={"01.1", "02.2"})
    monkeypatch.setattr(soundtrack_assembly, "_decode", decoding)
    # Every abrupt thought is named before any recording is decoded.
    with pytest.raises(
        soundtrack_assembly.AssemblyError,
        match=r"^Thought takes end abruptly without a declared release: 01\.1, 02\.2$",
    ):
        soundtrack_assembly.assemble(two_chapters)


def test_a_declared_release_lets_its_thought_take_end_abruptly(two_chapters, monkeypatch):
    bind_thought_takes(two_chapters, cut={"01.1"})
    script = repository.ROOT / two_chapters.script
    declared = json.loads(script.read_text())
    declared["voice_performance"]["released_tail_seconds"] = {"01.1": 0.12}
    script.write_text(json.dumps(declared, ensure_ascii=False))
    monkeypatch.setattr(soundtrack_assembly, "_decode", decoding)
    with pytest.raises(Decoded):
        soundtrack_assembly.assemble(two_chapters)


def test_assembly_refuses_a_value_the_chapter_metadata_cannot_hold_before_it_decodes(
    two_chapters, monkeypatch
):
    # A chapter title that ends in a backslash cannot be kept in chapters.ffmeta: the assembly
    # refuses it before a recording is decoded and before anything is written.
    script = repository.ROOT / two_chapters.script
    declared = json.loads(script.read_text())
    declared["segments"][1]["chapter_title"] = "B\\"
    script.write_text(json.dumps(declared, ensure_ascii=False))
    monkeypatch.setattr(soundtrack_assembly, "_decode", decoding)
    with pytest.raises(CaptionError) as refusal:
        soundtrack_assembly.assemble(two_chapters)
    # The assembly reads the script, and says so.
    assert str(refusal.value).startswith(
        'content/zh/film-script.json holds chapter_title of segment 02 "B\\\\": '
        "chapters.ffmeta cannot"
    )
    assert not two_chapters.artifacts.exists()


@pytest.mark.ffmpeg
def test_segments_of_one_chapter_are_leveled_within_the_declared_tolerance(two_chapters):
    # Without the declaration the two recordings stand as far apart as they were recorded.
    script = json.loads((repository.ROOT / two_chapters.script).read_text())
    for segment in script["segments"]:
        segment["chapter"], segment["chapter_title"] = "a", "A"
    (repository.ROOT / two_chapters.script).write_text(json.dumps(script, ensure_ascii=False))
    soundtrack_assembly.assemble(two_chapters)
    undeclared = two_chapters.soundtrack.read_bytes()
    records = json.loads(two_chapters.audio_assembly.read_text())["records"]
    assert [record["segment_gain_db"] for record in records] == [0.0, 0.0]
    # One chapter is the whole film here, so no chapter gain applies either.
    assert [record["chapter_gain_db"] for record in records] == [0.0, 0.0]
    # The tones stand 3.52 dB apart and the first declares 1 dB of gain: 1.26 dB to either
    # side of the chapter's median. Declared, each segment moves to 0.3 dB from it.
    script["voice_performance"]["segment_level_tolerance_db"] = 0.3
    (repository.ROOT / two_chapters.script).write_text(json.dumps(script, ensure_ascii=False))
    soundtrack_assembly.assemble(two_chapters)
    receipt = json.loads(two_chapters.audio_assembly.read_text())
    assert receipt["designed_pause_policy"]["segment_level_tolerance"] == 0.3
    gains = [record["segment_gain_db"] for record in receipt["records"]]
    assert gains == [pytest.approx(0.96, abs=0.02), pytest.approx(-0.96, abs=0.02)]
    assert [record["chapter_gain_db"] for record in receipt["records"]] == [0.0, 0.0]
    assert two_chapters.soundtrack.read_bytes() != undeclared


@pytest.mark.ffmpeg
def test_natural_thought_takes_assemble_the_same_soundtrack(two_chapters):
    soundtrack_assembly.assemble(two_chapters)
    unbound = two_chapters.soundtrack.read_bytes()
    bind_thought_takes(two_chapters)
    soundtrack_assembly.assemble(two_chapters)
    assert two_chapters.soundtrack.read_bytes() == unbound


@pytest.mark.ffmpeg
def test_assembly_refuses_an_unmarked_pause_above_its_limit_before_writing(two_chapters):
    # The second recording halts 0.6 s between 甲 and 乙, where its text has no mark.
    words = (("甲", 0.4, 0.9), ("乙", 1.5, 2.0), ("丙", 2.6, 3.1), ("丁", 3.1, 3.6))
    pcm = np.zeros(round(4.1 * RATE))
    for _, start, end in words:
        span = np.arange(round(start * RATE), round(end * RATE))
        pcm[span] = 9000 * np.sin(2 * np.pi * 440 * span / RATE)
    path = repository.ROOT / "take-02.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(np.rint(pcm).astype("<i2").tobytes())
    for record_file, key in (
        (two_chapters.narration_selected, "records"),
        (two_chapters.alignment_selected, "records"),
    ):
        bound = json.loads(record_file.read_text())
        bound[key][1]["wav_sha256"] = repository.sha(path)
        if "items" in bound[key][1]:
            bound[key][1]["items"] = [
                {"text": word, "start_time": start, "end_time": end} for word, start, end in words
            ]
        record_file.write_text(json.dumps(bound, ensure_ascii=False))
    refusal = r"^zh 02\.1: a 0\.(59|60) s pause between 甲 and 乙, where the text has no mark, "
    with pytest.raises(soundtrack_assembly.AssemblyError, match=refusal + r"exceeds its 0\.40 s"):
        soundtrack_assembly.assemble(two_chapters)
    for written in (two_chapters.soundtrack, two_chapters.timeline, two_chapters.audio_assembly):
        assert not written.exists()


@pytest.mark.ffmpeg
def test_a_timeline_without_anchors_keeps_the_bytes_written_before_anchors(two_chapters):
    soundtrack_assembly.assemble(two_chapters)
    assert two_chapters.timeline.read_text() == GOLDEN["timeline"]


@pytest.mark.ffmpeg
def test_each_anchor_takes_the_times_of_its_first_and_last_words(two_chapters):
    path = repository.ROOT / two_chapters.script
    script = json.loads(path.read_text())
    script["segments"][0]["anchored_groups"] = ["{pair}甲乙{/pair}。", "丙{last}丁{/last}。"]
    path.write_text(json.dumps(script, ensure_ascii=False))
    soundtrack_assembly.assemble(two_chapters)
    first, second = json.loads(two_chapters.timeline.read_text())["segments"]
    words = first["words"]
    assert first["anchored_groups"] == script["segments"][0]["anchored_groups"]
    # Each id in the order of its open mark: its first word's start, its last word's end, its
    # units among the segment's and its thought.
    assert list(first["anchors"].items()) == [
        (
            "pair",
            {"start": words[0]["start"], "end": words[1]["end"], "units": [0, 2], "thought": 1},
        ),
        (
            "last",
            {"start": words[3]["start"], "end": words[3]["end"], "units": [3, 4], "thought": 2},
        ),
    ]
    # A segment of an edition that marks anchors holds an empty object where it marks none.
    assert second["anchors"] == {}


def test_the_resolver_refuses_words_that_are_not_the_units_of_their_text():
    segment = {"id": "01", "anchored_groups": ["{a}甲乙{/a}。"], "utterance_groups": ["甲乙。"]}
    timeline = {
        "segments": [{**segment, "text": "甲乙。", "words": [{"text": "甲", "start": 1, "end": 2}]}]
    }
    with pytest.raises(anchors.AnchorError, match="zh 01: its words are not the units of its text"):
        anchors.place(timeline, "zh")


@pytest.mark.ffmpeg
def test_assembly_places_the_anchors_before_it_writes_anything(two_chapters, monkeypatch):
    def refuse(timeline, code):
        raise anchors.AnchorError(f"{code} 01: its words are not the units of its text")

    monkeypatch.setattr(soundtrack_assembly.anchors, "place", refuse)
    with pytest.raises(anchors.AnchorError, match="zh 01: its words"):
        soundtrack_assembly.assemble(two_chapters)
    for written in (two_chapters.soundtrack, two_chapters.timeline, two_chapters.audio_assembly):
        assert not written.exists()


def test_a_timeline_whose_script_marks_no_anchor_holds_none():
    words = [{"text": "甲", "start": 1, "end": 2}, {"text": "乙", "start": 2, "end": 3}]
    unmarked = {"id": "01", "anchored_groups": ["甲乙。"], "utterance_groups": ["甲乙。"]}
    timeline = {"segments": [{**unmarked, "text": "甲乙。", "words": words}]}
    anchors.place(timeline, "zh")
    assert "anchors" not in timeline["segments"][0]
