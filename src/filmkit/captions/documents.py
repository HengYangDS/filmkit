"""Write each edition's subtitle documents: captions, chapters, transcript and chapter metadata.

The SRT and VTT files show each cue's display copy on one line. chapters.json, the transcript
and the FFmetadata chapters share one derivation of the chapters from the timeline: a chapter
starts where the timeline's segments change chapter. The transcript, which the player shows too
(`filmkit.delivery.player`), heads each chapter with its start and each scene with the start of
its voice, as a player shows a time (`clock`), and gives each thought, an utterance group, a
paragraph. Every title, heading and tag they write is typeset as the captions are, with
typographic quotation marks (`filmkit.captions.timing.typeset`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from filmkit.captions.timing import shown_text, typeset
from filmkit.repository import write
from filmkit.specification import AUTHOR, CHAPTER_CARD_SHOWN, DURATION

if TYPE_CHECKING:
    from filmkit.production import Edition


def clock(seconds: float) -> str:
    """A time as a player shows it: minutes and whole seconds, and hours past the first hour."""
    hours, rest = divmod(int(seconds), 3600)
    minutes, whole = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{whole:02}" if hours else f"{minutes}:{whole:02}"


def timecode(seconds: float, separator: str = ",") -> str:
    """A time as hours, minutes and seconds, then milliseconds after the given separator."""
    value = round(seconds * 1000)
    h, value = divmod(value, 3600000)
    m, value = divmod(value, 60000)
    s, ms = divmod(value, 1000)
    return f"{h:02}:{m:02}:{s:02}{separator}{ms:03}"


@dataclass(frozen=True)
class _Chapter:
    """A chapter's entry in chapters.json, and the timeline segments it holds."""

    entry: dict
    segments: list[dict]


@dataclass(frozen=True)
class Scene:
    """A scene as the transcript gives it: its id and title, when its voice starts, and its
    thoughts."""

    id: str
    title: str
    start: float
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class Part:
    """A chapter as the transcript gives it: its number, title and start, and its scenes."""

    number: int
    title: str
    start: float
    sections: tuple[Scene, ...]


def _chapters(segments: list[dict]) -> list[_Chapter]:
    """Each chapter of the timeline in order, from the first of its segments.

    A later chapter begins once its card replaces the previous running head.
    """
    chapters: list[_Chapter] = []
    for segment in segments:
        if not chapters or chapters[-1].entry["id"] != segment["chapter"]:
            start = segment["start"] + (CHAPTER_CARD_SHOWN if chapters else 0.0)
            entry = {
                "id": segment["chapter"],
                "title": typeset(segment["chapter_title"]),
                "start": round(start, 3),
            }
            chapters.append(_Chapter(entry, []))
        chapters[-1].segments.append(segment)
    return chapters


def _cue_documents(captions: list[dict]) -> tuple[str, str]:
    """The SRT and VTT documents of the cues."""
    srt = []
    vtt = ["WEBVTT\n"]
    for i, cue in enumerate(captions, 1):
        display = shown_text(cue).strip()
        srt.append(f"{i}\n{timecode(cue['start'])} --> {timecode(cue['end'])}\n{display}\n")
        vtt.append(f"{timecode(cue['start'], '.')} --> {timecode(cue['end'], '.')}\n{display}\n")
    return "\n".join(srt), "\n".join(vtt)


def transcript_parts(segments: list[dict]) -> list[Part]:
    """Each chapter of the timeline's segments with its scenes, as the transcript gives them.

    A chapter starts as chapters.json gives it, a scene where its voice starts, to the
    millisecond, and each of a scene's utterance groups is one paragraph.
    """
    return [
        Part(
            number,
            chapter.entry["title"],
            chapter.entry["start"],
            tuple(
                Scene(
                    segment["id"],
                    typeset(segment["title"]),
                    round(segment["voice_start"], 3),
                    tuple(typeset(group).strip() for group in segment["utterance_groups"]),
                )
                for segment in chapter.segments
            ),
        )
        for number, chapter in enumerate(_chapters(segments), 1)
    ]


def _transcript(title: str, segments: list[dict], code: str) -> str:
    """The transcript: the byline, then each chapter and each of its scenes headed by its
    time, and a paragraph for each thought."""
    byline = (
        f"{AUTHOR} · 中文 · {DURATION // 60} 分钟"
        if code == "zh"
        else f"{AUTHOR} · English · {DURATION // 60} min"
    )
    transcript = f"# {typeset(title)}\n\n{byline}\n"
    for part in transcript_parts(segments):
        transcript += f"\n## {clock(part.start)} · {part.number:02d} {part.title}\n"
        for scene in part.sections:
            transcript += f"\n### {clock(scene.start)} · {scene.title}\n"
            transcript += "".join(f"\n{paragraph}\n" for paragraph in scene.paragraphs)
    return transcript


def _chapter_metadata(title: str, comment: str, chapters: list[_Chapter]) -> str:
    """The FFmetadata of the film's tags and chapters, in milliseconds; the last ends the film."""
    metadata = (
        f";FFMETADATA1\ntitle={typeset(title)}\nartist={AUTHOR}\nauthor={AUTHOR}\n"
        f"comment={typeset(comment)}\n"
    )
    for i, chapter in enumerate(chapters):
        end = chapters[i + 1].entry["start"] if i + 1 < len(chapters) else DURATION
        metadata += (
            "\n[CHAPTER]\nTIMEBASE=1/1000\n"
            f"START={round(chapter.entry['start'] * 1000)}\n"
            f"END={round(end * 1000)}\ntitle={chapter.entry['title']}\n"
        )
    return metadata


def subtitle_files(timeline: dict, edition: Edition) -> None:
    """Write the edition's SRT and VTT captions, chapters, transcript and chapter metadata."""
    output = edition.artifacts
    srt, vtt = _cue_documents(timeline["captions"])
    (output / f"{edition.prefix}.srt").write_text(srt)
    (output / f"{edition.prefix}.vtt").write_text(vtt)
    chapters = _chapters(timeline["segments"])
    write(output / "chapters.json", {"chapters": [chapter.entry for chapter in chapters]})
    transcript = _transcript(timeline["title"], timeline["segments"], edition.code)
    (output / f"{edition.prefix}-transcript.md").write_text(transcript)
    metadata = _chapter_metadata(timeline["title"], edition.comment, chapters)
    (output / "chapters.ffmeta").write_text(metadata)
