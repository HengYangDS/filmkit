"""The writer of the release record: what it asks before it writes, and each refusal."""

import json
import shutil

import pytest
from pydantic import TypeAdapter
from release_build import DECLARED, SOURCES, refused, uncaptioned_stage, unchanged_refusal

import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.packaging as packaging
import filmkit.delivery.release as release
import filmkit.delivery.reproduction as reproduction
import filmkit.repository as repository
from filmkit.graph import records, runs
from filmkit.production import CODES, STAGE_PAGE

# The sample film declares review levels; these reviews keep the overall and dimension floors.
pytestmark = pytest.mark.usefixtures("unleveled")


# What the writer asks (task 2.1).


def test_a_build_that_the_films_folder_below_a_host_root_holds_passes_every_check(built):
    before = built.tree()
    release.main(["--dry-run"])
    # The staging was asked for each edition's uncaptioned stage, which a derived picture's
    # receipt does not bind.
    assert built.asked == [(code, uncaptioned_stage(code), False) for code in CODES]
    assert built.tree() == before


def test_a_moved_soundtrack_refuses_as_the_verifier_words_it(built):
    built.editions["en"].edition.soundtrack.write_bytes(b"another soundtrack")
    assert unchanged_refusal(built) == "en: Narration custody differs from the current script"


def test_an_edition_without_its_film_s_still_scan_refuses_as_the_scan_words_it(built):
    # The still scan's requirement is one of the bound inputs the verifier gives, so the writer
    # asks it with them and states no requirement of its own.
    built.editions["en"].edition.film_stills.unlink()
    assert (
        unchanged_refusal(built)
        == "en: The en film has no still scan record; run filmkit build scan-film:en"
    )


def test_a_stale_uncaptioned_stage_of_a_derived_picture_refuses_naming_edition_and_picture(built):
    edition = built.editions["zh"].edition
    receipt = repository.read(edition.rendered(captions=False).receipt)
    assert isinstance(receipt["derived"], dict)
    (uncaptioned_stage("zh") / STAGE_PAGE).write_text("<html>stale</html>")
    assert unchanged_refusal(built) == (
        "zh: uncaptioned picture: "
        "The staged document differs from the one the current sources derive"
    )


def test_an_edition_without_a_review_record_refuses_naming_the_record(built):
    built.editions["en"].edition.production_review.unlink()
    assert unchanged_refusal(built) == (
        "en: No review record build/evidence/editions/en/production-review.json"
    )


def test_a_folder_that_holds_an_earlier_build_refuses_naming_its_members(built):
    # A build delivered only to a folder named with --destination leaves the film's own folder
    # with the build before.
    (built.folder / "zh/sample-reel-zh-uhd.mp4").write_text("an earlier build\n")
    (built.folder / "en/sample-reel-en.vtt").unlink()
    line = unchanged_refusal(built)
    assert f"The film's delivery folder {built.folder}, which FILMKIT_DELIVERY_ROOT gave" in line
    assert "zh/sample-reel-zh-uhd.mp4 holds other bytes" in line
    assert "en/sample-reel-en.vtt is missing" in line
    # A folder that holds nothing names its first members and counts the rest.
    shutil.rmtree(built.folder)
    line = unchanged_refusal(built)
    assert "index.html is missing, zh/sample-reel-zh-uhd.mp4 is missing" in line
    assert "and 20 more" in line


def test_a_host_root_that_is_no_absolute_path_refuses_in_the_deliverys_words(built, monkeypatch):
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, "films")
    line = unchanged_refusal(built)
    assert line.startswith("FILMKIT_DELIVERY_ROOT names no absolute path ('films')")


def test_a_pre_release_version_refuses_naming_the_version(built):
    built.version("1.4.0-rc.1")
    line = unchanged_refusal(built)
    assert "VERSION holds '1.4.0-rc.1'" in line
    assert "three numbers" in line


@pytest.mark.parametrize("held", ["{}", "not a manifest", '{"version": "1.2"}'])
def test_a_tracked_manifest_that_is_none_refuses_naming_the_file(built, held):
    built.manifest.write_text(held)
    line = unchanged_refusal(built)
    assert line.startswith("release.json is not a release manifest")


def test_a_film_that_declares_no_source_is_refused_naming_the_key(built):
    # With no record to replace and with one that lists sources: the command takes no list
    # from the record.
    for tracked in (False, True):
        if tracked:
            built.track()
        assert unchanged_refusal(built, sources=[]) == (
            "content/film.toml declares no film-bound source in [release] sources: declare "
            "there each tracked file whose exact bytes the build of the published films reads"
        )


def test_a_source_that_is_gone_refuses_naming_the_path(built):
    line = unchanged_refusal(built, sources=[*SOURCES, "content/gone.json"])
    assert line == f"{DECLARED} is no file: content/gone.json"
    # A folder is no file either.
    line = unchanged_refusal(built, sources=["content", *SOURCES])
    assert line == f"{DECLARED} is no file: content"


def test_the_checks_refuse_in_their_order_and_the_first_stops_the_command(built):
    english = built.editions["en"]
    edition = english.edition
    soundtrack = edition.soundtrack.read_bytes()
    built.version("1.4.0-rc.1")
    edition.soundtrack.write_bytes(b"another soundtrack")
    (uncaptioned_stage("en") / STAGE_PAGE).write_text("<html>stale</html>")
    edition.production_review.unlink()
    (built.folder / "index.html").unlink()
    built.manifest.write_text("{}")
    # The sources declared are asked last: every other refusal comes before this one's.
    built.declare(["content/absent.json"])
    absent = []
    assert refused(absent).startswith("en: Narration custody differs")
    # The Chinese edition was asked whole before the English one, whose stage was not reached.
    assert built.asked == [("zh", uncaptioned_stage("zh"), False)]
    edition.soundtrack.write_bytes(soundtrack)
    assert refused(absent).startswith("en: uncaptioned picture: The staged document differs")
    (uncaptioned_stage("en") / STAGE_PAGE).write_text("<html>uncaptioned</html>")
    assert refused(absent).startswith("en: No review record")
    english.review()
    assert "index.html is missing" in refused(absent)
    built.deliver()
    assert "three numbers" in refused(absent)
    built.version(built.fixture_version)
    assert refused(absent).startswith("release.json is not a release manifest")
    built.manifest.unlink()
    assert refused(absent) == f"{DECLARED} is no file: content/absent.json"


def test_a_path_the_manifests_model_does_not_list_is_refused_by_that_models_rule(built):
    # Each of these is a file. The rule is the model's alone, so the refusal names the model and
    # prints its pattern, which is true of every path it refuses: one below the root with a name
    # that begins with a dot or holds a space, as one from the top or with ./ or .. in it.
    for name in (".config/policy.toml", "content/My Notes.md"):
        (built.root / name).parent.mkdir(parents=True, exist_ok=True)
        (built.root / name).write_text("stated\n")
    absolute = str(built.root / SOURCES[0])
    pattern = TypeAdapter(reproduction.SourcePath).json_schema()["pattern"]
    for stated in (
        *(".config/policy.toml", "content/My Notes.md"),
        *(absolute, f"./{SOURCES[0]}", f"content/../{SOURCES[0]}"),
    ):
        line = unchanged_refusal(built, sources=[stated, *SOURCES[1:]])
        assert line == (
            f"{DECLARED} is no path as the release manifest's model lists one "
            f"(reproduction.SourcePath: {pattern}): {stated}"
        )


def test_the_record_itself_is_no_source(built):
    # Before a first record is written, and beside one that stands.
    stated = [str(reproduction.MANIFEST), *SOURCES]
    refusal = f"{DECLARED} is or leads to the release record itself, which lists the sources "
    refusal += "and is none"
    first = unchanged_refusal(built, sources=stated)
    assert first == f"{refusal}: {reproduction.MANIFEST}"
    built.track()
    assert unchanged_refusal(built, sources=stated) == first
    # A link elsewhere below the root that leads to the record is refused as the record.
    (built.root / "content/alias.json").symlink_to(built.manifest)
    line = unchanged_refusal(built, sources=["content/alias.json", *SOURCES])
    assert line == f"{refusal}: content/alias.json"


def test_a_path_below_the_films_generated_folder_is_no_source(built):
    generated = "build/artifacts/film/zh/sample-reel-zh.srt"
    assert (built.root / generated).is_file()
    refusal = f"{DECLARED} lies or leads below build/, which holds what the engine generates"
    line = unchanged_refusal(built, sources=[generated, *SOURCES])
    assert line == f"{refusal}: {generated}"
    # A link elsewhere below the root that leads there is refused the same way.
    (built.root / "content/captions.srt").symlink_to(built.root / generated)
    line = unchanged_refusal(built, sources=["content/captions.srt", *SOURCES])
    assert line == f"{refusal}: content/captions.srt"


def test_a_link_that_leads_outside_the_films_root_is_no_source(built):
    elsewhere = built.folder.parent / "another-films-script.json"
    elsewhere.write_text("{}\n")
    (built.root / "content/linked.json").symlink_to(elsewhere)
    line = unchanged_refusal(built, sources=["content/linked.json", *SOURCES])
    assert line == f"{DECLARED} leads outside the film's root: content/linked.json"


# The record is written only after `filmkit verify` passes (record-every-run).


def test_a_soundtrack_changed_by_no_declared_writer_refuses_the_release_and_its_dry_run(
    built, table_of
):
    table_of("assemble")
    with runs.run("zh", "assemble"):
        pass
    soundtrack = built.editions["zh"].edition.soundtrack
    soundtrack.write_bytes(soundtrack.read_bytes() + b"changed by hand")
    for arguments in (["--dry-run"], []):
        assert unchanged_refusal(built, arguments).startswith(
            f"filmkit verify refuses: {repository.relative(soundtrack)}: its bytes are "
            "accounted for by no record of a declared writer; it is bound by assemble:zh"
        )


def test_a_release_is_recorded_after_both_editions_wrote_the_entry_page(built, table_of):
    table_of("package-metadata")
    # One package writes the page first and the other replaces it whole, with the bytes the
    # build holds, which the viewing packages bind.
    page = repository.ROOT / packaging.LANGUAGE_INDEX
    pages = (b"the entry page as the first package wrote it\n", page.read_bytes())
    for code, written in zip(CODES, pages, strict=True):
        with runs.run(code, "package-metadata"):
            page.write_bytes(written)
    bound = [
        records.read(records.place("package-metadata", code)).outputs["entry"] for code in CODES
    ]
    assert bound[0].sha256 != bound[1].sha256 == records.digest(page)
    release.main([])
    assert built.manifest.is_file()


# The record stands at the film's root, its sources declared (design decision 15 of
# build-a-film-by-its-verbs).


def test_a_release_is_written_at_the_films_root_from_the_declared_sources(built):
    built.declare(SOURCES[:2])
    release.main([])
    written = json.loads((built.root / "release.json").read_text())
    assert written["sources"] == {path: repository.sha(path) for path in SOURCES[:2]}
    assert not (built.root / "content/release.json").exists()
