"""The engine's node table: each command of an edition's build chain as a node, by what it binds
(`filmkit.graph.bindings`), its run, the gates it waits for and the host class it is expected
to measure at; the paths that several nodes write, the reads each makes aside, and the groups a
target may name (design decisions 1, 4 and 5 of record-every-run; `filmkit.graph.nodes` loads
it). The runs of the nodes that no owner's function runs are here: the engine's tools run with
the arguments the films' task lines passed, a whole stage and the uncaptioned picture's way.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import filmkit.check as source_check
import filmkit.delivery.packaging as packaging
import filmkit.delivery.verification as verification
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
from filmkit.graph import build_command, key
from filmkit.graph.bindings import (
    ASSEMBLED,
    LOADED,
    NARRATED,
    SELECTED,
    caches,
    check_outputs,
    checked,
    compared,
    declared,
    derived_from,
    derived_uncaptioned,
    documents,
    faces,
    gated,
    metadata,
    metadata_inputs,
    named,
    narration,
    native,
    only,
    packaged,
    pictured,
    rendered,
    root,
    sources,
    stage,
    staged_picture,
    staging,
    uncaptioned_way,
    work,
)
from filmkit.graph.nodes import EVERY, REPLACES, REWRITES, Node, Places, Table, Wait, Writer, load
from filmkit.graph.nodes import FILM as ONCE
from filmkit.graph.records import Folder
from filmkit.narration import selection
from filmkit.production import CODES, Edition
from filmkit.review import set_aside

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# The tools whose reads the check of each run's opens sees only through their arguments.
MEDIA, BROWSER = ("FFmpeg", "ffprobe"), ("Chrome",)
# The geometry check's step, which every film's task line passed (design decision 14).
GEOMETRY_STEP = "2"


def ran(tool: str, arguments: list[str]) -> None:
    """Run one of the engine's Node tools as a node's owner, refused where it exits with another
    status than 0."""
    status = tools.run(tool, arguments)
    if status != 0:
        message = f"{tool} exited with status {status}"
        raise tools.ToolError(message)


def geometry_check(edition: Edition) -> None:
    """Check the geometry of the edition's staged picture at the engine's step, gating the gaps
    between rows where the film declares it (`[picture] gate_row_gaps`), and refuse a record
    that does not cover the whole current staged film, as the delivery's verification will
    (`verification.geometry_gaps`), naming the record, what it lacks and the stage to make
    whole."""
    record = repository.relative(edition.picture_geometry)
    stage_folder = repository.relative(edition.rendered().stage)
    rows = ["--gate-row-gaps"] if FILM.picture.gate_row_gaps else []
    ran("geometry-check", [stage_folder, record, GEOMETRY_STEP, *rows])
    try:
        lacks = verification.geometry_gaps(edition, repository.read(edition.picture_geometry))
    except (OSError, ValueError):
        lacks = ["it cannot be read"]
    if lacks:
        message = (
            f"{record} does not cover the current staged film: {'; '.join(lacks)}; stage the "
            "whole picture and check it again, "
            + build_command(key(name, edition.code) for name in ("stage-picture", "geometry-check"))
        )
        raise tools.ToolError(message)


def cover_refusal(status: int, report: Path, cover: str, painting: Path) -> str | None:
    """Why a tracked cover is not the one the composition paints, by the cover check's exit status
    and report, naming the painting to track; None where the two are identical."""
    try:
        found = repository.read(report)
    except (OSError, ValueError):
        return f"the cover check exited with status {status} and no report"
    if status == 0 and found.get("identical"):
        return None
    painted = repository.relative(painting)
    if found.get("cover_sha256") is None:
        return f"no tracked cover at {cover}; track the painting {painted}"
    if found.get("differing_pixels") is None:
        return f"{cover} is not the size of the painting {painted}"
    return (
        f"{cover} differs in {found['differing_pixels']} pixels from the cover the composition "
        f"paints; track the painting {painted}"
    )


def cover_check(edition: Edition) -> None:
    """Paint the cover the edition's composition draws and compare it with the tracked cover,
    refusing a tracked cover other than the painting (`cover_refusal`)."""
    painting, report = work("cover-{code}.png")(edition), work("cover-{code}.json")(edition)
    stage_folder = repository.relative(edition.rendered().stage)
    arguments = ["cover", stage_folder, str(edition.cover), repository.relative(painting)]
    refused = cover_refusal(
        tools.run("player-check", arguments, stdout=report), report, edition.cover, painting
    )
    if refused:
        raise tools.ToolError(refused)


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
        {"default": lambda e: declared(e, SELECTED) | sources(e) | narration(e)},
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
                declared(e, ASSEMBLED)
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
                declared(e, LOADED)
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
                gated(e)
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
        {"default": lambda e: declared(e, LOADED) | stage(e) | {"cover": root(e.cover)}},
        lambda e: {
            "painted_cover": work("cover-{code}.png")(e),
            "cover": work("cover-{code}.json")(e),
        },
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
        {"default": lambda e: declared(e, LOADED) | still_scan.subject_places(e)},
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
    "repair-pictures": "it redoes the renders and comparisons of other nodes and runs as them",
    "converge": "a search that writes the cast, a tracked source; its narrations are whole runs",
    "verify": "it judges the whole build and derives nothing a later step reads",
    "reproduce": "it judges a rebuild against the release record and derives nothing",
}


# The derivation's nodes as groups of the table's nodes, which a target may name (design decision
# 2 of build-a-film-by-its-verbs); `narrate` is its own, and the target `all` holds every node but
# it, which `filmkit narrate` runs.
GROUPS = {
    "sound": ("select", "assemble", "refresh-captions", "check-sound"),
    "audit": (
        "stage-picture",
        "stage-picture-uncaptioned",
        "geometry-check",
        "player-check-cover",
        "check-picture",
        "render-draft",
    ),
    "picture": (
        "render-picture",
        "render-picture-uncaptioned",
        "validate-picture",
        "validate-picture-uncaptioned",
        "qualify-renderer",
        "compare-pictures",
    ),
    "package": ("package-metadata", "package-film", "scan-film"),
}
NOT_IN_ALL = ("narrate",)


def table() -> Table:
    """The engine's table over the film's editions."""
    return load(TABLE, SHARED, CODES, GROUPS)
