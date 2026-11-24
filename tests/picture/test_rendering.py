"""Stage, render and bind the picture with fixture inputs and the real composition."""

import contextlib
import json
import os
import platform
import re
import shutil
import signal
import sys
import textwrap
import time
from pathlib import Path

import pytest
from assembled import stage

import filmkit.captions.refresh as refresh
import filmkit.picture.encoding as encoding
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.released as released
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import STAGE_RECORD, Edition, UnassembledError
from filmkit.specification import FPS

# The real composition, found before a test rebinds the repository root.
COMPOSITION = repository.ROOT / picture_rendering.COMPOSITION
# The runtime the fixture's timelines state: an odd number of seconds, unlike the sample's 60.
RUNTIME = 1477
# The template patterns that the renderer document replaces.
PLACEHOLDERS = (
    "/* FILM_DATA */",
    '<link rel="stylesheet" href="film.css">',
    '<script src="film.js"></script>',
    'data-duration="1200"',
    'data-width="1920"',
    'data-height="1080"',
    'content="width=1920, height=1080"',
    'width="1920" height="1080"',
)
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


def put(path, data):
    """Write text or JSON to a fixture file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


@pytest.fixture(autouse=True)
def root(tmp_path, monkeypatch):
    """A repository root with both editions' current inputs and the real composition."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    supported = {
        "name": picture_renderer.RENDERER_NAME,
        "version": picture_renderer.RENDERER_VERSION,
    }
    put(root / "node_modules" / picture_renderer.RENDERER_PACKAGE, supported)
    shutil.copytree(COMPOSITION, root / picture_rendering.COMPOSITION)
    for path, source in picture_rendering.staged_members():
        if not (root / source).exists():
            put(root / source, f"fixture {path}")
    put(root / "content/source-manifest.json", {"members": []})
    for code, text in (("zh", "先看数据。"), ("en", "Read the data.")):
        edition = Edition(code)
        script = {"segments": [{"id": "01", "text": text}]}
        put(root / edition.script, script)
        segment = {"id": "01", "text": text, "words": []}
        timeline = {**script, "edition": code, "duration": RUNTIME, "segments": [segment]}
        timeline["captions"] = []
        put(edition.timeline, timeline)
        put(edition.soundtrack, f"{code} narration")
        assembly = {
            "script_sha256": repository.sha(edition.script),
            "soundtrack_sha256": repository.sha(edition.soundtrack),
        }
        put(edition.audio_assembly, assembly)
    return root


def passing_gates(edition, **changes):
    """A gate record that check-picture passed for the edition's current picture."""
    composition = repository.ROOT / picture_rendering.COMPOSITION_SCRIPT
    record = {
        "composition_sha256": repository.sha(composition),
        "timeline_sha256": repository.sha(edition.timeline),
        "engine_version": released.version(),
        **picture_rendering.face_bindings(),
        "verdict": "pass",
        **changes,
    }
    put(edition.picture_gates, record)


@pytest.fixture
def staged():
    """The Chinese edition, staged complete at the UHD frame, its picture checked."""
    edition = Edition("zh")
    picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
    passing_gates(edition)
    return edition


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


@pytest.mark.parametrize("code", ["zh", "en"])
def test_staging_twice_writes_the_same_complete_document(code):
    edition = Edition(code)
    stage = edition.picture_stage
    written = []
    for _ in range(2):
        picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
        written.append(((stage / "index.html").read_bytes(), (stage / "stage.json").read_bytes()))
    assert written[0] == written[1]
    document = written[0][0].decode()
    template = (COMPOSITION / "index.html").read_text()
    for placeholder in PLACEHOLDERS:
        assert placeholder in template
        assert placeholder not in document
    assert f'<html lang="{"en" if code == "en" else "zh-CN"}">' in document
    assert 'data-duration="1477"' in document
    assert '<div style="width:3840px;height:2160px" id="film"' in document
    assert "<script>" + (COMPOSITION / "film.js").read_text() + "</script>" in document
    assert "<style>" + (COMPOSITION / "film.css").read_text() + "</style>" in document
    film = json.loads(document.split("window.FILM=", 1)[1].split(";</script>", 1)[0])
    assert (film["edition"], film["render_offset"]) == (code, 0)
    binding = json.loads(written[0][1])
    inputs, timeline = picture_rendering.candidate_picture_inputs(edition)
    assert binding["inputs"] == inputs
    # The edition is the one the assembly wrote into the timeline, which staging copies.
    assert timeline["edition"] == code
    assert film == {**timeline, "render_offset": 0}
    assert [(member["path"], member["source"]) for member in binding["members"]] == [
        (path, str(source)) for path, source in picture_rendering.staged_members()
    ]
    for member in binding["members"]:
        assert repository.sha(stage / member["path"]) == member["sha256"]


def test_a_stage_holds_exactly_the_declared_fonts_in_order(staged):
    stage = staged.picture_stage
    declared = [Path(font) for font in FILM.picture.fonts]
    binding = json.loads((stage / "stage.json").read_text())
    fonts = [(member["path"], member["source"]) for member in binding["members"][2:]]
    assert fonts == [(f"fonts/{font.name}", str(font)) for font in declared]
    assert sorted(path.name for path in (stage / "fonts").iterdir()) == sorted(
        font.name for font in declared
    )


def test_staging_reads_each_bound_input_once(root, monkeypatch):
    # The stage inlines the very timeline whose bytes it binds.
    edition = Edition("zh")
    opened = []
    path_open = Path.open

    def counted(self, *args, **kwargs):
        opened.append(self)
        return path_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counted)
    picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
    for path in (root / edition.script, edition.timeline, edition.audio_assembly):
        assert opened.count(path) == 1


def test_candidate_inputs_refuse_a_timeline_or_soundtrack_of_other_sources():
    edition = Edition("zh")
    timeline = json.loads(edition.timeline.read_text())
    segment = {**timeline["segments"][0], "text": "另一句。"}
    put(edition.timeline, {**timeline, "segments": [segment]})
    with pytest.raises(PictureError, match="timeline differs from its authored script"):
        picture_rendering.candidate_picture_inputs(edition)
    put(edition.timeline, timeline)
    put(edition.soundtrack, "another narration")
    with pytest.raises(PictureError, match="soundtrack differs from its native assembly"):
        picture_rendering.candidate_picture_inputs(edition)


def test_an_edition_refreshed_after_an_anchor_is_added_stages_as_following_its_script(
    tmp_path, monkeypatch
):
    words = (("甲", 2.0, 2.4), ("乙", 2.4, 2.8), ("丙", 3.4, 3.8), ("丁", 3.8, 4.2))
    edition = stage(tmp_path, monkeypatch, "zh", ["甲乙。", "丙丁。"], words)
    script = repository.read(edition.script)
    script["segments"][0]["anchored_groups"] = ["甲乙。", "{last}丙丁{/last}。"]
    put(repository.ROOT / edition.script, script)
    refresh.refresh_captions(edition)
    picture_rendering.stage_picture(edition, None, 9, 3840, 2160)
    staged = repository.read(edition.rendered(True).stage / picture_rendering.DATA)
    # The stage's data holds the anchor with the times of its words, 丙 to 丁.
    assert [staged["segments"][0]["anchors"]["last"][key] for key in ("start", "end")] == [3.4, 4.2]


def test_staging_refuses_other_frames_durations_and_places(root):
    edition = Edition("zh")
    for duration, size, start in ((RUNTIME + 1, (3840, 2160), 0), (RUNTIME, (1280, 720), 0)):
        with pytest.raises(PictureError, match="admitted frame and duration"):
            picture_rendering.stage_picture(edition, None, duration, *size, start)
    with pytest.raises(PictureError, match="build owner"):
        picture_rendering.stage_picture(edition, root / "elsewhere", RUNTIME, 3840, 2160)
    assert not edition.picture_stage.exists()


def test_the_document_refuses_a_template_pattern_it_does_not_find_exactly(root):
    edition = Edition("zh")
    template = root / picture_rendering.COMPOSITION / "index.html"
    text = template.read_text()
    for changed, pattern in (
        (text.replace('data-width="1920"', 'data-width="1600"'), 'data-width="1920"'),
        (text.replace("</body>", '<div id="film"></div></body>'), '<div id="film"'),
        (text.replace(' data-duration="1200"', ""), 'data-duration="1200"'),
    ):
        template.write_text(changed)
        with pytest.raises(PictureError, match=re.escape(repr(pattern))):
            picture_rendering.picture_html(edition, RUNTIME, 3840, 2160, 0)


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


def test_a_stage_spans_the_runtime_its_edition_s_timeline_states(staged):
    edition = staged
    record = json.loads((edition.picture_stage / STAGE_RECORD).read_text())
    assert (record["duration"], record["start"]) == (1477, 0)
    assert picture_rendering.require_current_stage(edition, edition.picture_stage) == record
    # A stage of the sample's 60 s is no stage of this edition's whole runtime.
    picture_rendering.stage_picture(edition, None, 60, 3840, 2160)
    with pytest.raises(PictureError, match="duration differ"):
        picture_rendering.require_current_stage(edition, edition.picture_stage)


def test_an_edition_without_a_timeline_is_refused_before_a_stage_is_written():
    edition = Edition("en")
    edition.timeline.unlink()
    with pytest.raises(UnassembledError) as refused:
        picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
    assert str(refused.value) == (
        "The en edition has no timeline at build/artifacts/film/en/timeline.json, so no runtime: "
        "run produce assemble --language en"
    )
    assert not edition.picture_stage.exists()


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


def test_another_renderer_version_refuses_staging_and_rendering(
    staged, root, tmp_path, monkeypatch
):
    manifest = root / "node_modules" / picture_renderer.RENDERER_PACKAGE
    manifest.write_text(json.dumps({"name": "@napi-rs/canvas", "version": "0.0.1"}))
    pinned = re.escape(picture_renderer.RENDERER_VERSION)
    versions = rf"installs @napi-rs/canvas 0\.0\.1; the engine draws with @napi-rs/canvas {pinned}"
    with pytest.raises(PictureError, match=versions):
        picture_rendering.stage_picture(staged, None, RUNTIME, 3840, 2160)
    fake = renderer(tmp_path, "open(__file__ + '.ran', 'w').close()")
    with pytest.raises(PictureError, match=versions):
        render(monkeypatch, staged, fake, 60)
    assert not Path(f"{fake}.ran").exists()
    assert not staged.render_receipt.exists()


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        (None, "has no gate record; run check-picture"),
        ({"verdict": "refuse"}, "did not pass; run check-picture"),
        ({"engine_version": "0.0.0"}, "binds another engine_version; run check-picture"),
        ({"fonts_sha256": {}}, "binds another fonts_sha256; run check-picture"),
        ({"stylesheet_sha256": "0" * 64}, "binds another stylesheet_sha256; run check-picture"),
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
    with pytest.raises(PictureError, match="binds another composition_sha256; run check-picture"):
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
