"""Qualifying the renderer: a second render of the captioned stage, compared with the first by the
measure of a rendered pair, on small real clips that the stand-in renderer writes."""

import json

import pytest
from test_faults import CAPTION, FRAGMENT, LABEL, SECONDS, encode

import filmkit.picture.qualification as qualification
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition

pytestmark = pytest.mark.ffmpeg

# The renderer version the fixture's film installs, which is the engine's.
RENDERER = picture_rendering.RENDERER_VERSION
FRAMES = SECONDS * 60


@pytest.fixture
def rendered(film_root, tmp_path, monkeypatch):
    """The Chinese edition staged and checked, with a renderer that writes the clips queued for
    it: `renders(first, second)` queues the picture's render and the qualification's and renders
    the picture. A picture's binding is validated as it is; its media, which are a film's size
    and length, are not."""
    edition = Edition("zh")
    film_root.staged(edition)

    def bound(edition, captions=True):
        receipt = repository.read(edition.rendered(captions).receipt)
        picture_rendering.validate_picture_binding(edition, receipt, captions=captions)
        return receipt

    monkeypatch.setattr(picture_rendering, "validate_picture", bound)

    def renders(*clips):
        files = []
        for number, boxes in enumerate(clips):
            files.append(tmp_path / f"render-{number}.mp4")
            encode(files[-1], *boxes)
        film_root.queue(edition.picture, *files)
        picture_rendering.render_picture(edition, 60)

    # The browser the renders run: a build of the test's own, named as a film names another.
    browser = film_root.path.parent / "browser/chrome-headless-shell"
    browser.parent.mkdir()
    browser.write_text("a browser build")
    monkeypatch.setenv("FILM_CHROMIUM_PATH", str(browser))
    return edition, film_root, renders


def test_two_renders_that_show_the_same_pass_and_the_second_is_removed(rendered, capsys):
    edition, film_root, renders = rendered
    renders([CAPTION, LABEL], [CAPTION, LABEL])
    capsys.readouterr()
    record = qualification.qualify_renderer(edition, 60)
    assert repository.read(edition.renderer_qualification) == record
    assert [*record] == [
        "renderer",
        "browser",
        "capture",
        "stage_sha256",
        "first",
        "second",
        "comparison",
        "identical_frames",
        "first_differing_frame",
        "lowest_psnr_db",
        "lowest_psnr_frame",
        "findings",
        "verdict",
    ]
    assert (record["verdict"], record["findings"]) == ("pass", [])
    assert (record["identical_frames"], record["first_differing_frame"]) == (FRAMES, None)
    assert (record["lowest_psnr_db"], record["lowest_psnr_frame"]) == (None, None)
    assert record["renderer"] == {"package": "hyperframes", "version": RENDERER}
    # The record names the capture the two renders were made with, the sample film's own.
    assert record["capture"] == "software"
    first, second = record["first"], record["second"]
    assert first["sha256"] == repository.sha(edition.picture)
    assert (first["frames"], second["frames"]) == (FRAMES, FRAMES)
    assert first["workers"] == second["workers"] == 8
    # The comparison's report: the sampled frames against their floor, and every frame's scan.
    comparison = record["comparison"]
    assert (comparison["frames"], comparison["failing_frames"]) == (4, 0)
    assert comparison["psnr_floor_db"] == 45.0 and comparison["lowest_psnr_db"] is None
    every = comparison["every_frame"]
    assert (every["frames"], every["differing_frames"], every["fault_frames"]) == (FRAMES, 0, 0)
    assert (every["lasting_runs"], every["residue_frames"]) == (0, 0)
    assert every["slivers"]["frames_beyond_the_bound"] == 0
    # The printed line names the verdict, the findings, the frames that decode identically and
    # the lowest PSNR of any frame, which no frame has here.
    printed = json.loads(capsys.readouterr().out.splitlines()[-1])
    facts = {"identical_frames": FRAMES, "lowest_psnr_db": None}
    assert printed == {"verdict": "pass", "findings": [], **facts}
    work = repository.ROOT / qualification.WORK / "zh"
    assert not (work / edition.picture.name).exists()
    # The second render ran the pictures' command on the same stage, to the work file.
    again = film_root.runs()[-1]["argv"]
    assert again[1] == str(edition.picture_stage)
    assert again[again.index("--output") + 1] == str(work / edition.picture.name)
    # The delivered picture and its receipt are as they were.
    picture_rendering.validate_picture(edition)


def test_the_record_states_the_renderer_and_the_browser_that_ran(rendered, monkeypatch):
    edition, film_root, renders = rendered
    renders([CAPTION], [CAPTION], [CAPTION])
    browser = film_root.path.parent / "browser/chrome-headless-shell"
    # A browser named by the film, which is not the build the engine pins.
    record = qualification.qualify_renderer(edition, 60)
    assert record["browser"] == {
        "executable": str(browser),
        "sha256": repository.sha(browser),
        "pinned_build": None,
    }
    # The pinned build is named when the executable that ran holds its bytes.
    monkeypatch.setattr(picture_rendering, "BROWSER_SHA256", repository.sha(browser))
    record = qualification.qualify_renderer(edition, 60)
    product, version = picture_rendering.BROWSER
    assert record["browser"]["pinned_build"] == f"{product}@{version}"
    # The renderer's version is the installed package's, read when the qualification runs.
    manifest = film_root.path / "node_modules" / picture_rendering.RENDERER_PACKAGE
    manifest.write_text('{"name": "hyperframes", "version": "0.0.1"}')
    runs = len(film_root.runs())
    with pytest.raises(PictureError, match="The film installs HyperFrames 0.0.1"):
        qualification.qualify_renderer(edition, 60)
    assert len(film_root.runs()) == runs


def test_a_qualification_without_a_browser_is_refused_before_it_renders(rendered, monkeypatch):
    edition, film_root, renders = rendered
    renders([CAPTION])
    # No browser is named, and the supply has installed none.
    monkeypatch.delenv("FILM_CHROMIUM_PATH")
    picture_rendering.supplied_browser().unlink()
    runs = len(film_root.runs())
    with pytest.raises(PictureError, match="No browser at .*chrome-headless-shell; run .*supply"):
        qualification.qualify_renderer(edition, 60)
    assert len(film_root.runs()) == runs


def test_a_one_frame_fault_of_the_second_render_is_refused_by_its_frame(rendered, capsys):
    edition, _, renders = rendered
    renders([CAPTION], [CAPTION, FRAGMENT])
    fault = (
        "encoded frame 77 at 1.283 s: the second picture holds a one-frame fault of 150 levels "
        "in box [40, 10, 44, 14]"
    )
    kept = "build/runtime/work/renderer-qualification/zh"
    with pytest.raises(PictureError) as refused:
        qualification.qualify_renderer(edition, 60)
    assert str(refused.value) == (
        f"Two renders of the zh captioned stage do not show the same: {fault}; the second "
        f"render is kept in {kept}"
    )
    record = repository.read(edition.renderer_qualification)
    assert (record["verdict"], record["findings"]) == ("refuse", [fault])
    assert record["comparison"]["every_frame"]["fault_frames"] == 1
    # One frame of 120 does not decode identically; that is recorded and decides nothing.
    assert (record["identical_frames"], record["first_differing_frame"]) == (FRAMES - 1, 77)
    # The lowest PSNR of any frame is that frame's, which no sampled frame is.
    assert record["lowest_psnr_frame"] == 77 and record["lowest_psnr_db"] < 60
    assert record["comparison"]["lowest_psnr_db"] is None
    printed = json.loads(capsys.readouterr().out.splitlines()[-1])
    facts = {"identical_frames": FRAMES - 1, "lowest_psnr_db": record["lowest_psnr_db"]}
    assert printed == {"verdict": "refuse", "findings": [fault], **facts}
    # The second render is kept for inspection.
    assert (repository.ROOT / kept / edition.picture.name).is_file()


def test_renders_of_other_lengths_are_refused(rendered, tmp_path, monkeypatch):
    edition, film_root, renders = rendered
    renders([CAPTION])
    # The picture holds two seconds; the render queued for the qualification holds one.
    monkeypatch.setattr("test_faults.SECONDS", 1)
    encode(tmp_path / "short.mp4", CAPTION)
    film_root.queue(edition.picture, tmp_path / "short.mp4")
    with pytest.raises(PictureError, match="the renders hold 120 and 60 frames; the second"):
        qualification.qualify_renderer(edition, 60)
    record = repository.read(edition.renderer_qualification)
    assert (record["first"]["frames"], record["second"]["frames"]) == (120, 60)
    assert (record["comparison"], record["verdict"]) == (None, "refuse")


def test_a_picture_that_is_not_valid_is_not_rendered_again(rendered):
    edition, film_root, renders = rendered
    renders([CAPTION])
    edition.picture.write_text("another picture")
    runs = len(film_root.runs())
    with pytest.raises(PictureError, match="rendered picture differs from its receipt"):
        qualification.qualify_renderer(edition, 60)
    assert len(film_root.runs()) == runs
