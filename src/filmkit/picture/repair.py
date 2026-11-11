"""Render again only the pictures that hold attributed one-frame faults, within an attempt limit.

`repair_pictures` starts from the edition's comparison record (`filmkit.picture.equivalence`),
which must bind the current pictures and inputs; a record that passed leaves both pictures as
they are. It reads the record's faults by the picture that holds each (`faults.repairable`),
which refuses any finding that rendering one picture again cannot repair, and checks each named
picture's stage and gate record as `render-picture` would, before it moves anything.

Each attempt takes the next number below the edition's repairs (`Edition.picture_repairs`), so a
later run continues the numbering. It keeps there a copy of the refused record and, moved, each
named picture and its receipt, renders each named picture again (`rendering.render_picture`) and
compares the two pictures again; its attempt.json records the faults, each kept file's SHA-256,
the receipts of the pictures rendered again and the comparison's verdict and findings. The repair
stops at the first comparison that passes, and refuses when the last attempt still finds faults
or a later comparison holds a finding it cannot repair, naming the attempts it made. A render or
comparison that fails inside an attempt is recorded there with the receipts so far, and the
refusal names the attempt's folder and the commands that bring the edition back: `render-picture`
for each picture not rendered again, then `compare-pictures`.
A faulty render is evidence of a fault rather than a reproducible artifact, so the kept pictures
stay with the edition's evidence and not with the reviewed builds that `set-aside` keeps.

Usage: python -m filmkit.produce repair-pictures --language zh|en [--attempts <n>]
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
from filmkit.media import MediaError
from filmkit.picture.rendering import PictureError
from filmkit.tools import ToolError

if TYPE_CHECKING:
    from filmkit.production import Edition

# The attempts of one run, unless it is given another number, and the command that compares the
# two pictures again once an attempt stopped.
ATTEMPTS = 2
COMPARE = "python -m filmkit.produce compare-pictures --language {code}"
# What a render or comparison inside an attempt refuses with.
REFUSALS = (PictureError, MediaError, ToolError)


def current_record(edition: Edition) -> dict:
    """The edition's comparison record, refused unless it binds the current pictures, the
    composition, the timeline and the engine."""
    path = edition.caption_equivalence
    if not path.is_file():
        msg = f"The {edition.code} pictures have no comparison record; run compare-pictures"
        raise PictureError(msg)
    record = repository.read(path)
    try:
        current = equivalence.current_bindings(edition)
    except FileNotFoundError as error:
        missing = repository.relative(Path(error.filename))
        msg = f"The {edition.code} comparison record cannot be checked: missing {missing}"
        raise PictureError(msg) from error
    stale = [key for key, value in current.items() if record.get(key) != value]
    if stale:
        msg = (
            f"The {edition.code} comparison record does not bind the current {', '.join(stale)}; "
            "run compare-pictures"
        )
        raise PictureError(msg)
    return record


def require_renderable(edition: Edition, named: dict[str, list[dict]]) -> None:
    """Refuse unless each named picture can be rendered as it stands: the renderer, the passing
    gate record and the picture's current stage that `render_picture` requires."""
    rendering.require_renderer()
    rendering.require_passing_gates(edition)
    for name in named:
        rendered = edition.rendered(name == "captioned")
        rendering.require_current_stage(edition, rendered.stage, captions=rendered.captions)


def next_attempt(edition: Edition) -> Path:
    """The edition's next attempt folder, numbered one above the highest, created empty."""
    repairs = edition.picture_repairs
    found = repairs.iterdir() if repairs.is_dir() else ()
    numbered = (int(path.name) for path in found if re.fullmatch("[0-9]+", path.name))
    number = max(numbered, default=0) + 1
    folder = repairs / str(number)
    folder.mkdir(parents=True)
    return folder


def keep(edition: Edition, named: dict[str, list[dict]], folder: Path) -> dict[str, str]:
    """Copy the refused record and move each named picture and its receipt into an attempt
    folder; each kept file's SHA-256 by its path below the root."""
    shutil.copy2(edition.caption_equivalence, folder / edition.caption_equivalence.name)
    for name in named:
        rendered = edition.rendered(name == "captioned")
        for path in (rendered.file, rendered.receipt):
            shutil.move(path, folder / path.name)
    return {repository.relative(path): repository.sha(path) for path in sorted(folder.iterdir())}


def made(edition: Edition, numbers: list[int]) -> str:
    """The attempts a repair made and where it kept them, as its refusals name them."""
    attempts = "attempt" if len(numbers) == 1 else "attempts"
    kept = repository.relative(edition.picture_repairs)
    return f"{len(numbers)} {attempts}, kept in {kept} as {attempts} {', '.join(map(str, numbers))}"


def completed(receipt: dict | None) -> bool:
    """Whether a render receipt records a render that exited 0 within its deadline."""
    return receipt is not None and receipt.get("exit") == 0 and receipt.get("timed_out") is False


def stopped(edition: Edition, folder: Path, attempt: dict, error: BaseException) -> str:
    """The refusal of an attempt whose render or comparison failed: the attempt, its folder, the
    failure and the commands that bring the edition back."""
    code, rendered = edition.code, attempt["rendered"]
    renders = [
        faults.RENDER.format(code=code) + ("" if name == "captioned" else " --uncaptioned")
        for name in attempt["faults"]
        if not completed(rendered.get(name))
    ]
    again = f"render again with {' and '.join(renders)}, then " if renders else ""
    return (
        f"Attempt {folder.name} of the {code} repair stopped, with the faulty pictures kept in "
        f"{repository.relative(folder)}: {error}; {again}run {COMPARE.format(code=code)}"
    )


def render_and_compare(edition: Edition, attempt: dict, deadline: float) -> dict:
    """Render each picture an attempt names again, keeping each receipt in the attempt as it is
    written, and compare the two pictures; the comparison record."""
    for name in attempt["faults"]:
        captions = name == "captioned"
        try:
            rendering.render_picture(edition, deadline, captions=captions)
        finally:
            receipt = edition.rendered(captions).receipt
            if receipt.is_file():
                attempt["rendered"][name] = repository.read(receipt)
    return compare(edition)


def compare(edition: Edition) -> dict:
    """Compare the two pictures again; the record the comparison wrote, which binds them, or the
    comparison's own refusal where it wrote none."""
    try:
        return equivalence.compare_pictures(edition)
    except PictureError as error:
        refusal = error
    try:
        return current_record(edition)
    except PictureError:
        raise refusal from None


def repair_pictures(
    edition: Edition, attempts: int = ATTEMPTS, deadline: float = rendering.DEADLINE
) -> dict:
    """Render again the pictures that hold the faults a refused comparison attributes, and
    compare after each attempt; the passing comparison record."""
    if attempts < 1:
        msg = f"A repair makes at least one attempt, not {attempts}"
        raise PictureError(msg)
    record = current_record(edition)
    named = faults.repairable(record, edition.code)
    numbers: list[int] = []
    while named:
        require_renderable(edition, named)
        folder = next_attempt(edition)
        numbers.append(int(folder.name))
        attempt = {"faults": named, "kept": keep(edition, named, folder), "rendered": {}}
        repository.write(folder / "attempt.json", attempt)
        try:
            record = render_and_compare(edition, attempt, deadline)
        except BaseException as error:
            repository.write(folder / "attempt.json", {**attempt, "error": str(error)})
            if isinstance(error, REFUSALS):
                raise PictureError(stopped(edition, folder, attempt, error)) from error
            raise
        attempt |= {"verdict": record["verdict"], "findings": record["findings"]}
        repository.write(folder / "attempt.json", attempt)
        print(
            json.dumps({"attempt": numbers[-1], "pictures": [*named], "verdict": record["verdict"]})
        )
        try:
            named = faults.repairable(record, edition.code)
        except PictureError as error:
            msg = f"{error}; the repair stopped after {made(edition, numbers)}"
            raise PictureError(msg) from error
        if named and len(numbers) == attempts:
            msg = (
                f"The {edition.code} pictures still hold one-frame faults after "
                f"{made(edition, numbers)}: {'; '.join(record['findings'])}"
            )
            raise PictureError(msg)
    return record
