"""Transcribing a narration receipt's recordings with the pinned recognition model."""

import hashlib
from dataclasses import replace
from importlib.metadata import version
from types import SimpleNamespace

import pytest

import filmkit.narration.transcription as narration_transcription
import filmkit.repository as repository
from filmkit.narration.snapshots import RECOGNIZER, Snapshot, SnapshotError

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

    monkeypatch.setattr(narration_transcription, "load_recognizer", Recognizer)
    # The supplied snapshot's check, which reads the weights, is counted and passes.
    checks = []
    monkeypatch.setattr(Snapshot, "verify", lambda self, folder=None: checks.append(self.name))
    return {"record": record, "calls": calls, "recording": recording, "checks": checks}


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
    snapshot = SimpleNamespace(
        folder="recognizer",
        repo="repo",
        revision="r1",
        weights={"model.safetensors": "w1"},
        verify=lambda: checks.append("verified"),
    )
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.setattr(narration_transcription, "RECOGNIZER", snapshot)
    monkeypatch.setattr(narration_transcription, "load_model", loads.append)
    narration_transcription.load_asr()
    assert checks == ["verified"]
    assert loads == [str(tmp_path / "recognizer")]
    # The identity names what was checked and the speech library that runs it.
    assert narration_transcription.recognizer() == {
        "repo": "repo",
        "revision": "r1",
        "weights_sha256": "w1",
        "library": f"mlx-audio {version('mlx-audio')}",
    }
    assert checks == ["verified", "verified"]


def cache_files() -> list:
    return sorted((repository.ROOT / narration_transcription.CACHE / "chinese").glob("*.json"))


def test_a_cached_transcript_is_reused_without_loading_the_recognizer(receipt, monkeypatch):
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    first = (repository.ROOT / "asr.json").read_bytes()

    def unloaded():
        message = "the recognizer is not loaded when every transcript is cached"
        raise AssertionError(message)

    monkeypatch.setattr(narration_transcription, "load_recognizer", unloaded)
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    assert len(receipt["calls"]) == 1
    assert (repository.ROOT / "asr.json").read_bytes() == first
    # The supplied recognizer is checked on every run, also on one that loads no model: the
    # cache names its weights, and reading them is what proves the cache's recognizer is here.
    assert receipt["checks"] == ["recognizer", "recognizer"]
    (cache,) = cache_files()
    cached = repository.read(cache)
    assert cached["heard"] == "数据的用处"
    assert cached["recognizer"] == {
        "repo": RECOGNIZER.repo,
        "revision": ASR_REVISION,
        "weights_sha256": RECOGNIZER.weights["model.safetensors"],
        "library": f"mlx-audio {version('mlx-audio')}",
    }
    # A cache that binds another recording or recognizer than its place names is refused.
    for change in ({"wav_sha256": "0" * 64}, {"recognizer": {**cached["recognizer"], "repo": "x"}}):
        repository.write(cache, {**cached, **change})
        with pytest.raises(ValueError, match="Cached transcript binding differs"):
            narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])


def test_a_supplied_recognizer_that_differs_refuses_a_fully_cached_run(receipt, monkeypatch):
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    (repository.ROOT / "asr.json").unlink()

    def differs(self, folder=None):
        message = "The recognizer weights differ from the pinned SHA-256: model.safetensors"
        raise SnapshotError(message)

    monkeypatch.setattr(Snapshot, "verify", differs)
    with pytest.raises(SnapshotError, match="weights differ"):
        narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    assert not (repository.ROOT / "asr.json").exists()


@pytest.mark.parametrize(
    "change",
    [
        {"revision": "f" * 40},
        {"weights": {"model.safetensors": "0" * 64}},
        {"library": "mlx-audio 0.0.1"},
    ],
    ids=["revision", "weights", "library"],
)
def test_a_transcript_by_another_recognizer_or_library_is_not_reused(receipt, monkeypatch, change):
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    library = change.pop("library", None)
    if library:
        monkeypatch.setattr(narration_transcription, "LIBRARY", library)
    else:
        other = replace(RECOGNIZER, **change)
        monkeypatch.setattr(narration_transcription, "RECOGNIZER", other)
    narration_transcription.main([*ARGUMENTS, "--language", "Chinese"])
    assert len(receipt["calls"]) == 2
    assert len(cache_files()) == 2
