"""The writer of the release record: the record it builds, the release folder it stages and
replaces, the copy of an asset, and what a run that stops late leaves."""

import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from release_build import (
    EARLIER_VERSION,
    FFMPEG,
    SOURCES,
    refused,
    uncaptioned_stage,
    unchanged_refusal,
)

import filmkit.child_processes as child_processes
import filmkit.delivery.release as release
import filmkit.delivery.reproduction as reproduction
import filmkit.repository as repository
from filmkit.delivery.reproduction import ReproductionError
from filmkit.graph import cli
from filmkit.production import CODES, Edition

# The sample film declares review levels; these reviews keep the overall and dimension floors.
pytestmark = pytest.mark.usefixtures("unleveled")


# The record the writer builds (task 2.2).


def test_the_record_states_the_version_each_editions_digests_the_sources_and_every_asset(built):
    record, replaced = release.record(list(reversed(SOURCES)))
    assert replaced is None
    assert record.version == built.fixture_version
    for code in CODES:
        edition, held = Edition(code), record.editions[code]
        assert held.soundtrack_sha256 == repository.sha(edition.soundtrack)
        assert held.stage_sha256 == repository.sha(edition.picture_stage / "index.html")
        assert held.uncaptioned_stage_sha256 == repository.sha(
            uncaptioned_stage(code) / "index.html"
        )
        assert held.picture_floor_db == {}
        # Each film was encoded by the FFmpeg that runs, and the uncaptioned picture is derived.
        assert held.ffmpeg == dict.fromkeys([film.name for film in edition.films], FFMPEG)
        assert held.drawn_sha256 == {"captioned": repository.content_sha("captioned drawn")}
    # The sources stand in sorted order, however they were stated.
    assert list(record.sources.items()) == [(path, repository.sha(path)) for path in SOURCES]
    files = {
        name: source
        for code in CODES
        for name, (_, source) in reproduction.members(Edition(code)).items()
    }
    # Each edition's assets in the order it publishes them, and the checksums last.
    assert [asset.name for asset in record.assets] == [*files, reproduction.CHECKSUMS]
    for asset in record.assets[:-1]:
        source = files[asset.name]
        assert (asset.bytes, asset.sha256) == (source.stat().st_size, repository.sha(source))
    sums = reproduction.checksums(record)
    assert (record.assets[-1].bytes, record.assets[-1].sha256) == (
        len(sums.encode()),
        repository.content_sha(sums),
    )
    assert reproduction.check(record) is record


def test_each_film_keeps_the_floor_its_replaced_record_states_and_the_output_names_it(
    built, capsys
):
    chinese = [film.name for film in Edition("zh").films]
    english = [film.name for film in Edition("en").films]
    built.track(floors={"zh": {**dict.fromkeys(chinese, 45.0), chinese[1]: 41.5}, "en": {}})
    record, replaced = release.record(SOURCES)
    assert replaced.version == EARLIER_VERSION
    assert record.editions["zh"].picture_floor_db == {
        chinese[0]: 45.0,
        chinese[1]: 41.5,
        chinese[2]: 45.0,
        chinese[3]: 45.0,
    }
    # A film the replaced record does not name gets no floor, and the command says so.
    assert record.editions["en"].picture_floor_db == {}
    cli.main(["release", "--dry-run"])
    lines = capsys.readouterr().out.splitlines()
    assert f"{chinese[0]}: floor 45.0 dB" in lines
    assert f"{chinese[1]}: floor 41.5 dB" in lines
    assert [line for line in lines if line.endswith(": no floor")] == [
        f"{name}: no floor" for name in english
    ]


def test_a_first_record_states_no_floor_and_names_each_film_as_without_one(built, capsys):
    cli.main(["release", "--dry-run"])
    lines = capsys.readouterr().out.splitlines()
    films = [film.name for code in CODES for film in Edition(code).films]
    assert [line for line in lines if ": no floor" in line] == [
        f"{name}: no floor" for name in films
    ]
    assert not [line for line in lines if " dB" in line]


def test_a_script_changed_since_the_last_release_is_recorded_at_its_current_bytes(built):
    # The replaced record lists each script by the digest it had at the last release.
    built.track()
    replaced = reproduction.Release.model_validate_json(built.manifest.read_bytes())
    assert set(replaced.sources.values()) == {"0" * 64}
    cli.main(["release"])
    assert dict(reproduction.load().sources) == {path: repository.sha(path) for path in SOURCES}


def test_the_declared_set_replaces_whatever_the_replaced_record_listed(built):
    cast = Edition("zh").cast
    built.track(sources=[cast, *SOURCES])
    # A path the replaced record listed and the film does not declare is not recorded.
    built.declare(SOURCES[:2])
    cli.main(["release"])
    assert list(reproduction.load().sources) == SOURCES[:2]
    # A path it did not list is recorded when it is declared; the paths stand sorted, each once.
    record, replaced = release.record([cast, *reversed(SOURCES), cast])
    assert list(replaced.sources) == SOURCES[:2]
    assert list(record.sources) == sorted([cast, *SOURCES])
    assert record.sources[cast] == repository.sha(cast)


def test_a_replaced_record_whose_asset_names_changed_still_gives_its_floors(built):
    film = Edition("en").film("uhd").name
    built.track(
        floors={"en": {film: 44.0, "sample-reel-en-4k.mp4": 45.0}, "fr": {"another.mp4": 45.0}},
        assets=("sample-reel-en-4k.mp4", "sample-reel-en-notes.md"),
    )
    # The comparison's rules refuse such a record; the writer reads it by the model alone.
    with pytest.raises(ReproductionError):
        reproduction.load()
    record, replaced = release.record(SOURCES)
    assert [asset.name for asset in replaced.assets][0] == "sample-reel-en-4k.mp4"
    assert record.editions["en"].picture_floor_db == {film: 44.0}
    assert record.editions["zh"].picture_floor_db == {}
    assert reproduction.check(record) is record


def test_the_written_manifest_states_the_carried_floors_in_the_manifests_form(built):
    chinese = [film.name for film in Edition("zh").films]
    built.track(floors={"zh": {**dict.fromkeys(chinese, 45.0), chinese[1]: 41.5}, "en": {}})
    cli.main(["release"])
    # The floors are read back from the written manifest, as the comparison reads them.
    loaded = reproduction.load()
    assert loaded.editions["zh"].picture_floor_db == {
        chinese[0]: 45.0,
        chinese[1]: 41.5,
        chinese[2]: 45.0,
        chinese[3]: 45.0,
    }
    assert loaded.editions["en"].picture_floor_db == {}
    # The text has the form of the films' tracked records: an indent of two, the fields in the
    # model's order and a final newline.
    zh = Edition("zh")
    head = (
        "{\n"
        f'  "version": "{built.fixture_version}",\n'
        '  "editions": {\n'
        '    "zh": {\n'
        f'      "soundtrack_sha256": "{repository.sha(zh.soundtrack)}",\n'
        f'      "stage_sha256": "{repository.sha(zh.picture_stage / "index.html")}",\n'
        '      "uncaptioned_stage_sha256": '
        f'"{repository.sha(uncaptioned_stage("zh") / "index.html")}",\n'
        '      "picture_floor_db": {\n'
        f'        "{chinese[0]}": 45.0,\n'
        f'        "{chinese[1]}": 41.5,\n'
    )
    text = built.manifest.read_text()
    assert text.startswith(head)
    assert list(json.loads(text)) == ["version", "editions", "sources", "assets"]
    assert text.endswith("    }\n  ]\n}\n")


def test_a_dry_run_says_which_record_it_replaces(built, capsys):
    built.track()
    cli.main(["release", "--dry-run"])
    version = built.fixture_version
    assert capsys.readouterr().out.startswith(
        f"This record of {version} replaces a record of {EARLIER_VERSION}.\n"
    )
    built.manifest.unlink()
    cli.main(["release", "--dry-run"])
    assert capsys.readouterr().out.startswith(f"This record of {version} is the film's first")


def test_a_run_reports_the_sources_that_left_and_joined_the_replaced_records_list(built, capsys):
    # The replaced record lists one source more than this run states and one fewer.
    cast = Edition("zh").cast
    built.track(sources=[cast, *SOURCES[1:]])
    report = [
        f"Listed as a source by the replaced record and not stated now: {cast}",
        f"Stated as a source now and not listed by the replaced record: {SOURCES[0]}",
    ]
    # The report stands beside the version line, in a dry run as in a run, and refuses nothing.
    for arguments in (["--dry-run"], []):
        cli.main(["release", *arguments])
        assert capsys.readouterr().out.splitlines()[1:3] == report
    assert list(reproduction.load().sources) == SOURCES
    # A run that states what the replaced record lists, and a first record, report neither.
    cli.main(["release"])
    built.manifest.unlink()
    cli.main(["release", "--dry-run"])
    assert " as a source " not in capsys.readouterr().out


# The folder the writer stages and the manifest it writes (task 2.3).


def test_a_run_stages_exactly_the_recorded_assets_and_writes_the_manifest_last(
    built, monkeypatch, capsys
):
    staged_when_written = []
    write_text = repository.write_text

    def written(path, text):
        staged_when_written.append((str(path), built.staged()))
        write_text(path, text)

    monkeypatch.setattr(repository, "write_text", written)
    cli.main(["release"])
    manifest = reproduction.load()
    assert manifest.version == built.fixture_version
    names = sorted(asset.name for asset in manifest.assets)
    assert len(names) == 21
    # The folder holds exactly the assets, each with the bytes the manifest records.
    assert built.staged() == names
    assert sorted(reproduction.published(manifest)) == names
    assert (built.release / reproduction.CHECKSUMS).read_text() == reproduction.checksums(manifest)
    # The manifest was the last file written, the whole folder standing by then.
    assert staged_when_written == [(str(reproduction.MANIFEST), names)]
    assert built.manifest.read_text() == release.serialized(manifest)
    assert not (built.root / release.STAGING).exists()
    out = capsys.readouterr().out
    assert f"This record of {built.fixture_version} is the film's first" in out


def test_a_second_run_changes_no_byte_and_says_which_record_it_replaces(built, capsys):
    cli.main(["release"])
    first = built.tree()
    held = {entry.name: entry.stat().st_ino for entry in built.release.iterdir()}
    capsys.readouterr()
    cli.main(["release"])
    assert built.tree() == first
    # The folder that was already whole was left, not staged again.
    assert {entry.name: entry.stat().st_ino for entry in built.release.iterdir()} == held
    version = built.fixture_version
    assert f"This record of {version} replaces a record of {version}" in capsys.readouterr().out
    # With --replace too, a whole folder is left as it is.
    cli.main(["release", "--replace"])
    assert {entry.name: entry.stat().st_ino for entry in built.release.iterdir()} == held


def test_finders_file_refuses_nothing(built):
    # In a folder that holds nothing else, and beside a whole set of assets.
    built.release.mkdir(parents=True)
    (built.release / ".DS_Store").write_text("finder\n")
    cli.main(["release"])
    (built.release / ".DS_Store").write_text("finder\n")
    cli.main(["release"])
    assert (built.release / ".DS_Store").read_text() == "finder\n"
    assert sorted(reproduction.published(reproduction.load())) == [
        name for name in built.staged() if name != ".DS_Store"
    ]


def test_the_films_of_the_release_before_refuse_by_name_and_keep_every_byte(built, capsys):
    # The folder holds the last release's films: one under a name this release has too, one
    # under a name it has not.
    built.track()
    built.release.mkdir(parents=True)
    (built.release / "sample-reel-zh-uhd.mp4").write_text("the film of the release before\n")
    (built.release / "sample-reel-zh-1080p.mp4").write_text("a film under an earlier name\n")
    line = unchanged_refusal(built)
    assert "sample-reel-zh-1080p.mp4, sample-reel-zh-uhd.mp4" in line
    assert "--replace" in line
    # A dry run refuses as the run would.
    assert unchanged_refusal(built, ["--dry-run"]) == line
    capsys.readouterr()
    cli.main(["release", "--replace"])
    manifest = reproduction.load()
    assert built.staged() == sorted(asset.name for asset in manifest.assets)
    assert sorted(reproduction.published(manifest)) == built.staged()
    said = f"This record of {built.fixture_version} replaces a record of {EARLIER_VERSION}"
    assert said in capsys.readouterr().out


def test_a_record_written_again_after_its_review_was_recorded_again_replaces_the_folder(built):
    cli.main(["release"])
    built.editions["zh"].review("# Review of zh, recorded again\n")
    line = unchanged_refusal(built)
    assert "sample-reel-zh-production-review.json, sample-reel-zh-production-review.md" in line
    assert "--replace" in line
    cli.main(["release", "--replace"])
    manifest = reproduction.load()
    assert built.staged() == sorted(asset.name for asset in manifest.assets)
    assert sorted(reproduction.published(manifest)) == built.staged()
    listed = {asset.name: asset.sha256 for asset in manifest.assets}
    review = Edition("zh").production_review
    assert listed["sample-reel-zh-production-review.json"] == repository.sha(review)
    assert listed["sample-reel-zh-production-review.md"] == repository.sha(
        review.with_suffix(".md")
    )


def test_a_sibling_left_by_an_interrupted_run_is_removed(built):
    leftover = built.root / release.STAGING / "half-a-film.mp4"
    leftover.parent.mkdir(parents=True)
    leftover.write_text("half a film")
    cli.main(["release"])
    assert not leftover.parent.exists()
    assert "half-a-film.mp4" not in built.staged()
    assert sorted(reproduction.published(reproduction.load())) == built.staged()
    # A run that finds the release folder whole stages nothing and removes the sibling too; a
    # dry run leaves it, as it leaves every file.
    leftover.parent.mkdir()
    leftover.write_text("half a film")
    cli.main(["release", "--dry-run"])
    assert leftover.read_text() == "half a film"
    cli.main(["release"])
    assert not leftover.parent.exists()


def test_a_dry_run_prints_the_record_and_changes_no_file(built, capsys):
    before = built.tree()
    cli.main(["release", "--dry-run"])
    assert built.tree() == before
    out = capsys.readouterr().out
    printed = out[out.index("{\n") :]
    record, _ = release.record(SOURCES)
    assert printed == release.serialized(record)
    assert reproduction.check(reproduction.Release.model_validate_json(printed)) == record


def test_a_failure_while_staging_leaves_the_folder_and_the_manifest_as_they_were(
    built, monkeypatch
):
    cli.main(["release"])
    built.editions["en"].review("# Review of en, recorded again\n")
    copy = release.copy

    def failing(source, target):
        if target.name == "sample-reel-en.srt":
            command = [*release.SYSTEM_COPY, str(source), str(target)]
            raise subprocess.CalledProcessError(1, command, stderr=b"cp: No space left\n")
        copy(source, target)

    monkeypatch.setattr(release, "copy", failing)
    before = built.tree()
    line = refused(["--replace"])
    assert "sample-reel-en.srt" in line
    assert "No space left" in line
    # The folder and the manifest hold the bytes they held, and no half-staged set is left.
    assert built.tree() == before
    monkeypatch.setattr(release, "copy", copy)
    # A build file that moves while the set is staged is a failure too: the staged bytes are
    # held to the record before they take the folder's place.
    moved = Edition("zh").artifacts / "sample-reel-zh.vtt"
    members = reproduction.members

    def moving(edition, **options):
        moved.write_text("WEBVTT moved\n")
        return members(edition, **options)

    record, _ = release.record(SOURCES)
    monkeypatch.setattr(reproduction, "members", moving)
    with pytest.raises(ReproductionError, match="the build moved while it was staged"):
        release.stage(record)
    monkeypatch.setattr(reproduction, "members", members)
    moved.write_text("sample-reel-zh.vtt\n")
    assert built.tree() == before
    cli.main(["release", "--replace"])
    assert sorted(reproduction.published(reproduction.load())) == built.staged()


def test_on_macos_each_asset_is_copied_by_the_systems_own_cp_whatever_path_holds(
    built, monkeypatch
):
    commands = []

    def copied(command, timeout=120):
        commands.append(command)
        shutil.copyfile(command[-2], command[-1])

    monkeypatch.setattr(release, "sys", SimpleNamespace(platform="darwin"))
    monkeypatch.setattr(repository, "run", copied)
    cli.main(["release"])
    files = {
        name: source
        for code in CODES
        for name, (_, source) in reproduction.members(Edition(code)).items()
    }
    # The command names the system's cp by its path, so no other cp on PATH is asked for -c.
    assert commands == [
        ["/bin/cp", "-c", str(source), str(built.root / release.STAGING / name)]
        for name, source in files.items()
    ]
    assert sorted(reproduction.published(reproduction.load())) == built.staged()


def test_on_another_platform_each_asset_is_copied_without_the_systems_option(built, monkeypatch):
    def asked(command, timeout=120):
        pytest.fail(f"-c is macOS's option, and no command is run elsewhere: {command}")

    monkeypatch.setattr(release, "sys", SimpleNamespace(platform="linux"))
    monkeypatch.setattr(repository, "run", asked)
    cli.main(["release"])
    assert sorted(reproduction.published(reproduction.load())) == built.staged()
    # The copy keeps the file's times.
    film = Edition("zh").film("uhd")
    assert (built.release / film.name).stat().st_mtime_ns == film.stat().st_mtime_ns


@pytest.mark.parametrize("kind", ["file", "link"])
@pytest.mark.parametrize(
    "place", [reproduction.RELEASE, release.STAGING], ids=["release folder", "sibling"]
)
def test_a_release_or_sibling_path_that_is_no_real_folder_refuses_naming_the_path(
    built, place, kind
):
    path = built.root / place
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        path.write_text("no folder\n")
    else:
        kept = built.root / "build/artifacts/kept"
        kept.mkdir()
        (kept / "old-film.mp4").write_text("the film of the release before\n")
        path.symlink_to(kept, target_is_directory=True)
    found = "a link" if kind == "link" else "no folder"
    # With --replace too, and in a dry run: nothing is staged and nothing removed.
    for arguments in ([], ["--replace"], ["--dry-run"]):
        assert unchanged_refusal(built, arguments).startswith(f"{place} is {found}")
    assert path.is_symlink() == (kind == "link")


def test_a_run_that_stops_before_the_staged_set_is_in_place_is_completed_by_the_next(
    built, monkeypatch, capsys
):
    cli.main(["release"])
    tracked = built.manifest.read_bytes()
    review = built.editions["zh"].review("# Review of zh, recorded again\n")

    def interrupted(self, target):
        raise OSError("interrupted")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "rename", interrupted)
        with pytest.raises(SystemExit) as failed:
            cli.main(["release", "--replace"])
    # A fault that is no refusal: the command could not finish, and says why with its traceback.
    assert failed.value.code == child_processes.UNFINISHED
    assert capsys.readouterr().err.endswith("OSError: interrupted\n")
    # No release folder stands: the sibling holds the whole set, and the manifest what it held.
    assert not built.release.exists()
    assert len(list((built.root / release.STAGING).iterdir())) == 21
    assert built.manifest.read_bytes() == tracked
    # The next run stages again and needs no --replace, since no other bytes stand.
    cli.main(["release"])
    manifest = reproduction.load()
    assert sorted(reproduction.published(manifest)) == built.staged()
    assert not (built.root / release.STAGING).exists()
    listed = {asset.name: asset.sha256 for asset in manifest.assets}
    assert listed["sample-reel-zh-production-review.json"] == repository.sha(review)


def test_a_run_that_stops_before_the_manifest_is_written_is_completed_by_the_next(
    built, monkeypatch, capsys
):
    cli.main(["release"])
    tracked = built.manifest.read_bytes()
    built.editions["zh"].review("# Review of zh, recorded again\n")

    def unwritable(path, text):
        raise PermissionError(13, "Permission denied", str(path))

    with monkeypatch.context() as patch:
        patch.setattr(repository, "write_text", unwritable)
        with pytest.raises(SystemExit) as failed:
            cli.main(["release", "--replace"])
    assert failed.value.code == child_processes.UNFINISHED
    # The folder holds the new record's assets beside the manifest of the record before, so the
    # comparison refuses the pair until the next run.
    assert built.manifest.read_bytes() == tracked
    with pytest.raises(ReproductionError, match="published asset differs from the release"):
        reproduction.published(reproduction.load())
    capsys.readouterr()
    # The next run finds the folder whole, leaves it, and writes the manifest: no --replace.
    cli.main(["release"])
    assert "already held the record's 21 assets" in capsys.readouterr().out
    assert sorted(reproduction.published(reproduction.load())) == built.staged()
