"""Deriving a picture: the band's rows painted in the ground the source holds, the band measured in
the same decode, and a band that is not the ground refused."""

import subprocess

import numpy as np
import pytest

import filmkit.picture.derivation as derivation
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError

# The test pictures: two seconds at 60 fps of 320x180 frames with the caption band in rows 144-175.
SIZE, ROWS, FRAMES = (320, 180), (144, 176), 120
GROUND = "0x0F1519"
# A label that stays high in the frame, and a caption drawn in the band on frames 30 to 90.
LABEL = "drawbox=x=20:y=20:w=80:h=20:color=white:t=fill"
CAPTION = "drawbox=x=100:y=152:w=120:h=8:color=white:t=fill:enable='between(n,30,90)'"
# The frames without a caption that the ground check reads.
FREE = [(2, 25), (96, 117)]


def encode(path, *boxes):
    """A picture of the ground with the given boxes drawn on it, encoded as the pictures are."""
    path.parent.mkdir(parents=True, exist_ok=True)
    picture = f"color=c={GROUND}:s={SIZE[0]}x{SIZE[1]}:r=60:d=2"
    command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-f", "lavfi"]
    command += ["-i", picture, "-vf", ",".join(boxes), "-c:v", "libx264", "-preset", "veryfast"]
    command += ["-crf", "14", "-pix_fmt", "yuv420p", "-threads", "2", str(path)]
    subprocess.run(command, check=True, capture_output=True, timeout=60)


def band(path, rows=ROWS):
    """Every frame's samples of the rows of a picture, as frames of raw 4:2:0 samples."""
    crop = f"crop={SIZE[0]}:{rows[1] - rows[0]}:0:{rows[0]}"
    command = ["ffmpeg", "-v", "error", "-nostdin", "-threads", "2", "-i", str(path), "-vf", crop]
    command += ["-f", "rawvideo", "-pix_fmt", "yuv420p", "pipe:1"]
    data = subprocess.run(command, check=True, capture_output=True, timeout=60).stdout
    return np.frombuffer(data, dtype=np.uint8).reshape(-1, SIZE[0] * (rows[1] - rows[0]) * 3 // 2)


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A film root for the work of a derivation, whose encodes use two threads."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.setattr(derivation, "ENCODER", ("-threads", "2", *derivation.ENCODER))
    return tmp_path.resolve()


def test_the_frames_checked_leave_out_the_edges_of_each_stretch():
    stretches = [[0.0, 29 / 30], [2.0, 2.1], [3.0, 3.1 + 1 / 30], [5.0, 5.0]]
    assert derivation.free_frames(stretches) == [(4, 54), (184, 184)]
    assert derivation.EDGE_FRAMES == 4


def test_the_selection_is_true_inside_each_run_of_frames():
    assert derivation.selection([(2, 25)]) == "between(n,2,25)"
    assert derivation.selection([(2, 25), (96, 117), (130, 131)]) == (
        "((between(n,2,25)+between(n,96,117))+between(n,130,131))"
    )


@pytest.mark.ffmpeg
def test_a_derived_picture_holds_the_ground_in_its_band_and_every_frame(root):
    source, target = root / "captioned.mp4", root / "artifacts/uncaptioned.mp4"
    encode(source, LABEL, CAPTION)
    assert band(source).max() > 200
    made = derivation.derive(source, target, SIZE, ROWS, FREE, root / "work")
    ground = made["ground"]
    assert sorted(ground) == ["u", "v", "y"]
    check = made["check"]
    assert (check["frames"], check["verdict"]) == (46, "pass")
    assert check["largest_departure"] <= 1
    samples = band(target)
    luma = SIZE[0] * (ROWS[1] - ROWS[0])
    assert samples.shape[0] == FRAMES
    assert np.abs(samples[:, :luma].astype(int) - ground["y"]).max() <= 1
    assert np.abs(samples[:, luma : luma * 5 // 4].astype(int) - ground["u"]).max() <= 1
    # The label above the band is still there, and the work holds no picture or measure.
    assert band(target, (20, 40)).max() > 200
    assert not (root / "work/derived.mp4").exists() and not (root / "work/band-stats.txt").exists()
    command = made["command"]
    assert command[command.index("-g") + 1] == command[command.index("-keyint_min") + 1] == "120"
    assert command[command.index("-sc_threshold") + 1] == "0"
    assert "lutyuv=y={y}:u={u}:v={v}".format(**ground) in command[command.index("-i") + 3]


@pytest.mark.ffmpeg
def test_a_band_that_is_not_the_ground_at_a_frame_without_a_caption_is_refused(root):
    source, target = root / "captioned.mp4", root / "uncaptioned.mp4"
    encode(source, LABEL, CAPTION)
    # The frames named as free of captions include some that show one.
    with pytest.raises(PictureError, match=r"not the ground at frame (2[6-9]|30)"):
        derivation.derive(source, target, SIZE, ROWS, [(2, 40)], root / "work")
    assert not target.exists()
    assert not (root / "work/derived.mp4").exists()


@pytest.mark.ffmpeg
def test_a_failed_read_or_encode_is_refused_with_ffmpegs_message(root, monkeypatch):
    source = root / "captioned.mp4"
    encode(source, LABEL)
    with pytest.raises(PictureError, match="Reading the band of frame 2 failed"):
        derivation.derive(source, root / "out.mp4", SIZE, (144, 400), FREE, root / "work")
    monkeypatch.setattr(derivation, "ENCODER", ("-c:v", "no-such-encoder"))
    with pytest.raises(PictureError, match="encode failed: .*no-such-encoder"):
        derivation.derive(source, root / "out.mp4", SIZE, ROWS, FREE, root / "work")
    assert not (root / "out.mp4").exists()
    assert not (root / "work/derived.mp4").exists()


def measured(frames, ground=(21, 129, 125), fps=60):
    """The band's measures as the encode writes them, each frame at the ground."""
    planes = "".join(
        f"lavfi.signalstats.{plane}{end}={value}\n"
        for plane, value in zip("YUV", ground, strict=True)
        for end in ("MIN", "MAX")
    )
    return "".join(
        f"frame:{count}    pts:{frame * 256}   pts_time:{frame / fps:.6f}\n{planes}"
        "lavfi.signalstats.YAVG=21\nlavfi.signalstats.SATMAX=4\n"
        for count, frame in enumerate(frames)
    )


def test_the_ground_check_reads_every_frame_and_the_largest_departure(tmp_path):
    ground = {"y": 21, "u": 129, "v": 125}
    stats = tmp_path / "stats.txt"
    stats.write_text(measured(range(2, 6)).replace("UMAX=129", "UMAX=132", 1))
    assert derivation.ground_check(stats, [(2, 5)], ground) == {
        "frames": 4,
        "largest_departure": 3,
        "verdict": "pass",
    }
    stats.write_text(measured(range(2, 6)).replace("YMAX=21", "YMAX=235", 1))
    with pytest.raises(PictureError, match="frame 2, a frame without a caption: .* 214 levels"):
        derivation.ground_check(stats, [(2, 5)], ground)
    stats.write_text(measured(range(2, 5)))
    with pytest.raises(PictureError, match="measured at 3 of its 4 frames"):
        derivation.ground_check(stats, [(2, 5)], ground)
    stats.write_text(measured([2, 3, 4, 9]))
    with pytest.raises(PictureError, match="frame 5 is not readable"):
        derivation.ground_check(stats, [(2, 5)], ground)
