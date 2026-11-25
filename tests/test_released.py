"""The engine's record of what it was released on (`filmkit.released`): what it states, the one
place the engine's code reads the canvas's pin from, and how it refuses where it is missing,
unreadable or partial."""

import importlib
import shutil
from pathlib import Path

import pytest

import filmkit.released as released
from filmkit.picture import renderer

ENGINE = Path(__file__).resolve().parents[1]
# A task list, which the record does not read: the record reads the pin of Vale beside it.
TASKS = '[tasks.check]\nrun = "uv run filmkit check"\n'


@pytest.fixture
def project(tmp_path):
    """An engine's repository at a root: its npm manifest and lock and its uv lock."""
    for name in ("package.json", "package-lock.json", "uv.lock"):
        shutil.copy2(ENGINE / name, tmp_path / name)
    return tmp_path


def test_the_packaged_record_equals_what_the_repository_holds():
    assert released.load() == released.compute(ENGINE)


def test_the_record_states_the_vale_the_mise_configuration_pins(project):
    config = project / released.MISE_CONFIG
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(TASKS)
    with pytest.raises(released.ReleasedError, match=r"\.config/mise/config\.toml pins no Vale"):
        released.compute(project)
    config.write_text(f'{TASKS}\n[tools]\nnode = "26.13.1"\n"{released.VALE}" = "9.9.9"\n')
    assert released.compute(project)["vale"] == "9.9.9"
    config.write_text(f'{TASKS}\n[tools."{released.VALE}"]\nversion = "9.9.8"\n')
    assert released.compute(project)["vale"] == "9.9.8"


def test_an_engine_whose_record_states_no_vale_refuses_in_one_line(monkeypatch):
    record = released.load()
    assert released.vale() == record["vale"]
    monkeypatch.setattr(released, "load", lambda: {"npm": record["npm"]})
    with pytest.raises(released.ReleasedError) as refusal:
        released.vale()
    line = one_line(refusal)
    assert "states no Vale version" in line
    assert str(released.RECORD) in line
    assert "python -m filmkit.released" in line


def test_the_record_names_the_packages_a_film_declares_and_the_runtime_closure():
    record = released.load()
    assert set(record["npm"]) == {"@napi-rs/canvas", "@puppeteer/browsers", "puppeteer-core"}
    assert {"mlx-audio", "transformers", "pydantic"} <= set(record["python"])
    assert not {"pytest", "coverage", "filmkit"} & set(record["python"])


def test_the_renderer_draws_with_the_version_and_integrity_the_record_states(monkeypatch):
    # The record is the one place the engine's code reads the canvas's version and integrity
    # from: a record that states another build moves the renderer's pin with it.
    name, record = renderer.RENDERER_NAME, released.load()
    moved = {"version": "9.9.9", "integrity": "sha512-another-build"}
    monkeypatch.setattr(released, "load", lambda: {**record, "npm": {**record["npm"], name: moved}})
    try:
        reloaded = importlib.reload(renderer)
        assert (reloaded.RENDERER_VERSION, reloaded.INTEGRITY[name]) == tuple(moved.values())
    finally:
        monkeypatch.undo()
        importlib.reload(renderer)
    assert renderer.RENDERER_VERSION == record["npm"][name]["version"]


def one_line(refusal) -> str:
    """A refusal's words, which stand in one line."""
    line = str(refusal.value)
    assert line
    assert "\n" not in line
    return line


def test_an_engine_without_its_record_refuses_by_the_file_and_the_command_that_writes_it(
    monkeypatch, tmp_path
):
    absent = tmp_path / "released.json"
    monkeypatch.setattr(released, "RECORD", absent)
    try:
        with pytest.raises(released.ReleasedError) as refusal:
            released.load()
        line = one_line(refusal)
        assert str(absent) in line
        assert "python -m filmkit.released" in line and "mise run fix" in line
        # The renderer reads its pin when it is imported, and ends in the same line.
        with pytest.raises(released.ReleasedError) as imported:
            importlib.reload(renderer)
        assert one_line(imported) == line
        # A record that cannot be read is refused by the same names.
        absent.write_text("no record\n")
        with pytest.raises(released.ReleasedError) as refusal:
            released.load()
        unread = one_line(refusal)
        assert str(absent) in unread and "python -m filmkit.released" in unread
    finally:
        monkeypatch.undo()
        importlib.reload(renderer)


def test_a_record_without_the_canvas_refuses_in_one_line_that_names_it(monkeypatch):
    name, record = renderer.RENDERER_NAME, released.load()
    others = {held: entry for held, entry in record["npm"].items() if held != name}
    monkeypatch.setattr(released, "load", lambda: {**record, "npm": others})
    try:
        with pytest.raises(released.ReleasedError) as refusal:
            importlib.reload(renderer)
    finally:
        monkeypatch.undo()
        importlib.reload(renderer)
    line = one_line(refusal)
    assert name in line and str(released.RECORD) in line
    assert "python -m filmkit.released" in line


@pytest.mark.parametrize("stated", ["version", "integrity"])
def test_a_record_that_states_half_of_the_canvas_is_refused_as_one_that_states_none(
    monkeypatch, stated
):
    # The canvas's entry holds its version or its integrity, as the record states it, and not
    # the other: the renderer's pin is both.
    name, record = renderer.RENDERER_NAME, released.load()
    half = {stated: record["npm"][name][stated]}
    monkeypatch.setattr(released, "load", lambda: {**record, "npm": {**record["npm"], name: half}})
    with pytest.raises(released.ReleasedError) as refusal:
        released.npm_package(name)
    line = one_line(refusal)
    assert f"states no version and integrity of {name}" in line
    assert str(released.RECORD) in line and "python -m filmkit.released" in line


def test_the_records_command_runs_without_a_record_and_writes_the_tracked_bytes(
    monkeypatch, tmp_path, capsys
):
    tracked = released.RECORD.read_bytes()
    monkeypatch.setattr(released, "RECORD", tmp_path / "released.json")
    released.main()
    assert released.RECORD.read_bytes() == tracked
    assert capsys.readouterr().out.startswith("released.json: ")
