"""Exercise the review round: its command, the player-check binding and the records."""

import json
import re

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
import filmkit.review.files as review_files
import filmkit.review.round as review_round
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

PURPOSE = "superseded by its repairs"


@pytest.mark.usefixtures("root")
def test_the_command_reports_only_its_own_refusals(put):
    # A malformed review is a fault to see in full, not a refusal to report.
    put(review_files.round_directory(3) / "review-zh.json", "{")
    with pytest.raises(json.JSONDecodeError):
        review_round.main(["set-aside", "--round", "3", "--purpose", PURPOSE, "--dry-run"])


def test_bind_names_the_language_entry_and_each_packaged_member(root, put):
    put(root / "build/artifacts/film/index.html", "entry")
    for code in CODES:
        names = ["sample-reel-cover.png", f"sample-reel-{code}.srt", "index.html"]
        for name in names:
            put(root / "build/artifacts/film" / code / name, f"{code} {name}")
        put(
            Edition(code).viewing_package,
            {"members": [{"path": name, "sha256": "recorded"} for name in names]},
        )
    assert review_round.bind(root / "binding.json") == {
        "members": 11,
        "binding": "binding.json",
    }
    binding = json.loads((root / "binding.json").read_text())
    assert binding["destination"] == str(root / "build/artifacts/film")
    assert [member["path"] for member in binding["members"]] == [
        "index.html",
        *[
            f"{code}/{name}"
            for code in CODES
            for name in (
                f"sample-reel-{code}-uhd.mp4",
                f"sample-reel-{code}-1080p-captioned.mp4",
                "sample-reel-cover.png",
                f"sample-reel-{code}.srt",
                "index.html",
            )
        ],
    ]
    for member in binding["members"]:
        assert member["sha256"] == repository.sha(root / "build/artifacts/film" / member["path"])
    (root / "build/artifacts/film/en/index.html").unlink()
    with pytest.raises(ReviewError, match=re.escape("missing build/artifacts/film/en/index.html")):
        review_round.bind(root / "binding.json")


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
    review(folder, "en", media=relative, overall=97.0)
    with pytest.raises(
        ReviewError, match=re.escape("en: reported overall 97.0 is not the mean 96.0")
    ):
        review_round.review_records(folder)
    review(folder, "en", media=relative)
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
        for film in films[::-1]
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


def test_record_requires_each_review_to_report_its_overall(root, review):
    # The prompt asks for the overall score, so a review without one is incomplete.
    folder = root / "build/evidence/reviews/round-5"
    review(folder, "zh", overall=None)
    review(folder, "en")
    with pytest.raises(ReviewError, match="zh: a review reports its overall score"):
        review_round.review_records(folder)
