"""Qualifying the renderer: a second render of the captioned stage, compared with the first by the
measure of a rendered pair, on small real clips that the stand-in renderer writes."""

import json
import subprocess

import pytest
from test_faults import CAPTION, FRAGMENT, LABEL, SECONDS, encode

import filmkit.picture.qualification as qualification
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition

pytestmark = pytest.mark.ffmpeg

# The canvas version the fixture's film installs, which is the engine's.
RENDERER = picture_renderer.RENDERER_VERSION
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

    return edition, film_root, renders


def test_two_renders_that_show_the_same_pass_and_the_second_is_removed(rendered, capsys):
    edition, film_root, renders = rendered
    renders([CAPTION, LABEL], [CAPTION, LABEL])
    capsys.readouterr()
    record = qualification.qualify_renderer(edition, 60)
    assert repository.read(edition.renderer_qualification) == record
    assert [*record] == [
        "renderer",
        "pinned_build",
        "drawn_alike",
        "stage_sha256",
        "first",
        "second",
        "comparison",
        "identical_frames",
        "first_differing_frame",
        "lowest_psnr_db",
        "lowest_psnr_frame",
        "psnr_unmeasured",
        "findings",
        "verdict",
    ]
    assert (record["verdict"], record["findings"]) == ("pass", [])
    assert (record["identical_frames"], record["first_differing_frame"]) == (FRAMES, None)
    assert (record["lowest_psnr_db"], record["lowest_psnr_frame"]) == (None, None)
    assert record["psnr_unmeasured"] is None
    assert record["renderer"] == film_root.canvas()
    assert (record["renderer"]["version"], record["pinned_build"]) == (RENDERER, True)
    # Both renders state one digest of their drawn frames.
    assert record["drawn_alike"] is True
    first, second = record["first"], record["second"]
    assert first["sha256"] == repository.sha(edition.picture)
    assert (first["frames"], second["frames"]) == (FRAMES, FRAMES)
    assert first["drawn_sha256"] == second["drawn_sha256"] is not None
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
    # It was drawn in another count of spans than the first: one process against four.
    assert again[again.index("--spans") + 1] == "1"
    assert (first["spans"], second["spans"]) == (4, 1)
    # The delivered picture and its receipt are as they were.
    picture_rendering.validate_picture(edition)


def test_the_record_states_the_canvas_that_ran(rendered):
    edition, film_root, renders = rendered
    renders([CAPTION], [CAPTION])
    record = qualification.qualify_renderer(edition, 60)
    assert record["renderer"] == film_root.canvas()
    assert record["renderer"]["binary"]["sha256"] == picture_renderer.BINARY_SHA256
    assert record["renderer"]["text_renderer"] == "system"
    # The canvas's version is the installed package's, read when the qualification runs.
    manifest = film_root.path / "node_modules" / picture_renderer.RENDERER_PACKAGE
    manifest.write_text('{"name": "@napi-rs/canvas", "version": "0.0.1"}')
    runs = len(film_root.runs())
    with pytest.raises(PictureError, match="The film installs @napi-rs/canvas 0.0.1"):
        qualification.qualify_renderer(edition, 60)
    assert len(film_root.runs()) == runs


def test_a_picture_another_canvas_build_drew_is_not_qualified_with_the_one_that_runs(rendered):
    edition, film_root, renders = rendered
    renders([CAPTION], [CAPTION])
    drew = picture_renderer.INTEGRITY[picture_renderer.RENDERER_NAME]
    # The canvas that runs now is another build than the one the picture's receipt names.
    film_root.installs("sha512-another-build")
    runs = len(film_root.runs())
    with pytest.raises(PictureError) as refused:
        qualification.qualify_renderer(edition, 60)
    assert str(refused.value) == (
        f"The zh captioned picture's receipt names @napi-rs/canvas {RENDERER} ({drew}), and the "
        f"canvas the film installs now is @napi-rs/canvas {RENDERER} (sha512-another-build): a "
        "qualification compares two renders by one canvas; render the picture again"
    )
    # Nothing was rendered and no record was written.
    assert len(film_root.runs()) == runs
    assert not edition.renderer_qualification.exists()


def test_a_qualification_by_another_library_than_the_pinned_one_says_so(rendered):
    edition, film_root, renders = rendered
    # Both renders load one library, which is not the one the engine pins: the two are
    # compared and pass, and the record says that the pinned build was not what ran.
    loaded = film_root.loads(sha256="ee" * 32)
    renders([CAPTION], [CAPTION])
    record = qualification.qualify_renderer(edition, 60)
    assert (record["verdict"], record["pinned_build"]) == ("pass", False)
    assert record["renderer"]["binary"]["sha256"] == loaded["sha256"]


def test_two_renders_by_different_libraries_are_not_qualified_as_one(rendered):
    edition, film_root, renders = rendered
    renders([CAPTION], [CAPTION])
    # The second render's processes load another library than the first's did.
    film_root.loads(sha256="ee" * 32)
    runs = len(film_root.runs())
    with pytest.raises(PictureError) as refused:
        qualification.qualify_renderer(edition, 60)
    # The refusal names both builds by what differs between them, and nothing is recorded.
    said = str(refused.value)
    assert f"native library {picture_renderer.BINARY_SHA256} and system text" in said
    assert f"native library {'ee' * 32} and system text" in said
    assert "a qualification compares two renders by one build" in said
    assert len(film_root.runs()) == runs + 1
    assert not edition.renderer_qualification.exists()


def test_a_picture_another_renderer_made_is_refused_before_it_is_rendered_again(rendered):
    edition, film_root, renders = rendered
    renders([CAPTION], [CAPTION])
    receipt = repository.read(edition.rendered(True).receipt)
    assert receipt["renderer"]["version"] == RENDERER
    # The picture's receipt names another version than the engine's, or no canvas at all, as
    # the receipt of a browser's render does.
    other = {**receipt["renderer"], "version": "1.0.0"}
    runs = len(film_root.runs())
    for drawn_by, named in ((other, "@napi-rs/canvas 1.0.0 with system text"), (None, "no native")):
        repository.write(edition.rendered(True).receipt, receipt | {"renderer": drawn_by})
        with pytest.raises(PictureError) as refused:
            qualification.qualify_renderer(edition, 60)
        assert str(refused.value).startswith(f"The picture's receipt names {named}")
        assert f"@napi-rs/canvas {RENDERER} with system text" in str(refused.value)
    assert len(film_root.runs()) == runs
    assert not edition.renderer_qualification.exists()


def test_two_renders_that_drew_other_frames_are_refused(rendered):
    edition, film_root, renders = rendered
    renders([CAPTION], [CAPTION])
    # The second render reports another digest of its drawn frames than the first.
    (film_root.renderer.parent / "drawn").write_text("f" * 64)
    with pytest.raises(PictureError, match="the two renders drew different frames"):
        qualification.qualify_renderer(edition, 60)
    record = repository.read(edition.renderer_qualification)
    assert (record["drawn_alike"], record["verdict"]) == (False, "refuse")
    assert record["second"]["drawn_sha256"] == "f" * 64 != record["first"]["drawn_sha256"]
    # The comparison of the encoded frames found nothing: the digest alone refuses.
    assert len(record["findings"]) == 1
    # The second render is kept beside its receipt for inspection.
    work = repository.ROOT / qualification.WORK / "zh"
    assert (work / edition.picture.name).is_file() and (work / "receipt.json").is_file()


def test_a_failed_pass_over_every_frame_leaves_the_record_of_a_comparison_that_decided(
    rendered, monkeypatch, capsys
):
    edition, film_root, renders = rendered
    renders([CAPTION, LABEL], [CAPTION, LABEL])

    def failed(*_):
        raise subprocess.CalledProcessError(1, ["ffmpeg"], stderr=b"")

    monkeypatch.setattr(qualification.equivalence.media, "frame_psnr", failed)
    capsys.readouterr()
    record = qualification.qualify_renderer(edition, 60)
    assert repository.read(edition.renderer_qualification) == record
    assert (record["verdict"], record["findings"]) == ("pass", [])
    assert record["comparison"]["every_frame"]["frames"] == FRAMES
    assert record["identical_frames"] is None
    assert record["psnr_unmeasured"] == "FFmpeg's PSNR pass exited with 1"
    printed = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert printed["identical_frames"] is None and printed["verdict"] == "pass"


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
