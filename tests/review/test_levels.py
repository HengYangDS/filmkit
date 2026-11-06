"""A review passes level by level and judges every sentence, for a film that declares its levels."""

import json
import re

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.rendering as picture_rendering
import filmkit.review.prompts as review_prompts
import filmkit.review.record as review_record
import filmkit.review.round as review_round
import filmkit.sources as sources
from filmkit.delivery.verification import VerificationError
from filmkit.film import FILM, Level
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

# The sample film's dimensions in three levels.
LEVELS = {
    "信": Level(asks="true", dimensions=("subject_and_faithfulness", "concept_fidelity")),
    "达": Level(asks="understood", dimensions=("narration_and_language", "picture_and_sync")),
    "雅": Level(asks="graceful", dimensions=("deliverable_craft",)),
}
# Each edition's sentences, as its timeline gives them.
SENTENCES = ["01.1.1", "01.2.1", "02.1.1"]


@pytest.fixture
def leveled(monkeypatch):
    """The sample film with three review levels, whose editions each hold three sentences."""
    review = FILM.review.model_copy(update={"levels": LEVELS})
    monkeypatch.setattr(review_record, "LEVELS", review.levels)
    monkeypatch.setattr(review_record, "sentence_ids", lambda edition: list(SENTENCES))


def passing(**changes):
    """A review entry that passes every level and judges every sentence."""
    return {
        "levels": {name: {"verdict": "pass", "findings": []} for name in LEVELS},
        "sentences": dict.fromkeys(SENTENCES, "ok"),
    } | changes


def finding(name, level, severity="minor"):
    return {"id": name, "severity": severity, "level": level}


@pytest.mark.usefixtures("leveled")
def test_a_review_passes_only_level_by_level():
    scores = dict.fromkeys(review_record.DIMENSIONS, 96)
    assert review_record.level_problems(passing(), scores, []) == []
    # A level that fails, one that is missing, and one passed by averaging all refuse.
    failing = passing()["levels"] | {"达": {"verdict": "fail", "findings": ["R1"]}}
    assert review_record.level_problems(
        passing(levels=failing), scores, [finding("R1", "达", "material")]
    ) == ["达 fails"]
    missing = {name: verdict for name, verdict in passing()["levels"].items() if name != "雅"}
    assert review_record.level_problems(passing(levels=missing), scores, []) == [
        "no verdict for level 雅"
    ]
    low = scores | {"deliverable_craft": 93}
    assert review_record.level_problems(passing(), low, []) == [
        "雅 passes with deliverable_craft at 93, below the floor of 95"
    ]
    # A material finding in a level that passes contradicts its verdict, and every finding names a
    # level among the levels and stands in its level's findings.
    material = [finding("R2", "信", "material")]
    held = passing()["levels"] | {"信": {"verdict": "pass", "findings": ["R2"]}}
    assert review_record.level_problems(passing(levels=held), scores, material) == [
        "信 passes with material finding R2"
    ]
    assert review_record.level_problems(passing(), scores, [{"id": "R3", "severity": "note"}]) == [
        "finding R3 names no level"
    ]
    assert review_record.level_problems(passing(), scores, [finding("R4", "雅")]) == [
        "finding R4 is not among the findings of level 雅"
    ]
    assert review_record.level_problems(passing(), scores, [finding("R5", "美")]) == [
        "finding R5 names no level"
    ]


@pytest.mark.usefixtures("leveled")
def test_a_review_judges_every_sentence_once():
    findings = [finding("R1", "达")]
    judged = passing(sentences=dict.fromkeys(SENTENCES, "ok") | {"02.1.1": ["R1"]})
    assert review_record.sentence_problems(judged, findings, Edition("zh")) == []
    left_out = {key: value for key, value in judged["sentences"].items() if key != "01.2.1"}
    assert review_record.sentence_problems(
        passing(sentences=left_out | {"09.1.1": "ok"}), findings, Edition("zh")
    ) == ["no verdict for sentence 01.2.1", "no sentence 09.1.1 in the zh edition"]
    unknown = judged["sentences"] | {"01.1.1": ["R9"], "01.2.1": "fine"}
    assert review_record.sentence_problems(passing(sentences=unknown), findings, Edition("zh")) == [
        "sentence 01.1.1 names finding R9, which the review does not hold",
        "sentence 01.2.1 is neither ok nor a list of finding ids",
    ]


@pytest.mark.usefixtures("unleveled")
def test_a_film_without_levels_keeps_its_reviews():
    assert review_record.LEVELS is None
    assert review_record.level_problems({}, {}, [{"id": "R1", "severity": "minor"}]) == []
    assert review_record.sentence_problems({}, [], Edition("zh")) == []


def test_record_and_the_verifier_accept_a_review_level_by_level(root, review, put, leveled, capsys):
    for code in CODES:
        put(root / Edition(code).script, f"{code} script")
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition")
    folder = root / "build/evidence/reviews/round-5"
    findings = [finding("R5-1", "达")]
    levels = passing()["levels"] | {"达": {"verdict": "pass", "findings": ["R5-1"]}}
    review(folder, "zh", findings=findings, **passing(levels=levels))
    # A finding left out of its level's findings, and a sentence without a verdict, refuse.
    review(folder, "en", findings=findings, **passing())
    with pytest.raises(
        ReviewError,
        match=re.escape("en: the review's levels do not pass: finding R5-1 is not among"),
    ):
        review_round.review_records(folder)
    sentences = dict.fromkeys(SENTENCES[:2], "ok")
    review(folder, "en", findings=findings, **passing(levels=levels, sentences=sentences))
    with pytest.raises(
        ReviewError,
        match=re.escape("en: the review does not judge every sentence: no verdict for sentence"),
    ):
        review_round.review_records(folder)
    review(folder, "en", findings=findings, **passing(levels=levels))
    review_round.main(["record", "--round-dir", str(folder)])
    capsys.readouterr()
    record = json.loads(Edition("zh").production_review.read_text())
    assert record["levels"] == levels
    assert record["sentences"] == dict.fromkeys(SENTENCES, "ok")
    for code in CODES:
        edition = Edition(code)
        accepted = delivery_verification.verify_review(edition, sorted(edition.films))
        assert accepted["levels"] == {"信": "pass", "达": "pass", "雅": "pass"}
    # A record whose level fails, or that misses a sentence, does not verify.
    record["levels"]["雅"] = {"verdict": "fail", "findings": []}
    put(Edition("zh").production_review, record)
    edition = Edition("zh")
    with pytest.raises(VerificationError, match="Review levels do not pass: 雅 fails"):
        delivery_verification.verify_review(edition, sorted(edition.films))
    record["levels"]["雅"] = {"verdict": "pass", "findings": []}
    del record["sentences"]["02.1.1"]
    put(Edition("zh").production_review, record)
    with pytest.raises(
        VerificationError,
        match="Review does not judge every sentence: no verdict for sentence 02.1.1",
    ):
        delivery_verification.verify_review(edition, sorted(edition.films))


def timeline_of(code):
    """An edition's timeline of two segments, three thoughts and three sentences."""
    groups = {
        "zh": (["这部短片演示重建。", "脚本写着要说的话。"], ["构建时先录下旁白。"]),
        "en": (["This film shows a rebuild. ", "The script holds the words."], ["It narrates."]),
    }[code]
    segments = []
    for number, thoughts in enumerate(groups, 1):
        text = "".join(thoughts)
        units = (
            [c for c in text if "\u4e00" <= c <= "\u9fff"]
            if code == "zh"
            else re.findall(r"[A-Za-z]+", text)
        )
        words = [
            {"text": unit, "start": 10 * number + 0.2 * k, "end": 10 * number + 0.2 * k + 0.18}
            for k, unit in enumerate(units)
        ]
        segments.append(
            {"id": f"0{number}", "text": text, "utterance_groups": thoughts, "words": words}
        )
    return {"segments": segments, "captions": []}


def prompted(root, put, monkeypatch, template):
    """Write a first round's prompts from a template for the film with levels."""
    for code in CODES:
        put(
            root / Edition(code).script, {"voice_performance": {"thought_level_tolerance_db": 0.75}}
        )
        put(Edition(code).audio_assembly, {"program_level": {"policy": {"integrated_lufs": -16.5}}})
        put(Edition(code).timeline, timeline_of(code))
    put(
        root / sources.MANIFEST,
        {"repository": "https://example.test/readme", "members": [{"path": "README.md"}]},
    )
    monkeypatch.setenv(sources.CHECKOUT, "/source/readme")
    out = root / "build/evidence/reviews/round-1"
    for name in review_prompts.ROUND_INPUTS:
        put(out / name, {})
    review = FILM.review.model_copy(update={"levels": LEVELS})
    monkeypatch.setattr(review_prompts, "FILM", FILM.model_copy(update={"review": review}))
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    return out


def test_the_prompts_state_each_level_with_its_dimensions_and_name_the_sentences(
    root, put, monkeypatch
):
    template = "{media}\n{concepts} {readings}\nLevels:\n{levels}\nSentences: {sentences}\n"
    out = prompted(root, put, monkeypatch, template)
    review_prompts.prompts(None, out)
    text = (out / "prompt-zh.md").read_text()
    dimensions = FILM.review.dimensions
    assert (
        "Levels:\n- 信: true\n"
        f"  - subject_and_faithfulness: {dimensions['subject_and_faithfulness']}\n"
        f"  - concept_fidelity: {dimensions['concept_fidelity']}\n"
        "- 达: understood\n"
    ) in text
    assert f"- 雅: graceful\n  - deliverable_craft: {dimensions['deliverable_craft']}\n" in text
    assert "Sentences: ROOT/build/evidence/reviews/round-1/sentences-zh.json\n" in text
    written = json.loads((out / "sentences-en.json").read_text())
    assert written == {
        "edition": "en",
        "sentences": [
            {"id": "01.1.1", "text": "This film shows a rebuild.", "start": 10.0, "end": 10.98},
            {"id": "01.2.1", "text": "The script holds the words.", "start": 11.0, "end": 11.98},
            {"id": "02.1.1", "text": "It narrates.", "start": 20.0, "end": 20.38},
        ],
    }


def test_a_template_without_the_levels_or_the_sentences_is_refused(root, put, monkeypatch):
    out = prompted(root, put, monkeypatch, "{media}\n{concepts} {readings}\n{levels}\n")
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(None, out)
    assert str(refusal.value) == (
        "the review omits the levels the film declares: content/review/prompt.md never cites "
        "{sentences}"
    )
    assert not (out / "prompt-zh.md").exists()
    # A film without levels owes neither, and its prompts state none.
    review = FILM.review.model_copy(update={"levels": None})
    monkeypatch.setattr(review_prompts, "FILM", FILM.model_copy(update={"review": review}))
    monkeypatch.setattr(review_prompts, "TEMPLATE", "{media}\n{concepts} {readings}\n{levels}\n")
    review_prompts.prompts(None, out)
    assert not (out / "sentences-zh.json").exists()
    assert (out / "prompt-zh.md").read_text().endswith("none declared\n")


def test_the_sample_film_holds_its_dimensions_in_three_levels_and_cites_both_fields(
    root, put, monkeypatch
):
    levels = FILM.review.levels
    assert list(levels) == ["信", "达", "雅"]
    assert sorted(name for level in levels.values() for name in level.dimensions) == sorted(
        FILM.review.dimensions
    )
    assert review_prompts.level_gaps(review_prompts.TEMPLATE) == []
    out = prompted(root, put, monkeypatch, review_prompts.TEMPLATE)
    monkeypatch.setattr(review_prompts, "FILM", FILM)
    review_prompts.prompts(None, out)
    text = (out / "prompt-zh.md").read_text()
    for name, level in levels.items():
        assert f"- {name}: {level.asks}\n" in text
    assert "ROOT/build/evidence/reviews/round-1/sentences-zh.json" in text
    assert not re.search(r"\{[a-z_]+\}", text)
