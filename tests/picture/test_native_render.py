"""A native render as it really runs: the engine's renderer through Node, the canvas package the
repository installs and FFmpeg, on a stage of a small composition of the test's own. The films
it writes are read by the engine's own contract of a picture's video (`filmkit.media`)."""

import json
import shutil
import signal
import subprocess
import sys
import time

import pytest
from real_processes import wait_for

import filmkit.media as media
import filmkit.picture.browser as picture_browser
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.production import STAGE_PAGE, Edition
from filmkit.specification import DURATION

# Every test here has the deadline of a test that starts real processes, and their end.
pytestmark = [pytest.mark.ffmpeg, pytest.mark.usefixtures("processes")]

# The repository's own npm packages, the sample film's fonts and the engine's launcher, found
# before a test rebinds the repository root and the launcher.
PACKAGES = repository.node_modules()
FONTS = repository.ROOT / "assets/fonts"
LAUNCHER = picture_renderer.launcher
# A composition that draws the edition, the time and a caption's text in a face of the sample
# film's stylesheet, so that every frame differs from the last.
COMPOSITION = """
window.renderFrame = (seconds) => {
  const picture = document.getElementById("picture").getContext("2d");
  const width = Number(document.getElementById("film").dataset.width);
  picture.fillStyle = "#0f1519";
  picture.fillRect(0, 0, width, (width * 9) / 16);
  picture.fillStyle = "#e8eef2";
  picture.font = `${width / 32}px Sample`;
  const shown = window.FILM.captions.map((caption) => caption.text).join("");
  const words = `${window.FILM.edition} ${seconds.toFixed(2)} ${shown}`;
  picture.fillText(words, width / 8 + seconds * 6, width / 4);
};
"""
# The command that runs the engine's own run of a renderer in a process of its own, for a test
# that asks it to end.
COMMAND = """
import json, pathlib, sys
import filmkit.picture.renderer as renderer
renderer.repository.ROOT = pathlib.Path(sys.argv[1])
note("command")
renderer.run_renderer(json.loads(sys.argv[2]), 300)
"""
# Two frames a second keep each render short: the film's frames in groups of four.
FPS = 2


@pytest.fixture
def stage(film_root, monkeypatch):
    """A film root that installs the repository's canvas package and draws with the engine's
    renderer: `staged(width, height, captions)` stages the Chinese edition's picture."""
    shutil.rmtree(film_root.path / "node_modules")
    (film_root.path / "node_modules").symlink_to(PACKAGES)
    monkeypatch.setattr(picture_renderer, "launcher", LAUNCHER)
    (film_root.path / picture_rendering.COMPOSITION_SCRIPT).write_text(COMPOSITION)
    for font in FONTS.iterdir():
        shutil.copyfile(font, film_root.path / "assets/fonts" / font.name)
    edition = Edition("zh")
    film_root.timeline(edition, captions=[{"start": 0, "end": DURATION, "text": "先看数据。"}])

    def staged(name, width, height, *, captions=True):
        folder = film_root.path / "build/runtime/work/native" / name
        picture_rendering.stage_picture(edition, folder, DURATION, width, height, captions=captions)
        return folder

    return staged


def drawn(folder, spans):
    """Draw a stage at FPS in `spans` spans through the engine's own run and receipt."""
    output, receipt = folder.with_suffix(f".{spans}.mp4"), folder.with_suffix(f".{spans}.json")
    command = picture_renderer.command(folder, output, FPS, spans)
    page = folder / STAGE_PAGE
    return output, picture_renderer.record_render(command, page, output, receipt, 120, "test")


def test_a_native_picture_meets_the_engines_contract_of_a_picture(
    stage, film_root, monkeypatch, tmp_path
):
    folder, frames = stage("captioned", 1920, 1080), DURATION * FPS
    # No browser is supplied to this film, and one that is named would leave a mark if it ran.
    started = tmp_path / "browser-started"
    browser = tmp_path / "browser"
    browser.write_text(f"#!{sys.executable}\nopen({str(started)!r}, 'w').close()\n")
    browser.chmod(0o755)
    monkeypatch.setenv("FILM_CHROMIUM_PATH", str(browser))
    assert not picture_browser.supplied_browser().exists()
    joined, receipt = drawn(folder, 3)
    assert not started.exists()
    # The receipt states what ran: the pinned canvas with the host's text and the native library
    # its spans loaded, three spans, every frame, and a digest of what was drawn.
    assert picture_renderer.unqualified(receipt) is None
    picture_renderer.require_receipt_renderer(receipt)
    library = receipt["renderer"]["binary"]
    assert (library["package"], library["sha256"]) == (
        picture_renderer.BINARY_PACKAGE,
        picture_renderer.BINARY_SHA256,
    )
    assert repository.sha(library["path"]) == picture_renderer.BINARY_SHA256
    assert (receipt["spans"], receipt["frames"], receipt["exit"]) == (3, frames, 0)
    assert len(receipt["drawn_sha256"]) == 64
    # The film joined from spans is the picture the engine validates: every frame on the grid,
    # no B-frame, and a keyframe at every two seconds and nowhere else.
    media.require_video(
        media.probe(joined), frames=frames, fps=FPS, size=(1920, 1080), duration=DURATION
    )
    group = 2 * FPS
    assert media.video_cadence(joined, frames, FPS)["keyframes"] == list(range(0, frames, group))
    # Neither the spans' folder nor the renderer's report is left.
    left = sorted(path.name for path in folder.parent.iterdir())
    assert left == ["captioned", "captioned.3.json", "captioned.3.mp4"]
    # One process draws the same frames and writes the same keyframes.
    whole, again = drawn(folder, 1)
    assert (again["spans"], again["drawn_sha256"]) == (1, receipt["drawn_sha256"])
    assert media.video_cadence(whole, frames, FPS)["keyframes"] == list(range(0, frames, group))


def test_the_uncaptioned_stage_draws_other_frames_than_the_captioned_one(stage):
    captioned, uncaptioned = (
        stage("captioned", 1920, 1080),
        stage("bare", 1920, 1080, captions=False),
    )
    first, second = drawn(captioned, 1)[1], drawn(uncaptioned, 1)[1]
    assert first["frames"] == second["frames"] == DURATION * FPS
    assert first["drawn_sha256"] != second["drawn_sha256"]


def test_a_face_that_does_not_register_fails_the_render(stage, film_root):
    folder = stage("captioned", 1920, 1080)
    first = next(iter(sorted((folder / "fonts").iterdir())))
    first.write_text("no font")
    with pytest.raises(picture_rendering.PictureError, match="did not complete"):
        drawn(folder, 1)
    receipt = repository.read(folder.with_suffix(".1.json"))
    assert (receipt["exit"], receipt["drawn_sha256"]) == (1, None)


def test_a_draw_that_fails_midway_fails_the_render_at_once(stage, film_root):
    # The composition draws the first second and then fails, as a scene that fails at one time.
    failing = COMPOSITION.replace(
        "  picture.fillText(", "  if (seconds > 1) picture.noSuchCall();\n  picture.fillText("
    )
    assert failing != COMPOSITION
    (film_root.path / picture_rendering.COMPOSITION_SCRIPT).write_text(failing)
    folder = stage("failing", 1920, 1080)
    for spans in (1, 2):
        began = time.monotonic()
        with pytest.raises(picture_rendering.PictureError, match="did not complete"):
            drawn(folder, spans)
        # It ended by its own status, far from its deadline of 120 s, with nothing left running.
        assert time.monotonic() - began < 60
        receipt = repository.read(folder.with_suffix(f".{spans}.json"))
        assert (receipt["exit"], receipt["timed_out"], receipt["drawn_sha256"]) == (1, False, None)
        found = subprocess.run(["pgrep", "-f", str(folder)], capture_output=True, text=True)
        assert found.stdout.split() == []


def test_a_render_asked_to_end_leaves_no_span_and_no_encoder(stage, film_root, processes):
    # A film at the pictures' frame rate, in two spans, takes long enough to be met midway.
    folder = stage("whole", 1920, 1080)
    output = folder.with_suffix(".mp4")
    command = picture_renderer.command(folder, output, 60, 2)
    asked = processes.python(
        processes.script("command", COMMAND), str(film_root.path), json.dumps(command)
    )
    processes.noted("command")

    def running():
        found = subprocess.run(["pgrep", "-f", str(folder)], capture_output=True, text=True)
        return [int(line) for line in found.stdout.split()]

    # The command, the renderer, its two spans and their encoders all name the stage in their
    # commands.
    assert wait_for(lambda: len(running()) >= 6, 60)
    asked.send_signal(signal.SIGTERM)
    assert asked.wait(timeout=60) != 0
    assert wait_for(lambda: running() == [], 20)
    # It leaves no picture and no report that a later run could take for a whole render: the
    # picture is written by the join alone, and what the spans left is theirs to remove.
    work = folder.with_name(folder.name + "-spans")
    assert not output.exists() and not work.with_name(work.name + ".json").exists()
    assert all(path.name.startswith("span-") for path in work.iterdir())
