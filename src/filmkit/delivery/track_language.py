"""Set the language of a finished film's chapter track in place.

FFmpeg's MP4 muxer writes the chapter text track it makes from the chapter metadata with the
language English, whatever the film's language, and offers no option for it; a remux makes a
new track the same way. The track's media header holds its language as two bytes, three letters
of five bits each, so writing them in place changes no size and no offset of the file.
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# The handler type of a text track, as FFmpeg's chapter track declares it.
TEXT_HANDLER = b"text"


class TrackLanguageError(ValueError):
    """A film's boxes do not hold the one chapter track whose language is to be set."""


def boxes(data: bytes, start: int, end: int) -> Iterator[tuple[bytes, int, int]]:
    """Each box between `start` and `end`: its type, where its payload starts and where it ends."""
    at = start
    while at + 8 <= end:
        size, kind = struct.unpack(">I4s", data[at : at + 8])
        header = 8
        if size == 1:
            size, header = struct.unpack(">Q", data[at + 8 : at + 16])[0], 16
        elif size == 0:
            size = end - at
        if size < header or at + size > end:
            msg = f"A {kind!r} box at {at} overruns its parent"
            raise TrackLanguageError(msg)
        yield kind, at + header, at + size
        at += size


def movie_box(handle: BinaryIO) -> tuple[int, int, bytes]:
    """The film's movie box, read whole, with its offset in the file and the size of its header."""
    end = handle.seek(0, 2)
    at = 0
    while at + 8 <= end:
        handle.seek(at)
        head = handle.read(16)
        size, kind = struct.unpack(">I4s", head[:8])
        header = 8
        if size == 1:
            size, header = struct.unpack(">Q", head[8:16])[0], 16
        elif size == 0:
            size = end - at
        if kind == b"moov":
            handle.seek(at)
            return at, header, handle.read(size)
        if size < header:
            break
        at += size
    msg = "The film holds no movie box"
    raise TrackLanguageError(msg)


def chapter_language_offset(moov: bytes, header: int) -> int:
    """Where, in the movie box, the chapter track's media header holds its language."""
    found = []
    for kind, start, end in boxes(moov, header, len(moov)):
        if kind != b"trak":
            continue
        for inner, media_start, media_end in boxes(moov, start, end):
            if inner != b"mdia":
                continue
            parts = {k: (s, e) for k, s, e in boxes(moov, media_start, media_end)}
            if b"hdlr" in parts and b"mdhd" in parts:
                handler = moov[parts[b"hdlr"][0] + 8 : parts[b"hdlr"][0] + 12]
                header = parts[b"mdhd"][0]
                # Version 1 times are 64-bit: the language follows 28 bytes of fields, not 16.
                if handler == TEXT_HANDLER:
                    found.append(header + 4 + (28 if moov[header] == 1 else 16))
    if len(found) != 1:
        msg = f"The film holds {len(found)} text tracks, not one chapter track"
        raise TrackLanguageError(msg)
    return found[0]


def packed(language: str) -> bytes:
    """An ISO 639-2 code as a media header holds it: three letters of five bits each."""
    if len(language) != 3 or not language.isascii() or not language.islower():
        msg = f"Not a three-letter ISO 639-2 code: {language!r}"
        raise TrackLanguageError(msg)
    code = 0
    for letter in language:
        code = code << 5 | (ord(letter) - 0x60)
    return struct.pack(">H", code)


def set_chapter_language(path: Path, language: str) -> None:
    """Write `language` into the media header of the film's one chapter track, in place."""
    value = packed(language)
    with path.open("r+b") as handle:
        at, header, moov = movie_box(handle)
        handle.seek(at + chapter_language_offset(moov, header))
        handle.write(value)
