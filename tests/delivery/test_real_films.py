"""Real films: packaging's finished-film check, the verifier's media check and the derived
picture's own, on what the engine's commands make of a two-second picture at a small frame.

The other tests of these checks read a probe that the test wrote. These run FFmpeg and ExifTool:
a captioned picture encoded as the renderer's are, the picture derived from it, and the four
films packaged from the pair, at a tenth of the delivered frames' sides.
"""

import json
import subprocess
import wave
from dataclasses import replace

import pytest
from PIL import Image

import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.verification as delivery_verification
import filmkit.picture.derivation as derivation
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.delivery.packaging import PackagingError
from filmkit.delivery.verification import VerificationError
from filmkit.media import MediaError
from filmkit.picture.rendering import PictureError

pytestmark = [pytest.mark.ffmpeg, pytest.mark.exiftool]

# Two seconds at the films' rate; the pictures' frame and the viewing films', a tenth of the
# delivered sides; the painted rows, whole 16-row blocks, and the frames without a caption.
SECONDS, SIZE, VIEWING_SIZE = 2, (384, 216), (192, 108)
FRAMES = SECONDS * specification.FPS
ROWS, FREE = (176, 208), [(2, 25), (96, 117)]
GROUND = "0x0F1519"
LABEL = "drawbox=x=20:y=20:w=80:h=20:color=white:t=fill"
CAPTION = "drawbox=x=120:y=186:w=140:h=10:color=white:t=fill:enable='between(n,30,90)'"
CREATED = "2026-11-17T00:00:00+00:00"


# Every FFmpeg run of these tests uses two threads: its decoder and filters by these options
# before the picture, an x264 encode by `-threads` among its own options.
TWO_THREADS = ("-filter_threads", "2", "-filter_complex_threads", "2", "-threads", "2")


def small(rendition):
    """A rendition at the small frame, its scale written for it, on two threads."""
    video = tuple(option.replace("w=1920:h=1080", "w=192:h=108") for option in rendition.video)
    width, height = VIEWING_SIZE if rendition.reencoded else SIZE
    if rendition.reencoded:
        video += ("-threads:v:0", "2")
    return replace(rendition, width=width, height=height, video=video, decoding=TWO_THREADS)


RENDITIONS = {kind: small(rendition) for kind, rendition in production.RENDITIONS.items()}


def ffmpeg(*arguments):
    """Run FFmpeg on two threads: the options given, then the output, its encoder limited too."""
    *options, output = arguments
    command = ["ffmpeg", "-v", "error", "-nostdin", "-y", *TWO_THREADS, *options]
    subprocess.run([*command, "-threads", "2", output], check=True, capture_output=True, timeout=60)


def picture(path, *options):
    """A captioned picture: the ground, a label and a caption, encoded by x264."""
    path.parent.mkdir(parents=True, exist_ok=True)
    source = f"color=c={GROUND}:s={SIZE[0]}x{SIZE[1]}:r={specification.FPS}:d={SECONDS}"
    encoder = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-g", "120"]
    encoder += ["-keyint_min", "120", "-sc_threshold", "0", "-pix_fmt", "yuv420p", *options]
    ffmpeg("-f", "lavfi", "-i", source, "-vf", f"{LABEL},{CAPTION}", *encoder, path)


def stream(path) -> dict:
    """The first video stream of a file as FFprobe reports it."""
    probe = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json"]
    listed = subprocess.run([*probe, str(path)], check=True, capture_output=True, timeout=60)
    return json.loads(listed.stdout)["streams"][0]


@pytest.fixture(scope="module")
def pair(tmp_path_factory):
    """A film root with one edition's packaging inputs, real: the captioned picture, the picture
    derived from it with its receipt, the soundtrack, the chapters, the cover and the timeline,
    which states the films' two seconds. The contract's frame and levels are the small ones while
    the module's tests run."""
    root = tmp_path_factory.mktemp("real-films").resolve()
    edition = production.Edition("zh")
    script = repository.read(edition.script)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(repository, "ROOT", root)
        patch.setattr(derivation, "PICTURE_SIZE", SIZE)
        patch.setattr(derivation, "ENCODER", ("-threads", "2", *derivation.ENCODER))
        for height, level in ((SIZE[1], 52), (VIEWING_SIZE[1], 42)):
            patch.setitem(specification.H264_LEVELS, height, level)
        release = {"title": script["title"], "release": script["release"]}
        repository.write(root / edition.script, release)
        repository.write(edition.timeline, {"duration": SECONDS})
        (root / "VERSION").write_text("1.3.0\n")
        captioned, uncaptioned = edition.rendered(True), edition.rendered(False)
        picture(captioned.file, "-bf", "0")
        made = derivation.derive(
            captioned.file, uncaptioned.file, SIZE, ROWS, FREE, root / "work", edges=(8, 8)
        )
        derived = {"rows": list(ROWS), "ground": made["ground"]}
        repository.write(uncaptioned.receipt, {"picture": "uncaptioned", "derived": derived})
        with wave.open(str(edition.soundtrack), "wb") as sound:
            sound.setnchannels(2)
            sound.setsampwidth(2)
            sound.setframerate(specification.RATE)
            sound.writeframes(b"\0\0\0\0" * SECONDS * specification.RATE)
        step = SECONDS * 1000 // specification.CHAPTERS
        chapters = "".join(
            f"\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={n * step}\nEND={(n + 1) * step}\ntitle={n}\n"
            for n in range(specification.CHAPTERS)
        )
        (edition.artifacts / "chapters.ffmeta").write_text(";FFMETADATA1\n" + chapters)
        cover = Image.new("RGB", (160, 90), (15, 21, 25))
        cover.save(edition.artifacts / delivery_packaging.COVER_JPEG, quality=95)
        yield edition


def packaged(edition, kind, rendition=None):
    """One film as packaging makes it: encoded, finished, checked and linked into place."""
    target = edition.film(kind)
    target.unlink(missing_ok=True)
    rendition = rendition or RENDITIONS[kind]
    package = {"editions": []}
    member = delivery_packaging.package_rendition(edition, package, rendition, target, CREATED)
    return target, member


@pytest.mark.parametrize("kind", list(RENDITIONS))
def test_each_film_of_a_derived_pair_passes_packagings_check_and_the_verifiers(pair, kind):
    rendition = RENDITIONS[kind]
    film, member = packaged(pair, kind)
    # The 1080p uncaptioned film read the captioned picture; every other film its own.
    read = pair.rendered(rendition.captions or rendition.reencoded).file.name
    assert (member["path"], member["source"]) == (film.name, read)
    encode = member["commands"][0]
    assert encode[encode.index("-i") - 6 : encode.index("-i")] == list(TWO_THREADS)
    assert ("-threads:v:0" in encode) is rendition.reencoded
    report = delivery_verification.verify_media(pair, film, rendition)
    assert report["dimensions"] == [rendition.width, rendition.height]
    assert report["video_frames"] == FRAMES
    assert abs(report["audio_sample_frames_decoded"] - SECONDS * specification.RATE) <= 1024
    # No film's picture holds B-frames, whether its stream is a copy or the engine's encode.
    probed = stream(film)
    assert (int(probed["nb_frames"]), probed["has_b_frames"]) == (FRAMES, 0)


def test_the_painted_viewing_film_holds_the_ground_where_the_caption_stood(pair):
    film, _ = packaged(pair, "1080p-uncaptioned")
    shown, _ = packaged(pair, "1080p-captioned")

    def brightest(path):
        crop = ["-vf", "crop=192:8:0:92", "-frames:v", "70", "-f", "rawvideo", "-pix_fmt", "gray"]
        command = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), *crop, "pipe:1"]
        return max(subprocess.run(command, check=True, capture_output=True, timeout=60).stdout)

    assert brightest(shown) > 200 > 40 > brightest(film)


def test_a_film_whose_picture_holds_b_frames_is_refused_by_both_checks(pair):
    viewing = RENDITIONS["1080p-captioned"]
    at = viewing.video.index("-bf:v:0")
    reordering = replace(viewing, video=(*viewing.video[:at], *viewing.video[at + 2 :]))
    work = repository.ROOT / delivery_packaging.WORK / pair.code
    name = pair.film("1080p-captioned").name
    try:
        with pytest.raises(PackagingError, match="differs from the delivery contract"):
            packaged(pair, "1080p-captioned", reordering)
        # Packaging keeps the refused film in its work folder, where the verifier reads it.
        refused = work / "finished" / name
        assert stream(refused)["has_b_frames"] > 0
        with pytest.raises(VerificationError, match=f"delivery contract: {name}: .*: B-frames"):
            delivery_verification.verify_media(pair, refused, viewing)
    finally:
        for left in (work / name, work / "finished" / name):
            left.unlink(missing_ok=True)


def test_the_derived_picture_passes_its_own_media_check_and_others_are_refused(pair):
    derived = pair.rendered(False).file
    derivation.require_derived_media(derived, SECONDS)
    probed = stream(derived)
    assert (probed["nb_frames"], probed["has_b_frames"]) == (str(FRAMES), 0)
    # The same frames with a keyframe every second.
    other = derived.with_name("another-grid.mp4")
    ffmpeg("-i", derived, "-c:v", "libx264", "-g", "60", "-keyint_min", "60", "-bf", "0", other)
    with pytest.raises(PictureError, match="keyframes leave the 2 s grid: another-grid.mp4"):
        derivation.require_derived_media(other, SECONDS)
    # The same frames on the grid, with x264's default B-frames.
    grid = ["-g", "120", "-keyint_min", "120", "-sc_threshold", "0"]
    ffmpeg("-i", derived, "-c:v", "libx264", *grid, other)
    with pytest.raises(MediaError, match="another-grid.mp4: B-frames"):
        derivation.require_derived_media(other, SECONDS)
