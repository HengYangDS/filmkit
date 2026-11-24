"""The run record of schema 1, the partial record, and how one is stated, written and read.

A run record states one run of one build node for one edition: each input and output by its
path below the film's root, its size, its modification time (`mtime_ns`) and its SHA-256, a
folder by the digest of the members its pattern names; the engine that ran, its `released.json`
digest and the node's model pins; the outcome and the line the command ended with; the seconds,
phases, settings and 1-minute load its duration record states, from the same measurement
(`filmkit.durations.Run`); and the host class as measured (`filmkit.graph.host`). A partial
record states a run of part of a node: its outputs as they stand after it, its outcome and its
time, and no inputs, so it accounts for what it wrote and never makes its node fresh.

A record is written whole through `repository.write`, at
build/evidence/records/editions/<code>/<node>.json, a partial one beside it as
<node>.partial.json. A record that cannot be read, or one of another schema, is `Unreadable`.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
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
# The folder of the run records below the film's root, a folder for each edition by its code.
FOLDER = Path("build/evidence/records/editions")
# How a run ended: its owner passed, its owner refused with one line, or it failed otherwise.
Outcome = Literal["pass", "refuse", "error"]
# A node's host class as host rule 3 measures it, and the plan's word for one never measured.
HostClass = Literal["light", "heavy", "gpu"]
# The fields a run record takes from its duration record, which the same `Run` measured.
FROM_DURATION = ("started_at", "seconds", "load_1m", "phases", "settings")


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
    edition: str
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
    """One whole run of a node."""

    inputs: dict[str, State]


class PartialRecord(Common):
    """A run of part of a node, or of another place or size than its own."""

    partial: Literal[True] = True


class Folder(NamedTuple):
    """A folder input or output: its path and the pattern that names its members."""

    path: Path
    pattern: str


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


def stated(path: Path | Folder, known: State | None = None) -> State:
    """A file or a folder as it stands, digests taken from `known` where they still hold."""
    if isinstance(path, Folder):
        return folder_state(path, known if isinstance(known, FolderState) else None)
    return state(path, known if isinstance(known, FileState) else None)


def engine(pins: dict[str, str]) -> Engine:
    """The running engine: its version, its `released.json` digest and the pins given."""
    return Engine(version=released.version(), released_sha256=digest(released.RECORD), pins=pins)


def place(node: str, code: str, *, partial: bool = False) -> Path:
    """Where a node's record of an edition stands, or its partial record."""
    name = f"{node}.partial.json" if partial else f"{node}.json"
    return Path(repository.ROOT) / FOLDER / code / name


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
    """The file or folder a record states, below the film's root."""
    return Path(repository.ROOT) / recorded.path


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
    path = at(recorded)
    now = stated(Folder(path, recorded.pattern) if isinstance(recorded, FolderState) else path)
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
