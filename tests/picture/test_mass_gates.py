"""The picture gate on the content's balance.

Each run of the mass audit and each vertical run of the frame audit is refused by its scene, span
and offset, a role error with the frame audit's errors; the summaries stand in the bound reports,
and the gate record binds the uncaptioned stage the mass audit draws.
"""

import pytest
import staged_inputs
import test_gates
from test_gates import CLEAN, audits, put

import filmkit.picture.gates as gates
import filmkit.picture.rendering as rendering
import filmkit.repository as repository
from filmkit.picture import renderer
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError
from filmkit.production import STAGE_RECORD, Edition

# The gate's film root, as the gate's own tests build it.
film = test_gates.film


def frame(**found):
    """The clean reports with these frame findings."""
    return {**CLEAN, "frame": {**CLEAN["frame"], **found}}


@pytest.mark.usefixtures("film")
def test_a_mass_run_is_refused_by_its_scene_span_and_offset(monkeypatch):
    mass = {**CLEAN["mass"], "off_centre_mass": {"03": ["0.50-2.20 -120.0 px"]}}
    calls = audits(monkeypatch, {**CLEAN, "mass": mass})
    with pytest.raises(PictureError, match="1 gated findings"):
        gates.check_picture(Edition("zh"))
    record = repository.read(Edition("zh").picture_gates)
    assert record["verdict"] == "refuse"
    assert record["gated_findings"] == ["mass off_centre_mass 03: 0.50-2.20 -120.0 px"]
    # The mass audit draws the uncaptioned stage with the renderer's text renderer.
    stage = Edition("zh").rendered(captions=False).stage
    by_tool = {call[0]: call for call in calls}
    assert by_tool["mass-audit"][1] == [str(stage), "--text-renderer", renderer.TEXT_RENDERER]


@pytest.mark.parametrize(
    ("found", "named"),
    [
        (
            {"off_centre_vertical": {"02": ["0.50-3.00 80.0 px"]}},
            'frame off_centre_vertical: {"02": ["0.50-3.00 80.0 px"]}',
        ),
        (
            {"errors": [{"message": 'window.__paintRole is "frmae"', "t": 1.0}]},
            'frame errors: [{"message": "window.__paintRole is \\"frmae\\"", "t": 1.0}]',
        ),
    ],
)
@pytest.mark.usefixtures("film")
def test_a_vertical_run_and_a_role_error_are_refused(monkeypatch, found, named):
    audits(monkeypatch, frame(**found))
    with pytest.raises(PictureError, match="1 gated findings"):
        gates.check_picture(Edition("zh"))
    assert repository.read(Edition("zh").picture_gates)["gated_findings"] == [named]


def test_summaries_and_declared_frames_alone_pass_and_the_record_binds_the_stage(film, monkeypatch):
    edition = Edition("zh")
    summary = {"frames": 30, "faint": 2, "declared": 60, "median_dx": -60.0, "median_dy": 12.0}
    mass = {**CLEAN["mass"], "mass_balance": {"03": {**summary, "within": 0.9}}}
    declared = {"declared_frames": {"03": {"strokes": 2, "box": [198, 118, 1722, 921]}}}
    audits(monkeypatch, {**frame(**declared), "mass": mass})
    record = gates.check_picture(edition)
    assert record["verdict"] == "pass"
    assert record["gated_findings"] == []
    assert repository.read(film / record["reports"]["mass"]["path"]) == mass
    assert record["reports"]["mass"]["sha256"] == repository.sha(
        film / record["reports"]["mass"]["path"]
    )
    stage = edition.rendered(captions=False).stage / STAGE_RECORD
    assert record["uncaptioned_stage_sha256"] == repository.sha(stage)
    rendering.require_passing_gates(edition)
    # The stage staged again with other bytes after the check: the render waits for the check.
    put(stage, {"picture": "uncaptioned", "members": []})
    with pytest.raises(
        PictureError, match="binds another uncaptioned_stage_sha256; run filmkit build"
    ):
        rendering.require_passing_gates(edition)


@pytest.mark.usefixtures("film")
def test_an_uncaptioned_stage_not_yet_staged_is_refused_before_any_audit(monkeypatch):
    edition = Edition("zh")
    calls = audits(monkeypatch, CLEAN)
    gates.check_picture(edition)
    (edition.rendered(captions=False).stage / STAGE_RECORD).unlink()
    edition.picture_gates.unlink()
    calls.clear()
    words = (
        "No staged picture document and record in .*-uncaptioned; "
        "run filmkit build stage-picture-uncaptioned:zh"
    )
    with pytest.raises(PictureError, match=words):
        gates.check_picture(edition)
    assert calls == []
    assert not edition.picture_gates.exists()
    audits(monkeypatch, CLEAN)
    put(edition.picture_gates, {"verdict": "pass"})
    with pytest.raises(PictureError, match=words):
        rendering.require_passing_gates(edition)


@pytest.fixture
def staged(tmp_path, monkeypatch):
    """The Chinese edition with the real composition, both its pictures staged and checked."""
    staged_inputs.root(tmp_path, monkeypatch)
    return staged_inputs.staged()


def test_a_stale_uncaptioned_stage_is_refused_before_any_audit(staged, monkeypatch):
    # The composition changes and only the captioned picture is staged again: the mass audit would
    # measure the old picture beside a frame audit of the new one.
    calls = []
    monkeypatch.setattr(gates.tools, "run", lambda tool, *_, **__: calls.append(tool) or 0)
    script = repository.ROOT / COMPOSITION_SCRIPT
    script.write_text(script.read_text() + "\n// changed after staging\n")
    rendering.stage_picture(staged, None, staged_inputs.RUNTIME, 3840, 2160)
    staged.picture_gates.unlink()
    with pytest.raises(PictureError, match="differs"):
        gates.check_picture(staged)
    assert calls == []
    assert not staged.picture_gates.exists()
