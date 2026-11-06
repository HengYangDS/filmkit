"""The motion an edition's reviewers read: its picture gate's motion report, as measurement."""

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
import filmkit.review.measurement as review_measurement
import filmkit.review.motion as review_motion
from filmkit.production import Edition
from filmkit.review import ReviewError

# The followed motion of a report: two halts and a pop, the pop and one halt declared.
FOLLOWED = {
    "halts": [{"t": 12.3, "scene": "02"}, {"t": 30.1, "scene": "03"}],
    "starts": [],
    "races": [{"t": 40.1, "scene": "03", "speed": 1200}],
    "pops": [{"t": 51.0, "scene": "06", "way": "in"}],
    "findings": [
        {
            "kind": "halt",
            "scene": "02",
            "start": 12.3,
            "end": 12.3,
            "origin": "film.js:120",
            "module": None,
            "speed": 240,
            "frames": 1,
            "paints": ["fill"],
            "texts": [],
        },
        {
            "kind": "race",
            "scene": "03",
            "start": 40.1,
            "end": 40.1,
            "origin": "film.js:300",
            "module": None,
            "speed": 1200,
            "frames": 1,
            "paints": ["text"],
            "texts": ["原意会走样"],
        },
        {
            "kind": "pop",
            "way": "in",
            "scene": "06",
            "start": 51.0,
            "end": 51.0,
            "origin": "film.js:410",
            "module": "picture/film/scenes/p06/beats.js",
            "level": 132,
            "frames": 1,
            "paints": ["stroke"],
            "texts": [],
        },
    ],
    "speeds": {
        "02": {"flow": {"speed": 240, "t": 12.2}},
        "03": {"glide": {"speed": 1200, "t": 40.1}},
    },
}


@pytest.fixture
def gated(root, put):
    """The edition's current composition, timeline and a gate record bound to them."""
    edition = Edition("zh")
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition")
    put(edition.timeline, {"segments": []})
    report = put(root / "build/runtime/work/picture-gates/zh/motion.json", {"followed": FOLLOWED})
    put(
        edition.picture_gates,
        {
            "composition_sha256": repository.sha(root / picture_rendering.COMPOSITION_SCRIPT),
            "timeline_sha256": repository.sha(edition.timeline),
            "reports": {
                "motion": {"path": repository.relative(report), "sha256": repository.sha(report)}
            },
            "recorded_findings": [
                "motion halt 02 12.30 s: fill falls from 240 px/s to rest, drawn at film.js:120;"
                " declared: a stamp",
                "motion pop in 06 51.00 s: stroke at ink 132 appears within one frame, drawn at"
                " film.js:410 (picture/film/scenes/p06/beats.js); declared: a beat",
                "sync held over 02.2 2.85 s",
            ],
            "verdict": "pass",
        },
    )
    return edition, report


def test_the_measurement_reports_each_edition_s_motion_from_its_gate(gated):
    edition, _ = gated
    assert review_motion.picture_motion(edition) == {
        "method": review_motion.METHOD,
        "counts": {"halts": 2, "starts": 0, "races": 1, "pops": 1},
        "findings": 3,
        "declared": 2,
        "speeds": FOLLOWED["speeds"],
        "largest": {
            "flow": {"speed": 240, "t": 12.2, "scene": "02"},
            "glide": {"speed": 1200, "t": 40.1, "scene": "03"},
        },
        "events": FOLLOWED["findings"],
    }


def test_a_gate_record_or_report_bound_to_other_inputs_is_refused(gated, put, root):
    edition, report = gated
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition changed")
    with pytest.raises(
        ReviewError, match="zh: the picture gate record is not bound to the current composition"
    ):
        review_motion.picture_motion(edition)
    put(root / picture_rendering.COMPOSITION_SCRIPT, "composition")
    put(report, {"followed": {**FOLLOWED, "halts": []}})
    with pytest.raises(
        ReviewError, match="zh: the motion report differs from the one its gate record binds"
    ):
        review_motion.picture_motion(edition)
    report.unlink()
    with pytest.raises(
        ReviewError, match="missing build/runtime/work/picture-gates/zh/motion.json"
    ):
        review_motion.picture_motion(edition)
    edition.picture_gates.unlink()
    with pytest.raises(ReviewError, match="missing build/evidence/editions/zh/picture-gates.json"):
        review_motion.picture_motion(edition)


def test_the_edition_s_measurements_carry_its_motion_beside_its_sync(gated, monkeypatch):
    edition, _ = gated
    monkeypatch.setattr(review_measurement, "picture_sync", lambda *arguments: {"sync": True})
    monkeypatch.setattr(review_measurement, "picture_geometry", lambda *arguments: {"geometry": 1})
    measured = review_measurement.picture_measures(edition, repository.sha(edition.timeline))
    assert measured == {
        "picture": {"geometry": 1},
        "picture_sync": {"sync": True},
        "picture_motion": review_motion.picture_motion(edition),
    }
