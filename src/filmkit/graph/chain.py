"""The engine's node table: each command of an edition's build chain as a node, its inputs and
outputs as functions of an edition, the paths that several of them write, and the reads each
makes aside (design decisions 1, 4 and 5 of record-every-run; `filmkit.graph.nodes` loads it).

Where an owner binds its inputs, the node takes that owner's function (design decision 4). Every
node reads the film's declaration, which every command loads, and binds each top-level table of it
that the node may read, by the table's digest (design decision 12 of build-a-film-by-its-verbs):
every table, but the narration's for the nodes that make and deliver the pictures.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import filmkit.check as source_check
import filmkit.delivery.packaging as packaging
import filmkit.film as film
import filmkit.picture.derivation as derivation
import filmkit.picture.draft as draft
import filmkit.picture.equivalence as equivalence
import filmkit.picture.gates as picture_gates
import filmkit.picture.qualification as qualification
import filmkit.picture.renderer as renderer
import filmkit.picture.rendering as rendering
import filmkit.picture.still_scan as still_scan
import filmkit.repository as repository
import filmkit.soundtrack.assembly as assembly
import filmkit.soundtrack.gates as sound_gates
import filmkit.tools as tools
from filmkit.captions import refresh
from filmkit.film import FILM
from filmkit.graph.nodes import (
    EVERY,
    REPLACES,
    REWRITES,
    Node,
    Places,
    Table,
    Wait,
    Writer,
    load,
    stands,
)
from filmkit.graph.nodes import FILM as ONCE
from filmkit.graph.records import DeclarationTable, Folder, table_names
from filmkit.narration import alignment_records, readings, selection, transcript_records
from filmkit.narration.narrate import evidence_paths
from filmkit.production import CODES, Edition
from filmkit.review import set_aside

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# The tools whose reads the check of each run's opens sees only through their arguments.
MEDIA, BROWSER = ("FFmpeg", "ffprobe"), ("Chrome",)
# The geometry check's step, which every film's task line passed (design decision 14).
GEOMETRY_STEP = "2"
# The declaration's tables, each bound by its digest.
TABLES = tuple(dict.fromkeys(table_names(film.Film).values()))
# The tables no node that makes or delivers the pictures reads: no module of `filmkit.picture` or
# `filmkit.delivery` reaches a reader of the narration's table (`narration.audition`,
# `judgment`, `readings` and `selection`, `review.listening_plan` and `measurement`,
# `soundtrack.assembly`; read 2026-11-25), so a hearing recorded there leaves them fresh; the
# check of each run's opens holds each node to it.
PICTURED = tuple(t for t in TABLES if t != "narration")
# The tables the narration reads: the film's identity and editions and the pronunciation that
# the editions share (`narration.synthesis`, `narration.pronunciation`), so that an edit of the
# composition, of another edition's script or of the narration's table leaves it fresh (design
# decision 9).
NARRATED = ("identity", "editions", "pronunciation")


def root(path: str | Path) -> Path:
    """A path below the film's root, as the root stands when the table is read."""
    return repository.ROOT / path


def named(bindings: dict[str, Path]) -> Places:
    """An owner's binding list by the names its record keys them under, less `_sha256`."""
    return Places({name.removesuffix("_sha256"): path for name, path in bindings.items()})


def declared(edition: Edition | None, tables: tuple[str, ...] = TABLES) -> Places:
    """What every command reads: the film's declaration, which it loads, as the tables it may read,
    every one by default."""
    del edition
    path = root(repository.DECLARATION)
    return Places({f"declaration.{t}": DeclarationTable(path, t) for t in tables})


def pictured(edition: Edition | None) -> Places:
    """What a node that makes or delivers the pictures reads of the declaration (`PICTURED`)."""
    return declared(edition, PICTURED)


def sources(edition: Edition) -> Places:
    """The edition's tracked sources that its narration reads; its readings where it has them
    (`nodes.stands`)."""
    places = edition.places
    found = Places(
        script=root(edition.script),
        cast=root(edition.cast),
        pronunciation=root(places.pronunciation),
        reference=root(places.reference),
    )
    return found | ({"readings": root(places.readings)} if stands(root(places.readings)) else {})


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


def checked(edition: None) -> Places:
    """What the source check reads (`filmkit.check`): the declaration whole, which the loader
    reads, the words of every edition and its pronunciation and readings, the picture's sources
    with its template, the entry page and the review prompt, and the film's npm and Python
    manifests and locks."""
    del edition
    found = checked_words(None) | {"declaration": root(repository.DECLARATION)}
    for code in CODES:
        places = Edition(code).places
        found |= {f"cast_{code}": root(places.cast)}
        found |= {f"pronunciation_{code}": root(places.pronunciation)}
        if stands(root(places.readings)):
            found |= {f"readings_{code}": root(places.readings)}
    found |= {"entry": root(FILM.entry), "prompt": root(FILM.review.prompt)}
    pins = ("package.json", "package-lock.json", "pyproject.toml", "uv.lock")
    return found | {name: root(name) for name in pins if stands(root(name))}


def check_outputs(edition: None) -> Places:
    """The source check's verdict and each edition's occurrence plan."""
    del edition
    found = Places(verdict=root(source_check.VERDICT))
    return found | {f"plan_{code}": root(readings.plan_path(code)) for code in CODES}


def narration(edition: Edition) -> Places:
    """The edition's narration: its takes, their receipt, alignment and transcript."""
    paths = evidence_paths(edition.code)
    return Places(
        recordings=Folder(root(paths["folder"]), "**/*"),
        receipt=root(paths["receipt"]),
        alignment=root(paths["alignment"]),
        asr=root(paths["asr"]),
    )


def caches(edition: Edition) -> Places:
    """The narration's caches, which each narration reads and adds to: each recording's alignment
    and transcript, under the recording and the model that made it, in a folder for each
    language. Its outputs, not its inputs: a run reads them as they stood and leaves them grown,
    and a read of a node's own output is allowed."""
    language = edition.language.lower()
    return Places(
        alignments=Folder(root(alignment_records.CACHE) / language, "*"),
        transcripts=Folder(root(transcript_records.CACHE) / language, "*"),
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
    return pictured(edition) | found | faces()


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
    """Whether the edition's uncaptioned picture, as its receipt stands, was derived, by the
    owner's rule (`derivation.is_derived`). A receipt that is missing or cannot be read is no
    derived picture's, as `uncaptioned_way` takes one, so that the table loads and the owner's
    own check refuses the receipt (design decision 5)."""
    try:
        found = repository.read(edition.rendered(captions=False).receipt)
    except (OSError, ValueError):
        return False
    return isinstance(found, dict) and derivation.is_derived(found)


def native(edition: Edition) -> bool:
    """Whether the film renders the edition's uncaptioned picture from its own stage
    (`[picture] native_uncaptioned`)."""
    return edition.code in FILM.picture.native_uncaptioned


def uncaptioned_way(edition: Edition) -> str:
    """The way the uncaptioned picture takes: `derived` or `native`."""
    try:
        way = derivation.uncaptioned_way(edition, native=native(edition))["way"]
    except (OSError, ValueError, KeyError):
        way = "rendered"
    return "derived" if way == "derived" else "native"


def derived_from(edition: Edition) -> Places:
    """What the derived uncaptioned picture is made from: the captioned picture and receipt,
    the composition and the timeline, and what the validation of the captioned picture reads
    first (`derivation.derive_uncaptioned` calls `rendering.validate_picture`): its stage and the
    stage's sources."""
    found = {f"captioned_{name}": path for name, path in rendered(edition).items()}
    found |= {"composition": root(rendering.COMPOSITION_SCRIPT), "timeline": edition.timeline}
    return pictured(edition) | found | staged_picture(edition)


def compared(edition: Edition) -> Places:
    """What the comparison of the two pictures reads: the equivalence's list and both pictures,
    with the stage of each picture that was rendered."""
    found = pictured(edition) | named(equivalence.bound_inputs(edition)) | staged_picture(edition)
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
    return pictured(edition) | found


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


def ran(tool: str, arguments: list[str]) -> None:
    """Run one of the engine's Node tools as a node's owner, refused where it exits with another
    status than 0."""
    status = tools.run(tool, arguments)
    if status != 0:
        message = f"{tool} exited with status {status}"
        raise tools.ToolError(message)


def geometry_check(edition: Edition) -> None:
    """Check the geometry of the edition's staged picture at the engine's step, gating the gaps
    between rows where the film declares it (`[picture] gate_row_gaps`)."""
    stage_folder = repository.relative(edition.rendered().stage)
    arguments = [stage_folder, repository.relative(edition.picture_geometry), GEOMETRY_STEP]
    gaps = ["--gate-row-gaps"] if FILM.picture.gate_row_gaps else []
    ran("geometry-check", [*arguments, *gaps])


def cover_check(edition: Edition) -> None:
    """Paint the cover the edition's composition draws and compare it with the tracked cover."""
    painting = repository.relative(work("cover-{code}.png")(edition))
    stage_folder = repository.relative(edition.rendered().stage)
    ran("player-check", ["cover", stage_folder, str(edition.cover), painting])


def staged(edition: Edition, captions: bool) -> object:
    """Stage one of the edition's pictures whole: at the picture's size, from 0 to its runtime."""
    width, height = rendering.PICTURE_SIZE
    return rendering.stage_picture(
        edition, None, edition.runtime, width, height, 0, captions=captions
    )


def render_uncaptioned(edition: Edition) -> object:
    """Make the uncaptioned picture: derived from the captioned one where its way is derived,
    rendered from its own stage otherwise, and always where the film declares it native."""
    asked = native(edition)
    if derivation.uncaptioned_way(edition, native=asked)["way"] == "derived":
        return derivation.derive_uncaptioned(edition, derivation.DEADLINE)
    return derivation.render_uncaptioned(edition, renderer.DEADLINE, asked=asked)


def only(name: str, path: Callable[[Edition], Path | Folder]) -> Callable[[Edition], Places]:
    """A node's outputs that are one file or folder."""
    return lambda edition: Places({name: path(edition)})


def work(name: str) -> Callable[[Edition], Path]:
    """A file or folder below the work folder, named for the edition."""
    return lambda edition: root("build/runtime/work") / name.format(code=edition.code)


# The gates a render and a package wait for (design decision 4 of build-a-film-by-its-verbs):
# their own edition's sound gate, with the owner's hearing, and cover check; and, for a render,
# every edition's picture gate, geometry check and draft, since every edition renders one
# composition. A wait orders and gates; it binds none of the gate's bytes, and a wait on a node
# the table lacks, as on the draft of a film that declares none, is dropped when it loads.
SOUNDED = (Wait("check-sound"), Wait("player-check-cover"))
RENDERED = (
    *SOUNDED,
    Wait("check-picture", EVERY),
    Wait("geometry-check", EVERY),
    Wait("render-draft", EVERY),
)
# Every heavy or GPU node waits for the film's source check.
CHECKED = Wait("check")


TABLE = (
    Node(
        "check",
        {"default": checked},
        check_outputs,
        "light",
        per=ONCE,
        run=lambda _: source_check.run(),
    ),
    Node(
        "narrate",
        {"default": lambda e: declared(e, NARRATED) | sources(e)},
        lambda e: narration(e) | caches(e),
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
        run=lambda e: selection.select(e),
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
        run=lambda e: set_aside.after_set_aside(e, assembly.assemble),
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
        run=lambda e: set_aside.after_set_aside(e, refresh.refresh_captions),
    ),
    Node(
        "check-sound",
        {
            "default": lambda e: (
                declared(e)
                | named(sound_gates.bound_inputs(e))
                | {k: v for k, v in narration(e).items() if k in ("recordings", "receipt")}
                | {"narration_selected": e.narration_selected}
            )
        },
        only("sound_gates", lambda e: e.sound_gates),
        "light",
        tools=MEDIA,
        run=lambda e: sound_gates.check_sound(e),
    ),
    Node(
        "stage-picture",
        {"default": staging},
        stage,
        "light",
        run=lambda e: staged(e, captions=True),
    ),
    Node(
        "stage-picture-uncaptioned",
        {"default": staging},
        lambda e: stage(e, captions=False),
        "light",
        run=lambda e: staged(e, captions=False),
    ),
    Node(
        "geometry-check",
        {"default": lambda e: pictured(e) | stage(e)},
        only("picture_geometry", lambda e: e.picture_geometry),
        "heavy",
        tools=BROWSER,
        run=geometry_check,
    ),
    Node(
        "player-check-cover",
        {"default": lambda e: pictured(e) | stage(e) | {"cover": root(e.cover)}},
        only("painted_cover", work("cover-{code}.png")),
        "light",
        tools=BROWSER,
        run=cover_check,
    ),
    Node(
        "check-picture",
        {"default": lambda e: pictured(e) | named(picture_gates.bound_inputs(e)) | faces()},
        lambda e: {
            "picture_gates": e.picture_gates,
            "reports": Folder(work("picture-gates/{code}")(e), "*"),
        },
        "heavy",
        run=lambda e: picture_gates.check_picture(e),
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
        # Only a film that declares drafts renders them (`[picture] drafts`).
        editions=lambda codes: codes if FILM.picture.drafts else (),
        run=lambda e: draft.render_draft(e, draft.DEADLINE),
    ),
    Node(
        "render-picture",
        {"default": lambda e: staged_picture(e) | {"picture_gates": e.picture_gates}},
        rendered,
        "heavy",
        tools=MEDIA,
        run=lambda e: rendering.render_picture(e, renderer.DEADLINE, captions=True),
        waits=RENDERED,
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
        run=render_uncaptioned,
        waits=RENDERED,
    ),
    Node(
        "validate-picture",
        {"default": lambda e: staged_picture(e) | rendered(e)},
        lambda e: {},
        "light",
        tools=MEDIA,
        run=lambda e: rendering.validate_picture(e, captions=True),
    ),
    Node(
        "validate-picture-uncaptioned",
        {
            "native": lambda e: staged_picture(e, captions=False) | rendered(e, captions=False),
            "derived": lambda e: derived_from(e) | rendered(e, captions=False),
        },
        lambda e: {},
        "light",
        default_way=lambda e: "derived" if derived_uncaptioned(e) else "native",
        tools=MEDIA,
        run=lambda e: rendering.validate_picture(e, captions=False),
    ),
    Node(
        "qualify-renderer",
        {"default": lambda e: staged_picture(e) | rendered(e)},
        only("renderer_qualification", lambda e: e.renderer_qualification),
        "heavy",
        tools=MEDIA,
        # Once a build, on the edition the film qualifies (`film.qualified_edition`): every engine
        # release qualifies the canvas build it pins (`picture/qualification.py`).
        editions=lambda codes: tuple(c for c in codes if c == film.qualified_edition(FILM)),
        run=lambda e: qualification.qualify_renderer(e, renderer.DEADLINE),
    ),
    Node(
        "compare-pictures",
        {"default": compared},
        only("caption_equivalence", lambda e: e.caption_equivalence),
        "heavy",
        tools=MEDIA,
        run=lambda e: equivalence.compare_pictures(e),
    ),
    Node(
        "package-metadata",
        {"default": metadata_inputs},
        metadata,
        "light",
        run=lambda e: packaging.package_metadata(e),
    ),
    Node(
        "package-film",
        {"default": packaged},
        lambda e: (
            {f"film_{kind}": e.film(kind) for kind in packaging.RENDITIONS}
            | {"film_package": e.film_package}
            | {"packaging_failure": e.evidence / packaging.FAILURE_RECEIPT}
            | metadata(e)
        ),
        "heavy",
        tools=(*MEDIA, "ExifTool"),
        run=lambda e: packaging.package_film(e),
        waits=SOUNDED,
    ),
    Node(
        "scan-film",
        {"default": lambda e: pictured(e) | still_scan.subject_places(e)},
        only("film_stills", lambda e: e.film_stills),
        "heavy",
        tools=MEDIA,
        run=lambda e: still_scan.scan_film(e),
    ),
)
# The rule of `CHECKED`, stated once over the table.
TABLE = tuple(
    replace(node, waits=(*node.waits, CHECKED)) if node.expected in ("heavy", "gpu") else node
    for node in TABLE
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
    "package-metadata": (
        "the player page states the sizes of the films that package-film writes",
        lambda e: {f"film_{kind}": e.film(kind) for kind in packaging.RENDITIONS},
    ),
}


def aside(name: str, edition: Edition) -> Places:
    """The reads a node makes that are no input of it (`ASIDE`)."""
    return ASIDE[name][1](edition) if name in ASIDE else {}


# The commands the seam measures that are no node, each with its reason (design decisions 1 and 8
# of record-every-run).
NOT_NODES = {
    "fit": "it reports pause-policy variants and derives nothing a later step reads",
    "admitted": "it reads the readiness receipts and derives nothing",
    "preflight": "the waits and the plan's readiness replace it; it leaves with produce",
    "repair-pictures": "it redoes the renders and comparisons of other nodes and runs as them",
    "converge": "a search that writes the cast, a tracked source; its narrations are whole runs",
    "verify": "it judges the whole build and derives nothing a later step reads",
    "reproduce": "it judges a rebuild against the release record and derives nothing",
}


def table() -> Table:
    """The engine's table over the film's editions."""
    return load(TABLE, SHARED, CODES)
