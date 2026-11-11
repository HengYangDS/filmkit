"""Render an edition's draft and scan it into the record that the pre-render check reads.

`render_draft` stages the edition's captioned picture afresh at DRAFT_SIZE over the whole film in
the draft's own stage (`Edition.draft_stage`), after removing that stage, the draft beside it
(`Edition.draft_picture`) and the edition's earlier draft record and receipt, so that a refused
draft leaves no record for the pre-render check. It renders the stage with the pictures' renderer
settings and the film's declared capture (`rendering.renderer_command`) at DRAFT_FPS in draft
quality, under `nice` at NICENESS or the caller's niceness if that is higher, so that it yields to
other work on the host, within its deadline, and writes the draft's receipt beside the pictures'
receipts (`Edition.draft_receipt`). The still scan then
writes the edition's draft record (`still_scan.record_draft`), which `filmkit.preflight` requires
before a render.

A render that does not complete raises `PictureError` after its receipt is written and scans
nothing; a draft that holds a still picture over the limit raises it after its record is written.
A draft needs no passing gate record: it shows how the picture looks before the gates pass.

Usage: python -m filmkit.produce render-draft --language zh|en [--deadline <seconds>]
"""

from __future__ import annotations

import json
import os
import shutil
from typing import TYPE_CHECKING

import filmkit.picture.rendering as rendering
import filmkit.picture.still_scan as still_scan
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.specification import DURATION

if TYPE_CHECKING:
    from filmkit.production import Edition

# The draft's frame rate and frame, and the niceness it renders at unless the caller's is higher.
DRAFT_FPS = 10
DRAFT_SIZE = (1920, 1080)
NICENESS = 10
# Seconds a draft's render may take.
DEADLINE = 3600


def still_pictures(record: dict) -> str:
    """The still runs a draft record finds over its limit, each with its time and its speech."""
    return "; ".join(
        f"{run['start']:.2f}-{run['end']:.2f} s with {run['speech']:.2f} s of speech"
        for run in record["over_limit"]
    )


def render_draft(edition: Edition, deadline: float = DEADLINE) -> dict:
    """Stage, render and scan the edition's draft; its draft record."""
    stage, draft = edition.draft_stage, edition.draft_picture
    if stage.exists():
        shutil.rmtree(stage)
    for earlier in (draft, edition.draft_stills, edition.draft_receipt):
        earlier.unlink(missing_ok=True)
    rendering.stage_picture(edition, stage, DURATION, *DRAFT_SIZE)
    command = rendering.renderer_command(stage, draft, DRAFT_FPS, "draft")
    # nice raises the niceness by its increment, so a caller nicer than NICENESS stays as it is.
    increment = max(0, NICENESS - os.getpriority(os.PRIO_PROCESS, 0))
    niced = ["nice", "-n", str(increment), *command]
    rendering.record_render(niced, stage, draft, edition.draft_receipt, deadline, "draft")
    try:
        record = still_scan.record_draft(edition, draft)
    except still_scan.StillScanError as error:
        raise PictureError(str(error)) from error
    longest, failing = record["longest_fine_speech"], len(record["over_limit"])
    print(json.dumps({"longest_fine_speech": longest, "over_limit": failing}))
    if failing:
        msg = (
            f"The {edition.code} draft holds a still picture over {record['limit_seconds']} s of "
            f"speech: {still_pictures(record)}; see {repository.relative(edition.draft_stills)}"
        )
        raise PictureError(msg)
    return record
