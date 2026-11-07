"""Set an edition's packaged films aside before its next render and package.

package-film refuses to extend a package bound to changed inputs, and the next render would
overwrite the pictures in place. Setting aside renames each edition's films and package record,
and its rendered pictures unless that edition keeps them (when the successor's render has
already replaced them, or when the next build does not replace them), within the volume into
build/artifacts/film/superseded/<label>/<code>/, and records them in manifest.json with their
hashes, the consumer that still holds their bytes and the exit condition. Each member is read
back by its hash after it moves. A build's films are its films with captions and those without
that it made (`built_films`): a build packaged before the films without captions existed holds
only the first, and has only the captioned picture.

A reviewed round's packages are bound by the round's review, which must name every film hash;
their label is round-<n>. An unreviewed build, such as a preview the owner watched, is bound by
a consumer folder that holds its films byte-identical in <consumer>/<code>/, and is labelled
round-<n> or by a name of its own. Every planned edition is checked before anything moves.

Assembling an edition's soundtrack or refreshing its captions rewrites the inputs of its
packaged build in place, so `filmkit.produce` refuses both while the prompts of a review round
bind the edition's current films and that round has not set the edition aside
(`require_set_aside`).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

import filmkit.repository as repository
from filmkit.production import CODES, RENDITIONS, Edition
from filmkit.review import ReviewError
from filmkit.review.files import REVIEWS, edition_review, present, round_number

EXIT_CONDITION = "Retire after the successor delivery is accepted"
# Below the film's root, the folder each set-aside label holds, with one folder per edition.
SUPERSEDED = Path("build/artifacts/film/superseded")
# A label is a lowercase name of words joined by hyphens, such as round-5 or preview-2026-11-05.
LABEL = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# The command that sets one edition of a reviewed round aside, as a refusal names it.
SET_ASIDE_COMMAND = (
    "python -m filmkit.review.round set-aside --round {number} --purpose <text> --language {code}"
)


class SetAside(NamedTuple):
    """One edition's members, the folder they move to and its manifest."""

    code: str
    target: Path
    sources: list[Path]
    manifest: dict


def round_label(number: int) -> str:
    return f"round-{number}"


def built_films(edition: Edition) -> list[Path]:
    """The films of the edition's build, in `RENDITIONS` order: every film with captions, and
    each film without them that is in place, since a build packaged before those films existed
    holds none of them."""
    return [
        edition.film(kind)
        for kind, rendition in RENDITIONS.items()
        if rendition.captions or edition.film(kind).is_file()
    ]


def built_pictures(edition: Edition) -> list[Path]:
    """The edition's rendered pictures: the captioned one, and the uncaptioned one when it is in
    place."""
    uncaptioned = edition.rendered(captions=False).file
    return [edition.picture, *([uncaptioned] if uncaptioned.is_file() else [])]


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
    sources = [
        *built_films(edition),
        edition.film_package,
        *(built_pictures(edition) if picture else []),
    ]
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

    Refused unless, for every edition, its members can move and the round's review binds each
    of its film hashes.
    """
    plans = []
    for code in codes:
        target, sources = edition_members(round_label(number), code, picture=code in pictures)
        review = review_dir / f"review-{code}.json"
        bound = {item["sha256"] for item in edition_review(review, code)[1].get("media", [])}
        hashes = hashed(sources)
        if not all(hashes[film] in bound for film in built_films(Edition(code))):
            msg = f"{code}: the packaged films are not the ones round {number} reviewed"
            raise ReviewError(msg)
        what = f"{code} package and picture reviewed in round {number}: {purpose}"
        binding = f"{repository.relative(review)} binds the film hashes"
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
    copies of each of its films byte-identical in <consumer>/<code>/, other than the films.
    """
    plans = []
    for code in codes:
        target, sources = edition_members(label, code, picture=code in pictures)
        hashes = hashed(sources)
        copies = consumer / code
        for film in built_films(Edition(code)):
            copy = copies / film.name
            if copy.resolve() == film.resolve():
                msg = f"{code}: {copy} is the film itself, not a consumer's copy"
                raise ReviewError(msg)
            if not copy.is_file() or repository.sha(copy) != hashes[film]:
                msg = f"{code}: {copy} does not hold the bytes of {repository.relative(film)}"
                raise ReviewError(msg)
        what = f"{code} package of an unreviewed build: {purpose}"
        binding = f"{repository.relative(copies)} holds the films' bytes"
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


def binding_rounds(edition: Edition) -> list[int]:
    """The review rounds whose prompts name each of the edition's current films by its hash.

    A round's prompt for the edition is prompt-<code>.md in its directory round-<n> below
    `REVIEWS`. The films are the build's (`built_films`); an edition whose films with captions
    are not all in place is bound by none, and the films are hashed only when a round holds
    such a prompt.
    """
    prompts = sorted(
        (number, path)
        for path in (repository.ROOT / REVIEWS).glob(f"round-*/prompt-{edition.code}.md")
        if (number := round_number(path.parent)) is not None
    )
    films = built_films(edition)
    if not prompts or not all(film.is_file() for film in films):
        return []
    hashes = [repository.sha(film) for film in films]
    bound = []
    for number, path in prompts:
        text = path.read_text(encoding="utf-8")
        if all(digest in text for digest in hashes):
            bound.append(number)
    return bound


def set_aside_finished(number: int, code: str) -> bool:
    """Whether a set-aside of the round has moved every member of the edition and recorded it."""
    record = repository.ROOT / SUPERSEDED / round_label(number) / code / "manifest.json"
    return record.is_file() and repository.read(record).get("moved_at") is not None


def require_set_aside(edition: Edition) -> None:
    """Refuse while a review round's prompts bind the edition's current films, not set aside.

    A round has set the edition aside once its manifest below
    build/artifacts/film/superseded/round-<n>/<code>/ records that every member moved. The
    refusal names each round that binds the films and the command that sets the latest one
    aside for this edition, which moves the films and so frees them from every such round.
    """
    code = edition.code
    unset = [number for number in binding_rounds(edition) if not set_aside_finished(number, code)]
    if unset:
        rounds = " and ".join(f"round {number}" for number in unset)
        command = SET_ASIDE_COMMAND.format(number=unset[-1], code=code)
        msg = (
            f"the current {code} films are bound by the prompts of review {rounds} and have not "
            f"been set aside; first run {command}"
        )
        raise ReviewError(msg)
