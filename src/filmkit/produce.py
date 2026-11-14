"""The production command: one production action for an edition.

Each action belongs to its owning module, which derives its media and receipts from the
current production contract; the command parses the options and calls that owner. Every
action needs --language. `--deadline` bounds a render in seconds, by default its owner's own:
10800 for a picture, also each one that repair-pictures renders, and 3600 for a draft
(`filmkit.picture.draft`). `--uncaptioned` makes stage-picture, render-picture and
validate-picture act on the edition's uncaptioned picture instead of its captioned one, and
every other action refuses it; compare-pictures proves that the two pictures differ only by the
captions (`filmkit.picture.equivalence`). `--variants` names fit's pause-policy variants, a file
below the film's root or an absolute one (`filmkit.soundtrack.fit`), and `--attempts` bounds
repair-pictures (`filmkit.picture.repair`); every other action refuses them.
A refusal by an action's owner exits with status 1 and "<action>: <reason>" on standard
error. check-sound measures the assembled soundtrack with its refreshed captions and refuses a
segment under the film's clarity floor, an abrupt or cut ending and a stopped phrase
(`filmkit.soundtrack.gates`). Assembling a soundtrack and refreshing captions first refuse while
a review round binds the edition's films and has not set them aside
(`filmkit.review.set_aside.require_set_aside`).
The command owns no goal, approval, repository lifecycle, service or task state.

Usage: python -m filmkit.produce <edition action> --language zh|en [--uncaptioned] [options]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.picture.draft as draft
import filmkit.picture.rendering as rendering
from filmkit.captions import CaptionError
from filmkit.captions.refresh import refresh_captions
from filmkit.delivery.packaging import PackagingError, package_film, package_metadata
from filmkit.media import MediaError
from filmkit.narration.selection import SelectionError, select
from filmkit.narration.spoken_units import AlignmentError
from filmkit.narration.thought_groups import RetainedUtteranceError
from filmkit.picture.draft import render_draft
from filmkit.picture.equivalence import compare_pictures
from filmkit.picture.gates import check_picture
from filmkit.picture.rendering import (
    PictureError,
    render_picture,
    stage_picture,
    validate_picture,
)
from filmkit.picture.repair import ATTEMPTS, repair_pictures
from filmkit.preflight import PreflightError, preflight
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError
from filmkit.review.set_aside import require_set_aside
from filmkit.soundtrack.assembly import AssemblyError, assemble
from filmkit.soundtrack.fit import VariantsError, fit, read_variants
from filmkit.soundtrack.gates import check_sound
from filmkit.soundtrack.level import LevelError
from filmkit.soundtrack.pauses import PauseError
from filmkit.soundtrack.policy import PausePolicyError
from filmkit.specification import DURATION
from filmkit.tools import ToolError

if TYPE_CHECKING:
    from collections.abc import Callable


def deadline(options: argparse.Namespace, default: float) -> float:
    """The deadline that --deadline gives, or else the owner's own default."""
    return default if options.deadline is None else options.deadline


def after_set_aside(edition: Edition, owner: Callable[[Edition], object]) -> object:
    """Run an owner that rewrites the edition's build in place, unless a round still binds it.

    Refused while a review round's prompts bind the edition's films and that round has not set
    them aside (`require_set_aside`).
    """
    require_set_aside(edition)
    return owner(edition)


# Each edition action's adapter from the parsed options to its owner. The adapters name their
# owners when they run, so a test can replace an owner.
EDITION_ACTIONS: dict[str, Callable[[Edition, argparse.Namespace], object]] = {
    "select": lambda edition, _: select(edition),
    "fit": lambda edition, options: fit(
        edition, read_variants(options.variants) if options.variants else {}
    ),
    "assemble": lambda edition, _: after_set_aside(edition, assemble),
    "refresh-captions": lambda edition, _: after_set_aside(edition, refresh_captions),
    "check-sound": lambda edition, _: check_sound(edition),
    "stage-picture": lambda edition, options: stage_picture(
        edition,
        options.output,
        options.duration,
        options.width,
        options.height,
        options.start,
        captions=not options.uncaptioned,
    ),
    "check-picture": lambda edition, _: check_picture(edition),
    "render-draft": lambda edition, options: render_draft(
        edition, deadline(options, draft.DEADLINE)
    ),
    "preflight": lambda edition, _: preflight(edition),
    "render-picture": lambda edition, options: render_picture(
        edition, deadline(options, rendering.DEADLINE), captions=not options.uncaptioned
    ),
    "package-metadata": lambda edition, _: package_metadata(edition),
    "validate-picture": lambda edition, options: validate_picture(
        edition, captions=not options.uncaptioned
    ),
    "compare-pictures": lambda edition, _: compare_pictures(edition),
    "repair-pictures": lambda edition, options: repair_pictures(
        edition,
        ATTEMPTS if options.attempts is None else options.attempts,
        deadline(options, rendering.DEADLINE),
    ),
    "package-film": lambda edition, _: package_film(edition),
}
# The actions that take either of the edition's two pictures.
PICTURE_ACTIONS = ("stage-picture", "render-picture", "validate-picture")
# The refusals of the actions' owners, which end the command with the action's name and the
# reason; any other exception keeps its traceback.
REFUSALS = (
    SelectionError,
    RetainedUtteranceError,
    AlignmentError,
    AssemblyError,
    PausePolicyError,
    VariantsError,
    PauseError,
    LevelError,
    CaptionError,
    PictureError,
    ToolError,
    MediaError,
    PackagingError,
    PreflightError,
    ReviewError,
)


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=[*EDITION_ACTIONS])
    parser.add_argument("--duration", type=int, default=DURATION)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--height", type=int, default=2160)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--language", choices=CODES, help="the edition of an edition action")
    parser.add_argument("--deadline", type=int, help="seconds a render may take")
    parser.add_argument(
        "--variants",
        type=Path,
        help="fit: a JSON file of pause-policy variants, below the film's root or absolute",
    )
    parser.add_argument("--attempts", type=int, help="repair-pictures: at most this many attempts")
    parser.add_argument(
        "--uncaptioned",
        action="store_true",
        help="act on the uncaptioned picture: " + ", ".join(PICTURE_ACTIONS),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = arguments()
    options = parser.parse_args(argv)
    if options.language is None:
        parser.error("the following arguments are required: --language")
    if options.uncaptioned and options.action not in PICTURE_ACTIONS:
        parser.error(f"--uncaptioned applies only to {', '.join(PICTURE_ACTIONS)}")
    for option, action in (("variants", "fit"), ("attempts", "repair-pictures")):
        if getattr(options, option) is not None and options.action != action:
            parser.error(f"--{option} applies only to {action}")
    try:
        EDITION_ACTIONS[options.action](Edition(options.language), options)
    except REFUSALS as error:
        msg = f"{options.action}: {error}"
        raise SystemExit(msg) from None


if __name__ == "__main__":
    main()
