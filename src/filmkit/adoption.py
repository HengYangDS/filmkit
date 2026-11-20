"""What this engine release asks of a film's tracked files, listed at once.

Usage: python -m filmkit.adoption
Run at the film's root, or anywhere with `FILMKIT_ROOT` naming it, in any environment that holds
the engine. The command reads tracked files only: it needs no declaration that loads, none of
the film's npm packages, no supply and no build. It asks five questions and prints one JSON line
with every finding of each; while one stands it exits with status 1 and names them all. A file
of the film that cannot be read is a finding of the question that reads it.

- `declaration`: every problem of `content/film.toml` (`filmkit.film.problems`).
- `npm_packages`: the film's `package.json` declares each package the engine runs at the version
  the engine was released on, and its lock holds each at that version and integrity. A package
  the film alone holds is the film's.
- `python_lock`: the film pins this release by its tag, its `uv.lock` holds the engine at this
  release, and every package of the engine's runtime that the lock shares stands at the engine's
  version; the finding prints the constraints that close the difference.
- `tasks`: every engine module that a Mise task's text names after `-m` exists in this engine,
  every `filmkit.produce` command names an action the engine has, and where the tasks render a
  picture, some task asks `preflight`. A task's text is read as text, command by command: a
  line with its continuations, up to `&&`, `||`, `;`, `|` or `&`, comment lines left out. The
  order of the commands, the editions they name and what a shell would make of them are not
  judged. A `filmkit.produce` command that holds a variable outside its options and names no
  action of this engine by a word is named under `not_read`, whatever else it names, and the
  tasks' readiness is then not judged either.
- `template`: `picture/index.html` holds each text staging replaces as often as staging
  expects, and names no script or stylesheet that staging does not inline
  (`filmkit.picture.template`).

What the engine was released on is its own record (`filmkit.released`). The manifests, the locks
and the tasks are read at the film's root or above it, up to the folder that holds the film's
repository; a film outside any repository is asked at its root alone. What the command could
not compare it names under `not_read`. Whether a build is ready to render is another question,
`preflight`'s.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import tomllib
from importlib.metadata import version
from pathlib import Path

import filmkit.film as film
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture import template

QUESTIONS = ("declaration", "npm_packages", "python_lock", "tasks", "template")
# Where a film's Mise tasks stand, in the order Mise's own documentation lists the files.
TASK_FILES = (".config/mise/config.toml", "mise.toml", ".mise.toml")
PRODUCE = "filmkit.produce"
# An engine module as a task's text names it after `-m`, whatever runs it.
MODULE = re.compile(r"""(?<![\w.-])-m\s+["']?(filmkit(?:\.[A-Za-z_]\w*)*)(?=["'\s]|$)""")
# Where one command of a task's text ends.
COMMAND_END = re.compile(r"\n|&&|\|\||[;|&]")
RENDER, READINESS = "render-picture", "preflight"


class UnreadableError(ValueError):
    """A file of the film that cannot be read as what it is."""


def read_json(path: Path) -> dict:
    """The JSON object a file of the film holds."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        message = f"{path.name} cannot be read: {error}"
        raise UnreadableError(message) from error
    if not isinstance(value, dict):
        message = f"{path.name} cannot be read: it holds no JSON object"
        raise UnreadableError(message)
    return value


def read_toml(path: Path) -> dict:
    """The TOML table a file of the film holds."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        message = f"{path.name} cannot be read: {error}"
        raise UnreadableError(message) from error


def table(value: object, where: str) -> dict:
    """A table one of the film's files holds, none where the file states none, or the refusal
    that names the place where something else stands."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        message = f"{where} holds no table where one is read"
        raise UnreadableError(message)
    return value


def held(root: Path, *names: str) -> Path | None:
    """The first of the named files at a film's root or above it, no higher than the folder that
    holds the film's repository; a film outside any repository is asked at its root alone."""
    folders = [root, *root.parents]
    top = next((index for index, folder in enumerate(folders) if (folder / ".git").exists()), 0)
    for folder in folders[: top + 1]:
        for name in names:
            if (folder / name).is_file():
                return folder / name
    return None


def engine_actions() -> set[str]:
    """The actions `filmkit.produce` takes, read from the command's source: the command itself
    cannot be imported before the film's declaration loads."""
    source = Path(__file__).with_name("produce.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.AnnAssign)
            and getattr(node.target, "id", None) == "EDITION_ACTIONS"
            and isinstance(node.value, ast.Dict)
        ):
            keys = [key.value for key in node.value.keys if isinstance(key, ast.Constant)]
            return {key for key in keys if isinstance(key, str)}
    message = "filmkit.produce states no actions where the adoption command reads them"
    raise LookupError(message)


def module_exists(module: str) -> bool:
    """Whether this engine holds a module that `python -m` can run."""
    path = Path(__file__).parent.joinpath(*module.split(".")[1:])
    return path.with_suffix(".py").is_file() or (path / "__main__.py").is_file()


def npm_packages(root: Path) -> list[str]:
    """What the film's npm manifest and lock hold against the engine's record."""
    record = released.load()["npm"]
    manifest = held(root, "package.json")
    if manifest is None:
        asked = ", ".join(f"{name} {entry['version']}" for name, entry in record.items())
        return [f"no package.json at or above the film; the engine runs {asked}"]
    stated = read_json(manifest)
    declared = {
        **table(stated.get("devDependencies"), "package.json: devDependencies"),
        **table(stated.get("dependencies"), "package.json: dependencies"),
    }
    lock = manifest.with_name("package-lock.json")
    locked = None
    if lock.is_file():
        locked = table(read_json(lock).get("packages"), "package-lock.json: packages")
    found = [] if locked is not None else ["no package-lock.json beside the film's package.json"]
    for name, entry in record.items():
        asked = f"{name} {entry['version']}"
        if declared.get(name) != entry["version"]:
            has = f"{name} {declared[name]}" if name in declared else f"no {name}"
            found.append(f"package.json declares {has}; the engine runs {asked}")
            continue
        if locked is None:
            continue
        installs = locked.get(f"node_modules/{name}")
        if not isinstance(installs, dict):
            found.append(f"package-lock.json holds no {name}; the engine was released on {asked}")
        elif (installs.get("version"), installs.get("integrity")) != (
            entry["version"],
            entry["integrity"],
        ):
            found.append(
                f"package-lock.json holds {name} {installs.get('version')} with the integrity "
                f"{installs.get('integrity')}; the engine was released on {asked} with the "
                f"integrity {entry['integrity']}"
            )
    return found


def pinned(root: Path, engine: str, not_read: list[str]) -> list[str]:
    """A pin of another release than this engine's, where the film pins the engine by a tag."""
    project = held(root, "pyproject.toml")
    if project is None:
        return []
    tool = table(read_toml(project).get("tool"), "pyproject.toml: tool")
    uv = table(tool.get("uv"), "pyproject.toml: tool.uv")
    pin = table(uv.get("sources"), "pyproject.toml: tool.uv.sources").get(released.ENGINE)
    if isinstance(pin, dict) and isinstance(pin.get("tag"), str):
        if pin["tag"] != f"v{engine}":
            return [f"pyproject.toml pins filmkit {pin['tag']}; this engine is v{engine}"]
    elif pin is not None:
        not_read.append(
            "python_lock: pyproject.toml pins filmkit by something other than one tag, so the "
            "release it pins was not compared"
        )
    return []


def python_lock(root: Path, not_read: list[str]) -> list[str]:
    """The release the film pins and locks, and what its Python lock holds against the engine's
    record. A lock of another release is named only where the pin is this one: a film that pins
    another release has locked that one."""
    record, engine = released.load()["python"], version(released.ENGINE)
    found = pinned(root, engine, not_read)
    lock = held(root, "uv.lock")
    if lock is None:
        return [*found, "no uv.lock at or above the film; it locks the release it pins"]
    packages = read_toml(lock).get("package") or []
    if not isinstance(packages, list) or not all(isinstance(entry, dict) for entry in packages):
        message = "uv.lock holds no list of package tables"
        raise UnreadableError(message)
    holds: dict[str, set[str]] = {}
    for package in packages:
        holds.setdefault(package.get("name", ""), set()).add(package.get("version", ""))
    locked = holds.get(released.ENGINE, set()) - {""}
    if released.ENGINE not in holds:
        found.append("uv.lock holds no filmkit; the film locks the release it pins")
    elif not found and locked and locked != {engine}:
        stands = "/".join(sorted(locked))
        found.append(f"uv.lock holds filmkit {stands}; this engine is {engine}: lock again")
    other = sorted(name for name in record if name in holds and holds[name] != {record[name]})
    if other:
        listed = ", ".join(
            f"{name} {'/'.join(sorted(holds[name]))} (the engine: {record[name]})" for name in other
        )
        closing = ", ".join(f'"{name}=={record[name]}"' for name in other)
        count = "1 package" if len(other) == 1 else f"{len(other)} packages"
        versions = "another version" if len(other) == 1 else "other versions"
        found.append(
            f"uv.lock holds {count} of the engine's runtime at {versions} than the engine was "
            f"released on: {listed}; hold them under [tool.uv] with "
            f"constraint-dependencies = [{closing}] and lock again"
        )
    return found


def named(run: object) -> list[tuple[str, list[str]]]:
    """Each engine module that the text of a task's `run` names after `-m`, with the words that
    follow it in its command: a line with its continuations, up to `&&`, `||`, `;`, `|` or `&`.
    The text is one string or a list of strings, a comment line is left out before the lines are
    joined, and a table in a list names another task and holds no text."""
    found = []
    for text in run if isinstance(run, list) else [run]:
        if not isinstance(text, str):
            continue
        lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
        for command in COMMAND_END.split("\n".join(lines).replace("\\\n", " ")):
            for match in MODULE.finditer(command):
                words = [word.strip("\"'") for word in command[match.end() :].split()]
                found.append((match[1], [word for word in words if word]))
    return found


def tasks(root: Path, not_read: list[str]) -> list[str]:
    """The engine modules and actions the film's tasks name that this engine does not have, and
    tasks that render a picture while none asks readiness."""
    config = held(root, *TASK_FILES)
    if config is None:
        places = ", ".join(TASK_FILES)
        not_read.append(f"tasks: no Mise configuration ({places}) at or above the film")
        return []
    declared = table(read_toml(config).get("tasks"), f"{config.name}: tasks")
    actions, found = engine_actions(), []
    asked: set[str] = set()
    unread: list[str] = []
    for name, task in declared.items():
        run = task.get("run") if isinstance(task, dict) else task
        for module, words in named(run):
            if not module_exists(module):
                found.append(f"{name}: this engine has no module {module}")
            elif module == PRODUCE:
                known = [word for word in words if word in actions]
                plain = " ".join(word for word in words if not word.startswith("-"))
                if known:
                    asked.add(known[0])
                elif "$" in plain or "{{" in plain:
                    unread.append(name)
                else:
                    found.append(
                        f"{name}: {PRODUCE} is asked for no action this engine has; the "
                        f"command names {plain or 'none'}"
                    )
    not_read += [
        f"tasks: {name} holds a {PRODUCE} command with a variable that names no action of this "
        "engine by a word, so it was not compared"
        for name in dict.fromkeys(unread)
    ]
    if RENDER in asked and READINESS not in asked and not unread:
        found.append(f"the tasks render a picture and none asks {PRODUCE} {READINESS}")
    return found


def picture_template(root: Path) -> list[str]:
    """What staging would refuse in the film's picture template, all of it."""
    path = root / template.TEMPLATE
    if not path.is_file():
        return [f"no {template.TEMPLATE}"]
    try:
        return template.problems(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"{path.name} cannot be read: {error}"]


def report(root: Path) -> dict:
    """Every finding of each question for the film at a root, and what could not be compared."""
    not_read: list[str] = []
    questions = {
        "declaration": lambda: film.problems(root),
        "npm_packages": lambda: npm_packages(root),
        "python_lock": lambda: python_lock(root, not_read),
        "tasks": lambda: tasks(root, not_read),
        "template": lambda: picture_template(root),
    }
    findings = {}
    for name, ask in questions.items():
        try:
            findings[name] = ask()
        except UnreadableError as error:
            findings[name] = [str(error)]
    return {"engine": version(released.ENGINE), "findings": findings, "not_read": not_read}


def main(argv: list[str] | None = None) -> None:
    argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0]).parse_args(argv)
    result = report(repository.ROOT)
    print(json.dumps(result, ensure_ascii=False))
    listed = [f"{name}: {text}" for name, texts in result["findings"].items() for text in texts]
    if listed:
        count = f"{len(listed)} finding{'' if len(listed) == 1 else 's'}"
        engine = result["engine"]
        message = f"adoption: {count} before this film builds on filmkit {engine}: "
        raise SystemExit(message + " | ".join(listed))


if __name__ == "__main__":
    main()
