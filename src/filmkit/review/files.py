"""The files a review round reads: its directory, the files a step requires and its reviews.

Each step of `filmkit.review.round` refuses a missing input with `ReviewError` before it moves or
writes anything, and the reviewer prompts cite a path below the film's root as ROOT/<path>. A
round's directory is round-<n> below `REVIEWS`, and n is the round's number.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import filmkit.repository as repository
from filmkit.production import CODES
from filmkit.review import ReviewError

# Below the film's root, the folder that holds each review round's directory.
REVIEWS = Path("build/evidence/reviews")
# The name of a round's directory, which holds the round's number.
ROUND_NAME = re.compile(r"round-(\d+)")


def cited(path: Path) -> str:
    """A path as the prompts cite it: ROOT/<path> inside the repository."""
    text = repository.relative(path)
    return text if Path(text).is_absolute() else f"ROOT/{text}"


def present(paths: list[Path]) -> list[Path]:
    """The given files, refused when any is missing."""
    missing = [repository.relative(path) for path in paths if not path.is_file()]
    if missing:
        msg = f"missing {', '.join(missing)}"
        raise ReviewError(msg)
    return paths


def round_directory(number: int) -> Path:
    return repository.ROOT / REVIEWS / f"round-{number}"


def round_number(directory: Path) -> int | None:
    """The number of the round whose directory this is, or None for a folder of another name."""
    name = ROUND_NAME.fullmatch(directory.name)
    return None if name is None else int(name[1])


def edition_review(path: Path, code: str) -> tuple[dict, dict]:
    """A round's review file and its entry for one edition, refused when either is absent."""
    review = repository.read(present([path])[0])
    entry = review.get("editions", {}).get(code)
    if not isinstance(entry, dict):
        msg = f"{repository.relative(path)} reviews no {code} edition"
        raise ReviewError(msg)
    return review, entry


def round_findings(directory: Path) -> dict[str, list[str]]:
    """Each edition's finding identifiers in a round's reviews, in the order its review gives them.

    They are every `findings[].id` of each edition's review-<code>.json. Refused unless both
    reviews exist and each identifier names one finding, so that a disposition keyed by an
    identifier answers one finding.
    """
    findings = {
        code: [
            finding["id"]
            for finding in edition_review(directory / f"review-{code}.json", code)[1]["findings"]
        ]
        for code in CODES
    }
    counts = Counter(name for names in findings.values() for name in names)
    repeated = ", ".join(name for name, count in counts.items() if count > 1)
    if repeated:
        msg = f"{repository.relative(directory)} gives {repeated} to more than one finding"
        raise ReviewError(msg)
    return findings
