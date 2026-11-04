"""A finished film's chapter track takes the edition's language in place."""

import json
import struct
import subprocess

import pytest

from filmkit.delivery.track_language import (
    TrackLanguageError,
    packed,
    set_chapter_language,
)


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", 8 + len(payload), kind) + payload


def track(handler: bytes, version: int, language: str) -> bytes:
    """A track whose media header is of `version` and whose handler is of type `handler`."""
    times = b"\0" * (28 if version else 16)
    header = box(b"mdhd", bytes([version, 0, 0, 0]) + times + packed(language) + b"\0\0")
    handler_box = box(b"hdlr", b"\0" * 8 + handler + b"\0" * 13)
    return box(b"trak", box(b"mdia", header + handler_box))


def languages(path) -> list[str]:
    """Each track's language as FFprobe reads it."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream_tags=language", "-of", "json", path],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return [stream["tags"]["language"] for stream in json.loads(probe.stdout)["streams"]]


@pytest.mark.ffmpeg
def test_the_chapter_track_ffmpeg_makes_takes_the_edition_language(tmp_path):
    chapters = tmp_path / "chapters.ffmeta"
    chapters.write_text(
        ";FFMETADATA1\n\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=0\nEND=1000\ntitle=一\n"
        "\n[CHAPTER]\nTIMEBASE=1/1000\nSTART=1000\nEND=2000\ntitle=二\n"
    )
    film = tmp_path / "film.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i", "color=s=64x36:r=10:d=2"]
        + ["-f", "ffmetadata", "-i", str(chapters), "-map", "0:v", "-map_chapters", "1"]
        + ["-c:v", "libx264", "-metadata:s:v:0", "language=zho", "-movflags", "+faststart"]
        + [str(film)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    assert languages(film) == ["zho", "eng"]
    size = film.stat().st_size
    set_chapter_language(film, "zho")
    assert languages(film) == ["zho", "zho"]
    assert film.stat().st_size == size


def test_a_version_one_header_is_written_and_other_tracks_are_kept(tmp_path):
    film = tmp_path / "film.mp4"
    moov = box(b"moov", track(b"vide", 0, "zho") + track(b"text", 1, "eng"))
    film.write_bytes(box(b"ftyp", b"isom") + moov + box(b"mdat", b"\0" * 32))
    set_chapter_language(film, "zho")
    written = film.read_bytes()
    assert written.count(packed("zho")) == 2 and packed("eng") not in written
    assert len(written) == 12 + len(moov) + 40


@pytest.mark.parametrize(
    ("tracks", "language", "refusal"),
    [
        ([track(b"vide", 0, "zho")], "zho", "holds 0 text tracks"),
        ([track(b"text", 0, "eng"), track(b"text", 0, "eng")], "zho", "holds 2 text tracks"),
        ([track(b"text", 0, "eng")], "Chinese", "Not a three-letter ISO 639-2 code"),
    ],
)
def test_a_film_without_one_chapter_track_or_a_code_refuses(tmp_path, tracks, language, refusal):
    film = tmp_path / "film.mp4"
    film.write_bytes(box(b"ftyp", b"isom") + box(b"moov", b"".join(tracks)))
    before = film.read_bytes()
    with pytest.raises(TrackLanguageError, match=refusal):
        set_chapter_language(film, language)
    assert film.read_bytes() == before


def test_a_large_movie_box_is_read_and_a_box_that_overruns_its_parent_refuses(tmp_path):
    film = tmp_path / "film.mp4"
    tracks = track(b"text", 0, "eng")
    # A movie box whose size is given in 64 bits after a size field of 1.
    large = struct.pack(">I4sQ", 1, b"moov", 16 + len(tracks)) + tracks
    film.write_bytes(box(b"ftyp", b"isom") + large)
    set_chapter_language(film, "zho")
    assert packed("zho") in film.read_bytes()
    broken = bytearray(box(b"moov", tracks))
    broken[8:12] = struct.pack(">I", len(tracks) + 64)
    film.write_bytes(box(b"ftyp", b"isom") + bytes(broken))
    with pytest.raises(TrackLanguageError, match="overruns its parent"):
        set_chapter_language(film, "zho")


def test_a_film_without_a_movie_box_refuses(tmp_path):
    film = tmp_path / "film.mp4"
    film.write_bytes(box(b"ftyp", b"isom") + box(b"mdat", b"\0" * 8))
    with pytest.raises(TrackLanguageError, match="no movie box"):
        set_chapter_language(film, "zho")
