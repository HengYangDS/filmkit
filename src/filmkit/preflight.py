"""Check, before an expensive render, every input the render and the next packaging bind.

`preflight` answers whether an edition is ready for its first render. It reports at once every
stale or missing input of the edition, each by the owner that would refuse it later, and refuses
with `PreflightError` while any remains:

- the stages: the complete current UHD pictures that `render-picture` renders, the captioned one
  and the uncaptioned one (`filmkit.picture.rendering.require_current_stage`);
- the cover: the edition's tracked cover identical to the cover the staged composition paints,
  as `filmkit.tools player-check cover` compares them, the painting written below
  build/runtime/work/preflight/<code>/;
- the film package: an earlier package record, which `package-film` would refuse to extend once
  the render replaces the picture it binds, with the fields the current inputs no longer match
  (`filmkit.delivery.packaging.stale_bindings`); set its films aside first
  (`filmkit.review.round set-aside`);
- the draft, for a film that declares drafts (`picture.drafts`): the still scan of the edition's
  10 fps draft (`Edition.draft_stills`), which must exist, list no still run at the limit and
  bind the current timeline and composition; an early warning, since the scan of the film
  itself decides once it is packaged (`filmkit.picture.still_scan.scan_film`);
- the concepts: the film's words against its concept contract (`filmkit.concepts.check`);
- the register: the film's words against the formal register (`filmkit.register.check`);
- the picture gate: a passing gate record bound to the current composition, timeline,
  stylesheet, fonts and engine (`filmkit.picture.rendering.require_passing_gates`);
- the sound gate: a passing record of `check-sound` bound to the current soundtrack, timeline
  and engine;
- the thoughts under the clarity floor, for a film that declares the line a single thought is
  judged against (`review.clarity_thought_margin_db`): none under that line, which with a
  margin of zero is the floor, and each between the line and the floor declared by its name
  (`review.clarity_exceptions`), but a thought whose selected take the owner heard clear
  (`narration.heard`, its lines naming `clarity`) and the assembled soundtrack holds (the
  assembly record's `source_sha256` of its segment is the selected recording's, else "run
  assemble"); each it refuses is named for the owner's ear with its selected take's audio
  SHA-256, where the selection bound one;
- the caption cues above the edition's reading rate, each declared by its text
  (`captions.rate_exceptions`);
- the geometry: the record that the delivery's verification requires, passed on the whole
  current staged film (`filmkit.delivery.verification.require_covering_geometry`).

A declared thought or cue that no longer stands under its line is refused as stale.

The answer is written as the edition's readiness receipt (`Edition.readiness`): the verdict, each
question's answer, the engine version and the SHA-256 of every input the answer was judged on,
the declaration, which holds the film's register exceptions, and the entry page among them.
`admitted` reads receipts without repeating the work: it refuses unless the edition's receipt
passed and each input it bound still holds, and unless every other edition's receipt passed on the
composition, stylesheet, fonts, declaration and entry page as they stand, since every edition
renders one composition and a finding in any changes it for all.

Usage: python -m filmkit.produce preflight --language <code>
       python -m filmkit.produce admitted --language <code>
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.concepts as concepts
import filmkit.delivery.packaging as packaging
import filmkit.delivery.verification as verification
import filmkit.picture.renderer as renderer
import filmkit.picture.rendering as rendering
import filmkit.picture.still_scan as still_scan
import filmkit.register as register
import filmkit.released as released
import filmkit.repository as repository
import filmkit.review.clarity as review_clarity
import filmkit.soundtrack.gates as sound_gates
import filmkit.sources as sources
import filmkit.tools as tools
from filmkit.film import FILM
from filmkit.narration import anchors
from filmkit.production import CODES, Edition

if TYPE_CHECKING:
    from collections.abc import Callable

# The cover paintings, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/preflight")
CURRENT = "current"
# What the report says of a draft scan that the film does not declare.
NO_DRAFTS = "not asked: the film declares no drafts"
# What it says of thoughts under the clarity floor when the film declares no line for them.
NO_THOUGHT_LINE = review_clarity.NO_THOUGHT_LINE


class PreflightError(ValueError):
    """An input of the render or of the packaging after it is stale or missing."""


def missing(error: FileNotFoundError) -> str:
    """A missing input, as the check names it."""
    return f"missing {repository.relative(Path(error.filename))}"


def stage(edition: Edition, *, captions: bool = True) -> str | None:
    """Whether the stage of the captioned picture, or of the uncaptioned one, is current."""
    rendered = edition.rendered(captions)
    try:
        rendering.require_current_stage(edition, rendered.stage, captions=captions)
    except rendering.PictureError as error:
        return f"{error}; run stage-picture" + ("" if captions else " --uncaptioned")
    except FileNotFoundError as error:
        return missing(error)
    return None


def cover(edition: Edition) -> str | None:
    """Whether the tracked cover is the one the current stage's composition paints."""
    work = repository.ROOT / WORK / edition.code
    work.mkdir(parents=True, exist_ok=True)
    painting, result = work / "cover.png", work / "cover.json"
    arguments = ["cover", str(edition.picture_stage), edition.cover, str(painting)]
    try:
        status = tools.run("player-check", arguments, stdout=result)
    except (rendering.PictureError, tools.ToolError) as error:
        return f"not compared: {error}"
    try:
        report = json.loads(result.read_text())
    except ValueError:
        return f"the cover check exited with status {status} and no report"
    if status == 0 and report.get("identical"):
        return None
    painted = repository.relative(painting)
    if report.get("cover_sha256") is None:
        return f"no tracked cover at {edition.cover}; track the painting {painted}"
    if report.get("differing_pixels") is None:
        return f"{edition.cover} is not the size of the painting {painted}"
    return (
        f"{edition.cover} differs in {report['differing_pixels']} pixels from the cover the "
        f"composition paints; track the painting {painted}"
    )


def package(edition: Edition) -> str | None:
    """Whether an earlier film package record would refuse the packaging after this render."""
    if not edition.film_package.is_file():
        return None
    record = repository.relative(edition.film_package)
    stale = packaging.stale_bindings(edition, repository.read(edition.film_package))
    binds = f"binds other {', '.join(stale)}" if stale else "binds the picture the render replaces"
    return f"{record} {binds}; set its films aside first"


def draft(edition: Edition) -> str | None:
    """Whether the draft's still scan passed on the current timeline and composition, on a
    draft that the engine's renderer drew. The record is read by the reader of the film's
    record (`still_scan.draft_record`): one that cannot be read, binds another timeline or
    composition, states other rules than the engine's, did not read the whole draft or
    contradicts itself admits no render."""
    path, named = edition.draft_stills, repository.relative(edition.draft_stills)
    if not path.is_file():
        return f"no still scan of the 10 fps draft at {named}"
    try:
        record = still_scan.draft_record(edition)
    except FileNotFoundError as error:
        return missing(error)
    except rendering.PictureError as error:
        return str(error)
    except still_scan.NoAnswerError as error:
        return f"{named} {error}; scan a new draft"
    draws = {
        "package": renderer.RENDERER_NAME,
        "version": renderer.RENDERER_VERSION,
        "text_renderer": renderer.TEXT_RENDERER,
    }
    if record.get("drawn_by") != draws:
        return f"{named} scanned a draft that another renderer drew; render the draft again"
    held = len(still_scan.over_limit(record))
    return f"{named} finds {held} still pictures with {still_scan.limit_words()}" if held else None


def words(check: Callable[[], object], *refusals: type[Exception]) -> str | None:
    """Whether a check of the film's words passes: its refusals on one line, or what it misses."""
    try:
        check()
    except refusals as error:
        # A register refusal counts its refusals apart from its advice on keeping a word.
        lines = (
            error.lines if isinstance(error, register.RegisterError) else str(error).splitlines()
        )
        return "; ".join(lines)
    except FileNotFoundError as error:
        return missing(error)
    return None


def gates(edition: Edition) -> str | None:
    try:
        rendering.require_passing_gates(edition)
    except rendering.PictureError as error:
        return str(error)
    except FileNotFoundError as error:
        return missing(error)
    return None


def sound(edition: Edition) -> str | None:
    """Whether check-sound passed the edition's current inputs, those its record binds
    (`filmkit.soundtrack.gates.bound_inputs`)."""
    path, named = edition.sound_gates, repository.relative(edition.sound_gates)
    if not path.is_file():
        return f"no sound gate record at {named}; run check-sound"
    record = repository.read(path)
    try:
        current = sound_gates.bindings(edition)
    except FileNotFoundError as error:
        return missing(error)
    stale = [key for key, value in current.items() if record.get(key) != value]
    if stale:
        return f"{named} binds another {', '.join(stale)}; run check-sound"
    if record.get("verdict") != "pass":
        return f"{named} did not pass; run check-sound"
    return None


def clarity(edition: Edition) -> str | None:
    """Whether each thought under the clarity floor is one the film declares, above its line, or
    one the owner heard clear (`sound_gates.thought_findings`, which the sound gate asks)."""
    if FILM.review.clarity_thought_margin_db is None:
        return NO_THOUGHT_LINE
    if not edition.sound_gates.is_file():
        return "not judged: no sound gate record"
    measured = repository.read(edition.sound_gates)["clarity"]
    return "; ".join(sound_gates.thought_findings(edition, measured)) or None


def caption_rate(edition: Edition) -> str | None:
    """Whether each cue above the edition's reading rate is one the film declares by its text
    (`sound_gates.rate_findings`, which the sound gate asks)."""
    try:
        cues = repository.read(edition.timeline)["captions"]
    except FileNotFoundError as error:
        return missing(error)
    return "; ".join(sound_gates.rate_findings(edition, cues)) or None


def geometry(edition: Edition) -> str | None:
    """Whether the geometry record passed on the whole current staged film, as the delivery's
    verification will require it."""
    try:
        verification.require_covering_geometry(edition)
    except verification.VerificationError as error:
        named = repository.relative(edition.picture_geometry)
        return f"{error} ({named}); run filmkit.tools geometry-check on the stage"
    except FileNotFoundError as error:
        return missing(error)
    return None


def shared_places() -> dict[str, Path]:
    """The inputs every edition shares besides the faces (`rendering.face_places`), by name."""
    root = repository.ROOT
    return {
        "composition": root / rendering.COMPOSITION_SCRIPT,
        "declaration": root / repository.DECLARATION,
        "entry": root / FILM.entry,
    }


def own_places(edition: Edition) -> dict[str, Path]:
    """The edition's own inputs of its readiness, by name."""
    root = repository.ROOT
    return {
        "script": root / edition.script,
        "cast": root / edition.cast,
        "timeline": edition.timeline,
        "assembly": edition.audio_assembly,
        "soundtrack": edition.soundtrack,
    }


def shared_inputs() -> dict:
    """The SHA-256 of the inputs every edition shares, by name: a receipt of any binds them."""
    faces = rendering.face_bindings()
    digests = {name: repository.sha(path) for name, path in shared_places().items()}
    return {
        "composition": digests["composition"],
        "stylesheet": faces["stylesheet_sha256"],
        "fonts": faces["fonts_sha256"],
        "declaration": digests["declaration"],
        "entry": digests["entry"],
    }


def bound_inputs(edition: Edition) -> dict:
    """The SHA-256 of every input an edition's readiness is judged on, by its name: the inputs
    every edition shares, then the edition's own."""
    own = {name: repository.sha(path) for name, path in own_places(edition).items()}
    return {**shared_inputs(), **own}


def preflight(edition: Edition) -> dict:
    """Report each input of the edition's render as current or stale, write the edition's
    readiness receipt and refuse a stale input.

    The cover is painted from the stage, so it is compared only once the stage is current. A
    question the film does not ask (`NO_DRAFTS`, `NO_THOUGHT_LINE`) is reported and refuses
    nothing. A missing input leaves the receipt without digests, and is refused by name. A
    script that breaks an anchor's rule is refused before anything is written
    (`filmkit.narration.anchors`).
    """
    if (repository.ROOT / edition.script).is_file():
        anchors.require(repository.read(edition.script), edition.code)
    staged = stage(edition)
    found = {
        "stage": staged,
        "uncaptioned_stage": stage(edition, captions=False),
        "picture_gate": gates(edition),
        "sound_gate": sound(edition),
        "thought_clarity": clarity(edition),
        "caption_rate": caption_rate(edition),
        "geometry": geometry(edition),
        "draft_stills": draft(edition) if FILM.picture.drafts else NO_DRAFTS,
        "concepts": words(concepts.check, concepts.ConceptError, sources.SourceError),
        "register": words(register.check, register.RegisterError),
        "film_package": package(edition),
        "cover": cover(edition) if staged is None else "not compared: the stage is not current",
    }
    unasked = {name for name, value in found.items() if value in (NO_DRAFTS, NO_THOUGHT_LINE)}
    report = {name: value or CURRENT for name, value in found.items()}
    stale = [f"{name}: {value}" for name, value in found.items() if value and name not in unasked]
    try:
        bound = bound_inputs(edition)
    except FileNotFoundError as error:
        bound = None
        stale.append(f"receipt: {missing(error)}")
    receipt = {
        "edition": edition.code,
        "verdict": "refuse" if stale else "pass",
        "engine_version": released.version(),
        "inputs": report,
        "bound": bound,
    }
    repository.write(edition.readiness, receipt)
    print(json.dumps({"language": edition.code, "inputs": report}, ensure_ascii=False))
    if stale:
        msg = f"{len(stale)} stale or missing inputs before the {edition.code} render: " + (
            " | ".join(stale)
        )
        raise PreflightError(msg)
    return report


def moved_inputs(receipt: dict, edition: Edition, *, own: bool) -> list[str]:
    """The inputs a receipt bound that no longer hold, an engine of another version first:
    all of the edition's inputs, or with `own` False only those every edition shares."""
    moved = [] if receipt.get("engine_version") == released.version() else ["engine_version"]
    try:
        current = bound_inputs(edition) if own else shared_inputs()
    except FileNotFoundError as error:
        return [*moved, missing(error)]
    bound = receipt.get("bound") or {}
    return moved + [name for name, digest in current.items() if bound.get(name) != digest]


def admitted(edition: Edition) -> dict:
    """Whether the readiness receipts admit heavy work on the edition now, without repeating
    the checks.

    Refused unless the edition's receipt passed and every input it bound still holds, and unless
    every other edition's receipt passed on the shared inputs as they stand: a change of another
    edition's own script, cast, timeline or sound since its receipt refuses nothing here.
    """
    refusals = []
    for code in (edition.code, *(c for c in CODES if c != edition.code)):
        own, judged = code == edition.code, Edition(code)
        named = repository.relative(judged.readiness)
        if not judged.readiness.is_file():
            refusals.append(f"no readiness receipt at {named}; run preflight --language {code}")
            continue
        receipt = repository.read(judged.readiness)
        if receipt.get("verdict") != "pass":
            refusals.append(f"{named} did not pass; run preflight --language {code}")
            continue
        moved = moved_inputs(receipt, judged, own=own)
        if moved:
            refusals.append(
                f"{named} binds another {', '.join(moved)}; run preflight --language {code}"
            )
    if refusals:
        msg = f"The {edition.code} edition is not admitted: " + " | ".join(refusals)
        raise PreflightError(msg)
    answer = {"language": edition.code, "admitted": True}
    print(json.dumps(answer))
    return answer
