"""Exercise the review round's command and its records; `test_prepare` holds its preparation."""

import json
import os
import shutil
import subprocess
import sys

import pytest
from preparing import ROUND, prepare, refusal

import filmkit.declared_sources as declared_sources
import filmkit.delivery.verification as delivery_verification
import filmkit.film as film
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
import filmkit.review.files as review_files
import filmkit.review.record as review_record
import filmkit.review.round as review_round
from filmkit.delivery.verification import VerificationError
from filmkit.graph import runs, verify
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

PURPOSE = "superseded by its repairs"


@pytest.mark.usefixtures("root")
def test_the_command_reports_only_its_own_refusals(put):
    # A malformed review is a fault to see in full, not a refusal to report.
    put(review_files.round_directory(3) / "review-zh.json", "{")
    with pytest.raises(json.JSONDecodeError):
        review_round.main(["set-aside", "--round", "3", "--purpose", PURPOSE, "--dry-run"])


@pytest.mark.usefixtures("unleveled")
def test_record_writes_reviews_that_verify_film_accepts(root, review, put, capsys):
    for code in CODES:
        put(root / Edition(code).script, f"{code} script")
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition")
    folder = root / "build/evidence/reviews/round-5"
    relative = [
        {"path": str(film.relative_to(root)), "sha256": repository.sha(film)}
        for film in Edition("en").films
    ]
    review(folder, "zh", findings=[{"id": "R5-1", "severity": "minor"}])
    # A stated overall decides nothing: the record derives 96.0 from the scores.
    review(folder, "en", media=relative, overall=97.0)
    put(Edition("zh").film("uhd"), "zh uhd changed")
    with pytest.raises(ReviewError, match="zh: reviewed media differ"):
        review_round.review_records(folder)
    review(folder, "zh", findings=[{"id": "R5-1", "severity": "minor"}])
    review_round.main(["record", "--round-dir", str(folder), "--dry-run"])
    assert json.loads(capsys.readouterr().out)["dry_run"] is True
    assert not (root / "evidence").exists()

    review_round.main(["record", "--round-dir", str(folder)])
    assert json.loads(capsys.readouterr().out) == {
        "dry_run": False,
        "editions": [
            {"language": "zh", "overall": 96.0, "minimum": 96, "material": 0},
            {"language": "en", "overall": 96.0, "minimum": 96, "material": 0},
        ],
    }
    record = json.loads(Edition("zh").production_review.read_text())
    assert list(record) == [
        "schema_version",
        "language",
        "reviewer",
        "recorded_at",
        "media",
        "script_sha256",
        "composition_sha256",
        "scores",
        "overall",
        "findings",
        "human_listening",
        "report",
        "source_review",
    ]
    films = Edition("zh").films
    assert record["media"] == [
        {"path": str(film.relative_to(root)), "sha256": repository.sha(film)}
        for film in sorted(films)
    ]
    assert record["human_listening"]["checklist"] == ["Listen to 24.3 in its clause."]
    assert record["source_review"] == {
        "path": "build/evidence/reviews/round-5/review-zh.json",
        "sha256": repository.sha(folder / "review-zh.json"),
    }
    for code in CODES:
        edition = Edition(code)
        accepted = delivery_verification.verify_review(edition, sorted(edition.films))
        assert accepted["overall"] == 96.0
        assert root / accepted["path"] == edition.production_review


@pytest.mark.usefixtures("unleveled")
def test_the_record_derives_the_overall_whatever_a_review_states(root, review, put):
    # Round 42 of the DDWG film stated 99.3 for twelve scores whose mean is 99.25, which the
    # engine rounds to 99.2; the record's overall is the engine's.
    assert review_record.overall(dict(enumerate([99] * 9 + [100] * 3))) == 99.2
    for code in CODES:
        put(root / Edition(code).script, f"{code} script")
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition")
    folder = root / "build/evidence/reviews/round-5"
    review(folder, "zh", overall=None)
    review(folder, "en", overall=99.3)
    records = review_round.review_records(folder)
    assert [written.record["overall"] for written in records] == [96.0, 96.0]


def reviewed_build(root, put):
    """The scripts and the composition a record binds, and the round's directory."""
    for code in CODES:
        put(root / Edition(code).script, f"{code} script")
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition")
    return root / "build/evidence/reviews/round-5"


@pytest.mark.usefixtures("unleveled")
def test_a_film_that_accepts_notes_records_no_review_with_another_finding(
    root, review, put, monkeypatch
):
    folder = reviewed_build(root, put)
    monkeypatch.setattr(review_record, "ACCEPTED_SEVERITIES", ("note",))
    note = {"id": "R5-0", "severity": "note"}
    review(folder, "en")
    # Every score stands above the floor: the finding refuses, by its id and its severity.
    for finding, named in (
        ({"id": "R5-1", "severity": "minor"}, "minor finding R5-1"),
        ({"id": "R5-2", "severity": "minro"}, "minro finding R5-2"),
        ({"id": "R5-3"}, "finding R5-3 without a severity"),
    ):
        review(folder, "zh", findings=[note, finding])
        with pytest.raises(ReviewError) as refusal:
            review_round.review_records(folder)
        assert str(refusal.value) == (
            f"zh: the review holds what the film does not accept: {named}"
        )
    review(folder, "zh", findings=[note])
    assert [written.record["findings"] for written in review_round.review_records(folder)] == [
        [note],
        [],
    ]
    # An empty list accepts no finding.
    monkeypatch.setattr(review_record, "ACCEPTED_SEVERITIES", ())
    with pytest.raises(ReviewError, match="does not accept: note finding R5-0"):
        review_round.review_records(folder)


@pytest.mark.usefixtures("unleveled")
def test_a_film_that_declares_no_severities_records_a_material_finding_the_verifier_refuses(
    root, review, put, capsys
):
    # Without the list and without levels nothing in `record` names a severity: the review is
    # recorded as before, and the verifier refuses the record as before.
    assert review_record.ACCEPTED_SEVERITIES is None
    folder = reviewed_build(root, put)
    review(folder, "zh", findings=[{"id": "R5-1", "severity": "material"}])
    review(folder, "en")
    review_round.main(["record", "--round-dir", str(folder)])
    assert [edition["material"] for edition in json.loads(capsys.readouterr().out)["editions"]] == [
        1,
        0,
    ]
    zh, en = Edition("zh"), Edition("en")
    with pytest.raises(VerificationError) as refusal:
        delivery_verification.verify_review(zh, sorted(zh.films))
    assert str(refusal.value) == "Review records an unresolved material finding R5-1"
    assert delivery_verification.verify_review(en, sorted(en.films))["overall"] == 96.0


@pytest.mark.usefixtures("unleveled")
def test_twelve_scores_with_the_mean_99_25_are_recorded_with_the_overall_99_2(
    root, review, put, monkeypatch, capsys
):
    # The scores of the DDWG film's round 42, whose review stated 99.3: the written record
    # holds the engine's rounding of their mean.
    scores = {f"dimension_{number}": 99 if number < 9 else 100 for number in range(12)}
    assert sum(scores.values()) / len(scores) == 99.25
    monkeypatch.setattr(review_round, "DIMENSIONS", dict.fromkeys(scores, "asked"))
    folder = reviewed_build(root, put)
    for code in CODES:
        review(folder, code, scores=scores, overall=99.3)
    review_round.main(["record", "--round-dir", str(folder)])
    printed = json.loads(capsys.readouterr().out)["editions"]
    assert [edition["overall"] for edition in printed] == [99.2, 99.2]
    for code in CODES:
        record = json.loads(Edition(code).production_review.read_text())
        assert (record["overall"], record["scores"]) == (99.2, scores)


def test_a_declaration_s_accepted_severities_reach_the_record_through_the_loader(tmp_path, put):
    # A film's own declaration file, read by the engine as a command reads it: nothing here
    # sets the record's constant, so a record that ignored the declaration would fail this.
    for _field, path in declared_sources.named_files(film.FILM):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, tmp_path / path)
    declared = (repository.ROOT / film.DECLARATION).read_text(encoding="utf-8")
    assert "accepted_severities" not in declared
    folder = tmp_path / "build/evidence/reviews/round-5"
    media = []
    for name in ("uhd", "1080p-captioned", "uhd-uncaptioned", "1080p-uncaptioned"):
        path = put(tmp_path / f"build/artifacts/film/zh/sample-reel-zh-{name}.mp4", name)
        media.append({"path": str(path), "sha256": repository.content_sha(name)})
    scores = dict.fromkeys(review_record.DIMENSIONS, 96)
    entry = {"media": media, "scores": scores, "findings": [{"id": "R5-1", "severity": "minor"}]}
    put(folder / "review-zh.json", {"reviewer": "Reviewer", "editions": {"zh": entry}})
    put(folder / "zh-review.md", "# zh review\n")

    def recorded(declaration):
        put(tmp_path / film.DECLARATION, declaration)
        command = [sys.executable, "-m", "filmkit.review.round", "record", "--round-dir", folder]
        environment = os.environ | {"FILMKIT_ROOT": str(tmp_path)}
        ended = subprocess.run(
            command,
            cwd=tmp_path,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=110,
        )
        return ended.returncode, ended.stderr.strip().splitlines()[-1]

    accepting = declared.replace("[review]\n", '[review]\naccepted_severities = ["note"]\n', 1)
    assert recorded(accepting) == (
        1,
        "record: zh: the review holds what the film does not accept: minor finding R5-1",
    )
    # The same film without the list is not refused for its minor finding: its levels are next.
    assert recorded(declared) == (
        1,
        "record: zh: the review's levels do not pass: no verdict for level 信; no verdict for "
        "level 达; no verdict for level 雅; finding R5-1 names no level",
    )


# A round's preparation runs `filmkit verify` before it writes anything (record-every-run).


def recorded(*named):
    """Record a run of each node of an edition that states its files as they stand."""
    for name, code in named:
        with runs.run(code, name):
            pass


def test_a_preparation_is_refused_for_a_film_changed_by_no_declared_writer(put, ready):
    recorded(*(("package-film", code) for code in CODES))
    film = Edition("zh").film("1080p-captioned")
    put(film, "a film changed by hand\n")
    assert refusal() == (
        f"prepare: filmkit verify refuses: {repository.relative(film)}: its bytes are "
        "accounted for by no record of a declared writer; it is bound by package-film:zh"
    )
    assert not review_files.round_directory(ROUND).exists()
    assert "prompts" not in [step for step, _ in ready]


def test_a_preparation_after_a_repair_writes_the_round(ready):
    recorded(("render-picture", "zh"), ("compare-pictures", "zh"))
    edition = Edition("zh")
    with runs.run("zh", "repair-pictures"):
        with runs.node("zh", "render-picture"):
            edition.rendered(True).file.write_bytes(b"the repaired picture")
        with runs.node("zh", "compare-pictures"):
            repository.write(edition.caption_equivalence, {"verdict": "pass", "findings": []})
    recorded(("package-film", "zh"))
    assert verify.verify().refusals == ()
    prepare()
    assert "prompts" in [step for step, _ in ready]
