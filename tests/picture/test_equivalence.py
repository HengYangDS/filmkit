"""The equivalence gate: an edition's uncaptioned picture differs from its captioned one only by its
captions, at the composition and in the encoded pictures."""

import json
import subprocess

import numpy as np
import pytest

import filmkit.picture.equivalence as equivalence
import filmkit.repository as repository
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError
from filmkit.production import Edition

# The test pictures: two seconds at 60 fps of 96x54 frames, the composition's frame scaled by 1/20.
SIZE, SECONDS = (96, 54), 2
GROUND = "0x0F1519"
# A caption drawn from 0.5 s to 1 s in the bottom rows, and a label beside it high in the frame.
CAPTION = "drawbox=x=30:y=44:w=36:h=6:color=white:t=fill:enable='between(t,0.5,1)'"
LABEL = "drawbox=x=8:y=6:w=24:h=8:color=white:t=fill:enable='between(t,0.5,1)'"
# The band the composition's caption paints cover, in rows of the 1080-row frame.
BAND = {"left": 600, "top": 880, "right": 1320, "bottom": 1000}
CUES = [{"start": 0.5, "end": 1.0, "text": "One."}]


def encode(path, *boxes, seconds=SECONDS):
    """A lossless picture of the ground with the given boxes drawn on it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    picture = f"color=c={GROUND}:s={SIZE[0]}x{SIZE[1]}:r=60:d={seconds}"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "lavfi", "-i", picture]
        + (["-vf", ",".join(boxes)] if boxes else [])
        + ["-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(path)],
        check=True,
        capture_output=True,
        timeout=60,
    )


def composition_report(differing=0):
    """The caption-equivalence tool's report, with as many differing instants as named."""
    findings = [
        {"time": 1.5, "captioned": {"kind": "fill", "scene": None}, "uncaptioned": None}
    ] * differing
    return {
        "format": "caption-equivalence",
        "instants": 7,
        "cues": 1,
        "cues_shown_at_their_middle": 1,
        "caption_paints": 3,
        "band": BAND,
        "differing_instants": differing,
        "findings": findings,
        "verdict": "differs" if differing else "equivalent",
    }


@pytest.fixture
def pictures(tmp_path, monkeypatch):
    """The Chinese edition's two rendered pictures, valid, and their timeline and composition."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.setattr(equivalence, "PICTURE_SIZE", SIZE)
    monkeypatch.setattr(equivalence, "DURATION", SECONDS)
    monkeypatch.setattr(equivalence, "validate_picture", lambda _edition, captions: {})
    edition = Edition("zh")
    repository.write(edition.timeline, {"duration": SECONDS, "captions": CUES})
    (tmp_path / COMPOSITION_SCRIPT).parent.mkdir(parents=True)
    (tmp_path / COMPOSITION_SCRIPT).write_text("/* film */")
    for captions in (True, False):
        rendered = edition.rendered(captions)
        rendered.stage.mkdir(parents=True)
        (rendered.stage / "index.html").write_text(f"<html>{rendered.name}</html>")
        repository.write(rendered.receipt, {"picture": rendered.name})
    encode(edition.rendered(True).file, CAPTION)
    encode(edition.rendered(False).file)
    reports = []

    def run(tool, arguments, *, stdout, environment=None):
        reports.append((tool, arguments))
        repository.write(stdout, composition_report(run.differing))
        return 0

    run.differing = 0
    monkeypatch.setattr(equivalence.tools, "run", run)
    return edition, run, reports


def test_the_sampled_frames_are_every_half_second_and_each_cue_s_start_middle_and_end(
    monkeypatch,
):
    monkeypatch.setattr(equivalence, "DURATION", SECONDS)
    timeline = {"captions": [{"start": 0.51, "end": 1.0}, {"start": 1.9, "end": 2.5}]}
    # A cue's instants fall on the frames that show them, and none past the last frame.
    assert equivalence.sampled_frames(timeline) == [0, 30, 45, 60, 90, 114, 119]


def test_the_caption_band_is_widened_and_aligned_to_the_encoder_s_blocks():
    assert equivalence.excluded_rows({"top": 971, "bottom": 1008}, 2160) == (1888, 2064)
    assert equivalence.excluded_rows({"top": 10, "bottom": 1079}, 2160) == (0, 2160)
    assert equivalence.excluded_rows(None, 2160) == (0, 0)


def test_the_selection_stays_shallow_for_any_number_of_frames():
    expression = equivalence.selection([0, 1, 30, 31, 45])
    assert expression == "((not(mod(n,30))+eq(n,1))+(eq(n,31)+eq(n,45)))"
    deep = equivalence.selection(list(range(0, 90000, 7)))
    assert deep.count("eq(") == len([f for f in range(0, 90000, 7) if f % 30])
    assert max(len(part) for part in deep.split("+")) < 200


def test_the_measures_name_tiles_that_differ_and_the_psnr_of_the_rest():
    size, rows = (96, 54), (40, 54)
    ground = np.full(96 * 54 * 3 // 2, 20, dtype=np.uint8)
    same = equivalence.frame_measures(ground, ground.copy(), size, rows)
    assert same == {"largest_tile": 0.0, "psnr_db": None, "largest_sample": 0}
    assert not equivalence.differs(same)
    changed = ground.copy().reshape(-1)
    luma = changed[: 96 * 54].reshape(54, 96)
    luma[45:50, 10:20] = 255
    # Inside the excluded rows a difference counts for nothing.
    assert equivalence.frame_measures(ground, changed, size, rows)["largest_sample"] == 0
    luma[2:4, 2:4] = 120
    measured = equivalence.frame_measures(ground, changed, size, rows)
    assert measured["largest_sample"] == 100
    assert measured["largest_tile"] == pytest.approx(100 * 4 / 4)
    # A whole frame two levels lighter is under the PSNR floor, though no tile reaches its limit;
    # one level lighter lies within the encoders' noise.
    shifted = equivalence.frame_measures(ground, ground + 2, size, (0, 0))
    assert shifted["psnr_db"] == pytest.approx(42.11, abs=0.01)
    assert shifted["largest_tile"] == 2.0
    assert equivalence.differs(shifted)
    lighter = equivalence.frame_measures(ground, ground + 1, size, (0, 0))
    assert lighter["psnr_db"] == pytest.approx(48.13, abs=0.01)
    assert not equivalence.differs(lighter)
    # A tile at the edge holds the pixels that are left.
    assert equivalence.largest_tile(np.ones((5, 7)), 4) == 1.0


def test_keyframe_noise_passes_while_a_shift_or_a_missing_label_fails():
    # At 1080p, outside a caption band of rows 880-1000, as the films compare their pictures.
    size, rows = (1920, 1080), (880, 1000)
    samples = size[0] * size[1] * 3 // 2
    ground = np.full(samples, 30, dtype=np.uint8)
    # A keyframe's noise spreads thinly over the frame: 7.5% of the samples 3 levels off and a few
    # 47 off, as the ETHOS film's frame 50580 measured 49.76 dB with its largest tile 1.847.
    rng = np.random.default_rng(50580)
    noise = np.where(rng.random(samples) < 0.075, rng.choice([-3, 3], size=samples), 0)
    noise[rng.choice(samples, 40, replace=False)] = 47
    keyframe = (ground + noise).clip(0, 255).astype(np.uint8)
    measured = equivalence.frame_measures(ground, keyframe, size, rows)
    assert 49.5 < measured["psnr_db"] < 50.0
    assert measured["largest_tile"] < 2 and measured["largest_sample"] == 47
    assert not equivalence.differs(measured)
    # A uniform shift of two levels fails on the PSNR floor alone.
    shifted = equivalence.frame_measures(ground, ground + 2, size, rows)
    assert shifted["psnr_db"] == pytest.approx(42.11, abs=0.01)
    assert shifted["largest_tile"] < equivalence.TILE_LIMIT and equivalence.differs(shifted)
    # A label missing outside the captions fails on its tile, whatever the PSNR of the frame.
    missing = ground.copy()
    missing[: size[0] * size[1]].reshape(size[1], size[0])[200:212, 400:424] = 90
    label = equivalence.frame_measures(ground, missing, size, rows)
    assert label["largest_tile"] > equivalence.TILE_LIMIT
    assert label["psnr_db"] > equivalence.PSNR_FLOOR_DB and equivalence.differs(label)


@pytest.mark.ffmpeg
def test_pictures_that_differ_only_in_the_caption_band_pass_and_bind_both(pictures):
    edition, _, reports = pictures
    record = equivalence.compare_pictures(edition)
    assert reports == [("caption-equivalence", [str(edition.timeline), "0.5"])]
    assert record["verdict"] == "pass" and record["findings"] == []
    assert record["pictures"]["uncaptioned"]["picture_sha256"] == repository.sha(
        edition.rendered(False).file
    )
    encoded = record["encoded"]
    assert (encoded["frames"], encoded["excluded_rows"]) == (5, [32, 54])
    assert encoded["identical_frames"] == 5
    assert encoded["largest_tile"] == 0.0
    composition = record["composition"]
    assert (composition["instants"], composition["band"]) == (7, BAND)
    assert repository.read(edition.caption_equivalence) == record
    assert equivalence.require_equivalence(edition) == record


@pytest.mark.ffmpeg
def test_an_uncaptioned_picture_that_differs_outside_the_captions_is_refused(pictures):
    edition, _, _ = pictures
    encode(edition.rendered(False).file, LABEL)
    with pytest.raises(PictureError, match="differ beyond their captions: encoded frame 30"):
        equivalence.compare_pictures(edition)
    record = repository.read(edition.caption_equivalence)
    assert record["verdict"] == "refuse"
    assert record["encoded"]["failing_frames"] == 3
    assert [row["frame"] for row in record["encoded"]["failing"]] == [30, 45, 60]
    with pytest.raises(PictureError, match="did not pass; run compare-pictures"):
        equivalence.require_equivalence(edition)


@pytest.mark.ffmpeg
def test_a_composition_that_paints_more_from_its_captions_is_refused_before_decoding(pictures):
    edition, run, _ = pictures
    run.differing = 2
    edition.rendered(False).file.write_bytes(b"not decoded")
    with pytest.raises(PictureError) as refused:
        equivalence.compare_pictures(edition)
    assert "composition at 1.500 s: the captioned frame paints" in str(refused.value)
    assert "composition: 0 more" not in str(refused.value)
    record = repository.read(edition.caption_equivalence)
    assert record["encoded"] == {"not_compared": "the compositions differ beyond their captions"}
    assert len(record["findings"]) == 2


@pytest.mark.ffmpeg
def test_a_picture_short_of_the_sampled_frames_is_refused(pictures):
    edition, _, _ = pictures
    encode(edition.rendered(False).file, seconds=1)
    with pytest.raises(PictureError, match=r"gave 3 of their 5 sampled frames"):
        equivalence.compare_pictures(edition)


@pytest.mark.ffmpeg
def test_packaging_needs_a_record_of_the_current_pictures(pictures):
    edition, _, _ = pictures
    with pytest.raises(PictureError, match="no equivalence record; run compare-pictures"):
        equivalence.require_equivalence(edition)
    equivalence.compare_pictures(edition)
    encode(edition.rendered(False).file, CAPTION)
    with pytest.raises(PictureError, match="binds another pictures; run compare-pictures"):
        equivalence.require_equivalence(edition)
    record = json.loads(edition.caption_equivalence.read_text())
    assert record["verdict"] == "pass"
