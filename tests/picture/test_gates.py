"""The picture's gate before a render: the gated findings of the audits and the record they bind."""

import json
import shutil
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.picture.gates as gates
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.metrics import VARIABLE
from filmkit.picture.rendering import COMPOSITION_SCRIPT, STYLE, PictureError
from filmkit.production import Edition

# The sample film, whose stylesheet and fonts the gate's film declares.
SAMPLE = Path(__file__).resolve().parents[2] / "examples/sample-film"

# Reports of a clean picture: no gated frame finding, every label in sync, no long still.
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
    "motion": {"still": [{"start": 4.0, "end": 7.2, "seconds": 3.2}], "pops": [1]},
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


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root with a composition, the sample film's stylesheet and fonts, and the Chinese
    edition's timeline."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    put(root / COMPOSITION_SCRIPT, "scenes = {};\n")
    for path in (STYLE, *FILM.picture.fonts):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE / path, root / path)
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
    assert record["recorded_findings"] == []
    assert record["composition_sha256"] == repository.sha(film / COMPOSITION_SCRIPT)
    assert record["timeline_sha256"] == repository.sha(edition.timeline)
    assert record["engine_version"] == version("filmkit")
    # The audits measure text by the faces the stylesheet declares from these fonts.
    assert record["stylesheet_sha256"] == repository.sha(film / STYLE)
    assert record["fonts_sha256"] == {
        font: repository.sha(film / font) for font in FILM.picture.fonts
    }
    assert record["frames_checked"] == 301
    assert sorted(record["reports"]) == ["frame", "motion", "sync"]
    for report in record["reports"].values():
        assert report["sha256"] == repository.sha(film / report["path"])
    # The frame audit runs at one thirtieth of a second with its traces, the motion audit at
    # 30 frames per second, both on the edition's timeline.
    (frame_tool, frame_args, frame_env), (motion_tool, motion_args, motion_env) = calls
    assert (frame_tool, frame_args) == ("frame-audit", [str(edition.timeline), "0.0333333"])
    assert sorted(frame_env) == [VARIABLE, "MARKS", "TRACE"]
    assert (motion_tool, motion_args[:2]) == ("motion-audit", [str(edition.timeline), "30"])
    assert motion_env == {VARIABLE: frame_env[VARIABLE]}
    table = repository.read(Path(frame_env[VARIABLE]))
    assert sorted(table["faces"]) == ["Sample", "SampleBold", "SampleLatin", "SampleLatinBold"]
    assert table["fonts_sha256"] == record["fonts_sha256"]


@pytest.mark.parametrize(
    ("reports", "named"),
    [
        ({**CLEAN, "frame": {**CLEAN["frame"], "overlaps": [{"pair": "04:a|b"}]}}, "overlaps"),
        (
            {**CLEAN, "frame": {**CLEAN["frame"], "off_centre_runs": {"04": ["1.00-3.50 13.0%"]}}},
            "off_centre_runs",
        ),
        (
            {**CLEAN, "frame": {**CLEAN["frame"], "ragged_rows": {"02": [RAGGED_ROW]}}},
            "frame ragged_rows",
        ),
        (
            {
                **CLEAN,
                "frame": {**CLEAN["frame"], "off_centre_builds": {"04": ["1.00-2.60 -120.0 px"]}},
            },
            "frame off_centre_builds",
        ),
        (
            {
                **CLEAN,
                "frame": {
                    **CLEAN["frame"],
                    "uneven_pitch": {
                        "03": [
                            {
                                "start": 2.0,
                                "end": 4.5,
                                "texts": ["A", "B", "C"],
                                "pitch": [168.4, 184.6],
                                "gaps": [100.0, 100.0],
                            }
                        ]
                    },
                },
            },
            "frame uneven_pitch",
        ),
        (
            {
                **CLEAN,
                "sync": {
                    **CLEAN["sync"],
                    "findings": [
                        {"scene": "05", "label": "ETHOS", "verdict": "after-words", "legible": 9.5}
                    ],
                },
            },
            "sync 05 ETHOS: after-words",
        ),
        (
            {**CLEAN, "motion": {"still": [{"start": 4.0, "end": 7.6, "seconds": 3.6}]}},
            "motion still 4.00-7.60 s",
        ),
        (
            continuity(
                seats=[{"thought": "03.2", "at": 153.167, "lag": 2.13, "box": [1, 2, 3, 4]}]
            ),
            "sync seat 03.2 at 153.17 s: a mark waits 2.13 s for its name",
        ),
        (
            continuity(unnamed_speech=[{"thought": "03.7", "from": 260.823, "to": 262.456}]),
            "sync unnamed speech 03.7 260.82-262.46 s",
        ),
        (
            continuity(caption_echoes=[{**ECHO, "whole": True, "share": 1.0, "labels": ["x"]}]),
            "sync caption echo 717.70 s: one label repeats",
        ),
        (
            {**CLEAN, "frame": {**CLEAN["frame"], "mixed_case": {"08": [RAGGED_ROW]}}},
            "frame mixed_case",
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


def test_a_still_state_off_centre_is_recorded_and_refuses_nothing(film, monkeypatch):
    # Whether a still state is a settled composition or a build-up waiting for its next parts
    # only the stage's intent tells, so the reviewers judge it from the record.
    frame = {**CLEAN["frame"], "off_centre_settled": {"09": ["0.50-3.00 60.0 px"]}}
    audits(monkeypatch, {**CLEAN, "frame": frame})
    record = gates.check_picture(Edition("zh"))
    assert record["verdict"] == "pass" and record["gated_findings"] == []
    assert record["recorded_findings"] == [
        'frame off_centre_settled: {"09": ["0.50-3.00 60.0 px"]}'
    ]
    assert set(gates.FRAME_RECORDED).isdisjoint(gates.FRAME_GATES)


def test_a_held_picture_and_a_partial_echo_are_recorded_and_refuse_nothing(film, monkeypatch):
    # A deliberate index may stay while the first new name arrives, and labels may name the marks
    # whose words a cue says; the reviewers judge both from the record.
    labels = ["The people watching the pipeline", "report this back"]
    echo = {**ECHO, "whole": False, "share": 1.0, "labels": labels}
    reports = continuity(held_over=[{"thought": "02.2", "held": 2.85}], caption_echoes=[echo])
    audits(monkeypatch, reports)
    record = gates.check_picture(Edition("zh"))
    assert record["verdict"] == "pass" and record["gated_findings"] == []
    assert record["recorded_findings"] == [
        "sync held over 02.2 2.85 s",
        "sync caption echo 717.70 s: labels repeat 100% of "
        "'The people watching the pipeline report this back,'",
    ]


def test_a_quoted_cue_drawn_whole_is_recorded_as_a_quotation(film, monkeypatch):
    # The narration reads out the document the picture shows; the reviewers judge it.
    text = "“Deduplicate by stock code and date.”"
    label = "Deduplicate by stock code and date"
    echo = {**ECHO, "text": text, "whole": False, "quoted": True, "share": 1.0, "labels": [label]}
    audits(monkeypatch, continuity(caption_echoes=[echo]))
    record = gates.check_picture(Edition("zh"))
    assert record["verdict"] == "pass" and record["gated_findings"] == []
    assert record["recorded_findings"] == [
        f"sync caption echo 717.70 s: labels repeat 100% of {text!r}, a quotation the picture shows"
    ]


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
