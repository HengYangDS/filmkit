"""The engine's renderer as a film meets it: the command a render runs, the spans it is drawn in,
the canvas a receipt names, and the data a stage holds for it."""

import json
import sys
import textwrap
from pathlib import Path

import pytest

import filmkit.media as media
import filmkit.picture.browser as picture_browser
import filmkit.picture.derivation as derivation
import filmkit.picture.draft as picture_draft
import filmkit.picture.encoding as encoding
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition
from filmkit.specification import DURATION, FPS


def spans_of(command):
    return command[command.index("--spans") + 1]


def test_a_picture_is_drawn_in_four_spans_and_a_draft_in_one(film_root, monkeypatch):
    monkeypatch.delenv(picture_renderer.SPANS_VARIABLE, raising=False)
    assert picture_renderer.spans() == picture_renderer.SPANS == 4
    assert picture_renderer.DRAFT_SPANS == 1
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    receipt = repository.read(edition.render_receipt)
    assert (spans_of(receipt["command"]), receipt["spans"]) == ("4", 4)


def test_a_count_named_for_a_measurement_is_passed_and_recorded(film_root, monkeypatch):
    monkeypatch.setenv(picture_renderer.SPANS_VARIABLE, "6")
    assert picture_renderer.spans() == 6
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    receipt = repository.read(edition.render_receipt)
    assert (spans_of(receipt["command"]), receipt["spans"]) == ("6", 6)


@pytest.mark.parametrize("named", ["many", "0", "-1", "1.5", "４"])
def test_a_value_that_is_no_count_is_refused_by_the_variables_name(film_root, monkeypatch, named):
    monkeypatch.setenv(picture_renderer.SPANS_VARIABLE, named)
    edition = Edition("zh")
    film_root.staged(edition)
    with pytest.raises(PictureError, match="FILMKIT_RENDER_SPANS names"):
        picture_rendering.render_picture(edition, 60)
    assert film_root.runs() == []


def test_an_empty_variable_names_no_count(monkeypatch):
    monkeypatch.setenv(picture_renderer.SPANS_VARIABLE, "")
    assert picture_renderer.spans() == 4


def test_a_receipt_names_the_canvas_installed_and_the_library_loaded(film_root):
    name, binary = picture_renderer.RENDERER_NAME, picture_renderer.BINARY_PACKAGE
    version, pinned = picture_renderer.RENDERER_VERSION, picture_renderer.INTEGRITY
    assert picture_renderer.installed() == {
        "package": name,
        "version": version,
        "integrity": pinned[name],
    }
    loaded = film_root.loads()
    drawn = picture_renderer.drawn_by({"text_renderer": "system", "binary": loaded})
    assert drawn == {
        **picture_renderer.installed(),
        "binary": {
            "package": binary,
            "version": version,
            "integrity": pinned[binary],
            "path": loaded["path"],
            "sha256": picture_renderer.BINARY_SHA256,
        },
        "text_renderer": "system",
    }
    assert picture_renderer.unqualified({"renderer": drawn}) is None
    # A render that reported nothing names no library, and is no render by the pinned build.
    unreported = picture_renderer.drawn_by({})
    assert unreported["binary"] == dict.fromkeys(
        ("package", "version", "integrity", "path", "sha256")
    )
    assert "native library of None None with the SHA-256 None" in picture_renderer.unqualified(
        {"renderer": {**unreported, "text_renderer": "system"}}
    )
    # Packages that record nothing of what npm installed name no integrity, and no pinned build.
    (film_root.path / "node_modules" / picture_renderer.INSTALLED).unlink()
    assert picture_renderer.installed() == {"package": name, "version": version, "integrity": None}
    why = picture_renderer.unqualified({"renderer": {**drawn, "integrity": None}})
    assert why == (
        f"it was drawn by {name} {version} with the integrity None, and the engine pins "
        f"{name} {version} with {pinned[name]}"
    )


def test_a_library_that_is_not_the_pinned_one_is_named_as_itself_on_any_host(film_root):
    # The pinned package with other bytes, as the loader takes them from a named file.
    other = picture_renderer.drawn_by(
        {"text_renderer": "system", "binary": film_root.loads(sha256="ee" * 32)}
    )
    version = picture_renderer.RENDERER_VERSION
    assert picture_renderer.unqualified({"renderer": other}) == (
        f"its canvas loaded the native library of {picture_renderer.BINARY_PACKAGE} {version} "
        f"with the SHA-256 {'ee' * 32}, and the engine pins that of "
        f"{picture_renderer.BINARY_PACKAGE} {version}, {picture_renderer.BINARY_SHA256}"
    )
    # Another platform's package is recorded as it is, with what npm recorded of it: nothing.
    linux = film_root.loads(sha256="dd" * 32, package="@napi-rs/canvas-linux-x64-gnu")
    drawn = picture_renderer.drawn_by({"text_renderer": "system", "binary": linux})
    assert (drawn["binary"]["package"], drawn["binary"]["integrity"]) == (linux["package"], None)
    assert "@napi-rs/canvas-linux-x64-gnu" in picture_renderer.unqualified({"renderer": drawn})
    # The receipt still validates as the engine's renderer: only a derivation asks for the pin.
    picture_renderer.require_receipt_renderer({"renderer": drawn})


def test_the_pins_are_what_the_engines_own_packages_hold():
    # The repository's own packages, which the sample film builds with, are the pinned build:
    # the integrity npm recorded, and the bytes of the native library its binary package holds.
    name = picture_renderer.RENDERER_NAME
    assert picture_renderer.installed()["integrity"] == picture_renderer.INTEGRITY[name]
    held = repository.node_modules() / picture_renderer.BINARY_PACKAGE
    recorded = picture_renderer.recorded(picture_renderer.BINARY_PACKAGE)
    assert recorded["integrity"] == picture_renderer.INTEGRITY[picture_renderer.BINARY_PACKAGE]
    [library] = held.glob("*.node")
    assert repository.sha(library) == picture_renderer.BINARY_SHA256


def test_a_render_is_not_given_the_variable_that_names_another_library(film_root, monkeypatch):
    monkeypatch.setenv(picture_renderer.LIBRARY_VARIABLE, "/elsewhere/skia.node")
    monkeypatch.setenv("FILMKIT_KEPT", "kept")
    shown = film_root.path / "environment.json"
    script = "import json, os, sys; json.dump(dict(os.environ), open(sys.argv[1], 'w'))"
    status = picture_renderer.run_renderer([sys.executable, "-c", script, str(shown)], 30)
    assert status == (0, False)
    environment = json.loads(shown.read_text())
    assert picture_renderer.LIBRARY_VARIABLE not in environment
    assert environment["FILMKIT_KEPT"] == "kept"


def test_a_stage_holds_the_data_its_document_inlines(film_root):
    edition = Edition("zh")
    film_root.timeline(edition, captions=[{"start": 1, "end": 2, "text": "先看数据。"}])
    film_root.staged(edition)
    captioned, uncaptioned = edition.rendered(True).stage, edition.rendered(False).stage
    data = (captioned / picture_rendering.DATA).read_text()
    assert f"window.FILM={data};</script>" in (captioned / "index.html").read_text()
    film = json.loads(data)
    assert (film["edition"], film["render_offset"], len(film["captions"])) == ("zh", 0, 1)
    # The uncaptioned stage's data is the same timeline with no captions.
    assert json.loads((uncaptioned / picture_rendering.DATA).read_text()) == {
        **film,
        "captions": [],
    }
    # Data edited after staging, or removed, is not what the current sources derive.
    (captioned / picture_rendering.DATA).write_text(data.replace("先看数据", "先看别的"))
    with pytest.raises(PictureError, match="picture data differs"):
        picture_rendering.require_current_stage(edition, captioned)
    (captioned / picture_rendering.DATA).unlink()
    with pytest.raises(PictureError, match="picture data differs"):
        picture_rendering.require_current_stage(edition, captioned)


def test_a_rendered_picture_is_encoded_as_its_derived_twin_is(film_root):
    # One definition for both pictures of an edition, held here option by option.
    assert (
        derivation.ENCODER
        == encoding.encoder(FPS)
        == (
            *("-c:v", "libx264", "-preset", "veryfast", "-crf", "12"),
            *("-g", "120", "-keyint_min", "120", "-sc_threshold", "0", "-bf", "0"),
            *("-pix_fmt", "yuv420p"),
        )
    )
    stage = Edition("zh").picture_stage
    command = picture_renderer.command(stage, stage.with_suffix(".mp4"), FPS, 4)
    assert json.loads(command[command.index("--encoder") + 1]) == list(derivation.ENCODER)
    assert command[command.index("--group") + 1] == "120"
    # A draft's ten frames a second keep the two seconds between keyframes.
    draft = picture_renderer.command(stage, stage.with_suffix(".mp4"), 10, 1)
    options = json.loads(draft[draft.index("--encoder") + 1])
    assert draft[draft.index("--group") + 1] == options[options.index("-g") + 1] == "20"
    assert options[options.index("-keyint_min") + 1] == "20"
    # The text renderer has one owner, and the command names it to the module.
    assert command[command.index("--text-renderer") + 1] == picture_renderer.TEXT_RENDERER


class Declared:
    """A film's declaration whose capture no render may read, wherever a render finds it."""

    def __init__(self, declared, capture):
        self.declared, self.capture = declared, capture

    def __getattr__(self, name):
        held = getattr(self.declared, name)
        if name == "picture":
            return Declared(held, self.capture)
        if name == "capture":
            raise AssertionError(f"a render read the declared capture, {self.capture}")
        return held


@pytest.mark.parametrize("capture", ["fast", "screenshot", "software"])
def test_no_render_reads_the_declared_capture(film_root, monkeypatch, capture):
    import filmkit.film as film

    for module in (picture_rendering, film):
        monkeypatch.setattr(module, "FILM", Declared(FILM, capture))
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    receipt = repository.read(edition.render_receipt)
    # The command is the one every film runs, and neither it nor the receipt names a capture.
    stage, picture = edition.picture_stage, edition.picture
    assert receipt["command"][1:7] == [
        "render",
        str(stage),
        "--output",
        str(picture),
        "--fps",
        "60",
    ]
    assert "capture" not in receipt and "browser" not in receipt
    assert not any("capture" in word or "gpu" in word for word in receipt["command"][7:])
    # Nor does a draft, which is drawn by the same renderer in one process.
    scanned = {"longest_fine_speech": 0.0, "over_limit": [], "limit_seconds": 3.5}
    monkeypatch.setattr(picture_draft.still_scan, "record_draft", lambda *_: scanned)
    picture_draft.render_draft(edition, 60)
    draft = repository.read(edition.draft_receipt)
    assert "capture" not in draft and draft["command"][3:5] == [str(film_root.renderer), "render"]


def test_a_render_without_node_is_refused(monkeypatch):
    monkeypatch.setattr(picture_renderer.shutil, "which", lambda _name: None)
    with pytest.raises(PictureError, match="No node on PATH"):
        picture_renderer.launcher()


def launched(monkeypatch, tmp_path, body):
    """Have renders run a stand-in that runs `body` and reports nothing of its own accord."""
    fake = tmp_path / "stand-in"
    fake.write_text(f"#!{sys.executable}\nimport sys\n{textwrap.dedent(body)}")
    fake.chmod(0o755)
    monkeypatch.setattr(picture_renderer, "launcher", lambda: [str(fake)])


def test_a_render_that_reports_no_drawn_frames_is_refused_after_its_receipt(
    film_root, tmp_path, monkeypatch
):
    edition = Edition("zh")
    film_root.staged(edition)
    launched(monkeypatch, tmp_path, "open(sys.argv[sys.argv.index('--output') + 1], 'w').close()")
    with pytest.raises(PictureError, match="exited 0 and reported no drawn frames"):
        picture_rendering.render_picture(edition, 60)
    receipt = repository.read(edition.render_receipt)
    assert (receipt["exit"], receipt["drawn_sha256"], receipt["spans"]) == (0, None, None)


def test_a_report_left_by_an_earlier_run_is_not_this_runs(film_root, tmp_path, monkeypatch):
    edition = Edition("zh")
    film_root.staged(edition)
    stage = edition.picture_stage
    left = stage.with_name(stage.name + "-spans.json")
    left.write_text(json.dumps({"drawn_sha256": "cd" * 32}))
    launched(monkeypatch, tmp_path, "raise SystemExit(3)")
    with pytest.raises(PictureError, match="did not complete"):
        picture_rendering.render_picture(edition, 60)
    assert repository.read(edition.render_receipt)["drawn_sha256"] is None
    assert not left.exists()


def test_receipt_paths_name_their_place_below_any_checkout_root(tmp_path):
    root = tmp_path / "restored"
    picture = root / "build/artifacts/film/zh/sample-reel-final-picture.mp4"
    elsewhere = "/elsewhere/checkout/build/artifacts/film"
    assert picture_rendering.recorded_at(
        f"{elsewhere}/zh/sample-reel-final-picture.mp4", picture, root
    )
    assert picture_rendering.recorded_at(str(picture), picture, root)
    assert not picture_rendering.recorded_at(
        f"{elsewhere}/en/sample-reel-final-picture.mp4", picture, root
    )
    assert not picture_rendering.recorded_at("sample-reel-final-picture.mp4", picture, root)


def test_the_checks_browser_is_the_supplied_one_unless_another_is_named(film_root, monkeypatch):
    monkeypatch.delenv("FILM_CHROMIUM_PATH", raising=False)
    supplied = "build/runtime/tool-cache/browsers/chrome-headless-shell/mac_arm-152.0.7977.30"
    executable = "chrome-headless-shell-mac-arm64/chrome-headless-shell"
    assert picture_browser.browser_path() == film_root.path / supplied / executable
    monkeypatch.setenv("FILM_CHROMIUM_PATH", "/opt/chromium/chrome")
    assert picture_browser.browser_path() == Path("/opt/chromium/chrome")


def test_the_rendered_picture_meets_the_shared_video_contract(film_root, monkeypatch):
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    cover = {"codec_type": "video", "disposition": {"attached_pic": 1}, "width": 640}
    video = {
        "codec_type": "video",
        "disposition": {"attached_pic": 0},
        "nb_frames": str(DURATION * FPS),
        "avg_frame_rate": "60/1",
        "has_b_frames": 0,
        "width": 3840,
        "height": 2160,
        "duration": f"{DURATION + 1e-7}",
    }
    probed = {"streams": [cover, video], "format": {"duration": f"{DURATION:.6f}"}}
    cadence, keyframes = [], list(range(0, DURATION * FPS, 2 * FPS))

    def video_cadence(*arguments):
        cadence.append(arguments)
        return {"keyframes": keyframes}

    monkeypatch.setattr(media, "probe", lambda _: probed)
    monkeypatch.setattr(media, "video_cadence", video_cadence)
    # The video stream is found by type behind a cover, and durations agree within 1e-6 s.
    assert picture_rendering.validate_picture(edition)["exit"] == 0
    assert cadence == [(edition.picture, DURATION * FPS, FPS)]
    # A keyframe off the two-second grid, or one missing from it, is refused by the grid's name.
    for off in ([*keyframes, 7], keyframes[:-1]):
        keyframes = sorted(off)
        with pytest.raises(PictureError, match="rendered picture's keyframes leave the 2 s grid"):
            picture_rendering.validate_picture(edition)
    keyframes = list(range(0, DURATION * FPS, 2 * FPS))
    frames = str(DURATION * FPS - 1)
    for change in ({"nb_frames": frames}, {"avg_frame_rate": "30/1"}, {"has_b_frames": 2}):
        probed["streams"] = [cover, {**video, **change}]
        with pytest.raises(media.MediaError, match="Video differs"):
            picture_rendering.validate_picture(edition)
