"""What this engine release asks of a film's tracked files, listed at once.

Usage: python -m filmkit.adoption
Run at the film's root, or anywhere with `FILMKIT_ROOT` naming it, in any environment that holds
the engine. The command reads tracked files only: it needs no declaration that loads, none of
the film's npm packages, no supply and no build. It asks seven questions and prints one JSON line
with every finding of each; while one stands it exits with status 1 and names them all. A file
of the film that cannot be read is a finding of the question that reads it.

- `declaration`: every problem of `content/film.toml` (`filmkit.film.problems`).
- `runtime`: what the film's scripts, casts and review prompt state of the runtime and the
  credits that this release removes or moves, read as text: each edition's script that declares
  `duration` or `credits_duration` and each cast that declares `runtime_fit`
  (`filmkit.film.WITHDRAWN`), each named with what to do instead; and each line of the review
  prompt that cites the runtime's field and does not say "This edition", since each prompt fills
  it with its own edition's runtime and the two editions may differ in length. That reading fails
  closed: such a line is named whatever else it says. A declaration that states no
  `credits_duration`, and a script or cast that the declaration names and that is missing, are
  the `declaration` question's.
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
- `vale`: the film's Mise configuration, the file its tasks are read from, pins under `[tools]`
  the Vale the engine was released on, which the register check runs and beside which it
  refuses every other (`filmkit.register`). Only the tool the engine itself pins is read
  (`filmkit.released.VALE`), as one version, in that one file. The finding names the file and
  what it holds under that tool's name, another version or none, with the release's version: a
  pin of Vale under another name or in another file of Mise's is not read, so the finding says
  that the file holds none under this name, not that the film pins none. A film without a Mise
  configuration is named as having none.

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
import string
import tomllib
from pathlib import Path

import filmkit.film as film
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture import template
from filmkit.review import RUNTIME_FIELD

QUESTIONS = ("declaration", "runtime", "npm_packages", "python_lock", "tasks", "template", "vale")
# Where a film's Mise tasks stand, in the order Mise's own documentation lists the files.
TASK_FILES = (".config/mise/config.toml", "mise.toml", ".mise.toml")
PRODUCE = "filmkit.produce"
# The folder that holds the engine's modules.
PACKAGE = Path(__file__).parent
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


def module_path(module: str, package: Path = PACKAGE) -> Path:
    """Where the engine holds one of its modules, the suffix of its file left to the caller."""
    return package.joinpath(*module.split(".")[1:])


def stores(tree: ast.Module) -> list[str]:
    """Every name that a module's source binds by an assignment, once for each binding."""
    found = (node for node in ast.walk(tree) if isinstance(node, ast.Name))
    return [node.id for node in found if isinstance(node.ctx, ast.Store)]


def stated(tree: ast.Module, name: str, where: str) -> ast.expr:
    """What a module's source states under a name: the value of the one statement that binds
    the name, at the module's top level. A name bound nowhere, more than once or below the top
    level is refused: what it holds when the module has run cannot be read from the source."""
    values = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign | ast.AnnAssign)
        and node.value is not None
        and [
            getattr(target, "id", None)
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        ]
        == [name]
    ]
    if values and stores(tree).count(name) == 1:
        return values[0]
    message = f"{where} states {name} in no one statement that the adoption command can read"
    raise LookupError(message)


def action(key: ast.expr | None, modules: dict[str, Path]) -> str:
    """The action that one key of the command's table names."""
    match key:
        case ast.Constant(value=str(name)):
            return name
        case ast.Attribute(value=ast.Name(id=owner), attr=name) if owner in modules:
            source = ast.parse(modules[owner].read_text(encoding="utf-8"))
            match stated(source, name, modules[owner].name):
                case ast.Constant(value=str(value)):
                    return value
    form = ast.unparse(key) if key else "another table's entries"
    message = f"{PRODUCE} names an action by {form}, which the adoption command cannot read"
    raise LookupError(message)


def engine_actions(command: Path = PACKAGE / "produce.py") -> set[str]:
    """The actions `filmkit.produce` takes, read from the command's source: the command itself
    cannot be imported before the film's declaration loads. The command states its table once,
    at its top level, and names each action there by a string, or by a name that a module of
    the engine states once as a string and that the command imports at its top level under a
    name it binds nowhere else. Any other form of the table or of a key is refused, never left
    out. What the command does to the table after stating it, and a name bound again by an
    import or a definition, are not read: the engine's tests hold the command's own table to
    this reading."""
    source = ast.parse(command.read_text(encoding="utf-8"))
    table = stated(source, "EDITION_ACTIONS", PRODUCE)
    if not isinstance(table, ast.Dict):
        message = f"{PRODUCE} states its actions in no table that the adoption command can read"
        raise LookupError(message)
    modules: dict[str, Path] = {}
    for alias in (
        alias for node in source.body if isinstance(node, ast.Import) for alias in node.names
    ):
        path = module_path(alias.name, command.parent).with_suffix(".py")
        if alias.asname and alias.name.split(".")[0] == PACKAGE.name and path.is_file():
            modules[alias.asname] = path
    for name in stores(source):
        modules.pop(name, None)
    return {action(key, modules) for key in table.keys}


def module_exists(module: str) -> bool:
    """Whether this engine holds a module that `python -m` can run."""
    path = module_path(module)
    return path.with_suffix(".py").is_file() or (path / "__main__.py").is_file()


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
        "the runtime of the prompt's own edition, and the two editions may differ in length: "
        f'reword the line, as "This edition: exactly {field} s"'
        for number, line in enumerate(text.splitlines(), 1)
        if RUNTIME_FIELD in cited(line) and "this edition" not in line.casefold()
    ]


def runtime(root: Path) -> list[str]:
    """What the film's scripts, casts and review prompt state of the runtime and the credits that
    this release removes or moves: edition by edition, each key of `filmkit.film.WITHDRAWN` that
    the edition's script or cast declares, with what to do instead, then each line of the review
    prompt that ties the runtime to no one edition (`untied_runtime`). Read as text, so that no
    declaration need load; the declaration's own `credits_duration` and a file it names that is
    missing are the `declaration` question's."""
    declared = read_toml(root / film.DECLARATION)
    found = []
    editions = table(declared.get("editions"), f"{film.DECLARATION}: editions")
    for code, edition in editions.items():
        sources = table(edition, f"{film.DECLARATION}: editions.{code}").get("sources")
        for name, keys in film.WITHDRAWN.items():
            path = root / str(sources) / name
            if not isinstance(sources, str) or not path.is_file():
                continue
            held = read_json(path)
            found += [
                f"{sources}/{name} declares {key}; {instead}"
                for key, instead in keys.items()
                if key in held
            ]
    return found + untied_runtime(root, declared)


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


def vale(root: Path) -> list[str]:
    """The film's pin of the Vale that the register check runs, against the engine's record:
    another version, another form of pin or none under that tool's name in the one file read,
    each named with the release's version."""
    asked = released.vale()
    on = f"the engine was released on Vale {asked}"
    pin = f'pin "{released.VALE}" = "{asked}" under [tools]'
    config = held(root, *TASK_FILES)
    if config is None:
        places = ", ".join(TASK_FILES)
        return [f"the film has no Mise configuration ({places}) at or above it; {on}: {pin}"]
    tools = table(read_toml(config).get("tools"), f"{config.name}: tools")
    pinned = released.pinned_vale(tools)
    if pinned is None:
        return [f'{config.name} holds no "{released.VALE}" version under [tools]; {on}: {pin}']
    return [] if pinned == asked else [f"{config.name} pins Vale {pinned}; {on}"]


def report(root: Path) -> dict:
    """Every finding of each question for the film at a root, and what could not be compared."""
    not_read: list[str] = []
    questions = {
        "declaration": lambda: film.problems(root),
        "runtime": lambda: runtime(root),
        "npm_packages": lambda: npm_packages(root),
        "python_lock": lambda: python_lock(root, not_read),
        "tasks": lambda: tasks(root, not_read),
        "template": lambda: picture_template(root),
        "vale": lambda: vale(root),
    }
    findings = {}
    for name, ask in questions.items():
        try:
            findings[name] = ask()
        except UnreadableError as error:
            findings[name] = [str(error)]
    return {"engine": released.version(), "findings": findings, "not_read": not_read}


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
