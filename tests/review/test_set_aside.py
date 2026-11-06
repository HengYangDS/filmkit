"""Exercise setting a build's packages aside: a reviewed round's, and an unreviewed build's."""

import json

import pytest

import filmkit.repository as repository
import filmkit.review.files as review_files
import filmkit.review.round as review_round
import filmkit.review.set_aside as review_set_aside
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

PURPOSE = "superseded by its repairs"


def test_set_aside_refuses_before_moving_then_reads_back_each_member(root, review):
    reviews = root / "build/evidence/reviews/round-3"
    review(reviews, "zh")
    review(reviews, "en", media=[{"path": "other.mp4", "sha256": "0" * 64}])
    with pytest.raises(ReviewError, match="en: the packaged films are not the ones round 3"):
        review_set_aside.plan_set_aside(3, PURPOSE, reviews)
    review(reviews, "en")
    Edition("zh").picture.unlink()
    with pytest.raises(
        ReviewError, match="missing build/artifacts/film/zh/sample-reel-final-picture"
    ):
        review_set_aside.plan_set_aside(3, PURPOSE, reviews)
    assert Edition("zh").film("uhd").is_file()
    assert not (root / "build/artifacts/film/superseded").exists()

    plans = review_set_aside.plan_set_aside(3, PURPOSE, reviews, pictures=())
    assert not (root / "build/artifacts/film/superseded").exists()
    sources = {
        code: [
            f"build/artifacts/film/{code}/sample-reel-{code}-uhd.mp4",
            f"build/artifacts/film/{code}/sample-reel-{code}-1080p-captioned.mp4",
            f"build/evidence/editions/{code}/film-package.json",
        ]
        for code in CODES
    }
    before = {path: repository.sha(root / path) for paths in sources.values() for path in paths}
    review_set_aside.move_aside(plans)
    for code in CODES:
        target = root / "build/artifacts/film/superseded/round-3" / code
        manifest = json.loads((target / "manifest.json").read_text())
        assert list(manifest) == ["purpose", "consumer", "exit_condition", "moved_at", "members"]
        assert manifest["purpose"] == f"{code} package and picture reviewed in round 3: {PURPOSE}"
        consumer = f"build/evidence/reviews/round-3/review-{code}.json"
        assert manifest["consumer"] == f"{consumer} binds the two film hashes"
        assert manifest["exit_condition"] == "Retire after the successor delivery is accepted"
        assert manifest["moved_at"]
        assert [member["source"] for member in manifest["members"]] == sources[code]
        for member in manifest["members"]:
            moved = root / member["path"]
            assert not (root / member["source"]).exists()
            assert moved.parent == target
            assert member["sha256"] == before[member["source"]] == repository.sha(moved)
            assert member["bytes"] == moved.stat().st_size
    assert Edition("en").picture.is_file()
    with pytest.raises(ReviewError, match="round-3/zh exists; inspect it"):
        review_set_aside.plan_set_aside(3, PURPOSE, reviews)


def test_set_aside_records_its_members_before_the_first_move(root, review, monkeypatch):
    # An interrupted set-aside leaves a manifest that names every member it was moving.
    reviews = root / "build/evidence/reviews/round-3"
    review(reviews, "zh")
    review(reviews, "en")
    plans = review_set_aside.plan_set_aside(3, PURPOSE, reviews)
    rename = review_set_aside.Path.rename
    moved = []

    def interrupted(self, target):
        if moved:
            message = "interrupted"
            raise OSError(message)
        moved.append(self)
        return rename(self, target)

    monkeypatch.setattr(review_set_aside.Path, "rename", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        review_set_aside.move_aside(plans)
    target = root / "build/artifacts/film/superseded/round-3/zh"
    manifest = json.loads((target / "manifest.json").read_text())
    assert manifest["moved_at"] is None
    assert [member["path"] for member in manifest["members"]] == [
        f"build/artifacts/film/superseded/round-3/zh/{name}"
        for name in (
            "sample-reel-zh-uhd.mp4",
            "sample-reel-zh-1080p-captioned.mp4",
            "film-package.json",
        )
    ] + ["build/artifacts/film/superseded/round-3/zh/sample-reel-final-picture.mp4"]


def test_cli_defaults_the_round_directory_and_reports_refusals(root, review, capsys):
    review(review_files.round_directory(3), "zh")
    review(review_files.round_directory(3), "en")
    review_round.main(["set-aside", "--round", "3", "--purpose", "superseded", "--dry-run"])
    printed = json.loads(capsys.readouterr().out)
    assert printed == {
        "dry_run": True,
        "editions": [
            {
                "language": code,
                "target": f"build/artifacts/film/superseded/round-3/{code}",
                "members": [
                    f"build/artifacts/film/superseded/round-3/{code}/{name}"
                    for name in (
                        f"sample-reel-{code}-uhd.mp4",
                        f"sample-reel-{code}-1080p-captioned.mp4",
                        "film-package.json",
                        "sample-reel-final-picture.mp4",
                    )
                ],
            }
            for code in CODES
        ],
    }
    assert not (root / "build/artifacts/film/superseded").exists()
    with pytest.raises(SystemExit, match="set-aside: missing build/evidence/reviews/round-4"):
        review_round.main(["set-aside", "--round", "4", "--purpose", "superseded"])
    review_round.main(["set-aside", "--round", "3", "--purpose", "superseded"])
    assert json.loads(capsys.readouterr().out)["dry_run"] is False
    assert (root / "build/artifacts/film/superseded/round-3/en/manifest.json").is_file()


def preview_copies(folder, codes=CODES):
    """Copy each edition's two films byte-identical into <folder>/<code>/, as a preview delivery."""
    for code in codes:
        for film in Edition(code).films:
            copy = folder / code / film.name
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(film.read_bytes())
    return folder


def test_an_unreviewed_build_is_set_aside_by_the_copies_its_consumer_holds(root, tmp_path):
    consumer = preview_copies(tmp_path / "Documents/sample-reel-preview")
    (consumer / "en" / Edition("en").film("uhd").name).write_bytes(b"another film")
    with pytest.raises(ReviewError) as refusal:
        review_set_aside.plan_unreviewed("preview-1", PURPOSE, consumer)
    assert str(refusal.value) == (
        f"en: {consumer}/en/sample-reel-en-uhd.mp4 does not hold the bytes of "
        "build/artifacts/film/en/sample-reel-en-uhd.mp4"
    )
    with pytest.raises(ReviewError, match="'Preview 1' is not a label"):
        review_set_aside.plan_unreviewed("Preview 1", PURPOSE, consumer)
    # The films' own folder holds no copy of them.
    with pytest.raises(ReviewError, match="zh: .* is the film itself, not a consumer's copy"):
        review_set_aside.plan_unreviewed("preview-1", PURPOSE, root / "build/artifacts/film")
    assert not (root / "build/artifacts/film/superseded").exists()

    preview_copies(consumer)
    before = {path: repository.sha(path) for code in CODES for path in Edition(code).films}
    review_set_aside.move_aside(review_set_aside.plan_unreviewed("preview-1", PURPOSE, consumer))
    for code in CODES:
        target = root / "build/artifacts/film/superseded/preview-1" / code
        manifest = json.loads((target / "manifest.json").read_text())
        assert list(manifest) == ["purpose", "consumer", "exit_condition", "moved_at", "members"]
        assert manifest["purpose"] == f"{code} package of an unreviewed build: {PURPOSE}"
        # The consumer is named below the root when it lies there, as every member is.
        assert manifest["consumer"] == (
            f"Documents/sample-reel-preview/{code} holds the two films' bytes"
        )
        assert manifest["exit_condition"] == "Retire after the successor delivery is accepted"
        assert manifest["moved_at"]
        assert [member["source"] for member in manifest["members"]] == [
            f"build/artifacts/film/{code}/sample-reel-{code}-uhd.mp4",
            f"build/artifacts/film/{code}/sample-reel-{code}-1080p-captioned.mp4",
            f"build/evidence/editions/{code}/film-package.json",
            f"build/artifacts/film/{code}/sample-reel-final-picture.mp4",
        ]
        for film in Edition(code).films:
            assert not film.exists()
            assert repository.sha(target / film.name) == before[film]


def test_the_command_sets_aside_one_edition_of_an_unreviewed_build_and_keeps_its_picture(
    root, tmp_path, capsys
):
    consumer = preview_copies(tmp_path / "preview", codes=("en",))
    with pytest.raises(SystemExit, match="an unreviewed set-aside names its --consumer"):
        review_round.main(["set-aside", "--unreviewed", "--round", "5", "--purpose", PURPOSE])
    with pytest.raises(SystemExit, match="a reviewed set-aside names its --round"):
        review_round.main(["set-aside", "--label", "preview-5", "--purpose", PURPOSE])
    with pytest.raises(SystemExit, match="zh: .*/preview/zh/sample-reel-zh-uhd.mp4 does not hold"):
        review_round.main(
            ["set-aside", "--unreviewed", "--consumer", str(consumer), "--round", "5"]
            + ["--purpose", PURPOSE, "--dry-run"]
        )
    capsys.readouterr()
    review_round.main(
        ["set-aside", "--unreviewed", "--consumer", str(consumer), "--round", "5"]
        + ["--purpose", PURPOSE, "--language", "en", "--without-picture", "en"]
    )
    assert json.loads(capsys.readouterr().out) == {
        "dry_run": False,
        "editions": [
            {
                "language": "en",
                "target": "build/artifacts/film/superseded/round-5/en",
                "members": [
                    f"build/artifacts/film/superseded/round-5/en/{name}"
                    for name in (
                        "sample-reel-en-uhd.mp4",
                        "sample-reel-en-1080p-captioned.mp4",
                        "film-package.json",
                    )
                ],
            }
        ],
    }
    # The English picture stays for the next package, and the Chinese edition is untouched.
    assert Edition("en").picture.is_file()
    assert all(path.is_file() for path in (*Edition("zh").films, Edition("zh").film_package))
    assert not (root / "build/artifacts/film/superseded/round-5/zh").exists()


def test_a_reviewed_set_aside_keeps_the_pictures_it_is_told_to(root, review, capsys):
    reviews = root / "build/evidence/reviews/round-3"
    review(reviews, "zh")
    review(reviews, "en")
    plans = review_set_aside.plan_set_aside(3, PURPOSE, reviews, pictures=("zh",))
    moved = {plan.code: [path.name for path in plan.sources] for plan in plans}
    assert moved["zh"][-1] == "sample-reel-final-picture.mp4"
    assert "sample-reel-final-picture.mp4" not in moved["en"]
    # Named without an edition, --without-picture keeps every edition's picture.
    review_round.main(
        ["set-aside", "--round", "3", "--purpose", PURPOSE, "--without-picture", "--dry-run"]
    )
    printed = json.loads(capsys.readouterr().out)["editions"]
    assert [len(edition["members"]) for edition in printed] == [3, 3]
    assert not any("final-picture" in path for edition in printed for path in edition["members"])
    assert not (root / "build/artifacts/film/superseded").exists()


def test_the_rounds_whose_prompts_bind_an_edition_s_films_hold_them_until_set_aside(
    root, review, put, monkeypatch
):
    zh, en = Edition("zh"), Edition("en")

    def named(*films):
        return "".join(f"- {film} (SHA-256 {repository.sha(film)})\n" for film in films)

    for number in (9, 10):
        put(review_files.round_directory(number) / "prompt-zh.md", named(*zh.films))
    put(review_files.round_directory(10) / "prompt-en.md", named(*en.films))
    # Prompts that name another build or only one of the films bind nothing, and neither does a
    # prompt outside a round's directory.
    put(review_files.round_directory(8) / "prompt-zh.md", f"- other.mp4 (SHA-256 {'0' * 64})\n")
    put(review_files.round_directory(7) / "prompt-zh.md", named(zh.film("uhd")))
    put(root / "build/evidence/reviews/typography/prompt-zh.md", named(*zh.films))
    with pytest.raises(ReviewError) as refusal:
        review_set_aside.require_set_aside(zh)
    assert str(refusal.value) == (
        "the current zh films are bound by the prompts of review round 9 and round 10 and have "
        "not been set aside; first run python -m filmkit.review.round set-aside --round 10 "
        "--purpose <text> --language zh"
    )
    # Setting the Chinese edition aside moves its films, and the English stays bound.
    reviews = review_files.round_directory(10)
    review(reviews, "zh")
    review_set_aside.move_aside(
        review_set_aside.plan_set_aside(10, PURPOSE, reviews, codes=("zh",))
    )
    review_set_aside.require_set_aside(zh)
    with pytest.raises(ReviewError, match="bound by the prompts of review round 10 and have not"):
        review_set_aside.require_set_aside(en)
    # A build rebuilt to the same bytes stays bound by the round that has not been set aside.
    record = root / "build/artifacts/film/superseded/round-10/zh/manifest.json"
    for member in json.loads(record.read_text())["members"]:
        (root / member["source"]).write_bytes((root / member["path"]).read_bytes())
    with pytest.raises(ReviewError, match=r"review round 9 and have not been set aside; .* 9 "):
        review_set_aside.require_set_aside(zh)
    # A set-aside interrupted before its first move has not set the round aside.
    reviews = review_files.round_directory(9)
    review(reviews, "zh")
    plans = review_set_aside.plan_set_aside(9, PURPOSE, reviews, codes=("zh",))

    def interrupted(self, target):
        message = "interrupted"
        raise OSError(message)

    monkeypatch.setattr(review_set_aside.Path, "rename", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        review_set_aside.move_aside(plans)
    assert (root / "build/artifacts/film/superseded/round-9/zh/manifest.json").is_file()
    with pytest.raises(ReviewError, match="bound by the prompts of review round 9 and have not"):
        review_set_aside.require_set_aside(zh)
