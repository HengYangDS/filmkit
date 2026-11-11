"""Fixtures shared by the soundtrack tests: a complete designed pause contract, and two chapters of
one recording each, selected and aligned for assembly."""

import hashlib
import json
import wave

import numpy as np
import pytest

import filmkit.production as production
import filmkit.repository as repository
import filmkit.soundtrack.assembly as soundtrack_assembly
import filmkit.soundtrack.policy as soundtrack_policy

PERFORMANCE = {
    "assembly_mode": "native-speech-designed-pauses",
    "designed_pauses": {
        "thought": 0.45,
        "question": 0.7,
        "opening": 3.0,
        "paragraph": 1.6,
        "chapter": 3.4,
        "closing": 2.6,
    },
    "designed_pause_limits": {"opening": 9.0, "paragraph": 5.5, "chapter": 9.0},
    "designed_pause_weights": {"opening": 2.0, "paragraph": 1.0, "chapter": 2.5},
    "tail_guard_seconds": 0.3,
    "thought_pause_range": [0.3, 0.6],
    "paragraph_pause_range": [1.2, 2.0],
}


@pytest.fixture
def performance():
    """A voice performance that declares only the required parts of the pause contract."""
    return {**PERFORMANCE}


@pytest.fixture
def designed_policy(performance):
    """Validate the performance's pause contract with the given parts declared over it."""

    def designed(**overrides):
        return soundtrack_policy.designed_pause_policy({**performance, **overrides})

    return designed


# The recordings' sample rate.
RATE = 48000
# Two thoughts per recording: 0.4 s of quiet, two words of tone, 0.6 s of quiet at the join,
# two more words and 0.5 s of quiet.
WORDS = (("甲", 0.4, 0.9), ("乙", 0.9, 1.4), ("丙", 2.0, 2.5), ("丁", 2.5, 3.0))


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tones(path, amplitude) -> None:
    """Write a mono 48 kHz recording whose words are tones and whose pauses are silent."""
    pcm = np.zeros(round(3.5 * RATE))
    for _, start, end in WORDS:
        time = np.arange(round(end * RATE) - round(start * RATE)) / RATE
        pcm[round(start * RATE) : round(end * RATE)] = amplitude * np.sin(2 * np.pi * 440 * time)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(np.rint(pcm).astype("<i2").tobytes())


@pytest.fixture
def two_chapters(tmp_path, monkeypatch, performance):
    """Stage two one-segment chapters at different levels; the first declares a level gain."""
    release = repository.read(production.Edition("zh").script)["release"]
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.setattr(soundtrack_assembly, "DURATION", 24)
    monkeypatch.setattr(soundtrack_assembly, "CREDITS_DURATION", 4)
    # Retained-group custody has its own tests; these recordings carry no groups.
    monkeypatch.setattr(soundtrack_assembly, "validate_group_inputs", lambda *_, **__: set())
    edition = production.Edition("zh")
    edition.evidence.mkdir(parents=True)
    text = "甲乙。丙丁。"
    segments, records, alignments = [], [], []
    for index, (chapter, amplitude) in enumerate((("a", 6000), ("b", 9000)), 1):
        segment_id = f"{index:02d}"
        path = tmp_path / f"take-{segment_id}.wav"
        write_tones(path, amplitude)
        segments.append(
            {
                "id": segment_id,
                "chapter": chapter,
                "chapter_title": chapter.upper(),
                "title": f"Scene {segment_id}",
                "utterance_groups": ["甲乙。", "丙丁。"],
                "text": text,
            }
        )
        text_sha256 = hashlib.sha256(text.encode()).hexdigest()
        records.append(
            {
                "id": segment_id,
                "text": text,
                "text_sha256": text_sha256,
                "path": path.name,
                "wav_sha256": sha256(path),
            }
        )
        alignments.append(
            {
                "id": segment_id,
                "wav_sha256": sha256(path),
                "text_sha256": text_sha256,
                "items": [
                    {"text": word, "start_time": start, "end_time": end}
                    for word, start, end in WORDS
                ],
            }
        )
    level = tmp_path / "level-01.json"
    level.write_text(json.dumps({"recording_sha256": records[0]["wav_sha256"], "gain_db": 1.0}))
    records[0]["level_correction"] = {
        "gain_db": 1.0,
        "evidence": level.name,
        "evidence_sha256": sha256(level),
    }
    script = {
        "title": "Sample Reel",
        "voice_performance": {
            **performance,
            "thought_level_tolerance_db": 0.75,
            "chapter_level_tolerance_db": 0.3,
        },
        "caption_timing": {"tail_seconds": 0.25, "short_cue_lead_seconds": 0.1},
        "release": release,
        "segments": segments,
    }
    (tmp_path / "content").mkdir()
    (tmp_path / edition.script).write_text(json.dumps(script, ensure_ascii=False))
    edition.narration_selected.write_text(json.dumps({"records": records}, ensure_ascii=False))
    edition.alignment_selected.write_text(json.dumps({"records": alignments}, ensure_ascii=False))
    return edition
