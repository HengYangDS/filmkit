"""The sound gate: the lines a soundtrack must hold before the picture follows it."""

import json

import pytest

import filmkit.preflight as preflight
import filmkit.repository as repository
import filmkit.soundtrack.gates as sound_gates
from filmkit.production import Edition
from filmkit.soundtrack.assembly import AssemblyError

CLEAR = {
    "floor_db": 17.0,
    "soundtrack": {"cpp_db": 17.65, "frames": 9000, "below_floor": False},
    "segments": [{"id": "08", "cpp_db": 17.12, "frames": 400, "below_floor": False}],
    "segments_below_floor": [],
}
NATURAL = {
    "delivered": {
        "thoughts": 2,
        "natural": 2,
        "abrupt": [],
        "released": [],
        "cut_while_voiced": [],
    },
    "phrase_endings": {"heard": 3, "stopped": []},
}


def test_a_soundtrack_that_holds_every_line_has_no_finding():
    assert sound_gates.sound_findings(CLEAR, NATURAL) == []


def test_each_broken_line_is_named_with_its_place_and_figure():
    clarity = {
        "floor_db": 17.0,
        "soundtrack": {"cpp_db": 16.9, "frames": 9000, "below_floor": True},
        "segments": [{"id": "08", "cpp_db": 16.72, "frames": 400, "below_floor": True}],
        "segments_below_floor": ["08"],
    }
    endings = {
        "delivered": {
            "thoughts": 3,
            "natural": 2,
            "abrupt": ["03.2"],
            "released": ["05.1"],
            "cut_while_voiced": ["05.1"],
        },
        "phrase_endings": {
            "heard": 3,
            "stopped": [
                {"thought": "14.4", "word": "person,", "end": 742.31, "fall_ms": 8, "gain_db": 0.0}
            ],
        },
    }
    assert sound_gates.sound_findings(clarity, endings) == [
        "the soundtrack's clarity is 16.9 dB, below the declared 17.0 dB",
        "segment 08's clarity is 16.72 dB, below the declared 17.0 dB",
        "thought 03.2 ends abruptly as delivered",
        "thought 05.1 is cut while voiced where its release begins",
        "thought 14.4 stops at 'person,' (742.31 s) without a heard fall",
    ]


def test_a_film_without_a_floor_is_not_judged_on_clarity():
    clarity = {
        "floor_db": None,
        "soundtrack": {"cpp_db": 12.0, "frames": 9000, "below_floor": None},
        "segments": [{"id": "01", "cpp_db": 11.0, "frames": 400, "below_floor": None}],
        "segments_below_floor": [],
    }
    assert sound_gates.sound_findings(clarity, NATURAL) == []


@pytest.fixture
def measured(tmp_path, monkeypatch):
    """An edition whose soundtrack, timeline and assembly record exist, with its measures
    replaceable."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = Edition("en")
    for path, text in (
        (edition.timeline, json.dumps({"segments": [], "captions": []})),
        (edition.audio_assembly, json.dumps({"program_level": {"gain_db": -1.5}})),
        (tmp_path / repository.DECLARATION, 'slug = "sample-reel"\n'),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    edition.soundtrack.write_bytes(b"RIFF")
    measures = {"clarity": CLEAR, "endings": NATURAL}
    monkeypatch.setattr(sound_gates.clarity, "voice_clarity", lambda *_: measures["clarity"])
    monkeypatch.setattr(sound_gates.endings, "endings", lambda *_: measures["endings"])
    return edition, measures


def test_a_passing_check_writes_a_record_bound_to_the_soundtrack_and_timeline(measured, capsys):
    edition, _ = measured
    record = sound_gates.check_sound(edition)
    assert record == repository.read(edition.sound_gates)
    assert record["verdict"] == "pass"
    assert record["gated_findings"] == []
    assert record["soundtrack_sha256"] == repository.sha(edition.soundtrack)
    assert record["timeline_sha256"] == repository.sha(edition.timeline)
    assert record["clarity"] == CLEAR
    assert record["endings"] == NATURAL
    assert json.loads(capsys.readouterr().out) == {"verdict": "pass", "gated_findings": 0}


def test_a_record_is_refused_by_the_pre_render_check_after_an_edit_of_the_declaration(measured):
    edition, _ = measured
    record = sound_gates.check_sound(edition)
    assert record["assembly_sha256"] == repository.sha(edition.audio_assembly)
    assert preflight.sound(edition) is None
    (repository.ROOT / repository.DECLARATION).write_text('slug = "edited"\n')
    assert preflight.sound(edition) == (
        f"{repository.relative(edition.sound_gates)} binds another declaration_sha256; "
        "run check-sound"
    )


def test_a_gated_finding_is_recorded_and_refused(measured):
    edition, measures = measured
    stopped = {"thought": "14.4", "word": "person,", "end": 742.31, "fall_ms": 8, "gain_db": 0.0}
    measures["endings"] = {**NATURAL, "phrase_endings": {"heard": 3, "stopped": [stopped]}}
    message = "The en soundtrack has 1 gated finding: thought 14.4 stops at 'person,'"
    with pytest.raises(AssemblyError, match=message):
        sound_gates.check_sound(edition)
    record = repository.read(edition.sound_gates)
    assert record["verdict"] == "refuse"
    assert len(record["gated_findings"]) == 1


def test_a_segment_whose_thoughts_were_heard_clear_is_still_refused_under_the_floor(
    measured, monkeypatch
):
    import filmkit.film as film

    edition, measures = measured
    # The owner heard every take of segment 08 clear; the gate reads no record of hearing.
    heard = tuple(
        film.Heard(
            edition="en",
            thought=f"08.{index}",
            take=f"{index}" * 64,
            lines=("clarity",),
            listener=film.FILM.author,
            date="2026-11-24",
            note="Heard clear.",
        )
        for index in (1, 2)
    )
    narration = film.FILM.narration.model_copy(update={"heard": heard})
    declared = film.FILM.model_copy(update={"narration": narration})
    for module in (film, sound_gates.clarity):
        monkeypatch.setattr(module, "FILM", declared)
    measures["clarity"] = {
        "floor_db": 18.0,
        "soundtrack": {"cpp_db": 18.3, "frames": 9000, "below_floor": False},
        "segments": [{"id": "08", "cpp_db": 17.6, "frames": 400, "below_floor": True}],
        "segments_below_floor": ["08"],
    }
    message = "segment 08's clarity is 17.6 dB, below the declared 18.0 dB"
    with pytest.raises(AssemblyError, match=message):
        sound_gates.check_sound(edition)
    assert repository.read(edition.sound_gates)["verdict"] == "refuse"
