"""Reports of a picture's audits as the picture gate reads them, for the gate's tests: a clean
picture, and the rows that make each finding."""

import filmkit.picture.gates as gates


def opening(title, seconds, *, contrast=15.6, step=1 / 30):
    """Text trace rows of a title card shown from the start for `seconds`."""
    return "".join(
        f"{k * step:.2f}\t\ttitle\t{contrast:.3f}\t1.000\t{title}\n"
        for k in range(round(seconds / step))
    )


# Reports of a clean picture: no gated frame finding, every label in sync, no long still, a
# title card through the 2 s before the first word, and no finding of the detail audit on a
# composition that publishes its drawn strokes.
CLEAN = {
    "frame": {
        **dict.fromkeys(gates.FRAME_GATES, {}),
        "errors": [],
        "overlaps": [],
        "frames_checked": 301,
        "long_names": {"03": ["a name@4.0"]},
    },
    "sync": {
        "findings": [],
        "out_of_sync": 0,
        "labels_judged": 12,
        "continuity": {"unnamed_speech": [], "held_over": [], "seats": [], "caption_echoes": []},
    },
    "motion": {
        "still": [{"start": 4.0, "end": 7.2, "seconds": 3.2}],
        "pops": [1],
        "followed": {"findings": []},
    },
    "detail": {
        "lines": {"pace": 450, "race": 900, "rail_clear": 48},
        "ink_drops": [],
        "outside_runs": [],
        "draws_published": True,
        "part_drawn": [],
        "racing_tips": [],
        "rails": [],
    },
    "texts": opening("示例影片", 2.0),
    # The mass audit's report of a picture whose weight stands within 90 px of x 960 throughout.
    "mass": {
        "canvas": [1920, 1080],
        "step": 0.1,
        "frames": [],
        "off_centre_mass": {},
        "mass_balance": {
            "03": {
                "frames": 30,
                "faint": 0,
                "declared": 0,
                "median_dx": -12.0,
                "median_dy": 4.0,
                "within": 1.0,
            }
        },
        "outside_scenes": 0,
    },
}
# A caption cue that labels drawn during it repeat, as the sync audit lists it.
ECHO = {
    "start": 717.7,
    "segment": "08",
    "text": "The people watching the pipeline report this back,",
}


def continuity(**rows):
    """The clean reports with the sync audit's continuity lists replaced by `rows`."""
    return {
        **CLEAN,
        "sync": {**CLEAN["sync"], "continuity": {**CLEAN["sync"]["continuity"], **rows}},
    }


# A text-layout run as the frame audit reports it per scene.
RAGGED_ROW = {
    "start": 1.0,
    "end": 3.0,
    "texts": ["Sources", "Films"],
    "baselines": [500.0, 506.0],
    "gap": 199.2,
}


def wrapped(lines, breaks, at=12.25):
    """A wrapped label as the frame audit reports it per scene."""
    shares = [1.0] * len(lines)
    return {"lines": lines, "seen": at - 0.5, "at": at, "breaks": breaks, "shares": shares}


# A label that ends a line on a preposition, and its finding.
BROKEN = wrapped(["A trade in", "the market"], ['line 1 ends on the lead word "in"'])
BROKEN_FINDING = (
    'frame wrapped label 10 "A trade in" / "the market" at rest 12.25 s: '
    'line 1 ends on the lead word "in"'
)
