"""The picture gate's judgement of whole turns: a stroked clockwise arc through a whole turn from
a start off a whole number of turns, which the renderer's browser drew from each of its starts,
refuses a scene's line it painted without ink from one of them and records every other."""

import math

import filmkit.picture.gates as gates

# Whole turns as the frame audit writes them: each line's draws of one start and end, with the
# first and last frame and the frames that drew it. 1.9335 rad is a start whose whole turn
# Chrome Headless Shell 152 paints without ink; pi, 3 pi / 2 and -pi / 2 it paints in full.
TURN = 2 * math.pi
FAILING = 1.9335
REMEDY = "ellipse(x, y, r, r, start, 0, 2 * Math.PI)"


def draw(scene, origin, start, at, until, frames, *, module=None):
    """One start of a line's whole turns, as the frame audit writes it."""
    return {
        "scene": scene,
        "origin": origin,
        "module": module,
        "start": start,
        "end": start + TURN,
        "from": at,
        "to": until,
        "frames": frames,
    }


def painted(*shares):
    """The browser's draws of whole turns: each start's share of a full ring's ink, and whether
    it paints."""
    turns = [
        {"start": start, "end": start + TURN, "share": share, "paints": share >= 0.6}
        for start, share in shares
    ]
    return {"browser": "HeadlessChrome/152.0.7977.30", "turns": turns}


def test_whole_turns_the_browser_paints_are_recorded_and_refuse_nothing():
    rings = [
        draw("01", "film.js:423", math.pi, 9.13, 24.27, 1400, module="picture/film/strokes.js"),
        draw("02", "film.js:423", 3 * math.pi / 2, 56.3, 153.9, 8408),
        draw("03", "film.js:352", -math.pi / 2, 161.0, 289.73, 7536),
    ]
    shares = painted((math.pi, 1.0), (3 * math.pi / 2, 0.999), (-math.pi / 2, 1.0))
    gated, recorded = gates.turn_findings(rings, shares)
    assert gated == []
    assert recorded == [
        f"frame whole_turns {scene} {span} s: a clockwise arc through a whole turn from {start}"
        f" rad, drawn at {line}, paints in the renderer's browser from each of its 1 starts;"
        f" the ellipse draws it from any start: {REMEDY}"
        for scene, span, start, line in (
            ("01", "9.13-24.27", "3.1416", "film.js:423 (picture/film/strokes.js)"),
            ("02", "56.30-153.90", "4.7124", "film.js:423"),
            ("03", "161.00-289.73", "-1.5708", "film.js:352"),
        )
    ]


def test_a_turning_ring_refuses_on_the_starts_the_browser_does_not_paint():
    # A ring that turns draws a new start in each frame; each start was drawn in the browser once,
    # and a scene's line is judged by all its starts.
    rings = [
        draw("07", "film.js:88", 1.0, 3.0, 3.0, 1),
        draw("07", "film.js:88", FAILING, 3.5, 4.0, 2),
        draw("07", "film.js:88", 2.0, 4.5, 6.0, 4),
        draw("08", "film.js:88", 2.0, 9.0, 9.5, 2),
    ]
    gated, recorded = gates.turn_findings(rings, painted((1.0, 1.0), (FAILING, 0.0), (2.0, 1.0)))
    assert gated == [
        "frame vanishing_arcs 07 3.50-4.00 s: a clockwise arc through a whole turn from 1.9335"
        " rad, drawn at film.js:88, paints no ink in the renderer's browser from 1 of its 3"
        f" starts; draw it as {REMEDY}"
    ]
    assert len(recorded) == 1 and recorded[0].startswith("frame whole_turns 08 9.00-9.50 s:")


def test_a_whole_turn_the_browser_did_not_draw_refuses():
    gated, recorded = gates.turn_findings([draw("02", "film.js:9", 0.5, 1.0, 2.0, 30)], painted())
    assert gated == [
        "frame vanishing_arcs 02: 1 starts of the whole turn drawn at film.js:9 were not drawn in"
        " the renderer's browser"
    ]
    assert recorded == []
