"""The release manifest's rules, which the comparison holds before any layer: what each edition
publishes, the published assets and film-bound sources against the manifest, its checksums and
its own consistency."""

import json

import pytest

import filmkit.delivery.packaging as packaging
import filmkit.delivery.reproduction as reproduction
import filmkit.picture.rendering as picture_rendering
import filmkit.production as production
from filmkit.delivery.reproduction import ReproductionError

pytestmark = pytest.mark.ffmpeg


def test_a_release_publishes_every_edition_s_films_without_captions_or_none(release):
    path = release.root / reproduction.MANIFEST
    manifest = json.loads(path.read_text())
    manifest["editions"]["en"].pop("uncaptioned_stage_sha256")
    path.write_text(json.dumps(manifest))
    with pytest.raises(ReproductionError, match="uncaptioned picture's stage exactly when"):
        reproduction.load()
    # One edition's films without captions, and not the other's, name no complete release.
    (release.folder / "sample-reel-en-uhd-uncaptioned.mp4").unlink()
    release.record()
    with pytest.raises(ReproductionError, match="does not name every published asset"):
        reproduction.load()


def test_a_review_that_does_not_bind_the_published_films_fails(release):
    edition = production.Edition("en")
    path = release.folder / reproduction.release_name(edition, edition.production_review)
    review = json.loads(path.read_text())
    review["media"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(review))
    release.record()
    report = release.compare()
    assert report["editions"]["en"]["review"]["verdict"] == "fail"
    assert "current delivered edition" in report["editions"]["en"]["review"]["reason"]
    assert report["verdict"] == "fail"


def test_a_published_asset_that_differs_from_the_manifest_refuses_before_any_layer(
    release, released
):
    (release.folder / "sample-reel-zh.srt").write_text("edited\n")
    refused = r"published asset differs from the release manifest: sample-reel-zh\.srt"
    with pytest.raises(ReproductionError, match=refused):
        release.compare()
    with pytest.raises(SystemExit, match=refused):
        released()


def test_a_film_bound_source_that_differs_from_the_manifest_refuses_before_any_layer(release):
    (release.root / picture_rendering.COMPOSITION_SCRIPT).write_text("/* edited */")
    with pytest.raises(
        ReproductionError,
        match=r"film-bound sources differ from the release manifest: picture/film\.js",
    ):
        release.compare()


@pytest.mark.usefixtures("release")
def test_checksums_list_every_other_asset_for_shasum():
    manifest = reproduction.load()
    lines = reproduction.checksums(manifest).splitlines()
    names = [line.split("  ", 1)[1] for line in lines]
    assert names == sorted(asset.name for asset in manifest.assets if asset.name != "SHA256SUMS")
    assert all(len(line.split("  ", 1)[0]) == 64 for line in lines)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda manifest: manifest["editions"].pop("en"), "records the editions"),
        (
            lambda manifest: manifest["assets"].pop(0),
            "does not name every published asset of the editions",
        ),
        (
            lambda manifest: manifest["editions"]["zh"].update(soundtrack_sha256="abc"),
            "is not a release manifest",
        ),
        (
            lambda manifest: manifest["editions"]["zh"]["picture_floor_db"].update(
                {"sample-reel-zh.srt": 30.0}
            ),
            "records a floor for an asset that is not a film",
        ),
        (
            lambda manifest: manifest["assets"][-1].update(sha256="0" * 64),
            "SHA256SUMS differs from the assets it lists",
        ),
        (lambda manifest: manifest.pop("sources"), "is not a release manifest"),
        (
            lambda manifest: manifest["sources"].update({"../film.js": "0" * 64}),
            "is not a release manifest",
        ),
    ],
)
def test_an_inconsistent_manifest_is_refused(release, change, message):
    path = release.root / reproduction.MANIFEST
    manifest = json.loads(path.read_text())
    change(manifest)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ReproductionError, match=message):
        reproduction.load()


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda manifest: manifest["editions"].pop("en"), "records the editions"),
        (
            lambda manifest: manifest["assets"].pop(0),
            "does not name every published asset of the editions",
        ),
        (
            lambda manifest: manifest["editions"]["en"].pop("uncaptioned_stage_sha256"),
            "uncaptioned picture's stage exactly when",
        ),
        (
            lambda manifest: manifest["editions"]["zh"]["picture_floor_db"].update(
                {"sample-reel-zh.srt": 30.0}
            ),
            "records a floor for an asset that is not a film",
        ),
        (
            lambda manifest: manifest["assets"][-1].update(sha256="0" * 64),
            "SHA256SUMS differs from the assets it lists",
        ),
    ],
)
def test_the_check_refuses_a_record_in_memory_as_load_refuses_it_on_disk(release, change, message):
    path = release.root / reproduction.MANIFEST
    manifest = json.loads(path.read_text())
    # The record as it stands passes, and the check hands it back.
    faithful = reproduction.Release.model_validate(manifest)
    assert reproduction.check(faithful) is faithful
    change(manifest)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ReproductionError, match=message) as on_disk:
        reproduction.load()
    # The same record, not yet written: the check reads no manifest, and words it as `load` does.
    path.unlink()
    with pytest.raises(ReproductionError, match=message) as in_memory:
        reproduction.check(reproduction.Release.model_validate(manifest))
    assert str(in_memory.value) == str(on_disk.value)


@pytest.mark.usefixtures("release")
def test_each_edition_publishes_its_films_documents_cover_and_review():
    edition = production.Edition("en")
    published = reproduction.members(edition)
    assert published["sample-reel-en-cover.png"] == (
        "document",
        edition.artifacts / packaging.COVER_PNG,
    )
    assert published["sample-reel-en-production-review.json"] == (
        "review",
        edition.production_review,
    )
    assert [name for name, (layer, _) in published.items() if layer == "film"] == [
        film.name for film in edition.films
    ]


def test_a_record_of_a_film_of_three_editions_names_the_edition_it_misses(release, monkeypatch):
    monkeypatch.setattr(production, "CODES", ("zh", "en", "xb"))
    with pytest.raises(ReproductionError) as refusal:
        reproduction.load()
    assert "records the editions ['en', 'zh']: no record of the xb edition" in str(refusal.value)
