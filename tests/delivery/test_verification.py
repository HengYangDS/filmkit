"""The verifier's qualification of an edition and its command."""

import json

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.verification import VerificationError


@pytest.fixture
def qualified(tmp_path, monkeypatch):
    """Every check of an edition replaced by a marker of its call."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for name in ("sources", "narration", "picture", "package", "spotlight"):
        monkeypatch.setattr(delivery_verification, f"verify_{name}", lambda *_, n=name: n)
    monkeypatch.setattr(
        delivery_verification,
        "verify_media",
        lambda _edition, path, rendition: (path.name, (rendition.width, rendition.height)),
    )
    monkeypatch.setattr(
        delivery_verification,
        "verify_review",
        lambda edition, files: (edition.code, [path.name for path in files]),
    )


@pytest.mark.usefixtures("qualified")
def test_an_edition_is_qualified_as_its_four_current_films():
    edition = production.Edition("en")
    films = list(reversed(edition.films))
    report = delivery_verification.qualify(edition, films)
    assert list(report) == [
        "verdict",
        "scope",
        "language",
        "sources",
        "narration",
        "picture",
        "package",
        "media",
        "media_seconds",
        "spotlight",
        "review",
        "limits",
    ]
    assert (report["verdict"], report["scope"], report["language"]) == ("pass", "acceptance", "en")
    assert report["media"] == [
        ("sample-reel-en-1080p-captioned.mp4", (1920, 1080)),
        ("sample-reel-en-1080p-uncaptioned.mp4", (1920, 1080)),
        ("sample-reel-en-uhd-uncaptioned.mp4", (3840, 2160)),
        ("sample-reel-en-uhd.mp4", (3840, 2160)),
    ]
    assert report["review"] == ("en", sorted(film.name for film in films))
    technical = delivery_verification.qualify(edition, films, technical_only=True)
    assert (technical["scope"], technical["review"]) == ("technical", {"verdict": "not_reviewed"})
    for files in (
        films[:1],
        [*films, edition.artifacts / "sample-reel-en-uhd.mp4"],
        [edition.artifacts.parent / "zh" / film.name for film in films],
        production.Edition("zh").films,
    ):
        with pytest.raises(VerificationError, match="four current delivered films"):
            delivery_verification.qualify(edition, files)


@pytest.mark.usefixtures("unleveled")
def test_the_bound_inputs_and_the_review_are_checked_without_the_decode(editions, monkeypatch):
    class DecodedError(Exception):
        """A film's media was asked for."""

    def decode(*_arguments, **_options):
        raise DecodedError

    for name in (
        *("probe", "require_video", "video_cadence"),
        *("decoded_video_frames", "decoded_audio_frames"),
    ):
        monkeypatch.setattr(delivery_verification.media, name, decode)
    monkeypatch.setattr(delivery_verification.spotlight, "imported", decode)
    for code, inputs in editions.items():
        edition = inputs.edition
        inputs.review()
        bound = delivery_verification.verify_bindings(edition)
        assert list(bound) == ["sources", "narration", "picture", "package"]
        assert bound["sources"]["documents"] == "not_checked"
        assert bound["narration"]["soundtrack_sha256"] == repository.sha(edition.soundtrack)
        assert bound["picture"]["picture_sha256"] == repository.sha(edition.picture)
        assert bound["package"]["films"] == sorted(film.name for film in edition.films)
        accepted = delivery_verification.verify_review(edition, edition.films)
        assert accepted["path"] == f"build/evidence/editions/{code}/production-review.json"
        # The verifier's command asks the same checks and then decodes the films.
        with pytest.raises(DecodedError):
            delivery_verification.qualify(edition, edition.films)


@pytest.mark.usefixtures("qualified")
def test_the_verifier_reports_the_bound_inputs_where_it_reported_them(monkeypatch):
    edition = production.Edition("zh")
    assert delivery_verification.verify_bindings(edition) == {
        name: name for name in ("sources", "narration", "picture", "package")
    }
    # The command's report holds what the one check gives, in the phase it ran them in.
    phases = []
    monkeypatch.setattr(
        delivery_verification, "verify_bindings", lambda _edition: {"bound": phases[-1]}
    )
    phase = delivery_verification.durations.phase

    def named(name):
        phases.append(name)
        return phase(name)

    monkeypatch.setattr(delivery_verification.durations, "phase", named)
    report = delivery_verification.qualify(edition, edition.films, technical_only=True)
    assert report["bound"] == "bindings"
    assert phases == ["bindings", "media", "spotlight"]


@pytest.mark.usefixtures("qualified")
def test_the_command_prints_each_editions_report_and_writes_only_its_duration(tmp_path, capsys):
    films = [str(film) for code in production.CODES for film in production.Edition(code).films]
    delivery_verification.main(["--read-only", "--technical-only", "--language", "all", *films])
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [(report["language"], report["scope"]) for report in reports] == [
        ("zh", "technical"),
        ("en", "technical"),
    ]
    delivery_verification.main(["--language", "en", *films[4:]])
    (report,) = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert (report["language"], report["scope"]) == ("en", "acceptance")
    # With --read-only nothing was written; without it, the edition's duration record alone.
    written = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*.*"))
    assert written == ["build/evidence/editions/en/durations/verify.json"]
    # Without named films, each selected edition's current delivered films are verified.
    delivery_verification.main(["--technical-only", "--language", "all"])
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [report["language"] for report in reports] == ["zh", "en"]
    delivery_verification.main(["--technical-only", "--language", "en"])
    (report,) = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    english = sorted(film.name for film in production.Edition("en").films)
    assert [name for name, _size in report["media"]] == english
    with pytest.raises(VerificationError, match="both editions' current films"):
        delivery_verification.main(["--language", "all", *films[1:]])
    with pytest.raises(SystemExit):
        delivery_verification.main(["--language", "fr", *films])
