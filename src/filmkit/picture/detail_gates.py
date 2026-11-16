"""The detail audit's findings in an edition's gate record, and the film's exceptions to them.

The detail audit (`picture/detail-audit.mjs`) reads what a reviewer finds on single lines,
strokes and names: a line that loses part of its ink within one frame, a text outside every
scene that moves over the pace line, a stroke that stands part-drawn in the quiet between two
thoughts or whose tip races, and the names of a rail on two baselines that stand closer than
the line its report states. The frame audit adds the runs in which the picture stands far off
centre (`off_centre_far`, rules/balance.mjs). Each is gated by its kind and scene unless one of
the edition's `[[picture.detail.exceptions]]` names it, which records it with the exception's
reason; an exception of the edition that matches no finding is gated as stale.

A text outside scenes that moves over the pace line and under the pace at which a mark races is
refused only over the pace limit the film declares, as a scene's glides and flows are
(`filmkit.picture.gates.motion_findings`). A composition that publishes no `draws` cannot be
read for its strokes: the record says that they were not judged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from filmkit.film import Detail

# What the record says of a composition whose layout publishes no drawn strokes.
NO_DRAWS = (
    "detail strokes: the composition publishes no `draws`, so no stroke is judged in a quiet or"
    " by its tip's pace"
)


def drawn(row: dict) -> str:
    """The line that drew a finding's stroke, with its module where the composition names one."""
    return row["origin"] + (f" ({row['module']})" if row["module"] else "")


def side(run: str) -> str:
    """The side of a far run, from its offset as the frame audit states it."""
    return "left" if run.split()[1].startswith("-") else "right"


def rows(detail: dict, frame: dict) -> Iterator[tuple[str, str, tuple[str, ...], str]]:
    """Each finding of the two reports as its kind, its scene, the sources that name it within
    its scene and its words in the record."""
    lines = detail["lines"]
    for row in detail["ink_drops"]:
        yield (
            "ink_drop",
            row["scene"],
            tuple(v for v in (row["origin"], row["module"]) if v),
            f"detail ink_drop {row['scene']} {row['t']:.2f} s: a line loses {row['lost']} of its"
            f" {row['of']} px within one frame, drawn at {drawn(row)}",
        )
    for row in detail["outside_runs"]:
        yield (
            "outside_pace",
            row["scene"],
            (row["text"],),
            f"detail outside_pace {row['scene']} {row['start']:.2f}-{row['end']:.2f} s:"
            f" {row['text']!r}, outside every scene, moves {row['way']} px at up to"
            f" {row['speed']} px/s at {row['at']:.2f} s, over the pace of {lines['pace']} px/s"
            f" for {row['frames']} frames",
        )
    for row in detail["part_drawn"]:
        yield (
            "part_drawn",
            row["scene"],
            (row["quiet"],),
            f"detail part_drawn {row['scene']} {row['rest']:.2f}-{row['resume']:.2f} s: the"
            f" stroke keyed at {row['cue']:.2f} s stands {row['share']:.0%} drawn through the"
            f" quiet after thought {row['quiet']}",
        )
    for row in detail["racing_tips"]:
        yield (
            "racing_tip",
            row["scene"],
            (),
            f"detail racing_tip {row['scene']}: the tip of the stroke keyed at {row['cue']:.2f} s"
            f" draws at {row['pace']} px/s, at or over the {lines['race']} px/s at which a mark"
            " races",
        )
    for row in detail["rails"]:
        if row["clear"] >= lines["rail_clear"]:
            continue
        first, second = row["names"]
        yield (
            "rail",
            row["scene"],
            (row["set"],),
            f"detail rail {row['scene']} {row['set']} at the rest of thought {row['at']}:"
            f" {first!r} and {second!r} on its two baselines stand {row['clear']:g} px apart,"
            f" under {lines['rail_clear']} px",
        )
    for scene, runs in sorted(frame.get("off_centre_far", {}).items()):
        for run in runs:
            yield "off_centre_far", scene, (side(run),), f"frame off_centre_far {scene}: {run}"


def detail_findings(
    detail: dict, frame: dict, policy: Detail, pace_limit: float | None, code: str
) -> tuple[list[str], list[str]]:
    """The gated and the recorded findings of an edition's detail audit and far runs.

    Each finding is gated unless one of the edition's exceptions names its kind and scene and,
    where it gives a source, one of the finding's sources, which records it with the exception's
    reason. A text outside scenes under the pace at which a mark races is gated only over the
    film's `pace_limit`, and recorded otherwise. An exception of the edition that matches no
    finding is gated as stale.
    """
    exceptions = [e for e in policy.exceptions if e.edition == code]
    matched, gated, recorded = set(), [], []
    speeds = {(row["scene"], row["text"]): row["speed"] for row in detail["outside_runs"]}
    for kind, scene, sources, named in rows(detail, frame):
        kept = next(
            (
                e
                for e in exceptions
                if (e.kind, e.scene) == (kind, scene) and (e.source is None or e.source in sources)
            ),
            None,
        )
        if kept is not None:
            matched.add(kept)
            recorded.append(f"{named}; declared: {kept.reason}")
        elif kind == "outside_pace" and speeds[scene, sources[0]] < detail["lines"]["race"]:
            if pace_limit is None:
                recorded.append(f"{named}; recorded: the film declares no pace limit")
            elif speeds[scene, sources[0]] > pace_limit:
                gated.append(named)
            else:
                recorded.append(
                    f"{named}; recorded: within the film's pace limit of {pace_limit:g} px/s"
                )
        else:
            gated.append(named)
    gated += [
        f"detail exception {e.kind} {e.scene}{f' {e.source}' if e.source else ''} is stale: no"
        " finding of the edition matches it"
        for e in exceptions
        if e not in matched
    ]
    if not detail["draws_published"]:
        recorded.append(NO_DRAWS)
    return gated, recorded
