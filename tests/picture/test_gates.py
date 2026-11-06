"""The picture's gate before a render: the gated findings of the audits and the record they bind."""

import json
import shutil
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.picture.gates as gates
import filmkit.repository as repository
from filmkit.film import FILM, Wrapping
from filmkit.picture.metrics import VARIABLE
from filmkit.picture.rendering import COMPOSITION_SCRIPT, STYLE, PictureError
from filmkit.production import Edition

# The sample film, whose stylesheet and fonts the gate's film declares.
SAMPLE = Path(__file__).resolve().parents[2] / "examples/sample-film"


def opening(title, seconds, *, contrast=15.6, step=1 / 30):
    """Text trace rows of a title card shown from the start for `seconds`."""
    return "".join(
        f"{k * step:.2f}\t\ttitle\t{contrast:.3f}\t1.000\t{title}\n"
        for k in range(round(seconds / step))
    )


# Reports of a clean picture: no gated frame finding, every label in sync, no long still, and a
# title card through the 2 s before the first word.
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
    "texts": opening("示例影片", 2.0),
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
    segment = {"id": "01", "words": [{"text": "构建", "start": 2.0, "end": 2.4}]}
    put(Edition("zh").timeline, {"title": "示例影片", "segments": [segment], "captions": []})
    return root


def audits(monkeypatch, reports, *, change=None):
    """Stand in for the three audits: each writes its report from `reports`; `change` edits a
    file while the frame audit runs."""
    calls = []

    def run(tool, arguments, *, environment=None, stdout=None):
        calls.append((tool, arguments, environment))
        if tool == "frame-audit":
            put(stdout, reports["frame"])
            put(Path(environment["TEXTS"]), reports["texts"])
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
    assert sorted(record["reports"]) == ["frame", "motion", "sync", "texts"]
    for report in record["reports"].values():
        assert report["sha256"] == repository.sha(film / report["path"])
    # The frame audit runs at one thirtieth of a second with its traces, the motion audit at
    # 30 frames per second, both on the edition's timeline.
    (frame_tool, frame_args, frame_env), (motion_tool, motion_args, motion_env) = calls
    assert (frame_tool, frame_args) == ("frame-audit", [str(edition.timeline), "0.0333333"])
    assert sorted(frame_env) == [VARIABLE, gates.WRAPPING_VARIABLE, "MARKS", "TEXTS", "TRACE"]
    # The frame audit judges wrapped labels by the declared shares and lead words.
    rules = repository.read(Path(frame_env[gates.WRAPPING_VARIABLE]))
    assert rules == {"line_share": 0.8, "last_share": 0.6, "lead_words": []}
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
        (
            {**CLEAN, "frame": {**CLEAN["frame"], "wrapped_labels": {"10": [BROKEN]}}},
            BROKEN_FINDING,
        ),
        (
            {**CLEAN, "texts": opening("示例", 2.0)},
            "text title '示例影片' shown 0.00 s before the first word at 2.00 s; "
            "never shown: 影, 片",
        ),
        (
            {
                **CLEAN,
                "texts": CLEAN["texts"]
                + "".join(f"{3 + k / 30:.2f}\t02\tlabel\t3.340\t0.580\t音轨\n" for k in range(30)),
            },
            "text contrast 02 '音轨' 3.00-4.00 s at 3.34:1",
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


def declaring(monkeypatch, **wrapping):
    """Stand in for the film's declaration with these wrapping rules."""
    picture = FILM.picture.model_copy(update={"wrapping": Wrapping(**wrapping)})
    monkeypatch.setattr(gates, "FILM", FILM.model_copy(update={"picture": picture}))


def test_wrapped_labels_are_judged_by_the_declared_rules_and_refused_by_name(film, monkeypatch):
    # A label that breaks no rule, and one that never stands at rest, refuse nothing.
    clean = wrapped(["A trade", "on the market"], [])
    entering = {**wrapped(["Bias may hide", "elsewhere"], []), "at": None}
    later = wrapped(["Rollback or", "degradation"], ['line 1 ends on the lead word "or"'], 30.5)
    labels = {"11": [later], "10": [clean, BROKEN, entering]}
    calls = audits(monkeypatch, {**CLEAN, "frame": {**CLEAN["frame"], "wrapped_labels": labels}})
    declaring(monkeypatch, line_share=0.75, last_share=0.5, lead_words=["versus"])
    with pytest.raises(PictureError, match="2 gated findings"):
        gates.check_picture(Edition("zh"))
    record = repository.read(Edition("zh").picture_gates)
    assert record["gated_findings"] == [
        BROKEN_FINDING,
        'frame wrapped label 11 "Rollback or" / "degradation" at rest 30.50 s: '
        'line 1 ends on the lead word "or"',
    ]
    rules = repository.read(Path(calls[0][2][gates.WRAPPING_VARIABLE]))
    assert rules == {"line_share": 0.75, "last_share": 0.5, "lead_words": ["versus"]}


def test_a_declared_exception_is_recorded_with_its_reason_and_a_stale_one_refuses(
    film, monkeypatch
):
    frame = {**CLEAN["frame"], "wrapped_labels": {"10": [BROKEN]}}
    audits(monkeypatch, {**CLEAN, "frame": frame})
    reason = "the market names the venue the narration quotes"
    kept = {"edition": "zh", "lines": ["A trade in", "the market"], "reason": reason}
    # An exception of the other edition is judged in its own edition only.
    other = {"edition": "en", "lines": ["Stated", "assumptions"], "reason": "a term"}
    declaring(monkeypatch, exceptions=[kept, other])
    record = gates.check_picture(Edition("zh"))
    assert record["verdict"] == "pass" and record["gated_findings"] == []
    assert record["recorded_findings"] == [f"{BROKEN_FINDING}; declared: {reason}"]
    # A label painted but never at rest is painted; lines no frame paints make a stale exception.
    entering = {**wrapped(["Bias may hide", "elsewhere"], []), "at": None}
    frame["wrapped_labels"]["12"] = [entering]
    painted = {**other, "edition": "zh", "lines": ["Bias may hide", "elsewhere"]}
    declaring(monkeypatch, exceptions=[kept, painted, {**other, "edition": "zh"}])
    with pytest.raises(PictureError, match="1 gated findings"):
        gates.check_picture(Edition("zh"))
    assert repository.read(Edition("zh").picture_gates)["gated_findings"] == [
        'frame wrapping exception "Stated" / "assumptions" is stale: no frame of the edition'
        " paints it"
    ]
