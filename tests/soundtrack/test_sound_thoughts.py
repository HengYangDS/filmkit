"""The sound gate holds each thought to the film's thought line, with the owner's hearing of its
selected take, and each caption cue to its edition's reading rate (design decision 7 of
build-a-film-by-its-verbs): the rules a render waited for in the pre-render check, word for
word."""

import json

import pytest

import filmkit.film as film
import filmkit.repository as repository
import filmkit.soundtrack.gates as sound_gates
from filmkit.film import FILM
from filmkit.production import Edition
from filmkit.soundtrack.assembly import AssemblyError

A, B, C = "a" * 64, "b" * 64, "c" * 64


def put(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False))


def thoughts(**values) -> dict:
    """The sound gate's clarity of these thoughts, against the floor of 18 dB."""
    rows = [
        {"id": name, "cpp_db": value, "below_floor": value < 18} for name, value in values.items()
    ]
    return {"floor_db": 18.0, "thoughts": rows}


def said(edition: Edition, measured: dict) -> str | None:
    """The gate's thought findings in one line, or None."""
    return "; ".join(sound_gates.thought_findings(edition, measured)) or None


def declaring(monkeypatch, **tables) -> None:
    """The film's declaration with these tables, as the gate reads it."""
    monkeypatch.setattr(sound_gates, "FILM", FILM.model_copy(update=tables))


@pytest.fixture
def edition(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return Edition("zh")


def test_a_thought_under_the_floor_is_declared_and_none_stands_under_the_thought_line(
    edition, monkeypatch
):
    # A film that declares no line for a single thought is not judged.
    assert said(edition, thoughts(**{"01.1": 18.4, "01.2": 17.62, "02.1": 16.9})) is None
    kept = [
        {"edition": "zh", "thought": "01.2", "reason": "thirty-two takes"},
        {"edition": "zh", "thought": "03.1", "reason": "an earlier build"},
        {"edition": "en", "thought": "02.1", "reason": "the other edition's"},
    ]
    review = type(FILM.review)(
        **{
            **FILM.review.model_dump(),
            "clarity_thought_margin_db": 1.0,
            "clarity_exceptions": kept,
        }
    )
    declaring(monkeypatch, review=review)
    assert said(edition, thoughts(**{"01.1": 18.4, "01.2": 17.62, "02.1": 16.9})) == (
        "thought 02.1 reads 16.9 dB, under the thought line of 17.0 dB; "
        "the declared thought 03.1 is stale: it does not read under the floor"
    )
    assert said(
        edition, thoughts(**{"01.1": 18.4, "01.2": 17.62, "02.1": 17.0, "03.1": 17.99})
    ) == (
        "thought 02.1 reads 17.0 dB, under the floor of 18.0 dB, and is not declared in"
        " review.clarity_exceptions"
    )
    assert said(edition, thoughts(**{"01.2": 17.62, "03.1": 17.99})) is None
    # A declaration keeps no thought under the thought line.
    assert said(edition, thoughts(**{"01.2": 16.4, "03.1": 17.99})) == (
        "thought 01.2 reads 16.4 dB, under the thought line of 17.0 dB"
    )


def test_with_a_margin_of_zero_every_thought_is_held_to_the_floor_itself(edition, monkeypatch):
    review = type(FILM.review)(**{**FILM.review.model_dump(), "clarity_thought_margin_db": 0})
    declaring(monkeypatch, review=review)
    # A thought at the floor passes.
    assert said(edition, thoughts(**{"01.1": 18.0, "01.2": 18.4})) is None
    # A thought a hundredth of a decibel under it is refused, and no declaration could keep it.
    assert said(edition, thoughts(**{"01.1": 18.0, "01.2": 17.99, "02.1": 16.9})) == (
        "thought 01.2 reads 17.99 dB, under the floor of 18.0 dB, to which the film holds every "
        "thought; thought 02.1 reads 16.9 dB, under the floor of 18.0 dB, to which the film "
        "holds every thought"
    )


def test_a_cue_above_the_reading_rate_is_declared_by_its_text(monkeypatch):
    english = Edition("en")
    fast = "The people watching the pipeline."
    cues = [
        {"segment": "01", "text": "Read the data first.", "start": 1.0, "end": 3.0},
        {"segment": "01", "text": fast, "start": 3.0, "end": 4.2},
    ]
    assert sound_gates.rate_findings(english, cues) == [
        f"the cue {fast!r} reads at 27.5 characters per second, above 25, and is not declared in"
        " captions.rate_exceptions"
    ]
    kept = [
        {"edition": "en", "text": fast, "reason": "a quoted line kept whole"},
        {"edition": "en", "text": "Read the data first.", "reason": "an earlier build"},
    ]
    declaring(monkeypatch, captions=type(FILM.captions)(rate_exceptions=kept))
    assert sound_gates.rate_findings(english, cues) == [
        "the declared cue 'Read the data first.' is stale: no cue with that text reads above the"
        " rate"
    ]
    declaring(monkeypatch, captions=type(FILM.captions)(rate_exceptions=kept[:1]))
    assert sound_gates.rate_findings(english, cues) == []
    # A Chinese cue has no reading rate, so none is above it, and a declared one is stale.
    chinese = [{**cues[1], "text": "先看数据，再看流水线。"}]
    assert sound_gates.rate_findings(Edition("zh"), chinese) == []
    kept = [{"edition": "zh", "text": "先看数据，再看流水线。", "reason": "kept whole"}]
    declaring(monkeypatch, captions=type(FILM.captions)(rate_exceptions=kept))
    assert sound_gates.rate_findings(Edition("zh"), chinese) == [
        "the declared cue '先看数据，再看流水线。' is stale: no cue with that text reads above the"
        " rate"
    ]


def selected(edition, take: str, *, assembled: bool = True) -> None:
    """Write the selection of 01.1's take, its segment's recording derived from it, and, where
    `assembled`, the assembly record's source of segment 01 as `assemble` writes it from that
    selection."""
    segment = {"id": "01", "wav_sha256": f"segment of {take}"}
    segment["utterance_groups"] = {"records": [{"index": 1, "wav_sha256": take}]}
    put(edition.narration_selected, {"records": [segment]})
    if assembled:
        put(
            edition.audio_assembly,
            {"records": [{"id": "01", "source_sha256": segment["wav_sha256"]}]},
        )


def heard_clear(monkeypatch, take: str) -> None:
    """Hold every thought to the floor and record the owner's hearing of one take of 01.1."""
    record = film.Heard(
        edition="zh",
        thought="01.1",
        take=take,
        lines=("clarity",),
        listener=FILM.author,
        date="2026-11-24",
        note="Heard clear on the clip.",
    )
    review = FILM.review.model_copy(update={"clarity_thought_margin_db": 0})
    narration = FILM.narration.model_copy(update={"heard": (record,)})
    declaring(monkeypatch, review=review, narration=narration)


UNDER = (
    "thought 01.1 reads 17.4 dB, under the floor of 18.0 dB, to which the film holds every thought"
)
HEARD = thoughts(**{"01.1": 17.4})


def test_a_thought_heard_clear_on_its_selected_and_assembled_take_is_refused_nothing(
    edition, monkeypatch
):
    selected(edition, A)
    heard_clear(monkeypatch, A)
    assert said(edition, HEARD) is None


def test_a_thought_heard_clear_on_another_take_is_refused_for_the_ear(edition, monkeypatch):
    selected(edition, B)
    heard_clear(monkeypatch, A)
    assert said(edition, HEARD) == f"{UNDER}: for the owner's ear, its selected take {B}"
    # Without a selected narration no take is named, and the thought is still refused.
    (repository.ROOT / edition.narration_selected).unlink()
    assert said(edition, HEARD) == UNDER


def test_a_heard_take_selected_after_the_assembly_is_refused_until_assembled(edition, monkeypatch):
    # Take A of 01.1 was assembled and reads 17.4 dB; the owner rejected it, take C was selected
    # after, and he heard C clear. The soundtrack still holds A, which no one heard.
    selected(edition, A)
    selected(edition, C, assembled=False)
    heard_clear(monkeypatch, C)
    refused = (
        "thought 01.1 reads 17.4 dB: the owner heard its selected take, but the soundtrack was "
        "assembled from another selection of segment 01; run filmkit build assemble:zh"
    )
    assert said(edition, HEARD) == refused
    # With no assembly record, nothing holds the heard take either.
    (repository.ROOT / edition.audio_assembly).unlink()
    assert said(edition, HEARD) == refused
    # Assembled from the selection he heard, the thought is refused nothing.
    selected(edition, C)
    assert said(edition, HEARD) is None


def test_check_sound_refuses_a_thought_under_its_line_and_a_segment_its_hearing_cannot_settle(
    edition, monkeypatch, capsys
):
    put(edition.timeline, {"segments": [], "captions": []})
    selected(edition, A)
    edition.soundtrack.parent.mkdir(parents=True, exist_ok=True)
    edition.soundtrack.write_bytes(b"RIFF")
    put(repository.ROOT / repository.DECLARATION, {})
    segments = [{"id": "01", "cpp_db": 17.4, "frames": 400, "below_floor": True}]
    measured = {
        **HEARD,
        "soundtrack": {"cpp_db": 18.2, "frames": 9000, "below_floor": False},
        "segments": segments,
        "segments_below_floor": ["01"],
    }
    natural = {
        "delivered": {"abrupt": [], "cut_while_voiced": []},
        "phrase_endings": {"stopped": []},
    }
    monkeypatch.setattr(sound_gates.clarity, "voice_clarity", lambda *_: measured)
    monkeypatch.setattr(sound_gates.endings, "endings", lambda *_: natural)
    heard_clear(monkeypatch, B)
    with pytest.raises(AssemblyError) as refused:
        sound_gates.check_sound(edition)
    # The thought is refused for the ear; the segment holding it is refused by the floor, which
    # no record of hearing settles.
    assert repository.read(edition.sound_gates)["gated_findings"] == [
        "segment 01's clarity is 17.4 dB, below the declared 18.0 dB",
        f"{UNDER}: for the owner's ear, its selected take {A}",
    ]
    assert "2 gated findings" in str(refused.value)
    heard_clear(monkeypatch, A)
    with pytest.raises(AssemblyError, match="1 gated finding: segment 01's clarity is 17.4 dB"):
        sound_gates.check_sound(edition)
