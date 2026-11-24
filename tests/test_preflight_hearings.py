"""Preflight with the owner's hearing of a take: a thought under its clarity line passes where he
heard its selected take clear and the soundtrack the sound gate measured was assembled from that
selection; each other is refused, named for his ear."""

import json

import pytest

import filmkit.film as film
import filmkit.preflight as preflight
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.production import Edition

A, B, C = "a" * 64, "b" * 64, "c" * 64


def put(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False))


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """The Chinese edition with a sound gate record of one thought, 01.1, at 17.4 dB under an
    18.0 dB floor held for every thought."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    edition = Edition("zh")
    rows = [{"id": "01.1", "cpp_db": 17.4, "below_floor": True}]
    put(edition.sound_gates, {"clarity": {"floor_db": 18.0, "thoughts": rows}})
    return edition


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
    monkeypatch.setattr(
        preflight, "FILM", FILM.model_copy(update={"review": review, "narration": narration})
    )


UNDER = (
    "thought 01.1 reads 17.4 dB, under the floor of 18.0 dB, to which the film holds every thought"
)


def test_a_thought_heard_clear_on_its_selected_and_assembled_take_is_refused_nothing(
    edition, monkeypatch
):
    selected(edition, A)
    heard_clear(monkeypatch, A)
    assert preflight.clarity(edition) is None


def test_a_thought_heard_clear_on_another_take_is_refused_for_the_ear(edition, monkeypatch):
    selected(edition, B)
    heard_clear(monkeypatch, A)
    assert preflight.clarity(edition) == f"{UNDER}: for the owner's ear, its selected take {B}"
    # Without a selected narration no take is named, and the thought is still refused.
    (repository.ROOT / edition.narration_selected).unlink()
    assert preflight.clarity(edition) == UNDER


def test_a_heard_take_selected_after_the_assembly_is_refused_until_assembled(edition, monkeypatch):
    # Take A of 01.1 was assembled and reads 17.4 dB; the owner rejected it, take C was selected
    # after, and he heard C clear. The soundtrack still holds A, which no one heard.
    selected(edition, A)
    selected(edition, C, assembled=False)
    heard_clear(monkeypatch, C)
    refused = (
        "thought 01.1 reads 17.4 dB: the owner heard its selected take, but the soundtrack was "
        "assembled from another selection of segment 01; run assemble"
    )
    assert preflight.clarity(edition) == refused
    # With no assembly record, nothing holds the heard take either.
    (repository.ROOT / edition.audio_assembly).unlink()
    assert preflight.clarity(edition) == refused
    # Assembled from the selection he heard, the thought is refused nothing.
    selected(edition, C)
    assert preflight.clarity(edition) is None
