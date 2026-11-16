"""Transcribing a narration receipt's recordings with the pinned recognition model."""

import hashlib
from types import SimpleNamespace

import pytest

import filmkit.narration.transcription as narration_transcription
import filmkit.repository as repository

ASR_REVISION = "eae2b51f96265328f1e7beced788adb0e4536f92"


@pytest.fixture
def receipt(tmp_path, monkeypatch) -> dict:
    """One bound recording and a recognizer double that records what it transcribes."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    recording = tmp_path / "recordings/01.wav"
    recording.parent.mkdir()
    recording.write_bytes(b"pcm")
    record = {
        "id": "01",
        "path": "recordings/01.wav",
        "text": "数据的用途。",
        "text_sha256": hashlib.sha256("数据的用途。".encode()).hexdigest(),
        "language": "Chinese",
        "wav_sha256": hashlib.sha256(b"pcm").hexdigest(),
    }
    repository.write("receipt.json", {"records": [record]})
    calls = []

    class Recognizer:
        def generate(self, path, *, language):
            calls.append((path, language))
            return SimpleNamespace(text="数据的用处")

    monkeypatch.setattr(narration_transcription, "load_asr", Recognizer)
    return {"record": record, "calls": calls, "recording": recording}


ARGUMENTS = ["--receipt", "receipt.json", "--output", "asr.json"]


def test_transcription_reports_unit_error_rates_of_bound_recordings(receipt):
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    report = repository.read("asr.json")
    assert receipt["calls"] == [(str(receipt["recording"]), "Chinese")]
    assert report == {
        "model": "mlx-community/Qwen3-ASR-0.6B-bf16",
        "revision": ASR_REVISION,
        "language": "Chinese",
        "scope": narration_transcription.SCOPE,
        "records": [
            {
                "id": "01",
                "path": "recordings/01.wav",
                "wav_sha256": receipt["record"]["wav_sha256"],
                "heard": "数据的用处",
                "unit_error_rate": 0.2,
            }
        ],
    }


@pytest.mark.parametrize(
    ("tamper", "language", "message"),
    [
        (lambda _receipt: None, "English", "01: the recording language differs"),
        (
            lambda receipt: receipt["recording"].write_bytes(b"changed"),
            "Chinese",
            "01: the recording differs from its receipt",
        ),
    ],
    ids=["language", "recording"],
)
def test_a_recording_that_differs_from_its_receipt_is_not_transcribed(
    tmp_path, receipt, tamper, language, message
):
    tamper(receipt)
    with pytest.raises(ValueError, match=message):
        narration_transcription.main([*ARGUMENTS, "--language", language])
    assert receipt["calls"] == []
    assert not (tmp_path / "asr.json").exists()


def test_the_recognizer_loads_from_its_checked_supplied_snapshot(tmp_path, monkeypatch):
    checks, loads = [], []
    snapshot = SimpleNamespace(folder="recognizer", verify=lambda: checks.append("verified"))
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.setattr(narration_transcription, "RECOGNIZER", snapshot)
    monkeypatch.setattr(narration_transcription, "load_model", loads.append)
    narration_transcription.load_asr()
    assert checks == ["verified"]
    assert loads == [str(tmp_path / "recognizer")]


def test_a_cached_transcript_is_reused_without_loading_the_recognizer(receipt, monkeypatch):
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    first = (repository.ROOT / "asr.json").read_bytes()

    def unloaded():
        message = "the recognizer is not loaded when every transcript is cached"
        raise AssertionError(message)

    monkeypatch.setattr(narration_transcription, "load_asr", unloaded)
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    assert len(receipt["calls"]) == 1
    assert (repository.ROOT / "asr.json").read_bytes() == first
    (cache,) = (repository.ROOT / narration_transcription.CACHE / "chinese").glob("*.json")
    cached = repository.read(cache)
    assert (cached["heard"], cached["revision"]) == ("数据的用处", ASR_REVISION)
    # A cache that binds another recording than its place names is refused.
    repository.write(cache, {**cached, "wav_sha256": "0" * 64})
    with pytest.raises(ValueError, match="Cached transcript binding differs"):
        narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])


def test_a_transcript_by_another_recognizer_revision_is_not_reused(receipt, monkeypatch):
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    monkeypatch.setattr(narration_transcription, "ASR_REVISION", "f" * 40)
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    assert len(receipt["calls"]) == 2
    caches = (repository.ROOT / narration_transcription.CACHE / "chinese").glob("*.json")
    assert len(list(caches)) == 2
