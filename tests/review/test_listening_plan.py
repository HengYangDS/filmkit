"""Exercise the pronunciation listening plan on the current scripts and on small fixtures."""

import json
import re
import wave

import numpy as np
import pytest

import filmkit.repository as repository
import filmkit.review.listening_plan as review_listening_plan
from filmkit.film import FILM
from filmkit.production import Edition
from filmkit.review import ReviewError
from filmkit.review.listening_plan import Readings

CONTRACT = "content/voice-performance.json"


def test_the_listening_plan_derives_for_the_current_scripts(tmp_path):
    # Every heteronym occurrence of the current scripts has its part of speech recorded in
    # the film's readings, so a script edit cannot reach the review with a stale reading table.
    plan = review_listening_plan.listening_plan(tmp_path / "plan.json")
    assert plan["occurrences"]["zh"] > 0
    assert plan["occurrences"]["en"] > 0
    written = json.loads((tmp_path / "plan.json").read_text())
    contract = repository.read(Edition("zh").script)["pronunciation_contract"]
    assert written["derived_from"] == {"path": contract, "sha256": repository.sha(contract)}
    assert set(written["heard_moments"]) == {"zh", "en"}


def test_listening_plan_binds_each_occurrence_and_refuses_unrecorded_readings(root, put):
    noun, verb = (
        review_listening_plan.arpabet("Y UW1 S", 1),
        review_listening_plan.arpabet("Y UW1 Z", 1),
    )
    english = [
        {
            "term": "use",
            "kind": "contextual-homograph",
            "lexical_stress": {"noun": noun, "verb": verb},
        },
        {
            "term": "data",
            "kind": "lexical",
            "lexical_stress": review_listening_plan.arpabet("D EY1 T AH0", 1),
        },
    ]
    chinese = [{"term": "调度", "kind": "contextual-mandarin-word", "target_reading": "diàodù"}]
    contract = {
        "sources": [{"id": "cmudict"}],
        "control_boundary": "Targets are acceptance criteria.",
        "acceptance": ["Listen to each occurrence in its clause."],
        "languages": {"Chinese": {"targets": chinese}, "English": {"targets": english}},
    }
    put(root / CONTRACT, {"pronunciation": contract})
    scripts = {
        "zh": ["先看调度。", "再改调度表，重新跑。"],
        "en": ["We use data. ", "Data takes the lead."],
    }
    for code, groups in scripts.items():
        script, cast = Edition(code).script, Edition(code).cast
        segment = {"id": "01", "text": "".join(groups), "utterance_groups": groups}
        put(root / script, {"pronunciation_contract": CONTRACT, "segments": [segment]})
        put(
            root / cast,
            {
                "reference_audio": f"assets/{code}.wav",
                "reference_sha256": "a" * 64,
                "reference_text_sha256": "b" * 64,
            },
        )
    put(root / "content/source-manifest.json", {"members": []})
    lead = {"noun": review_listening_plan.arpabet("L IY1 D", 1)}
    readings = {
        "mandarin": {"重新": "chóngxīn"},
        "heteronyms": {"lead": {"noun": {"phones": "L IY1 D", "primary": 1}}},
        "grammar": {"use": {"01:3": "verb"}, "lead": {"01:28": "noun"}},
    }
    put(root / FILM.review.readings, readings)
    out = root / "plan.json"
    assert review_listening_plan.listening_plan(out) == {
        "output": "plan.json",
        "occurrences": {"zh": 3, "en": 4},
        "english_targets": 3,
    }
    plan = json.loads(out.read_text())
    entries = plan["occurrence_plan"]["entries"]
    assert [(e["locale"], e["display_span"], e["grammar"], e["clause"]) for e in entries] == [
        ("zh", [2, 4], "contextual-mandarin-word", "先看调度。"),
        ("zh", [7, 9], "contextual-mandarin-word", "再改调度表，重新跑。"),
        ("zh", [11, 13], "contextual-mandarin-word", "再改调度表，重新跑。"),
        ("en", [3, 6], "verb", "We use data. "),
        ("en", [7, 11], "lexical", "We use data. "),
        ("en", [13, 17], "lexical", "Data takes the lead."),
        ("en", [28, 32], "noun", "Data takes the lead."),
    ]
    assert entries[2]["target_reading"] == "chóngxīn"
    assert entries[3]["target_stress"] == verb
    assert entries[6]["target_stress"] == lead["noun"]
    assert {e["status"] for e in entries} == {"planned-not-listened"}
    assert plan["languages"]["English"]["targets"][-1]["source"] == "analyst-inference"
    assert {"id": "analyst-inference", "qualification": review_listening_plan.BASIS} in plan[
        "sources"
    ]
    assert plan["languages"]["Chinese"]["targets"][-1]["source"] == "analyst-mandarin"
    assert [binding["sha256"] for binding in plan["script_bindings"]] == [
        repository.sha(root / "content/film-script.json"),
        repository.sha(root / "content/en/film-script.json"),
    ]
    assert plan["derived_from"] == {"path": CONTRACT, "sha256": repository.sha(root / CONTRACT)}

    put(root / FILM.review.readings, {**readings, "grammar": {"lead": {"01:28": "noun"}}})
    with pytest.raises(ReviewError, match="use at 01:3: record its part of speech"):
        review_listening_plan.listening_plan(out)
    grammar = {"use": {"01:3": "verb"}, "lead": {"01:28": "noun", "01:40": "verb"}}
    put(root / FILM.review.readings, {**readings, "grammar": grammar})
    stale = re.escape("no current occurrence: {'lead': ['01:40']}")
    with pytest.raises(ReviewError, match=stale):
        review_listening_plan.listening_plan(out)
    # The command reports its refusals, and lets any other fault show in full.
    with pytest.raises(SystemExit, match=f"listening plan: recorded parts of speech name {stale}"):
        review_listening_plan.main(["--out", str(out)])
    put(root / CONTRACT, "{")
    with pytest.raises(json.JSONDecodeError):
        review_listening_plan.main(["--out", str(out)])


def test_scripts_that_name_different_contracts_refuse_the_plan(root, put):
    for code in ("zh", "en"):
        script = {"pronunciation_contract": f"content/{code}-contract.json", "segments": []}
        put(root / Edition(code).script, script)
    with pytest.raises(ReviewError, match="different pronunciation contracts"):
        review_listening_plan.listening_plan(root / "plan.json")


def test_an_extra_variant_is_labelled_only_where_it_is_added():
    # A dictionary reading is kept as its source states it; only an added variant is the
    # analyst's inference.
    noun = review_listening_plan.arpabet("Y UW1 S IH0 Z", 1, weak=[2])
    dictionary = {**review_listening_plan.arpabet("Y UW1 Z IH0 Z", 1, weak=[2]), "basis": "CMU"}
    added = review_listening_plan.arpabet("Y UW1 Z IH0 Z", 1, weak=[2])
    variant = {"verb": {"phones": "Y UW1 Z IH0 Z", "primary": 1, "weak": [2]}}
    readings = Readings.model_validate({"variants": {"uses": variant, "users": variant}})
    targets = [
        {"term": "uses", "kind": "contextual-homograph", "lexical_stress": {"noun": noun}},
        {
            "term": "users",
            "kind": "contextual-homograph",
            "lexical_stress": {"noun": noun, "verb": dictionary},
        },
    ]
    contract = {
        "sources": [],
        "languages": {"Chinese": {"targets": []}, "English": {"targets": targets}},
    }
    extended, kept = review_listening_plan.analyst_contract(contract, readings)["languages"][
        "English"
    ]["targets"]
    assert extended["lexical_stress"] == {"noun": noun, "verb": added}
    assert extended["variant_sources"] == {"verb": "analyst-inference"}
    assert kept["lexical_stress"] == {"noun": noun, "verb": dictionary}
    assert "variant_sources" not in kept


def test_an_occurrence_outside_every_thought_is_refused():
    target = {"term": "调度", "kind": "contextual-mandarin-word", "target_reading": "diàodù"}
    segment = {"id": "07", "text": "先看调度。", "utterance_groups": ["先看"]}
    with pytest.raises(ReviewError, match="07: 调度 at 2 lies outside every thought"):
        review_listening_plan.target_entries("zh", target, [segment], {})


def test_the_plan_names_the_pauses_and_steps_of_each_assembled_soundtrack(root, put):
    # 0.3 s of quiet between 据 and 再, where the text has no mark, stays within 0.4 s.
    words = [("先", 0.2, 0.4), ("看", 0.4, 0.6), ("数", 0.6, 0.8), ("据", 0.8, 1.0)]
    words += [("再", 1.3, 1.5), ("决", 1.5, 1.7), ("定", 1.7, 1.9)]
    edition = Edition("zh")
    put(root / edition.script, {"segments": []})
    segment = {"id": "01", "text": "先看数据再决定。", "utterance_groups": ["先看数据再决定。"]}
    segment["words"] = [{"text": text, "start": start, "end": end} for text, start, end in words]
    put(edition.timeline, {"segments": [segment]})
    mono = np.zeros(round(2.2 * 48000))
    for _, start, end in words:
        span = np.arange(round(start * 48000), round(end * 48000))
        mono[span] = 9000 * np.sin(2 * np.pi * 200 * span / 48000)
    with wave.open(str(edition.soundtrack), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(48000)
        audio.writeframes(np.repeat(mono, 2).astype("<i2").tobytes())
    moments = review_listening_plan.heard_moments(edition)
    assert moments["status"] == "planned-not-listened"
    assert moments["soundtrack"]["sha256"] == repository.sha(edition.soundtrack)
    assert [
        (row["thought"], row["left"], row["right"], row["pause_s"]) for row in moments["pauses"]
    ] == [("01.1", "据", "再", 0.3)]
    assert moments["steps"] == {"rate_ratio": [], "pitch_semitones": [], "level_db": []}
    assert moments["narration_terms"] == []
    assert review_listening_plan.heard_moments(Edition("en")) == {"status": "not-assembled"}
