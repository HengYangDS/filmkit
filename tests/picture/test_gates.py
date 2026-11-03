"""The picture's gate before a render: the gated findings of the audits and the record they bind."""

import json
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.picture.gates as gates
import filmkit.repository as repository
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError
from filmkit.production import Edition

# Reports of a clean picture: no gated frame finding, every label in sync, no long still.
CLEAN = {
    "frame": {
        **dict.fromkeys(gates.FRAME_GATES, {}),
        "errors": [],
        "overlaps": [],
        "frames_checked": 301,
        "caption_echoes": {"03": ["a name@4.0"]},
    },
    "sync": {"findings": [], "out_of_sync": 0, "labels_judged": 12},
    "motion": {"still": [{"start": 4.0, "end": 7.2, "seconds": 3.2}], "pops": [1]},
}


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root with a composition and the Chinese edition's timeline."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    put(root / COMPOSITION_SCRIPT, "scenes = {};\n")
    put(Edition("zh").timeline, {"segments": [], "captions": []})
    return root


def audits(monkeypatch, reports, *, change=None):
    """Stand in for the three audits: each writes its report from `reports`; `change` edits a
    file while the frame audit runs."""
    calls = []

    def run(tool, arguments, *, environment=None, stdout=None):
        calls.append((tool, arguments, environment))
        if tool == "frame-audit":
            put(stdout, reports["frame"])
            if change is not None:
                change()
        else:
            put(stdout, {"summary": True})
            put(Path(arguments[arguments.index("--out") + 1]), reports["motion"])
        return 0

    monkeypatch.setattr(gates.tools, "run", run)
    monkeypatch.setattr(gates.sync_audit, "full_report", lambda *arguments: reports["sync"])
    return calls


def test_a_clean_picture_writes_a_passing_record_of_what_it_checked(film, monkeypatch):
    edition = Edition("zh")
    calls = audits(monkeypatch, CLEAN)
    record = gates.check_picture(edition)
    assert repository.read(edition.picture_gates) == record
    assert record["verdict"] == "pass" and record["gated_findings"] == []
    assert record["composition_sha256"] == repository.sha(film / COMPOSITION_SCRIPT)
    assert record["timeline_sha256"] == repository.sha(edition.timeline)
    assert record["engine_version"] == version("filmkit")
    assert record["frames_checked"] == 301
    assert sorted(record["reports"]) == ["frame", "motion", "sync"]
    for report in record["reports"].values():
        assert report["sha256"] == repository.sha(film / report["path"])
    # The frame audit runs at one thirtieth of a second with its traces, the motion audit at
    # 30 frames per second, both on the edition's timeline.
    (frame_tool, frame_args, frame_env), (motion_tool, motion_args, _) = calls
    assert (frame_tool, frame_args) == ("frame-audit", [str(edition.timeline), "0.0333333"])
    assert sorted(frame_env) == ["MARKS", "TRACE"]
    assert (motion_tool, motion_args[:2]) == ("motion-audit", [str(edition.timeline), "30"])


@pytest.mark.parametrize(
    ("reports", "named"),
    [
        ({**CLEAN, "frame": {**CLEAN["frame"], "overlaps": [{"pair": "04:a|b"}]}}, "overlaps"),
        (
            {**CLEAN, "frame": {**CLEAN["frame"], "off_centre_runs": {"04": ["1.00-3.50 13.0%"]}}},
            "off_centre_runs",
        ),
        (
            {
                **CLEAN,
                "sync": {
                    "findings": [
                        {"scene": "05", "label": "ETHOS", "verdict": "after-words", "legible": 9.5}
                    ]
                },
            },
            "sync 05 ETHOS: after-words",
        ),
        (
            {**CLEAN, "motion": {"still": [{"start": 4.0, "end": 7.6, "seconds": 3.6}]}},
            "motion still 4.00-7.60 s",
        ),
    ],
)
def test_a_gated_finding_writes_a_refused_record_and_refuses(film, monkeypatch, reports, named):
    edition = Edition("zh")
    audits(monkeypatch, reports)
    with pytest.raises(PictureError, match=f"1 gated findings: .*{named}"):
        gates.check_picture(edition)
    record = repository.read(edition.picture_gates)
    assert record["verdict"] == "refuse"
    assert len(record["gated_findings"]) == 1 and named in record["gated_findings"][0]


def test_a_picture_changed_while_it_is_checked_is_refused(film, monkeypatch):
    edition = Edition("zh")
    audits(monkeypatch, CLEAN, change=lambda: put(film / COMPOSITION_SCRIPT, "changed"))
    with pytest.raises(PictureError, match="changed while it was checked"):
        gates.check_picture(edition)
    assert not edition.picture_gates.exists()


def test_a_failed_audit_is_refused_with_its_report(film, monkeypatch):
    monkeypatch.setattr(gates.tools, "run", lambda *arguments, **options: 1)
    with pytest.raises(PictureError, match="frame-audit exited with status 1"):
        gates.check_picture(Edition("zh"))
