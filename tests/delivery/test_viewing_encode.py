"""The 1080p films' encode: x264 in software, with its keyframes forced on the declared grid."""

import subprocess

import pytest

import filmkit.delivery.packaging as delivery_packaging
import filmkit.picture.derivation as derivation
import filmkit.production as production
import filmkit.repository as repository
from filmkit.production import RENDITIONS, VIEWING, Edition
from filmkit.specification import FPS


def test_a_1080p_film_is_encoded_by_x264_on_a_forced_grid_without_videotoolbox():
    for kind in ("1080p-captioned", "1080p-uncaptioned"):
        rendition = RENDITIONS[kind]
        options = [*rendition.decoding, *rendition.video]
        options += delivery_packaging.keyframe_options(rendition)
        assert options[options.index("-c:v:0") + 1] == "libx264"
        assert options[options.index("-preset:v:0") + 1] == "veryfast"
        assert options[options.index("-crf:v:0") + 1] == "10"
        assert options[options.index("-bf:v:0") + 1] == "0"
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


def test_the_1080p_settings_are_the_measured_constants():
    assert (production.VIEWING_ENCODER, production.VIEWING_PRESET) == ("libx264", "veryfast")
    assert production.VIEWING_RATE_FACTOR == 10


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


def test_each_film_reads_its_own_picture_unless_the_pair_is_derived(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    edition = Edition("zh")
    captioned, uncaptioned = edition.rendered(True), edition.rendered(False)
    # Without a receipt, and with a render's receipt, every film reads its own picture.
    for kind, rendition in RENDITIONS.items():
        own = edition.rendered(rendition.captions).file
        assert derivation.film_source(edition, rendition) == (own, "0:v:0", rendition.video), kind
    repository.write(uncaptioned.receipt, {"picture": "uncaptioned", "command": ["hyperframes"]})
    viewing = RENDITIONS["1080p-uncaptioned"]
    assert derivation.film_source(edition, viewing) == (uncaptioned.file, "0:v:0", viewing.video)
    # Of a derived pair, the 1080p uncaptioned film is painted and scaled from the captioned one.
    derived = {"rows": [1872, 2048], "ground": {"y": 21, "u": 129, "v": 125}}
    repository.write(uncaptioned.receipt, {"picture": "uncaptioned", "derived": derived})
    source, mapped, video = derivation.film_source(edition, viewing)
    assert (source, mapped) == (captioned.file, "[viewing]")
    assert video[0] == "-filter_complex"
    assert video[1] == (
        "[0:v:0]split=2[main][strip];"
        "[strip]crop=3840:176:0:1872,lutyuv=y=21:u=129:v=125[paint];"
        "[main][paint]overlay=x=0:y=1872:format=yuv420[painted];"
        "[painted]scale=w=1920:h=1080:flags=area[viewing]"
    )
    assert video[2:] == viewing.video[2:]
    # The UHD uncaptioned film copies the derived picture, and the captioned films their own.
    master = RENDITIONS["uhd-uncaptioned"]
    assert derivation.film_source(edition, master) == (uncaptioned.file, "0:v:0", master.video)
    shown = RENDITIONS["1080p-captioned"]
    assert derivation.film_source(edition, shown) == (captioned.file, "0:v:0", shown.video)


@pytest.mark.ffmpeg
def test_a_painted_and_scaled_film_holds_the_ground_where_the_caption_stood(tmp_path):
    source, film = tmp_path / "captioned.mp4", tmp_path / "viewing.mp4"
    caption = "drawbox=x=100:y=152:w=120:h=8:color=white:t=fill"
    picture = f"color=c=0x0F1519:s=320x180:r={FPS}:d=1,{caption}"
    command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-f", "lavfi"]
    command += ["-i", picture, "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(source)]
    subprocess.run(command, check=True, capture_output=True, timeout=60)
    ground = {"y": 33, "u": 130, "v": 126}
    paint = derivation.painted("0:v:0", (320, 180), (144, 176), ground, "painted")
    graph = f"{paint};[painted]scale=w=160:h=90:flags=area[viewing]"
    command = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "2", "-i", str(source)]
    command += ["-filter_complex", graph, "-map", "[viewing]", "-c:v", "libx264", "-qp", "0"]
    command += ["-pix_fmt", "yuv420p", "-threads", "2", str(film)]
    subprocess.run(command, check=True, capture_output=True, timeout=60)
    raw = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(film), "-vf", "crop=160:16:0:72"]
    raw += ["-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv420p", "pipe:1"]
    band = subprocess.run(raw, check=True, capture_output=True, timeout=60).stdout
    luma = 160 * 16
    assert (set(band[:luma]), set(band[luma : luma * 5 // 4])) == ({33}, {130})
