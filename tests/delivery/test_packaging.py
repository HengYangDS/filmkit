"""The packaged films: their encodes, the finished-film checks and the package records."""

import json
import subprocess
from pathlib import Path

import pytest

import filmkit.delivery.packaging as delivery_packaging
import filmkit.media as media
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.delivery.packaging import PackagingError
from filmkit.picture.rendering import PictureError


def probe(
    *,
    frames=specification.DURATION * specification.FPS,
    author=specification.AUTHOR,
    sound="audio",
    kind="uhd",
    changes=None,
    chapters="zho",
):
    """A probe of a finished film, as FFprobe reports one that meets the delivery contract.

    Its tags are the zh edition's release tags for the rendition of the given kind, and
    `changes` replaces or, with None, removes some of them; its chapter track's language is
    `chapters`.
    """
    edition = production.Edition("zh")
    rendition = production.RENDITIONS[kind]
    duration = f"{specification.DURATION:.6f}"
    tags = {**delivery_packaging.delivered_tags(edition, rendition)}
    tags["com.apple.quicktime.author"] = author
    for key, value in (changes or {}).items():
        if value is None:
            tags.pop(key, None)
        else:
            tags[key] = value
    names = delivery_packaging.track_names(edition)
    return {
        "streams": [
            {
                "codec_type": "video",
                "nb_frames": str(frames),
                "avg_frame_rate": "60/1",
                "tags": {"language": "zho", "handler_name": names["picture"]},
            },
            {
                "codec_type": sound,
                "duration": duration,
                "tags": {"language": "zho", "handler_name": names["narration"]},
            },
            {"codec_type": "data", "tags": {"language": chapters, "handler_name": "Chapters"}},
            {"codec_type": "video", "disposition": {"attached_pic": 1}},
        ],
        "format": {"duration": duration, "tags": {k: v for k, v in tags.items() if v}},
    }


@pytest.fixture
def packaging_root(tmp_path, monkeypatch):
    """A root holding one edition's packaging inputs, with FFmpeg and ExifTool simulated."""
    edition = production.Edition("zh")
    script = repository.read(edition.script)
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    (tmp_path / edition.script).parent.mkdir(parents=True)
    (tmp_path / edition.script).write_text(
        json.dumps({"title": script["title"], "release": script["release"]}, ensure_ascii=False)
    )
    edition.artifacts.mkdir(parents=True)
    for path, body in (
        (edition.picture, "picture"),
        (edition.rendered(captions=False).file, "uncaptioned picture"),
        (edition.caption_equivalence, "{}"),
        (edition.soundtrack, "soundtrack"),
        (edition.artifacts / "chapters.ffmeta", ";FFMETADATA1\n"),
        (edition.artifacts / delivery_packaging.COVER_JPEG, "cover"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    calls = []

    def run(command, timeout=120):
        calls.append((command, timeout))
        output = Path(command[-1])
        if command[0] == "ffmpeg":
            output.write_text(
                f"{output.name} encoded from {Path(command[command.index('-i') + 1]).name}\n",
                encoding="utf-8",
            )
        else:
            output.write_text(
                output.read_text(encoding="utf-8") + "author tagged\n", encoding="utf-8"
            )
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(delivery_packaging, "run", run)
    monkeypatch.setattr(delivery_packaging, "validate_picture", lambda _edition, captions: {})
    monkeypatch.setattr(delivery_packaging, "require_equivalence", lambda _edition: {})
    # The chapter track's language is written into each finished film after its keys.
    monkeypatch.setattr(
        delivery_packaging,
        "set_chapter_language",
        lambda path, language: calls.append((["chapter-language", language, str(path)], 0)),
    )
    monkeypatch.setattr(delivery_packaging, "package_metadata", lambda _edition: None)
    monkeypatch.setattr(media, "probe", lambda path: probe(kind=kind_of(path)))
    monkeypatch.setattr(media, "video_cadence", lambda _path, frames, fps: keyed(frames, 2 * fps))
    return tmp_path, edition, calls


def keyed(frames: int, every: int) -> dict:
    """A cadence record whose keyframes stand at every `every` frames from the first."""
    return {"frames": frames, "keyframes": list(range(0, frames, every))}


def kind_of(path) -> str:
    """The rendition kind a film's name declares."""
    stem = Path(path).stem
    return next(kind for kind in production.RENDITIONS if stem.endswith(f"-{kind}"))


def test_each_film_is_encoded_finished_and_checked_in_work_before_it_is_linked_into_place(
    packaging_root,
):
    root, edition, calls = packaging_root
    delivery_packaging.package_film(edition)
    package = json.loads(edition.film_package.read_text())
    assert list(package) == [
        "picture_sha256",
        "uncaptioned_picture_sha256",
        "caption_equivalence_sha256",
        "soundtrack_sha256",
        "cover_sha256",
        "script_sha256",
        "chapters_sha256",
        "editions",
        "caption_owner",
    ]
    assert package["uncaptioned_picture_sha256"] == repository.sha(
        edition.rendered(captions=False).file
    )
    assert package["caption_equivalence_sha256"] == repository.sha(edition.caption_equivalence)
    # Each film names the picture it carries.
    assert [(member["path"], member["picture"]) for member in package["editions"]] == [
        ("sample-reel-zh-uhd.mp4", "captioned"),
        ("sample-reel-zh-1080p-captioned.mp4", "captioned"),
        ("sample-reel-zh-uhd-uncaptioned.mp4", "uncaptioned"),
        ("sample-reel-zh-1080p-uncaptioned.mp4", "uncaptioned"),
    ]
    work = root / "build/runtime/work/final-film-packaging/zh"
    for member, film in zip(package["editions"], edition.films, strict=True):
        assert member["sha256"] == repository.sha(film)
        assert film.read_text() == f"{film.name} encoded from {film.name}\nauthor tagged\n"
        encode, cover, author = member["commands"]
        assert encode[-1] == str(work / film.name)
        assert cover[-1] == author[-1] == str(work / "finished" / film.name)
        assert [command for command, _ in calls[:3]] == member["commands"]
        assert calls[3][0] == ["chapter-language", "zho", str(work / "finished" / film.name)]
        calls[:4] = []
    assert list(work.rglob("*.mp4")) == []
    assert not (edition.evidence / "packaging-failure.json").exists()


def test_packaging_waits_for_both_valid_pictures_and_their_equivalence(packaging_root, monkeypatch):
    _, edition, calls = packaging_root
    checked = []
    monkeypatch.setattr(
        delivery_packaging,
        "validate_picture",
        lambda _edition, captions: checked.append(("picture", captions)),
    )

    def refuse(_edition):
        checked.append(("equivalence",))
        msg = "The zh equivalence record did not pass; run compare-pictures"
        raise PictureError(msg)

    monkeypatch.setattr(delivery_packaging, "require_equivalence", refuse)
    with pytest.raises(PictureError, match="did not pass; run compare-pictures"):
        delivery_packaging.package_film(edition)
    assert checked == [("picture", True), ("picture", False), ("equivalence",)]
    assert calls == []
    assert not edition.film_package.exists()
    edition.rendered(captions=False).file.unlink()
    with pytest.raises(PackagingError, match="No rendered picture at .*-uncaptioned.mp4"):
        delivery_packaging.package_film(edition)


def test_the_viewing_package_is_derived_again_once_the_films_are_in_place(
    packaging_root, monkeypatch
):
    _, edition, _ = packaging_root
    seen = []
    monkeypatch.setattr(
        delivery_packaging,
        "package_metadata",
        lambda current: seen.append([film.is_file() for film in current.films]),
    )
    delivery_packaging.package_film(edition)
    # Before the films, for the cover and chapters they carry; after them, for the sizes the
    # player names.
    assert seen == [[False] * 4, [True] * 4]


def test_the_commands_carry_the_release_metadata(packaging_root):
    root, edition, calls = packaging_root
    delivery_packaging.package_film(edition)
    release = repository.read(edition.script)["release"]
    artifacts, work = (
        f"{root}/build/artifacts/film/zh",
        f"{root}/build/runtime/work/final-film-packaging/zh",
    )
    created = next(argument for argument in calls[0][0] if argument.startswith("creation_time="))
    rest = [
        "-i",
        f"{artifacts}/sample-reel-zh-narration.wav",
        "-f",
        "ffmetadata",
        "-i",
        f"{artifacts}/chapters.ffmeta",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map_metadata",
        "2",
        "-map_chapters",
        "2",
    ]
    sound = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2"]
    sound += ["-t", str(specification.DURATION)]
    tags = [
        "title=示例影片 · 从源文件到成片",
        "artist=Yang HENG",
        "album_artist=Yang HENG",
        "album=示例影片 · 从源文件到成片",
        "genre=教育",
        "date=2026",
        "comment=filmkit 的示例影片，供测试和演示；内容依据 ddwg-film 的 README",
        "description=从源文件重建影片的示例；中文；纯 2D；仅旁白",
        "synopsis=" + release["synopsis"],
        "copyright=© 2026 Yang HENG",
        "media_type=9",
    ]
    streams = [
        "-metadata:s:v:0",
        "language=zho",
        "-metadata:s:v:0",
        "handler_name=画面",
        "-metadata:s:a:0",
        "language=zho",
        "-metadata:s:a:0",
        "handler_name=中文旁白",
    ]
    bitstream = (
        "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1"
        ":video_full_range_flag=0:level="
    )
    # The 1080p film averages each 2x2 block of the UHD picture between the VideoToolbox decode
    # and encode, and holds a keyframe every 2 s.
    hardware = ["-hwaccel", "videotoolbox"]
    scaled = [
        "-filter:v:0",
        "scale=w=1920:h=1080:flags=area",
        "-c:v:0",
        "h264_videotoolbox",
        "-b:v:0",
        "10M",
        "-g:v:0",
        str(2 * specification.FPS),
    ]
    attach = ["-map", "0:v:0", "-map", "0:a:0", "-map", "1:v:0", "-map_metadata", "0"]
    attach += ["-map_chapters", "0", "-c", "copy", "-disposition:v:1", "attached_pic"]
    keys = [
        "-Keys:Author=Yang HENG",
        "-Keys:Title=示例影片 · 从源文件到成片",
        "-Keys:Album=示例影片 · 从源文件到成片",
        "-Keys:Genre=教育",
        "-Keys:Description=从源文件重建影片的示例；中文；纯 2D；仅旁白",
        "-Keys:Comment=filmkit 的示例影片，供测试和演示；内容依据 ddwg-film 的 README",
        "-Keys:Copyright=© 2026 Yang HENG",
        "-Keys:Keywords=" + ", ".join(release["keywords"]),
        "-Keys:Year=2026",
        "-Keys:CreationDate=" + created.removeprefix("creation_time="),
    ]
    expected = []
    viewing = max(delivery_packaging.DEADLINE_FLOOR, 2 * specification.DURATION)
    captioned, uncaptioned = (
        "sample-reel-final-picture.mp4",
        "sample-reel-final-picture-uncaptioned.mp4",
    )
    for name, picture, decoding, video, level, marks, deadline in (
        ("sample-reel-zh-uhd.mp4", captioned, [], ["-c:v:0", "copy"], "5.2", [], 600),
        (
            "sample-reel-zh-1080p-captioned.mp4",
            captioned,
            hardware,
            scaled,
            "4.2",
            ["hd_video=2"],
            viewing,
        ),
        ("sample-reel-zh-uhd-uncaptioned.mp4", uncaptioned, [], ["-c:v:0", "copy"], "5.2", [], 600),
        (
            "sample-reel-zh-1080p-uncaptioned.mp4",
            uncaptioned,
            hardware,
            scaled,
            "4.2",
            ["hd_video=2"],
            viewing,
        ),
    ):
        inputs = ["-i", f"{artifacts}/{picture}", *rest]
        intermediate, finished = f"{work}/{name}", f"{work}/finished/{name}"
        cover = ["-i", intermediate, "-i", f"{artifacts}/sample-reel-cover.jpg", *attach]
        metadata = [arg for tag in [*tags, *marks, created] for arg in ("-metadata", tag)]
        encode = [*decoding, *inputs, *video, "-bsf:v:0", bitstream + level, *sound, *metadata]
        encode += [*streams, "-movflags", "+faststart", intermediate]
        expected += [
            (["ffmpeg", "-v", "warning", "-nostdin", *encode], deadline),
            (
                [
                    "ffmpeg",
                    "-v",
                    "warning",
                    "-nostdin",
                    *cover,
                    "-movflags",
                    "+faststart",
                    finished,
                ],
                120,
            ),
            (["exiftool", "-overwrite_original", *keys, finished], 120),
            (["chapter-language", "zho", finished], 0),
        ]
    assert calls == expected
    created = {
        argument for command, _ in calls for argument in command if "creation_time" in argument
    }
    assert len(created) == 1


def test_a_failed_check_leaves_no_film_in_place_and_keeps_the_work(packaging_root, monkeypatch):
    root, edition, _ = packaging_root
    monkeypatch.setattr(
        media, "probe", lambda path: probe(author="Someone else", kind=kind_of(path))
    )
    with pytest.raises(PackagingError, match="finished film differs from the delivery contract"):
        delivery_packaging.package_film(edition)
    assert not edition.film("uhd").exists()
    work = root / "build/runtime/work/final-film-packaging/zh"
    assert (work / "finished/sample-reel-zh-uhd.mp4").is_file()
    assert json.loads(edition.film_package.read_text())["editions"] == []
    monkeypatch.setattr(media, "probe", lambda path: probe(kind=kind_of(path)))
    with pytest.raises(PackagingError, match="Preserve existing packaging input"):
        delivery_packaging.package_film(edition)


@pytest.mark.parametrize(
    "change",
    [
        {"frames": specification.DURATION * specification.FPS - 1},
        {"author": None},
        {"sound": "data"},
        {"changes": {"album": None}},
        {"changes": {"synopsis": "Another film."}},
        {"changes": {"com.apple.quicktime.keywords": None}},
        {"changes": {"com.apple.quicktime.artist": specification.AUTHOR}},
        {"kind": "1080p-captioned"},
        {"chapters": "eng"},
    ],
    ids=[
        "frames",
        "author",
        "sound",
        "album",
        "synopsis",
        "keywords",
        "second-author",
        "hd-mark",
        "chapters",
    ],
)
def test_a_finished_film_needs_every_frame_its_author_and_release(tmp_path, monkeypatch, change):
    monkeypatch.setattr(media, "probe", lambda _path: probe(**change))
    with pytest.raises(PackagingError, match="differs from the delivery contract"):
        delivery_packaging.check_delivered_film(
            tmp_path / "film.mp4", production.Edition("zh"), production.RENDITIONS["uhd"]
        )


def test_a_finished_film_may_carry_its_creation_date_beside_its_release_keys(tmp_path, monkeypatch):
    changes = {"com.apple.quicktime.creationdate": "2026-11-09T22:00:00+00:00"}
    monkeypatch.setattr(media, "probe", lambda _path: probe(changes=changes))
    delivery_packaging.check_delivered_film(
        tmp_path / "film.mp4", production.Edition("zh"), production.RENDITIONS["uhd"]
    )


@pytest.mark.parametrize(("every", "passes"), [(2 * specification.FPS, True), (12, False)])
def test_a_1080p_film_holds_a_keyframe_every_2_seconds(tmp_path, monkeypatch, every, passes):
    monkeypatch.setattr(media, "probe", lambda _path: probe(kind="1080p-captioned"))
    monkeypatch.setattr(media, "video_cadence", lambda _path, frames, _fps: keyed(frames, every))

    def check():
        delivery_packaging.check_delivered_film(
            tmp_path / "film.mp4",
            production.Edition("zh"),
            production.RENDITIONS["1080p-captioned"],
        )

    if passes:
        check()
    else:
        with pytest.raises(PackagingError, match="differs from the delivery contract"):
            check()


def test_the_release_tags_come_from_the_script():
    edition, uhd = production.Edition("zh"), production.RENDITIONS["uhd"]
    release = repository.read(edition.script)["release"]
    tags = dict(delivery_packaging.release_tags(edition, uhd))
    assert tags == {
        "title": "示例影片 · 从源文件到成片",
        "artist": "Yang HENG",
        "album_artist": "Yang HENG",
        "album": release["collection"],
        "genre": "教育",
        "date": "2026",
        "comment": edition.comment,
        "description": edition.description,
        "synopsis": release["synopsis"],
        "copyright": "© 2026 Yang HENG",
        "media_type": "9",
    }
    viewing = dict(
        delivery_packaging.release_tags(edition, production.RENDITIONS["1080p-captioned"])
    )
    assert viewing == {**tags, "hd_video": "2"}
    assert delivery_packaging.track_names(production.Edition("en")) == {
        "picture": "Picture",
        "narration": "English narration",
    }


def test_the_release_prose_sets_typographic_quotes(tmp_path, monkeypatch):
    edition, uhd = production.Edition("en"), production.RENDITIONS["uhd"]
    script = repository.read(edition.script)
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    prose = {key: f'The {key} says "Done." It\'s done.' for key in ("comment", "description")}
    release = {**script["release"], **prose, "synopsis": 'An Agent reports "Done."'}
    repository.write(edition.script, {**script, "title": 'The "Sample" Reel', "release": release})
    tags = delivery_packaging.delivered_tags(edition, uhd)
    assert tags["title"] == tags["com.apple.quicktime.title"] == "The “Sample” Reel"
    assert tags["synopsis"] == "An Agent reports “Done.”"
    for key in ("comment", "description"):
        assert (
            tags[key] == tags[f"com.apple.quicktime.{key}"] == f"The {key} says “Done.” It’s done."
        )


def test_a_failed_encode_records_its_bindings_and_command(packaging_root, monkeypatch):
    _, edition, _ = packaging_root

    def fail(command, timeout=120):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(delivery_packaging, "run", fail)
    with pytest.raises(subprocess.TimeoutExpired):
        delivery_packaging.package_film(edition)
    failure = json.loads((edition.evidence / "packaging-failure.json").read_text())
    assert list(failure) == [
        "input_bindings",
        "command",
        "deadline_seconds",
        "error_type",
        "intermediate",
        "intermediate_sha256",
        "completed_members",
    ]
    assert failure["input_bindings"]["caption_owner"] == delivery_packaging.CAPTION_OWNER
    assert "editions" not in failure["input_bindings"]
    assert (failure["deadline_seconds"], failure["error_type"]) == (600, "TimeoutExpired")
    assert failure["intermediate"] == (
        "build/runtime/work/final-film-packaging/zh/sample-reel-zh-uhd.mp4"
    )
    assert failure["intermediate_sha256"] is None
    assert failure["completed_members"] == []


def test_a_finished_package_retires_the_receipt_of_an_earlier_failed_attempt(
    packaging_root, monkeypatch
):
    _, edition, _ = packaging_root
    succeed = delivery_packaging.run

    def fail(command, timeout=120):
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(delivery_packaging, "run", fail)
    with pytest.raises(subprocess.TimeoutExpired):
        delivery_packaging.package_film(edition)
    assert (edition.evidence / "packaging-failure.json").exists()
    monkeypatch.setattr(delivery_packaging, "run", succeed)
    delivery_packaging.package_film(edition)
    assert edition.film_package.exists()
    assert not (edition.evidence / "packaging-failure.json").exists()


def test_a_package_resumes_its_verified_films_and_refuses_changed_inputs(packaging_root):
    _, edition, calls = packaging_root
    delivery_packaging.package_film(edition)
    recorded = edition.film_package.read_text()
    calls.clear()
    delivery_packaging.package_film(edition)
    assert calls == []
    assert edition.film_package.read_text() == recorded
    edition.film("1080p-captioned").write_text("changed\n")
    with pytest.raises(PackagingError, match="Completed package member differs"):
        delivery_packaging.package_film(edition)
    edition.soundtrack.write_text("another soundtrack")
    with pytest.raises(PackagingError, match="bound to different production inputs"):
        delivery_packaging.package_film(edition)


def test_an_unrecorded_film_in_place_is_preserved(packaging_root):
    _, edition, calls = packaging_root
    edition.film("uhd").write_text("left by an interrupted step\n")
    with pytest.raises(PackagingError, match="Preserve existing film output"):
        delivery_packaging.package_film(edition)
    assert calls == []
    assert edition.film("uhd").read_text() == "left by an interrupted step\n"
    edition.picture.unlink()
    with pytest.raises(PackagingError, match="No rendered picture"):
        delivery_packaging.package_film(edition)
