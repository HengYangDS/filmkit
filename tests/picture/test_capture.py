"""The capture declaration: the flags each render passes the renderer, the mode its receipt
records, and the mode validation reads back from a receipt."""

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition


def declaring(monkeypatch, capture: str) -> None:
    """Declare the film's capture as `[picture] capture` would."""
    picture = FILM.picture.model_copy(update={"capture": capture})
    monkeypatch.setattr(picture_rendering, "FILM", FILM.model_copy(update={"picture": picture}))


def rendered(film_root, captions: bool = True) -> dict:
    """Stage and check the Chinese edition, render one picture and return its receipt."""
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60, captions=captions)
    return repository.read(edition.rendered(captions).receipt)


def picture_command(
    film_root, captions: bool, capture_flag: str, browser_flag: str = "--browser-gpu"
) -> list[str]:
    """filmkit 0.19.0's renderer command for a picture of the Chinese edition, with the capture
    and browser flags given."""
    places = Edition("zh").rendered(captions)
    return [
        str(film_root.renderer),
        "render",
        str(places.stage),
        "--output",
        str(places.file),
        "--fps",
        "60",
        "--quality",
        "looks",
        "--crf",
        "14",
        "--workers",
        "8",
        "--gpu",
        browser_flag,
        "--no-low-memory-mode",
        capture_flag,
        "--strict",
    ]


@pytest.mark.parametrize("captions", [True, False])
def test_the_default_capture_keeps_the_0_19_0_command(film_root, captions):
    receipt = rendered(film_root, captions)
    expected = picture_command(film_root, captions, "--experimental-fast-capture")
    assert receipt["command"] == expected
    assert [run["argv"] for run in film_root.runs()] == [expected[1:]]
    assert receipt["capture"] == "fast"


@pytest.mark.parametrize("captions", [True, False])
def test_screenshot_capture_turns_fast_capture_off_in_its_place(film_root, monkeypatch, captions):
    declaring(monkeypatch, "screenshot")
    receipt = rendered(film_root, captions)
    expected = picture_command(film_root, captions, "--experimental-fast-capture=false")
    assert receipt["command"] == expected
    assert [run["argv"] for run in film_root.runs()] == [expected[1:]]
    assert receipt["capture"] == "screenshot"
    picture_rendering.validate_picture_binding(Edition("zh"), receipt, captions=captions)


@pytest.mark.parametrize("captions", [True, False])
def test_software_capture_draws_in_the_software_rasterizer(film_root, monkeypatch, captions):
    declaring(monkeypatch, "software")
    receipt = rendered(film_root, captions)
    expected = picture_command(
        film_root, captions, "--experimental-fast-capture=false", "--no-browser-gpu"
    )
    assert receipt["command"] == expected
    assert [run["argv"] for run in film_root.runs()] == [expected[1:]]
    assert receipt["capture"] == "software"
    picture_rendering.validate_picture_binding(Edition("zh"), receipt, captions=captions)


@pytest.mark.parametrize(
    ("flags", "mode"),
    [
        (["--browser-gpu", "--experimental-fast-capture"], "fast"),
        (["--experimental-fast-capture"], "fast"),
        (["--browser-gpu", "--experimental-fast-capture=false"], "screenshot"),
        (["--no-browser-gpu", "--experimental-fast-capture=false"], "software"),
        (["--no-browser-gpu", "--experimental-fast-capture"], None),
        (["--browser-gpu"], None),
        (["--experimental-fast-capture", "--experimental-fast-capture=false"], None),
    ],
)
def test_a_command_names_its_capture_by_its_capture_and_browser_flags(flags, mode):
    assert picture_rendering.command_capture(["hyperframes", "render", *flags]) == mode


@pytest.mark.parametrize(
    ("rendered_with", "declared"),
    [
        ("fast", "screenshot"),
        ("screenshot", "fast"),
        ("screenshot", "software"),
        ("software", "screenshot"),
    ],
)
def test_validation_refuses_a_picture_of_another_capture(
    film_root, monkeypatch, rendered_with, declared
):
    declaring(monkeypatch, rendered_with)
    receipt = rendered(film_root)
    declaring(monkeypatch, declared)
    named = f"rendered with {rendered_with} capture; the film declares {declared} capture"
    with pytest.raises(PictureError, match=named):
        picture_rendering.validate_picture_binding(Edition("zh"), receipt)


def test_a_receipt_written_before_the_declaration_is_read_by_its_flag(film_root, monkeypatch):
    # filmkit 0.19.0 wrote no capture; its command passes the fast capture flag.
    earlier = {key: value for key, value in rendered(film_root).items() if key != "capture"}
    picture_rendering.validate_picture_binding(Edition("zh"), earlier)
    declaring(monkeypatch, "screenshot")
    named = "rendered with fast capture; the film declares screenshot capture"
    with pytest.raises(PictureError, match=named):
        picture_rendering.validate_picture_binding(Edition("zh"), earlier)


def test_a_receipt_whose_capture_disagrees_with_its_command_is_refused(film_root):
    receipt = rendered(film_root)
    unflagged = [part for part in receipt["command"] if part != "--experimental-fast-capture"]
    for changed, named in (
        ({"capture": "screenshot"}, "records screenshot capture, but its command passes fast"),
        ({"command": unflagged}, "records fast capture, but its command passes no capture flag"),
    ):
        with pytest.raises(PictureError, match=named):
            picture_rendering.validate_picture_binding(Edition("zh"), {**receipt, **changed})
    # A receipt that records no capture and passes no flag was rendered in no declared mode.
    unrecorded = {key: value for key, value in receipt.items() if key != "capture"}
    with pytest.raises(PictureError, match="rendered with no capture; the film declares fast"):
        picture_rendering.validate_picture_binding(
            Edition("zh"), {**unrecorded, "command": unflagged}
        )
