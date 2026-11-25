"""The run record of schema 1, the partial record, and how one is stated, written and read.

A run record states one run of one build node, for one edition or for the film: each input and
output by its path below the film's root, its size, its modification time (`mtime_ns`) and its
SHA-256, a folder by the digest of the members its pattern names, a top-level table of the
film's declaration by the digest of its canonical JSON (`DeclarationTable`); the engine that
ran, its `released.json` digest and the node's model pins; the outcome and the line the command
ended with; the run's start, seconds, phases, settings and 1-minute load at both ends, as the
seam measured them (`filmkit.graph.runs.Run`); and the host class as measured
(`filmkit.graph.host`). A partial
record states a run of part of a node: its outputs as they stand after it, its outcome and its
time, and no inputs, so it accounts for what it wrote and never makes its node fresh.

A record is written whole through `repository.write`, an edition's node's at
build/evidence/records/editions/<code>/<node>.json and a film-wide node's, whose record names no
edition, at build/evidence/records/film/<node>.json; a partial one beside it as
<node>.partial.json. A record that cannot be read, or one of another schema, is `Unreadable`.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import tomllib
import typing
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError

import filmkit.released as released
import filmkit.repository as repository

if TYPE_CHECKING:
    import os
    from collections.abc import Iterator

# The schema this engine writes and reads; a record of any other is unreadable.
SCHEMA = 1
# The folder of the run records below the film's root, a folder for each edition by its code, and
# the folder of the film-wide nodes' records.
FOLDER = Path("build/evidence/records/editions")
FILM_FOLDER = Path("build/evidence/records/film")
# How a run ended: its owner passed, its owner refused with one line, or it failed otherwise.
Outcome = Literal["pass", "refuse", "error"]
# A node's host class as host rule 3 measures it, and the plan's word for one never measured.
HostClass = Literal["light", "heavy", "gpu"]
# The fields a run record takes from the seam's measurement of the run (`runs.Run.measured`).
MEASURED = ("started_at", "seconds", "load_1m", "phases", "settings")


class Unreadable(ValueError):
    """A record that is no JSON object of this schema."""


class Stated(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class FileState(Stated):
    """A file as a run found it: its path below the root, size, modification time and digest."""

    path: str
    size: int
    mtime_ns: int
    sha256: str


class Member(Stated):
    """A member of a folder, by its path below the folder."""

    path: str
    size: int
    mtime_ns: int
    sha256: str


class FolderState(Stated):
    """A folder by the members its pattern names: their digest, and each member."""

    path: str
    pattern: str
    sha256: str
    members: tuple[Member, ...]


State = FileState | FolderState


class Engine(Stated):
    """The engine that ran: its version, its `released.json` digest and the node's model pins,
    each snapshot by its repository and revision."""

    version: str
    released_sha256: str
    pins: dict[str, str]


class Measured(Stated):
    """The raw measures of host rule 3: CPU seconds of the run and its waited-for children,
    their ratio to the wall time, how many samples of the process tree were taken, and the
    longest run of consecutive samples above two cores."""

    cpu_seconds: float
    cpu_per_wall: float
    samples: int
    above: int


class Common(Stated):
    """What a run record and a partial record both state."""

    schema_: Literal[1] = Field(default=SCHEMA, alias="schema")
    node: str
    edition: str | None
    engine: Engine
    outputs: dict[str, State]
    outcome: Outcome
    refusal: str | None
    started_at: str
    seconds: float
    load_1m: dict[str, float | None]
    phases: dict[str, float]
    settings: dict[str, object]
    measured: Measured
    host_class: HostClass = Field(alias="class")


class RunRecord(Common):
    """One whole run of a node. `carried` names each input that a rewriter read as its own
    previous run wrote it, with the digest that its chain of runs first read from another writer,
    so that the earlier writer's binding holds through a rewriter run again (design decision 5)."""

    inputs: dict[str, State]
    carried: dict[str, str] = Field(default_factory=dict)


class PartialRecord(Common):
    """A run of part of a node, or of another place or size than its own."""

    partial: Literal[True] = True


class Folder(NamedTuple):
    """A folder input or output: its path and the pattern that names its members."""

    path: Path
    pattern: str


class DeclarationTable(NamedTuple):
    """A top-level table of the film's declaration as an input: the declaration's file and the
    table's name as the file names it, `identity` for the declaration's own values (design
    decision 12 of build-a-film-by-its-verbs). A record states it at `<file>#<table>`, with the
    file's size and time and the digest of the table's canonical JSON."""

    path: Path
    name: str


# The table of the declaration's own values, which no table of the file holds.
IDENTITY = "identity"


def table_names(model: type[BaseModel]) -> dict[str, str]:
    """Each top-level field of the declaration's model by the table it belongs to: a field that
    holds a table (a model or a mapping) is the table of its name in the file, every other field
    is of `identity`."""
    found = {}
    for name, field in model.model_fields.items():
        kind = typing.get_origin(field.annotation) or field.annotation
        holds = kind is dict or isinstance(kind, type) and issubclass(kind, BaseModel)
        found[name] = (field.alias or name) if holds else IDENTITY
    return found


def canonical(value: object) -> str:
    """The SHA-256 of a value's JSON with sorted keys."""
    return repository.content_sha(json.dumps(value, sort_keys=True, ensure_ascii=False))


def table_digests(declaration: BaseModel) -> dict[str, str]:
    """Each table of a loaded declaration by the digest of its canonical JSON
    (`model_dump(mode="json")`, sorted keys)."""
    dumped = declaration.model_dump(mode="json", by_alias=True)
    grouped: dict[str, dict] = {}
    for name, table in table_names(type(declaration)).items():
        field = type(declaration).model_fields[name].alias or name
        if table == IDENTITY:
            grouped.setdefault(IDENTITY, {})[field] = dumped[field]
        else:
            grouped[table] = dumped[field]
    return {table: canonical(value) for table, value in grouped.items()}


# Each declaration's table digests, by its path, size and time.
_TABLES: dict[tuple[str, int, int], dict[str, str]] = {}


def tables_of(path: Path, found: os.stat_result) -> dict[str, str]:
    """The table digests of the declaration at a path, at the size and time it has: of the film it
    loads, or, for one that does not load, of its TOML's tables, so that a change still shows."""
    named = (str(path), found.st_size, found.st_mtime_ns)
    if named not in _TABLES:
        import filmkit.film as film

        root = Path(path).parents[len(Path(repository.DECLARATION).parts) - 1]
        loaded, _ = film.read(root)
        if loaded is not None:
            _TABLES[named] = table_digests(loaded)
        else:
            raw = tomllib.loads(Path(path).read_text(encoding="utf-8"))
            own = {k: v for k, v in raw.items() if not isinstance(v, dict)}
            tables = {k: v for k, v in raw.items() if isinstance(v, dict)}
            _TABLES[named] = {k: canonical(v) for k, v in {**tables, IDENTITY: own}.items()}
    return _TABLES[named]


def table_state(table: DeclarationTable, known: FileState | None = None) -> FileState:
    """A table of the declaration as it stands: the file's size and time, the table's digest
    taken from `known` where they are the ones `known` states."""
    found = table.path.stat()
    same = known is not None and (known.size, known.mtime_ns) == (found.st_size, found.st_mtime_ns)
    return FileState(
        path=f"{below_root(table.path)}#{table.name}",
        size=found.st_size,
        mtime_ns=found.st_mtime_ns,
        sha256=known.sha256 if same and known else tables_of(table.path, found).get(table.name, ""),
    )


def file_of(place: Path | Folder | DeclarationTable) -> Path:
    """The file or folder a declared place names, a table's declaration for a table."""
    return Path(place.path if isinstance(place, (Folder, DeclarationTable)) else place)


def digest(path: Path) -> str:
    """The SHA-256 of a file's bytes, read in blocks."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


# The digests taken while `once` holds, by path, size and time.
_TAKEN: contextvars.ContextVar[dict | None] = contextvars.ContextVar("digests", default=None)


@contextlib.contextmanager
def once() -> Iterator[dict]:
    """Hash each file once while the block runs, at the size and time it then had, though
    several records state it; the digests taken, by path, size and time."""
    taken: dict = {}
    token = _TAKEN.set(taken)
    try:
        yield taken
    finally:
        _TAKEN.reset(token)


def taken(path: Path, found: os.stat_result) -> str:
    """A file's digest: hashed, or within `once` as it was first hashed at this size and time."""
    held = _TAKEN.get()
    if held is None:
        return digest(path)
    named = (str(path), found.st_size, found.st_mtime_ns)
    if named not in held:
        held[named] = digest(path)
    return held[named]


def below_root(path: Path) -> str:
    """A path as a record states it: below the film's root, both sides resolved, or absolute."""
    real, root = Path(path).resolve(), Path(repository.ROOT).resolve()
    return real.relative_to(root).as_posix() if real.is_relative_to(root) else str(real)


def state(path: Path, known: FileState | Member | None = None) -> FileState:
    """A file as it stands; its digest is taken from `known` where the size and time are
    the ones `known` states, and hashed otherwise."""
    found = path.stat()
    same = known is not None and (known.size, known.mtime_ns) == (found.st_size, found.st_mtime_ns)
    return FileState(
        path=below_root(path),
        size=found.st_size,
        mtime_ns=found.st_mtime_ns,
        sha256=known.sha256 if same and known else taken(path, found),
    )


def members(folder: Folder) -> list[Path]:
    """The files of a folder that its pattern names, in the order of their relative paths."""
    named = (path for path in folder.path.glob(folder.pattern) if path.is_file())
    return sorted(named, key=lambda path: path.relative_to(folder.path).as_posix())


def folder_state(folder: Folder, known: FolderState | None = None) -> FolderState:
    """A folder as it stands: each member as `state` states it, and their digest, the SHA-256 of
    their sorted relative paths, sizes and digests, which no time enters."""
    was = {member.path: member for member in (known.members if known else ())}
    stated = []
    for path in members(folder):
        name = path.relative_to(folder.path).as_posix()
        found = state(path, was.get(name))
        stated.append(Member(**found.model_dump(exclude={"path"}), path=name))
    listing = "".join(f"{m.path}\t{m.size}\t{m.sha256}\n" for m in stated)
    return FolderState(
        path=below_root(folder.path),
        pattern=folder.pattern,
        sha256=repository.content_sha(listing),
        members=tuple(stated),
    )


def stated(path: Path | Folder | DeclarationTable, known: State | None = None) -> State:
    """A file, a folder or a table as it stands, digests taken from `known` where they still
    hold."""
    if isinstance(path, Folder):
        return folder_state(path, known if isinstance(known, FolderState) else None)
    if isinstance(path, DeclarationTable):
        return table_state(path, known if isinstance(known, FileState) else None)
    return state(path, known if isinstance(known, FileState) else None)


def engine(pins: dict[str, str]) -> Engine:
    """The running engine: its version, its `released.json` digest and the pins given."""
    return Engine(version=released.version(), released_sha256=digest(released.RECORD), pins=pins)


def place(node: str, code: str | None, *, partial: bool = False) -> Path:
    """Where a node's record of an edition stands, or of the film where no edition is named, or
    its partial record."""
    name = f"{node}.partial.json" if partial else f"{node}.json"
    folder = FILM_FOLDER if code is None else FOLDER / code
    return Path(repository.ROOT) / folder / name


def write(record: RunRecord | PartialRecord) -> None:
    """Write a record whole, replacing the one that stood."""
    partial = isinstance(record, PartialRecord)
    path = place(record.node, record.edition, partial=partial)
    repository.write(path, record.model_dump(mode="json", by_alias=True))


def read(path: Path) -> RunRecord | PartialRecord:
    """The record at a path; `Unreadable` for one that is no JSON object of this schema, and
    `FileNotFoundError` where none stands."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise Unreadable(f"{below_root(path)} is no JSON: {error}") from None
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        found = value.get("schema") if isinstance(value, dict) else None
        raise Unreadable(f"{below_root(path)} is of schema {found!r}, not {SCHEMA}")
    model = PartialRecord if value.get("partial") is True else RunRecord
    try:
        return model.model_validate(value)
    except ValidationError as error:
        raise Unreadable(f"{below_root(path)} does not hold a record: {error}") from None


class Compared(NamedTuple):
    """One file of a record against the file as it stands: `same` by size and time, or by its
    digest when every file is hashed; `touched` with another size or time and the same digest;
    `changed`; `missing`; or `blind`, the same size and time with another digest."""

    side: str
    name: str
    path: str
    result: str


class Judgment(NamedTuple):
    """A record judged against the files as they stand: each reason it is stale, none for a
    fresh record, each file it states as compared, and the reasons that concern no one file."""

    reasons: tuple[str, ...]
    files: tuple[Compared, ...]
    own: tuple[str, ...] = ()


# What a reason says of a file of each result that makes its record stale.
SAYS = {
    "changed": "changed",
    "missing": "missing",
    "blind": "changed while keeping its size and time",
}


def at(recorded: State) -> Path:
    """The file or folder a record states, below the film's root; a table's declaration for a
    table."""
    return Path(repository.ROOT) / recorded.path.partition("#")[0]


def placed(recorded: State) -> Path | Folder | DeclarationTable:
    """What a record states, as a place to state again."""
    path = at(recorded)
    if isinstance(recorded, FolderState):
        return Folder(path, recorded.pattern)
    _, mark, name = recorded.path.partition("#")
    return DeclarationTable(path, name) if mark else path


def standing(recorded: State) -> tuple[tuple[int, int], ...] | None:
    """The sizes and times of what a record states as it stands now, or None where it is gone."""
    path = at(recorded)
    if isinstance(recorded, FileState):
        if not path.is_file():
            return None
        found = path.stat()
        return ((found.st_size, found.st_mtime_ns),)
    if not path.is_dir():
        return None
    folder = Folder(path, recorded.pattern)
    return tuple((p.stat().st_size, p.stat().st_mtime_ns) for p in members(folder))


def compare(side: str, name: str, recorded: State, *, full: bool) -> Compared:
    """One stated file or folder against what stands: hashed only where a size or time differs,
    or, with `full`, always."""
    stats = standing(recorded)
    if stats is None:
        return Compared(side, name, recorded.path, "missing")
    held = (
        ((recorded.size, recorded.mtime_ns),)
        if isinstance(recorded, FileState)
        else tuple((m.size, m.mtime_ns) for m in recorded.members)
    )
    if stats == held and not full:
        return Compared(side, name, recorded.path, "same")
    now = stated(placed(recorded))
    if now.sha256 == recorded.sha256:
        return Compared(side, name, recorded.path, "same" if stats == held else "touched")
    return Compared(side, name, recorded.path, "blind" if stats == held else "changed")


def engine_reasons(recorded: Engine, running: Engine) -> list[str]:
    """Why a record's engine is not the running one."""
    reasons = []
    if recorded.version != running.version:
        reasons.append(f"another engine: recorded {recorded.version}, running {running.version}")
    if recorded.released_sha256 != running.released_sha256:
        reasons.append("another released.json: the engine's pins differ")
    if recorded.pins != running.pins:
        reasons.append("other model pins")
    return reasons


def judge(
    record: RunRecord | PartialRecord | Unreadable | None,
    *,
    declared: dict[str, str] | None,
    running: Engine,
    full: bool = False,
    settled: frozenset[tuple[str, str]] = frozenset(),
) -> Judgment:
    """A record against the files as they stand (design decision 6 of record-every-run).

    Stale, with each reason named, where no record stands or it cannot be read, its run did not
    pass, it names another engine, `released.json` or pins, the inputs its way declares
    (`declared`, each name's path below the root) are not the ones it recorded, or an input or
    output is missing or changed. Each file is compared by size and time and hashed only where
    they differ, unless `full` asks for every file to be hashed, which alone sees a change that
    kept both. A partial record states no inputs, and its inputs are not compared. A file that
    `settled` names by its side and name is left to the caller, which judges it otherwise.
    """
    if record is None:
        return Judgment(("no record",), (), ("no record",))
    if isinstance(record, Unreadable):
        unread = (f"unreadable record: {record}",)
        return Judgment(unread, (), unread)
    reasons = (
        [] if record.outcome == "pass" else [f"its run ended with the outcome {record.outcome}"]
    )
    reasons += engine_reasons(record.engine, running)
    inputs = record.inputs if isinstance(record, RunRecord) else {}
    if declared is not None and isinstance(record, RunRecord):
        held = {name: state.path for name, state in inputs.items()}
        names = sorted({*held, *declared} - {n for n in held if declared.get(n) == held[n]})
        if names:
            reasons.append(
                f"the inputs its way declares differ from those it recorded: {', '.join(names)}"
            )
    stated = [("input", n, s) for n, s in inputs.items()]
    stated += [("output", n, s) for n, s in record.outputs.items()]
    files = [
        compare(side, name, state, full=full)
        for side, name, state in stated
        if (side, name) not in settled
    ]
    own = tuple(reasons)
    reasons += [f"{f.side} {f.name} {SAYS[f.result]}: {f.path}" for f in files if f.result in SAYS]
    return Judgment(tuple(reasons), tuple(files), own)
