"""Check, before an expensive render, every input the render and the next packaging bind.

`preflight` reports at once every stale or missing input of an edition, each by the owner that
would refuse it later, and refuses with `PreflightError` while any remains:

- the stages: the complete current UHD pictures that `render-picture` renders, the captioned one
  and the uncaptioned one (`filmkit.picture.rendering.require_current_stage`);
- the cover: the edition's tracked cover identical to the cover the staged composition paints,
  as `filmkit.tools player-check cover` compares them, the painting written below
  build/runtime/work/preflight/<code>/;
- the film package: an earlier package record, which `package-film` would refuse to extend once
  the render replaces the picture it binds, with the fields the current inputs no longer match
  (`filmkit.delivery.packaging.stale_bindings`); set its films aside first
  (`filmkit.review.round set-aside`);
- the draft: the still scan of the edition's 10 fps draft (`Edition.draft_stills`), which must
  exist, find no still run over the limit and bind the current timeline and composition;
- the concepts: the film's words against its concept contract (`filmkit.concepts.check`);
- the picture gate: a passing gate record bound to the current composition, timeline,
  stylesheet, fonts and engine (`filmkit.picture.rendering.require_passing_gates`).

Usage: python -m filmkit.produce preflight --language zh|en
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.concepts as concepts
import filmkit.delivery.packaging as packaging
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
import filmkit.sources as sources
import filmkit.tools as tools

if TYPE_CHECKING:
    from filmkit.production import Edition

# The cover paintings, below the film's root, in a folder for each edition.
WORK = Path("build/runtime/work/preflight")
CURRENT = "current"


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


def preflight(edition: Edition) -> dict:
    """Report each input of the edition's render as current or stale, and refuse a stale one.

    The cover is painted from the stage, so it is compared only once the stage is current.
    """
    staged = stage(edition)
    found = {
        "stage": staged,
        "uncaptioned_stage": stage(edition, captions=False),
        "picture_gate": gates(edition),
        "draft_stills": draft(edition),
        "concepts": concept_check(),
        "film_package": package(edition),
        "cover": cover(edition) if staged is None else "not compared: the stage is not current",
    }
    report = {name: value or CURRENT for name, value in found.items()}
    print(json.dumps({"language": edition.code, "inputs": report}, ensure_ascii=False))
    stale = [f"{name}: {value}" for name, value in found.items() if value]
    if stale:
        msg = f"{len(stale)} stale or missing inputs before the {edition.code} render: " + (
            " | ".join(stale)
        )
        raise PreflightError(msg)
    return report
