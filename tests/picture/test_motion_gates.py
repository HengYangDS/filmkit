"""The motion gate's one-frame changes: jumps, the pops a declared cut brings, and dash snaps."""

import pytest

import filmkit.picture.gates as gates
from filmkit.film import Motion

# A jump as the motion audit groups it: a field and its name that a stage cut moved 354 px left.
JUMP = {
    "kind": "jump",
    "scene": "04",
    "origin": "film.js:1960",
    "module": None,
    "start": 165.8,
    "end": 165.8,
    "shift": [-354, 0],
    "distance": 354,
    "marks": 2,
    "frames": 1,
    "paints": ["stroke", "text"],
    "texts": ["边界"],
}
# A join whose solid line turned into dashes of 8 px on and 8 px off within one frame.
DASH = {
    "kind": "dash",
    "scene": "13",
    "origin": "film.js:4667",
    "module": "picture/film/scenes/p13/join.js",
    "start": 645.967,
    "end": 645.967,
    "gaps": [0, 0.5],
    "frames": 1,
    "paints": ["stroke"],
    "texts": [],
}
# A name that a declared cut brought at full ink into a stage that otherwise stood.
POP = {
    "kind": "pop",
    "way": "in",
    "declared_cut": True,
    "scene": "06",
    "origin": "film.js:2660",
    "module": None,
    "start": 300.2,
    "end": 300.2,
    "level": 221,
    "frames": 1,
    "paints": ["text"],
    "texts": ["Hypothesis"],
}


@pytest.mark.parametrize(
    ("finding", "named"),
    [
        (
            JUMP,
            "motion_jumps 04 165.80 s: stroke/text '边界' jump 354 px (-354, 0) beyond their motion"
            " as 2 marks at a cut, drawn at film.js:1960",
        ),
        (
            DASH,
            "motion_dash_snaps 13 645.97 s: stroke turns from 0% to 50% gap in its dash pattern"
            " within one frame, drawn at film.js:4667 (picture/film/scenes/p13/join.js)",
        ),
        (
            POP,
            "motion_pops 06 300.20 s: text 'Hypothesis' at ink 221 appears within one frame at a"
            " declared cut that keeps its stage, drawn at film.js:2660",
        ),
    ],
)
def test_each_one_frame_change_refuses_by_its_time_scene_and_line(finding, named):
    motion = {"followed": {"findings": [finding]}}
    assert gates.motion_findings(motion, Motion(), "en") == ([named], [])


def test_a_declared_jump_or_dash_snap_is_recorded_with_its_reason():
    kept = Motion(
        exceptions=(
            {
                "edition": "en",
                "scene": "04",
                "source": "film.js:1960",
                "kind": "jump",
                "reason": "the field re-forms its stage",
            },
            {
                "edition": "en",
                "scene": "13",
                "source": DASH["module"],
                "kind": "dash",
                "reason": "the join breaks on its word",
            },
        )
    )
    gated, recorded = gates.motion_findings({"followed": {"findings": [JUMP, DASH]}}, kept, "en")
    assert gated == []
    assert [row.split("; declared: ")[1] for row in recorded] == [
        "the field re-forms its stage",
        "the join breaks on its word",
    ]
