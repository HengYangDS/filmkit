"""The tools command: the engine's Node tools run from a copy below the film, with its packages."""

import json
import re
import shutil
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.child_processes as child_processes
import filmkit.picture.browser as picture_browser
import filmkit.picture.renderer as picture_renderer
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.film import FILM
from filmkit.picture.metrics import TABLE, VARIABLE
from filmkit.picture.rendering import STYLE

# The engine's npm packages, found before a test rebinds the film root; they hold the renderer
# version the engine supports.
PACKAGES = repository.node_modules()


# The sample film, whose stylesheet and fonts the tools' film declares.
SAMPLE = Path(__file__).resolve().parents[1] / "examples/sample-film"


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root whose npm packages are the engine's own, away from the engine's sources,
    with the sample film's stylesheet and fonts and a stand-in for the supplied browser build,
    which a tool that drives the browser asks for before it starts."""
    root = tmp_path.resolve() / "film"
    root.mkdir()
    (root / "node_modules").symlink_to(PACKAGES)
    monkeypatch.setattr(repository, "ROOT", root)
    browser = picture_browser.browser_path()
    browser.parent.mkdir(parents=True)
    browser.write_text("a stand-in for the supplied browser build")
    for path in (STYLE, *FILM.picture.fonts):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE / path, root / path)
    return root


def cached(root, path):
    """A tool module's copy in the film's tool cache."""
    return root / tools.CACHE / version("filmkit") / path


def test_a_tool_runs_from_its_copy_with_the_films_packages(film, capfd):
    # Without arguments the player check refuses its invocation with status 2, after loading the
    # browser driver that it imports from the film's packages: no finding, so the run raises it.
    with pytest.raises(subprocess.CalledProcessError) as failed:
        tools.run("player-check", [])
    assert failed.value.returncode == 2
    copy = cached(film, "delivery/player-check.mjs")
    assert copy.read_bytes() == (tools.PACKAGE / "delivery/player-check.mjs").read_bytes()
    assert "Usage: node player-check.mjs players" in capfd.readouterr().err


def test_the_copies_keep_their_folders_and_only_changed_bytes_are_replaced(film):
    cache = tools.stage_tools()
    modules = sorted(path.relative_to(tools.PACKAGE) for path in tools.PACKAGE.rglob("*.mjs"))
    assert sorted(path.relative_to(cache) for path in cache.rglob("*.mjs")) == modules
    classes = tools.PACKAGE / "languages/scripts.json"
    assert (cache / "languages/scripts.json").read_bytes() == classes.read_bytes()
    assert cache == cached(film, "")
    stale, kept = cache / "picture/geometry-check.mjs", cache / "picture/seat-marks.mjs"
    stale.write_text("an earlier copy")
    before = kept.stat().st_mtime_ns
    tools.stage_tools()
    assert stale.read_bytes() == (tools.PACKAGE / "picture/geometry-check.mjs").read_bytes()
    assert kept.stat().st_mtime_ns == before


def test_a_tool_runs_at_the_film_root_with_the_renderers_browser(
    film, tmp_path, monkeypatch, capfd
):
    package = tmp_path / "package"
    probe = (
        "console.log(JSON.stringify("
        "{cwd: process.cwd(), browser: process.env.FILM_CHROMIUM_PATH}));"
    )
    (package / "picture").mkdir(parents=True)
    (package / "picture/geometry-check.mjs").write_text(probe)
    monkeypatch.setattr(tools, "PACKAGE", package)
    monkeypatch.delenv("FILM_CHROMIUM_PATH", raising=False)
    assert tools.run("geometry-check", []) == 0
    shown = json.loads(capfd.readouterr().out)
    assert shown == {"cwd": str(film), "browser": str(picture_browser.supplied_browser())}
    named = tmp_path / "chromium"
    named.write_text("another browser build, which the variable names")
    monkeypatch.setenv("FILM_CHROMIUM_PATH", str(named))
    assert tools.run("geometry-check", []) == 0
    assert json.loads(capfd.readouterr().out)["browser"] == str(named)


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ("process.exitCode = 1;", 1),
        ('throw new Error("the tool crashed");', 2),
        ('await Promise.reject(new Error("the tool crashed"));', 2),
        ('Promise.reject(new Error("the tool crashed")); setTimeout(() => {}, 50);', 2),
        ('process.kill(process.pid, "SIGKILL");', -9),
    ],
)
def test_a_tool_that_cannot_finish_is_a_failure_and_a_finding_its_status(
    film, tmp_path, monkeypatch, capfd, body, status
):
    # A finding is 1, which the caller reads as a refusal; a tool that crashes or a signal ends is
    # no finding, and the run raises it as a failure to finish.
    package = tmp_path / "package"
    (package / "picture").mkdir(parents=True)
    (package / "picture/geometry-check.mjs").write_text(body)
    monkeypatch.setattr(tools, "PACKAGE", package)
    if status == 1:
        assert tools.run("geometry-check", []) == 1
        return
    with pytest.raises(subprocess.CalledProcessError) as failed:
        tools.run("geometry-check", [])
    assert failed.value.returncode == status
    assert ("the tool crashed" in capfd.readouterr().err) is (status == 2)


def test_a_tool_takes_added_variables_and_may_write_its_output_to_a_file(
    film, tmp_path, monkeypatch, capfd
):
    package = tmp_path / "package"
    (package / "picture").mkdir(parents=True)
    (package / "picture/frame-audit.mjs").write_text(
        "console.log(JSON.stringify({trace: process.env.TRACE ?? null}));"
    )
    monkeypatch.setattr(tools, "PACKAGE", package)
    out = tmp_path / "report.json"
    assert tools.run("frame-audit", [], environment={"TRACE": "trace.tsv"}, stdout=out) == 0
    assert json.loads(out.read_text()) == {"trace": "trace.tsv"}
    assert capfd.readouterr().out == ""


def test_the_headless_audits_measure_text_by_the_films_faces(film, tmp_path, monkeypatch, capfd):
    package = tmp_path / "package"
    (package / "picture").mkdir(parents=True)
    probe = f"console.log(JSON.stringify({{table: process.env.{VARIABLE} ?? null}}));"
    headless = [name for name, tool in tools.TOOLS.items() if tool.measures]
    for tool in (*headless, "geometry-check"):
        (package / tools.TOOLS[tool].module).write_text(probe)
    monkeypatch.setattr(tools, "PACKAGE", package)
    monkeypatch.delenv(VARIABLE, raising=False)
    # Each tool that runs the composition headlessly is given the table of the film's declared
    # faces.
    for tool in headless:
        assert tools.run(tool, []) == 0
        assert json.loads(capfd.readouterr().out) == {"table": str(film / TABLE)}
    assert sorted(repository.read(film / TABLE)["faces"]) == [
        "Sample",
        "SampleBold",
        "SampleLatin",
        "SampleLatinBold",
    ]
    # A browser check measures the real fonts, and a caller's own table is kept.
    assert tools.run("geometry-check", []) == 0
    assert json.loads(capfd.readouterr().out) == {"table": None}
    assert tools.run("frame-audit", [], environment={VARIABLE: "own.json"}) == 0
    assert json.loads(capfd.readouterr().out) == {"table": "own.json"}


def test_another_renderer_version_stops_before_any_tool_runs(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    manifest = root / "node_modules" / picture_renderer.RENDERER_PACKAGE
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": "@napi-rs/canvas", "version": "0.8.149"}))
    pinned = re.escape(picture_renderer.RENDERER_VERSION)
    # The canvas the engine draws with is a tool the host lacks until the packages are installed
    # again, which no input of a node records.
    missing = child_processes.MissingToolError
    with pytest.raises(missing, match=rf"@napi-rs/canvas 0\.8\.149.*@napi-rs/canvas {pinned}"):
        tools.run("geometry-check", [])
    manifest.unlink()
    with pytest.raises(missing, match=rf"installs no @napi-rs/canvas.*@napi-rs/canvas {pinned}"):
        tools.run("frame-audit", [])
    assert not (root / "build").exists()


def test_a_tool_that_drives_the_browser_stops_where_no_browser_build_stands(film, monkeypatch):
    monkeypatch.setattr(picture_browser, "browser_path", lambda: film / "no-browser")
    with pytest.raises(child_processes.MissingToolError, match="No browser build at .*no-browser"):
        tools.run("player-check", [])


def test_a_film_without_node_on_its_path_cannot_run_its_tools(film, monkeypatch):
    monkeypatch.setenv("PATH", str(film))
    with pytest.raises(child_processes.MissingToolError, match="No node on PATH"):
        tools.run("geometry-check", [])


def test_the_engine_names_each_tool_by_its_module():
    assert sorted(tools.TOOLS) == [
        "anchor-reads",
        "band-audit",
        "caption-equivalence",
        "detail-audit",
        "frame-audit",
        "geometry-check",
        "mass-audit",
        "motion-audit",
        "player-check",
        "whole-turns",
    ]
    for tool in tools.TOOLS.values():
        assert (tools.PACKAGE / tool.module).is_file()


def test_a_tool_measures_text_where_its_module_reads_the_faces_table():
    # The field states what the module does: it reads the table the run names to it.
    for name, tool in tools.TOOLS.items():
        reads = "readTextMetrics" in (tools.PACKAGE / tool.module).read_text()
        assert tool.measures is reads, name


def test_a_tool_browses_where_its_module_drives_the_supplied_browser():
    # The field states what the module does: it imports the browser driver.
    for name, tool in tools.TOOLS.items():
        drives = "headless-browser.mjs" in (tools.PACKAGE / tool.module).read_text()
        assert tool.browses is drives, name
