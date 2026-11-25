"""The verifier's requirement of the still scan of an edition's 1080p captioned film: the record
that `scan-film` writes, as `filmkit.picture.still_scan.require_film_scan` reads it."""

import pytest

import filmkit.delivery.verification as delivery_verification
from filmkit.picture.errors import PictureError


@pytest.fixture
def verify(inputs, monkeypatch):
    """Qualify the edition's bound inputs in the technical scope: its narration, pictures,
    packages and still scan are read as they stand, and its sources, media and Spotlight
    readback pass, as their own tests cover."""
    for name in ("sources", "spotlight"):
        monkeypatch.setattr(delivery_verification, f"verify_{name}", lambda *_: {})
    monkeypatch.setattr(
        delivery_verification, "verify_media", lambda _edition, path, _rendition: path.name
    )
    edition = inputs.edition
    return lambda: delivery_verification.qualify(edition, edition.films, technical_only=True)


def test_an_edition_whose_film_passed_its_scan_is_verified(inputs, verify):
    assert verify()["still_scan"] == {
        "film": inputs.edition.film("1080p-captioned").name,
        "longest_fine_speech": 0,
        "limit_seconds": 3.5,
    }
    # A run under the limit is the record's longest and refuses nothing.
    inputs.scan_film({"start": 3.0, "end": 6.6, "speech": 3.49})
    assert verify()["still_scan"]["longest_fine_speech"] == 3.49


def test_a_film_that_holds_a_still_run_is_refused_with_its_seconds_and_its_speech(inputs, verify):
    held = {"start": 2.7, "end": 7.4, "speech": 3.86}
    inputs.scan_film({"start": 0.2, "end": 2.5, "speech": 2.1}, held)
    with pytest.raises(PictureError) as refused:
        verify()
    assert str(refused.value) == (
        "The zh film holds a still picture with 3.5 s of speech or more: 2.70-7.40 s with "
        "3.86 s of speech; see build/evidence/editions/zh/film-stills.json"
    )


@pytest.mark.parametrize("limit", [99, 2.5])
def test_a_record_written_under_another_limit_is_refused_with_both_limits(inputs, verify, limit):
    # A laxer record would pass a run the engine refuses, and a stricter one states failures
    # that are not the engine's: neither answers, whatever runs it lists.
    inputs.scan_film({"start": 0.9, "end": 4.9, "speech": 3.0})
    record = inputs.edition.film_stills
    inputs.change(record, "rules", "limit_seconds", value=limit)
    inputs.change(record, "limit_seconds", value=limit)
    with pytest.raises(PictureError) as refused:
        verify()
    assert str(refused.value) == (
        "The zh film's still scan record states other rules than the engine's: a limit of "
        f"{limit} s where the engine's is 3.5 s; run filmkit build scan-film:zh"
    )


def test_a_record_cut_short_is_refused_with_the_action_that_writes_it(inputs, verify):
    record = inputs.edition.film_stills
    record.write_text(record.read_text()[:200])
    with pytest.raises(PictureError) as refused:
        verify()
    assert (
        str(refused.value)
        == "The zh film's still scan record cannot be read; run filmkit build scan-film:zh"
    )


def test_a_record_whose_runs_a_hand_emptied_is_not_trusted(inputs, verify):
    # The record of a film that stands still, its list of runs emptied: its own list of the
    # runs at the limit and its longest speech still state the run.
    inputs.scan_film({"start": 2.7, "end": 7.4, "speech": 3.86})
    inputs.change(inputs.edition.film_stills, "fine", "runs", value=[])
    with pytest.raises(PictureError) as refused:
        verify()
    assert str(refused.value) == (
        "The zh film's still scan record cannot be trusted, as it contradicts itself in its runs "
        "at the limit and its longest speech; run filmkit build scan-film:zh"
    )


@pytest.mark.parametrize(
    ("keys", "named"),
    [
        (("movie", "sha256"), "movie"),
        (("timeline", "sha256"), "timeline"),
        (("composition", "sha256"), "composition"),
        (("engine_version",), "engine"),
    ],
)
def test_a_record_of_another_film_timeline_composition_or_engine_is_refused(
    inputs, verify, keys, named
):
    inputs.change(inputs.edition.film_stills, *keys, value="0" * 64)
    with pytest.raises(PictureError) as refused:
        verify()
    assert str(refused.value) == (
        f"The zh film's still scan record binds another {named}; run filmkit build scan-film:zh"
    )


def test_an_edition_without_the_record_is_refused_with_the_action_that_writes_it(inputs, verify):
    inputs.edition.film_stills.unlink()
    with pytest.raises(PictureError) as refused:
        verify()
    assert (
        str(refused.value) == "The zh film has no still scan record; run filmkit build scan-film:zh"
    )


def test_the_draft_s_record_does_not_stand_in_for_the_film_s(inputs, verify):
    # A film that declares drafts holds a passing draft record; the film's own record decides.
    record = inputs.edition.film_stills
    record.rename(inputs.edition.draft_stills)
    with pytest.raises(
        PictureError, match="has no still scan record; run filmkit build scan-film:zh"
    ):
        verify()
