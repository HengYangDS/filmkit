"""An assembled edition below a scratch root, as the caption refresh and the picture's staging read
it: its script, cast, timeline, waveform, receipt and selection."""

import hashlib
import json
from pathlib import Path

import derived_languages

import filmkit.production as production
import filmkit.repository as repository

# The sample film, whose release the staged scripts declare.
SAMPLE = Path(__file__).resolve().parents[1] / "examples/sample-film"


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))


def stage(tmp_path, monkeypatch, code, groups, words, captions=()):
    """Stage an assembled edition: script, cast, timeline, waveform, receipt and selection. A
    test language's edition takes the release of the sample's edition it derives from."""
    source = derived_languages.DERIVED.get(code, (code,))[0]
    release = json.loads((SAMPLE / production.Edition(source).script).read_text())["release"]
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
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
    write_json(tmp_path / edition.cast, {})
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
    # What an assembly writes beside and over the script's keys (`production.ASSEMBLED`).
    timeline = {
        **script,
        "edition": edition.code,
        "duration": 9,
        "credits_duration": 3.0,
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
