"""Exercise the reviewer prompts: the media, the previous or a first round, and the policies."""

import re

import pytest

import filmkit.repository as repository
import filmkit.review.prompts as review_prompts
import filmkit.review.record as review_record
import filmkit.review.round as review_round
import filmkit.sources as sources
import filmkit.specification as specification
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError


@pytest.mark.usefixtures("unleveled")
def test_prompts_cite_the_exact_media_previous_findings_and_round_inputs(
    root, review, put, monkeypatch
):
    policies = {
        "zh": {
            "inner_pause_cap_seconds": 0.33,
            "inner_pause_floors_seconds": {"。？！": 0.31, "，": 0.155},
            "inner_breath": {"longest_group_seconds": 7.5, "pause_seconds": 0.26},
            "thought_level_tolerance_db": 0.75,
            "thought_boundary_ratio": 1.2,
            "thought_boundary_margin_seconds": 0.04,
            "coda_thought_pause_seconds": 1.4,
        },
        "en": {
            "inner_pause_cap_seconds": 0.33,
            "inner_pause_caps_seconds": {",": 0.22},
            "thought_level_tolerance_db": 0.75,
            "thought_boundary_ratio": 1.62,
            "coda_thought_pause_seconds": 0.9,
        },
    }
    for code, policy in policies.items():
        put(root / Edition(code).script, {"voice_performance": policy})
        put(
            Edition(code).audio_assembly,
            {"program_level": {"policy": {"integrated_lufs": -16.5}}},
        )
    put(
        root / sources.MANIFEST,
        {
            "repository": "https://example.test/guidelines",
            "commit": "abc",
            "members": [
                {"path": f"docs/{name}.md"}
                for name in (
                    "charter",
                    "decide",
                    "data",
                    "deliver",
                    "human-agent",
                    "communicate",
                    "evolve",
                )
            ],
        },
    )
    monkeypatch.setenv(sources.CHECKOUT, "/source/guidelines")
    previous = root / "build/evidence/reviews/round-4"
    findings = [
        {"id": "R4-1", "severity": "minor"},
        {"id": "R4-2", "severity": "note"},
        {"id": "R4-3", "severity": "note"},
    ]
    review(previous, "zh", findings=findings)
    review(previous, "en")
    (previous / "zh").mkdir()
    out = root / "build/evidence/reviews/round-5"
    changes = put(root / "changes.md", "- Repairs: 07.6 names all seven checks.\n\n")
    disposed = put(
        root / "dispositions.json",
        {
            "round": 4,
            "findings": {
                name: {"disposition": "fixed", "evidence": f"{name} reverified."}
                for name in ("R4-1", "R4-2", "R4-3")
            },
        },
    )
    with pytest.raises(ReviewError, match="missing build/evidence/reviews/round-5/pronun"):
        review_prompts.prompts(previous, out, changes, disposed)
    for name in review_prompts.ROUND_INPUTS:
        put(out / name, {})
    assert review_prompts.prompts(previous, out, changes, disposed) == {
        "prompts": [
            "build/evidence/reviews/round-5/prompt-zh.md",
            "build/evidence/reviews/round-5/prompt-en.md",
        ]
    }
    zh, en = ((out / f"prompt-{code}.md").read_text() for code in CODES)
    uhd = Edition("zh").film("uhd")
    for expected in (
        f"- {uhd} (SHA-256 {repository.sha(uhd)})",
        "and the read-only source /source/guidelines. ",
        (
            "Canonical source: charter, decide, data, deliver, human-agent, communicate, "
            "evolve in /source/guidelines."
        ),
        (
            "ROOT/build/evidence/reviews/round-4/zh-review.md and "
            "ROOT/build/evidence/reviews/round-4/review-zh.json "
            "(findings: minor R4-1; note R4-2, R4-3)."
        ),
        "working files are in ROOT/build/evidence/reviews/round-4/zh/; you may copy",
        (
            "Concept contract: ROOT/content/concepts.toml; judge each concept's words in "
            "narration, captions and picture against it. Reading occurrence plans: "
            "ROOT/build/evidence/readings/zh-plan.json and "
            "ROOT/build/evidence/readings/en-plan.json."
        ),
        "your own output directory.\n- Dispositions of round 4's findings. Re-verify ",
        (
            "    - R4-3: R4-3 reverified.\n  - Declared: none.\n  - Deferred: none.\n"
            "- Repairs: 07.6 names all seven checks.\n- Pause policy the scripts declare:"
        ),
        "Write only under ROOT/build/evidence/reviews/round-5/.",
        "inner pauses at most 0.33 s Chinese; 0.33 s (0.22 s at commas) English;",
        "inner pause floors Chinese 。？！ 0.31 s, ， 0.155 s; English none declared;",
        "breaths Chinese 7.5 s with a 0.26 s pause; English none declared;",
        "ratios and margins 1.2 and 0.04 s Chinese, 1.62 and 0.00 s English;",
        "level tolerances 0.75 dB Chinese, 0.75 dB English;",
        "coda thought pauses 1.40 s Chinese, 0.90 s English.",
        (
            "\n1. subject_and_faithfulness: the rebuild of a film from its sources remains "
            "the subject;"
        ),
        "\n2. concept_fidelity: each concept the film names keeps its source meaning",
        "\n5. deliverable_craft: cover, credits and metadata name the film and its author;",
        "and ROOT/build/evidence/reviews/round-5/review-zh.json with:",
        "Put working files under ROOT/build/evidence/reviews/round-5/zh/.",
        # The delivery format is the specification's, at the soundtracks' program level.
        (
            f"Each edition: exactly {specification.DURATION} s, 16:9 pure 2D, "
            f"{specification.FPS} fps, UHD master and a 1080p viewing edition, each with its "
            "captions drawn in the picture and again without captions, "
            f"{specification.RATE // 1000} kHz stereo narration at -16.5 LUFS integrated, "
            "no music."
        ),
    ):
        assert expected in zh
    assert "(no findings). Verify" in en
    # An edition whose previous review holds no findings has none to dispose of.
    assert "everything independently.\n- Repairs: 07.6 names all seven checks.\n" in en
    assert "working files are in" not in en
    assert "The Chinese (zh) edition is the same film in its own language" in en
    for text in (zh, en):
        assert not re.search(r"\{[a-z_]+\}", text)
        # No prompt cites a work folder; the root itself may lie anywhere.
        assert "runtime/work" not in text.replace(str(root), "ROOT")
    monkeypatch.setattr(specification, "DURATION", 1260)
    monkeypatch.setattr(specification, "RATE", 44100)
    monkeypatch.setattr(
        review_prompts, "FILM", review_prompts.FILM.model_copy(update={"concepts": None})
    )
    review_prompts.prompts(previous, out, changes, disposed)
    assert "exactly 1260 s, 16:9 pure 2D" in (out / "prompt-en.md").read_text()
    assert "44.1 kHz stereo narration" in (out / "prompt-en.md").read_text()
    assert "Concept contract: none declared;" in (out / "prompt-en.md").read_text()
    Edition("en").film("uhd").unlink()
    with pytest.raises(
        ReviewError, match=re.escape("missing build/artifacts/film/en/sample-reel-en-uhd.mp4")
    ):
        review_prompts.prompts(previous, out, changes, disposed)


def test_prompts_name_the_optional_pause_fields_a_script_omits(root, put, monkeypatch):
    policies = {
        "zh": {"thought_level_tolerance_db": 0.75},
        "en": {
            "inner_pause_cap_seconds": 0.6,
            "thought_level_tolerance_db": 0.75,
            "thought_boundary_ratio": 1.62,
            "coda_thought_pause_seconds": 1.9,
        },
    }
    for code, policy in policies.items():
        put(root / Edition(code).script, {"voice_performance": policy})
        put(
            Edition(code).audio_assembly,
            {"program_level": {"policy": {"integrated_lufs": -16.5}}},
        )
    put(
        root / sources.MANIFEST,
        {
            "repository": "https://example.test/guidelines",
            "commit": "abc",
            "members": [{"path": "docs/charter.md"}],
        },
    )
    monkeypatch.setenv(sources.CHECKOUT, "/source/guidelines")
    out = root / "build/evidence/reviews/round-5"
    context = review_prompts.prompt_context(out, root / "build/evidence/reviews/round-4", None)
    assert context["caps"] == "none declared Chinese; 0.60 s English"
    assert context["ratios"] == "none declared Chinese, 1.62 and 0.00 s English"
    assert context["codas"] == "none declared Chinese, 1.90 s English"


def test_prompts_refuse_a_review_that_leaves_out_the_declared_concept_contract(root, monkeypatch):
    # The sample film declares a contract, cites it and scores concept fidelity.
    assert review_prompts.contract_gaps(review_prompts.TEMPLATE, review_record.DIMENSIONS) == []
    template = "Review the {language} edition: {media}\n{dimensions}\n"
    dimensions = {
        name: text
        for name, text in review_record.DIMENSIONS.items()
        if name != review_prompts.CONCEPT_DIMENSION
    }
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    monkeypatch.setattr(review_prompts, "DIMENSIONS", dimensions)
    out = root / "build/evidence/reviews/round-5"
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(root / "build/evidence/reviews/round-4", out)
    assert str(refusal.value) == (
        "the review omits the concept contract the film declares: "
        "content/review/prompt.md never cites {concepts}; "
        "content/review/prompt.md never cites {readings}; "
        "review.dimensions has no concept_fidelity"
    )
    assert not out.exists()
    # A film without a contract owes neither.
    monkeypatch.setattr(
        review_prompts, "FILM", review_prompts.FILM.model_copy(update={"concepts": None})
    )
    assert review_prompts.contract_gaps(template, dimensions) == []


def round_inputs(root, put, monkeypatch):
    """The scripts' pause policies, the assemblies, the source and a round's own inputs."""
    for code in CODES:
        put(
            root / Edition(code).script,
            {"voice_performance": {"thought_level_tolerance_db": 0.75}},
        )
        put(
            Edition(code).audio_assembly,
            {"program_level": {"policy": {"integrated_lufs": -16.5}}},
        )
    put(
        root / sources.MANIFEST,
        {"repository": "https://example.test/readme", "members": [{"path": "README.md"}]},
    )
    monkeypatch.setenv(sources.CHECKOUT, "/source/readme")
    out = root / "build/evidence/reviews/round-1"
    for name in review_prompts.ROUND_INPUTS:
        put(out / name, {})
    return out


@pytest.mark.usefixtures("unleveled")
def test_a_first_round_states_that_no_earlier_review_exists(root, put, monkeypatch):
    out = round_inputs(root, put, monkeypatch)
    review_round.main(["prompts", "--round", "1"])
    for code in CODES:
        text = (out / f"prompt-{code}.md").read_text()
        # A first round has no dispositions to state, so its prompts read as before.
        assert f"- {review_prompts.FIRST_ROUND}\n- Pause policy the scripts declare:" in text
        assert "previous review is in" not in text
        assert "working files are in" not in text
        assert not re.search(r"\{[a-z_]+\}", text)
        # The floors come from the declaration's clarity_minimum_db.
        assert "Voice clarity floors the film declares: 18 dB Chinese, 16 dB English." in text
    review = review_prompts.FILM.review.model_copy(update={"clarity_minimum_db": None})
    monkeypatch.setattr(
        review_prompts, "FILM", review_prompts.FILM.model_copy(update={"review": review})
    )
    review_prompts.prompts(None, out)
    assert "floors the film declares: none declared." in (out / "prompt-zh.md").read_text()


@pytest.mark.usefixtures("unleveled")
def test_a_template_that_cites_the_previous_review_needs_a_previous_round(
    root, review, put, monkeypatch
):
    out = round_inputs(root, put, monkeypatch)
    template = (
        "{media}\n- The previous review is in {previous}/{code}-review.md ({findings}).{scripts}\n"
        "{dispositions}{concepts} {readings}\n"
    )
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(None, out)
    assert str(refusal.value) == (
        "content/review/prompt.md cites {findings} and {previous}, which only a previous round "
        "fills; a first round's template cites {previous_review}"
    )
    assert not (out / "prompt-zh.md").exists()
    # With a previous round the same template is filled as before.
    previous = root / "build/evidence/reviews/round-0"
    review(previous, "zh", findings=[{"id": "R0-1", "severity": "minor"}])
    review(previous, "en")
    fixed = {"disposition": "fixed", "evidence": "The card names all seven checks."}
    disposed = put(root / "dispositions.json", {"round": 0, "findings": {"R0-1": fixed}})
    review_prompts.prompts(previous, out, dispositions=disposed)
    assert (
        "- The previous review is in ROOT/build/evidence/reviews/round-0/zh-review.md "
        "(findings: minor R0-1).\n"
    ) in (out / "prompt-zh.md").read_text()
    assert "(no findings).\n" in (out / "prompt-en.md").read_text()


@pytest.mark.usefixtures("unleveled")
def test_the_previous_review_field_cites_the_previous_round(root, review, put, monkeypatch):
    out = round_inputs(root, put, monkeypatch)
    previous = root / "build/evidence/reviews/round-0"
    review(previous, "zh")
    review(previous, "en")
    assert review_prompts.previous_review(previous, "en", "no findings") == (
        "The previous review is in ROOT/build/evidence/reviews/round-0/en-review.md and "
        "ROOT/build/evidence/reviews/round-0/review-en.json (no findings). Verify on these media "
        "whether each repair landed, and judge everything independently."
    )
    # A previous round without findings still has its dispositions file, which names none.
    disposed = put(root / "dispositions.json", {"round": 0, "findings": {}})
    review_prompts.prompts(previous, out, dispositions=disposed)
    text = (out / "prompt-en.md").read_text()
    assert review_prompts.FIRST_ROUND not in text
    assert "ROOT/build/evidence/reviews/round-0/review-en.json (no findings)." in text


def test_a_round_after_the_first_needs_the_dispositions_of_the_previous_findings(
    root, review, put, monkeypatch
):
    out = round_inputs(root, put, monkeypatch)
    previous = root / "build/evidence/reviews/round-0"
    review(previous, "zh", findings=[{"id": "R0-1", "severity": "minor"}])
    review(previous, "en")
    fixed = {"disposition": "fixed", "evidence": "The card names all seven checks."}
    disposed = put(root / "dispositions.json", {"round": 0, "findings": {"R0-1": fixed}})
    later = ["prompts", "--round", "1", "--previous", str(previous)]
    refusals = [
        (
            later,
            "--previous build/evidence/reviews/round-0 needs --dispositions <file>, a disposition "
            "of each of its findings",
        ),
        (
            ["prompts", "--round", "1", "--dispositions", str(disposed)],
            "--dispositions needs --previous; a first round has no findings to dispose of",
        ),
    ]
    for command, refusal in refusals:
        with pytest.raises(SystemExit) as stopped:
            review_round.main(command)
        assert str(stopped.value) == f"prompts: {refusal}"
    # The previous round's number is the n of its directory round-<n>.
    renamed = root / "build/evidence/reviews/recheck"
    previous.rename(renamed)
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(renamed, out, dispositions=disposed)
    assert str(refusal.value) == (
        "the previous round's directory build/evidence/reviews/recheck is not named round-<n>"
    )
    renamed.rename(previous)
    # A template that would not state the dispositions is refused when they are given.
    template = review_prompts.TEMPLATE.replace("{dispositions}", "")
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(previous, out, dispositions=disposed)
    assert str(refusal.value) == (
        "content/review/prompt.md never cites {dispositions}, which states the dispositions of "
        "the previous round's findings"
    )
    assert not list(out.glob("prompt-*.md"))


def test_the_dispositions_answer_each_previous_finding_once(root, review, put, monkeypatch):
    out = round_inputs(root, put, monkeypatch)
    previous = root / "build/evidence/reviews/round-0"
    review(previous, "zh", findings=[{"id": f"R0-{n}", "severity": "note"} for n in (1, 2, 3, 4)])
    review(previous, "en", findings=[{"id": "EN0-1", "severity": "minor"}])
    findings = {
        "R0-1": {"disposition": "fixed", "evidence": " "},
        "R0-2": {"disposition": "deferred", "owner": "filmkit 0.12.0"},
        "R0-3": {"disposition": "accepted", "reason": "It reads well."},
        "R0-9": {"disposition": "fixed", "evidence": "Reverified."},
        "EN0-1": {"disposition": "declared", "design": "Design §8.", "reason": "Kept."},
    }
    disposed = put(root / "dispositions.json", {"round": 0, "findings": findings})
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(previous, out, dispositions=disposed)
    assert str(refusal.value) == (
        "dispositions.json does not dispose of round 0's findings: no disposition of R0-4; "
        "round 0 holds no finding R0-9; R0-1: a fixed disposition states its evidence; "
        "R0-2: a deferred disposition states its owner and reason; "
        "R0-3: a disposition is fixed, declared or deferred; "
        "EN0-1: a declared disposition holds no reason"
    )
    complete = {
        name: {"disposition": "fixed", "evidence": "Reverified."}
        for name in ("R0-1", "R0-2", "R0-3", "R0-4", "EN0-1")
    }
    for record, message in (
        ({"round": 3, "findings": complete}, "names round 3, but the previous round is round 0"),
        (
            {"round": 0, "findings": list(complete)},
            'is not {"round": <n>, "findings": {<finding id>: <disposition>}}',
        ),
    ):
        put(disposed, record)
        with pytest.raises(ReviewError) as refusal:
            review_prompts.prompts(previous, out, dispositions=disposed)
        assert str(refusal.value) == f"dispositions.json {message}"
    # A disposition keyed by an identifier that names two findings would answer both.
    review(previous, "en", findings=[{"id": "R0-1", "severity": "minor"}])
    put(disposed, {"round": 0, "findings": complete})
    with pytest.raises(ReviewError) as refusal:
        review_prompts.prompts(previous, out, dispositions=disposed)
    assert (
        str(refusal.value) == "build/evidence/reviews/round-0 gives R0-1 to more than one finding"
    )
    assert not list(out.glob("prompt-*.md"))


@pytest.mark.usefixtures("unleveled")
def test_each_edition_s_prompt_states_its_dispositions_in_three_groups(
    root, review, put, monkeypatch
):
    out = round_inputs(root, put, monkeypatch)
    previous = root / "build/evidence/reviews/round-0"
    review(previous, "zh", findings=[{"id": f"R0-{n}", "severity": "note"} for n in (1, 2, 3, 4)])
    review(previous, "en", findings=[{"id": "EN0-1", "severity": "minor"}])
    findings = {
        "R0-4": {
            "disposition": "deferred",
            "owner": "filmkit 0.12.0",
            "reason": "The engine\n  cannot measure it yet.",
        },
        "R0-3": {"disposition": "fixed", "evidence": "The cover names the author."},
        "R0-2": {"disposition": "declared", "design": "Design §8 keeps the two-line title."},
        "R0-1": {"disposition": "fixed", "evidence": "07.6 names all seven checks."},
        "EN0-1": {"disposition": "fixed", "evidence": "08.2 stands on one line."},
    }
    disposed = put(root / "dispositions.json", {"round": 0, "findings": findings})
    review_round.main(
        ["prompts", "--round", "1", "--previous", str(previous), "--dispositions", str(disposed)]
    )
    zh, en = ((out / f"prompt-{code}.md").read_text() for code in CODES)
    statement = (
        "- Dispositions of round 0's findings. Re-verify each fixed finding on these media by its "
        "own reverification line; judge a declared finding against the design that keeps it, and "
        "a deferred one as it stands.\n"
    )
    # Each group lists its findings in the order of the previous review.
    assert (
        f"judge everything independently.\n{statement}"
        "  - Fixed:\n"
        "    - R0-1: 07.6 names all seven checks.\n"
        "    - R0-3: The cover names the author.\n"
        "  - Declared:\n"
        "    - R0-2: Design §8 keeps the two-line title.\n"
        "  - Deferred:\n"
        "    - R0-4 (owner: filmkit 0.12.0): The engine cannot measure it yet.\n"
        "- Pause policy the scripts declare:"
    ) in zh
    assert (
        f"judge everything independently.\n{statement}"
        "  - Fixed:\n"
        "    - EN0-1: 08.2 stands on one line.\n"
        "  - Declared: none.\n"
        "  - Deferred: none.\n"
        "- Pause policy the scripts declare:"
    ) in en
    # Each edition's reviewer is given the dispositions of its own edition's findings.
    assert "EN0-1" not in zh
    assert "R0-" not in en
