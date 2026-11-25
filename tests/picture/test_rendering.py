"""Render and bind the picture of a staged edition with fixture inputs and the real composition:
the receipt, a failed or late render, the renderer's version and the picture gate it asks."""

import contextlib
import json
import os
import platform
import re
import signal
import sys
import textwrap
import time
from pathlib import Path

import pytest
import staged_inputs
from staged_inputs import RUNTIME, passing_gates, put

import filmkit.picture.encoding as encoding
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.child_processes import MissingToolError
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import STAGE_RECORD
from filmkit.specification import FPS

RECEIPT_KEYS = [
    "picture",
    "command",
    "renderer",
    "operating_system",
    "spans",
    "frames",
    "drawn_sha256",
    "exit",
    "timed_out",
    "deadline_seconds",
    "started_at",
    "elapsed_seconds",
    "source_sha256",
    "output_path",
    "output_sha256",
]

# The film root of both editions' inputs, for every test here, and the staged Chinese edition.
root = pytest.fixture(autouse=True)(staged_inputs.root)
staged = pytest.fixture(staged_inputs.staged)


# What a stand-in renderer begins with: `report`, which writes the report the renderer command
# names, as the renderer does once it has drawn every frame.
# The native library a stand-in reports that it loaded: the pinned one.
LOADED = {
    "path": "/packages/@napi-rs/canvas-darwin-arm64/skia.darwin-arm64.node",
    "sha256": picture_renderer.BINARY_SHA256,
    "package": picture_renderer.BINARY_PACKAGE,
    "version": picture_renderer.RENDERER_VERSION,
}
REPORT = """
import json, sys
def report(**facts):
    said = {"frames": 1, "spans": 4, "text_renderer": "system", "drawn_sha256": "0" * 64}
    said["binary"] = LOADED
    with open(sys.argv[sys.argv.index("--report") + 1], "w") as file:
        json.dump({**said, **facts}, file)
""".replace("LOADED", json.dumps(LOADED))


def renderer(folder, body):
    """A stand-in renderer: an executable Python script that runs `body` after `REPORT`."""
    path = folder / "native-canvas"
    path.write_text(f"#!{sys.executable}\n{REPORT}{textwrap.dedent(body)}")
    path.chmod(0o755)
    return path


def render(monkeypatch, edition, fake, deadline):
    """Render an edition with a stand-in in place of the engine's renderer."""
    monkeypatch.setattr(picture_renderer, "launcher", lambda: [str(fake)])
    picture_rendering.render_picture(edition, deadline)


def completed_receipt(edition):
    """A receipt of a completed render of the current stage by the engine's renderer, beside its
    picture."""
    stage, picture = edition.picture_stage, edition.picture
    put(picture, "rendered picture")
    drawn_by = {
        "package": picture_renderer.RENDERER_NAME,
        "version": picture_renderer.RENDERER_VERSION,
        "text_renderer": picture_renderer.TEXT_RENDERER,
    }
    return {
        "command": ["node", "native-canvas.mjs", "render", str(stage), "--output", str(picture)],
        "renderer": drawn_by,
        "exit": 0,
        "timed_out": False,
        "source_sha256": repository.sha(edition.rendered().page),
        "output_path": str(picture),
        "output_sha256": repository.sha(picture),
    }


def gone(pid, wait=5.0):
    """Whether a process has exited and been reaped within `wait` seconds."""
    ends = time.monotonic() + wait
    while time.monotonic() < ends:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def test_a_completed_render_binds_only_the_current_stage(staged):
    edition = staged
    receipt = completed_receipt(edition)
    picture_rendering.validate_picture_binding(edition, receipt)
    # A failed, timed-out or misplaced render is refused by a named error, not an assert.
    for change in (
        {"exit": 1},
        {"timed_out": True},
        {"output_sha256": "0" * 64},
        {"output_path": "/elsewhere/build/artifacts/film/en/sample-reel-final-picture.mp4"},
        {"command": ["node", "native-canvas.mjs", "render", "/elsewhere/stage", "--output"]},
        # A picture that a browser drew, whose receipt names no canvas.
        {"renderer": None},
        {"renderer": {**receipt["renderer"], "text_renderer": "portable"}},
    ):
        with pytest.raises(PictureError):
            picture_rendering.validate_picture_binding(edition, {**receipt, **change})
    # A document edited after staging no longer derives from the current sources, even
    # when its render receipt names it.
    document = edition.rendered().page
    original = document.read_text()
    document.write_text(original.replace("<title>", "<title>Edited "))
    edited = {**receipt, "source_sha256": repository.sha(document)}
    with pytest.raises(PictureError, match="staged document differs"):
        picture_rendering.validate_picture_binding(edition, edited)
    document.write_text(original)
    picture_rendering.validate_picture_binding(edition, receipt)


def test_a_changed_template_or_copied_member_refuses_the_stage(staged, root):
    edition = staged
    receipt = completed_receipt(edition)
    template = root / picture_rendering.COMPOSITION / "index.html"
    original = template.read_text()
    template.write_text(original.replace("<title>", "<title>Changed "))
    with pytest.raises(PictureError, match="template_sha256"):
        picture_rendering.validate_picture_binding(edition, receipt)
    template.write_text(original)
    staged_font = f"fonts/{Path(FILM.picture.fonts[-1]).name}"
    (edition.picture_stage / staged_font).write_text("another font")
    with pytest.raises(PictureError, match=re.escape(staged_font)):
        picture_rendering.validate_picture_binding(edition, receipt)
    # A record that drops its members cannot pass by checking none of them.
    record = edition.picture_stage / STAGE_RECORD
    put(record, {**json.loads(record.read_text()), "members": []})
    with pytest.raises(PictureError, match="declared members"):
        picture_rendering.require_current_stage(edition, edition.picture_stage)


def test_a_receipt_is_refused_for_what_it_lacks_and_by_that_name(staged):
    edition = staged
    receipt = completed_receipt(edition)
    # A render that failed reports no text renderer: it is refused as a render that did not
    # complete, not as another renderer's.
    failed = {**receipt, "exit": 1, "renderer": {**receipt["renderer"], "text_renderer": None}}
    with pytest.raises(PictureError, match="records no completed render of the staged document"):
        picture_rendering.validate_picture_binding(edition, failed)
    # A receipt that names no canvas, as a browser's render wrote it, is another renderer's,
    # whether or not its stage is the current one.
    for browsers in ({**receipt, "renderer": None}, {**receipt, "source_sha256": "0" * 64}):
        browsers.pop("renderer") if browsers["renderer"] is None else None
        named = "no native canvas" if "renderer" not in browsers else "no completed render"
        with pytest.raises(PictureError, match=named):
            picture_rendering.validate_picture_binding(edition, browsers)
    # A completed render with another text renderer is refused by the renderer's name.
    portable = {**receipt, "renderer": {**receipt["renderer"], "text_renderer": "portable"}}
    with pytest.raises(PictureError, match="with portable text"):
        picture_rendering.validate_picture_binding(edition, portable)


def test_rendering_records_a_completed_render_that_binds(staged, root, tmp_path, monkeypatch):
    edition = staged
    fake = renderer(
        tmp_path,
        """
        import os
        output = sys.argv[sys.argv.index("--output") + 1]
        with open(output, "w") as picture:
            picture.write("rendered picture")
        observed = {
            "stdin": sys.stdin.read(),
            "session_leader": os.getsid(0) == os.getpid(),
            "cwd": os.getcwd(),
        }
        with open(sys.argv[0] + ".json", "w") as record:
            json.dump(observed, record)
        report(frames=7, drawn_sha256="ab" * 32)
        """,
    )
    render(monkeypatch, edition, fake, 60)
    receipt = repository.read(edition.render_receipt)
    assert list(receipt) == RECEIPT_KEYS
    stage, picture = edition.picture_stage, edition.picture
    work = stage.with_name(stage.name + "-spans")
    report = work.with_name(work.name + ".json")
    # The engine's renderer on the stage: the pictures' frame rate, a keyframe every two
    # seconds, the rate factor and four spans.
    assert receipt["command"] == [
        *[str(fake), "render", str(stage), "--output", str(picture), "--fps", str(FPS)],
        *["--group", str(2 * FPS), "--encoder", json.dumps(encoding.encoder(FPS))],
        *["--text-renderer", "system", "--spans", "4"],
        *["--work", str(work), "--report", str(report)],
    ]
    assert (receipt["exit"], receipt["timed_out"], receipt["deadline_seconds"]) == (0, False, 60)
    # The canvas the film's packages install, which is the engine's, and the text renderer, the
    # spans, the frames and the digest that the renderer reported; its report is taken.
    reported = {"text_renderer": "system", "binary": LOADED}
    assert receipt["renderer"] == picture_renderer.drawn_by(reported)
    assert receipt["renderer"]["binary"]["sha256"] == picture_renderer.BINARY_SHA256
    assert receipt["renderer"]["version"] == picture_renderer.RENDERER_VERSION
    assert receipt["operating_system"] == {
        "system": platform.system(),
        "release": platform.release(),
        "macos": platform.mac_ver()[0] or None,
    }
    assert (receipt["spans"], receipt["frames"], receipt["drawn_sha256"]) == (4, 7, "ab" * 32)
    assert not report.exists()
    assert receipt["source_sha256"] == repository.sha(stage / "index.html")
    assert receipt["output_sha256"] == repository.sha(picture)
    observed = json.loads(Path(f"{fake}.json").read_text(encoding="utf-8"))
    assert observed == {"stdin": "", "session_leader": True, "cwd": str(root)}
    picture_rendering.validate_picture_binding(edition, receipt)


def test_rendering_refuses_a_failed_render_after_recording_it(staged, tmp_path, monkeypatch):
    edition = staged
    with pytest.raises(PictureError, match="did not complete"):
        render(monkeypatch, edition, renderer(tmp_path, "raise SystemExit(3)"), 60)
    receipt = repository.read(edition.render_receipt)
    assert (receipt["exit"], receipt["timed_out"], receipt["output_sha256"]) == (3, False, None)


def test_failed_rendering_stops_its_remaining_workers(staged, tmp_path, monkeypatch):
    monkeypatch.setattr(picture_renderer, "STOP_GRACE_SECONDS", 0.5)
    worker = tmp_path / "worker.py"
    worker.write_text(
        textwrap.dedent(
            """
            import os, pathlib, signal, sys, time
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            pathlib.Path(sys.argv[0]).with_suffix(".pid").write_text(str(os.getpid()))
            time.sleep(60)
            """
        )
    )
    fake = renderer(
        tmp_path,
        f"""
        import pathlib, subprocess, sys, time
        subprocess.Popen([sys.executable, {str(worker)!r}])
        while not pathlib.Path({str(worker.with_suffix(".pid"))!r}).exists():
            time.sleep(0.01)
        raise SystemExit(3)
        """,
    )
    try:
        with pytest.raises(PictureError, match="did not complete"):
            render(monkeypatch, staged, fake, 10)
        receipt = repository.read(staged.render_receipt)
        assert (receipt["exit"], receipt["timed_out"]) == (3, False)
        assert gone(int(worker.with_suffix(".pid").read_text()))
    finally:
        if worker.with_suffix(".pid").exists():
            with contextlib.suppress(ProcessLookupError):
                os.kill(int(worker.with_suffix(".pid").read_text()), signal.SIGKILL)


def test_another_renderer_version_stops_staging_and_rendering_as_a_missing_tool(
    staged, root, tmp_path, monkeypatch
):
    manifest = root / "node_modules" / picture_renderer.RENDERER_PACKAGE
    manifest.write_text(json.dumps({"name": "@napi-rs/canvas", "version": "0.0.1"}))
    pinned = re.escape(picture_renderer.RENDERER_VERSION)
    versions = rf"installs @napi-rs/canvas 0\.0\.1; the engine draws with @napi-rs/canvas {pinned}"
    with pytest.raises(MissingToolError, match=versions):
        picture_rendering.stage_picture(staged, None, RUNTIME, 3840, 2160)
    fake = renderer(tmp_path, "open(__file__ + '.ran', 'w').close()")
    with pytest.raises(MissingToolError, match=versions):
        render(monkeypatch, staged, fake, 60)
    assert not Path(f"{fake}.ran").exists()
    assert not staged.render_receipt.exists()


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        (None, "has no gate record; run filmkit build check-picture"),
        ({"verdict": "refuse"}, "did not pass; run filmkit build check-picture"),
        (
            {"engine_version": "0.0.0"},
            "binds another engine_version; run filmkit build check-picture",
        ),
        ({"fonts_sha256": {}}, "binds another fonts_sha256; run filmkit build check-picture"),
        (
            {"stylesheet_sha256": "0" * 64},
            "binds another stylesheet_sha256; run filmkit build check-picture",
        ),
    ],
)
def test_rendering_refuses_a_picture_without_a_current_passing_check(
    staged, tmp_path, monkeypatch, record, reason
):
    if record is None:
        staged.picture_gates.unlink()
    else:
        passing_gates(staged, **record)
    fake = renderer(tmp_path, "open(__file__ + '.ran', 'w').close()")
    with pytest.raises(PictureError, match=reason):
        render(monkeypatch, staged, fake, 60)
    assert not Path(f"{fake}.ran").exists()
    assert not staged.render_receipt.exists()


def test_rendering_refuses_a_composition_changed_after_its_check(
    staged, root, tmp_path, monkeypatch
):
    script = root / picture_rendering.COMPOSITION_SCRIPT
    script.write_text(script.read_text() + "\n// changed after its check\n")
    fake = renderer(tmp_path, "open(__file__ + '.ran', 'w').close()")
    with pytest.raises(
        PictureError, match="binds another composition_sha256; run filmkit build check-picture"
    ):
        render(monkeypatch, staged, fake, 60)
    assert not Path(f"{fake}.ran").exists()


def test_rendering_refuses_a_stale_stage_before_running(staged, root, tmp_path, monkeypatch):
    edition = staged
    template = root / picture_rendering.COMPOSITION / "index.html"
    template.write_text(template.read_text().replace("<title>", "<title>Changed "))
    fake = renderer(tmp_path, "open(__file__ + '.ran', 'w').close()")
    with pytest.raises(PictureError, match="template_sha256"):
        render(monkeypatch, edition, fake, 60)
    assert not Path(f"{fake}.ran").exists()
    assert not edition.render_receipt.exists()


def test_rendering_stops_the_whole_process_group_at_its_deadline(staged, tmp_path, monkeypatch):
    # The renderer ignores SIGTERM and its worker obeys it: the group is sent SIGTERM at
    # the deadline and SIGKILL after the grace, and neither process outlives the render.
    monkeypatch.setattr(picture_renderer, "STOP_GRACE_SECONDS", 0.5)
    edition = staged
    worker = tmp_path / "worker.py"
    worker.write_text(
        textwrap.dedent(
            """
            import os, pathlib, signal, sys, time
            here = pathlib.Path(sys.argv[0]).parent
            def stop(*_):
                (here / "worker-terminated").write_text("")
                sys.exit(0)
            signal.signal(signal.SIGTERM, stop)
            (here / "worker.pid").write_text(str(os.getpid()))
            time.sleep(60)
            """
        )
    )
    fake = renderer(
        tmp_path,
        f"""
        import os, pathlib, signal, subprocess, sys, time
        here = pathlib.Path(sys.argv[0]).parent
        subprocess.Popen([sys.executable, {str(worker)!r}])
        while not (here / "worker.pid").exists():
            time.sleep(0.01)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        (here / "renderer.pid").write_text(str(os.getpid()))
        time.sleep(60)
        """,
    )
    started = time.monotonic()
    with pytest.raises(PictureError, match="did not complete"):
        render(monkeypatch, edition, fake, 2)
    assert time.monotonic() - started < 10
    receipt = repository.read(edition.render_receipt)
    assert (receipt["exit"], receipt["timed_out"]) == (None, True)
    assert receipt["elapsed_seconds"] >= 2
    assert (tmp_path / "worker-terminated").exists()
    assert gone(int((tmp_path / "renderer.pid").read_text()))
    assert gone(int((tmp_path / "worker.pid").read_text()))
