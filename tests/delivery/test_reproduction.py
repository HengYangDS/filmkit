"""The comparison of a rebuild with the published release under the reproduction standard,
layer by layer, across the encoders' versions and through `filmkit verify --release`."""

import json
import shutil

import pytest
from reproducing import ANOTHER, RECORDED, drawn_digest, listing, packaged_anew

import filmkit.delivery.reproduction as reproduction
import filmkit.production as production
import filmkit.repository as repository
from filmkit.graph import cli

pytestmark = pytest.mark.ffmpeg


@pytest.mark.usefixtures("unleveled")
def test_a_film_that_holds_the_published_bytes_passes_every_layer_and_is_not_decoded(
    release, decodes
):
    report = release.compare()
    assert report["verdict"] == "pass"
    assert decodes == []
    uhd = report["editions"]["zh"]["films"][0]
    assert uhd["identical_file"] is True
    assert uhd["sha256"] == repository.sha(release.folder / "sample-reel-zh-uhd.mp4")
    assert (uhd["audio"], uhd["container"]) == ("identical", "identical")
    # Nothing was decoded: the report counts no frame and measures no PSNR.
    unmeasured = dict.fromkeys(("identical_frames", "minimum_db", "mean_db"))
    assert (uhd["frames"], uhd["failing"], uhd["verdict"]) == (None, [], "pass")
    assert uhd["psnr"] == {"floor_db": 30.0, "measured": False, "lowest": [], "below_floor": []} | (
        unmeasured
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda film: film.write_bytes(film.read_bytes()[:-1] + b"\xff"),
        lambda film: film.write_bytes(film.read_bytes() + b"\x00"),
    ],
    ids=["one byte changed", "one byte longer"],
)
def test_a_film_that_differs_by_one_byte_is_decoded(release, decodes, change):
    change(production.Edition("zh").film("uhd"))
    films = release.compare()["editions"]["zh"]["films"]
    assert decodes == ["sample-reel-zh-uhd.mp4"]
    assert (films[0]["identical_file"], films[0]["frames"]) == (False, 6)
    assert (films[0]["psnr"]["measured"], films[0]["psnr"]["identical_frames"]) == (True, 6)
    assert "sha256" not in films[0]
    assert [film["identical_file"] for film in films[1:]] == [True, True, True]


@pytest.mark.usefixtures("unleveled")
def test_without_a_floor_a_film_that_holds_the_published_bytes_calibrates_none(
    release, decodes, released
):
    release.record(floors=None)
    report = release.compare()
    assert decodes == []
    assert report["verdict"] == "calibrating"
    uhd = report["editions"]["zh"]["films"][0]
    assert (uhd["identical_file"], uhd["verdict"]) == (True, "calibrating")
    psnr = uhd["psnr"]
    assert (psnr["floor_db"], psnr["measured"], psnr["minimum_db"]) == (None, False, None)
    assert "calibrates no floor" in uhd["note"]
    with pytest.raises(SystemExit, match="calibrating"):
        released()


@pytest.mark.usefixtures("unleveled")
def test_a_faithful_rebuild_passes_and_reports_every_layer(release):
    # A rebuilt film is packaged anew: it decodes as the published film without holding its bytes.
    shutil.copyfile(release.films["later"], production.Edition("zh").film("uhd"))
    report = release.compare()
    assert report["verdict"] == "pass"
    assert report["release"] == "1.0.0"
    zh = report["editions"]["zh"]
    assert {zh["soundtrack"]["verdict"], zh["stage"]["verdict"], zh["review"]["verdict"]} == {
        "pass"
    }
    assert [document["asset"] for document in zh["documents"]] == [
        "sample-reel-zh.srt",
        "sample-reel-zh.vtt",
        "sample-reel-zh-transcript.md",
        "sample-reel-zh-cover.png",
    ]
    uhd = zh["films"][0]
    assert uhd["asset"] == "sample-reel-zh-uhd.mp4"
    assert (uhd["frames"], uhd["audio"], uhd["container"]) == (6, "identical", "identical")
    assert (uhd["identical_file"], uhd["psnr"]["measured"]) == (False, True)
    assert uhd["psnr"]["identical_frames"] == 6
    assert uhd["psnr"]["minimum_db"] is None
    assert uhd["verdict"] == "pass"


@pytest.mark.usefixtures("unleveled")
def test_filmkit_verify_release_compares_only_after_the_records_and_writes_nothing(
    release, decodes, released, capsys
):
    # One byte changed: the comparison would decode the film.
    film = production.Edition("zh").film("uhd")
    film.write_bytes(film.read_bytes() + b"\x00")
    before = listing(release.root)
    # Every node of the engine's table is without its record below the release's root: the
    # records refuse, and no film is decoded.
    with pytest.raises(SystemExit) as stopped:
        cli.main(["verify", "--release"])
    lines = capsys.readouterr().out.splitlines()
    assert stopped.value.code == 1 and lines[0].startswith("refused: no record: ")
    assert decodes == []
    status, lines = released()
    assert status == 0
    assert lines[0].startswith("filmkit verify passes")
    assert json.loads(lines[1]) == {"verdict": "pass", "release": "1.0.0"}
    assert decodes == ["sample-reel-zh-uhd.mp4"]
    assert listing(release.root) == before


@pytest.mark.usefixtures("unleveled")
def test_without_a_floor_the_comparison_reports_the_lowest_frames_and_does_not_pass(
    release, released
):
    shutil.copyfile(release.films["picture"], production.Edition("zh").film("uhd"))
    release.record(floors=None)
    report = release.compare()
    assert report["verdict"] == "calibrating"
    psnr = report["editions"]["zh"]["films"][0]["psnr"]
    assert (psnr["floor_db"], psnr["identical_frames"]) == (None, 0)
    lowest = [frame["psnr_db"] for frame in psnr["lowest"]]
    assert lowest == sorted(lowest)
    assert psnr["minimum_db"] == lowest[0]
    with pytest.raises(SystemExit, match="calibrating"):
        released()


def test_a_frame_below_its_floor_fails_naming_the_film_and_frame(release, released):
    shutil.copyfile(release.films["picture"], production.Edition("en").film("1080p-captioned"))
    film = release.compare()["editions"]["en"]["films"][1]
    assert film["verdict"] == "fail"
    assert film["psnr"]["below_floor"][0] == 0
    with pytest.raises(SystemExit, match=r"en: sample-reel-en-1080p-captioned\.mp4: picture"):
        released()


def test_under_the_recorded_ffmpeg_a_film_is_compared_as_before(release, decodes):
    packaged_anew(release, "zh")
    uhd = release.compare()["editions"]["zh"]["films"][0]
    assert uhd["encoders"] == {"recorded": RECORDED, "running": RECORDED}
    assert uhd["compared"] == {"audio": "decoded", "picture": "decoded frames against the floor"}
    assert (uhd["psnr"]["measured"], uhd["verdict"]) == (True, "pass")
    assert sorted(decodes) == sorted(film.name for film in production.Edition("zh").films)


@pytest.mark.usefixtures("unleveled")
def test_under_another_ffmpeg_audio_and_pictures_are_compared_before_encoding(release, decodes):
    packaged_anew(release, *production.CODES)
    release.running = ANOTHER
    report = release.compare()
    assert (report["verdict"], report["ffmpeg"]) == ("pass", ANOTHER)
    # No film is decoded: each picture is held to its drawn-frame digest.
    assert decodes == []
    for code, edition in report["editions"].items():
        for film in edition["films"]:
            picture = "captioned" if "-uncaptioned" not in film["asset"] else "uncaptioned"
            assert film["encoders"] == {"recorded": RECORDED, "running": ANOTHER}
            assert film["compared"] == {
                "audio": "before encoding: the soundtrack's bytes",
                "picture": f"before encoding: the {picture} picture's drawn-frame digest",
            }
            digest = drawn_digest(code, picture)
            assert film["drawn_sha256"] == {"recorded": digest, "rebuilt": digest}
            assert (film["frames"], film["audio"], film["psnr"]["measured"]) == (
                6,
                "identical",
                False,
            )
            assert film["verdict"] == "pass"
    # The audio is held to the soundtrack's bytes.
    production.Edition("en").soundtrack.write_bytes(b"another soundtrack")
    english = release.compare()["editions"]["en"]
    assert english["soundtrack"]["verdict"] == "fail"
    assert {film["audio"] for film in english["films"]} == {"differs"}


def test_under_another_ffmpeg_a_picture_drawn_otherwise_is_refused(release, decodes, released):
    packaged_anew(release, "zh")
    receipt = production.Edition("zh").rendered(captions=True).receipt
    repository.write(receipt, {"picture": "captioned", "drawn_sha256": "0" * 64})
    release.running = ANOTHER
    films = release.compare()["editions"]["zh"]["films"]
    assert [film["failing"] for film in films] == [["picture"], ["picture"], [], []]
    assert films[0]["drawn_sha256"] == {
        "recorded": drawn_digest("zh", "captioned"),
        "rebuilt": "0" * 64,
    }
    assert decodes == []
    with pytest.raises(SystemExit, match=r"zh: sample-reel-zh-uhd\.mp4: picture"):
        released()


@pytest.mark.usefixtures("unleveled")
def test_across_encoders_a_derived_picture_is_compared_by_decoded_frames(release, decodes):
    english = production.Edition("en")
    derived = {"picture": "uncaptioned", "derived": {"rows": [1872, 2048]}}
    repository.write(english.rendered(captions=False).receipt, derived)
    release.record()
    assert "uncaptioned" not in reproduction.load().editions["en"].drawn_sha256
    packaged_anew(release, "en")
    release.running = ANOTHER
    report = release.compare()
    assert report["verdict"] == "pass"
    films = {film["asset"]: film for film in report["editions"]["en"]["films"]}
    uncaptioned = {name for name in films if "-uncaptioned" in name}
    assert set(decodes) == uncaptioned and len(decodes) == 2
    for name, film in films.items():
        decoded = name in uncaptioned
        assert film["compared"]["picture"].startswith("decoded") is decoded
        assert film["psnr"]["measured"] is decoded
        assert (film["psnr"]["floor_db"], film["verdict"]) == (30.0, "pass")


@pytest.mark.usefixtures("unleveled")
def test_a_record_without_encoders_compares_films_of_an_unknown_encoder(release, decodes):
    release.record(encoders=False)
    packaged_anew(release, "zh")
    report = release.compare()
    assert report["verdict"] == "pass"
    films = report["editions"]["zh"]["films"]
    assert sorted(decodes) == sorted(film["asset"] for film in films)
    for film in films:
        assert film["encoders"] == {"recorded": None, "running": RECORDED}
        assert film["compared"] == {
            "audio": "before encoding: the soundtrack's bytes",
            "picture": "decoded frames against the floor",
        }
        assert "encoder is unknown" in film["note"]
        assert (film["psnr"]["floor_db"], film["verdict"]) == (30.0, "pass")
    production.Edition("zh").soundtrack.write_bytes(b"another soundtrack")
    films = release.compare()["editions"]["zh"]["films"]
    assert {film["audio"] for film in films} == {"differs"}


def test_a_film_packaged_later_differs_only_in_its_creation_date(release):
    shutil.copyfile(release.films["later"], production.Edition("zh").film("uhd"))
    film = release.compare()["editions"]["zh"]["films"][0]
    assert (film["container"], film["audio"], film["verdict"]) == ("identical", "identical", "pass")


def test_different_decoded_audio_fails(release):
    shutil.copyfile(release.films["sound"], production.Edition("zh").film("uhd"))
    film = release.compare()["editions"]["zh"]["films"][0]
    assert (film["audio"], film["verdict"]) == ("differs", "fail")


@pytest.mark.parametrize(
    ("change", "layer"),
    [
        (lambda edition: edition.soundtrack.write_bytes(b"another soundtrack"), "soundtrack"),
        (
            lambda edition: edition.rendered().page.write_text("<html></html>"),
            "stage",
        ),
        (
            lambda edition: edition.rendered(captions=False).page.write_text("<html></html>"),
            "uncaptioned_stage",
        ),
        (
            lambda edition: (edition.artifacts / "sample-reel-zh.vtt").write_text("WEBVTT\n"),
            "documents",
        ),
    ],
)
def test_a_rebuilt_byte_that_differs_fails_naming_the_edition_and_layer(
    release, released, change, layer
):
    change(production.Edition("zh"))
    report = release.compare()
    assert report["verdict"] == "fail"
    with pytest.raises(SystemExit, match=f"zh: .*{layer}"):
        released()


@pytest.mark.usefixtures("unleveled")
def test_a_release_without_the_films_without_captions_compares_the_films_it_published(release):
    # A release published before the films without captions existed holds each edition's two
    # films with captions, and its reviews bind those.
    for code in production.CODES:
        edition = production.Edition(code)
        for kind in ("uhd-uncaptioned", "1080p-uncaptioned"):
            (release.folder / edition.film(kind).name).unlink()
        path = release.folder / reproduction.release_name(edition, edition.production_review)
        review = json.loads(path.read_text())
        review["media"] = [item for item in review["media"] if "uncaptioned" not in item["path"]]
        path.write_text(json.dumps(review))
    release.record()
    report = release.compare()
    assert report["verdict"] == "pass"
    zh = report["editions"]["zh"]
    assert [film["asset"] for film in zh["films"]] == [
        "sample-reel-zh-uhd.mp4",
        "sample-reel-zh-1080p-captioned.mp4",
    ]
    assert zh["unpublished"] == [
        "sample-reel-zh-uhd-uncaptioned.mp4",
        "sample-reel-zh-1080p-uncaptioned.mp4",
    ]
    assert "uncaptioned_stage" not in zh
    assert zh["review"]["verdict"] == "pass"
