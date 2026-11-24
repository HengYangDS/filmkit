"""The production command: one production action for an edition.

Each action belongs to its owning module, which derives its media and receipts from the
current production contract; the command parses the options and calls that owner. Every
action needs --language. `--deadline` bounds a render in seconds, by default its owner's own:
10800 for a picture, also each one that repair-pictures renders, and 3600 for a draft
(`filmkit.picture.draft`). `--uncaptioned` makes stage-picture, render-picture and
validate-picture act on the edition's uncaptioned picture instead of its captioned one, and
every other action refuses it. render-picture --uncaptioned derives that picture from the
captioned one (`filmkit.picture.derivation`) for a film that declares software capture, and
renders its own stage for any other film or when `--native` asks for it. compare-pictures proves
that the two pictures differ only by the captions (`filmkit.picture.equivalence`), and
qualify-renderer that two renders of the captioned stage show the same by that measure
(`filmkit.picture.qualification`). `--variants` names fit's
pause-policy variants, a file below the film's root or an absolute one
(`filmkit.soundtrack.fit`), and `--attempts` bounds repair-pictures (`filmkit.picture.repair`);
every other action refuses them.
A refusal by an action's owner exits with status 1 and "<action>: <reason>" on standard
error. check-sound measures the assembled soundtrack with its refreshed captions and refuses a
segment under the film's clarity floor, an abrupt or cut ending and a stopped phrase
(`filmkit.soundtrack.gates`). scan-film scans the edition's packaged 1080p captioned film for
still pictures under speech and writes the record that the delivery's verification and a
review round's preparation require (`filmkit.picture.still_scan`). Assembling a soundtrack and
refreshing captions first refuse while a review round binds the edition's films and has not set
them aside (`filmkit.review.set_aside.require_set_aside`).
Every action writes a duration record for its edition when it ends, named after the action and,
for the uncaptioned picture, with `-uncaptioned` after it (`filmkit.durations`).
The command owns no goal, approval, repository lifecycle, service or task state.

Usage: python -m filmkit.produce <edition action> --language <code> [--uncaptioned [--native]]
           [options]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.child_processes as child_processes
import filmkit.durations as durations
import filmkit.picture.derivation as derivation
import filmkit.picture.draft as draft
import filmkit.picture.renderer as renderer
import filmkit.picture.still_scan as still_scan
from filmkit.captions.refresh import refresh_captions
from filmkit.delivery.packaging import PackagingError, package_film, package_metadata
from filmkit.media import MediaError
from filmkit.narration.anchors import AnchorError
from filmkit.narration.selection import select
from filmkit.picture.draft import render_draft
from filmkit.picture.equivalence import compare_pictures
from filmkit.picture.gates import check_picture
from filmkit.picture.qualification import qualify_renderer
from filmkit.picture.rendering import (
    PICTURE_SIZE,
    PictureError,
    render_picture,
    stage_picture,
    validate_picture,
)
from filmkit.picture.repair import ATTEMPTS, repair_pictures
from filmkit.preflight import PreflightError, admitted, preflight
from filmkit.production import CODES, Edition, UnassembledError
from filmkit.review import ReviewError
from filmkit.review.set_aside import require_set_aside
from filmkit.soundtrack.assembly import assemble
from filmkit.soundtrack.fit import REFUSALS as FIT_REFUSALS
from filmkit.soundtrack.fit import VariantsError, fit, read_variants
from filmkit.soundtrack.gates import check_sound
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


def render(edition: Edition, options: argparse.Namespace) -> object:
    """Render the captioned picture, or make the uncaptioned one: derived from the captioned
    picture for a film of the deriving capture, unless --native asks for a render of its own
    stage; rendered from that stage otherwise, its receipt saying why."""
    if not options.uncaptioned:
        return render_picture(edition, deadline(options, renderer.DEADLINE), captions=True)
    way = derivation.uncaptioned_way(edition, native=options.native)
    if way["way"] == "derived":
        return derivation.derive_uncaptioned(edition, deadline(options, derivation.DEADLINE))
    seconds = deadline(options, renderer.DEADLINE)
    return derivation.render_uncaptioned(edition, seconds, asked=options.native)


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
        edition.runtime if options.duration is None else options.duration,
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
    "admitted": lambda edition, _: admitted(edition),
    "render-picture": lambda edition, options: render(edition, options),
    "package-metadata": lambda edition, _: package_metadata(edition),
    "validate-picture": lambda edition, options: validate_picture(
        edition, captions=not options.uncaptioned
    ),
    "qualify-renderer": lambda edition, options: qualify_renderer(
        edition, deadline(options, renderer.DEADLINE)
    ),
    "compare-pictures": lambda edition, _: compare_pictures(edition),
    "repair-pictures": lambda edition, options: repair_pictures(
        edition,
        ATTEMPTS if options.attempts is None else options.attempts,
        deadline(options, renderer.DEADLINE),
    ),
    "package-film": lambda edition, _: package_film(edition),
    still_scan.SCAN_ACTION: lambda edition, _: still_scan.scan_film(edition),
}
# The actions that take either of the edition's two pictures.
PICTURE_ACTIONS = ("stage-picture", "render-picture", "validate-picture")
# The refusals of the actions' owners, which end the command with the action's name and the
# reason; any other exception keeps its traceback. Those of the selection and the assembly
# up to the gap allocation are the ones the fit names for a caller that answers them
# (`filmkit.soundtrack.fit.REFUSALS`).
REFUSALS = (
    *FIT_REFUSALS,
    VariantsError,
    PictureError,
    ToolError,
    MediaError,
    PackagingError,
    PreflightError,
    ReviewError,
    UnassembledError,
    AnchorError,
)


def arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=[*EDITION_ACTIONS])
    parser.add_argument(
        "--duration", type=int, help="stage-picture: the seconds staged, by default the runtime"
    )
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--width", type=int, default=PICTURE_SIZE[0])
    parser.add_argument("--height", type=int, default=PICTURE_SIZE[1])
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
    parser.add_argument(
        "--native",
        action="store_true",
        help="render-picture --uncaptioned: render the uncaptioned stage instead of deriving",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = arguments()
    options = parser.parse_args(argv)
    if options.language is None:
        parser.error("the following arguments are required: --language")
    if options.uncaptioned and options.action not in PICTURE_ACTIONS:
        parser.error(f"--uncaptioned applies only to {', '.join(PICTURE_ACTIONS)}")
    if options.native and not (options.uncaptioned and options.action == "render-picture"):
        parser.error("--native applies only to render-picture --uncaptioned")
    for option, action in (("variants", "fit"), ("attempts", "repair-pictures")):
        if getattr(options, option) is not None and options.action != action:
            parser.error(f"--{option} applies only to {action}")
    command = options.action + ("-uncaptioned" if options.uncaptioned else "")
    try:
        # A request to end while the action runs a renderer, or an interrupt anywhere, unwinds
        # the action, which ends that renderer, and the command then leaves with one line.
        with (
            child_processes.ending(f"{options.action}: stopped by {{request}}"),
            durations.run(options.language, command),
        ):
            EDITION_ACTIONS[options.action](Edition(options.language), options)
    except REFUSALS as error:
        msg = f"{options.action}: {error}"
        raise SystemExit(msg) from None


if __name__ == "__main__":
    main()
