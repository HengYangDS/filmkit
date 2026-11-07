"""The production command runs each action's owner for the selected edition."""

import json
import sys

import pytest

import filmkit.produce as produce
import filmkit.production as production
import filmkit.repository as repository
import filmkit.review.round as review_round
from filmkit.picture.rendering import PictureError


@pytest.fixture
def root(tmp_path, monkeypatch):
    """An empty film root, which no review round binds."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return tmp_path.resolve()


@pytest.fixture
def reviewed(root):
    """The Chinese edition's packaged build, whose films round 7's prompts and reviews bind."""
    edition = production.Edition("zh")
    for path in (*edition.films, edition.picture, edition.film_package):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"zh {path.name}")
    media = [{"path": str(film), "sha256": repository.sha(film)} for film in edition.films]
    folder = root / "build/evidence/reviews/round-7"
    folder.mkdir(parents=True)
    named = "".join(f"- {item['path']} (SHA-256 {item['sha256']})\n" for item in media)
    (folder / "prompt-zh.md").write_text(f"## Media under review (the exact files)\n{named}")
    review = {"reviewer": "Reviewer", "editions": {"zh": {"media": media, "findings": []}}}
    (folder / "review-zh.json").write_text(json.dumps(review))
    return edition


@pytest.mark.usefixtures("root")
def test_an_action_runs_its_owner_for_the_selected_edition(monkeypatch):
    calls = []
    monkeypatch.setattr(produce, "assemble", calls.append)
    monkeypatch.setattr(sys, "argv", ["produce.py", "assemble", "--language", "en"])
    produce.main()
    assert calls == [production.Edition("en")]


def test_the_actions_are_the_documented_ones_in_order():
    assert [*produce.EDITION_ACTIONS] == [
        "select",
        "assemble",
        "refresh-captions",
        "stage-picture",
        "check-picture",
        "preflight",
        "render-picture",
        "package-metadata",
        "validate-picture",
        "compare-pictures",
        "package-film",
    ]


def test_an_edition_action_passes_its_options_to_its_owner(monkeypatch, tmp_path):
    calls = []

    def owner(*arguments, **options):
        calls.append((*arguments, options))

    for name in ("stage_picture", "render_picture", "validate_picture", "compare_pictures"):
        monkeypatch.setattr(produce, name, owner)
    output = tmp_path / "stage"
    stage = ["--output", str(output), "--duration", "60", "--width", "1920", "--height", "1080"]
    produce.main(["stage-picture", "--language", "zh", *stage, "--start", "12.5"])
    produce.main(["render-picture", "--language", "en", "--deadline", "600"])
    # The uncaptioned picture is staged, rendered and validated by the same owners.
    produce.main(["stage-picture", "--language", "en", "--uncaptioned"])
    produce.main(["render-picture", "--language", "zh", "--uncaptioned", "--deadline", "600"])
    produce.main(["validate-picture", "--language", "zh", "--uncaptioned"])
    produce.main(["compare-pictures", "--language", "en"])
    zh, en = production.Edition("zh"), production.Edition("en")
    assert calls == [
        (zh, output, 60, 1920, 1080, 12.5, {"captions": True}),
        (en, 600, {"captions": True}),
        (en, None, produce.DURATION, 3840, 2160, 0, {"captions": False}),
        (zh, 600, {"captions": False}),
        (zh, {"captions": False}),
        (en, {}),
    ]


@pytest.mark.parametrize("action", ["check-picture", "compare-pictures", "package-film"])
def test_only_the_picture_actions_take_the_uncaptioned_picture(monkeypatch, capsys, action):
    monkeypatch.setattr(produce, "package_film", lambda _edition: pytest.fail("ran"))
    with pytest.raises(SystemExit) as stopped:
        produce.main([action, "--language", "zh", "--uncaptioned"])
    assert stopped.value.code == 2
    assert (
        "--uncaptioned applies only to stage-picture, render-picture, validate-picture"
        in capsys.readouterr().err
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["select"], "the following arguments are required: --language"),
        (["render-picture"], "the following arguments are required: --language"),
        (["package-film", "--language", "fr"], "invalid choice: 'fr'"),
    ],
)
def test_an_action_refuses_without_its_required_inputs(monkeypatch, capsys, arguments, message):
    monkeypatch.setattr(sys, "argv", ["produce.py", *arguments])
    with pytest.raises(SystemExit) as stopped:
        produce.main()
    assert stopped.value.code == 2
    assert message in capsys.readouterr().err


def test_a_refusal_ends_the_command_with_the_action_and_its_reason(monkeypatch):
    def refuse(_edition, **_options):
        msg = "The render receipt does not bind the staged picture"
        raise PictureError(msg)

    monkeypatch.setattr(produce, "validate_picture", refuse)
    with pytest.raises(SystemExit) as stopped:
        produce.main(["validate-picture", "--language", "zh"])
    assert stopped.value.code == (
        "validate-picture: The render receipt does not bind the staged picture"
    )


def test_any_other_error_keeps_its_traceback(monkeypatch):
    def defect(_edition):
        msg = "a programming error"
        raise ValueError(msg)

    monkeypatch.setattr(produce, "package_film", defect)
    with pytest.raises(ValueError, match="a programming error"):
        produce.main(["package-film", "--language", "en"])


@pytest.mark.parametrize(
    ("action", "owner"), [("assemble", "assemble"), ("refresh-captions", "refresh_captions")]
)
def test_a_rebuild_over_a_reviewed_build_waits_for_its_set_aside(
    reviewed, monkeypatch, action, owner
):
    calls = []
    monkeypatch.setattr(produce, owner, calls.append)
    with pytest.raises(SystemExit) as stopped:
        produce.main([action, "--language", "zh"])
    assert stopped.value.code == (
        f"{action}: the current zh films are bound by the prompts of review round 7 and have not "
        "been set aside; first run python -m filmkit.review.round set-aside --round 7 "
        "--purpose <text> --language zh"
    )
    assert calls == []
    # The English edition's films are bound by no round.
    produce.main([action, "--language", "en"])
    assert calls == [production.Edition("en")]
    review_round.main(["set-aside", "--round", "7", "--purpose", "retakes", "--language", "zh"])
    produce.main([action, "--language", "zh"])
    assert calls == [production.Edition("en"), reviewed]
