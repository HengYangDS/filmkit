"""What a release asks of a film's tracked files, listed at once: the engine's record of what it
was released on, and the adoption command that compares a film with it."""

import importlib
import json
import re
import shutil
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.adoption as adoption
import filmkit.film as film
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture import renderer

ENGINE = Path(__file__).resolve().parents[1]
TASKS = """\
[tasks."film:picture"]
run = [
  "uv run python -m filmkit.produce stage-picture --language zh",
  "uv run python -m filmkit.produce preflight --language zh",
  "uv run python -m filmkit.produce preflight --language en",
  "uv run python -m filmkit.produce render-picture --language zh",
  "uv run python -m filmkit.produce render-picture --language en",
]

[tasks."film:deliver"]
run = ["uv run python -m filmkit.delivery.folder"]
"""
# The film's pin of the Vale this release was released on, as its Mise configuration states it.
PIN = f'\n[tools]\n"{released.VALE}" = "{released.vale()}"\n'


@pytest.fixture
def project(tmp_path):
    """A film that holds what this release asks: the sample film's declaration, the files it
    names and its picture template, with the engine's own manifests, locks, a task list and
    the release's pin of Vale."""
    for _field, path in film.named_files(film.FILM):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, target)
    for path in (film.DECLARATION, "picture/index.html"):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, tmp_path / path)
    for name in ("package.json", "package-lock.json", "uv.lock"):
        shutil.copy2(ENGINE / name, tmp_path / name)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.sources]\nfilmkit = { git = "https://example.invalid/filmkit", '
        f'tag = "v{version("filmkit")}" }}\n'
    )
    (tmp_path / ".config/mise").mkdir(parents=True)
    (tmp_path / ".config/mise/config.toml").write_text(TASKS + PIN)
    return tmp_path


# The browser driver among the packages a film declares, and another version of it as a case.
DRIVER, OTHER_DRIVER = "puppeteer-core", "25.17.0"


def declared(name: str, at: str | None = None) -> str:
    """A package's line in a manifest: at the version the engine's record states, which is the
    engine's own manifest's, or at another that a test names as a case."""
    return f'"{name}": "{at or released.load()["npm"][name]["version"]}"'


def rewrite(path: Path, old: str, new: str) -> None:
    """Replace one text of a file, which must hold it."""
    text = path.read_text()
    assert old in text, old
    path.write_text(text.replace(old, new, 1))


def older(lock: Path, name: str) -> str:
    """Set one package of a uv lock to version 0.0.1 and return the version it held."""
    text = lock.read_text()
    block = re.search(
        rf'(\[\[package\]\]\nname = "{re.escape(name)}"\nversion = ")([^"]+)(")', text
    )
    assert block, name
    lock.write_text(text.replace(block.group(0), block.group(1) + "0.0.1" + block.group(3), 1))
    return block.group(2)


def found(root: Path) -> dict[str, list[str]]:
    return adoption.report(root)["findings"]


def test_a_film_that_holds_what_the_release_asks_has_no_finding(project):
    assert found(project) == {name: [] for name in adoption.QUESTIONS}


def test_the_sample_film_has_no_finding():
    assert found(repository.ROOT) == {name: [] for name in adoption.QUESTIONS}


def test_every_finding_of_every_question_is_listed_in_one_run(project):
    rewrite(project / film.DECLARATION, "\ndelivery_folder = ", "\ndocuments_folder = ")
    rewrite(project / "package.json", declared(renderer.RENDERER_NAME), '"gsap": "3.15.1"')
    held = older(project / "uv.lock", "transformers")
    rewrite(
        project / ".config/mise/config.toml",
        "filmkit.delivery.folder",
        "filmkit.delivery.documents_folder",
    )
    rewrite(
        project / "picture/index.html",
        "</head>",
        '<script src="node_modules/gsap/dist/gsap.min.js"></script></head>',
    )
    rewrite(project / ".config/mise/config.toml", PIN, PIN.replace(released.vale(), "9.9.9"))
    findings = found(project)
    assert all(findings[name] for name in adoption.QUESTIONS), findings
    assert "declares documents_folder" in " ".join(findings["declaration"])
    asked = f"{renderer.RENDERER_NAME} {renderer.RENDERER_VERSION}"
    assert asked in " ".join(findings["npm_packages"])
    assert f"transformers 0.0.1 (the engine: {held})" in " ".join(findings["python_lock"])
    assert "filmkit.delivery.documents_folder" in " ".join(findings["tasks"])
    assert "node_modules/gsap/dist/gsap.min.js" in " ".join(findings["template"])


def test_a_package_the_film_alone_holds_is_no_finding(project):
    rewrite(
        project / "package.json",
        '"devDependencies": {',
        '"devDependencies": {\n    "esbuild": "0.28.2",',
    )
    assert found(project)["npm_packages"] == []


def test_a_declared_package_at_another_version_or_integrity_is_a_finding(project):
    rewrite(project / "package.json", declared(DRIVER), declared(DRIVER, OTHER_DRIVER))
    lock = json.loads((project / "package-lock.json").read_text())
    lock["packages"]["node_modules/@napi-rs/canvas"]["integrity"] = "sha512-other"
    (project / "package-lock.json").write_text(json.dumps(lock))
    text = " ".join(found(project)["npm_packages"])
    released_at = released.load()["npm"][DRIVER]["version"]
    assert f"{DRIVER} {OTHER_DRIVER}" in text and f"{DRIVER} {released_at}" in text
    assert "@napi-rs/canvas" in text and "integrity" in text


def test_a_film_without_a_lock_is_a_finding_of_that_lock(project):
    (project / "package-lock.json").unlink()
    (project / "uv.lock").unlink()
    findings = found(project)
    assert "package-lock.json" in " ".join(findings["npm_packages"])
    assert "uv.lock" in " ".join(findings["python_lock"])


def test_the_python_finding_prints_the_constraints_that_close_it(project):
    held = older(project / "uv.lock", "regex")
    (finding,) = found(project)["python_lock"]
    assert f'constraint-dependencies = ["regex=={held}"]' in finding


def test_a_package_outside_the_engines_runtime_is_the_films_own(project):
    older(project / "uv.lock", "coverage")
    assert found(project)["python_lock"] == []


def test_a_pin_of_another_engine_release_is_a_finding(project):
    rewrite(project / "pyproject.toml", f'tag = "v{version("filmkit")}"', 'tag = "v0.0.0"')
    (finding,) = found(project)["python_lock"]
    assert "pins filmkit v0.0.0" in finding and f"v{version('filmkit')}" in finding


def test_a_task_names_only_modules_and_actions_this_engine_has(project):
    tasks = project / ".config/mise/config.toml"
    rewrite(tasks, "filmkit.produce stage-picture", "filmkit.produce stage-pictures")
    rewrite(tasks, "filmkit.delivery.folder", "filmkit.delivery.documents_folder")
    text = " ".join(found(project)["tasks"])
    assert "film:picture" in text and "stage-pictures" in text
    assert "film:deliver" in text and "filmkit.delivery.documents_folder" in text


def test_tasks_that_render_ask_readiness_somewhere(project):
    tasks = project / ".config/mise/config.toml"
    plain = tasks.read_text()
    rewrite(tasks, '  "uv run python -m filmkit.produce preflight --language en",\n', "")
    assert found(project)["tasks"] == []
    rewrite(tasks, '  "uv run python -m filmkit.produce preflight --language zh",\n', "")
    assert found(project)["tasks"] == [
        "the tasks render a picture and none asks filmkit.produce preflight"
    ]
    asking = '  "uv run python -m filmkit.produce preflight --language zh",\n'
    close = ']\n\n[tasks."film:deliver"]'
    tasks.write_text(plain.replace(asking, "").replace(close, asking + close))
    assert found(project)["tasks"] == []


def test_a_film_without_a_mise_configuration_has_unread_tasks_and_pins_no_vale(project):
    shutil.rmtree(project / ".config")
    result = adoption.report(project)
    assert result["findings"]["tasks"] == []
    assert any("tasks" in note for note in result["not_read"])
    # A film without a Mise configuration pins no Vale, which is a finding and not unread.
    (absent,) = result["findings"]["vale"]
    assert absent.startswith("no Mise configuration (.config/mise/config.toml, mise.toml, ")


def test_the_template_is_asked_for_every_anchor_at_once(project):
    template = project / "picture/index.html"
    rewrite(
        template, 'data-duration="1200"', 'data-duration="1200" data-held="x" data-duration="1200"'
    )
    rewrite(template, "/* FILM_DATA */", "")
    text = " ".join(found(project)["template"])
    assert "data-duration" in text and "2 times" in text
    assert "FILM_DATA" in text and "0 times" in text


def test_the_command_prints_one_line_and_exits_by_its_findings(project, monkeypatch, capsys):
    monkeypatch.setattr(repository, "ROOT", project)
    adoption.main([])
    printed = json.loads(capsys.readouterr().out)
    assert printed["findings"] == {name: [] for name in adoption.QUESTIONS}
    rewrite(project / "package.json", declared(DRIVER), declared(DRIVER, OTHER_DRIVER))
    with pytest.raises(SystemExit) as refusal:
        adoption.main([])
    assert str(refusal.value).startswith("adoption: 1 finding")
    assert json.loads(capsys.readouterr().out)["findings"]["npm_packages"]


def test_the_packaged_record_equals_what_the_repository_holds():
    assert released.load() == released.compute(ENGINE)


# The finding for a film whose Mise configuration holds no pin of the tool the engine pins.
ABSENT = (
    'config.toml pins no Vale ([tools] holds no "{tool}" version); {on}: '
    'pin "{tool}" = "{asked}" under [tools]'
)
# What a film's Mise configuration states of Vale, and the finding that names it: its pin, or its
# absence, with the version the release record states. A pin under another name, in another form
# or of no one version is not the release's.
PINS = [
    ('[tools]\n"{tool}" = "{asked}"\n', None),
    ('[tools."{tool}"]\nversion = "{asked}"\n', None),
    ('[tools]\n"{tool}" = "9.9.9"\n', "config.toml pins Vale 9.9.9; {on}"),
    ('[tools."{tool}"]\nversion = "9.9.8"\n', "config.toml pins Vale 9.9.8; {on}"),
    ('[tools]\n"{tool}" = ["{asked}"]\n', "config.toml pins Vale ['{asked}']; {on}"),
    ('[tools]\nnode = "26.13.1"\n', ABSENT),
    ('[tools]\nvale = "{asked}"\n', ABSENT),
    ("", ABSENT),
]


@pytest.mark.parametrize(("tools", "finding"), PINS)
def test_a_film_that_pins_another_vale_or_none_is_named(project, tools, finding):
    tool, asked = released.VALE, released.vale()
    words = {"tool": tool, "asked": asked, "on": f"the engine was released on Vale {asked}"}
    (project / ".config/mise/config.toml").write_text(TASKS + tools.format(**words))
    assert found(project)["vale"] == ([finding.format(**words)] if finding else [])


def test_the_record_states_the_vale_the_mise_configuration_pins(project):
    config = project / released.MISE_CONFIG
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


# The cases of the independent review of 19 November 2026, each as it was probed.


def tasks_of(project: Path, body: str) -> list[str]:
    """The findings of the tasks question for a film whose one task is the body given."""
    (project / ".config/mise/config.toml").write_text(body)
    return found(project)["tasks"]


def test_an_action_is_found_after_its_options_and_inside_quotes(project):
    body = (
        '[tasks.p]\nrun = [\n  "uv run python -m filmkit.produce --language zh preflight",\n'
        "  \"uv run python -m filmkit.produce 'preflight' --language en\",\n]\n"
    )
    assert tasks_of(project, body) == []


def test_a_module_is_named_by_its_whole_word_whatever_runs_it(project):
    body = (
        '[tasks.p]\nrun = [\n  "python3 -m filmkit.gone",\n  "python -m filmkit_tools.build",\n'
        '  "# was: python -m filmkit.old.module",\n]\n'
    )
    assert tasks_of(project, body) == ["p: this engine has no module filmkit.gone"]


def test_a_film_outside_any_repository_is_asked_at_its_root_alone(tmp_path, project):
    film_root = tmp_path / "nogit" / "film"
    shutil.copytree(project, film_root, ignore=shutil.ignore_patterns("nogit"))
    for name in ("package.json", "package-lock.json", "uv.lock", "pyproject.toml"):
        (film_root / name).unlink()
    shutil.rmtree(film_root / ".config")
    (tmp_path / "nogit/package.json").write_text('{"dependencies": {"gsap": "3.15.1"}}')
    (tmp_path / "nogit/mise.toml").write_text('[tasks.x]\nrun = "python -m filmkit.gone"\n')
    result = adoption.report(film_root)
    assert result["findings"]["tasks"] == []
    assert any("no package.json" in text for text in result["findings"]["npm_packages"])


@pytest.mark.parametrize(
    ("path", "question"),
    [
        ("package.json", "npm_packages"),
        ("package-lock.json", "npm_packages"),
        ("uv.lock", "python_lock"),
        ("pyproject.toml", "python_lock"),
        (".config/mise/config.toml", "tasks vale"),
        (film.DECLARATION, "declaration"),
    ],
)
def test_a_file_that_cannot_be_read_is_a_finding_of_its_question(project, path, question):
    (project / path).write_bytes(b"\xff\xfe not text {")
    result = adoption.report(project)
    for asked in question.split():
        (finding,) = result["findings"][asked]
        assert Path(path).name in finding
    others = [name for name in adoption.QUESTIONS if name not in question.split()]
    assert all(result["findings"][name] == [] for name in others), result["findings"]


def test_the_template_names_scripts_and_stylesheets_as_a_browser_reads_them(project):
    template = project / "picture/index.html"
    rewrite(
        template,
        "</head>",
        "<script src=bare.js></script>"
        '<link rel="alternate stylesheet" href="other.css">'
        '<link href="more.css" rel="stylesheet preload">'
        '<!-- <script src="old.js"></script> -->'
        '<script data-src="lazy.js"></script>'
        '<link rel="icon" href="icon.png"></head>',
    )
    (finding,) = found(project)["template"]
    assert "bare.js, more.css, other.css;" in finding
    assert "old.js" not in finding and "lazy.js" not in finding and "icon.png" not in finding


def test_a_pin_that_is_no_tag_is_named_as_not_compared(project):
    rewrite(project / "pyproject.toml", f'tag = "v{version("filmkit")}"', 'rev = "db7a837"')
    result = adoption.report(project)
    assert result["findings"]["python_lock"] == []
    assert any("python_lock" in note and "tag" in note for note in result["not_read"])


def test_a_lock_without_the_engine_is_a_finding(project):
    (project / "uv.lock").write_text("version = 1\n")
    (finding,) = found(project)["python_lock"]
    assert "holds no filmkit" in finding


def test_one_package_is_counted_in_the_singular_and_a_missing_entry_is_said_plainly(project):
    older(project / "uv.lock", "regex")
    assert (
        "holds 1 package of the engine's runtime at another version"
        in found(project)["python_lock"][0]
    )
    lock = json.loads((project / "package-lock.json").read_text())
    del lock["packages"]["node_modules/puppeteer-core"]
    (project / "package-lock.json").write_text(json.dumps(lock))
    (finding,) = found(project)["npm_packages"]
    assert "package-lock.json holds no puppeteer-core" in finding and "None" not in finding


# The cases of the review's second pass.


def task_report(project: Path, body: str) -> dict:
    (project / ".config/mise/config.toml").write_text(body)
    return adoption.report(project)


def test_an_action_named_by_a_variable_is_not_compared_and_an_edition_is_not_read(project):
    by_variable = (
        '[tasks.p]\nrun = [\n  "uv run python -m filmkit.produce $ACTION --language zh",\n'
        '  "uv run python -m filmkit.produce render-picture --language zh",\n]\n'
    )
    result = task_report(project, by_variable)
    assert result["findings"]["tasks"] == []
    assert any(note.startswith("tasks: p") and "variable" in note for note in result["not_read"])
    loop = (
        "[tasks.p]\nrun = '''\nfor code in zh en; do\n"
        '  uv run python -m filmkit.produce preflight --language "$code"\n'
        "  uv run python -m filmkit.produce render-picture --language \"$code\"\ndone\n'''\n"
    )
    result = task_report(project, loop)
    assert result["findings"]["tasks"] == []
    assert not any(note.startswith("tasks:") for note in result["not_read"])


def test_a_command_continued_on_the_next_line_is_one_command(project):
    lone = (
        "[tasks.p]\nrun = '''\nuv run python -m filmkit.produce \\\n"
        "  render-picture --language en\n'''\n"
    )
    assert tasks_of(project, lone) == [
        "the tasks render a picture and none asks filmkit.produce preflight"
    ]
    asked = (
        "[tasks.p]\nrun = '''\nuv run python -m filmkit.produce \\\n  preflight \\\n"
        "  --language en\n"
        "uv run python -m filmkit.produce render-picture --language en\n'''\n"
    )
    assert tasks_of(project, asked) == []
    gone = "[tasks.p]\nrun = '''\nuv run python -m \\\n  filmkit.gone\n'''\n"
    assert tasks_of(project, gone) == ["p: this engine has no module filmkit.gone"]


def test_a_word_after_m_that_is_no_module_name_is_not_read(project):
    body = (
        "[tasks.p]\nrun = [\n"
        "  \"git commit -m 'filmkit.adoption: adopt a release'\",\n"
        '  "uv run -m filmkit.gone",\n]\n'
    )
    assert tasks_of(project, body) == ["p: this engine has no module filmkit.gone"]


def test_a_command_a_shell_is_given_as_a_string_is_read(project):
    inside = (
        "[tasks.p]\nrun = [\n"
        "  \"sh -c 'uv run python -m filmkit.produce preflight --language en'\",\n"
        '  "uv run python -m filmkit.produce render-picture --language en",\n]\n'
    )
    assert tasks_of(project, inside) == []
    render = (
        '[tasks.p]\nrun = "bash -c '
        "'uv run python -m filmkit.produce render-picture --language zh'\"\n"
    )
    assert tasks_of(project, render) == [
        "the tasks render a picture and none asks filmkit.produce preflight"
    ]


@pytest.mark.parametrize(
    ("path", "text", "question"),
    [
        ("package.json", '{"dependencies": ["a"]}', "npm_packages"),
        ("package-lock.json", '{"packages": [1]}', "npm_packages"),
        ("uv.lock", "package = [1]\n", "python_lock"),
        ("pyproject.toml", 'tool = "x"\n', "python_lock"),
        (".config/mise/config.toml", "tasks = [1]\n", "tasks"),
    ],
)
def test_a_file_of_another_shape_is_a_finding_of_its_question(project, path, text, question):
    (project / path).write_text(text)
    result = adoption.report(project)
    assert result["findings"][question], result
    assert any(Path(path).name in finding for finding in result["findings"][question])


def test_a_second_naming_of_the_inlined_stylesheet_is_a_finding(project):
    rewrite(
        project / "picture/index.html",
        "</head>",
        '<link rel="stylesheet" href="film.css" media="print"></head>',
    )
    (finding,) = found(project)["template"]
    assert "loads film.css" in finding


def test_a_lock_of_another_engine_release_is_a_finding_when_the_pin_is_this_one(project):
    # A film's lock states the engine's version; the repository's own, an editable source, none.
    rewrite(
        project / "uv.lock",
        'name = "filmkit"\nsource = { editable = "." }',
        'name = "filmkit"\nversion = "0.0.1"\nsource = { git = "https://example.invalid/filmkit" }',
    )
    (finding,) = found(project)["python_lock"]
    assert "uv.lock holds filmkit 0.0.1" in finding and "lock again" in finding
    rewrite(project / "pyproject.toml", f'tag = "v{version("filmkit")}"', 'tag = "v0.0.0"')
    (finding,) = found(project)["python_lock"]
    assert "pins filmkit v0.0.0" in finding


def test_a_film_outside_any_repository_reads_the_tasks_at_its_root_or_says_so(tmp_path, project):
    film_root = tmp_path / "nogit" / "film"
    shutil.copytree(project, film_root, ignore=shutil.ignore_patterns("nogit"))
    shutil.rmtree(film_root / ".config")
    (tmp_path / "nogit/mise.toml").write_text('[tasks.x]\nrun = "python -m filmkit.gone"\n')
    result = adoption.report(film_root)
    assert result["findings"]["tasks"] == []
    assert any(note.startswith("tasks: no Mise configuration") for note in result["not_read"])


# The cases of the review's fourth pass (20 November 2026), on the question as cut.


def test_readiness_asked_in_one_task_serves_a_render_in_another(project):
    body = (
        '[tasks.ready]\nrun = ["uv run python -m filmkit.produce preflight --language zh"]\n\n'
        '[tasks.p]\nrun = ["uv run python -m filmkit.produce render-picture --language en"]\n'
    )
    assert tasks_of(project, body) == []


def test_an_action_named_by_a_task_argument_is_not_compared(project):
    body = (
        "[tasks.p]\nrun = [\n"
        "  \"uv run python -m filmkit.produce {{arg(name='action')}} --language zh\",\n"
        '  "uv run python -m filmkit.produce render-picture --language zh",\n]\n'
    )
    result = task_report(project, body)
    assert result["findings"]["tasks"] == []
    assert any(note.startswith("tasks: p") for note in result["not_read"])


def test_a_variable_beside_an_unknown_word_is_said_as_it_was_read(project):
    body = '[tasks.p]\nrun = "uv run python -m filmkit.produce stage-pictures --language $code"\n'
    result = task_report(project, body)
    assert result["findings"]["tasks"] == []
    (note,) = (note for note in result["not_read"] if note.startswith("tasks:"))
    assert "with a variable that names no action of this engine by a word" in note


def test_an_edition_named_by_a_variable_hides_no_render_without_readiness(project):
    body = '[tasks.p]\nrun = "uv run python -m filmkit.produce render-picture --language $code"\n'
    assert tasks_of(project, body) == [
        "the tasks render a picture and none asks filmkit.produce preflight"
    ]


def test_a_comment_line_that_ends_in_a_backslash_takes_no_line_with_it(project):
    asked = (
        "[tasks.p]\nrun = '''\n# check first \\\n"
        "uv run python -m filmkit.produce preflight --language zh\n"
        "uv run python -m filmkit.produce render-picture --language zh\n'''\n"
    )
    assert tasks_of(project, asked) == []
    gone = "[tasks.p]\nrun = '''\n# deliver \\\nuv run python -m filmkit.gone\n'''\n"
    assert tasks_of(project, gone) == ["p: this engine has no module filmkit.gone"]
