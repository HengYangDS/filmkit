"""Render each edition's player page from the film's words and colours and its delivered files.

The engine owns the page: its structure, style and script, and the interface words of both
languages. A film declares only the summary each edition shows under the film,
`editions.<code>.summary`, and the five colours of `[player]` (`filmkit.film`); the rest comes
from the edition's script, timeline and delivered files:

- the header: the title, then the author, the language, the film's version as the edition labels
  it, the running time and the frame rate, and links to the other edition's player and to the
  entry page;
- the video, which opens on the viewing film with its captions. Each version has two films: one
  whose picture draws the captions and one without them. The captions control, a button pressed
  while the captions show, switches the film to the other one of the same version, and a version
  button to the film of its version with the captions as they are; both keep the time and
  whether the film plays, and a frame of the film on the screen: the page's script
  (`player-page.js`) makes the chosen film ready in a second video in the same grid cell and
  shows it only once it holds its frame. The page shows the captions no other way: its one
  track of the edition's WebVTT cues is a metadata track, which stays hidden and which no
  browser's own controls offer, so the captions are never doubled. The page embeds the cues as
  a data URL, since Chrome refuses a page opened from disk the caption file beside it;
- a button for each version and the captions control, and a button for each chapter, which seeks
  to the chapter's start and plays;
- the summary, then the transcript (`filmkit.captions.documents.transcript_parts`): each chapter
  and scene headed by its time in a button that seeks there and plays, and each thought a
  paragraph, which the track's cues mark as the current one while the film plays;
- the files list: each delivered file by kind, version, format and size, in decimal units, and
  for each film whether its picture draws the captions; the dot before a size follows a closing
  full-width bracket without a space. A browser shows the films and covers as a viewer expects,
  so they are links. It would show every other file as raw text, so the Markdown
  transcript, the chapter files and the SRT and WebVTT captions are downloads, labelled by kind
  and purpose, as data URLs of their bytes, since a browser ignores `download` on a file beside
  a page opened from disk. The transcript in the page stays the place to read.

`player_binding` names what a page shows beyond the script and the timeline that the viewing
package binds: the declared words and colours, and the size of each listed file. Packaging reads
the film's version and passes it to the page, which names it with the edition's label,
版本号 1.3.0 or Version 1.3.0; `entry_version` is the line that names it with both labels under
the film's title on the entry page.
"""

from __future__ import annotations

import base64
import json
import math
import re
from html import escape
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.captions.documents import clock, transcript_parts
from filmkit.captions.timing import shown_text, typeset
from filmkit.film import FILM
from filmkit.production import CODES
from filmkit.specification import AUTHOR, DURATION, FPS

if TYPE_CHECKING:
    from filmkit.captions.documents import Part, Scene
    from filmkit.production import Edition

# What a thought's words and its cues' are compared without: all but letters and digits.
UNSPOKEN = re.compile(r"[\W_]+")
# The closing full-width brackets, which hold their own space before what follows them.
CLOSING = ("）", "」", "』", "】", "〕", "〉", "》")
# Each edition's cover as delivered, PNG and JPEG; the PNG is the video's poster.
COVER_PNG = f"{FILM.slug}-cover.png"
COVER_JPEG = f"{FILM.slug}-cover.jpg"
# Each version's films with and without captions, whether the page opens on it, and the word of
# its button.
VERSIONS = (
    ("1080p-captioned", "1080p-uncaptioned", "true", "viewing"),
    ("uhd", "uhd-uncaptioned", "false", "uhd"),
)
# The words of each edition's page.
WORDS = {
    "zh": {
        "lang": "zh-CN",
        "language": "中文",
        "version": "版本号",
        "versions": "视频版本",
        "viewing": "观看版 · 1080p",
        "uhd": "超高清 4K · 2160p",
        "captions": "字幕",
        "captions_on": "：开",
        "captions_off": "：关",
        "track": "中文字幕",
        "chapters": "章节",
        "transcript": "完整讲稿",
        "files": "文件",
        "film": "影片",
        "viewing_film": "观看版 1080p",
        "uhd_film": "超高清 4K",
        "drawn": "画面内含字幕",
        "undrawn": "无字幕",
        "downloads": "下载",
        "labelled": "{kind}（{form}，{purpose}）",
        "to_download": "供下载",
        "for_players": "下载后供其他播放器使用",
        "script": "讲稿",
        "cover": "封面",
        "languages": "语言",
        "entry": "选择语言",
        "play_from": "从 {} 播放",
        "unplayable": "这个浏览器播放不了当前的编码，可以用系统的播放器打开文件里的影片。",
    },
    "en": {
        "lang": "en",
        "language": "English",
        "version": "Version",
        "versions": "Video versions",
        "viewing": "Viewing edition · 1080p",
        "uhd": "4K UHD · 2160p",
        "captions": "Captions",
        "captions_on": ": on",
        "captions_off": ": off",
        "track": "English captions",
        "chapters": "Chapters",
        "transcript": "Transcript",
        "files": "Files",
        "film": "Film",
        "viewing_film": "Viewing edition 1080p",
        "uhd_film": "4K UHD",
        "drawn": "captions in the picture",
        "undrawn": "no captions",
        "downloads": "Downloads",
        "labelled": "{kind} ({form}, {purpose})",
        "to_download": "download",
        "for_players": "download for other players",
        "script": "Transcript",
        "cover": "Cover",
        "languages": "Languages",
        "entry": "Choose a language",
        "play_from": "Play from {}",
        "unplayable": "This browser cannot play this encoding; open the film from the files "
        "below in your system’s player.",
    },
}
# The page's style, in the declared colours.
STYLE = Template(
    ":root{color-scheme:dark;background:$background;color:$text;"
    'font-family:system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}'
    "*{box-sizing:border-box}body{margin:0;padding:36px 5vw 48px}"
    "header,main{max-width:1400px;margin:0 auto}"
    "header{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;"
    "gap:12px 24px;margin-bottom:24px}h1{font-size:23px;font-weight:600;margin:0}"
    "header p{font-size:13px;color:$muted;margin:6px 0 0}"
    ".screen{display:grid}.screen>video{grid-area:1/1}"
    "video{display:block;width:100%;aspect-ratio:16/9;background:$background;"
    "border:1px solid $line}nav{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}"
    "header nav{margin:0}button,a{display:inline-block;background:transparent;color:$text;"
    "border:1px solid $line;"
    "border-radius:3px;padding:10px 14px;font:inherit;font-size:14px;text-decoration:none;"
    "cursor:pointer}button:hover,a:hover,button[aria-pressed=true]{border-color:$accent}"
    ":focus-visible{outline:2px solid $accent;outline-offset:3px}"
    "#summary p{font-size:14px;color:$muted;line-height:1.75;margin:10px 0;max-width:60em}"
    "#transcript{margin-top:28px;border-top:1px solid $line;padding-top:14px}"
    "#transcript summary{cursor:pointer;font-size:15px}"
    "#transcript h2{font-size:17px;font-weight:600;margin:30px 0 6px}"
    "#transcript h3{font-size:14px;font-weight:500;color:$muted;margin:18px 0 2px}"
    "#transcript p{max-width:46em;line-height:1.75;margin:8px 0}"
    "#transcript p[aria-current=true]{color:$accent}"
    "button.time{padding:2px 8px;margin-right:6px;font-size:13px;"
    "font-variant-numeric:tabular-nums}"
    "footer{margin-top:28px;border-top:1px solid $line;padding-top:16px}"
    "footer h2{font-size:15px;font-weight:600;margin:0 0 12px}"
    "footer h3{font-size:14px;font-weight:500;color:$muted;margin:0 0 10px}"
    "footer ul{list-style:none;margin:0 0 12px;padding:0;display:flex;flex-wrap:wrap;gap:12px}"
    ".size{white-space:nowrap}"
    "@media(max-width:700px){body{padding:20px 16px}h1{font-size:19px}"
    "button,a{font-size:13px}}"
)
# What the page does (`player-page.js`, beside this module), inlined into the page.
SCRIPT = Path(__file__).with_name("player-page.js").read_text(encoding="utf-8")


def runtime_label() -> str:
    """The films' running time as the player and the entry page show it, minutes:seconds."""
    minutes, seconds = divmod(DURATION, 60)
    return f"{minutes:02d}:{seconds:02d}"


def version_label(code: str, version: str) -> str:
    """The film's version as an edition names it, with its label: 版本号 1.3.0, Version 1.3.0."""
    return f"{WORDS[code]['version']} {version}"


def entry_version(version: str) -> str:
    """The entry page's line under the film's title: the version with both editions' labels."""
    labels = " / ".join(
        f'<span lang="{WORDS[code]["lang"]}">{WORDS[code]["version"]}</span>' for code in CODES
    )
    return f'<p class="version">{labels} {escape(version)}</p>'


def size_label(size: int) -> str:
    """A file's size in decimal units, as the files list names it: 404 B, 13 KB, 263 MB, 1.5 GB.

    A size rounds half up to whole kilobytes and megabytes and to tenths of a gigabyte, the
    arithmetic the real-browser readback repeats (`player-verdict.mjs`).
    """
    if size < 1000:
        return f"{size} B"
    for unit, scale in (("KB", 1e3), ("MB", 1e6)):
        if (value := math.floor(size / scale + 0.5)) < 1000:
            return f"{value} {unit}"
    return f"{math.floor(size / 1e8 + 0.5) / 10:.1f} GB"


def listed_files(edition: Edition) -> list[tuple[str, str]]:
    """Each delivered file a browser shows as a viewer expects, in list order, by name, with its
    kind, version, captions and format in the edition's language: each version's film with its
    captions drawn and without them, then the covers."""
    words = WORDS[edition.code]
    film, cover = words["film"], words["cover"]
    return [
        *(
            (edition.film(kind).name, f"{film} · {words[version]} · {words[captions]} · MP4")
            for version, kinds in (
                ("viewing_film", ("1080p-captioned", "1080p-uncaptioned")),
                ("uhd_film", ("uhd", "uhd-uncaptioned")),
            )
            for kind, captions in zip(kinds, ("drawn", "undrawn"), strict=True)
        ),
        (COVER_PNG, f"{cover} · PNG"),
        (COVER_JPEG, f"{cover} · JPEG"),
    ]


def download_files(edition: Edition) -> list[tuple[str, str, str]]:
    """Each delivered file a browser would show as raw text, offered as a download: by name, with
    its media type and its label of kind, format and purpose in the edition's language."""
    words = WORDS[edition.code]
    prefix, label = edition.prefix, words["labelled"].format
    return [
        (name, media_type, label(kind=words[kind], form=form, purpose=words[purpose]))
        for name, media_type, kind, form, purpose in (
            (f"{prefix}-transcript.md", "text/markdown", "script", "Markdown", "to_download"),
            ("chapters.json", "application/json", "chapters", "JSON", "to_download"),
            ("chapters.ffmeta", "text/plain", "chapters", "FFmetadata", "to_download"),
            (f"{prefix}.vtt", "text/vtt", "captions", "WebVTT", "for_players"),
            (f"{prefix}.srt", "application/x-subrip", "captions", "SRT", "for_players"),
        )
    ]


def file_size(edition: Edition, name: str) -> int | None:
    """The size in bytes of a delivered file beside the player, or None before it is made."""
    path = edition.artifacts / name
    return path.stat().st_size if path.is_file() else None


def sized(label: str, size: int | None) -> str:
    """A files list entry's words: its label, then its size, which never wraps from its unit.

    The dot before the size follows a space, or directly a closing full-width bracket, which
    holds its own space: 讲稿（Markdown，供下载）· 9 KB.
    """
    shown = escape(label)
    if size is None:
        return shown
    space = "" if label.endswith(CLOSING) else " "
    return f'{shown}<span class="size">{space}· {size_label(size)}</span>'


def file_link(edition: Edition, name: str, label: str) -> str:
    """A files list entry: a link to the file, named by its kind, version, format and size."""
    shown = sized(label, file_size(edition, name))
    return f'<li><a class="file" href="{name}">{shown}</a></li>'


def embedded(edition: Edition, name: str, media_type: str) -> str:
    """A delivered text file as a data URL of its bytes."""
    data = base64.b64encode((edition.artifacts / name).read_bytes()).decode("ascii")
    return f"data:{media_type};charset=utf-8;base64,{data}"


def download_link(edition: Edition, name: str, media_type: str, label: str) -> str:
    """A files list entry a browser saves, from a page opened from disk too: a data URL named
    as the delivered file."""
    url, shown = embedded(edition, name, media_type), sized(label, file_size(edition, name))
    return f'<li><a class="file" href="{url}" download="{name}">{shown}</a></li>'


def player_binding(edition: Edition) -> dict:
    """What the page shows beyond the bound script and timeline: the SHA-256 of the declared
    summary and colours, and the size of each listed file, None for one not yet made."""
    declared = {"summary": FILM.editions[edition.code].summary, "player": FILM.player.model_dump()}
    text = json.dumps(declared, ensure_ascii=False, sort_keys=True)
    names = [name for name, _ in listed_files(edition)]
    names += [name for name, _, _ in download_files(edition)]
    return {
        "declaration_sha256": repository.content_sha(text),
        "files": [{"path": name, "bytes": file_size(edition, name)} for name in names],
    }


def seek_time(value: float) -> str:
    """A time for a button to seek to, to the millisecond and without trailing zeros."""
    return f"{round(value, 3):.3f}".rstrip("0").rstrip(".")


def time_button(value: float, words: dict[str, str]) -> str:
    """A button that shows a time and plays the film from it."""
    shown = clock(value)
    label = escape(words["play_from"].format(shown))
    return (
        f'<button type="button" class="time" data-time="{seek_time(value)}" '
        f'aria-label="{label}">{shown}</button>'
    )


def thought_starts(scene: Scene, captions: list[dict]) -> list[float | None]:
    """When each of a scene's thoughts starts: at the first of the scene's cues that falls in it.

    A scene's cues hold its thoughts' words in order, so a thought ends where the letters and
    digits of the cues so far reach its own. A thought no cue reaches has no start.
    """
    cues = iter(cue for cue in captions if cue["segment"] == scene.id)
    starts: list[float | None] = []
    said = reached = 0
    for paragraph in scene.paragraphs:
        reached += len(UNSPOKEN.sub("", paragraph))
        start = None
        while said < reached and (cue := next(cues, None)) is not None:
            start = cue["start"] if start is None else start
            said += len(UNSPOKEN.sub("", shown_text(cue)))
        starts.append(start)
    return starts


def thought_html(paragraph: str, start: float | None) -> str:
    """A thought as a paragraph, with the time its first cue marks it from."""
    marked = "" if start is None else f' data-from="{seek_time(start)}"'
    return f"<p{marked}>{escape(paragraph)}</p>"


def transcript_html(parts: list[Part], captions: list[dict], words: dict[str, str]) -> str:
    """The transcript: each chapter and scene headed by its time, and each thought a paragraph."""
    return "".join(
        f"<h2>{time_button(part.start, words)} {part.number:02d} {escape(part.title)}</h2>"
        + "".join(
            f"<h3>{time_button(scene.start, words)} {escape(scene.title)}</h3>"
            + "".join(
                thought_html(paragraph, start)
                for paragraph, start in zip(
                    scene.paragraphs, thought_starts(scene, captions), strict=True
                )
            )
            for scene in part.sections
        )
        for part in parts
    )


def controls(edition: Edition, parts: list[Part], words: dict[str, str]) -> str:
    """The version buttons and the captions control, then a button for each chapter.

    A version button names its films with and without captions. The captions control is pressed
    while the captions show; its words say whether they do, and its name, the part a screen
    reader reads beside the pressed state, is the word for captions alone.
    """
    versions = "".join(
        f'<button type="button" data-captioned="{edition.film(captioned).name}" '
        f'data-uncaptioned="{edition.film(uncaptioned).name}" '
        f'aria-pressed="{pressed}">{words[name]}</button>'
        for captioned, uncaptioned, pressed, name in VERSIONS
    )
    on, off = escape(words["captions_on"]), escape(words["captions_off"])
    versions += (
        f'<button type="button" id="captions" aria-pressed="true" data-on="{on}" '
        f'data-off="{off}">{words["captions"]}<span aria-hidden="true">{on}</span></button>'
    )
    chapters = "".join(
        f'<button type="button" class="chapter" data-time="{seek_time(part.start)}">'
        f"{escape(part.title)}</button>"
        for part in parts
    )
    return (
        f'<nav aria-label="{words["versions"]}">{versions}</nav>'
        f'<nav id="chapters" aria-label="{words["chapters"]}">{chapters}</nav>'
    )


def player_page(edition: Edition, version: str) -> str:
    """The edition's player page, from the film's declaration, its version and the edition's
    files."""
    code = edition.code
    words, other_code = WORDS[code], next(c for c in CODES if c != code)
    other = WORDS[other_code]
    title = escape(typeset(repository.read(edition.script)["title"]))
    timeline = repository.read(edition.timeline)
    parts = transcript_parts(timeline["segments"])
    track = embedded(edition, f"{edition.prefix}.vtt", "text/vtt")
    files = "".join(file_link(edition, name, label) for name, label in listed_files(edition))
    downloads = "".join(
        download_link(edition, name, media_type, label)
        for name, media_type, label in download_files(edition)
    )
    languages = (
        f'<nav id="languages" aria-label="{words["languages"]}">'
        f'<a class="language" href="../{other_code}/index.html" lang="{other["lang"]}" '
        f'hreflang="{other["lang"]}">{other["language"]}</a>'
        f'<a class="language" href="../index.html">{words["entry"]}</a></nav>'
    )
    shown = escape(version_label(code, version))
    byline = f"{escape(AUTHOR)} · {words['language']} · {shown} · {runtime_label()} · {FPS} fps"
    return f"""<!doctype html>
<html lang="{words["lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="{escape(AUTHOR)}">
<title>{title}</title>
<style>{STYLE.substitute(FILM.player.model_dump())}</style>
</head>
<body>
<header><div><h1>{title}</h1><p>{byline}</p></div>{languages}</header>
<main>
<div class="screen"><video id="film" controls playsinline preload="metadata" poster="{COVER_PNG}">
<source src="{edition.film("1080p-captioned").name}" type="video/mp4">
<track kind="metadata" srclang="{code}" label="{words["track"]}" default src="{track}">
</video></div>
{controls(edition, parts, words)}
<section id="summary"><p>{escape(FILM.editions[code].summary)}</p><p id="playback-status" \
role="status" data-unplayable="{escape(words["unplayable"])}">\
{words["viewing"]} · {words["captions"]}{words["captions_on"]}</p></section>
<section id="transcript"><details><summary>{words["transcript"]}</summary>\
{transcript_html(parts, timeline["captions"], words)}</details></section>
<footer><h2>{words["files"]}</h2><ul>{files}</ul><h3>{words["downloads"]}</h3>\
<ul>{downloads}</ul><a href="#transcript">{words["transcript"]}</a></footer>
</main>
<script>{SCRIPT}</script>
</body>
</html>
"""
