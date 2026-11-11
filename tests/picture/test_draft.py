"""The draft render: the edition's captioned picture staged afresh at 1080p, rendered at 10 fps in
draft quality at a lower scheduling priority, and scanned into the record the pre-render check
reads."""

import os
import subprocess
import sys

import numpy as np
import pytest

import filmkit.picture.draft as picture_draft
import filmkit.picture.rendering as picture_rendering
import filmkit.picture.still_scan as still_scan
import filmkit.preflight as preflight
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition
from filmkit.specification import DURATION

# A draft record and receipt that an earlier draft left, bound to the current inputs.
EARLIER = {"over_limit": [], "limit_seconds": 3.5, "movie": {"path": "earlier.mp4"}}


def lanes_command(stage, draft, capture="--experimental-fast-capture", browser="--browser-gpu"):
    """The film lanes' draft.py command after the renderer's path."""
    return [
        "render",
        str(stage),
        "--output",
        str(draft),
        "--fps",
        "10",
        "--quality",
        "draft",
        "--workers",
        "8",
        "--gpu",
        browser,
        "--no-low-memory-mode",
        capture,
        "--strict",
    ]


def frames(moving, still):
    """480x270 grey frames of a bright square that moves for `moving` frames and then stands for
    `still` more, as the scan reads a draft."""
    out = []
    for k in range(moving + still):
        frame = np.full((still_scan.HEIGHT, still_scan.WIDTH), 15, dtype=np.uint8)
        x = 100 + 5 * min(k, moving - 1)
        frame[100:120, x : x + 20] = 200
        out.append(frame)
    return out


def scanning(monkeypatch, moving, still):
    """Have the scan read these frames from any draft at either phase."""
    monkeypatch.setattr(still_scan, "decode", lambda _movie, _phase: iter(frames(moving, still)))


def places(code="zh"):
    """The draft's stage, its file and its receipt, below the film's root."""
    work = repository.ROOT / "build/runtime/work/picture-draft"
    receipt = repository.ROOT / f"build/evidence/editions/{code}/render/receipt-draft.json"
    return work / code, work / f"{code}.mp4", receipt


def test_a_draft_is_staged_afresh_and_rendered_as_the_lanes_render_it(film_root, monkeypatch):
    scanning(monkeypatch, 40, 0)
    stage, draft, receipt_path = places()
    retired = stage / "fonts/retired-font.otf"
    retired.parent.mkdir(parents=True)
    retired.write_text("a font the declaration no longer names")
    picture_draft.render_draft(Edition("zh"), 60)
    assert not retired.exists()
    record = repository.read(stage / "stage.json")
    assert (record["width"], record["height"], record["duration"]) == (1920, 1080, DURATION)
    assert (record["start"], record["picture"]) == (0, "captioned")
    members = sorted(str(path.relative_to(stage)) for path in stage.rglob("*") if path.is_file())
    declared = [path for path, _ in picture_rendering.staged_members()]
    assert members == sorted([*declared, "index.html", "stage.json"])
    receipt = repository.read(receipt_path)
    assert receipt["command"][:2] == ["nice", "-n"]
    assert receipt["command"][3:] == [str(film_root.renderer), *lanes_command(stage, draft)]
    assert [run["argv"] for run in film_root.runs()] == [lanes_command(stage, draft)]
    assert (receipt["picture"], receipt["capture"], receipt["exit"]) == ("draft", "fast", 0)
    assert (receipt["timed_out"], receipt["deadline_seconds"]) == (False, 60)
    assert receipt["source_sha256"] == repository.sha(stage / "index.html")
    assert receipt["output_sha256"] == repository.sha(draft)


def test_the_draft_renders_at_niceness_10_or_the_callers_with_its_input_closed_in_its_session(
    film_root, monkeypatch
):
    scanning(monkeypatch, 40, 0)
    picture_draft.render_draft(Edition("zh"), 60)
    (run,) = film_root.runs()
    caller = os.getpriority(os.PRIO_PROCESS, 0)
    assert run["niceness"] == max(caller, 10)
    assert (run["stdin"], run["session_leader"]) == ("", True)


@pytest.mark.parametrize(
    ("capture", "browser"), [("screenshot", "--browser-gpu"), ("software", "--no-browser-gpu")]
)
def test_the_draft_honours_the_declared_capture(film_root, monkeypatch, capture, browser):
    scanning(monkeypatch, 40, 0)
    picture = FILM.picture.model_copy(update={"capture": capture})
    monkeypatch.setattr(picture_rendering, "FILM", FILM.model_copy(update={"picture": picture}))
    picture_draft.render_draft(Edition("en"), 60)
    stage, draft, receipt_path = places("en")
    off = lanes_command(stage, draft, "--experimental-fast-capture=false", browser)
    assert [run["argv"] for run in film_root.runs()] == [off]
    assert repository.read(receipt_path)["capture"] == capture


@pytest.mark.ffmpeg
def test_the_draft_scan_lands_where_preflight_reads_it(film_root, tmp_path):
    edition = Edition("zh")
    film_root.timeline(edition, words=[{"text": "先看", "start": 1.0, "end": 2.0}])
    movie = tmp_path / "moving.mp4"
    grey = f"{still_scan.WIDTH}x{still_scan.HEIGHT}"
    encode = ["ffmpeg", "-v", "error", "-nostdin", "-f", "rawvideo", "-pix_fmt", "gray"]
    encode += ["-s", grey, "-r", "10", "-i", "-", "-c:v", "libx264", "-qp", "0", str(movie)]
    pixels = b"".join(frame.tobytes() for frame in frames(40, 0))
    subprocess.run(encode, input=pixels, check=True, capture_output=True, timeout=60)
    _, draft, _ = places()
    film_root.queue(draft, movie)
    picture_draft.render_draft(edition, 60)
    record = repository.read(edition.draft_stills)
    assert record["movie"] == {
        "path": "build/runtime/work/picture-draft/zh.mp4",
        "sha256": repository.sha(draft),
    }
    assert record["timeline"]["sha256"] == repository.sha(edition.timeline)
    composition = repository.sha(repository.ROOT / picture_rendering.COMPOSITION_SCRIPT)
    assert record["composition"]["sha256"] == composition
    assert (record["frames"], record["over_limit"]) == (40, [])
    assert preflight.draft(edition) is None


@pytest.mark.parametrize(
    ("body", "deadline", "ends"),
    [
        ("raise SystemExit(3)", 60, {"exit": 3, "timed_out": False}),
        ("import time\ntime.sleep(60)", 1, {"exit": None, "timed_out": True}),
    ],
)
def test_a_draft_that_does_not_complete_writes_its_receipt_and_no_scan(
    film_root, monkeypatch, body, deadline, ends
):
    monkeypatch.setattr(picture_rendering, "STOP_GRACE_SECONDS", 0.5)
    film_root.renderer.write_text(f"#!{sys.executable}\n{body}\n")
    scanning(monkeypatch, 40, 0)
    edition = Edition("zh")
    _, draft, receipt_path = places()
    draft.parent.mkdir(parents=True)
    draft.write_text("an earlier draft")
    earlier(edition)
    with pytest.raises(PictureError, match="did not complete"):
        picture_draft.render_draft(edition, deadline)
    receipt = repository.read(receipt_path)
    assert {key: receipt[key] for key in ends} == ends
    assert (receipt["deadline_seconds"], receipt["output_sha256"]) == (deadline, None)
    assert not draft.exists()
    assert not edition.draft_stills.exists()


def earlier(edition):
    """Leave an earlier draft's record, bound to the current timeline and composition, and its
    receipt."""
    composition = repository.sha(repository.ROOT / picture_rendering.COMPOSITION_SCRIPT)
    bound = {"timeline": {"sha256": repository.sha(edition.timeline)}}
    repository.write(
        edition.draft_stills, {**EARLIER, **bound, "composition": {"sha256": composition}}
    )
    repository.write(places(edition.code)[2], {"picture": "draft", "exit": 0})
    assert preflight.draft(edition) is None


def test_a_draft_refused_before_it_renders_leaves_no_earlier_record(film_root):
    edition = Edition("zh")
    earlier(edition)
    manifest = film_root.path / "node_modules" / picture_rendering.RENDERER_PACKAGE
    manifest.write_text('{"name": "hyperframes", "version": "0.0.1"}')
    with pytest.raises(PictureError, match="installs HyperFrames 0.0.1"):
        picture_draft.render_draft(edition, 60)
    assert not edition.draft_stills.exists()
    assert not places()[2].exists()
    assert preflight.draft(edition) == (
        "no still scan of the 10 fps draft at build/evidence/editions/zh/draft-stills.json"
    )


def test_a_draft_with_a_still_picture_is_recorded_and_refused(film_root, monkeypatch):
    # The square stops after 0.9 s; the picture then stands for 5 s, 4 s of them under speech.
    edition = Edition("zh")
    film_root.timeline(edition, words=[{"text": "先看数据", "start": 1.0, "end": 5.0}])
    scanning(monkeypatch, 10, 50)
    named = (
        "The zh draft holds a still picture over 3.5 s of speech: 0.90-5.90 s with 4.00 s of "
        "speech; see build/evidence/editions/zh/draft-stills.json"
    )
    with pytest.raises(PictureError, match=f"^{named}$"):
        picture_draft.render_draft(edition, 60)
    record = repository.read(edition.draft_stills)
    assert record["over_limit"] == [{"start": 0.9, "end": 5.9, "speech": 4.0}]
    assert preflight.draft(edition) == (
        "build/evidence/editions/zh/draft-stills.json finds 1 still pictures over 3.5 s of speech"
    )
