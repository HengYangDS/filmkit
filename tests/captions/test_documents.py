"""Subtitle documents: the captions, chapters, transcript and chapter metadata of an edition."""

import json

import pytest

import filmkit.captions.documents as captions_documents
import filmkit.captions.timing as captions_timing
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification


@pytest.mark.parametrize(
    ("code", "byline"),
    [("zh", "Yang HENG · 中文 · 1 分钟"), ("en", "Yang HENG · English · 1 min")],
)
def test_chapters_land_on_their_cards_and_head_the_transcript(tmp_path, monkeypatch, code, byline):
    release = repository.read(production.Edition(code).script)["release"]
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition(code)
    repository.write(edition.script, {"release": release})
    edition.artifacts.mkdir(parents=True)

    def segment(sid, chapter, title, start):
        return {
            "id": sid,
            "chapter": chapter,
            "chapter_title": title,
            "title": f"Scene {sid}",
            "start": start,
            "voice_start": start + 1.8,
            "text": f"Text {sid}. More {sid}.",
            "utterance_groups": [f"Text {sid}. ", f"More {sid}."],
        }

    timeline = {
        "title": "Sample Reel",
        "captions": [{"start": 1.9, "end": 3.0, "text": "Text 01. "}],
        "segments": [
            segment("01", "purpose", "One", 0.0),
            segment("02", "purpose", "One", 15.0),
            segment("03", "decide", "Two", 30.0),
        ],
    }
    timeline["segments"][2]["utterance_groups"] = ["Text 03 isn't done."]
    captions_documents.subtitle_files(timeline, edition)
    output = edition.artifacts
    chapters = json.loads((output / "chapters.json").read_text())["chapters"]
    # The second chapter starts once its card is shown, after its scene starts.
    second = 30.0 + specification.CHAPTER_CARD_SHOWN
    assert [(c["title"], c["start"]) for c in chapters] == [("One", 0.0), ("Two", second)]
    metadata = (output / "chapters.ffmeta").read_text()
    assert f"START={round(second * 1000)}\n" in metadata
    assert f"END={specification.DURATION * 1000}\n" in metadata
    assert f"comment={edition.comment}\n" in metadata
    assert ("示例影片" in metadata) == (code == "zh")
    for name in (f"{edition.prefix}.srt", f"{edition.prefix}.vtt"):
        lines = (output / name).read_text().splitlines()
        assert "Text 01." in lines
        assert all(line == line.rstrip() for line in lines)
    transcript = (output / f"{edition.prefix}-transcript.md").read_text()
    assert transcript.splitlines()[2] == byline
    assert transcript.count("\n## ") == 2
    # A chapter is headed by its start and a scene by its voice start, as m:ss, and each
    # thought is a paragraph.
    assert "\n## 0:00 · 01 One\n\n### 0:01 · Scene 01\n\nText 01.\n\nMore 01.\n" in transcript
    assert "\n## 0:30 · 02 Two\n\n### 0:31 · Scene 03\n" in transcript
    # Display copy sets an apostrophe as a typographic right single quote.
    assert "Text 03 isn’t done." in transcript
    assert captions_timing.typeset("Others' work isn't done") == "Others’ work isn’t done"


def test_titles_headings_and_chapters_set_typographic_quotes(tmp_path, monkeypatch):
    # The transcript, its player and the chapter carriers set quotes as the captions do.
    release = repository.read(production.Edition("en").script)["release"]
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition("en")
    repository.write(edition.script, {"release": {**release, "comment": 'It says "Done".'}})
    edition.artifacts.mkdir(parents=True)
    segment = {
        "id": "01",
        "chapter": "life",
        "chapter_title": "One requirement's life",
        "title": '"Done"',
        "start": 0.0,
        "voice_start": 1.8,
        "text": 'It says "Done."',
        "utterance_groups": ['It says "Done."'],
    }
    timeline = {"title": 'The "Sample" Reel', "captions": [], "segments": [segment]}
    captions_documents.subtitle_files(timeline, edition)
    output = edition.artifacts
    transcript = (output / f"{edition.prefix}-transcript.md").read_text()
    assert transcript.startswith("# The “Sample” Reel\n")
    assert "\n## 0:00 · 01 One requirement’s life\n\n### 0:01 · “Done”\n\nIt says “Done.”\n" in (
        transcript
    )
    chapters = json.loads((output / "chapters.json").read_text())["chapters"]
    assert chapters[0]["title"] == "One requirement’s life"
    metadata = (output / "chapters.ffmeta").read_text()
    assert "title=The “Sample” Reel\n" in metadata
    assert "comment=It says “Done”.\n" in metadata
    assert "title=One requirement’s life\n" in metadata
    assert '"' not in transcript + metadata and "'" not in transcript + metadata


def test_chinese_titles_keep_their_marks(tmp_path, monkeypatch):
    release = repository.read(production.Edition("zh").script)["release"]
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition("zh")
    repository.write(edition.script, {"release": release})
    edition.artifacts.mkdir(parents=True)
    segment = {
        "id": "01",
        "chapter": "question",
        "chapter_title": "问题",
        "title": "“做完了”",
        "start": 0.0,
        "voice_start": 1.8,
        "text": "它交回一句话：“做完了。”",
        "utterance_groups": ["它交回一句话：“做完了。”"],
    }
    timeline = {"title": "示例影片", "captions": [], "segments": [segment]}
    captions_documents.subtitle_files(timeline, edition)
    transcript = (edition.artifacts / f"{edition.prefix}-transcript.md").read_text()
    assert "### 0:01 · “做完了”\n\n它交回一句话：“做完了。”\n" in transcript


def test_timecodes_round_to_the_millisecond():
    assert captions_documents.timecode(3723.4567) == "01:02:03,457"
    assert captions_documents.timecode(59.9996, ".") == "00:01:00.000"


def test_a_player_time_is_minutes_and_whole_seconds_with_hours_past_an_hour():
    clock = captions_documents.clock
    assert [clock(0), clock(2.872), clock(59.999), clock(600), clock(1499.5)] == [
        "0:00",
        "0:02",
        "0:59",
        "10:00",
        "24:59",
    ]
    assert [clock(3599.9), clock(3600), clock(3725.2)] == ["59:59", "1:00:00", "1:02:05"]


def test_the_transcript_parts_give_each_chapter_its_scenes_and_each_scene_its_thoughts():
    segments = [
        {
            "id": sid,
            "chapter": chapter,
            "chapter_title": title,
            "title": f"Scene {sid}",
            "start": start,
            "voice_start": start + 2.8721,
            "utterance_groups": [f"One {sid}. ", f"Two {sid}'s."],
        }
        for sid, chapter, title, start in (
            ("01", "a", "Ay", 0.0),
            ("02", "a", "Ay", 20.0),
            ("03", "b", "Bee", 40.0),
        )
    ]
    parts = captions_documents.transcript_parts(segments)
    assert [(c.number, c.title, c.start) for c in parts] == [
        (1, "Ay", 0.0),
        (2, "Bee", 40.0 + specification.CHAPTER_CARD_SHOWN),
    ]
    assert [[(s.title, s.start) for s in c.sections] for c in parts] == [
        [("Scene 01", 2.872), ("Scene 02", 22.872)],
        [("Scene 03", 42.872)],
    ]
    assert parts[1].sections[0].paragraphs == ("One 03.", "Two 03’s.")
