"""The sample film's declaration copied below a new root, which a test may rewrite: the fixture
`declared` (`conftest.py`) for the tests of the declaration."""

import shutil
from pathlib import Path

import filmkit.declared_sources as declared_sources
import filmkit.film as film
import filmkit.repository as repository


def copied(root: Path) -> Path:
    """Copy the sample film's declaration and every file it names below `root`; the root."""
    for _field, path in declared_sources.named_files(film.FILM):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, target)
    shutil.copy2(repository.ROOT / film.DECLARATION, root / film.DECLARATION)
    return root


def rewrite(root: Path, old: str, new: str) -> None:
    """Replace the first `old` in the declaration below `root` with `new`; it must hold `old`."""
    path = root / film.DECLARATION
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))
