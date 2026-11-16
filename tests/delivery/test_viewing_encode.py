"""The 1080p films' encode: x264 in software, with its keyframes forced on the declared grid."""

import subprocess

import pytest

import filmkit.delivery.packaging as delivery_packaging
from filmkit.production import RENDITIONS, VIEWING
from filmkit.specification import FPS


def test_a_1080p_film_is_encoded_by_x264_on_a_forced_grid_without_videotoolbox():
    for kind in ("1080p-captioned", "1080p-uncaptioned"):
        rendition = RENDITIONS[kind]
        options = [*rendition.decoding, *rendition.video]
        options += delivery_packaging.keyframe_options(rendition)
        assert options[options.index("-c:v:0") + 1] == "libx264"
        assert "-crf:v:0" in options
        interval = str(2 * FPS)
        assert options[-6:] == [
            "-g:v:0",
            interval,
            "-keyint_min:v:0",
            interval,
            "-sc_threshold:v:0",
            "0",
        ]
        assert not [option for option in options if "videotoolbox" in option]
        assert rendition.decoding == ()


def test_a_film_that_copies_its_picture_takes_no_keyframe_option():
    assert delivery_packaging.keyframe_options(RENDITIONS["uhd"]) == ()
    assert delivery_packaging.keyframe_options(RENDITIONS["uhd-uncaptioned"]) == ()


@pytest.mark.ffmpeg
def test_four_seconds_encoded_with_the_1080p_options_hold_keyframes_at_0_and_120_alone(tmp_path):
    film = tmp_path / "viewing.mp4"
    # A picture that changes whole at frame 50, where an encoder left to itself sets a keyframe.
    cut = "drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='gte(n,50)'"
    source = f"color=c=0x0F1519:s=640x360:r={FPS}:d=4,{cut}"
    command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-f", "lavfi"]
    command += ["-i", source, *VIEWING.video, *delivery_packaging.keyframe_options(VIEWING)]
    command += ["-threads:v:0", "2", str(film)]
    subprocess.run(command, check=True, capture_output=True, timeout=110)
    packets = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts,flags"]
        + ["-of", "csv=p=0", str(film)],
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout.decode()
    listed = (line.split(",")[:2] for line in packets.split())
    rows = sorted((int(pts), flags) for pts, flags in listed)
    assert len(rows) == 4 * FPS
    assert [frame for frame, (_, flags) in enumerate(rows) if "K" in flags] == [0, 120]
    size = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height"]
        + ["-of", "csv=p=0", str(film)],
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout.decode()
    assert size.strip() == "1920,1080"
