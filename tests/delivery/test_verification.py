"""The verifier's qualification of an edition and its command."""

import json

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.still_scan as picture_still_scan
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.verification import VerificationError
from filmkit.graph import cli


@pytest.fixture
def checked(tmp_path, monkeypatch):
    """Every check of an edition that the verifier owns replaced by a marker of its call, below
    an empty root."""
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


@pytest.fixture
def qualified(checked, monkeypatch):
    """Every check of an edition replaced by a marker of its call, the requirement of the film's
    still scan among them, which the scan owns."""
    monkeypatch.setattr(picture_still_scan, "require_film_scan", lambda _edition: "still_scan")


@pytest.mark.usefixtures("checked")
@pytest.mark.parametrize("technical_only", [True, False])
def test_an_edition_without_its_film_s_still_scan_is_refused_in_either_scope(technical_only):
    # The root holds no record, so the scan's own requirement refuses, and the verifier reports
    # it as it reports every owner's refusal, naming the first edition.
    with pytest.raises(SystemExit) as stopped:
        list(delivery_verification.qualified(technical_only=technical_only))
    assert (
        stopped.value.code
        == "zh: The zh film has no still scan record; run filmkit build scan-film:zh"
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
        "still_scan",
        "media",
        "media_seconds",
        "spotlight",
        "review",
        "limits",
    ]
    assert (report["verdict"], report["scope"], report["language"]) == ("pass", "acceptance", "en")
    assert report["still_scan"] == "still_scan"
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
        assert list(bound) == ["sources", "narration", "picture", "package", "still_scan"]
        assert bound["sources"]["documents"] == "not_checked"
        assert bound["narration"]["soundtrack_sha256"] == repository.sha(edition.soundtrack)
        assert bound["picture"]["picture_sha256"] == repository.sha(edition.picture)
        assert bound["package"]["films"] == sorted(film.name for film in edition.films)
        # The still scan's requirement is one of them, answered from the film's record.
        scanned = edition.film(picture_still_scan.SCANNED_FILM).name
        assert bound["still_scan"]["film"] == scanned
        accepted = delivery_verification.verify_review(edition, edition.films)
        assert accepted["path"] == f"build/evidence/editions/{code}/production-review.json"
        # The verifier's command asks the same checks and then decodes the films.
        with pytest.raises(DecodedError):
            delivery_verification.qualify(edition, edition.films)


@pytest.mark.usefixtures("qualified")
def test_the_verifier_reports_the_bound_inputs_where_it_reported_them(monkeypatch):
    edition = production.Edition("zh")
    assert delivery_verification.verify_bindings(edition) == {
        name: name for name in ("sources", "narration", "picture", "package", "still_scan")
    }
    # The command's report holds what the one check gives, in the phase it ran them in.
    phases = []
    monkeypatch.setattr(
        delivery_verification, "verify_bindings", lambda _edition: {"bound": phases[-1]}
    )
    phase = delivery_verification.seam.phase

    def named(name):
        phases.append(name)
        return phase(name)

    monkeypatch.setattr(delivery_verification.seam, "phase", named)
    report = delivery_verification.qualify(edition, edition.films, technical_only=True)
    assert report["bound"] == "bindings"
    assert phases == ["bindings", "media", "spotlight"]


@pytest.mark.usefixtures("qualified")
def test_each_editions_report_is_given_in_either_scope_and_nothing_is_written(tmp_path, capsys):
    # Each edition's current delivered films are verified, and their reports printed.
    delivery_verification.verify_editions(technical_only=True)
    reports = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [(report["language"], report["scope"]) for report in reports] == [
        ("zh", "technical"),
        ("en", "technical"),
    ]
    english = sorted(film.name for film in production.Edition("en").films)
    assert [name for name, _size in reports[1]["media"]] == english
    accepted = list(delivery_verification.qualified(technical_only=False))
    assert [(report["language"], report["scope"]) for report in accepted] == [
        ("zh", "acceptance"),
        ("en", "acceptance"),
    ]
    assert sorted(tmp_path.rglob("*.*")) == []


def verb(capsys, *arguments: str) -> tuple[int | str, list[str]]:
    """`filmkit verify` with the arguments: its exit status or refusal, 0 where it returned, and
    its printed lines."""
    try:
        cli.main(["verify", *arguments])
    except SystemExit as stopped:
        return stopped.code, capsys.readouterr().out.splitlines()
    return 0, capsys.readouterr().out.splitlines()


@pytest.mark.usefixtures("checked")
def test_filmkit_verify_technical_only_reads_the_films_only_after_the_records(
    tmp_path, table_of, capsys, monkeypatch
):
    decoded = []
    monkeypatch.setattr(
        delivery_verification, "verify_films", lambda *_: decoded.append("films") or {}
    )
    # Every node of the engine's table is without its record below the empty root: the records
    # refuse, and no film is decoded.
    status, lines = verb(capsys, "--technical-only")
    assert status == 1
    assert lines[0].startswith("refused: no record: ")
    assert decoded == []
    # Held to no node, the records pass; the still scan's own requirement then refuses the first
    # edition in one line that names it.
    table_of()
    status, lines = verb(capsys, "--technical-only")
    assert status == "zh: The zh film has no still scan record; run filmkit build scan-film:zh"
    assert lines == [lines[0]] and lines[0].startswith("filmkit verify passes")
    monkeypatch.setattr(picture_still_scan, "require_film_scan", lambda _edition: "still_scan")
    status, lines = verb(capsys, "--technical-only")
    assert status == 0
    reports = [json.loads(line) for line in lines[1:]]
    assert [(r["language"], r["scope"], r["review"]["verdict"]) for r in reports] == [
        ("zh", "technical", "not_reviewed"),
        ("en", "technical", "not_reviewed"),
    ]
    assert decoded == ["films", "films"]
    assert sorted(tmp_path.rglob("*")) == []


def test_captions_end_where_the_timeline_s_credits_begin():
    # A runtime of 1476 s whose credits, as laid out, last 3.56 s: they begin at 1472.44 s.
    def timeline(end):
        caption = {"start": 1470.0, "end": end, "text": "数据先行。"}
        return {"duration": 1476, "credits_duration": 3.56, "captions": [caption]}

    assert delivery_verification.verify_captions(timeline(1472.44), "zh") == 1
    with pytest.raises(VerificationError, match="caption contract"):
        delivery_verification.verify_captions(timeline(1472.45), "zh")
    with pytest.raises(VerificationError, match="states no credits within its runtime"):
        delivery_verification.verify_captions({**timeline(1472.0), "credits_duration": None}, "zh")
