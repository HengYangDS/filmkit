"""How an uncaptioned picture is made: derived under software capture, rendered under any other
capture or when asked for, each receipt and comparison record saying which way and why."""

import pytest

import filmkit.media as media
import filmkit.picture.derivation as derivation
import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.graph import bindings, chain
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition
from filmkit.specification import FPS


def declaring(monkeypatch, capture: str) -> None:
    """Declare the film's capture as `[picture] capture` would."""
    picture = FILM.picture.model_copy(update={"capture": capture})
    monkeypatch.setattr(picture_rendering, "FILM", FILM.model_copy(update={"picture": picture}))


def declared_native(film, *codes: str):
    """The film with the editions' uncaptioned pictures declared native, and no other."""
    picture = film.picture.model_copy(update={"native_uncaptioned": codes})
    return film.model_copy(update={"picture": picture})


@pytest.fixture
def edition(film_root, monkeypatch):
    """The Chinese edition staged and checked, with media checks that pass and derivations
    recorded instead of encoded, of a film that declares no uncaptioned picture native."""
    monkeypatch.setattr(bindings, "FILM", declared_native(bindings.FILM))
    edition = Edition("zh")
    film_root.staged(edition)
    monkeypatch.setattr(media, "probe", lambda path: {})
    monkeypatch.setattr(media, "require_video", lambda *arguments, **options: {})
    grid = list(range(0, edition.runtime * FPS, 2 * FPS))
    monkeypatch.setattr(media, "video_cadence", lambda *arguments: {"keyframes": grid})
    derived = []
    monkeypatch.setattr(
        derivation, "derive_uncaptioned", lambda *arguments: derived.append(arguments)
    )
    return edition, film_root, derived


def uncaptioned(code="zh"):
    """Run the node that makes the edition's uncaptioned picture, as a build runs it."""
    chain.render_uncaptioned(Edition(code))


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
    assert receipt["picture"] == "uncaptioned"
    assert not derivation.is_derived(receipt)
    # The receipt still validates as the render it is.
    picture_rendering.validate_picture_binding(edition, receipt, captions=False)


def test_a_film_of_software_capture_derives_and_native_still_renders(edition, monkeypatch):
    edition, film_root, derived = edition
    assert picture_rendering.FILM.picture.capture == "software"
    uncaptioned()
    assert derived == [(edition, derivation.DEADLINE)]
    assert film_root.runs() == []
    # The film declares the edition's uncaptioned picture native (`[picture] native_uncaptioned`).
    monkeypatch.setattr(bindings, "FILM", declared_native(bindings.FILM, "zh"))
    uncaptioned()
    assert len(derived) == 1
    (run,) = film_root.runs()
    assert run["argv"][1] == str(edition.rendered(False).stage)
    receipt = repository.read(edition.rendered(False).receipt)
    assert receipt["uncaptioned"] == {
        "way": "rendered",
        "reason": "a render of its own stage was asked for",
    }


def test_a_render_receipt_names_the_canvas_that_drew_the_picture(edition):
    edition, film_root, _ = edition
    picture_rendering.render_picture(edition, 60)
    drawn = film_root.canvas()
    assert drawn["binary"]["sha256"] == picture_renderer.BINARY_SHA256
    assert drawn["integrity"] == picture_renderer.INTEGRITY[picture_renderer.RENDERER_NAME]
    assert repository.read(edition.render_receipt)["renderer"] == drawn
    # Another build of that version, as the film's packages record it, is named as itself.
    film_root.installs("sha512-another-build")
    picture_rendering.render_picture(edition, 60)
    receipt = repository.read(edition.render_receipt)
    assert receipt["renderer"] == {**drawn, "integrity": "sha512-another-build"}
    # So is another native library than the package's, as the render's processes report it.
    film_root.installs()
    loaded = film_root.loads(sha256="ee" * 32)
    picture_rendering.render_picture(edition, 60)
    binary = repository.read(edition.render_receipt)["renderer"]["binary"]
    assert (binary["sha256"], binary["path"]) == ("ee" * 32, loaded["path"])


def test_a_picture_drawn_by_another_canvas_build_is_not_derived_from(edition):
    edition, film_root, derived = edition
    film_root.installs("sha512-another-build")
    picture_rendering.render_picture(edition, 60)
    # The film declares software capture, and its captioned picture was not drawn by the pinned
    # build: the uncaptioned stage is rendered, and the receipt says why.
    uncaptioned()
    assert derived == []
    assert [run["argv"][1] for run in film_root.runs()] == [
        str(edition.rendered(True).stage),
        str(edition.rendered(False).stage),
    ]
    statement = repository.read(edition.rendered(False).receipt)["uncaptioned"]
    assert statement["way"] == "rendered"
    version = picture_renderer.RENDERER_VERSION
    pinned = picture_renderer.INTEGRITY[picture_renderer.RENDERER_NAME]
    assert statement["reason"] == (
        "the captioned picture is no render by the pinned build that the engine's release "
        f"qualifies: it was drawn by @napi-rs/canvas {version} with the integrity "
        f"sha512-another-build, and the engine pins @napi-rs/canvas {version} with {pinned}"
    )
    # A render whose processes loaded another native library than the pinned one derives
    # nothing either, whatever npm recorded of the packages.
    film_root.installs()
    film_root.loads(sha256="ee" * 32)
    picture_rendering.render_picture(edition, 60)
    assert derivation.uncaptioned_way(edition)["way"] == "rendered"
    assert f"with the SHA-256 {'ee' * 32}" in derivation.uncaptioned_way(edition)["reason"]
    film_root.loads()
    # A captioned receipt that names no canvas, as a browser's render wrote it, derives nothing,
    # nor one whose text another renderer drew.
    receipt = repository.read(edition.render_receipt)
    repository.write(edition.render_receipt, {**receipt, "renderer": None})
    assert derivation.uncaptioned_way(edition) == {
        "way": "rendered",
        "reason": "the captioned picture is no render by the pinned build that the engine's "
        "release qualifies: its receipt names no canvas",
    }
    # Drawn by the pinned build, it is derived from.
    film_root.installs()
    picture_rendering.render_picture(edition, 60)
    assert derivation.uncaptioned_way(edition)["way"] == "derived"
    portable = repository.read(edition.render_receipt)
    portable["renderer"]["text_renderer"] = "portable"
    assert picture_renderer.unqualified(portable) == "its text was drawn by the portable renderer"
    uncaptioned()
    assert derived == [(edition, derivation.DEADLINE)]


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
        rendered.page.write_text(rendered.name)
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
