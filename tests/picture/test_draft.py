"""The draft render: the edition's captioned picture staged afresh at 1080p, drawn at 10 fps in
one process at a lower scheduling priority, and scanned into the record the pre-render check
reads."""

import json
import os
import subprocess
import sys

import numpy as np
import pytest
import still_records

import filmkit.picture.draft as picture_draft
import filmkit.picture.encoding as encoding
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.picture.still_scan as still_scan
import filmkit.preflight as preflight
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition
from filmkit.specification import DURATION

# What the engine's renderer names itself as in a draft's receipt and record.
DREW = {
    "package": picture_renderer.RENDERER_NAME,
    "version": picture_renderer.RENDERER_VERSION,
    "text_renderer": picture_renderer.TEXT_RENDERER,
}


def draft_command(stage, draft):
    """The draft's command after the renderer's launcher: one process at 10 fps, the pictures'
    encoding with a keyframe every two seconds, the host's text renderer."""
    work = stage.with_name(stage.name + "-spans")
    return [
        *["render", str(stage), "--output", str(draft), "--fps", "10", "--group", "20"],
        *["--encoder", json.dumps(encoding.encoder(10)), "--text-renderer", "system"],
        *["--spans", "1"],
        *["--work", str(work), "--report", str(work.with_name(work.name + ".json"))],
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
    """Have the scan read these frames from any draft at either phase, and after them frames
    that keep moving to the end of the film's seconds: a draft is read whole."""

    def read(_movie, _phase):
        shown = frames(moving, still)
        yield from shown
        for k in range(DURATION * picture_draft.DRAFT_FPS - len(shown)):
            yield np.roll(shown[0], 7 * (k + 1), axis=1)

    monkeypatch.setattr(still_scan, "frame_rate", lambda _movie: picture_draft.DRAFT_FPS)
    monkeypatch.setattr(still_scan, "decode", read)


def places(code="zh"):
    """The draft's stage, its file and its receipt, below the film's root."""
    work = repository.ROOT / "build/runtime/work/picture-draft"
    receipt = repository.ROOT / f"build/evidence/editions/{code}/render/receipt-draft.json"
    return work / code, work / f"{code}.mp4", receipt


def test_a_draft_is_staged_afresh_and_drawn_in_one_process(film_root, monkeypatch):
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
    assert members == sorted([*declared, "film.json", "index.html", "stage.json"])
    receipt = repository.read(receipt_path)
    assert receipt["command"][:2] == ["nice", "-n"]
    assert receipt["command"][3:] == [str(film_root.renderer), *draft_command(stage, draft)]
    assert [run["argv"] for run in film_root.runs()] == [draft_command(stage, draft)]
    assert (receipt["picture"], receipt["spans"], receipt["exit"]) == ("draft", 1, 0)
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


@pytest.mark.ffmpeg
def test_the_draft_scan_lands_where_preflight_reads_it(film_root, tmp_path):
    edition = Edition("zh")
    film_root.timeline(edition, words=[{"text": "先看", "start": 1.0, "end": 2.0}])
    # The stand-in draft holds the film's seconds, as the timeline it is scanned against states
    # them: its square moves for four seconds and then stands, under no speech.
    whole = DURATION * picture_draft.DRAFT_FPS
    movie = tmp_path / "moving.mp4"
    grey = f"{still_scan.WIDTH}x{still_scan.HEIGHT}"
    encode = ["ffmpeg", "-v", "error", "-nostdin", "-f", "rawvideo", "-pix_fmt", "gray"]
    encode += ["-s", grey, "-r", "10", "-i", "-", "-c:v", "libx264", "-qp", "0", str(movie)]
    pixels = b"".join(frame.tobytes() for frame in frames(40, whole - 40))
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
    assert (record["frames"], record["over_limit"]) == (whole, [])
    # The record names what drew the draft, as the draft's receipt does, and admits a render
    # only by that renderer: a record of a browser's draft, which names none, does not.
    assert record["drawn_by"] == DREW
    assert preflight.draft(edition) is None
    for other in (None, {**DREW, "text_renderer": "portable"}, {**DREW, "version": "1.0.0"}):
        repository.write(edition.draft_stills, {**record, "drawn_by": other})
        assert preflight.draft(edition) == (
            "build/evidence/editions/zh/draft-stills.json scanned a draft that another "
            "renderer drew; render the draft again"
        )


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
    monkeypatch.setattr(picture_renderer, "STOP_GRACE_SECONDS", 0.5)
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
    repository.write(edition.draft_stills, still_records.draft_stills(edition))
    repository.write(places(edition.code)[2], {"picture": "draft", "exit": 0})
    assert preflight.draft(edition) is None


def test_a_draft_refused_before_it_renders_leaves_no_earlier_record(film_root):
    edition = Edition("zh")
    earlier(edition)
    manifest = film_root.path / "node_modules" / picture_renderer.RENDERER_PACKAGE
    manifest.write_text('{"name": "@napi-rs/canvas", "version": "0.0.1"}')
    with pytest.raises(PictureError, match="installs @napi-rs/canvas 0.0.1"):
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
        "The zh draft holds a still picture with 3.5 s of speech or more: 0.90-5.90 s with "
        "4.00 s of speech; see build/evidence/editions/zh/draft-stills.json"
    )
    with pytest.raises(PictureError, match=f"^{named}$"):
        picture_draft.render_draft(edition, 60)
    record = repository.read(edition.draft_stills)
    assert record["over_limit"] == [{"start": 0.9, "end": 5.9, "speech": 4.0}]
    assert preflight.draft(edition) == (
        "build/evidence/editions/zh/draft-stills.json finds 1 still pictures with 3.5 s of speech "
        "or more"
    )


def test_the_limit_has_one_wording_which_the_draft_the_pre_render_check_and_the_scan_ask(
    film_root, monkeypatch
):
    edition = Edition("zh")
    film_root.timeline(edition, words=[{"text": "先看数据", "start": 1.0, "end": 5.0}])
    scanning(monkeypatch, 10, 50)
    # Worded otherwise in its one place (`still_scan.limit_words`), the limit reads so in the
    # draft's refusal, in the pre-render check's answer and in the scan's own refusal.
    monkeypatch.setattr(still_scan, "limit_words", lambda limit=None: f"<{limit}>")
    with pytest.raises(PictureError, match="^The zh draft holds a still picture with <3.5>: "):
        picture_draft.render_draft(edition, 60)
    assert preflight.draft(edition) == (
        "build/evidence/editions/zh/draft-stills.json finds 1 still pictures with <None>"
    )
    with pytest.raises(PictureError, match="^The zh film holds a still picture with <None>: "):
        still_scan.refuse_still_pictures(edition, repository.read(edition.draft_stills))
