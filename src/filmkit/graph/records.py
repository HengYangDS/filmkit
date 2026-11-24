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

import hashlib
import json
from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError

import filmkit.released as released
import filmkit.repository as repository

# The schema this engine writes and reads; a record of any other is unreadable.
SCHEMA = 1
# The folder of the run records below the film's root, a folder for each edition by its code.
FOLDER = Path("build/evidence/records/editions")
# How a run ended: its owner passed, its owner refused with one line, or it failed otherwise.
Outcome = Literal["pass", "refuse", "error"]
# A node's host class as host rule 3 measures it, and the plan's word for one never measured.
HostClass = Literal["light", "heavy", "gpu"]


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
        sha256=known.sha256 if same and known else digest(path),
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
