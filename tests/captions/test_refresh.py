"""Caption refresh keeps the assembled waveform and rebinds the cues to the current script."""

import hashlib
import json
import re

import pytest

import filmkit.captions.documents as captions_documents
import filmkit.captions.refresh as captions_refresh
import filmkit.produce as produce
import filmkit.production as production
import filmkit.repository as repository
import filmkit.review.round as review_round

WORDS = (("甲", 2.0, 2.4), ("乙", 2.4, 2.8), ("丙", 3.4, 3.8), ("丁", 3.8, 4.2))


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))


def stage(tmp_path, monkeypatch, code, groups, words, captions=()):
    """Stage an assembled edition: script, cast, timeline, waveform, receipt and selection."""
    release = repository.read(production.Edition(code).script)["release"]
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition(code)
    text = "".join(groups)
    segment = {
        "id": "01",
        "chapter": "a",
        "chapter_title": "A",
        "title": "Scene 01",
        "utterance_groups": list(groups),
        "text": text,
        "spoken_text": text,
    }
    script = {
        "title": "Sample Reel",
        "caption_timing": {"tail_seconds": 0.25, "short_cue_lead_seconds": 0.1},
        "release": release,
        "segments": [segment],
    }
    write_json(tmp_path / edition.script, script)
    write_json(tmp_path / edition.cast, {"narration_language": "Chinese"})
    timed = {
        **segment,
        "start": 0.0,
        "voice_start": 2.0,
        "voice_end": 4.3,
        "gap_before": 2.0,
        "gap_kind": "opening",
        "words": [{"text": word, "start": start, "end": end} for word, start, end in words],
        "end": 6.0,
    }
    timeline = {
        **script,
        "segments": [timed],
        "timing_state": "Assembled",
        "captions": list(captions),
    }
    write_json(edition.timeline, timeline)
    edition.soundtrack.write_bytes(b"RIFF narration")
    write_json(
        edition.audio_assembly,
        {
            "script_sha256": sha256(tmp_path / edition.script),
            "soundtrack_sha256": sha256(edition.soundtrack),
            "caption_count": 0,
            "alignment_limits": "Model-aligned words",
            "caption_timing": "Timed",
            "captions_above_reading_rate": [],
        },
    )
    write_json(
        edition.narration_selected,
        {
            "records": [{"id": "01", "text": text}],
            "script_sha256": "0" * 64,
            "cast_sha256": sha256(tmp_path / edition.cast),
        },
    )
    return edition


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """An assembled Chinese edition of two thoughts."""
    return stage(tmp_path, monkeypatch, "zh", ["甲乙。", "丙丁。"], WORDS)


def read(path) -> dict:
    return json.loads(path.read_text())


def revise_script(edition, change) -> None:
    path = repository.ROOT / edition.script
    script = read(path)
    change(script)
    write_json(path, script)


def test_a_current_edition_refreshes_its_cues_and_its_selection_binding(edition, capsys):
    captions_refresh.refresh_captions(edition)
    timeline, receipt = read(edition.timeline), read(edition.audio_assembly)
    assert [cue["text"] for cue in timeline["captions"]] == ["甲乙。", "丙丁。"]
    assert timeline["captions"][0]["start"] == 2.0
    assert receipt["caption_count"] == 2
    assert list(receipt)[-4:] == [
        "caption_count",
        "alignment_limits",
        "caption_timing",
        "captions_above_reading_rate",
    ]
    # A Chinese edition has no reading rate, so no cue stands above one.
    assert receipt["captions_above_reading_rate"] == []
    assert receipt["caption_timing"].startswith("Nonoverlapping exact word-bound semantic cues")
    script_sha256 = sha256(repository.ROOT / edition.script)
    assert read(edition.narration_selected)["script_sha256"] == script_sha256
    assert (
        (edition.artifacts / f"{edition.prefix}.srt").read_text().startswith("1\n00:00:02,000 --> ")
    )
    assert json.loads(capsys.readouterr().out)["caption_count"] == 2


def test_a_presentation_revision_records_what_it_replaces(edition):
    before = {
        "script": sha256(repository.ROOT / edition.script),
        "timeline": sha256(edition.timeline),
        "receipt": sha256(edition.audio_assembly),
    }
    phrases = ["甲乙。", "丙丁。"]
    revise_script(edition, lambda script: script["segments"][0].update(caption_phrases=phrases))
    captions_refresh.refresh_captions(edition)
    receipt, timeline = read(edition.audio_assembly), read(edition.timeline)
    script_sha256 = sha256(repository.ROOT / edition.script)
    assert receipt["script_sha256"] == script_sha256
    assert receipt["caption_revision"] == {
        "previous_script_sha256": before["script"],
        "previous_timeline_sha256": before["timeline"],
        "previous_audio_assembly_sha256": before["receipt"],
        "script_sha256": script_sha256,
        "soundtrack_sha256": sha256(edition.soundtrack),
        "scope": (
            "Only authored visual and caption presentation changed; "
            "source copy, words and PCM preserved"
        ),
    }
    assert timeline["segments"][0]["caption_phrases"] == phrases
    assert list(receipt)[-1] == "caption_revision"


def test_a_presentation_revision_requires_the_assembled_waveform(edition):
    revise_script(edition, lambda script: script["segments"][0].update(visual_events=[]))
    edition.soundtrack.write_bytes(b"RIFF another narration")
    with pytest.raises(ValueError, match="requires the exact assembled waveform"):
        captions_refresh.refresh_captions(edition)


def test_a_copy_change_needs_a_new_assembly(edition):
    revise_script(
        edition,
        lambda script: script["segments"][0].update(
            text="甲己。丙丁。", spoken_text="甲己。丙丁。", utterance_groups=["甲己。", "丙丁。"]
        ),
    )
    with pytest.raises(ValueError, match="requires the exact current script and waveform"):
        captions_refresh.refresh_captions(edition)


def test_a_refresh_refuses_a_selection_of_other_copy(edition):
    selected = read(edition.narration_selected)
    selected["records"][0]["text"] = "甲。"
    write_json(edition.narration_selected, selected)
    with pytest.raises(ValueError, match="Selected narration differs"):
        captions_refresh.refresh_captions(edition)


def test_a_refresh_over_a_reviewed_build_waits_for_its_set_aside(edition):
    # The packaged build, whose films round 7's prompts and reviews bind.
    for path in (*edition.films, edition.picture, edition.film_package):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode())
    media = [{"path": str(film), "sha256": sha256(film)} for film in edition.films]
    folder = repository.ROOT / "build/evidence/reviews/round-7"
    write_json(
        folder / "review-zh.json", {"reviewer": "Reviewer", "editions": {"zh": {"media": media}}}
    )
    named = "".join(f"- {item['path']} (SHA-256 {item['sha256']})\n" for item in media)
    (folder / "prompt-zh.md").write_text(named)
    written = {path: path.read_bytes() for path in (edition.timeline, edition.audio_assembly)}
    refusal = "refresh-captions: the current zh films are bound by the prompts of review round 7"
    with pytest.raises(SystemExit, match=re.escape(refusal)):
        produce.main(["refresh-captions", "--language", "zh"])
    assert {path: path.read_bytes() for path in written} == written
    review_round.main(
        ["set-aside", "--round", "7", "--purpose", "caption repairs", "--language", "zh"]
    )
    produce.main(["refresh-captions", "--language", "zh"])
    assert [cue["text"] for cue in read(edition.timeline)["captions"]] == ["甲乙。", "丙丁。"]


# An English edition assembled before cues were typeset: each cue's text is the script's, and a
# cue with a straight mark carries its display copy beside it.
ENGLISH_GROUPS = ["It isn't done. ", 'The film\'s record says "Done."']
ENGLISH_WORDS = (
    ("It", 2.0, 2.2),
    ("isn't", 2.2, 2.6),
    ("done.", 2.6, 3.2),
    ("The", 3.8, 3.9),
    ("film's", 3.9, 4.3),
    ("record", 4.3, 4.7),
    ("says", 4.7, 5.0),
    ('"Done."', 5.0, 5.6),
)
ENGLISH_CUES = [(2.0, 3.45, "It isn’t done. "), (3.8, 5.85, "The film’s record says “Done.”")]


def test_a_refresh_typesets_the_cues_and_keeps_the_subtitles(tmp_path, monkeypatch):
    before = [
        {"start": start, "end": end, "text": text, "segment": "01", "display_text": shown}
        for (start, end, shown), text in zip(ENGLISH_CUES, ENGLISH_GROUPS, strict=True)
    ]
    edition = stage(tmp_path, monkeypatch, "en", ENGLISH_GROUPS, ENGLISH_WORDS, before)
    edition.artifacts.mkdir(parents=True, exist_ok=True)
    captions_documents.subtitle_files(read(edition.timeline), edition)
    subtitles = [edition.artifacts / f"{edition.prefix}.{kind}" for kind in ("srt", "vtt")]
    written = [path.read_bytes() for path in subtitles]
    captions_refresh.refresh_captions(edition)
    timeline = read(edition.timeline)
    # Each cue now holds the text it shows, and no cue holds a straight mark.
    assert timeline["captions"] == [
        {"start": start, "end": pytest.approx(end), "text": text, "segment": "01"}
        for start, end, text in ENGLISH_CUES
    ]
    assert not any(mark in cue["text"] for cue in timeline["captions"] for mark in "'\"")
    # The subtitles are the same bytes, and their lines are the cues' text.
    assert [path.read_bytes() for path in subtitles] == written
    lines = subtitles[0].read_text().splitlines()
    assert [lines[2], lines[6]] == [text.strip() for _, _, text in ENGLISH_CUES]
    # The narration, its thoughts and its aligned words stay the script's and the aligner's.
    script = read(repository.ROOT / edition.script)["segments"][0]
    timed = timeline["segments"][0]
    assert all(timed[key] == value for key, value in script.items())
    assert [word["text"] for word in timed["words"]] == [word for word, _, _ in ENGLISH_WORDS]
    assert read(edition.audio_assembly)["captions_above_reading_rate"] == []
