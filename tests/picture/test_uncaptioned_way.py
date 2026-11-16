"""How an uncaptioned picture is made: derived under software capture, rendered under any other
capture or when asked for, each receipt and comparison record saying which way and why."""

import pytest

import filmkit.media as media
import filmkit.picture.derivation as derivation
import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
import filmkit.picture.rendering as picture_rendering
import filmkit.produce as produce
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition


def declaring(monkeypatch, capture: str) -> None:
    """Declare the film's capture as `[picture] capture` would."""
    picture = FILM.picture.model_copy(update={"capture": capture})
    monkeypatch.setattr(picture_rendering, "FILM", FILM.model_copy(update={"picture": picture}))


@pytest.fixture
def edition(film_root, monkeypatch):
    """The Chinese edition staged and checked, with media checks that pass and derivations
    recorded instead of encoded."""
    edition = Edition("zh")
    film_root.staged(edition)
    monkeypatch.setattr(media, "probe", lambda path: {})
    monkeypatch.setattr(media, "require_video", lambda *arguments, **options: {})
    monkeypatch.setattr(media, "video_cadence", lambda *arguments: {"keyframes": []})
    derived = []
    monkeypatch.setattr(
        derivation, "derive_uncaptioned", lambda *arguments: derived.append(arguments)
    )
    return edition, film_root, derived


def uncaptioned(code="zh", *flags):
    produce.main(["render-picture", "--language", code, "--uncaptioned", *flags])


@pytest.mark.parametrize("capture", ["fast", "screenshot"])
def test_a_film_of_another_capture_gets_a_render_of_its_own_stage_without_asking(
    edition, monkeypatch, capture
):
    edition, film_root, derived = edition
    declaring(monkeypatch, capture)
    uncaptioned()
    assert derived == []
    (run,) = film_root.runs()
    assert run["argv"][1] == str(edition.rendered(False).stage)
    receipt = repository.read(edition.rendered(False).receipt)
    assert receipt["uncaptioned"]["way"] == "rendered"
    assert receipt["uncaptioned"]["reason"] == (
        f"the film declares {capture} capture, and a picture is derived only under software "
        "capture, which the engine's release qualifies"
    )
    assert (receipt["picture"], receipt["capture"]) == ("uncaptioned", capture)
    assert not derivation.is_derived(receipt)
    # The receipt still validates as the render it is.
    picture_rendering.validate_picture_binding(edition, receipt, captions=False)


def test_a_film_of_software_capture_derives_and_native_still_renders(edition, monkeypatch):
    edition, film_root, derived = edition
    assert picture_rendering.FILM.picture.capture == "software"
    uncaptioned()
    assert derived == [(edition, derivation.DEADLINE)]
    assert film_root.runs() == []
    uncaptioned("zh", "--native")
    assert len(derived) == 1
    (run,) = film_root.runs()
    assert run["argv"][1] == str(edition.rendered(False).stage)
    receipt = repository.read(edition.rendered(False).receipt)
    assert receipt["uncaptioned"] == {
        "way": "rendered",
        "reason": "a render of its own stage was asked for",
    }


@pytest.mark.parametrize(
    ("capture", "native", "way"),
    [
        ("software", False, "derived"),
        ("software", True, "rendered"),
        ("fast", False, "rendered"),
        ("fast", True, "rendered"),
        ("screenshot", False, "rendered"),
    ],
)
def test_the_way_follows_the_declared_capture_and_the_request(monkeypatch, capture, native, way):
    declaring(monkeypatch, capture)
    answer = derivation.uncaptioned_way(native=native)
    assert answer["way"] == way
    assert answer["reason"]
    if way == "derived":
        assert answer["reason"] == (
            "the film declares software capture, which the engine's release qualifies"
        )


def test_a_derivation_itself_refuses_a_film_of_another_capture(film_root, monkeypatch):
    edition = Edition("zh")
    film_root.staged(edition)
    declaring(monkeypatch, "fast")
    with pytest.raises(PictureError, match="not derived: the film declares fast capture"):
        derivation.derive_uncaptioned(edition)
    assert film_root.runs() == []


def test_a_derived_picture_does_not_stand_under_another_capture(film_root, monkeypatch):
    edition = Edition("zh")
    receipt = {"picture": "uncaptioned", "derived": {"rows": [0, 16]}, "exit": 0}
    declaring(monkeypatch, "screenshot")
    with pytest.raises(PictureError, match="is derived, and the film declares screenshot capture"):
        derivation.validate_binding(edition, receipt)


def test_a_rendered_pairs_comparison_record_says_why_the_picture_was_rendered(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    edition = Edition("zh")
    way = {"way": "rendered", "reason": "the film declares fast capture"}
    receipts = {
        True: {"picture": "captioned"},
        False: {"picture": "uncaptioned", "uncaptioned": way},
    }
    for captions, receipt in receipts.items():
        rendered = edition.rendered(captions)
        (rendered.stage).mkdir(parents=True)
        (rendered.stage / "index.html").write_text(rendered.name)
        rendered.file.parent.mkdir(parents=True, exist_ok=True)
        rendered.file.write_text(rendered.name)
        repository.write(rendered.receipt, receipt)
    repository.write(edition.timeline, {"duration": 2, "captions": []})
    (tmp_path / picture_rendering.COMPOSITION_SCRIPT).parent.mkdir(parents=True)
    (tmp_path / picture_rendering.COMPOSITION_SCRIPT).write_text("/* film */")
    monkeypatch.setattr(
        equivalence, "validate_picture", lambda _edition, captions: receipts[captions]
    )
    composition = {"instants": 5, "band": None, "differing_instants": 0, "findings": []}

    def run(tool, arguments, *, stdout, environment=None):
        repository.write(stdout, composition)
        return 0

    monkeypatch.setattr(equivalence.tools, "run", run)
    monkeypatch.setattr(equivalence, "compare_decoded", lambda *arguments: [])
    monkeypatch.setattr(faults, "scan", lambda *arguments: {})
    monkeypatch.setattr(faults, "findings", lambda *arguments: [])
    record = equivalence.compare_pictures(edition)
    assert record["verdict"] == "pass"
    assert record["uncaptioned"] == way
    # A receipt written before receipts said so leaves the record as it was.
    receipts[False] = {"picture": "uncaptioned"}
    repository.write(edition.rendered(False).receipt, receipts[False])
    assert "uncaptioned" not in equivalence.compare_pictures(edition)
