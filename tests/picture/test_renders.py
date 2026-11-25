"""Two renders of one stage, compared by the measure of a rendered pair with no row left out:
what `qualify-renderer` judges, on small real clips."""

import contextlib
import math
import subprocess

import pytest
from test_faults import BROKEN, CAPTION, FRAGMENT, LABEL, SECONDS, SIZE, encode

import filmkit.media as media
import filmkit.picture.equivalence as equivalence
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError

pytestmark = pytest.mark.ffmpeg

FRAMES = SECONDS * 60
# A stage whose every sample changes a little from frame to frame, so that a lossy encode of it
# differs from a lossless one in every frame, by the encoder's noise alone.
MOVING = f"gradients=s={SIZE[0]}x{SIZE[1]}:r=60:d={SECONDS}:seed=7:speed=0.05"
MOVING += ":c0=0x1A2228:c1=0x2C3A44"


def encoded(path, *options):
    """The moving stage, encoded by x264 with the options given."""
    command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-f", "lavfi"]
    command += ["-i", MOVING, "-c:v", "libx264", *options, "-pix_fmt", "yuv420p", "-threads", "2"]
    subprocess.run([*command, str(path)], check=True, capture_output=True, timeout=60)


@pytest.fixture
def renders(tmp_path, monkeypatch):
    """Two picture files below a root of their own, and the comparison's work folder."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return tmp_path / "first.mp4", tmp_path / "second.mp4", tmp_path / "work"


def test_two_renders_that_decode_alike_pass_and_the_report_holds_the_comparison(renders):
    first, second, work = renders
    encode(first, CAPTION, LABEL)
    encode(second, CAPTION, LABEL)
    compared = equivalence.compare_renders(first, second, work)
    assert [*compared] == [
        "frames",
        "comparison",
        "identical_frames",
        "first_differing_frame",
        "lowest_psnr_db",
        "lowest_psnr_frame",
        "psnr_unmeasured",
        "findings",
        "verdict",
    ]
    assert compared["frames"] == {"first": FRAMES, "second": FRAMES}
    assert (compared["verdict"], compared["findings"]) == ("pass", [])
    assert (compared["identical_frames"], compared["first_differing_frame"]) == (FRAMES, None)
    # No frame differs, so no frame has a PSNR.
    assert (compared["lowest_psnr_db"], compared["lowest_psnr_frame"]) == (None, None)
    comparison = compared["comparison"]
    # The comparison of a rendered pair, at the sampled frames and at every frame, with no row
    # left out and the pair's own thresholds.
    assert (comparison["frames"], comparison["excluded_rows"]) == (4, [0, 0])
    assert comparison["psnr_floor_db"] == equivalence.PSNR_FLOOR_DB
    assert (comparison["lowest_psnr_db"], comparison["failing_frames"]) == (None, 0)
    every = comparison["every_frame"]
    assert (every["frames"], every["differing_frames"], every["fault_frames"]) == (FRAMES, 0, 0)
    assert (every["lasting_runs"], every["residue_frames"], every["band_changes"]) == (0, 0, {})
    assert every["slivers"]["frames_beyond_the_bound"] == 0


def test_renders_that_differ_by_the_encoders_noise_in_every_frame_pass(renders):
    first, second, work = renders
    encoded(first, "-qp", "0")
    encoded(second, "-preset", "veryfast", "-crf", "20", "-bf", "0")
    compared = equivalence.compare_renders(first, second, work)
    # No frame decodes identically, and nothing differs beyond the encoders' noise.
    assert (compared["identical_frames"], compared["first_differing_frame"]) == (0, 0)
    assert (compared["verdict"], compared["findings"]) == ("pass", [])
    # The lowest PSNR is that of every frame's pass, and the frame it names is one of them.
    every = media.frame_psnr(first, second, 60)
    assert len(every) == FRAMES
    assert compared["lowest_psnr_db"] == min(every)
    assert every[compared["lowest_psnr_frame"]] == min(every)
    assert 30 < compared["lowest_psnr_db"] < 80
    comparison = compared["comparison"]
    assert comparison["identical_frames"] == 0
    assert comparison["lowest_psnr_db"] >= equivalence.PSNR_FLOOR_DB
    assert 0 < comparison["largest_tile"] <= equivalence.TILE_LIMIT
    assert comparison["every_frame"]["differing_frames"] == 0


def test_a_one_frame_fault_of_one_render_refuses_naming_the_frame_and_the_render(renders):
    first, second, work = renders
    # A glyph fragment above the caption in the second render, and a broken caption in the first:
    # no row is left out, so the caption is compared as the rest is.
    encode(first, CAPTION, BROKEN)
    encode(second, CAPTION, FRAGMENT)
    compared = equivalence.compare_renders(first, second, work)
    assert compared["verdict"] == "refuse"
    assert compared["findings"] == [
        "encoded frame 50 at 0.833 s: the first picture holds a one-frame fault of 150 levels in "
        "box [40, 44, 44, 48]",
        "encoded frame 77 at 1.283 s: the second picture holds a one-frame fault of 150 levels "
        "in box [40, 10, 44, 14]",
    ]
    assert compared["comparison"]["every_frame"]["fault_frames"] == 2
    # All but those two frames decode identically; that count decides nothing. The lowest PSNR
    # is one of the two frames', which the sampled frames, every half second, do not hold.
    assert (compared["identical_frames"], compared["first_differing_frame"]) == (FRAMES - 2, 50)
    assert compared["lowest_psnr_frame"] in (50, 77)
    assert compared["lowest_psnr_db"] < 60
    assert compared["comparison"]["lowest_psnr_db"] is None


def test_a_difference_that_lasts_refuses(renders):
    first, second, work = renders
    encode(first, CAPTION, LABEL)
    encode(second, CAPTION)
    compared = equivalence.compare_renders(first, second, work)
    assert compared["verdict"] == "refuse"
    findings = compared["findings"]
    # The label stands from 0.5 s to 1 s in one render alone: two sampled frames and a run.
    assert findings[0].startswith("encoded frame 30: tile difference ")
    assert findings[-1] == (
        "encoded frames 30-60: the pictures differ by more than 90 levels in box [8, 0, 32, 16]"
    )
    assert not [finding for finding in findings if "caption band" in finding]
    assert compared["comparison"]["every_frame"]["lasting_runs"] == 1


def test_renders_of_other_lengths_refuse_without_a_comparison(renders, monkeypatch):
    first, second, work = renders
    encode(first, CAPTION)
    monkeypatch.setattr("test_faults.SECONDS", 1)
    encode(second, CAPTION)
    compared = equivalence.compare_renders(first, second, work)
    assert compared == {
        "frames": {"first": FRAMES, "second": FRAMES // 2},
        "comparison": None,
        "identical_frames": None,
        "first_differing_frame": None,
        "lowest_psnr_db": None,
        "lowest_psnr_frame": None,
        "psnr_unmeasured": None,
        "findings": [f"the renders hold {FRAMES} and {FRAMES // 2} frames"],
        "verdict": "refuse",
    }


def test_one_pass_measures_every_frames_psnr_which_is_infinite_where_two_frames_are_equal(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    clips = []
    for name, colour in (("a", "0x0F1519"), ("b", "0x0F1519"), ("c", "0x101519")):
        clip = tmp_path / f"{name}.mp4"
        command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-f", "lavfi"]
        command += ["-i", f"color=c={colour}:s=64x36:r=60:d=0.5", "-c:v", "libx264", "-qp", "0"]
        subprocess.run([*command, "-pix_fmt", "yuv420p", str(clip)], check=True, timeout=60)
        clips.append(clip)
    same, other = (media.frame_psnr(clips[0], clip, 60) for clip in clips[1:])
    assert same == [math.inf] * 30
    # One level of one channel in every sample of a plane is far from equal, and is measured.
    assert len(other) == 30 and all(40 < value < 70 for value in other)


def failing(error):
    def pass_(*_):
        raise error

    return pass_


@pytest.mark.parametrize(
    ("measure", "why"),
    [
        (
            lambda *_: [math.inf] * (FRAMES - 1),
            f"the PSNR of {FRAMES - 1} of the renders' {FRAMES} frames was measured",
        ),
        (
            failing(subprocess.CalledProcessError(187, ["ffmpeg"], stderr=b"no such filter\n")),
            "FFmpeg's PSNR pass exited with 187: no such filter",
        ),
        (
            failing(subprocess.TimeoutExpired(["ffmpeg"], 7200)),
            f"FFmpeg's PSNR pass did not end within {equivalence.DECODE_DEADLINE} s",
        ),
    ],
)
def test_a_pass_that_fails_decides_nothing_and_is_recorded_as_a_missing_fact(
    renders, monkeypatch, measure, why
):
    first, second, work = renders
    encode(first, CAPTION)
    encode(second, CAPTION)
    monkeypatch.setattr(media, "frame_psnr", measure)
    compared = equivalence.compare_renders(first, second, work)
    # The comparison had decided: its report and verdict stand, and the facts are missing.
    assert (compared["verdict"], compared["findings"]) == ("pass", [])
    assert compared["comparison"]["every_frame"]["frames"] == FRAMES
    assert [compared[key] for key in equivalence.DECODED] == [None] * 4
    assert compared["psnr_unmeasured"] == why


def test_a_file_whose_container_states_no_count_of_frames_is_refused_in_words(renders, monkeypatch):
    first, second, work = renders
    encode(first, CAPTION)
    encode(second, CAPTION)
    stream = media.video_stream

    def without_a_count(probe):
        return {key: value for key, value in stream(probe).items() if key != "nb_frames"}

    monkeypatch.setattr(media, "video_stream", without_a_count)
    refusal = f"{first.name} states no count of frames in its container \\(None\\)"
    with pytest.raises(PictureError, match=refusal):
        equivalence.compare_renders(first, second, work)


def test_the_comparison_names_its_pass_over_every_frame_as_a_phase(renders, monkeypatch):
    first, second, work = renders
    encode(first, CAPTION)
    encode(second, CAPTION)
    phases = []

    @contextlib.contextmanager
    def phase(name):
        phases.append(name)
        yield

    monkeypatch.setattr(equivalence.seam, "phase", phase)
    equivalence.compare_renders(first, second, work)
    assert phases == ["sampled-frames", "every-frame-scan", "every-frame-psnr"]
    # Nothing hashes every frame of each render any more.
    assert not hasattr(equivalence, "frame_digests")
