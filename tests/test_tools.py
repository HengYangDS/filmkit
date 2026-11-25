"""The tools command: the engine's Node tools run from a copy below the film, with its packages."""

import contextlib
import json
import re
import shutil
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.picture.browser as picture_browser
import filmkit.picture.renderer as picture_renderer
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.film import FILM
from filmkit.graph import records
from filmkit.picture.metrics import TABLE, VARIABLE
from filmkit.picture.rendering import STYLE, PictureError
from filmkit.tools import ToolError

# The engine's npm packages, found before a test rebinds the film root; they hold the renderer
# version the engine supports.
PACKAGES = repository.node_modules()


# The sample film, whose stylesheet and fonts the tools' film declares.
SAMPLE = Path(__file__).resolve().parents[1] / "examples/sample-film"


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root whose npm packages are the engine's own, away from the engine's sources,
    with the sample film's stylesheet and fonts."""
    root = tmp_path.resolve() / "film"
    root.mkdir()
    (root / "node_modules").symlink_to(PACKAGES)
    for path in (STYLE, *FILM.picture.fonts):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE / path, root / path)
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


def test_the_headless_audits_measure_text_by_the_films_faces(film, tmp_path, monkeypatch, capfd):
    package = tmp_path / "package"
    (package / "picture").mkdir(parents=True)
    probe = f"console.log(JSON.stringify({{table: process.env.{VARIABLE} ?? null}}));"
    headless = ("frame-audit", "motion-audit", "detail-audit", "caption-equivalence", "band-audit")
    for tool in (*headless, "geometry-check"):
        (package / tools.TOOLS[tool]).write_text(probe)
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


def test_another_renderer_version_refuses_before_any_tool_runs(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    manifest = root / "node_modules" / picture_renderer.RENDERER_PACKAGE
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": "@napi-rs/canvas", "version": "0.8.149"}))
    pinned = re.escape(picture_renderer.RENDERER_VERSION)
    with pytest.raises(PictureError, match=rf"@napi-rs/canvas 0\.8\.149.*@napi-rs/canvas {pinned}"):
        tools.run("geometry-check", [])
    manifest.unlink()
    with pytest.raises(
        PictureError, match=rf"installs no @napi-rs/canvas.*@napi-rs/canvas {pinned}"
    ):
        tools.run("frame-audit", [])
    with pytest.raises(SystemExit, match=r"^motion-audit: The film installs no @napi-rs/canvas"):
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
    assert sorted(tools.TOOLS) == [
        "anchor-reads",
        "band-audit",
        "caption-equivalence",
        "detail-audit",
        "frame-audit",
        "geometry-check",
        "motion-audit",
        "player-check",
        "whole-turns",
    ]
    for path in tools.TOOLS.values():
        assert (tools.PACKAGE / path).is_file()


def test_a_run_that_names_no_edition_is_measured_under_none(monkeypatch):
    runs = []

    @contextlib.contextmanager
    def measured(code, name, *, record):
        runs.append((code, name, record))
        yield

    monkeypatch.setattr(tools.seam, "run", measured)
    monkeypatch.setattr(tools, "run", lambda tool, arguments: 0)
    with pytest.raises(SystemExit) as ended:
        tools.main(["frame-audit", "timeline.json"])
    assert ended.value.code == 0
    assert runs == [(None, "frame-audit", False)]


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return tmp_path.resolve()


@pytest.mark.parametrize(
    ("arguments", "code"),
    [
        (["build/runtime/work/final-delivery-zh-uhd", "build/evidence/x.json", "2"], "zh"),
        (["cover", "build/runtime/work/final-delivery-en-uhd", "assets/cover.png", "c.png"], "en"),
        (["build/artifacts/film/en/timeline.json", "0.5"], "en"),
        (["{root}/build/evidence/editions/zh/picture-geometry.json"], "zh"),
        # Another film's stage is no edition of this film.
        (["/elsewhere/build/evidence/editions/zh/picture-geometry.json"], None),
        (["../other-film/build/runtime/work/final-delivery-zh-uhd"], None),
        (["players", "binding.json", "receipt.json"], None),
        (["build/runtime/work/final-delivery-zh-uhd", "build/evidence/editions/en/x.json"], None),
    ],
)
def test_a_tools_edition_is_read_from_its_arguments_when_they_name_one(root, arguments, code):
    named = [argument.format(root=root) for argument in arguments]
    assert tools.edition_of(named) == code


STAGE = "build/runtime/work/final-delivery-zh-uhd"
GEOMETRY = "build/evidence/editions/zh/picture-geometry.json"


def recorded(root) -> list[str]:
    """The nodes whose run records stand below the root."""
    return sorted(path.stem for path in (root / records.FOLDER).rglob("*.json"))


@pytest.mark.parametrize(
    ("command", "record"),
    [
        (["geometry-check", STAGE, GEOMETRY, "2"], "geometry-check"),
        (["player-check", "cover", STAGE, "cover.png", "painting.png"], "player-check-cover"),
        # Any other tool, and the player check in another mode, is a run by hand.
        (["frame-audit", "build/artifacts/film/zh/timeline.json", "0.0333333"], None),
        (["caption-equivalence", "build/artifacts/film/zh/timeline.json", "0.5"], None),
        (["band-audit", "build/artifacts/film/zh/timeline.json", "936", "1024", "30"], None),
        (["player-check", "players", "build/evidence/editions/zh/binding.json", "r.json"], None),
        # The two checks of a build, for no single edition of this film.
        (["geometry-check", "/elsewhere/" + STAGE, "/elsewhere/" + GEOMETRY], None),
    ],
)
def test_only_the_checks_a_build_runs_from_the_command_line_write_a_run_record(
    root, monkeypatch, command, record
):
    monkeypatch.setattr(tools, "run", lambda tool, arguments: 0)
    with pytest.raises(SystemExit) as ended:
        tools.main(command)
    assert ended.value.code == 0
    assert recorded(root) == ([] if record is None else [record])
    assert tools.recorded(command[0], command[1:]) == (None if record is None else ("zh", record))


def test_a_check_of_a_build_is_recorded_whether_it_passes_or_fails(root, monkeypatch):
    ran = []
    monkeypatch.setattr(tools, "run", lambda tool, arguments: ran.append(tool) or 0)
    with pytest.raises(SystemExit) as ended:
        tools.main(["geometry-check", STAGE, GEOMETRY])
    assert ended.value.code == 0
    assert records.read(records.place("geometry-check", "zh")).outcome == "pass"
    # A failing check's run is recorded as refused, and the command exits with its status.
    monkeypatch.setattr(tools, "run", lambda tool, arguments: ran.append(tool) or 1)
    with pytest.raises(SystemExit) as ended:
        tools.main(["player-check", "cover", STAGE, "cover.png", "painting.png"])
    assert ended.value.code == 1
    written = records.read(records.place("player-check-cover", "zh"))
    assert (written.outcome, written.refusal) == ("refuse", "exit status 1")
    # A run that is no check of a build leaves both records byte for byte and adds none.
    folder = root / records.FOLDER
    before = {path.name: path.read_bytes() for path in folder.rglob("*.json")}
    for command in (
        ["player-check", "players", GEOMETRY, "receipt.json"],
        ["frame-audit", "build/artifacts/film/zh/timeline.json", "0.0333333"],
        ["geometry-check", "binding.json", "receipt.json"],
    ):
        with pytest.raises(SystemExit):
            tools.main(command)
    assert {path.name: path.read_bytes() for path in folder.rglob("*.json")} == before
    assert sorted(before) == ["geometry-check.json", "player-check-cover.json"]
    assert ran[2:] == ["player-check", "frame-audit", "geometry-check"]
