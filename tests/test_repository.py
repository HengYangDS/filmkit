"""How the engine finds the film it builds and that film's npm packages.

Each check imports the engine in a child process, below or outside a film that holds only its
declaration, so no film is loaded here and the module runs without the shared fixtures.
"""

import os
import subprocess
import sys

import pytest

DECLARATION = "content/film.toml"


def film(folder):
    """A folder that holds a film declaration, as the engine finds it."""
    (folder / DECLARATION).parent.mkdir(parents=True)
    (folder / DECLARATION).write_text("")
    return folder.resolve()


def engine(expression: str, cwd, root=None) -> subprocess.CompletedProcess:
    """Evaluate an expression on the engine's repository module in a child process.

    The child runs in `cwd`, with `FILMKIT_ROOT` set to `root`, or unset when that is None.
    """
    environment = {key: value for key, value in os.environ.items() if key != "FILMKIT_ROOT"}
    if root is not None:
        environment["FILMKIT_ROOT"] = str(root)
    return subprocess.run(
        [sys.executable, "-c", f"import filmkit.repository as r; print({expression})"],
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_a_command_below_a_film_builds_that_film(tmp_path):
    root = film(tmp_path / "film")
    below = root / "picture/drafts"
    below.mkdir(parents=True)
    found = engine("r.ROOT", below)
    assert found.returncode == 0, found.stderr
    assert found.stdout.strip() == str(root)


def test_filmkit_root_names_the_film_from_anywhere(tmp_path):
    root = film(tmp_path / "film")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    found = engine("r.ROOT", elsewhere, root=root)
    assert found.returncode == 0, found.stderr
    assert found.stdout.strip() == str(root)


def test_outside_any_film_the_engine_refuses_naming_where_it_began(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    refused = engine("r.ROOT", outside)
    assert refused.returncode != 0
    assert f"No film declaration {DECLARATION} at or above {outside.resolve()}" in refused.stderr


def test_a_named_folder_without_a_declaration_refuses(tmp_path):
    refused = engine("r.ROOT", tmp_path, root=tmp_path / "empty")
    assert refused.returncode != 0
    assert f"No film declaration {DECLARATION} in {(tmp_path / 'empty').resolve()}" in (
        refused.stderr
    )


@pytest.mark.parametrize(
    ("film_folder", "packages_folder"),
    [("", ""), ("examples/sample", ""), ("examples/sample", "examples/sample")],
)
def test_the_film_takes_the_nearest_npm_packages_at_or_above_it(
    tmp_path, film_folder, packages_folder
):
    root = film(tmp_path / film_folder)
    (tmp_path / "node_modules").mkdir(exist_ok=True)
    (tmp_path / packages_folder / "node_modules").mkdir(exist_ok=True)
    found = engine("r.node_modules()", root)
    assert found.returncode == 0, found.stderr
    assert found.stdout.strip() == str((tmp_path / packages_folder / "node_modules").resolve())


def test_a_film_without_npm_packages_refuses_naming_the_film(tmp_path):
    root = film(tmp_path / "film")
    refused = engine("r.node_modules()", root)
    assert refused.returncode != 0
    assert f"No node_modules folder at or above the film {root}" in refused.stderr
