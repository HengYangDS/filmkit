"""What this engine release asks of a film's tracked files, listed at once.

Usage: python -m filmkit.adoption
Run at the film's root, or anywhere with `FILMKIT_ROOT` naming it, in any environment that holds
the engine. The command reads tracked files only: it needs no declaration that loads, none of
the film's npm packages, no supply and no build. It asks eight questions and prints one JSON line
with every finding of each; while one stands it exits with status 1 and names them all. A file
of the film that cannot be read is a finding of the question that reads it. What a film keeps as
it stands, its history and the records the engine writes, is listed under `history` and fails
nothing.

- `declaration`: every problem of `content/film.toml` (`filmkit.film.problems`).
- `runtime`: each line of the review prompt that cites the runtime's field and does not say
  "This edition", since each prompt fills it with its own edition's runtime and the editions may
  differ in length, read as text. That reading fails closed: such a line is named whatever else
  it says. A key the engine has withdrawn, `duration` or `credits_duration` in a script and
  `runtime_fit` in a cast among them, is the `declaration` question's, which the loader refuses
  (`filmkit.withdrawn`), as is a declaration that states no `credits_duration`.
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
  expects, a root that names one language's tag named with the anchor to write instead, and
  names no script or stylesheet that staging does not inline (`filmkit.picture.template`).
- `vale`: the film's Mise configuration, the file its tasks are read from, pins under `[tools]`
  the Vale the engine was released on, which the register check runs and beside which it
  refuses every other (`filmkit.register`). Only the tool the engine itself pins is read
  (`filmkit.released.VALE`), as one version, in that one file. The finding names the file and
  what it holds under that tool's name, another version or none, with the release's version: a
  pin of Vale under another name or in another file of Mise's is not read, so the finding says
  that the file holds none under this name, not that the film pins none. A film without a Mise
  configuration is named as having none.
- `editions`: each line of a tracked text file of the film, but the sources the loader reads
  (the declaration, the review prompt, the entry page and each edition's files), that names a
  file this release moves or removes by its former path, with what to write instead: the paths
  that the declaration's withdrawn `sources` and `cover` and the casts' withdrawn
  `reference_audio` still name, each other recording a cast's derivation cites, whose place is
  the identity recording's, and the files the loader names as removed
  (`filmkit.declared_sources`). It reads the declaration as TOML, so a declaration that does not
  load hides none of them; it lists the tracked files by Git, or every file but `NOT_SOURCES`
  where Git holds none of them (`tracked`), and a file that cannot be listed, or read as text
  where no other question reads it, is its finding. A line of a file in `HISTORY`, the film's
  changelog, its archived OpenSpec changes and its release record, is listed under `history`
  instead: it records what was, and the release record's paths change at the next release. A
  bridge: R2b deletes it with this module,
  when the films' build chains and test loaders are gone. Run it before removing a withdrawn
  key, which names the former paths.

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
import subprocess
from pathlib import Path

import filmkit.declared_sources as declared_sources
import filmkit.film as film
import filmkit.places as places
import filmkit.released as released
import filmkit.repository as repository
from filmkit.check import (
    UnreadableError,
    held,
    npm_packages,
    picture_template,
    python_lock,
    read_json,
    read_toml,
    runtime,
    table,
)

QUESTIONS = (
    "declaration",
    "runtime",
    "npm_packages",
    "python_lock",
    "tasks",
    "template",
    "vale",
    "editions",
)
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


def former_paths(root: Path, declared: dict) -> tuple[dict[str, str], set[str]]:
    """Each former path of a file this release moves or removes, with what to write instead, and
    the sources the loader reads, whose findings are the `declaration` question's."""
    from filmkit.declared_sources import NARRATION_COPY, REMOVED, cited_recordings
    from filmkit.places import IDENTITY

    instead = {old: f"this release removes it; {text}" for old, text in REMOVED.items()}
    owned = {film.DECLARATION}
    review = declared.get("review")
    owned |= {
        path
        for path in (declared.get("entry"), review and review.get("prompt"))
        if isinstance(path, str)
    }
    slug = str(declared.get("slug"))
    editions = table(declared.get("editions"), f"{film.DECLARATION}: editions")
    references = {places.places(code, slug).reference for code in editions}
    for code, edition in editions.items():
        edition = edition if isinstance(edition, dict) else {}
        derived = places.places(code, slug)
        sources = edition.get("sources")
        folders = {derived.folder, *([sources] if isinstance(sources, str) else [])}
        owned |= {*declared_sources.edition_files(code, slug)[:3], derived.readings}
        owned |= {f"{folder}/{name}" for folder in folders for name in film.EDITION_FILES}
        instead |= {f"{folder}/{NARRATION_COPY}": "this release removes it" for folder in folders}
        moves = [
            (f"{sources}/{name}", place)
            for name, place in ((film.SCRIPT, derived.script), (film.CAST, derived.cast))
            if isinstance(sources, str)
        ]
        moves.append((edition.get("cover"), derived.cover))
        for cast in {f"{folder}/{film.CAST}" for folder in folders}:
            try:
                held = read_json(root / cast) if (root / cast).is_file() else {}
            except UnreadableError:
                held = {}
            moves.append((held.get("reference_audio"), derived.reference))
            moves += [(path, IDENTITY) for path in cited_recordings(held) - references]
        instead |= {
            old: f"write {new}" for old, new in moves if isinstance(old, str) and old != new
        }
    return instead, owned


# What a film's folders hold besides its sources: Git's own records, built output, packages and
# environments.
NOT_SOURCES = frozenset({".git", "build", "node_modules", ".venv"})
# The film's history and the record the engine writes of its release, which a film keeps as they
# stand: a file, or a folder by its trailing slash.
HISTORY = ("CHANGELOG.md", "openspec/changes/archive/", "content/release.json")
# The files another question reads, which names each that cannot be read.
READ_ELSEWHERE = frozenset(
    {*TASK_FILES, "package.json", "package-lock.json", "uv.lock", "pyproject.toml"}
    | {"picture/index.html"}
)


def tracked(root: Path) -> list[str]:
    """The files Git tracks below a root, by their paths from it. A root that Git does not hold,
    outside any work tree, ignored by the one that encloses it, or with nothing tracked below it,
    is a copy of the film's tracked files, as `git archive` extracts one (task 10.3 extracts its
    copies below the engine's ignored `build/`): every file below it but `NOT_SOURCES` is read,
    which can only add findings, so that no file goes unread for want of Git's record."""

    def git(*command: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *command], cwd=root, capture_output=True, timeout=60)

    try:
        listed = b""
        if git("rev-parse", "--is-inside-work-tree").returncode == 0:
            ignored = git("check-ignore", "-q", "--no-index", ".").returncode
            if ignored not in (0, 1):
                raise subprocess.SubprocessError(f"git check-ignore exited with {ignored}")
            if ignored == 1:
                files = git("ls-files", "-z")
                files.check_returncode()
                listed = files.stdout
    except (OSError, subprocess.SubprocessError) as error:
        message = f"the film's tracked files cannot be listed: {error}"
        raise UnreadableError(message) from error
    return sorted(path for path in listed.decode("utf-8").split("\0") if path) or sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not NOT_SOURCES & set(path.relative_to(root).parts)
    )


def editions(root: Path, history: list[str]) -> list[str]:
    """Each line of the film's tracked text, but the sources the loader reads, that names a file
    this release moves or removes by its former path, with what to write instead, and each file
    that cannot be read as text and that no other question reads (`READ_ELSEWHERE`, and the
    declaration, which the `declaration` question names). Such a line of a file in `HISTORY` is
    added to `history` instead. A file with a NUL byte in its first 8000 is binary and not
    read."""
    try:
        declared = read_toml(root / film.DECLARATION)
    except UnreadableError:
        return []
    instead, owned = former_paths(root, declared)
    found = []
    for path in tracked(root):
        if path in owned or not (root / path).is_file():
            continue
        with (root / path).open("rb") as file:
            if b"\0" in file.read(8000):
                continue
        data = (root / path).read_bytes()
        try:
            lines = data.decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            if path not in READ_ELSEWHERE:
                found.append(f"{path} cannot be read as text: {error}")
            continue
        kept = any(path.startswith(at) if at.endswith("/") else path == at for at in HISTORY)
        (history if kept else found).extend(
            f"{path}:{number} names {old}; {what}"
            for number, line in enumerate(lines, 1)
            for old, what in instead.items()
            if old in line
        )
    return found


def report(root: Path) -> dict:
    """Every finding of each question for the film at a root, what could not be compared, and
    each line of the film's history that names a former path."""
    not_read: list[str] = []
    history: list[str] = []
    questions = {
        "declaration": lambda: film.problems(root),
        "runtime": lambda: runtime(root),
        "npm_packages": lambda: npm_packages(root),
        "python_lock": lambda: python_lock(root, not_read),
        "tasks": lambda: tasks(root, not_read),
        "template": lambda: picture_template(root),
        "vale": lambda: vale(root),
        "editions": lambda: editions(root, history),
    }
    findings = {}
    for name, ask in questions.items():
        try:
            findings[name] = ask()
        except UnreadableError as error:
            findings[name] = [str(error)]
    return {
        "engine": released.version(),
        "findings": findings,
        "not_read": not_read,
        "history": history,
    }


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
