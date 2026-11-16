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
  10 fps draft (`Edition.draft_stills`), which must exist, find no still run over the limit and
  bind the current timeline and composition;
- the concepts: the film's words against its concept contract (`filmkit.concepts.check`);
- the picture gate: a passing gate record bound to the current composition, timeline,
  stylesheet, fonts and engine (`filmkit.picture.rendering.require_passing_gates`);
- the sound gate: a passing record of `check-sound` bound to the current soundtrack, timeline
  and engine;
- the thoughts under the clarity floor, for a film that declares the line a single thought is
  judged against (`review.clarity_thought_margin_db`): none under that line, and each between
  the line and the floor declared by its name (`review.clarity_exceptions`);
- the caption cues above the edition's reading rate, each declared by its text
  (`captions.rate_exceptions`);
- the geometry: the record that the delivery's verification requires, passed on the whole
  current staged film (`filmkit.delivery.verification.require_covering_geometry`).

A declared thought or cue that no longer stands under its line is refused as stale.

The answer is written as the edition's readiness receipt (`Edition.readiness`): the verdict, each
question's answer, the engine version and the SHA-256 of every input the answer was judged on.
`admitted` reads receipts without repeating the work: it refuses unless the edition's receipt
passed and each input it bound still holds, and unless the other edition's receipt passed on the
composition, stylesheet, fonts and declaration as they stand, since both editions render one
composition and a finding in either changes it for both.

Usage: python -m filmkit.produce preflight --language zh|en
       python -m filmkit.produce admitted --language zh|en
"""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path

import filmkit.concepts as concepts
import filmkit.delivery.packaging as packaging
import filmkit.delivery.verification as verification
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
import filmkit.sources as sources
import filmkit.tools as tools
from filmkit.captions.timing import READING_RATES, captions_above_rate
from filmkit.film import FILM
from filmkit.production import CODES, Edition

# The cover paintings, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/preflight")
CURRENT = "current"
# What the report says of a draft scan that the film does not declare.
NO_DRAFTS = "not asked: the film declares no drafts"
# What it says of thoughts under the clarity floor when the film declares no line for them.
NO_THOUGHT_LINE = "not judged: the film declares no line for a single thought"


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
    """Whether the draft's still scan passed on the current timeline and composition."""
    path, named = edition.draft_stills, repository.relative(edition.draft_stills)
    if not path.is_file():
        return f"no still scan of the 10 fps draft at {named}"
    record = repository.read(path)
    try:
        current = {
            "timeline": repository.sha(edition.timeline),
            "composition": repository.sha(repository.ROOT / rendering.COMPOSITION_SCRIPT),
        }
    except FileNotFoundError as error:
        return missing(error)
    other = [key for key, digest in current.items() if record.get(key, {}).get("sha256") != digest]
    if other:
        return f"{named} does not bind the current {' and '.join(other)}; scan a new draft"
    if record.get("over_limit"):
        runs, limit = len(record["over_limit"]), record.get("limit_seconds")
        return f"{named} finds {runs} still pictures over {limit} s of speech"
    return None


def concept_check() -> str | None:
    try:
        concepts.check()
    except (concepts.ConceptError, sources.SourceError) as error:
        return "; ".join(str(error).splitlines())
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
    """Whether check-sound passed the edition's current soundtrack and timeline."""
    path, named = edition.sound_gates, repository.relative(edition.sound_gates)
    if not path.is_file():
        return f"no sound gate record at {named}; run check-sound"
    record = repository.read(path)
    try:
        current = {
            "soundtrack_sha256": repository.sha(edition.soundtrack),
            "timeline_sha256": repository.sha(edition.timeline),
            "engine_version": version("filmkit"),
        }
    except FileNotFoundError as error:
        return missing(error)
    stale = [key for key, value in current.items() if record.get(key) != value]
    if stale:
        return f"{named} binds another {', '.join(stale)}; run check-sound"
    if record.get("verdict") != "pass":
        return f"{named} did not pass; run check-sound"
    return None


def clarity(edition: Edition) -> str | None:
    """Whether each thought under the clarity floor is one the film declares, above its line.

    The sound gate holds the floor for the soundtrack and its segments and records the thoughts.
    A film that declares `review.clarity_thought_margin_db` holds every thought to the floor less
    that margin and names each thought between the two lines; one that declares none is not
    judged here.
    """
    margin = FILM.review.clarity_thought_margin_db
    if margin is None:
        return NO_THOUGHT_LINE
    if not edition.sound_gates.is_file():
        return "not judged: no sound gate record"
    measured = repository.read(edition.sound_gates)["clarity"]
    line = round(measured["floor_db"] - margin, 2)
    below = {row["id"]: row["cpp_db"] for row in measured["thoughts"] if row["below_floor"]}
    declared = {e.thought for e in FILM.review.clarity_exceptions if e.edition == edition.code}
    found = [
        f"thought {name} reads {value} dB, under the thought line of {line} dB"
        for name, value in below.items()
        if value < line
    ]
    found += [
        f"thought {name} reads {value} dB, under the floor of {measured['floor_db']} dB, and is"
        " not declared in review.clarity_exceptions"
        for name, value in below.items()
        if value >= line and name not in declared
    ]
    found += [
        f"the declared thought {name} is stale: it does not read under the floor"
        for name in sorted(declared - set(below))
    ]
    return "; ".join(found) or None


def caption_rate(edition: Edition) -> str | None:
    """Whether each cue above the edition's reading rate is one the film declares by its text."""
    rate = READING_RATES.get(edition.code)
    try:
        cues = repository.read(edition.timeline)["captions"]
    except FileNotFoundError as error:
        return missing(error)
    fast = {cue["text"]: cue["characters_per_second"] for cue in captions_above_rate(cues, rate)}
    declared = {e.text for e in FILM.captions.rate_exceptions if e.edition == edition.code}
    found = [
        f"the cue {text!r} reads at {speed} characters per second, above {rate}, and is not"
        " declared in captions.rate_exceptions"
        for text, speed in fast.items()
        if text not in declared
    ]
    found += [
        f"the declared cue {text!r} is stale: no cue with that text reads above the rate"
        for text in sorted(declared - set(fast))
    ]
    return "; ".join(found) or None


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


def shared_inputs() -> dict:
    """The SHA-256 of the inputs both editions share, by name: a receipt of either binds them."""
    faces = rendering.face_bindings()
    return {
        "composition": repository.sha(repository.ROOT / rendering.COMPOSITION_SCRIPT),
        "stylesheet": faces["stylesheet_sha256"],
        "fonts": faces["fonts_sha256"],
        "declaration": repository.sha(repository.ROOT / repository.DECLARATION),
    }


def bound_inputs(edition: Edition) -> dict:
    """The SHA-256 of every input an edition's readiness is judged on, by its name: the inputs
    both editions share, then the edition's own."""
    root = repository.ROOT
    return {
        **shared_inputs(),
        "script": repository.sha(root / edition.script),
        "cast": repository.sha(root / edition.cast),
        "timeline": repository.sha(edition.timeline),
        "assembly": repository.sha(edition.audio_assembly),
        "soundtrack": repository.sha(edition.soundtrack),
    }


def preflight(edition: Edition) -> dict:
    """Report each input of the edition's render as current or stale, write the edition's
    readiness receipt and refuse a stale input.

    The cover is painted from the stage, so it is compared only once the stage is current. A
    question the film does not ask (`NO_DRAFTS`, `NO_THOUGHT_LINE`) is reported and refuses
    nothing. A missing input leaves the receipt without digests, and is refused by name.
    """
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
        "concepts": concept_check(),
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
        "engine_version": version("filmkit"),
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
    all of the edition's inputs, or with `own` False only those both editions share."""
    moved = [] if receipt.get("engine_version") == version("filmkit") else ["engine_version"]
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
    the other edition's receipt passed on the shared inputs as they stand: a change of the other
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
