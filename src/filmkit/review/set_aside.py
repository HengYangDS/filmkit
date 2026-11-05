"""Set an edition's packaged films aside before its next render and package.

package-film refuses to extend a package bound to changed inputs, and the next render would
overwrite the picture in place. Setting aside renames each edition's two films and package
record, and its rendered picture unless that edition keeps it (when the successor's render has
already replaced it, or when the next build does not replace it), within the volume into
build/artifacts/film/superseded/<label>/<code>/, and records them in manifest.json with their
hashes, the consumer that still holds their bytes and the exit condition. Each member is read
back by its hash after it moves.

A reviewed round's packages are bound by the round's review, which must name both film hashes;
their label is round-<n>. An unreviewed build, such as a preview the owner watched, is bound by
a consumer folder that holds both films byte-identical in <consumer>/<code>/, and is labelled
round-<n> or by a name of its own. Every planned edition is checked before anything moves.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

import filmkit.repository as repository
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError
from filmkit.review.files import edition_review, present

EXIT_CONDITION = "Retire after the successor delivery is accepted"
# Below the film's root, the folder each set-aside label holds, with one folder per edition.
SUPERSEDED = Path("build/artifacts/film/superseded")
# A label is a lowercase name of words joined by hyphens, such as round-5 or preview-2026-11-05.
LABEL = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SetAside(NamedTuple):
    """One edition's members, the folder they move to and its manifest."""

    code: str
    target: Path
    sources: list[Path]
    manifest: dict


def round_label(number: int) -> str:
    return f"round-{number}"


def edition_members(label: str, code: str, *, picture: bool) -> tuple[Path, list[Path]]:
    """An edition's target folder and the members to move there.

    Refused unless the label is a name, the target is new and every member exists on the
    target's volume.
    """
    if not LABEL.fullmatch(label):
        msg = f"{label!r} is not a label of lowercase words joined by hyphens"
        raise ReviewError(msg)
    edition = Edition(code)
    target = repository.ROOT / SUPERSEDED / label / code
    if target.exists():
        msg = f"{repository.relative(target)} exists; inspect it before setting aside again"
        raise ReviewError(msg)
    sources = [*edition.films, edition.film_package, *([edition.picture] if picture else [])]
    present(sources)
    volume = next(parent for parent in target.parents if parent.exists()).stat().st_dev
    if any(path.stat().st_dev != volume for path in sources):
        msg = f"{code}: a member lies outside the volume of {repository.relative(target)}"
        raise ReviewError(msg)
    return target, sources


def hashed(paths: list[Path]) -> dict[Path, str]:
    return {path: repository.sha(path) for path in paths}


def planned(code: str, target: Path, hashes: dict, purpose: str, consumer: str) -> SetAside:
    """One edition's set-aside, its manifest naming each member with its hash and size."""
    members = [
        {
            "source": repository.relative(path),
            "path": repository.relative(target / path.name),
            "sha256": digest,
            "bytes": path.stat().st_size,
        }
        for path, digest in hashes.items()
    ]
    manifest = {
        "purpose": purpose,
        "consumer": consumer,
        "exit_condition": EXIT_CONDITION,
        "moved_at": None,
        "members": members,
    }
    return SetAside(code, target, list(hashes), manifest)


def plan_set_aside(
    number: int,
    purpose: str,
    review_dir: Path,
    *,
    codes: tuple[str, ...] = CODES,
    pictures: tuple[str, ...] = CODES,
) -> list[SetAside]:
    """Plan moving a reviewed round's packages aside, each edition's picture among `pictures`.

    Refused unless, for every edition, its members can move and the round's review binds both
    of its film hashes.
    """
    plans = []
    for code in codes:
        target, sources = edition_members(round_label(number), code, picture=code in pictures)
        review = review_dir / f"review-{code}.json"
        bound = {item["sha256"] for item in edition_review(review, code)[1].get("media", [])}
        hashes = hashed(sources)
        if not all(hashes[film] in bound for film in Edition(code).films):
            msg = f"{code}: the packaged films are not the ones round {number} reviewed"
            raise ReviewError(msg)
        what = f"{code} package and picture reviewed in round {number}: {purpose}"
        binding = f"{repository.relative(review)} binds the two film hashes"
        plans.append(planned(code, target, hashes, what, binding))
    return plans


def plan_unreviewed(
    label: str,
    purpose: str,
    consumer: Path,
    *,
    codes: tuple[str, ...] = CODES,
    pictures: tuple[str, ...] = CODES,
) -> list[SetAside]:
    """Plan moving an unreviewed build's packages aside, each edition's picture among `pictures`.

    Refused unless, for every edition, its members can move and the consumer folder holds
    copies of both of its films byte-identical in <consumer>/<code>/, other than the films.
    """
    plans = []
    for code in codes:
        target, sources = edition_members(label, code, picture=code in pictures)
        hashes = hashed(sources)
        copies = consumer / code
        for film in Edition(code).films:
            copy = copies / film.name
            if copy.resolve() == film.resolve():
                msg = f"{code}: {copy} is the film itself, not a consumer's copy"
                raise ReviewError(msg)
            if not copy.is_file() or repository.sha(copy) != hashes[film]:
                msg = f"{code}: {copy} does not hold the bytes of {repository.relative(film)}"
                raise ReviewError(msg)
        what = f"{code} package of an unreviewed build: {purpose}"
        binding = f"{repository.relative(copies)} holds the two films' bytes"
        plans.append(planned(code, target, hashes, what, binding))
    return plans


def move_aside(plans: list[SetAside]) -> None:
    """Move each planned member aside and read it back by its hash.

    Each target's manifest is written before its first move, with moved_at null, so an
    interrupted set-aside still names every member it was moving; once every member has
    moved, the manifest records when.
    """
    for plan in plans:
        plan.target.mkdir(parents=True)
        repository.write(plan.target / "manifest.json", plan.manifest)
        for source, member in zip(plan.sources, plan.manifest["members"], strict=True):
            moved = source.rename(plan.target / source.name)
            if source.exists() or repository.sha(moved) != member["sha256"]:
                msg = f"{member['path']}: set-aside readback differs"
                raise ReviewError(msg)
        moved_at = datetime.now(UTC).isoformat()
        repository.write(plan.target / "manifest.json", {**plan.manifest, "moved_at": moved_at})


def set_aside_report(plans: list[SetAside], *, dry_run: bool) -> dict:
    """Each edition's set-aside target and members, as the command prints them."""
    return {
        "dry_run": dry_run,
        "editions": [
            {
                "language": plan.code,
                "target": repository.relative(plan.target),
                "members": [member["path"] for member in plan.manifest["members"]],
            }
            for plan in plans
        ],
    }
