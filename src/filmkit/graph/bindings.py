"""What each node of the engine's table binds, as functions of an edition: the film's sources and
the build's outputs it reads and writes by name, and the tables of the declaration its run reads,
each by its digest and no other (design decision 12 of build-a-film-by-its-verbs).
`filmkit.graph.chain` states the nodes over them.

Where an owner binds its inputs, the node takes that owner's function (design decision 4 of
record-every-run).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import filmkit.check as source_check
import filmkit.delivery.packaging as packaging
import filmkit.picture.derivation as derivation
import filmkit.picture.equivalence as equivalence
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.graph.nodes import Places, stands
from filmkit.graph.records import DeclarationTable, Folder
from filmkit.narration import alignment_records, readings, transcript_records
from filmkit.narration.narrate import evidence_paths
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# The tables of the declaration each node's run reads, each bound by its digest, and no other
# (design decision 12 of build-a-film-by-its-verbs). The check of each run's opens holds every
# node the light suite runs to its tables both ways (`opens.Report.unread`); the others are read
# from their owners' code (2026-11-25). Every run reads the film's identity, by the file prefix
# that every place takes (`production.Edition`), and its editions, which every engine process
# derives as it loads (`production.CODES`). No node reads the release's sources, which
# `filmkit release` reads (decision 15).
LOADED = ("identity", "editions")
# The narration's: the pronunciation the editions share (`narration.synthesis`,
# `narration.pronunciation`), so that an edit of the composition, of another edition's script or
# of the narration's table leaves it fresh (design decision 9).
NARRATED = (*LOADED, "pronunciation")
# The selection's: the pronunciation each recording is held to and the narration's flow and terms
# (`narration.selection`).
SELECTED = (*NARRATED, "narration")
# The assembly's: the narration's flow and terms, which the assembled speech is held to
# (`soundtrack.assembly`).
ASSEMBLED = (*LOADED, "narration")
# The sound gate's: the reading rate's exceptions and the clarity floors, line and exceptions
# (`soundtrack.gates`, `review.clarity`); the owner's hearings besides where it reads them
# (`gated`).
GATED = (*LOADED, "captions", "review")
# A stage's, a picture's and its checks': the fonts and the picture's exceptions and switches
# (`picture.rendering`, `picture.gates`, `picture.derivation`, `chain.geometry_check`).
PICTURED = (*LOADED, "picture")
# The player page's: its colours (`delivery.player`).
PLAYED = (*LOADED, "player")


def root(path: str | Path) -> Path:
    """A path below the film's root, as the root stands when the table is read."""
    return repository.ROOT / path


def named(bindings: dict[str, Path]) -> Places:
    """An owner's binding list by the names its record keys them under, less `_sha256`."""
    return Places({name.removesuffix("_sha256"): path for name, path in bindings.items()})


def declared(edition: Edition | None, tables: tuple[str, ...]) -> Places:
    """What a node reads of the film's declaration, which every command loads: the tables its run
    reads."""
    del edition
    path = root(repository.DECLARATION)
    return Places({f"declaration.{t}": DeclarationTable(path, t) for t in tables})


def gated(edition: Edition) -> Places:
    """What the sound gate reads of the declaration (`GATED`), with the narration's table, the
    owner's hearings, where the film declares `review.clarity_thought_margin_db`: only a gate that
    holds each thought to its line reads them (`soundtrack.gates.thought_findings`)."""
    heard = ("narration",) if FILM.review.clarity_thought_margin_db is not None else ()
    return declared(edition, (*GATED, *heard))


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
    return declared(edition, PLAYED) | found


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


def only(name: str, path: Callable[[Edition], Path | Folder]) -> Callable[[Edition], Places]:
    """A node's outputs that are one file or folder."""
    return lambda edition: Places({name: path(edition)})


def work(name: str) -> Callable[[Edition], Path]:
    """A file or folder below the work folder, named for the edition."""
    return lambda edition: root("build/runtime/work") / name.format(code=edition.code)
