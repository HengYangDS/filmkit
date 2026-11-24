"""What each run of a node opens, recorded, and checked against the node table (design decision 4
of record-every-run).

When `FILMKIT_OPENS` names a file, `filmkit/__init__.py` installs the recorder in every engine
Python process (`install`), and the engine starts Node with its recorder (`node_options`). It is
off by default, and a run is the same either way: Python's audit hook only appends, and Node's
permission audit refuses nothing. Each entry is one JSON line: the node whose run was open
(`FILMKIT_NODE`, which a node's run sets and every child inherits), the process, the kind and the
path. Python records, below the film's root, each `open` with whether it writes, an open for
reading of a path that does not stand as a `probe`, each `os.rename` (which `os.replace` raises)
with its source marked, each hard link, each removal, and each `subprocess.Popen` with the paths
in its arguments and environment that exist; a read made while the engine starts, as an engine
module loads or the film loader (`filmkit.film.read`) runs, is a `load`. What the recorder and
the seam read themselves, such as the node table's places, they read with the hook quiet
(`quiet`). Node records each file access outside its allowances on the channel
`node:permission-model:fs` (`opens.cjs`): reads of the node's inputs and outputs,
`build/runtime/`, the engine's package and the film's packages, writes of its outputs and
`build/runtime/`, so every other access below the root is in the log. Network use and paths
outside the root are judged by nothing.

`check` compares a log with the table: it fails a read outside the inputs and outputs of the way
a node's run took, a probe of a path that the node would not declare were it to stand, and a
write outside its outputs, names each node whose tools are seen only through their arguments,
and reports each exemption with its reason and the nodes it covered. It fails closed: nothing
below the root is let through without a declaration or a named exemption, and a read at start-up
by another path than the two the recorder knows is judged as a read.
"""

from __future__ import annotations

import contextlib
import fnmatch
import json
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

# The variable that names the log, and the one that names the open run, `<node>:<code>`.
VARIABLE, NODE = "FILMKIT_OPENS", "FILMKIT_NODE"
# The recorder Node loads, beside this module, and the engine's package, which Node may read.
RECORDER = Path(__file__).with_name("opens.cjs")
PACKAGE = Path(__file__).resolve().parents[1]
# The folder of bounded work and tool copies below the film's root (design decision 4).
RUNTIME = Path("build/runtime")
# The bits of an `open` event's flags that write.
WRITING = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
# The kinds of entry that write, and what a finding says each did.
WRITES = ("write", "rename", "link", "remove")
DID = {
    "write": "wrote",
    "rename": "wrote",
    "link": "linked",
    "remove": "removed",
    "probe": "looked for",
}
# What a path below the root may be read or written without a declaration, each with its reason.
EXEMPT = {
    "environment": "the Python environment and the npm packages, which the lock files supply",
    "records": "the run records and the duration records, which the run itself writes",
    "work": "bounded work and tool copies below build/runtime/, which no node declares",
    "resolution": "the package.json files that Node's module resolution looks up",
    "log": "the recorder's own log",
    "start-up": "what every engine process reads as it starts, before a command's run opens: "
    "the film loader's validation of the files the declaration names, and the film-wide values "
    "the engine's modules derive as they load; the node binds the declaration whole",
}
_installed = threading.Event()
_inside = threading.local()


def label() -> str:
    """The node whose run is open, `<node>:<code>`, or nothing."""
    return os.environ.get(NODE, "")


def absolute(path: object, cwd: str | None = None) -> str:
    """A path as a process names it, absolute from its working directory, links unresolved."""
    return os.path.normpath(os.path.join(cwd or os.getcwd(), os.fsdecode(path)))


def _root() -> tuple[str, ...]:
    """The film's root as the engine names it and as it resolves, once `filmkit.repository` is
    imported; nothing before, when no engine code has found the film."""
    repository = sys.modules.get("filmkit.repository")
    root = getattr(repository, "ROOT", None)
    if root is None:
        return ()
    return tuple(dict.fromkeys((str(root), os.path.realpath(root))))


def _below(path: str, tops: tuple[str, ...]) -> bool:
    return any(path.startswith(top + os.sep) for top in tops)


def _starting() -> bool:
    """Whether the engine is starting on this thread: an engine module's body runs as it is
    imported, or the film loader, `filmkit.film.read`, runs."""
    loader = getattr(sys.modules.get("filmkit.film"), "read", None)
    code = getattr(loader, "__code__", None)
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code is code or (
            frame.f_code.co_name == "<module>"
            and str(frame.f_globals.get("__name__", "")).startswith("filmkit.")
        ):
            return True
        frame = frame.f_back
    return False


def _note(event: str, args: tuple, write) -> None:
    """Turn one audit event into entries: an open, a probe, a rename, a link, a removal or a
    child; a read or probe made while the engine starts is a load."""
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        flags, path = (args[2] if isinstance(args[2], int) else 0), absolute(args[0])
        if flags & WRITING:
            write("write", path)
        else:
            write("load" if _starting() else "read" if os.path.lexists(path) else "probe", path)
    elif event == "os.rename":
        write("source", absolute(args[0]))
        write("rename", absolute(args[1]))
    elif event == "os.link":
        write("read", absolute(args[0]))
        write("link", absolute(args[1]))
    elif event in ("os.remove", "shutil.rmtree"):
        write("remove", absolute(args[0]))
    elif event == "subprocess.Popen":
        _, command, cwd, environment = args
        words = [command] if isinstance(command, (str, bytes, os.PathLike)) else list(command)
        folder = None if cwd is None else os.fsdecode(cwd)
        for word in [*words, *(environment or {}).values()]:
            if isinstance(word, (str, bytes, os.PathLike)):
                named = absolute(word, folder)
                if os.path.lexists(named):
                    write("argument", named)


@contextlib.contextmanager
def quiet():
    """Hold the hook quiet while the block runs: what the recorder and the seam read themselves
    is no access of the run."""
    was = getattr(_inside, "busy", False)
    _inside.busy = True
    try:
        yield
    finally:
        _inside.busy = was


def install() -> None:
    """Record this process's opens in the file `FILMKIT_OPENS` names, where one is named; once."""
    name = os.environ.get(VARIABLE)
    if not name or _installed.is_set():
        return
    _installed.set()
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

    def hook(event: str, args: tuple) -> None:
        # Only while a node's run is open; never into itself, and never raising into the engine.
        if not label() or getattr(_inside, "busy", False):
            return
        _inside.busy = True
        try:
            tops = _root()

            def write(kind: str, path: str) -> None:
                if not _below(path, tops):
                    return
                line = {
                    "node": label(),
                    "process": Path(sys.argv[0] or "python").name,
                    "pid": os.getpid(),
                    "kind": kind,
                    "path": path,
                }
                os.write(descriptor, (json.dumps(line) + "\n").encode())

            if tops:
                _note(event, args, write)
        except (OSError, ValueError, TypeError, IndexError):
            return
        finally:
            _inside.busy = False

    sys.addaudithook(hook)


def node_options() -> dict[str, str]:
    """What starts a Node process so that its run is recorded, for the node whose run is open,
    or nothing where the log is off or no run is open: `--permission-audit`, its allowances,
    and the recorder by `--require`, in `NODE_OPTIONS`, so that every Node child inherits them."""
    log = os.environ.get(VARIABLE)
    if not log or not label():
        return {}
    import filmkit.repository as repository

    with quiet():
        reads, writes = declared(label())
    runtime = repository.ROOT / RUNTIME
    with contextlib.suppress(repository.FilmRootError):
        reads.append(repository.node_modules())
    allowed_reads = _both([PACKAGE, runtime, Path(log), *reads])
    options = ["--permission-audit", *(f"--allow-fs-read={path}" for path in allowed_reads)]
    options += [f"--allow-fs-write={path}" for path in _both([runtime, Path(log), *writes])]
    options += ["--require", str(RECORDER)]
    quoted = ['"' + o.replace("\\", "\\\\").replace('"', '\\"') + '"' for o in options]
    return {"NODE_OPTIONS": " ".join(filter(None, [os.environ.get("NODE_OPTIONS"), *quoted]))}


def declared(named: str) -> tuple[list[Path], list[Path]]:
    """The places a node may read, its inputs of every way and its outputs, and those it may
    write, its outputs; nothing for a label that names no node of the table."""
    from filmkit.graph import chain

    try:
        node, edition = chain.table().node(named)
    except (KeyError, ValueError):
        return [], []
    inputs = [place(path) for way in node.ways.values() for path in way(edition).values()]
    outputs = [place(path) for path in node.outputs(edition).values()]
    return [*inputs, *outputs], outputs


def place(path: object) -> Path:
    """The file or folder a declared place names."""
    return Path(getattr(path, "path", path))


def _both(paths: Iterable[Path]) -> list[str]:
    """Each path as it is named and as it resolves, once each."""
    return list(dict.fromkeys(str(form) for path in paths for form in (path, path.resolve())))


@dataclass(frozen=True)
class Access:
    """One entry of the log: the node whose run was open, the process, the kind and the path."""

    node: str
    process: str
    pid: int
    kind: str
    path: Path


@dataclass
class Report:
    """What the check found: each read or write outside a node's declaration; each exemption,
    by its reason, with the nodes it covered; the nodes whose tools are seen only through their
    arguments; the nodes that ran; and the labels that name no node of the table."""

    findings: list[str] = field(default_factory=list)
    exempted: dict[str, set[str]] = field(default_factory=dict)
    unseen: dict[str, tuple[str, ...]] = field(default_factory=dict)
    seen: set[str] = field(default_factory=set)
    unjudged: set[str] = field(default_factory=set)

    @property
    def ok(self) -> bool:
        """Whether nothing was read or written outside a declaration and every label was a node."""
        return not self.findings and not self.unjudged


def accesses(log: Path) -> list[Access]:
    """The log's entries; a line that is no entry of the recorder is refused by its number."""
    found = []
    for number, line in enumerate(log.read_text(encoding="utf-8").splitlines(), 1):
        try:
            value = json.loads(line)
            named = Path(value["path"])
            path = named if named.is_absolute() else Path(value["cwd"]) / named
            found.append(Access(value["node"], value["process"], value["pid"], value["kind"], path))
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError(
                f"line {number} of {log} is no entry of the recorder: {error}"
            ) from None
    return found


def covered(path: Path, places: Iterable[tuple[Path, str | None]]) -> bool:
    """Whether a real path is a declared place, or a member of a declared folder, the members
    being the ones its pattern names."""
    for real, pattern in places:
        if path == real:
            return True
        if pattern is None or not path.is_relative_to(real):
            continue
        name = path.relative_to(real).as_posix()
        if pattern.startswith("**/") and name or "/" not in name and fnmatch.fnmatch(name, pattern):
            return True
    return False


class _Judged:
    """One node of the table as the check compares a log with it: what it may read and write,
    what it may look for and not find, what it reads aside, and every place any node of its
    edition declares."""

    def __init__(self, table, named: str) -> None:
        from filmkit.graph import chain, nodes, records

        self.node, self.edition = table.node(named)
        way = None
        with contextlib.suppress(records.Unreadable, FileNotFoundError):
            way = records.read(records.place(self.node.name, self.edition.code)).settings.get("way")
        inputs = list(self.node.inputs(self.edition, way).values())
        outputs = list(self.node.outputs(self.edition).values())
        self.reads, self.writes = real([*inputs, *outputs]), real(outputs)
        with nodes.as_if_standing():
            self.probes = real(self.node.inputs(self.edition, way).values())
        self.aside = real(chain.aside(self.node.name, self.edition).values())
        everything = [
            item
            for each in table.nodes.values()
            for way in each.ways.values()
            for item in [*way(self.edition).values(), *each.outputs(self.edition).values()]
        ]
        self.declared = real(everything)


def real(places: Iterable[object]) -> list[tuple[Path, str | None]]:
    """Each declared place by its real path and, for a folder, its pattern."""
    return [
        (Path(os.path.realpath(place(item))), getattr(item, "pattern", None)) for item in places
    ]


def exemption(path: Path, kind: str, judged: _Judged, log: Path) -> str:
    """The exemption that a real path no declaration names falls under, `outside` for one
    outside the root, or nothing."""
    import filmkit.repository as repository

    root = Path(os.path.realpath(repository.ROOT))
    if not path.is_relative_to(root):
        return "outside"
    relative = path.relative_to(root)
    if path == Path(os.path.realpath(log)):
        return "log"
    if "node_modules" in relative.parts or any(
        (folder / "pyvenv.cfg").is_file()
        for folder in (path, *path.parents)
        if folder.is_relative_to(root)
    ):
        return "environment"
    if (
        relative.parts[:3] == ("build", "evidence", "records")
        or "durations" in relative.parts[-2:-1]
    ):
        return "records"
    if relative.is_relative_to(RUNTIME) and not covered(path, judged.declared):
        return "work"
    if kind in ("read", "argument") and path.name == "package.json":
        return "resolution"
    return ""


def check(log: Path, table=None) -> Report:
    """A log compared with the table, the engine's by default: each read outside a node's inputs
    of the way its record states, or of its default way, and outputs, and each write outside its
    outputs; a `.partial` sibling renamed over its target is no write, the target is."""
    import filmkit.repository as repository
    from filmkit.graph import chain

    table = table or chain.table()
    report, judged = Report(), {}
    found = accesses(log)
    renamed = {(a.pid, a.path) for a in found if a.kind == "source"}
    for access in found:
        if access.node not in table.edges:
            if access.node:
                report.unjudged.add(access.node)
            continue
        if access.node not in judged:
            judged[access.node] = _Judged(table, access.node)
        judging = judged[access.node]
        report.seen.add(access.node)
        if judging.node.tools:
            report.unseen[access.node] = judging.node.tools
        if access.kind == "source" or (
            access.kind == "write" and (access.pid, access.path) in renamed
        ):
            continue
        path, writes = Path(os.path.realpath(access.path)), access.kind in WRITES
        if covered(path, judging.writes if writes else judging.reads):
            continue
        if access.kind == "probe" and covered(path, judging.probes):
            continue
        if not writes and covered(path, judging.aside):
            reason = f"aside: {chain.ASIDE[judging.node.name][0]}"
            report.exempted.setdefault(reason, set()).add(access.node)
            continue
        reason = "start-up" if access.kind == "load" else exemption(path, access.kind, judging, log)
        if reason == "outside":
            continue
        if reason:
            report.exempted.setdefault(f"{reason}: {EXEMPT[reason]}", set()).add(access.node)
            continue
        report.findings.append(
            f"{access.node}: {access.process} (pid {access.pid}) "
            f"{DID.get(access.kind, 'read')} {repository.relative(access.path)}, which "
            f"{'its outputs do' if writes else 'its declaration does'} not name"
        )
    return report
