"""The player each edition's viewing package holds, rendered by the engine from the film's words
and colours and the edition's delivered files."""

import base64
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

import pytest

import filmkit.captions.documents as captions_documents
import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.player as delivery_player
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.film import FILM
from filmkit.picture.rendering import COMPOSITION_SCRIPT


class Page(HTMLParser):
    """A page's elements in document order, each with its tag, its attributes and its text."""

    def __init__(self, html: str) -> None:
        super().__init__()
        self.elements: list[dict] = []
        self.open: list[dict] = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        element = {"tag": tag, **dict(attrs), "text": ""}
        self.elements.append(element)
        if tag not in ("meta", "source", "track"):
            self.open.append(element)

    def handle_endtag(self, tag):
        while self.open and self.open.pop()["tag"] != tag:
            pass

    def handle_data(self, data):
        for element in self.open:
            element["text"] += data

    def all(self, tag: str, **attrs: str) -> list[dict]:
        """The elements of a tag whose attributes hold these values, `class_` for the class."""
        wanted = {key.rstrip("_"): value for key, value in attrs.items()}
        return [
            e
            for e in self.elements
            if e["tag"] == tag and all(e.get(k) == v for k, v in wanted.items())
        ]


def segment(sid, chapter, title, start, groups):
    return {
        "id": sid,
        "chapter": chapter,
        "chapter_title": title,
        "title": f"Scene <{sid}>",
        "start": start,
        "voice_start": start + 2.8721,
        "utterance_groups": groups,
    }


def sizes(edition: production.Edition) -> dict[str, int]:
    """The delivered files beside the player and their sizes in bytes, the captions left out."""
    return {
        f"{edition.prefix}-1080p-captioned.mp4": 203_312_000,
        f"{edition.prefix}-1080p-uncaptioned.mp4": 198_700_000,
        f"{edition.prefix}-uhd.mp4": 262_800_000,
        f"{edition.prefix}-uhd-uncaptioned.mp4": 241_400_000,
        f"{edition.prefix}-transcript.md": 8_702,
        "chapters.json": 404,
        "chapters.ffmeta": 469,
        f"{FILM.slug}-cover.png": 260_300,
        f"{FILM.slug}-cover.jpg": 251_500,
    }


# The cues of the timeline below: one for each thought, and two for the one thought of scene 02.
CUES = [
    {"start": 3.0, "end": 4.0, "text": "One & two. ", "segment": "01"},
    {"start": 5.5, "end": 6.0, "text": "Three's.", "display_text": "Three’s.", "segment": "01"},
    {"start": 23.0, "end": 24.0, "text": "Four, ", "segment": "02"},
    {"start": 24.5, "end": 25.0, "text": "and more.", "segment": "02"},
    {"start": 43.0, "end": 44.0, "text": "Five.", "segment": "03"},
    {"start": 44.5, "end": 45.0, "text": "Six.", "segment": "03"},
]


@pytest.fixture
def delivered(tmp_path, monkeypatch):
    """Both editions' scripts, timelines and delivered files below a new root."""
    scripts = {code: repository.read(production.Edition(code).script) for code in ("zh", "en")}
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for code, script in scripts.items():
        edition = production.Edition(code)
        repository.write(edition.script, {"title": "A <Reel> & Co", "release": script["release"]})
        segments = [
            segment("01", "a", "Ay", 0.0, ["One & two. ", "Three's."]),
            segment("02", "a", "Ay", 20.0, ["Four, and more."]),
            segment("03", "b", "Bee", 40.0, ["Five.", "Six."]),
        ]
        repository.write(edition.timeline, {"segments": segments, "captions": CUES})
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n汉 A\n"
        (edition.artifacts / f"{edition.prefix}.vtt").write_text(vtt, encoding="utf-8")
        srt = "1\n00:00:01,000 --> 00:00:02,000\n汉 A\n"
        (edition.artifacts / f"{edition.prefix}.srt").write_text(srt, encoding="utf-8")
        for name, size in sizes(edition).items():
            with (edition.artifacts / name).open("wb") as handle:
                handle.truncate(size)
    return tmp_path


def test_sizes_are_named_in_decimal_units():
    label = delivery_player.size_label
    assert [label(404), label(999), label(1000), label(13_005), label(999_600)] == [
        "404 B",
        "999 B",
        "1 KB",
        "13 KB",
        "1 MB",
    ]
    assert [label(262_800_000), label(1_500_000_000)] == ["263 MB", "1.5 GB"]


def test_the_player_shows_the_film_its_versions_and_chapters_over_a_hidden_track(delivered):
    edition = production.Edition("zh")
    html = delivery_player.player_page(edition, "1.3.0")
    page = Page(html)
    assert page.all("html")[0]["lang"] == "zh-CN"
    assert page.all("title")[0]["text"] == "A <Reel> & Co"
    # The line under the title names the film's version after the language.
    runtime = f"{specification.DURATION // 60:02d}:{specification.DURATION % 60:02d}"
    byline = f"{specification.AUTHOR} · 中文 · 版本号 1.3.0 · {runtime} · 60 fps"
    assert page.all("header")[0]["text"] == f"A <Reel> & Co{byline}English选择语言"
    # The film's colours, and its summary under the film.
    assert all(colour in html for colour in FILM.player.model_dump().values())
    assert FILM.editions["zh"].summary in page.all("section", id="summary")[0]["text"]
    # The viewing film plays first, with its captions. The pictures draw the captions, so the track
    # of the edition's WebVTT cues is one no browser shows or offers: a metadata track, kept hidden.
    assert page.all("video", id="film")[0]["poster"] == "sample-reel-cover.png"
    assert [s["src"] for s in page.all("source")] == ["sample-reel-zh-1080p-captioned.mp4"]
    [track] = page.all("track")
    assert (track["kind"], track["srclang"], track["label"]) == ("metadata", "zh", "中文字幕")
    assert "default" in track
    embedded = "data:text/vtt;charset=utf-8;base64,"
    vtt = (edition.artifacts / "sample-reel-zh.vtt").read_bytes()
    assert base64.b64decode(track["src"].removeprefix(embedded)) == vtt
    assert track["src"].startswith(embedded)
    # Each version names its film with captions and its film without them.
    buttons = [b for b in page.all("button") if "data-captioned" in b]
    assert [
        (b["data-captioned"], b["data-uncaptioned"], b["text"], b["aria-pressed"]) for b in buttons
    ] == [
        (
            "sample-reel-zh-1080p-captioned.mp4",
            "sample-reel-zh-1080p-uncaptioned.mp4",
            "观看版 · 1080p",
            "true",
        ),
        (
            "sample-reel-zh-uhd.mp4",
            "sample-reel-zh-uhd-uncaptioned.mp4",
            "超高清 4K · 2160p",
            "false",
        ),
    ]
    # One captions control, pressed while the captions show: its words say so, and a screen reader
    # reads its name with the pressed state.
    [control] = page.all("button", id="captions")
    assert (control["aria-pressed"], control["text"]) == ("true", "字幕：开")
    assert (control["data-on"], control["data-off"]) == ("：开", "：关")
    [state] = [e for e in page.all("span") if e.get("aria-hidden") == "true"]
    assert state["text"] == "：开"
    assert page.all("p", id="playback-status")[0]["text"] == "观看版 · 1080p · 字幕：开"
    # The control switches films; showing the track would double the drawn captions, so nothing in
    # the page can.
    assert "showing" not in html and "::cue" not in html
    # Each chapter's button seeks to its start, as chapters.json gives it.
    chapters = [(b["text"], b["data-time"]) for b in page.all("button", class_="chapter")]
    assert chapters == [("Ay", "0"), ("Bee", f"{40 + specification.CHAPTER_CARD_SHOWN:g}")]


def test_the_page_runs_its_script_over_a_screen_that_can_hold_two_films(delivered):
    html = delivery_player.player_page(production.Edition("zh"), "1.3.0")
    page = Page(html)
    # The page's script is the engine's player-page.js, inlined whole.
    script = (Path(delivery_player.__file__).parent / "player-page.js").read_text()
    assert f"<script>{script}</script>" in html
    assert delivery_player.SCRIPT == script
    # The film stands in a grid cell that a second film can share while a switch makes it ready.
    screen = page.all("div", class_="screen")
    assert len(screen) == 1
    assert page.elements[page.elements.index(screen[0]) + 1]["id"] == "film"
    assert ".screen{display:grid}.screen>video{grid-area:1/1}" in html


def test_the_transcript_heads_each_chapter_and_scene_with_its_time_and_gives_each_thought(
    delivered,
):
    page = Page(delivery_player.player_page(production.Edition("zh"), "1.3.0"))
    buttons = page.all("button", class_="time")
    assert [(b["data-time"], b["text"], b["aria-label"]) for b in buttons] == [
        ("0", "0:00", "从 0:00 播放"),
        ("2.872", "0:02", "从 0:02 播放"),
        ("22.872", "0:22", "从 0:22 播放"),
        (f"{40 + specification.CHAPTER_CARD_SHOWN:g}", "0:40", "从 0:40 播放"),
        ("42.872", "0:42", "从 0:42 播放"),
    ]
    assert [h["text"] for h in page.all("h2")][:2] == ["0:00 01 Ay", "0:40 02 Bee"]
    assert [h["text"] for h in page.all("h3")][:3] == [
        "0:02 Scene <01>",
        "0:22 Scene <02>",
        "0:42 Scene <03>",
    ]
    transcript = [p["text"] for p in page.all("p") if not p.get("id") and p["text"]]
    assert transcript[-5:] == ["One & two.", "Three’s.", "Four, and more.", "Five.", "Six."]
    # Each thought starts at its first cue, which marks it as the current paragraph.
    thoughts = [(p["text"], p["data-from"]) for p in page.all("p") if "data-from" in p]
    assert thoughts == [
        ("One & two.", "3"),
        ("Three’s.", "5.5"),
        ("Four, and more.", "23"),
        ("Five.", "43"),
        ("Six.", "44.5"),
    ]


def test_the_files_list_names_each_delivered_file_and_the_language_links_lead_to_the_others(
    delivered,
):
    edition = production.Edition("zh")
    html = delivery_player.player_page(edition, "1.3.0")
    page = Page(html)
    vtt = (edition.artifacts / "sample-reel-zh.vtt").stat().st_size
    srt = (edition.artifacts / "sample-reel-zh.srt").stat().st_size
    files = page.all("a", class_="file")
    # A browser shows the films and covers as a viewer expects, and each film says whether its
    # picture draws the captions.
    drawn, undrawn = "画面内含字幕 · MP4", "无字幕 · MP4"
    assert [(a["href"], a["text"]) for a in files[:6]] == [
        ("sample-reel-zh-1080p-captioned.mp4", f"影片 · 观看版 1080p · {drawn} · 203 MB"),
        ("sample-reel-zh-1080p-uncaptioned.mp4", f"影片 · 观看版 1080p · {undrawn} · 199 MB"),
        ("sample-reel-zh-uhd.mp4", f"影片 · 超高清 4K · {drawn} · 263 MB"),
        ("sample-reel-zh-uhd-uncaptioned.mp4", f"影片 · 超高清 4K · {undrawn} · 241 MB"),
        ("sample-reel-cover.png", "封面 · PNG · 260 KB"),
        ("sample-reel-cover.jpg", "封面 · JPEG · 252 KB"),
    ]
    # Every text file it would only show raw is a real download, labelled by kind and purpose: a
    # page opened from disk can save what it holds, where a browser ignores `download` on a file
    # beside it. A size after a closing full-width bracket follows it without a space, since the
    # bracket holds its own.
    assert [(a["download"], a["text"]) for a in files[6:]] == [
        ("sample-reel-zh-transcript.md", "讲稿（Markdown，供下载）· 9 KB"),
        ("chapters.json", "章节（JSON，供下载）· 404 B"),
        ("chapters.ffmeta", "章节（FFmetadata，供下载）· 469 B"),
        ("sample-reel-zh.vtt", f"字幕（WebVTT，下载后供其他播放器使用）· {vtt} B"),
        ("sample-reel-zh.srt", f"字幕（SRT，下载后供其他播放器使用）· {srt} B"),
    ]
    for link in files[6:]:
        assert link["href"].startswith("data:")
        held = base64.b64decode(link["href"].split(",", 1)[1])
        assert held == (edition.artifacts / link["download"]).read_bytes()
    assert "下载" in [h["text"] for h in page.all("h3")]
    assert [(a["href"], a.get("lang"), a["text"]) for a in page.all("a", class_="language")] == [
        ("../en/index.html", "en", "English"),
        ("../index.html", None, "选择语言"),
    ]
    # A size stays whole on its line.
    assert ".size{white-space:nowrap}" in html
    assert html.count('<span class="size"> · ') == 6
    assert html.count('）<span class="size">· ') == 5
    # Nothing promises a download of a film or a cover, which a browser opening a file from disk
    # would not make.
    assert not any("download" in a or "下载" in a["text"] for a in files[:6])


def test_each_film_and_cover_opens_in_a_new_tab_beside_the_player(delivered):
    page = Page(delivery_player.player_page(production.Edition("zh"), "1.3.0"))
    files = page.all("a", class_="file")
    # A click keeps the player and its playback, and the new tab has no hold on the player.
    assert [(a.get("target"), a.get("rel")) for a in files[:6]] == [("_blank", "noopener")] * 6
    # A download saves its data where the page stands, opening no tab.
    assert [(a.get("target"), a.get("rel")) for a in files[6:]] == [(None, None)] * 5


def test_the_english_player_speaks_english_and_names_chinese_in_chinese(delivered):
    html = delivery_player.player_page(production.Edition("en"), "2.0.0")
    page = Page(html)
    assert page.all("html")[0]["lang"] == "en"
    runtime = f"{specification.DURATION // 60:02d}:{specification.DURATION % 60:02d}"
    byline = f"{specification.AUTHOR} · English · Version 2.0.0 · {runtime} · 60 fps"
    assert page.all("header")[0]["text"] == f"A <Reel> & Co{byline}中文Choose a language"
    [track] = page.all("track")
    assert (track["kind"], track["srclang"], track["label"]) == (
        "metadata",
        "en",
        "English captions",
    )
    assert [a["text"] for a in page.all("a", class_="file")][:4] == [
        "Film · Viewing edition 1080p · captions in the picture · MP4 · 203 MB",
        "Film · Viewing edition 1080p · no captions · MP4 · 199 MB",
        "Film · 4K UHD · captions in the picture · MP4 · 263 MB",
        "Film · 4K UHD · no captions · MP4 · 241 MB",
    ]
    [control] = page.all("button", id="captions")
    assert (control["text"], control["data-on"], control["data-off"]) == (
        "Captions: on",
        ": on",
        ": off",
    )
    edition = production.Edition("en")
    vtt = (edition.artifacts / "sample-reel-en.vtt").stat().st_size
    srt = (edition.artifacts / "sample-reel-en.srt").stat().st_size
    assert [a["text"] for a in page.all("a", class_="file")][6:] == [
        "Transcript (Markdown, download) · 9 KB",
        "Chapters (JSON, download) · 404 B",
        "Chapters (FFmetadata, download) · 469 B",
        f"Captions (WebVTT, download for other players) · {vtt} B",
        f"Captions (SRT, download for other players) · {srt} B",
    ]
    assert "Downloads" in [h["text"] for h in page.all("h3")]
    assert [(a["href"], a.get("lang"), a["text"]) for a in page.all("a", class_="language")] == [
        ("../zh/index.html", "zh-CN", "中文"),
        ("../index.html", None, "Choose a language"),
    ]
    # The only Chinese text names the Chinese edition, and an apostrophe is a typographic one.
    assert re.findall(r"[\u3000-\u303f\u3400-\u9fff\uff00-\uffef]+", html) == ["中文"]
    status = page.all("p", id="playback-status")[0]["data-unplayable"]
    assert "your system’s player" in status
    assert "'" not in status


def test_an_absent_film_is_listed_without_a_size_and_the_binding_names_what_the_page_shows(
    delivered,
):
    edition = production.Edition("zh")
    edition.film("uhd").unlink()
    page = Page(delivery_player.player_page(edition, "1.3.0"))
    assert [a["text"] for a in page.all("a", class_="file")][
        2
    ] == "影片 · 超高清 4K · 画面内含字幕 · MP4"
    binding = delivery_player.player_binding(edition)
    declared = {"summary": FILM.editions["zh"].summary, "player": FILM.player.model_dump()}
    assert binding["declaration_sha256"] == repository.content_sha(
        json.dumps(declared, ensure_ascii=False, sort_keys=True)
    )
    assert binding["files"][:4] == [
        {"path": "sample-reel-zh-1080p-captioned.mp4", "bytes": 203_312_000},
        {"path": "sample-reel-zh-1080p-uncaptioned.mp4", "bytes": 198_700_000},
        {"path": "sample-reel-zh-uhd.mp4", "bytes": None},
        {"path": "sample-reel-zh-uhd-uncaptioned.mp4", "bytes": 241_400_000},
    ]
    vtt = (edition.artifacts / "sample-reel-zh.vtt").stat().st_size
    assert {"path": "sample-reel-zh.vtt", "bytes": vtt} in binding["files"]


def test_packaging_writes_the_engines_player_and_records_what_it_shows(tmp_path, monkeypatch):
    edition = production.Edition("zh")
    sample = repository.ROOT
    script = repository.read(edition.script)
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    sources = (edition.script, production.Edition("en").script, edition.cover)
    for path in (*sources, delivery_packaging.INDEX, COMPOSITION_SCRIPT):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sample / path, tmp_path / path)
    # A timeline as assembly writes it: each scene's times beside its script fields.
    segments = []
    for index, scene in enumerate(script["segments"]):
        start = 12.0 * index
        voice = {"voice_start": start + 2, "voice_end": start + 10, "gap_kind": "thought"}
        segments.append({**scene, "start": start, "end": start + 12, **voice})
    duration, fps = specification.DURATION, specification.FPS
    timeline = {"title": script["title"], "duration": duration, "fps": fps, "segments": segments}
    timeline["captions"] = [{"start": 2.0, "end": 3.0, "text": "旁白。", "segment": "01"}]
    repository.write(edition.timeline, timeline)
    captions_documents.subtitle_files(timeline, edition)
    (tmp_path / "VERSION").write_text("1.3.0\n")
    delivery_packaging.package_metadata(edition)
    page = (edition.artifacts / "index.html").read_text()
    assert page == delivery_player.player_page(edition, "1.3.0")
    record = repository.read(edition.viewing_package)
    assert record["player"] == delivery_player.player_binding(edition)
    # The record names the version that both pages name.
    assert record["version"] == "1.3.0"
    entry = (tmp_path / delivery_packaging.LANGUAGE_INDEX).read_text()
    assert '<span lang="en">Version</span> 1.3.0</p>' in entry
    assert "player_source_sha256" not in record


def test_packaging_refuses_a_player_page_left_in_the_sources(tmp_path, monkeypatch):
    edition = production.Edition("en")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    (tmp_path / edition.sources).mkdir(parents=True)
    (tmp_path / edition.sources / "player.html").write_text("<html></html>")
    with pytest.raises(delivery_packaging.PackagingError) as refusal:
        delivery_packaging.package_metadata(edition)
    assert "content/en/player.html" in str(refusal.value)
    assert "editions.<code>.summary" in str(refusal.value) and "[player]" in str(refusal.value)
    assert not (tmp_path / "build").exists()
