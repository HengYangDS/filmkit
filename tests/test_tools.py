"""The tools command: the engine's Node tools run from a copy below the film, with its packages."""

import json
import re
from importlib.metadata import version

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.picture.rendering import PictureError
from filmkit.tools import ToolError

# The engine's npm packages, found before a test rebinds the film root; they hold the renderer
# version the engine supports.
PACKAGES = repository.node_modules()


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root whose npm packages are the engine's own, away from the engine's sources."""
    root = tmp_path.resolve() / "film"
    root.mkdir()
    (root / "node_modules").symlink_to(PACKAGES)
    monkeypatch.setattr(repository, "ROOT", root)
    return root


def cached(root, path):
    """A tool module's copy in the film's tool cache."""
    return root / tools.CACHE / version("filmkit") / path


def test_a_tool_runs_from_its_copy_with_the_films_packages(film, capfd):
    # Without arguments the player check refuses its invocation, after loading the browser
    # driver that it imports from the film's packages.
    assert tools.run("player-check", []) == 2
    copy = cached(film, "delivery/player-check.mjs")
    assert copy.read_bytes() == (tools.PACKAGE / "delivery/player-check.mjs").read_bytes()
    assert "Usage: python -m filmkit.tools player-check players" in capfd.readouterr().err


def test_the_copies_keep_their_folders_and_only_changed_bytes_are_replaced(film):
    cache = tools.stage_tools()
    modules = sorted(path.relative_to(tools.PACKAGE) for path in tools.PACKAGE.rglob("*.mjs"))
    assert sorted(path.relative_to(cache) for path in cache.rglob("*.mjs")) == modules
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
    assert shown == {"cwd": str(film), "browser": str(picture_rendering.supplied_browser())}
    monkeypatch.setenv("FILM_CHROMIUM_PATH", "/opt/chromium/chrome")
    assert tools.run("geometry-check", []) == 0
    assert json.loads(capfd.readouterr().out)["browser"] == "/opt/chromium/chrome"


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


def test_another_renderer_version_refuses_before_any_tool_runs(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    manifest = root / "node_modules" / picture_rendering.RENDERER_PACKAGE
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": "hyperframes", "version": "0.8.149"}))
    pinned = re.escape(picture_rendering.RENDERER_VERSION)
    with pytest.raises(PictureError, match=rf"HyperFrames 0\.8\.149.*HyperFrames {pinned}"):
        tools.run("geometry-check", [])
    manifest.unlink()
    with pytest.raises(PictureError, match=rf"installs no HyperFrames.*HyperFrames {pinned}"):
        tools.run("frame-audit", [])
    with pytest.raises(SystemExit, match=r"^motion-audit: The film installs no HyperFrames"):
        tools.main(["motion-audit", "timeline.json"])
    assert not (root / "build").exists()


def test_a_film_without_node_on_its_path_is_refused(film, monkeypatch):
    monkeypatch.setenv("PATH", str(film))
    with pytest.raises(ToolError, match="No node on PATH"):
        tools.run("geometry-check", [])


def test_the_command_names_each_tool_and_refuses_another(capsys):
    with pytest.raises(SystemExit) as refused:
        tools.main(["render"])
    assert refused.value.code == 2
    assert "invalid choice: 'render'" in capsys.readouterr().err
    assert sorted(tools.TOOLS) == ["frame-audit", "geometry-check", "motion-audit", "player-check"]
    for path in tools.TOOLS.values():
        assert (tools.PACKAGE / path).is_file()
