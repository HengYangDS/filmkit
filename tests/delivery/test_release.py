"""The writer of the release record: what it asks before it writes, and each refusal."""

import shutil

import pytest
from pydantic import TypeAdapter
from release_build import SOURCES, STATED, refused, uncaptioned_stage, unchanged_refusal

import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.release as release
import filmkit.delivery.reproduction as reproduction
import filmkit.repository as repository
from filmkit.production import CODES

# The sample film declares review levels; these reviews keep the overall and dimension floors.
pytestmark = pytest.mark.usefixtures("unleveled")


# What the writer asks (task 2.1).


def test_a_build_that_the_films_folder_below_a_host_root_holds_passes_every_check(built):
    before = built.tree()
    release.main(["--dry-run", *STATED])
    # The staging was asked for each edition's uncaptioned stage, which a derived picture's
    # receipt does not bind.
    assert built.asked == [(code, uncaptioned_stage(code), False) for code in CODES]
    assert built.tree() == before


def test_a_moved_soundtrack_refuses_as_the_verifier_words_it(built):
    built.editions["en"].edition.soundtrack.write_bytes(b"another soundtrack")
    assert unchanged_refusal(built) == "en: Narration custody differs from the current script"


def test_a_stale_uncaptioned_stage_of_a_derived_picture_refuses_naming_edition_and_picture(built):
    edition = built.editions["zh"].edition
    receipt = repository.read(edition.rendered(captions=False).receipt)
    assert isinstance(receipt["derived"], dict)
    (uncaptioned_stage("zh") / "index.html").write_text("<html>stale</html>")
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
    assert line.startswith("content/release.json is not a release manifest")


def test_a_run_without_its_sources_is_refused_by_the_command_line(built, capsys):
    # With no record to replace and with one that lists sources: the command carries no list.
    for tracked in (False, True):
        if tracked:
            built.track()
        before = built.tree()
        with pytest.raises(SystemExit) as refusal:
            release.main([])
        assert refusal.value.code == 2
        assert "the following arguments are required: --sources" in capsys.readouterr().err
        assert built.tree() == before


def test_a_source_that_is_gone_refuses_naming_the_path(built):
    line = unchanged_refusal(built, [*STATED, "content/gone.json"])
    assert line == "A film-bound source is no file: content/gone.json"
    # A folder is no file either.
    line = unchanged_refusal(built, ["--sources", "content", *SOURCES])
    assert line == "A film-bound source is no file: content"


def test_the_checks_refuse_in_their_order_and_the_first_stops_the_command(built):
    english = built.editions["en"]
    edition = english.edition
    soundtrack = edition.soundtrack.read_bytes()
    built.version("1.4.0-rc.1")
    edition.soundtrack.write_bytes(b"another soundtrack")
    (uncaptioned_stage("en") / "index.html").write_text("<html>stale</html>")
    edition.production_review.unlink()
    (built.folder / "index.html").unlink()
    built.manifest.write_text("{}")
    # The sources stated are asked last: every other refusal comes before this one's.
    absent = ["--sources", "content/absent.json"]
    assert refused(absent).startswith("en: Narration custody differs")
    # The Chinese edition was asked whole before the English one, whose stage was not reached.
    assert built.asked == [("zh", uncaptioned_stage("zh"), False)]
    edition.soundtrack.write_bytes(soundtrack)
    assert refused(absent).startswith("en: uncaptioned picture: The staged document differs")
    (uncaptioned_stage("en") / "index.html").write_text("<html>uncaptioned</html>")
    assert refused(absent).startswith("en: No review record")
    english.review()
    assert "index.html is missing" in refused(absent)
    built.deliver()
    assert "three numbers" in refused(absent)
    built.version(built.fixture_version)
    assert refused(absent).startswith("content/release.json is not a release manifest")
    built.manifest.unlink()
    assert refused(absent) == "A film-bound source is no file: content/absent.json"


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
        line = unchanged_refusal(built, ["--sources", stated, *SOURCES[1:]])
        assert line == (
            "A film-bound source is no path as the release manifest's model lists one "
            f"(reproduction.SourcePath: {pattern}): {stated}"
        )


def test_the_record_itself_is_no_source(built):
    # Before a first record is written, and beside one that stands.
    stated = ["--sources", str(reproduction.MANIFEST), *SOURCES]
    refusal = "A film-bound source is or leads to the release record itself, which lists the "
    refusal += "sources and is none"
    first = unchanged_refusal(built, stated)
    assert first == f"{refusal}: {reproduction.MANIFEST}"
    built.track()
    assert unchanged_refusal(built, stated) == first
    # A link elsewhere below the root that leads to the record is refused as the record.
    (built.root / "content/alias.json").symlink_to(built.manifest)
    line = unchanged_refusal(built, ["--sources", "content/alias.json", *SOURCES])
    assert line == f"{refusal}: content/alias.json"


def test_a_path_below_the_films_generated_folder_is_no_source(built):
    generated = "build/artifacts/film/zh/sample-reel-zh.srt"
    assert (built.root / generated).is_file()
    refusal = (
        "A film-bound source lies or leads below build/, which holds what the engine generates"
    )
    line = unchanged_refusal(built, ["--sources", generated, *SOURCES])
    assert line == f"{refusal}: {generated}"
    # A link elsewhere below the root that leads there is refused the same way.
    (built.root / "content/captions.srt").symlink_to(built.root / generated)
    line = unchanged_refusal(built, ["--sources", "content/captions.srt", *SOURCES])
    assert line == f"{refusal}: content/captions.srt"


def test_a_link_that_leads_outside_the_films_root_is_no_source(built):
    elsewhere = built.folder.parent / "another-films-script.json"
    elsewhere.write_text("{}\n")
    (built.root / "content/linked.json").symlink_to(elsewhere)
    line = unchanged_refusal(built, ["--sources", "content/linked.json", *SOURCES])
    assert line == "A film-bound source leads outside the film's root: content/linked.json"
