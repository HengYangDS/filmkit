"""Write the release record of the reviewed, delivered build, and stage the assets it names.

content/release.json is the record a rebuild is compared with; `filmkit.delivery.reproduction`
holds its model, its asset names and its checksums format, and reads it. This command writes it
from the build as it stands, and stages every asset the record names, under its release name,
in build/artifacts/release, where the comparison reads the published assets. It asks each fact
of the module that owns it, in this order, and the first refusal stops it in one line, before
any file is written:

- each edition's bound inputs, of the film verifier, which decodes no film for them; then its
  uncaptioned stage, of the staging, since the record states that stage's digest and the receipt
  of a derived uncaptioned picture binds no stage; then its recorded review, of the verifier.
  The line is the owner's words after the edition and, for the stage, the picture;
- the film's own delivery folder, as the host names it when the command runs: every delivery
  member there holds the build's bytes. The folder is read, not the readback of a delivery,
  which states one moment: another checkout of the film delivers to the same folder;
- the film's version, which the manifest states as three numbers;
- the record it replaces, read by the manifest's model alone, so that a record whose asset names
  have changed since still gives its floors;
- the film-bound sources, which `--sources` states at every run: each a path as the manifest's
  model lists one (`reproduction.SourcePath`, whose pattern the refusal prints) and a file below
  the film's root that is not the record and does not lie below the folder of what the engine
  generates, with no link that leads to either or outside the root. Nothing asks whether the
  file is tracked: which files are film-bound is the film's to declare.

Which files are film-bound is declared once, in the film. The command therefore keeps no list of
them and takes none from the record it replaces, which would be a second copy beside that
declaration: the film's task derives the paths from the declaration when it calls the command.
What the stated set changes of the list the replaced record held is printed beside the version
line, each path that left the list and each that joined it: a report, for which nothing is
refused.

The record states the film's version; each edition's soundtrack and both its staged documents by
SHA-256; each film's PSNR floor as the replaced record states it for a film of that name, and
none for a film it does not name, since the floor is the film's and the engine holds no number
for it; the stated sources in sorted order, each once, with its current SHA-256; and every
asset an edition publishes with its size and SHA-256, in the order it publishes them, the
checksums file last. The command prints each film's floor or that it has none: a film without
one does not pass the comparison until its record states one. It also prints the version of the
record it replaces beside the version it writes. A record of the version already recorded is
written again before its tag, after a review was recorded again or an edition rebuilt, so the
same version is no refusal: whether that version is released is the tag's to say.

The record is held to the rules `reproduction.load` holds a manifest to before any file is
written. Asset names carry no version, so the release folder can hold the only copy on this disk
of the last release's films under the names of this one's. A folder that holds any entry other
than an asset with the bytes the record states is therefore refused, naming the entries, unless
`--replace` is given; Finder's .DS_Store is no entry, as in a delivery. A release path or a
sibling path that is a link or no folder is refused by its path, with `--replace` too: the
command replaces a folder of its own and follows no link. A folder that already holds exactly
the record's assets is left as it is. Otherwise the whole set is staged in the sibling folder
build/artifacts/release.staging, each asset and then the checksums file. On macOS an asset is
copied with the system's own `/bin/cp -c`, a clone where the file system clones and a copy
elsewhere, whatever cp PATH holds first; on another platform, whose cp has no such option, with
a copy that keeps the file's times. The staged set is held to the record, the release folder is
removed and the staged one renamed to it. A run that writes removes the sibling first where an
interrupted run left it. The manifest is written last. `--dry-run` asks and refuses as a run
does, prints the record and changes no file.

A refusal, and a failure while staging, leave the release folder and the tracked manifest as
they were. A run that stops in its last two steps keeps its traceback and leaves the manifest as
it was, in one of two states that the next run repairs without `--replace`, since neither holds
other bytes. Stopped after the release folder was removed and before the staged set was renamed
to it, no release folder stands and the sibling holds the whole set: the next run stages again.
Stopped after the rename and before the manifest was written, the folder holds the new record's
assets beside the old manifest, a pair the comparison refuses: the next run finds the folder
whole and writes the manifest.

Usage: python -m filmkit.delivery.release --sources <path> ... [--replace] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from pydantic import TypeAdapter, ValidationError

import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.packaging as packaging
import filmkit.delivery.reproduction as reproduction
import filmkit.delivery.verification as verification
import filmkit.picture.rendering as picture_rendering
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.reproduction import (
    CHECKSUMS,
    MANIFEST,
    RELEASE,
    Asset,
    Release,
    ReproductionError,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

# The folder the release's assets are staged in, beside the release folder.
STAGING = RELEASE.with_name(f"{RELEASE.name}.staging")
# macOS's own cp with its option that clones a file where the file system clones and copies it
# elsewhere. It is named by its path: a cp that PATH holds first may be another's, as GNU's,
# which refuses the option.
SYSTEM_COPY = ("/bin/cp", "-c")
# Seconds the copy of one asset may take, where the file system does not clone.
DEADLINE = 3600
# A film-bound source's path as the manifest's model lists one. The rule is stated there alone:
# the refusal of another path names the model and prints its pattern.
SOURCE_PATH = TypeAdapter(reproduction.SourcePath)
# The folder below the film's root that holds what the engine generates. No module names it by
# itself; it is taken as the first name of the release folder's path, which the comparison states.
GENERATED = RELEASE.parts[0]
# The owners' refusals that the command reports in one line, as the manifest's error; any other
# exception keeps its traceback.
OWNERS = (*verification.REFUSALS, delivery_folder.DeliveryRefusedError, packaging.PackagingError)
# How many differing members of the delivery folder a refusal names before it counts the rest.
NAMED = 5


@contextmanager
def owned(*concerns: str) -> Iterator[None]:
    """Report an owner's refusal as the command's: the owner's words in one line, after what
    they concern."""
    try:
        yield
    except OWNERS as error:
        msg = ": ".join([*concerns, " ".join(str(error).splitlines())])
        raise ReproductionError(msg) from None


def first_problem(error: ValidationError) -> str:
    """The manifest model's refusal in one line: its first problem by its place in the record,
    and how many more there are."""
    first, more = error.errors()[0], error.error_count() - 1
    where = ".".join(str(part) for part in first["loc"])
    return (f"{where}: " if where else "") + first["msg"] + (f", and {more} more" if more else "")


def require_reviewed() -> None:
    """Refuse a build of which an edition's bound inputs, uncaptioned stage or recorded review
    does not stand, edition by edition.

    The verifier's picture check asks the staging for the captioned stage. It binds a derived
    uncaptioned picture by its derivation's receipt, which names no stage, so the uncaptioned
    stage, whose digest the record states, is asked of the staging here.
    """
    for code in production.CODES:
        edition = production.Edition(code)
        uncaptioned = edition.rendered(captions=False)
        with owned(code):
            verification.verify_bindings(edition)
        with owned(code, f"{uncaptioned.name} picture"):
            picture_rendering.require_current_stage(edition, uncaptioned.stage, captions=False)
        with owned(code):
            verification.verify_review(edition, edition.films)


def require_delivered() -> None:
    """Refuse a build that the film's own delivery folder, as the host names it now, does not
    hold member for member; a folder the delivery module refuses to name, in its words."""
    with owned():
        folder, rule = delivery_folder.delivery_destination()
    differing = delivery_folder.differing_members(repository.ROOT, folder)
    if differing:
        named = [f"{path} {found}" for path, found in differing.items()]
        rest = len(named) - NAMED
        listed = ", ".join(named[:NAMED]) + (f", and {rest} more" if rest > 0 else "")
        msg = (
            f"The film's delivery folder {folder}, which {rule} gave, does not hold the build: "
            f"{listed}; deliver the build, then record the release"
        )
        raise ReproductionError(msg)


def release_version() -> str:
    """The film's version, refused unless the manifest can state it: a film's `VERSION` may
    hold a pre-release, and the manifest states three numbers."""
    with owned():
        version = packaging.film_version()
    try:
        return TypeAdapter(reproduction.Version).validate_python(version)
    except ValidationError:
        msg = (
            f"The film's {packaging.VERSION} holds {version!r}, which a release manifest cannot "
            "state: it states three numbers and no pre-release, such as 1.3.0"
        )
        raise ReproductionError(msg) from None


def replaced_record() -> Release | None:
    """The tracked record that the new one replaces, as the manifest's model alone reads it, or
    None for a film's first record.

    The rules of `reproduction.load` are not asked: a record whose asset names have changed
    since still gives its floors, which are all the command takes from it. A tracked record the
    model refuses stops the command, since what it held is a person's to repair or to state
    again.
    """
    path = repository.ROOT / MANIFEST
    if not path.exists():
        return None
    try:
        return Release.model_validate_json(path.read_bytes())
    except OSError as error:
        reason = error.strerror
    except ValidationError as error:
        reason = first_problem(error)
    msg = (
        f"{MANIFEST} is not a release manifest ({reason}): repair it; or remove it, and state "
        "its floors again in the record this command then writes"
    )
    raise ReproductionError(msg)


def no_source(path: str) -> str | None:
    """Why a stated path is no film-bound source the record lists, or None for one that is.

    The path is one the manifest's model lists (`reproduction.SourcePath`): the refusal names
    the model and prints its pattern, and words the rule nowhere by hand. Its place, links
    followed, lies below the film's root; neither the path as stated nor that place is the
    record itself or lies below the folder of what the engine generates; and it is a file.

    These are the checks, and no more. The paths are compared as they are spelled, so the
    record or that folder in another letter case, on a volume that folds case, and a hard link
    to either are not seen. Nothing asks whether the file is tracked: the film declares which
    files are film-bound, and its task states them.
    """
    try:
        SOURCE_PATH.validate_python(path)
    except ValidationError:
        pattern = SOURCE_PATH.json_schema()["pattern"]
        return (
            "is no path as the release manifest's model lists one "
            f"(reproduction.SourcePath: {pattern})"
        )
    root = repository.ROOT.resolve()
    place = (root / path).resolve()
    if not place.is_relative_to(root):
        return "leads outside the film's root"
    named = (PurePath(path), place.relative_to(root))
    if MANIFEST in named:
        return "is or leads to the release record itself, which lists the sources and is none"
    if any(candidate.parts[:1] == (GENERATED,) for candidate in named):
        return f"lies or leads below {GENERATED}/, which holds what the engine generates"
    return None if place.is_file() else "is no file"


def bound_sources(stated: list[str]) -> dict[str, str]:
    """The stated film-bound sources with their current SHA-256, in sorted order and each once.
    A stated path that is no source the record lists (`no_source`) is refused by name, with
    every other stated path that is none for the same reason."""
    paths = sorted(stated)
    refused = {path: reason for path in paths if (reason := no_source(path))}
    if refused:
        reason = next(iter(refused.values()))
        named = [path for path, why in refused.items() if why == reason]
        msg = f"A film-bound source {reason}: {', '.join(named)}"
        raise ReproductionError(msg)
    return {path: repository.sha(path) for path in paths}


def record(stated: list[str]) -> tuple[Release, Release | None]:
    """The record of the build as it stands and the record it replaces, every fact asked of its
    owner first, in the command's order. `stated` holds the paths `--sources` names; the
    replaced record gives the floors alone."""
    require_reviewed()
    require_delivered()
    version = release_version()
    replaced = replaced_record()
    sources = bound_sources(stated)
    # A film has the same asset name from one record to the next, so a floor is carried by name.
    floors = {
        name: floor
        for stated_before in (replaced.editions.values() if replaced else ())
        for name, floor in stated_before.picture_floor_db.items()
    }
    editions, assets = {}, []
    for code in production.CODES:
        edition = production.Edition(code)
        films = [film.name for film in edition.films]
        editions[code] = reproduction.EditionRecord(
            soundtrack_sha256=repository.sha(edition.soundtrack),
            stage_sha256=repository.sha(edition.rendered().page),
            uncaptioned_stage_sha256=repository.sha(edition.rendered(captions=False).page),
            picture_floor_db={name: floors[name] for name in films if name in floors},
        )
        assets += [
            Asset(name=name, bytes=source.stat().st_size, sha256=repository.sha(source))
            for name, (_, source) in reproduction.members(edition).items()
        ]
    listed = Release(version=version, editions=editions, sources=sources, assets=assets)
    sums = reproduction.checksums(listed)
    checksums = Asset(name=CHECKSUMS, bytes=len(sums.encode()), sha256=repository.content_sha(sums))
    return listed.model_copy(update={"assets": (*listed.assets, checksums)}), replaced


def floor_lines(written: Release) -> list[str]:
    """Each film's floor as the record states it, or that it has none, in the films' order."""
    lines = []
    for code, edition in written.editions.items():
        for film in production.Edition(code).films:
            floor = edition.picture_floor_db.get(film.name)
            lines.append(f"{film.name}: " + ("no floor" if floor is None else f"floor {floor} dB"))
    return lines


def source_lines(written: Release, replaced: Release | None) -> list[str]:
    """What the stated sources change of the list the replaced record held: each path it listed
    that this run does not state, and each this run states that it did not list. It is a report:
    the replaced record is no source of the list, and nothing is refused for a difference."""
    stated = set(written.sources)
    listed = set(replaced.sources) if replaced else stated
    changes = (
        ("Listed as a source by the replaced record and not stated now", listed - stated),
        ("Stated as a source now and not listed by the replaced record", stated - listed),
    )
    return [f"{said}: {', '.join(sorted(paths))}" for said, paths in changes if paths]


def serialized(written: Release) -> str:
    """The record as the manifest holds it: the model's fields in their order, indented by two,
    an edition's absent uncaptioned stage left out, and a final newline."""
    fields = written.model_dump(mode="json", exclude_none=True)
    return json.dumps(fields, ensure_ascii=False, indent=2) + "\n"


def held(written: Release, folder: Path) -> tuple[list[str], bool]:
    """The entries of a folder that are no asset of the record with the bytes it states, by
    name, and whether the folder is whole: it holds every asset and no such entry. Finder's
    file is no entry."""
    listed = {asset.name: asset for asset in written.assets}
    entries = sorted(folder.iterdir()) if folder.is_dir() else []
    entries = [entry for entry in entries if entry.name != delivery_folder.FINDER_METADATA]
    others = [
        entry.name
        for entry in entries
        if (asset := listed.get(entry.name)) is None
        or not entry.is_file()
        or entry.stat().st_size != asset.bytes
        or repository.sha(entry) != asset.sha256
    ]
    return others, not others and len(entries) == len(listed)


def copy(source: Path, target: Path) -> None:
    """Copy a build file to its staged name: on macOS with the system's own `cp -c`, a clone
    where the file system clones and a copy elsewhere; on another platform, whose cp has no such
    option, with a copy that keeps the file's times."""
    if sys.platform == "darwin":
        repository.run([*SYSTEM_COPY, str(source), str(target)], timeout=DEADLINE)
    else:
        shutil.copy2(source, target)


def staging_failure(written: Release, staging: Path) -> str | None:
    """Stage the record's whole set in a folder, each asset copied and then the checksums file,
    and hold the staged set to the record: None, or what failed, in one line."""
    files = {
        name: source
        for code in production.CODES
        for name, (_, source) in reproduction.members(production.Edition(code)).items()
    }
    try:
        for staged, source in files.items():
            copy(source, staging / staged)
        staged = CHECKSUMS
        (staging / staged).write_text(reproduction.checksums(written))
    except (OSError, subprocess.SubprocessError) as error:
        said = getattr(error, "stderr", None) or str(error).encode()
        return f"{staged}: " + " ".join(said.decode(errors="replace").split())
    if not held(written, staging)[1]:
        return "the staged set differs from the record, so the build moved while it was staged"
    return None


def require_own_folders() -> None:
    """Refuse a release path or a sibling path that exists and is a link or no folder, by its
    path. The command removes and replaces a folder of its own there and follows no link, so
    `--replace` replaces no such path either."""
    for place in (RELEASE, STAGING):
        path = repository.ROOT / place
        link, other = path.is_symlink(), path.exists() and not path.is_dir()
        if link or other:
            msg = (
                f"{place} is {'a link' if link else 'no folder'}, where the command keeps a "
                "folder of its own: nothing is staged or removed; move it away, then record "
                "the release"
            )
            raise ReproductionError(msg)


def cleared_sibling() -> Path:
    """The sibling folder the set is staged in, removed where an interrupted run left it."""
    staging = repository.ROOT / STAGING
    if staging.exists():
        shutil.rmtree(staging)
    return staging


def stage(written: Release) -> None:
    """Put the record's assets in the release folder's place: the whole set staged beside it,
    then the folder removed and the staged one renamed to it. A failure while staging removes
    what was staged and leaves the release folder as it was."""
    folder, staging = repository.ROOT / RELEASE, cleared_sibling()
    staging.mkdir(parents=True)
    failure = staging_failure(written, staging)
    if failure:
        shutil.rmtree(staging, ignore_errors=True)
        msg = f"Staging failed ({failure}); {RELEASE} and {MANIFEST} are as they were"
        raise ReproductionError(msg)
    if folder.exists():
        shutil.rmtree(folder)
    staging.rename(folder)


def write(stated: list[str], *, replace: bool, dry_run: bool) -> None:
    """Record the release: ask, build the record and hold it to the manifest's rules, refuse a
    release or sibling path that is no folder of the command's own, refuse a release folder
    that holds other bytes unless `replace` says to replace it, print what the record
    replaces, what its sources change of the replaced list and each film's floor, then stage
    the assets and write the manifest last.
    With `dry_run` the record is printed and no file changes."""
    written, replaced = record(stated)
    reproduction.check(written)
    require_own_folders()
    others, whole = held(written, repository.ROOT / RELEASE)
    if others and not replace:
        msg = (
            f"{RELEASE} holds other bytes than this record's: {', '.join(others)}; --replace "
            "replaces the folder with the record's assets, and nothing here keeps what it held"
        )
        raise ReproductionError(msg)
    said = (
        f"is the film's first: no {MANIFEST} stands"
        if replaced is None
        else f"replaces a record of {replaced.version}"
    )
    print(f"This record of {written.version} {said}.")
    print("\n".join([*source_lines(written, replaced), *floor_lines(written)]))
    if dry_run:
        print("A dry run: no file is changed. The record:")
        print(serialized(written), end="")
        return
    if whole:
        cleared_sibling()
    else:
        stage(written)
    repository.write_text(MANIFEST, serialized(written))
    kept = "already held" if whole else "now holds"
    print(f"{RELEASE} {kept} the record's {len(written.assets)} assets. Wrote {MANIFEST}.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sources",
        nargs="+",
        required=True,
        metavar="PATH",
        help="the film-bound sources, at every run, each by the path the record lists it by",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace a release folder that holds other bytes than the record's",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the record only")
    options = parser.parse_args(argv)
    try:
        write(options.sources, replace=options.replace, dry_run=options.dry_run)
    except ReproductionError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
