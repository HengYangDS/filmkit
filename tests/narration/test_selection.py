"""Selecting the narration recordings and binding their narrator, alignment and script."""

import copy
import hashlib
import json
import wave

import numpy as np
import pytest

import filmkit.film as film
import filmkit.narration.selection as narration_selection
import filmkit.narration.terms as narration_terms
import filmkit.repository as repository
from filmkit.production import Edition


def sha256(data: bytes | str) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


@pytest.fixture
def edition(retained_group_record, monkeypatch):
    """An English edition whose script, cast, receipt and alignment bind one grouped record."""
    root, record, plans, settings = retained_group_record
    monkeypatch.setattr(repository, "ROOT", root)
    record = {**record, "text_sha256": sha256(record["text"])}
    section = {
        "id": record["id"],
        "text": record["text"],
        "spoken_text": record["spoken_text"],
        "language": "English",
        "utterance_groups": [plan["text"] for plan in plans],
    }
    repository.write(
        "content/voice-performance.json",
        {"pronunciation": {"languages": {"English": {"normalization": []}}}},
    )
    script = {
        "language": "English",
        "pronunciation_contract": "content/voice-performance.json",
        "segments": [section],
    }
    cast = {
        "reference_audio": settings["reference_audio"],
        "reference_sha256": settings["reference_sha256"],
        "reference_text": settings["reference_text"],
        "reference_text_sha256": sha256(settings["reference_text"]),
        "narration_language": "English",
        "reference_language": "English",
        "performance_recording": {
            "receipt": "build/receipt.json",
            "alignment": "build/alignment.json",
        },
    }
    alignment = {
        "records": [
            {
                "id": record["id"],
                "items": [
                    {"text": word, "start_time": start, "end_time": end}
                    for word, start, end in (
                        ("First", 0.1, 0.9),
                        ("thought", 0.9, 1.9),
                        ("Second", 2.4, 3.2),
                        ("thought", 3.2, 4.2),
                    )
                ],
                "wav_sha256": record["wav_sha256"],
                "text_sha256": record["text_sha256"],
            }
        ]
    }
    values = {"script": script, "cast": cast, "receipt": {"records": [record]}}
    values["alignment"] = alignment
    write_edition(values)
    return values


def write_edition(values: dict) -> None:
    edition = Edition("en")
    repository.write(edition.script, values["script"])
    repository.write(edition.cast, values["cast"])
    repository.write("build/receipt.json", values["receipt"])
    repository.write("build/alignment.json", values["alignment"])


def test_selection_binds_each_current_recording_and_its_alignment(edition, capsys):
    narration_selection.select(Edition("en"))
    selected = repository.read(Edition("en").narration_selected)
    assert selected == {
        "records": edition["receipt"]["records"],
        "script_sha256": repository.sha(Edition("en").script),
        "cast_sha256": repository.sha(Edition("en").cast),
        "selection": "Current paragraph text; original generation retained",
        "listening_acceptance": "Separate review required",
    }
    assert repository.read(Edition("en").alignment_selected) == edition["alignment"]
    assert json.loads(capsys.readouterr().out) == {"selected": 1, "seconds": 4.3}


def receipt_record(values: dict) -> dict:
    return values["receipt"]["records"][0]


@pytest.mark.parametrize(
    ("tamper", "error", "message"),
    [
        (
            lambda values: values["cast"].pop("performance_recording"),
            ValueError,
            "A current declared performance recording is required",
        ),
        (
            lambda values: receipt_record(values).update(text="Changed."),
            ValueError,
            "Recording text differs: 26",
        ),
        (
            lambda values: receipt_record(values).update(spoken_text="Changed."),
            ValueError,
            "Recording spoken text differs: 26",
        ),
        (
            lambda values: receipt_record(values).update(wav_sha256="0" * 64),
            ValueError,
            "Recording waveform differs: 26",
        ),
        (
            lambda values: receipt_record(values)["utterance_groups"]["records"][0].update(
                receipt_sha256="0" * 64
            ),
            RuntimeError,
            "Retained utterance input changed",
        ),
        (
            lambda values: values["cast"].update(reference_treatment={"pitch_shift": 0}),
            ValueError,
            "26: the recording's narrator reference differs from the cast",
        ),
        (
            lambda values: values["alignment"]["records"][0].update(wav_sha256="0" * 64),
            ValueError,
            "Selected alignment waveform differs: 26",
        ),
    ],
)
def test_selection_refuses_a_recording_that_differs(edition, tamper, error, message):
    tamper(edition)
    write_edition(edition)
    with pytest.raises(error, match=message):
        narration_selection.select(Edition("en"))
    assert not Edition("en").narration_selected.exists()


def test_selection_refuses_a_recording_outside_the_production_root(edition, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "recording.wav"
    outside.write_bytes(b"recording")
    record = receipt_record(edition)
    record.pop("utterance_groups")
    record.update(path=str(outside), wav_sha256=sha256(outside.read_bytes()))
    edition["script"]["segments"][0].pop("utterance_groups")
    edition["alignment"]["records"][0]["wav_sha256"] = record["wav_sha256"]
    write_edition(edition)
    with pytest.raises(ValueError, match="must belong to the production root"):
        narration_selection.select(Edition("en"))


def test_a_voice_record_binds_the_cast_reference(edition):
    record, cast = receipt_record(edition), edition["cast"]
    narration_selection.validate_voice_record(record, cast)
    for field, value in (
        ("reference_audio", "other.wav"),
        ("reference_sha256", "0" * 64),
        ("reference_text_sha256", sha256("Other.")),
        ("reference_treatment", {"pitch_shift": 0}),
    ):
        with pytest.raises(ValueError, match="narrator reference differs from the cast"):
            narration_selection.validate_voice_record({**record, field: value}, cast)


def test_a_voice_record_refuses_a_changed_cast_reference(edition):
    record, cast = receipt_record(edition), copy.deepcopy(edition["cast"])
    narration_selection.validate_voice_record(record, cast)
    reference = repository.ROOT / cast["reference_audio"]
    reference.write_bytes(reference.read_bytes() + b"\0\0")
    with pytest.raises(ValueError, match="differs from the cast's SHA-256"):
        narration_selection.validate_voice_record(record, cast)


RECORD = {"id": "01", "text": "先核验。", "text_sha256": sha256("先核验。"), "wav_sha256": "a" * 64}
ALIGNED = {key: RECORD[key] for key in ("id", "text_sha256", "wav_sha256")}


@pytest.mark.parametrize(
    ("record", "aligned", "message"),
    [
        (RECORD, {**ALIGNED, "id": "02"}, "Selected alignment identity differs: 01"),
        (RECORD, {**ALIGNED, "wav_sha256": "b" * 64}, "Selected alignment waveform differs: 01"),
        (RECORD, {**ALIGNED, "text_sha256": sha256("旧稿")}, "Selected alignment text differs: 01"),
        ({**RECORD, "text": "旧稿"}, ALIGNED, "Selected alignment text differs: 01"),
    ],
)
def test_an_alignment_binds_its_exact_recording_and_text(record, aligned, message):
    narration_selection.validate_aligned_recording(RECORD, ALIGNED)
    with pytest.raises(ValueError, match=message):
        narration_selection.validate_aligned_recording(record, aligned)


def speak(edition: dict, monkeypatch, groups: list[str], words: list[tuple]) -> None:
    """Bind one recording that voices each aligned word (text, start, end) and is silent between.

    Retained-thought custody has its own tests; this recording carries no thoughts.
    """
    monkeypatch.setattr(narration_selection, "validate_group_inputs", lambda *_, **__: set())
    pcm = np.zeros(round((words[-1][2] + 0.3) * 24000))
    for _, start, end in words:
        span = np.arange(round(start * 24000), round(end * 24000))
        pcm[span] = 8000 * np.sin(2 * np.pi * 200 * span / 24000)
    recording = repository.ROOT / "build/spoken.wav"
    with wave.open(str(recording), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(pcm.astype("<i2").tobytes())
    text = "".join(groups)
    record = receipt_record(edition)
    record.update(
        text=text,
        spoken_text=text,
        text_sha256=sha256(text),
        path="build/spoken.wav",
        wav_sha256=sha256(recording.read_bytes()),
        duration=len(pcm) / 24000,
    )
    edition["script"]["segments"][0].update(text=text, spoken_text=text, utterance_groups=groups)
    edition["alignment"]["records"][0].update(
        items=[{"text": word, "start_time": a, "end_time": b} for word, a, b in words],
        wav_sha256=record["wav_sha256"],
        text_sha256=record["text_sha256"],
    )
    write_edition(edition)


# 0.49 s of quiet between 的 and Agent, and 0.36 s between "commit" and "and".
HALTING = (
    ["换成可以替换的 Agent 来做。", " We commit and check."],
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
        ("We", 3.4, 3.6),
        ("commit", 3.6, 4.0),
        ("and", 4.36, 4.56),
        ("check", 4.56, 5.0),
    ],
)


def declare(monkeypatch, *exceptions: tuple[str, str, str], terms: tuple = ()) -> None:
    """Declare the film's terms and the English flow's exceptions, each a thought and two words."""
    declared = [
        film.FlowException(edition="en", thought=t, left=a, right=b, reason="Kept by the author.")
        for t, a, b in exceptions
    ]
    narration = film.Narration(flow=film.Flow(exceptions=tuple(declared)), terms=terms)
    monkeypatch.setattr(
        narration_selection, "FILM", film.FILM.model_copy(update={"narration": narration})
    )


def test_selection_refuses_an_unmarked_pause_above_its_limit_by_name(edition, monkeypatch):
    speak(edition, monkeypatch, *HALTING)
    # The pause where the script switches is above its 0.2 s limit; the 0.36 s pause between
    # two clauses the text leaves unmarked stays within 0.4 s.
    refusal = (
        "^en 26.1: a 0.49 s pause between 的 and Agent, where the text has no mark and the "
        "script switches, exceeds its 0.20 s limit$"
    )
    with pytest.raises(narration_selection.SelectionError, match=refusal):
        narration_selection.select(Edition("en"))
    assert not Edition("en").narration_selected.exists()
    # A declared exception keeps the pause; one that names no boundary is stale.
    declare(monkeypatch, ("26.1", "的", "Agent"))
    narration_selection.select(Edition("en"))
    declare(monkeypatch, ("26.1", "的", "Agent"), ("26.2", "commit", "check"))
    stale = "^en: the .narration.flow. exception 26.2 between commit and check matches no boundary"
    with pytest.raises(narration_selection.SelectionError, match=stale):
        narration_selection.select(Edition("en"))


def test_selection_refuses_a_term_said_unlike_its_reference(edition, monkeypatch):
    words = [("The", 0.2, 0.4), ("Agent", 0.4, 0.8), ("works", 0.8, 1.2)]
    words += [("Each", 1.7, 1.9), ("Agent", 1.9, 2.3), ("checks", 2.3, 2.7)]
    speak(edition, monkeypatch, ["The Agent works. ", "Each Agent checks."], words)
    term = {"term": "Agent", "spoken": "Agent", "ipa": "ˈeɪdʒənt"}
    reference = {"thought": "26.1", "index": 0}
    declare(monkeypatch, terms=(film.NarrationTerm(**term, reference={"en": reference}),))
    # The vowel measure has its own tests; here the second occurrence opens its F1 by `opened`.
    opened = iter((1.4, 1.6))

    def vowel(_recording, start, _end, _after=None):
        return narration_terms.Vowel(500.0 if start < 1 else 500.0 * ratio, 1800.0, 6)

    monkeypatch.setattr(narration_terms, "first_vowel", vowel)
    ratio = next(opened)
    narration_selection.select(Edition("en"))
    ratio = next(opened)
    refusal = (
        "^en 26.2 Agent #0 at 1.90 s: its first vowel measures F1 800 Hz and F2 1800 Hz, 1.60 and "
        "1.00 times those of the reference 26.1 #0, F1 500 Hz and F2 1800 Hz; an occurrence may "
        "reach 1.5 times its F1 and 0.85 times its F2$"
    )
    with pytest.raises(narration_selection.SelectionError, match=refusal):
        narration_selection.select(Edition("en"))
    # A reference the narration does not hold is stale.
    stale = film.NarrationTerm(**term, reference={"en": {**reference, "index": 1}})
    declare(monkeypatch, terms=(stale,))
    with pytest.raises(narration_selection.SelectionError, match="Agent reference 26.1 #1 is not"):
        narration_selection.select(Edition("en"))
