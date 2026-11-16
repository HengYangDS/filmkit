"""The detail gate: each finding of the detail audit and each far run refused by its kind and
scene, the film's exceptions to them, and the record of a composition whose strokes it cannot
read."""

import pytest
import test_gates
from pydantic import ValidationError
from test_gates import CLEAN, audits

import filmkit.picture.gates as gates
import filmkit.repository as repository
from filmkit.film import FILM, Detail, DetailException
from filmkit.picture.detail_gates import NO_DRAWS, detail_findings
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition

# The gate's film root, as the gate's own tests build it.
film = test_gates.film

# A path that opens a 55 px gap within one frame, as the detail audit reports it.
DROP = {
    "t": 392.6,
    "scene": "08",
    "origin": "film.js:2210",
    "module": "picture/film/scenes/p08/path.js",
    "lost": 55,
    "of": 640,
}
DROP_FINDING = (
    "detail ink_drop 08 392.60 s: a line loses 55 of its 640 px within one frame, drawn at"
    " film.js:2210 (picture/film/scenes/p08/path.js)"
)
# A chapter title that travels from its card to the running head.
TITLE = {
    "text": "Evidence",
    "start": 61.017,
    "end": 61.5,
    "frames": 30,
    "speed": 1198,
    "at": 61.25,
    "way": 520,
    "scene": "02",
}
TITLE_FINDING = (
    "detail outside_pace 02 61.02-61.50 s: 'Evidence', outside every scene, moves 520 px at up"
    " to 1198 px/s at 61.25 s, over the pace of 450 px/s for 30 frames"
)
# A bracket three fifths drawn through the quiet after the thought that names its layers.
BRACKET = {"quiet": "05.3", "rest": 214.2, "resume": 215.05, "scene": "05", "cue": 213.4}
BRACKET_FINDING = (
    "detail part_drawn 05 214.20-215.05 s: the stroke keyed at 213.40 s stands 60% drawn through"
    " the quiet after thought 05.3"
)
TIP_FINDING = (
    "detail racing_tip 05: the tip of the stroke keyed at 213.40 s draws at 950 px/s, at or over"
    " the 900 px/s at which a mark races"
)
# A rail whose second name reaches under its first, 13.8 px below it.
RAIL = {
    "scene": "13",
    "set": "duties",
    "clear": 13.8,
    "names": ["Find the users", "Plan the release"],
    "across": -20,
    "down": 13.8,
    "at": "13.2",
}
RAIL_FINDING = (
    "detail rail 13 duties at the rest of thought 13.2: 'Find the users' and 'Plan the release'"
    " on its two baselines stand 13.8 px apart, under 48 px"
)
FAR = {"27": ["1203.42-1204.40 -624.0 px"]}
FAR_FINDING = "frame off_centre_far 27: 1203.42-1204.40 -624.0 px"


def report(**rows):
    """The clean detail report with `rows` replaced."""
    return {**CLEAN["detail"], **rows}


def found(detail=None, frame=None, exceptions=(), pace_limit=None, code="zh"):
    """The gated and the recorded findings of the reports under the given exceptions."""
    policy = Detail(exceptions=[{"edition": "zh", "reason": "kept", **e} for e in exceptions])
    return detail_findings(detail or report(), frame or {}, policy, pace_limit, code)


@pytest.mark.parametrize(
    ("detail", "frame", "named"),
    [
        (report(ink_drops=[DROP]), {}, DROP_FINDING),
        (report(outside_runs=[TITLE]), {}, TITLE_FINDING),
        (report(part_drawn=[{**BRACKET, "share": 0.6}]), {}, BRACKET_FINDING),
        (report(racing_tips=[{"scene": "05", "cue": 213.4, "pace": 950}]), {}, TIP_FINDING),
        (report(rails=[RAIL]), {}, RAIL_FINDING),
        (report(), {"off_centre_far": FAR}, FAR_FINDING),
    ],
)
def test_each_detail_finding_is_gated_by_its_kind_scene_and_measure(detail, frame, named):
    assert found(detail, frame) == ([named], [])


@pytest.mark.parametrize(
    ("detail", "frame", "named", "exception"),
    [
        (
            report(ink_drops=[DROP]),
            {},
            DROP_FINDING,
            {"kind": "ink_drop", "scene": "08", "source": "film.js:2210"},
        ),
        (
            report(ink_drops=[DROP]),
            {},
            DROP_FINDING,
            {"kind": "ink_drop", "scene": "08", "source": "picture/film/scenes/p08/path.js"},
        ),
        (
            report(outside_runs=[TITLE]),
            {},
            TITLE_FINDING,
            {"kind": "outside_pace", "scene": "02", "source": "Evidence"},
        ),
        (
            report(part_drawn=[{**BRACKET, "share": 0.6}]),
            {},
            BRACKET_FINDING,
            {"kind": "part_drawn", "scene": "05", "source": "05.3"},
        ),
        (
            report(racing_tips=[{"scene": "05", "cue": 213.4, "pace": 950}]),
            {},
            TIP_FINDING,
            {"kind": "racing_tip", "scene": "05"},
        ),
        (report(rails=[RAIL]), {}, RAIL_FINDING, {"kind": "rail", "scene": "13"}),
        (
            report(rails=[RAIL]),
            {},
            RAIL_FINDING,
            {"kind": "rail", "scene": "13", "source": "duties"},
        ),
        (
            report(),
            {"off_centre_far": FAR},
            FAR_FINDING,
            {"kind": "off_centre_far", "scene": "27", "source": "left"},
        ),
    ],
)
def test_a_declared_finding_is_recorded_with_its_reason(detail, frame, named, exception):
    assert found(detail, frame, [exception]) == ([], [f"{named}; declared: kept"])


def test_an_exception_names_one_scene_one_source_and_one_edition():
    detail = report(rails=[RAIL, {**RAIL, "set": "owners", "clear": 17.0}])
    kept = {"kind": "rail", "scene": "13", "source": "owners"}
    gated, recorded = found(detail, exceptions=[kept])
    assert gated == [RAIL_FINDING]
    assert len(recorded) == 1 and "13 owners" in recorded[0]
    # A run on the other side, another scene's finding and another edition's are not named.
    far = {"off_centre_far": {"27": ["1.00-2.00 512.0 px"]}}
    left = {"kind": "off_centre_far", "scene": "27", "source": "left"}
    gated, recorded = found(frame=far, exceptions=[left])
    assert gated == [
        "frame off_centre_far 27: 1.00-2.00 512.0 px",
        "detail exception off_centre_far 27 left is stale: no finding of the edition matches it",
    ]
    assert found(report(rails=[RAIL]), exceptions=[{**kept, "source": None}], code="en") == (
        [RAIL_FINDING],
        [],
    )
    # With a run on each side of the scene, the declared side is recorded and the other refused.
    both = {"off_centre_far": {"27": ["1.00-2.00 -512.0 px", "5.00-6.00 512.0 px"]}}
    assert found(frame=both, exceptions=[left]) == (
        ["frame off_centre_far 27: 5.00-6.00 512.0 px"],
        ["frame off_centre_far 27: 1.00-2.00 -512.0 px; declared: kept"],
    )


def test_a_stale_exception_is_gated():
    stale = "detail exception rail 13 is stale: no finding of the edition matches it"
    assert found(exceptions=[{"kind": "rail", "scene": "13"}]) == ([stale], [])
    # A rail that stands clear is no finding, so its exception is stale too.
    clear = report(rails=[{**RAIL, "clear": 50.2}])
    assert found(clear, exceptions=[{"kind": "rail", "scene": "13"}]) == ([stale], [])
    assert found(clear) == ([], [])


def test_a_text_outside_scenes_under_the_race_is_judged_by_the_films_pace_limit():
    glide = {**TITLE, "speed": 610}
    named = TITLE_FINDING.replace("1198", "610")
    assert found(report(outside_runs=[glide])) == (
        [],
        [f"{named}; recorded: the film declares no pace limit"],
    )
    assert found(report(outside_runs=[glide]), pace_limit=450) == ([named], [])
    assert found(report(outside_runs=[glide]), pace_limit=700) == (
        [],
        [f"{named}; recorded: within the film's pace limit of 700 px/s"],
    )
    # At the pace at which a mark races no limit keeps it.
    assert found(report(outside_runs=[{**TITLE, "speed": 900}]), pace_limit=899)[1] == []


def test_a_composition_that_publishes_no_strokes_is_recorded_as_not_judged():
    assert found(report(draws_published=False)) == ([], [NO_DRAWS])


def test_an_exception_names_only_a_source_its_kind_can_carry():
    def declared(**fields):
        return DetailException(edition="zh", scene="05", reason="kept", **fields)

    assert declared(kind="off_centre_far", source="right").source == "right"
    for fields in (
        {"kind": "racing_tip", "source": "213.4"},
        {"kind": "off_centre_far", "source": "centre"},
    ):
        with pytest.raises(ValidationError, match="cannot name the source"):
            declared(**fields)
    twice = [declared(kind="rail", source="duties")] * 2
    with pytest.raises(ValidationError, match="two exceptions name the same detail finding"):
        Detail(exceptions=twice)


def test_the_gate_refuses_a_detail_finding_and_records_a_declared_one(film, monkeypatch):
    edition = Edition("zh")
    reports = {
        **CLEAN,
        "detail": report(rails=[RAIL]),
        "frame": {**CLEAN["frame"], "off_centre_far": FAR},
    }
    audits(monkeypatch, reports)
    with pytest.raises(PictureError, match="2 gated findings"):
        gates.check_picture(edition)
    record = repository.read(edition.picture_gates)
    assert record["verdict"] == "refuse"
    assert record["gated_findings"] == [RAIL_FINDING, FAR_FINDING]
    kept = [
        {"edition": "zh", "kind": "rail", "scene": "13", "source": "duties", "reason": "narrow"},
        {"edition": "zh", "kind": "off_centre_far", "scene": "27", "reason": "a list builds"},
    ]
    picture = FILM.picture.model_copy(update={"detail": Detail(exceptions=kept)})
    monkeypatch.setattr(gates, "FILM", FILM.model_copy(update={"picture": picture}))
    record = gates.check_picture(edition)
    assert record["verdict"] == "pass"
    assert record["recorded_findings"] == [
        f"{RAIL_FINDING}; declared: narrow",
        f"{FAR_FINDING}; declared: a list builds",
    ]
