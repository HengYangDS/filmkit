"""The node table: each command of an edition's build chain as a node, as data, with the edges
derived from the paths it reads and writes and the order from the standard library's `graphlib`.

A node is one of today's chain commands for one edition (design decision 1 of record-every-run),
named as its duration record names it. Each of its ways states its inputs as a function of an
edition that returns paths by name, and its outputs likewise; a folder names its members by a
pattern (`records.Folder`). Where an owner binds its inputs, the node takes that owner's
function (design decision 4); every node reads the film's declaration, which every command
loads, and binds it whole.

A path that several nodes write is declared in `SHARED` with each writer and its kind: one that
`rewrites` it after the writers it names, or one that `replaces` it whole (design decision 5).
The edges follow: a node that reads a path comes after each node that writes it, a rewriter
after the writers it names, and replacers of one path have no edge between them. Loading a
table refuses a cycle, naming its nodes, a path that two nodes write with no declaration,
naming the path and the nodes, and a node whose places bind one name to two places, naming the
name: a union of `Places` refuses it, so that no place is lost under another's name.
"""

from __future__ import annotations

import graphlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import filmkit.delivery.packaging as packaging
import filmkit.picture.derivation as derivation
import filmkit.picture.equivalence as equivalence
import filmkit.picture.gates as picture_gates
import filmkit.picture.rendering as rendering
import filmkit.picture.still_scan as still_scan
import filmkit.preflight as preflight
import filmkit.repository as repository
import filmkit.soundtrack.gates as sound_gates
from filmkit.film import FILM
from filmkit.graph.records import Folder, HostClass
from filmkit.narration.narrate import evidence_paths
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

# The kinds of a writer of a path that several nodes write (design decision 5).
REWRITES, REPLACES = "rewrites", "replaces"
# The tools whose reads the check of each run's opens sees only through their arguments.
MEDIA, BROWSER = ("FFmpeg", "ffprobe"), ("Chrome",)


@dataclass(frozen=True)
class Node:
    """One command of an edition's build chain: its ways, each with its inputs, its outputs,
    the host class it is expected to measure at, and whether it is model work. A node of several
    ways takes `default_way` where no run says which; `tools` names the tools it starts whose
    reads are seen only through their arguments."""

    name: str
    ways: dict[str, Callable[[Edition], Places]]
    outputs: Callable[[Edition], Places]
    expected: HostClass
    gpu: bool = False
    default_way: Callable[[Edition], str] | None = None
    tools: tuple[str, ...] = ()

    def way(self, edition: Edition, recorded: object = None) -> str:
        """The way a run took, or else the way the node takes by default."""
        if isinstance(recorded, str) and recorded in self.ways:
            return recorded
        return self.default_way(edition) if self.default_way else next(iter(self.ways))

    def inputs(self, edition: Edition, way: object = None) -> Places:
        """The inputs of a way, by default the node's own."""
        return self.ways[self.way(edition, way)](edition)


class Writer(NamedTuple):
    """A node that writes a path several nodes write, its kind, and for a rewriter the writers
    it follows."""

    node: str
    kind: str
    after: tuple[str, ...] = ()


class TableError(ValueError):
    """A node table that cannot be ordered, leaves a writer undeclared or binds one name of a
    node's places to two places."""


class Places(dict[str, "Path | Folder"]):
    """A node's places by name; a union that binds one name to two places is refused."""

    def __or__(self, other: dict) -> Places:
        return Places(joined(self, other))

    def __ror__(self, other: dict) -> Places:
        return Places(joined(other, self))

    def __ior__(self, other: dict) -> Places:  # type: ignore[override]
        self.update(joined(self, other))
        return self


def joined(first: dict, second: dict) -> dict:
    """Two sets of places in one, refused where a name stands for two places."""
    clash = sorted(n for n in first.keys() & second.keys() if place(first[n]) != place(second[n]))
    if clash:
        raise TableError(f"a node's places bind {', '.join(clash)} to two places each")
    return {**first, **second}


def key(node: str, code: str) -> str:
    """A node of one edition, as the plan names it: `<node>:<code>`."""
    return f"{node}:{code}"


def place(path: Path | Folder) -> Path:
    """The file or folder a declared path names, resolved."""
    return Path(path.path if isinstance(path, Folder) else path).resolve()


def overlaps(a: Path, b: Path) -> bool:
    """Whether two resolved places name one file or one holds the other, compared by their names
    (`Path.is_relative_to` compares them part by part, many times slower)."""
    first, second = f"{a}{os.sep}", f"{b}{os.sep}"
    return first.startswith(second) or second.startswith(first)


@dataclass(frozen=True)
class Table:
    """A loaded table: its nodes by name, its declared writers by output name, its editions,
    each node's predecessors by key and the derived order."""

    nodes: dict[str, Node]
    shared: dict[str, tuple[Writer, ...]]
    codes: tuple[str, ...]
    edges: dict[str, frozenset[str]]
    order: tuple[str, ...]

    def node(self, named: str) -> tuple[Node, Edition]:
        """A node of an edition by its key."""
        name, code = named.rsplit(":", 1)
        return self.nodes[name], Edition(code)

    def upstream(self, named: str) -> set[str]:
        """Every node before one, transitively."""
        found, pending = set(), list(self.edges[named])
        while pending:
            before = pending.pop()
            if before not in found:
                found.add(before)
                pending.extend(self.edges[before])
        return found


def written(nodes: dict[str, Node], codes: Iterable[str]) -> dict[Path, list[tuple[str, str]]]:
    """Each output path of every node of every edition, with the keys and output names that
    write it."""
    found: dict[Path, list[tuple[str, str]]] = {}
    for code in codes:
        for node in nodes.values():
            for name, path in node.outputs(Edition(code)).items():
                found.setdefault(place(path), []).append((key(node.name, code), name))
    return found


def undeclared(paths: dict[Path, list[tuple[str, str]]], shared: dict) -> list[str]:
    """Each path two nodes write that `shared` does not declare with exactly those writers."""
    refused = []
    for path, by in paths.items():
        if len(by) < 2:
            continue
        names = {name for _, name in by}
        nodes = sorted({named.rsplit(":", 1)[0] for named, _ in by})
        declared = len(names) == 1 and {w.node for w in shared.get(next(iter(names)), ())}
        if declared != set(nodes):
            keys = ", ".join(sorted(named for named, _ in by))
            refused.append(f"{repository.relative(path)} is written by {keys} with no declaration")
    return refused


def follows(writer: str, output: str, other: str, shared: dict) -> bool:
    """Whether a declared rewriter of an output comes after another node: one it names."""
    return any(w.node == writer and other in w.after for w in shared.get(output, ()))


def edges(nodes: dict[str, Node], shared: dict, codes: tuple[str, ...]) -> dict[str, set[str]]:
    """Each node's predecessors: the writers of each path it reads, but a rewriter that names
    the reader among those it follows, and for a rewriter the nodes it names; replacers of one
    path have no edge between them."""
    paths = written(nodes, codes)
    before: dict[str, set[str]] = {key(n, c): set() for c in codes for n in nodes}
    for code in codes:
        for node in nodes.values():
            reader, edition = key(node.name, code), Edition(code)
            reads = {place(p) for way in node.ways.values() for p in way(edition).values()}
            for out, by in paths.items():
                if not any(overlaps(read, out) for read in reads):
                    continue
                for named, output in by:
                    writer = named.rsplit(":", 1)[0]
                    if writer == node.name or follows(writer, output, node.name, shared):
                        continue
                    before[reader].add(named)
    for by in paths.values():
        for named, output in by:
            name, code = named.rsplit(":", 1)
            for writer in shared.get(output, ()):
                if writer.node == name and writer.kind == REWRITES:
                    before[named].update(
                        key(after, code) for after in writer.after if after in nodes
                    )
    return before


def load(nodes: Iterable[Node], shared: dict, codes: tuple[str, ...] = CODES) -> Table:
    """Load a table: refused for a path two nodes write with no declaration, naming it and its
    writers, and for a cycle, naming its nodes."""
    named = {node.name: node for node in nodes}
    refused = undeclared(written(named, codes), shared)
    if refused:
        raise TableError("; ".join(refused))
    before = edges(named, shared, codes)
    sorter = graphlib.TopologicalSorter(before)
    try:
        order = tuple(sorter.static_order())
    except graphlib.CycleError as error:
        cycle = " -> ".join(error.args[1])
        raise TableError(f"the node table has a cycle: {cycle}") from None
    frozen = {name: frozenset(found) for name, found in before.items()}
    return Table(named, dict(shared), tuple(codes), frozen, order)


# The chain's nodes. Each function of an edition returns paths by name.


def root(path: str | Path) -> Path:
    """A path below the film's root, as the root stands when the table is read."""
    return repository.ROOT / path


def named(bindings: dict[str, Path]) -> Places:
    """An owner's binding list by the names its record keys them under, less `_sha256`."""
    return Places({name.removesuffix("_sha256"): path for name, path in bindings.items()})


def declared(edition: Edition) -> Places:
    """What every command reads: the film's declaration, which it loads."""
    del edition
    return Places({"declaration": root(repository.DECLARATION)})


def sources(edition: Edition) -> Places:
    """The edition's tracked sources that its narration reads; its readings where it has them."""
    places = edition.places
    found = Places(
        script=root(edition.script),
        cast=root(edition.cast),
        pronunciation=root(places.pronunciation),
        reference=root(places.reference),
    )
    return found | ({"readings": root(places.readings)} if root(places.readings).is_file() else {})


def checked_words(edition: Edition) -> Places:
    """What the checks of words read: the source manifest, the concepts, every script and the
    composition's sources (`filmkit.concepts`, `filmkit.register`)."""
    del edition
    found = Places(
        source_manifest=root(FILM.source_manifest),
        composition_sources=Folder(root("picture"), "**/*"),
    )
    found |= {f"script_{code}": root(Edition(code).script) for code in CODES}
    return found | ({"concepts": root(FILM.concepts)} if FILM.concepts else {})


def narration(edition: Edition) -> Places:
    """The edition's narration: its takes, their receipt, alignment and transcript."""
    paths = evidence_paths(edition.code)
    return Places(
        recordings=Folder(root(paths["folder"]), "**/*"),
        receipt=root(paths["receipt"]),
        alignment=root(paths["alignment"]),
        asr=root(paths["asr"]),
    )


def documents(edition: Edition) -> Places:
    """What the assembly writes and the caption refresh writes again."""
    return Places(
        soundtrack=edition.soundtrack,
        timeline=edition.timeline,
        assembly=edition.audio_assembly,
        srt=edition.srt,
        vtt=edition.vtt,
        chapters=edition.chapters,
        transcript=edition.transcript,
        chapter_metadata=edition.chapter_metadata,
    )


def faces() -> Places:
    """The stylesheet and the declared fonts, each by its path."""
    return Places({f"face {name}": path for name, path in rendering.face_places().items()})


def staging(edition: Edition) -> Places:
    """What a stage is made from: the stage record's inputs, the composition, the template and
    the faces."""
    found = {name: root(path) for name, path in rendering.stage_places(edition).items()}
    found |= {
        "composition": root(rendering.COMPOSITION_SCRIPT),
        "template": root(rendering.TEMPLATE),
    }
    return declared(edition) | found | faces()


def stage(edition: Edition, captions: bool = True) -> Places:
    """A picture's stage, as a folder."""
    return Places({"stage": Folder(edition.rendered(captions).stage, "**/*")})


def rendered(edition: Edition, captions: bool = True) -> Places:
    """A picture and its receipt."""
    picture = edition.rendered(captions)
    return Places({"picture": picture.file, "receipt": picture.receipt})


def staged_picture(edition: Edition, captions: bool = True) -> Places:
    """What a render or a validation of a staged picture reads: the stage and its sources."""
    return staging(edition) | stage(edition, captions)


def derived_uncaptioned(edition: Edition) -> bool:
    """Whether the edition's uncaptioned picture, as its receipt stands, was derived."""
    receipt = edition.rendered(captions=False).receipt
    return receipt.is_file() and isinstance(repository.read(receipt).get("derived"), dict)


def uncaptioned_way(edition: Edition) -> str:
    """The way the uncaptioned picture takes without `--native`: `derived` or `native`."""
    try:
        way = derivation.uncaptioned_way(edition)["way"]
    except (OSError, ValueError, KeyError):
        way = "rendered"
    return "derived" if way == "derived" else "native"


def derived_from(edition: Edition) -> Places:
    """What the derived uncaptioned picture is made from: the captioned picture and receipt,
    the composition and the timeline."""
    found = {f"captioned_{name}": path for name, path in rendered(edition).items()}
    found |= {"composition": root(rendering.COMPOSITION_SCRIPT), "timeline": edition.timeline}
    return declared(edition) | found


def compared(edition: Edition) -> Places:
    """What the comparison of the two pictures reads: the equivalence's list and both pictures,
    with the stage of each picture that was rendered."""
    found = declared(edition) | named(equivalence.bound_inputs(edition)) | staged_picture(edition)
    for captions, side in ((True, "captioned"), (False, "uncaptioned")):
        found |= {f"{side}_{name}": path for name, path in rendered(edition, captions).items()}
    if not derived_uncaptioned(edition):
        found |= {"uncaptioned_stage": stage(edition, captions=False)["stage"]}
    return found


def metadata_inputs(edition: Edition) -> Places:
    """What the viewing package and the entry page are made from."""
    found = Places(
        cover=root(edition.cover),
        version=root(packaging.VERSION),
        script=root(edition.script),
        composition=root(rendering.COMPOSITION_SCRIPT),
        entry_source=root(FILM.entry),
    )
    kept = ("srt", "vtt", "chapters", "transcript", "chapter_metadata")
    found |= {name: path for name, path in documents(edition).items() if name in kept}
    found |= {f"timeline_{code}": Edition(code).timeline for code in CODES}
    return declared(edition) | found


def metadata(edition: Edition) -> Places:
    """The viewing package's own files and the entry page, which every edition replaces."""
    output = edition.artifacts
    return Places(
        cover_png=output / packaging.COVER_PNG,
        cover_jpg=output / packaging.COVER_JPEG,
        player=output / packaging.PAGE,
        shot_plan=edition.shot_plan,
        viewing_package=edition.viewing_package,
        entry=repository.ROOT / packaging.LANGUAGE_INDEX,
    )


def packaged(edition: Edition) -> Places:
    """What the films are made from: their inputs (`packaging.film_inputs`, each name marked
    `film_`) but the cover the packaging writes itself, both pictures' validations, and the
    viewing package's inputs."""
    bound = named(packaging.film_inputs(edition)).items()
    films = {f"film_{k}": p for k, p in bound if k != "cover"}
    return compared(edition) | metadata_inputs(edition) | films


def readiness(edition: Edition) -> Places:
    """What the pre-render check reads: its receipt's own list and the records and stages it
    judges."""
    found = preflight.shared_places() | faces() | preflight.own_places(edition)
    found |= stage(edition) | {"uncaptioned_stage": stage(edition, captions=False)["stage"]}
    found |= {
        "picture_gates": edition.picture_gates,
        "sound_gates": edition.sound_gates,
        "picture_geometry": edition.picture_geometry,
        "cover": root(edition.cover),
    }
    found |= {"draft_stills": edition.draft_stills} if FILM.picture.drafts else {}
    return checked_words(edition) | found


def only(name: str, path: Callable[[Edition], Path | Folder]) -> Callable[[Edition], Places]:
    """A node's outputs that are one file or folder."""
    return lambda edition: Places({name: path(edition)})


def work(name: str) -> Callable[[Edition], Path]:
    """A file or folder below the work folder, named for the edition."""
    return lambda edition: root("build/runtime/work") / name.format(code=edition.code)


TABLE = (
    Node(
        "narrate",
        {"default": lambda e: declared(e) | sources(e) | checked_words(e)},
        narration,
        "gpu",
        gpu=True,
    ),
    Node(
        "select",
        {"default": lambda e: declared(e) | sources(e) | narration(e)},
        lambda e: {
            "narration_selected": e.narration_selected,
            "alignment_selected": e.alignment_selected,
        },
        "light",
    ),
    Node(
        "assemble",
        {
            "default": lambda e: (
                declared(e)
                | {k: v for k, v in sources(e).items() if k in ("script", "cast")}
                | {
                    "narration_selected": e.narration_selected,
                    "alignment_selected": e.alignment_selected,
                }
                | {"recordings": narration(e)["recordings"]}
            )
        },
        documents,
        "light",
        tools=MEDIA,
    ),
    Node(
        "refresh-captions",
        {
            "default": lambda e: (
                declared(e)
                | {
                    "script": root(e.script),
                    "cast": root(e.cast),
                    "narration_selected": e.narration_selected,
                }
                | {
                    k: v
                    for k, v in documents(e).items()
                    if k in ("timeline", "assembly", "soundtrack")
                }
            )
        },
        lambda e: (
            {k: v for k, v in documents(e).items() if k != "soundtrack"}
            | {"narration_selected": e.narration_selected}
        ),
        "light",
    ),
    Node(
        "check-sound",
        {
            "default": lambda e: (
                declared(e)
                | named(sound_gates.bound_inputs(e))
                | {k: v for k, v in narration(e).items() if k in ("recordings", "receipt")}
            )
        },
        only("sound_gates", lambda e: e.sound_gates),
        "light",
        tools=MEDIA,
    ),
    Node("stage-picture", {"default": staging}, stage, "light"),
    Node(
        "stage-picture-uncaptioned",
        {"default": staging},
        lambda e: stage(e, captions=False),
        "light",
    ),
    Node(
        "geometry-check",
        {"default": lambda e: declared(e) | stage(e)},
        only("picture_geometry", lambda e: e.picture_geometry),
        "heavy",
        tools=BROWSER,
    ),
    Node(
        "player-check-cover",
        {"default": lambda e: declared(e) | stage(e) | {"cover": root(e.cover)}},
        only("painted_cover", work("cover-{code}.png")),
        "light",
        tools=BROWSER,
    ),
    Node(
        "check-picture",
        {"default": lambda e: declared(e) | named(picture_gates.bound_inputs(e)) | faces()},
        lambda e: {
            "picture_gates": e.picture_gates,
            "reports": Folder(work("picture-gates/{code}")(e), "*"),
        },
        "heavy",
    ),
    Node(
        "render-draft",
        {"default": staging},
        lambda e: {
            "draft_stage": Folder(e.draft_stage, "**/*"),
            "draft_picture": e.draft_picture,
            "draft_receipt": e.draft_receipt,
            "draft_stills": e.draft_stills,
        },
        "heavy",
        tools=MEDIA,
    ),
    Node(
        "preflight",
        {"default": lambda e: declared(e) | readiness(e)},
        lambda e: {
            "readiness": e.readiness,
            "cover_check": Folder(work("preflight/{code}")(e), "*"),
        },
        "light",
        tools=BROWSER,
    ),
    Node(
        "render-picture",
        {"default": lambda e: staged_picture(e) | {"picture_gates": e.picture_gates}},
        rendered,
        "heavy",
        tools=MEDIA,
    ),
    Node(
        "render-picture-uncaptioned",
        {
            "native": lambda e: (
                staged_picture(e, captions=False) | {"picture_gates": e.picture_gates}
            ),
            "derived": derived_from,
        },
        lambda e: rendered(e, captions=False),
        "heavy",
        default_way=uncaptioned_way,
        tools=MEDIA,
    ),
    Node(
        "validate-picture",
        {"default": lambda e: staged_picture(e) | rendered(e)},
        lambda e: {},
        "light",
        tools=MEDIA,
    ),
    Node(
        "validate-picture-uncaptioned",
        {
            "native": lambda e: staged_picture(e, captions=False) | rendered(e, captions=False),
            "derived": lambda e: derived_from(e) | staged_picture(e) | rendered(e, captions=False),
        },
        lambda e: {},
        "light",
        default_way=lambda e: "derived" if derived_uncaptioned(e) else "native",
        tools=MEDIA,
    ),
    Node(
        "qualify-renderer",
        {"default": lambda e: staged_picture(e) | rendered(e)},
        only("renderer_qualification", lambda e: e.renderer_qualification),
        "heavy",
        tools=MEDIA,
    ),
    Node(
        "compare-pictures",
        {"default": compared},
        only("caption_equivalence", lambda e: e.caption_equivalence),
        "heavy",
        tools=MEDIA,
    ),
    Node("package-metadata", {"default": metadata_inputs}, metadata, "light"),
    Node(
        "package-film",
        {"default": packaged},
        lambda e: (
            {f"film_{kind}": e.film(kind) for kind in packaging.RENDITIONS}
            | {"film_package": e.film_package}
            | metadata(e)
        ),
        "heavy",
        tools=(*MEDIA, "ExifTool"),
    ),
    Node(
        "scan-film",
        {"default": lambda e: declared(e) | still_scan.subject_places(e)},
        only("film_stills", lambda e: e.film_stills),
        "heavy",
        tools=MEDIA,
    ),
)

# The paths that several nodes write, by the name each writer gives the output, with each
# writer's kind (design decision 5; build/evidence/record-every-run/research.md).
_DOCUMENTS = (Writer("assemble", REPLACES), Writer("refresh-captions", REPLACES))
_PACKAGE = (Writer("package-metadata", REPLACES), Writer("package-film", REPLACES))
SHARED = {
    "timeline": (Writer("assemble", REPLACES), Writer("refresh-captions", REWRITES, ("assemble",))),
    "assembly": (Writer("assemble", REPLACES), Writer("refresh-captions", REWRITES, ("assemble",))),
    "narration_selected": (
        Writer("select", REPLACES),
        Writer("refresh-captions", REWRITES, ("select", "assemble")),
    ),
    **dict.fromkeys(("srt", "vtt", "chapters", "transcript", "chapter_metadata"), _DOCUMENTS),
    **dict.fromkeys(
        ("cover_png", "cover_jpg", "player", "shot_plan", "viewing_package", "entry"), _PACKAGE
    ),
}
# Reads a node makes that are no input of it, each with its reason: a read of a later node's
# output, which as an input would close a cycle (build/evidence/record-every-run/research.md).
# The check of each run's opens allows them and reports each as an exemption.
ASIDE: dict[str, tuple[str, Callable[[Edition], Places]]] = {
    "preflight": (
        "it asks whether an earlier film package record would refuse the next packaging",
        lambda e: {"film_package": e.film_package},
    ),
    "package-metadata": (
        "the player page states the sizes of the films that package-film writes",
        lambda e: {f"film_{kind}": e.film(kind) for kind in packaging.RENDITIONS},
    ),
}


def aside(name: str, edition: Edition) -> Places:
    """The reads a node makes that are no input of it (`ASIDE`)."""
    return ASIDE[name][1](edition) if name in ASIDE else {}


# The commands that write a duration record and are no node, each with its reason (design
# decisions 1 and 8).
NOT_NODES = {
    "fit": "it reports pause-policy variants and derives nothing a later step reads",
    "admitted": "it reads the readiness receipts and derives nothing",
    "repair-pictures": "it redoes the renders and comparisons of other nodes and runs as them",
    "converge": "a search that writes the cast, a tracked source; its narrations are whole runs",
    "verify": "it judges the whole build and derives nothing a later step reads",
    "reproduce": "it judges a rebuild against the release record and derives nothing",
    "narrate-checks": "a run of part of narrate, which writes narrate's partial record",
}


def chain() -> Table:
    """The engine's table over the film's editions."""
    return load(TABLE, SHARED, CODES)
