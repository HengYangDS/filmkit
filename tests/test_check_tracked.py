"""`filmkit check`'s questions of a film's tracked files, listed at once: its npm packages, its
Python lock and pin of the engine, its picture template and the review prompt's runtime, each
against the engine's record of what it was released on (`filmkit.check.tracked`)."""

import json
import re
import shutil
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.check as check
import filmkit.declared_sources as declared_sources
import filmkit.film as film
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture import renderer

ENGINE = Path(__file__).resolve().parents[1]
QUESTIONS = ("npm_packages", "python_lock", "template", "runtime")


@pytest.fixture
def project(tmp_path):
    """A film that holds what this release asks: the sample film's declaration, the files it
    names and its picture template, with the engine's own manifests and locks and a pin of this
    release."""
    for _field, path in declared_sources.named_files(film.FILM):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, target)
    for path in (film.DECLARATION, "picture/index.html"):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, tmp_path / path)
    for name in ("package.json", "package-lock.json", "uv.lock"):
        shutil.copy2(ENGINE / name, tmp_path / name)
    (tmp_path / "pyproject.toml").write_text(
        f'[tool.uv.sources]\n{released.ENGINE} = {{ git = "https://example.invalid/filmkit", '
        f'tag = "v{released.version()}" }}\n'
    )
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


def report(root: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Each question's findings at a root, and what was not compared."""
    not_read: list[str] = []
    return check.tracked(root, not_read), not_read


def found(root: Path) -> dict[str, list[str]]:
    return report(root)[0]


def test_a_film_that_holds_what_the_release_asks_has_no_finding(project):
    assert found(project) == {name: [] for name in QUESTIONS}


def test_the_sample_film_has_no_finding():
    assert found(repository.ROOT) == {name: [] for name in QUESTIONS}


def test_every_finding_of_every_question_is_listed_in_one_run(project):
    rewrite(project / "package.json", declared(renderer.RENDERER_NAME), '"gsap": "3.15.1"')
    held = older(project / "uv.lock", "transformers")
    rewrite(
        project / "picture/index.html",
        "</head>",
        '<script src="node_modules/gsap/dist/gsap.min.js"></script></head>',
    )
    prompt = project / "content/review/prompt.md"
    rewrite(prompt, "This edition: exactly {duration} s", "Each edition: exactly {duration} s")
    findings = found(project)
    assert all(findings[name] for name in QUESTIONS), findings
    assert "prompt.md:9 cites {duration}" in " ".join(findings["runtime"])
    asked = f"{renderer.RENDERER_NAME} {renderer.RENDERER_VERSION}"
    assert asked in " ".join(findings["npm_packages"])
    assert f"transformers 0.0.1 (the engine: {held})" in " ".join(findings["python_lock"])
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
    rewrite(project / "pyproject.toml", f'tag = "v{released.version()}"', 'tag = "v0.0.0"')
    (finding,) = found(project)["python_lock"]
    assert "pins filmkit v0.0.0" in finding and f"v{version('filmkit')}" in finding


def test_the_template_is_asked_for_every_anchor_at_once(project):
    template = project / "picture/index.html"
    rewrite(
        template, 'data-duration="1200"', 'data-duration="1200" data-held="x" data-duration="1200"'
    )
    rewrite(template, "/* FILM_DATA */", "")
    text = " ".join(found(project)["template"])
    assert "data-duration" in text and "2 times" in text
    assert "FILM_DATA" in text and "0 times" in text


def test_a_template_whose_root_names_one_language_is_named_with_the_anchor_to_write(project):
    # A film's template written before this release opens with its Chinese edition's tag.
    rewrite(project / "picture/index.html", '<html lang="und">', '<html lang="zh-CN">')
    assert found(project)["template"] == [
        'The picture template opens with <html lang="zh-CN">, one language\'s tag; staging gives '
        'each edition its own, in place of <html lang="und">, which the template holds once'
    ]


def test_a_film_outside_any_repository_is_asked_at_its_root_alone(tmp_path, project):
    film_root = tmp_path / "nogit" / "film"
    shutil.copytree(project, film_root, ignore=shutil.ignore_patterns("nogit"))
    for name in ("package.json", "package-lock.json", "uv.lock", "pyproject.toml"):
        (film_root / name).unlink()
    (tmp_path / "nogit/package.json").write_text('{"dependencies": {"gsap": "3.15.1"}}')
    assert any("no package.json" in text for text in found(film_root)["npm_packages"])


@pytest.mark.parametrize(
    ("path", "question"),
    [
        ("package.json", "npm_packages"),
        ("package-lock.json", "npm_packages"),
        ("uv.lock", "python_lock"),
        ("pyproject.toml", "python_lock"),
        (film.DECLARATION, "runtime"),
    ],
)
def test_a_file_that_cannot_be_read_is_a_finding_of_its_question(project, path, question):
    (project / path).write_bytes(b"\xff\xfe not text {")
    findings = found(project)
    (finding,) = findings[question]
    assert Path(path).name in finding
    assert all(findings[name] == [] for name in QUESTIONS if name != question), findings


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
    rewrite(project / "pyproject.toml", f'tag = "v{released.version()}"', 'rev = "db7a837"')
    findings, not_read = report(project)
    assert findings["python_lock"] == []
    assert any("python_lock" in note and "tag" in note for note in not_read)


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


@pytest.mark.parametrize(
    ("path", "text", "question"),
    [
        ("package.json", '{"dependencies": ["a"]}', "npm_packages"),
        ("package-lock.json", '{"packages": [1]}', "npm_packages"),
        ("uv.lock", "package = [1]\n", "python_lock"),
        ("pyproject.toml", 'tool = "x"\n', "python_lock"),
    ],
)
def test_a_file_of_another_shape_is_a_finding_of_its_question(project, path, text, question):
    (project / path).write_text(text)
    findings = found(project)
    assert any(Path(path).name in finding for finding in findings[question]), findings


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
    named = f'name = "{released.ENGINE}"\n'
    rewrite(
        project / "uv.lock",
        named + 'source = { editable = "." }',
        named + 'version = "0.0.1"\nsource = { git = "https://example.invalid/filmkit" }',
    )
    (finding,) = found(project)["python_lock"]
    assert "uv.lock holds filmkit 0.0.1" in finding and "lock again" in finding
    rewrite(project / "pyproject.toml", f'tag = "v{released.version()}"', 'tag = "v0.0.0"')
    (finding,) = found(project)["python_lock"]
    assert "pins filmkit v0.0.0" in finding
