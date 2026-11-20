"""The verifier's acceptance of the recorded independent review."""

import json

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.rendering as picture_rendering
import filmkit.production as production
import filmkit.repository as repository
import filmkit.review.record as review_record
from filmkit.delivery.verification import VerificationError


@pytest.fixture
def current_review(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition("zh")
    for name, body in (
        ("content/film-script.json", "{}"),
        (str(picture_rendering.COMPOSITION_SCRIPT), "/* film */"),
        ("build/evidence/editions/zh/production-review.md", "# Review\n"),
        ("build/artifacts/film/zh/sample-reel-zh-uhd.mp4", "uhd"),
        ("build/artifacts/film/zh/sample-reel-zh-1080p-captioned.mp4", "viewing"),
    ):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(body)
    files = sorted((tmp_path / "build/artifacts/film/zh").glob("*.mp4"))
    record = {
        "schema_version": 2,
        "language": "zh",
        "reviewer": "independent reviewer",
        "media": [
            {"path": str(f.relative_to(tmp_path)), "sha256": repository.sha(f)} for f in files
        ],
        "script_sha256": repository.sha(tmp_path / edition.script),
        "composition_sha256": repository.sha(tmp_path / picture_rendering.COMPOSITION_SCRIPT),
        "scores": dict.fromkeys(review_record.DIMENSIONS, 96),
        "overall": 96.0,
        "findings": [{"severity": "minor"}],
        "human_listening": {"state": "not_performed"},
        # A published record keeps the report path of the repository that recorded it.
        "report": {
            "path": "evidence/reviews/production-review.md",
            "sha256": repository.sha(edition.production_review.with_name("production-review.md")),
        },
    }
    path = edition.production_review

    def check(**changes):
        path.write_text(json.dumps({**record, **changes}))
        return delivery_verification.verify_review(edition, files)

    return check, record, files


@pytest.mark.usefixtures("unleveled")
def test_a_published_review_is_read_beside_its_report_wherever_it_lies(current_review, tmp_path):
    _, record, files = current_review
    # A release names each edition's record and report after the edition's file prefix.
    release = tmp_path / "build/artifacts/release"
    release.mkdir(parents=True)
    films = [release / film.name for film in files]
    for film, published in zip(files, films, strict=True):
        published.write_bytes(film.read_bytes())
    (release / "sample-reel-zh-production-review.md").write_text("# Review\n")
    published = release / "sample-reel-zh-production-review.json"
    published.write_text(json.dumps(record))
    edition = production.Edition("zh")
    accepted = delivery_verification.verify_review(edition, films, record=published)
    assert accepted["path"] == "build/artifacts/release/sample-reel-zh-production-review.json"
    (release / "sample-reel-zh-production-review.md").write_text("# Another review\n")
    with pytest.raises(VerificationError, match="Review report differs from its record"):
        delivery_verification.verify_review(edition, films, record=published)


@pytest.mark.usefixtures("unleveled")
def test_review_accepts_only_current_media_above_thresholds(current_review):
    check, record, files = current_review
    accepted = check()
    assert (accepted["overall"], accepted["minimum_dimension"]) == (96.0, 96)
    # Every dimension at the film's floors of 95 qualifies; one dimension at 94 does not.
    floor = check(scores=dict.fromkeys(review_record.DIMENSIONS, 95), overall=95.0)
    assert (floor["overall"], floor["minimum_dimension"]) == (95.0, 95)
    low = {**record["scores"], next(iter(review_record.DIMENSIONS)): 94}
    with pytest.raises(VerificationError, match="below the acceptance thresholds"):
        check(scores=low, overall=round(sum(low.values()) / len(low), 1))
    with pytest.raises(VerificationError, match="mean of its dimensions"):
        check(overall=97.0)
    missing = dict(list(record["scores"].items())[1:])
    with pytest.raises(VerificationError, match="every declared dimension"):
        check(scores=missing)
    with pytest.raises(VerificationError, match="unresolved material finding"):
        check(findings=[{"severity": "material"}])
    with pytest.raises(VerificationError, match="current delivered edition"):
        check(schema_version=1)
    edition = production.Edition("zh")
    report = edition.production_review.with_name("production-review.md")
    report.write_text("# Another review\n")
    with pytest.raises(VerificationError, match="Review report differs from its record"):
        check()
    report.write_text("# Review\n")
    files[0].write_text("re-encoded")
    with pytest.raises(VerificationError, match="current delivered edition"):
        check()


@pytest.mark.usefixtures("unleveled")
def test_a_film_that_accepts_notes_verifies_no_review_with_another_finding(
    current_review, monkeypatch
):
    check, _, _ = current_review
    # A film that does not declare the list accepts the minor finding its record holds.
    assert review_record.ACCEPTED_SEVERITIES is None
    assert check()["overall"] == 96.0
    monkeypatch.setattr(review_record, "ACCEPTED_SEVERITIES", ("note",))
    note = {"id": "R1", "severity": "note"}
    assert check(findings=[note])["overall"] == 96.0
    for finding, named in (
        ({"id": "R2", "severity": "minor"}, "minor finding R2"),
        ({"id": "R3", "severity": "minro"}, "minro finding R3"),
        ({"id": "R4"}, "finding R4 without a severity"),
        ({"severity": "material"}, "material finding"),
    ):
        with pytest.raises(VerificationError) as refusal:
            check(findings=[note, finding])
        assert str(refusal.value) == f"Review records an unresolved {named}"
    # An empty list accepts no finding.
    monkeypatch.setattr(review_record, "ACCEPTED_SEVERITIES", ())
    with pytest.raises(VerificationError, match="unresolved note finding R1"):
        check(findings=[note])
