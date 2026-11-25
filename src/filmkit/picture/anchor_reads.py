"""What a picture reads of its anchors, refused where the edition does not mark it.

The headless runtime (`picture/headless-composition.mjs`) presents each segment's `anchors`
through a recorder that notes every id the composition reads and gives a stand-in for one the
edition does not mark there, so that a scene goes on and every unmarked id of a draw is found.
Two checks refuse by those ids, each naming every one with its segment and edition:

- before narration (`check`), which narration's gate asks after its readings check, in a dry run
  too and before any speech model loads: both scripts' anchors must keep their rules
  (`filmkit.narration.anchors`), and the `anchor-reads` tool draws the composition for each edition
  over the timeline the engine derives from that edition's script, every frame from 0 at a step of
  `STEP`. An id is required only of an edition whose picture reads it. A scene that throws is named
  as not judged, with its error and the ids it read in a frame that threw, and a composition that
  does not load is named as not judged for its whole edition with its error's one line, whether or
  not the film marks anchors; neither refuses, and the check's answer is then "not judged", not
  "pass": the picture gate still refuses before any render. A check whose tool or packages are
  missing refuses with the reason, and so does an unmarked id read by a scene that loads. A film
  without a composition is not asked.
- the picture gate (`filmkit.picture.gates`), which refuses each unmarked id that the frame audit
  records while it draws the edition's timeline (`unmarked`), also when an audit fails.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.narration import anchors
from filmkit.narration.anchors import AnchorError
from filmkit.picture.errors import PictureError
from filmkit.picture.rendering import COMPOSITION_SCRIPT
from filmkit.production import CODES, Edition

# The seconds between the frames the check before narration draws.
STEP = 0.25
# What the check says of a film that has no composition.
NOT_ASKED = "not asked: the film has no composition"


def unmarked(reads: list[dict], code: str) -> list[str]:
    """Each id a picture read from a segment's anchors where the edition does not mark it."""
    return [
        f"{code} {read['segment']} {read['id']}: the {code} picture reads it from segment"
        f" {read['segment']} and the {code} edition does not mark it there"
        for read in reads
        if not read["marked"]
    ]


def recorded(path: Path) -> list[dict]:
    """The reads a frame audit recorded in its `ANCHORS` file, none where it wrote no file."""
    return repository.read(path)["reads"] if path.is_file() else []


def check(*, rules: bool = True) -> dict | str:
    """Refuse a film whose scripts break an anchor's rule or do not mark what either edition's
    picture reads, before narration; with `rules` false the caller asks the anchors' rules
    itself (`filmkit.check`), and only what the pictures read is asked here.

    Returns:
        The verdict, "pass" or "not judged"; for each edition the scenes the check could not
        judge; the editions whose composition does not load, each with its error's one line; or
        `NOT_ASKED`.
    """
    if rules:
        anchors.require_editions()
    if not (repository.ROOT / COMPOSITION_SCRIPT).is_file():
        return NOT_ASKED
    refusals, unjudged, unloaded = [], {}, {}
    with tempfile.TemporaryDirectory() as folder:
        for code in CODES:
            drawn = _draw(code, Path(folder))
            if drawn["loads"] is False:
                unloaded[code] = drawn["error"].splitlines()[0]
            refusals += unmarked(drawn["reads"], code)
            unjudged[code] = drawn["unjudged"]
    if refusals:
        msg = "The scripts do not mark anchors their picture reads:\n" + "\n".join(refusals)
        raise AnchorError(msg)
    judged = not unloaded and not any(unjudged.values())
    return {
        "verdict": "pass" if judged else "not judged",
        "not_judged": unjudged,
        "not_loaded": unloaded,
    }


def _draw(code: str, folder: Path) -> dict:
    """The `anchor-reads` tool's report of an edition's picture over its derived timeline: drawn,
    or not loaded; any other end of the tool refuses."""
    timeline, report = folder / f"{code}.json", folder / f"{code}-reads.json"
    repository.write(
        timeline, anchors.derived_timeline(repository.read(Edition(code).script), code)
    )
    try:
        status = tools.run("anchor-reads", [str(timeline), str(STEP)], stdout=report)
    except PictureError as error:
        reason = str(error)
    else:
        drawn = repository.read(report) if report.stat().st_size else {}
        if (status == 0 and drawn.get("drawn")) or drawn.get("loads") is False:
            return drawn
        reason = drawn.get("error") or f"the anchor-reads tool exited with status {status}"
    msg = f"The check of what the {code} picture reads cannot draw it: {reason}"
    raise AnchorError(msg)
