"""The root of the film the engine builds, and file access from it.

The film's root is the folder that `FILMKIT_ROOT` names or, when it is unset, the nearest folder
at or above the working directory that holds the film's declaration; outside any film the engine
refuses to start. Tests rebind `ROOT`, so other modules read it through this module when they
run instead of importing its value. Paths are taken below the root; an absolute path is used as
given.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

# The film's declaration, below its root.
DECLARATION = "content/film.toml"
# The variable that names the film's root, wherever the engine runs.
ROOT_VARIABLE = "FILMKIT_ROOT"


class FilmRootError(LookupError):
    """No film declaration where the engine looked, or no npm packages above the film."""


def film_root(start: Path | None = None) -> Path:
    """The root of the film the engine builds.

    That is the folder `FILMKIT_ROOT` names, or else the nearest folder at or above `start`,
    the working directory by default, that holds the declaration. The refusal names the
    folder where the search began.
    """
    named = os.environ.get(ROOT_VARIABLE)
    if named:
        root = Path(named).resolve()
        if not (root / DECLARATION).is_file():
            message = f"No film declaration {DECLARATION} in {root}, which {ROOT_VARIABLE} names"
            raise FilmRootError(message)
        return root
    begin = (start or Path.cwd()).resolve()
    for folder in (begin, *begin.parents):
        if (folder / DECLARATION).is_file():
            return folder
    message = (
        f"No film declaration {DECLARATION} at or above {begin}; "
        f"run below a film or set {ROOT_VARIABLE} to its root"
    )
    raise FilmRootError(message)


ROOT = film_root()


def node_modules() -> Path:
    """The film's npm packages: the nearest `node_modules` folder at or above its root."""
    for folder in (ROOT, *ROOT.parents):
        if (folder / "node_modules").is_dir():
            return folder / "node_modules"
    message = f"No node_modules folder at or above the film {ROOT}; install its npm packages"
    raise FilmRootError(message)


def read(path: str | Path) -> dict:
    """Read the JSON object at a path."""
    return json.loads((ROOT / path).read_text())


def write(path: str | Path, value: dict) -> None:
    """Write a JSON object with an indent of two and a final newline, creating its folder.

    The text goes to a new sibling file that then replaces the target, so a reader never sees
    a partial record and an interrupted write leaves the previous one in place. The file is
    created like `Path.write_text` creates one, so its mode follows the umask.
    """
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f".{target.name}.{os.getpid()}.partial")
    descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        partial.replace(target)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def sha(path: str | Path) -> str:
    """Return the SHA-256 of a file's bytes, read in blocks."""
    with (ROOT / path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def content_sha(value: str | bytes) -> str:
    """Return the SHA-256 of bytes, or of a text's UTF-8 bytes."""
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def relative(path: Path) -> str:
    """Return a path relative to the root, or absolute when it lies outside."""
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def run(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a command from the root without input, capturing its output and failing on error."""
    return subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        timeout=timeout,
    )
