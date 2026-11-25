"""The review's measurements of the picture: the sync report the picture gate judged and the
geometry of the current staged document, each refused where it is not of the current build."""

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.picture.sync_audit as picture_sync_audit
import filmkit.repository as repository
import filmkit.review.measurement as review_measurement
from filmkit.production import Edition
from filmkit.review import ReviewError


def test_the_measured_sync_is_the_report_the_picture_gate_judged(root, put):
    # The review reads unnamed speech, held pictures and seats from the measurements, and only
    # from the sync report that the gate record of the current timeline and composition binds.
    edition = Edition("zh")
    composition = put(root / picture_rendering.COMPOSITION_SCRIPT, "/* film */")
    timeline = put(edition.timeline, {"segments": []})
    continuity = {"unnamed_speech": [], "held_over": [], "seats": []}
    judged = dict.fromkeys(picture_sync_audit.SUMMARY_KEYS, 0)
    judged |= {"findings": [], "continuity": continuity}
    report = put(root / "build/runtime/work/picture-gates/zh/sync.json", judged | {"judged": []})
    record = {
        "composition_sha256": repository.sha(composition),
        "timeline_sha256": repository.sha(timeline),
        "reports": {
            "sync": {"path": repository.relative(report), "sha256": repository.sha(report)}
        },
    }
    put(edition.picture_gates, record)
    # A gated edition is measured from the gate's report; no separate sync record exists.
    assert not (edition.evidence / "picture-sync.json").exists()
    assert review_measurement.picture_sync(edition) == judged

    def refusal():
        with pytest.raises(ReviewError) as refused:
            review_measurement.picture_sync(edition)
        return str(refused.value)

    put(timeline, {"segments": [], "moved": True})
    assert refusal() == "zh: the picture gate record is not bound to the current timeline"
    put(timeline, {"segments": []})
    put(composition, "/* another film */")
    assert refusal() == "zh: the picture gate record is not bound to the current composition"
    put(composition, "/* film */")
    put(report, judged | {"judged": [], "tolerance": 0.5})
    assert refusal() == "zh: the sync report differs from the one its gate record binds"
    # A report cleared from the gate's work folder, a record that binds none and an edition that
    # was never gated each refuse in one line that names the command to run.
    report.unlink()
    assert refusal() == (
        "zh: missing build/runtime/work/picture-gates/zh/sync.json, the sync report its gate "
        "record binds; run check-picture again"
    )
    put(edition.picture_gates, record | {"reports": {"motion": record["reports"]["sync"]}})
    assert refusal() == "zh: the picture gate record binds no sync report; run check-picture again"
    edition.picture_gates.unlink()
    assert refusal() == (
        "zh: missing build/evidence/editions/zh/picture-gates.json, the picture gate record; "
        "run check-picture"
    )


@pytest.mark.usefixtures("root")
def test_the_measured_geometry_checks_the_current_staged_document(put):
    edition = Edition("en")
    staged = put(edition.rendered().page, "<!doctype html>")
    geometry = {
        "checked": 45000,
        "step_frames": 2,
        "findings": [],
        "errors": [],
        "browser": "Chrome",
        "index_sha256": repository.sha(staged),
    }
    put(edition.picture_geometry, geometry)
    assert review_measurement.picture_geometry(edition) == {
        "geometry_frames_checked": 45000,
        "step_frames": 2,
        "findings": 0,
        "errors": 0,
        "browser": "Chrome",
        "index_sha256": repository.sha(staged),
    }
    put(staged, "<!doctype html><title>Restaged</title>")
    with pytest.raises(
        ReviewError, match="en: the picture geometry does not check the current stage"
    ):
        review_measurement.picture_geometry(edition)
