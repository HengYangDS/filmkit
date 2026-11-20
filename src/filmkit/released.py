"""What this engine was released on, as a record inside the package.

The repository's manifests and locks are the source. `package.json` names under `dependencies`
the npm packages the engine runs in a film, which a film declares at those versions;
`package-lock.json` holds their integrity; `uv.lock` holds the version of every Python package
the engine's own dependencies resolve to, on every platform the lock covers, so the record
also names a package that another platform alone installs. An installed engine holds none of
those files, so the record `released.json` beside this module carries what they state. An
engine that holds no record it can read, or a record without a package the engine asks it for,
ends in an error whose one line names the file and this command, which writes it (`load`,
`npm_package`). The renderer asks when it is imported, so a caller sees that line as the last
of a traceback. The command itself reads no record.

Usage: python -m filmkit.released
Run in the engine's repository, where it writes the record from the manifests and locks. The
repository's fix task runs it, and its tests refuse a record that differs from them.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

RECORD = Path(__file__).with_name("released.json")
# The engine's name: that of the package this module and its record lie in. The project's own
# file states it, and an installed engine holds no such file.
ENGINE = RECORD.parent.name
# The command that writes the record, in the engine's repository.
COMMAND = f"python -m {ENGINE}.{Path(__file__).stem}"
# The repository's npm manifest, its npm lock and its Python lock, which the record is written
# from.
MANIFEST, NPM_LOCK, PYTHON_LOCK = "package.json", "package-lock.json", "uv.lock"


class ReleasedError(ValueError):
    """The manifests and locks do not state one release, or the engine holds no record that
    states what it is asked for."""


def compute(root: Path) -> dict:
    """The record the engine's repository at a root states: each npm package a film declares
    with its version and integrity, and each Python package of the engine's runtime with its
    version. The engine's own development tools are in neither."""
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    locked = json.loads((root / NPM_LOCK).read_text(encoding="utf-8"))["packages"]
    npm = {}
    for name, stated in sorted((manifest.get("dependencies") or {}).items()):
        entry = locked.get(f"node_modules/{name}") or {}
        if entry.get("version") != stated or not entry.get("integrity"):
            message = f"{NPM_LOCK} does not hold {name} {stated} with its integrity"
            raise ReleasedError(message)
        npm[name] = {"version": stated, "integrity": entry["integrity"]}
    packages: dict[str, list[dict]] = {}
    for package in tomllib.loads((root / PYTHON_LOCK).read_text(encoding="utf-8"))["package"]:
        packages.setdefault(package["name"], []).append(package)
    reached: set[str] = set()
    waiting = [needed["name"] for needed in packages[ENGINE][0].get("dependencies", [])]
    while waiting:
        name = waiting.pop()
        if name in reached:
            continue
        reached.add(name)
        for package in packages[name]:
            waiting += [needed["name"] for needed in package.get("dependencies", [])]
    python = {}
    for name in sorted(reached):
        versions = {package["version"] for package in packages[name]}
        if len(versions) != 1:
            message = (
                f"{PYTHON_LOCK} holds {name} at {len(versions)} versions; the record states one"
            )
            raise ReleasedError(message)
        python[name] = versions.pop()
    return {"npm": npm, "python": python}


def written_by() -> str:
    """Where the record comes from, as a refusal ends: the command that writes it."""
    return f"`{COMMAND}` writes it in the engine's repository, where `mise run fix` runs it"


def load() -> dict:
    """The record this engine carries. Where the engine holds none, or one that is no JSON, the
    error's one line names the file and the command that writes it.

    A record that is JSON of another shape than the command writes is not asked about here: it
    is a fault in the engine's own record and keeps its traceback wherever it is read, as a
    fault in the engine's other own records does.
    """
    try:
        return json.loads(RECORD.read_text(encoding="utf-8"))
    except FileNotFoundError:
        found = "holds no record of what it was released on"
    except (OSError, ValueError) as error:
        found = (
            f"cannot read its record of what it was released on ({' '.join(str(error).split())})"
        )
    message = f"This engine {found}, {RECORD}: {written_by()}"
    raise ReleasedError(message)


def npm_package(name: str) -> dict:
    """What the record states of an npm package the engine runs in a film: its version and its
    integrity. A record that states none of the package, or one of the two alone, ends in an
    error whose one line names the package, the file and the command that writes it."""
    entry = load().get("npm", {}).get(name)
    if not isinstance(entry, dict) or not {"version", "integrity"} <= set(entry):
        message = (
            f"This engine's record of what it was released on, {RECORD}, states no version and "
            f"integrity of {name}: {written_by()}"
        )
        raise ReleasedError(message)
    return entry


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    if not all((root / name).is_file() for name in (MANIFEST, NPM_LOCK, PYTHON_LOCK)):
        message = f"released: {root} is no engine repository; an installed engine holds its record"
        raise SystemExit(message)
    try:
        record = compute(root)
    except ReleasedError as error:
        raise SystemExit(f"released: {error}") from error
    RECORD.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        f"{RECORD.name}: {len(record['npm'])} npm packages, {len(record['python'])} Python packages"
    )


if __name__ == "__main__":
    main()
