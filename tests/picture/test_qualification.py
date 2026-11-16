"""Qualifying the renderer: a second render of the captioned stage, compared frame by frame."""

import subprocess

import pytest

import filmkit.media as media
import filmkit.picture.qualification as qualification
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition

# The renderer version the fixture's film installs, which is the engine's.
RENDERER = picture_rendering.RENDERER_VERSION


@pytest.fixture
def rendered(film_root, monkeypatch):
    """The Chinese edition with its captioned picture rendered by the stand-in and media checks
    that pass; each render's frames are read from the digests set for its file."""
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    monkeypatch.setattr(media, "probe", lambda path: {})
    monkeypatch.setattr(media, "require_video", lambda *arguments, **options: {})
    monkeypatch.setattr(media, "video_cadence", lambda *arguments: {"keyframes": []})
    digests = {}
    monkeypatch.setattr(qualification, "frame_digests", lambda path: digests[path.parent.name])
    # The browser the renders run: a build of the test's own, named as a film names another.
    browser = film_root.path.parent / "browser/chrome-headless-shell"
    browser.parent.mkdir()
    browser.write_text("a browser build")
    monkeypatch.setenv("FILM_CHROMIUM_PATH", str(browser))
    return edition, film_root, digests


def test_two_renders_that_decode_alike_pass_and_the_second_is_removed(rendered):
    edition, film_root, digests = rendered
    digests |= {"zh": ["a", "b", "c"]}
    record = qualification.qualify_renderer(edition, 60)
    assert repository.read(edition.renderer_qualification) == record
    assert (record["verdict"], record["differing_frames"]) == ("pass", 0)
    assert record["first_differing_frame"] is None
    assert record["renderer"] == {"package": "hyperframes", "version": RENDERER}
    # The record names the capture the two renders were made with, the sample film's own.
    assert record["capture"] == "software"
    first, second = record["first"], record["second"]
    assert first["sha256"] == repository.sha(edition.picture)
    assert (first["frames"], second["frames"]) == (3, 3)
    assert first["workers"] == second["workers"] == picture_rendering.render_workers()
    work = repository.ROOT / qualification.WORK / "zh"
    assert not (work / edition.picture.name).exists()
    # The second render ran the pictures' command on the same stage, to the work file.
    again = film_root.runs()[-1]["argv"]
    assert again[1] == str(edition.picture_stage)
    assert again[again.index("--output") + 1] == str(work / edition.picture.name)
    # The delivered picture and its receipt are as they were.
    picture_rendering.validate_picture(edition)


def test_the_record_states_the_renderer_and_the_browser_that_ran(rendered, monkeypatch):
    edition, film_root, digests = rendered
    digests |= {"zh": ["a"]}
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
    edition, film_root, _ = rendered
    monkeypatch.delenv("FILM_CHROMIUM_PATH")
    runs = len(film_root.runs())
    with pytest.raises(PictureError, match="No browser at .*chrome-headless-shell; run .*supply"):
        qualification.qualify_renderer(edition, 60)
    assert len(film_root.runs()) == runs


def test_a_frame_that_differs_is_refused_by_the_first_such_frame(rendered, monkeypatch):
    edition, _, _ = rendered
    by_file = {edition.picture: ["a", "b", "c", "d"]}
    monkeypatch.setattr(
        qualification, "frame_digests", lambda path: by_file.get(path, ["a", "x", "c", "y"])
    )
    with pytest.raises(PictureError, match="frame 1 is the first of 2 that differ"):
        qualification.qualify_renderer(edition, 60)
    record = repository.read(edition.renderer_qualification)
    assert (record["verdict"], record["differing_frames"]) == ("refuse", 2)
    assert record["first_differing_frame"] == 1
    # The second render is kept for inspection.
    assert (repository.ROOT / qualification.WORK / "zh" / edition.picture.name).is_file()


def test_renders_of_other_lengths_are_refused(rendered, monkeypatch):
    edition, _, _ = rendered
    by_file = {edition.picture: ["a", "b", "c"]}
    monkeypatch.setattr(qualification, "frame_digests", lambda path: by_file.get(path, ["a", "b"]))
    with pytest.raises(PictureError, match="the renders hold 3 and 2 frames"):
        qualification.qualify_renderer(edition, 60)


def test_a_picture_that_is_not_valid_is_not_rendered_again(rendered):
    edition, film_root, _ = rendered
    edition.picture.write_text("another picture")
    runs = len(film_root.runs())
    with pytest.raises(PictureError, match="rendered picture differs from its receipt"):
        qualification.qualify_renderer(edition, 60)
    assert len(film_root.runs()) == runs


@pytest.mark.ffmpeg
def test_the_digests_are_one_for_each_decoded_frame(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    clips = []
    for name, colour in (("a", "0x0F1519"), ("b", "0x0F1519"), ("c", "0x101519")):
        clip = tmp_path / f"{name}.mp4"
        command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-f", "lavfi"]
        command += ["-i", f"color=c={colour}:s=64x36:r=60:d=0.5", "-c:v", "libx264", "-qp", "0"]
        subprocess.run([*command, "-pix_fmt", "yuv420p", str(clip)], check=True, timeout=60)
        clips.append(qualification.frame_digests(clip))
    assert [len(digests) for digests in clips] == [30, 30, 30]
    assert clips[0] == clips[1] != clips[2]
