"""Soundtrack assembly checks every selected recording against its script before mixing."""

import json
import wave

import numpy as np
import pytest

import filmkit.production as production
import filmkit.repository as repository
import filmkit.soundtrack.assembly as soundtrack_assembly

REPOSITORY = repository.ROOT
RATE = 48000


@pytest.fixture
def edition(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    performance = json.loads((REPOSITORY / "content/film-script.json").read_text())[
        "voice_performance"
    ]

    def stage(script, recording, wav=b"RIFF"):
        (tmp_path / "content").mkdir(exist_ok=True)
        (tmp_path / "content/film-script.json").write_text(json.dumps(script))
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
    # The gaps, the speech and the closing quiet fill the runtime before the credits exactly.
    gaps = [round(gap["seconds"] * RATE) for gap in receipt["gaps"]]
    assert [gap["kind"] for gap in receipt["gaps"]] == ["opening", "chapter"]
    assert records[0]["start_sample"] == gaps[0]
    assert records[1]["start_sample"] == gaps[0] + records[0]["frames"] + gaps[1]
    closing = round(receipt["closing_seconds"] * RATE)
    assert sum(gaps) + sum(record["frames"] for record in records) + closing == 20 * RATE
    assert receipt["samples_per_channel"] == 24 * RATE
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
    assert len(pcm) == 24 * RATE
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
