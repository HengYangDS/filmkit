"""`filmkit check`: the film's light gates on its sources, every finding at once, the run of the
film-wide node `check` (design decision 6 of build-a-film-by-its-verbs).

It asks, in one run and whatever an earlier question found:

- `declaration`: every problem of the declaration as the loader reads it (`filmkit.film.read`).
  Where its fields load, the other questions are asked of the film it reads, problems and all;
  where they do not, the questions that read the loaded film are not asked.
- `concepts`: the concept contract (`filmkit.concepts`).
- `register`: the formal register, with the Vale the engine pins (`filmkit.register`).
- `readings`: each edition's readings and names, and its occurrence plan
  (`filmkit.narration.readings`).
- `anchors`: the rules of every script's anchors (`filmkit.narration.anchors`).
- `picture_reads`: what each edition's picture reads of its anchors over the timeline the engine
  derives from the edition's script (`filmkit.picture.anchor_reads`), whatever the anchors' rules
  found. A picture that does not load, and a scene that throws, are reported as not judged and
  refuse nothing.
- `npm_packages`, `python_lock`: the film's npm manifest and lock and its Python pin and lock
  against the engine's record of what it was released on (`filmkit.released`).
- `template`: what staging would refuse in the film's picture template (`filmkit.picture.template`).
- `runtime`: each line of the review prompt that cites the runtime's field and does not say "This
  edition", since each prompt fills it with its own edition's runtime, read as text.

The verdict is `build/evidence/check/verdict.json`: the outcome, each question's findings and what
the picture reads did not judge, with no digest and no time, so that a passing run after an edit
elsewhere writes the same bytes. Each edition's occurrence plan is the readings check's. With
`write` false nothing is written: the findings go to the caller alone. It needs no model, no
browser, no dictionary, no FFmpeg and no build.
"""

from __future__ import annotations

import json
import re
import string
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.film as film
import filmkit.released as released
import filmkit.repository as repository

if TYPE_CHECKING:
    from collections.abc import Callable

# The verdict, below the film's root.
VERDICT = Path("build/evidence/check/verdict.json")
# The questions, in the order they are asked and reported.
QUESTIONS = (
    "declaration",
    "concepts",
    "register",
    "readings",
    "anchors",
    "picture_reads",
    "npm_packages",
    "python_lock",
    "template",
    "runtime",
)
# What a question says that the declaration's fields keep it from asking.
NOT_LOADED = "not asked: the declaration's fields do not load"


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


def cited(line: str) -> set[str]:
    """The fields a line of a `str.format` template cites, by their first names. A line that the
    format cannot parse is taken to cite every name it holds after a brace, so that it is read,
    not passed over."""
    try:
        fields = [name for _, name, _, _ in string.Formatter().parse(line) if name is not None]
    except ValueError:
        return set(re.findall(r"\{([A-Za-z_]\w*)", line))
    return {re.split(r"[.\[]", name, maxsplit=1)[0] for name in fields}


def untied_runtime(root: Path, declared: dict) -> list[str]:
    """Each line of the film's review prompt that cites the runtime's field and does not say
    "This edition", in any case: each prompt fills the field with its own edition's runtime."""
    from filmkit.review import RUNTIME_FIELD

    review = table(declared.get("review"), f"{film.DECLARATION}: review")
    prompt = review.get("prompt")
    if not isinstance(prompt, str) or not (root / prompt).is_file():
        return []
    try:
        text = (root / prompt).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        message = f"{Path(prompt).name} cannot be read: {error}"
        raise UnreadableError(message) from error
    field = f"{{{RUNTIME_FIELD}}}"
    return [
        f'{prompt}:{number} cites {field} in a line that does not say "This edition"; {field} is '
        "the runtime of the prompt's own edition, and the editions may differ in length: "
        f'reword the line, as "This edition: exactly {field} s"'
        for number, line in enumerate(text.splitlines(), 1)
        if RUNTIME_FIELD in cited(line) and "this edition" not in line.casefold()
    ]


def runtime(root: Path) -> list[str]:
    """Each line of the review prompt that ties the runtime to no one edition (`untied_runtime`),
    read as text, so that no declaration need load."""
    return untied_runtime(root, read_toml(root / film.DECLARATION))


def npm_packages(root: Path) -> list[str]:
    """What the film's npm manifest and lock hold against the engine's record."""
    record = released.load()["npm"]
    manifest = held(root, released.MANIFEST)
    if manifest is None:
        asked = ", ".join(f"{name} {entry['version']}" for name, entry in record.items())
        return [f"no package.json at or above the film; the engine runs {asked}"]
    stated = read_json(manifest)
    declared = {
        **table(stated.get("devDependencies"), "package.json: devDependencies"),
        **table(stated.get("dependencies"), "package.json: dependencies"),
    }
    lock = manifest.with_name(released.NPM_LOCK)
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
    record, engine = released.load()["python"], released.version()
    found = pinned(root, engine, not_read)
    lock = held(root, released.PYTHON_LOCK)
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


def picture_template(root: Path) -> list[str]:
    """What staging would refuse in the film's picture template, all of it."""
    from filmkit.picture import template

    path = root / template.TEMPLATE
    if not path.is_file():
        return [f"no {template.TEMPLATE}"]
    try:
        return template.problems(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"{path.name} cannot be read: {error}"]


def loaded(root: Path) -> list[str]:
    """Every problem of the declaration at a root; where its fields load, the film it reads is the
    engine's film for this process (`filmkit.film.FILM`), so that the other questions are asked of
    it, problems and all."""
    declared, problems = film.read(root)
    if declared is not None and "FILM" not in vars(film):
        film.FILM = declared
    return problems


def lines(ask: Callable[[], object], *refusals: type[Exception]) -> list[str]:
    """A question's findings: none where it passes, else the lines of its refusal."""
    try:
        ask()
    except refusals as error:
        return list(getattr(error, "lines", None) or str(error).splitlines())
    return []


def words(write: bool) -> tuple[dict[str, list[str]], object]:
    """The questions of the film's words, each with its findings, and what the picture reads
    judged, or why it was not asked."""
    import filmkit.concepts as concepts
    import filmkit.register as register
    import filmkit.sources as sources
    from filmkit.narration import anchors, readings
    from filmkit.picture import anchor_reads
    from filmkit.production import CODES

    found = {
        "concepts": lines(concepts.check, concepts.ConceptError, sources.SourceError),
        "register": lines(register.check, register.RegisterError),
        "readings": [
            f"{code}: {line}"
            for code in CODES
            for line in lines(lambda c=code: readings.check(c, write=write), readings.ReadingError)
        ],
        "anchors": lines(anchors.require_editions, anchors.AnchorError),
        "picture_reads": [],
    }
    try:
        reads = anchor_reads.check(rules=False)
    except anchors.AnchorError as error:
        found["picture_reads"], reads = str(error).splitlines(), "refuse"
    return found, reads


def asked(root: Path, *, write: bool = True) -> dict:
    """Every question asked of the film at a root: the verdict, its outcome `pass` or `refuse`,
    each question's findings and what the picture reads judged. With `write` each edition's
    occurrence plan is written; nothing else is."""
    not_read: list[str] = []
    found = {"declaration": loaded(root)}
    reads: object = NOT_LOADED
    if "FILM" in vars(film):
        more, reads = words(write)
        found |= more
    else:
        found |= dict.fromkeys(QUESTIONS[1:6], [NOT_LOADED])
    others = {
        "npm_packages": lambda: npm_packages(root),
        "python_lock": lambda: python_lock(root, not_read),
        "template": lambda: picture_template(root),
        "runtime": lambda: runtime(root),
    }
    for name, ask in others.items():
        try:
            found[name] = ask()
        except UnreadableError as error:
            found[name] = [str(error)]
    refused = any(found[name] for name in QUESTIONS)
    return {
        "outcome": "refuse" if refused else "pass",
        "findings": {name: found[name] for name in QUESTIONS},
        "picture_reads": reads,
        "not_read": not_read,
    }


def summary(verdict: dict) -> str:
    """A refused verdict in one line: how many findings, each with its question."""
    listed = [f"{name}: {text}" for name, texts in verdict["findings"].items() for text in texts]
    count = f"{len(listed)} finding{'' if len(listed) == 1 else 's'}"
    return f"check: {count}: " + " | ".join(listed)


def run(root: Path | None = None) -> dict:
    """The node's run: ask every question, write the verdict and the occurrence plans, and refuse
    in one line where a question found anything."""
    verdict = asked(root or repository.ROOT)
    repository.write(VERDICT, verdict)
    if verdict["outcome"] != "pass":
        raise SystemExit(summary(verdict))
    return verdict
