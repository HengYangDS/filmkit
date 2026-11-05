"""The files a review round reads: its directory, the files a step requires and its reviews.

Each step of `filmkit.review.round` refuses a missing input with `ReviewError` before it moves or
writes anything, and the reviewer prompts cite a path below the film's root as ROOT/<path>.
"""

from __future__ import annotations

from pathlib import Path

import filmkit.repository as repository
from filmkit.review import ReviewError


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
    return repository.ROOT / "build/evidence/reviews" / f"round-{number}"


def edition_review(path: Path, code: str) -> tuple[dict, dict]:
    """A round's review file and its entry for one edition, refused when either is absent."""
    review = repository.read(present([path])[0])
    entry = review.get("editions", {}).get(code)
    if not isinstance(entry, dict):
        msg = f"{repository.relative(path)} reviews no {code} edition"
        raise ReviewError(msg)
    return review, entry
