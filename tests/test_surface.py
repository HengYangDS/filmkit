"""The engine's surface (design decision 17 of build-a-film-by-its-verbs): beside the console
command `filmkit`, the package runs as `python -m` only the modules decision 17 keeps, each until
its release, and the two commands moved out of the retired production command name their
options."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import filmkit
import filmkit.repository as repository

PACKAGE = Path(filmkit.__file__).resolve().parent
# The modules decision 17 keeps as `python -m` commands, by the release that retires each.
KEPT = {
    # R4, the narration lock: the narration's internal processes and its tools.
    "filmkit.narration.narrate",
    "filmkit.narration.synthesis",
    "filmkit.narration.alignment",
    "filmkit.narration.transcription",
    "filmkit.narration.judge",
    "filmkit.narration.audition",
    "filmkit.narration.readings",
    "filmkit.narration.anchors",
    "filmkit.soundtrack.fit",
    # R3, one picture runtime.
    "filmkit.picture.repair",
    "filmkit.picture.still_scan",
    "filmkit.picture.sync_audit",
    # R6, the review's seams.
    "filmkit.review.listening_plan",
    "filmkit.review.measurement",
    # The engine's own development step.
    "filmkit.released",
}


def entries() -> set[str]:
    """Each module of the installed package that `python -m` runs: a package's `__main__.py`, or a
    module whose body acts when it runs as the program."""
    found = set()
    for path in PACKAGE.rglob("*.py"):
        name = ".".join(("filmkit", *path.relative_to(PACKAGE).with_suffix("").parts))
        if path.name == "__main__.py":
            found.add(name.removesuffix(".__main__"))
            continue
        body = ast.parse(path.read_text(encoding="utf-8")).body
        if any(isinstance(node, ast.If) and "__main__" in ast.unparse(node.test) for node in body):
            found.add(name)
    return found


def test_every_module_the_package_runs_is_one_that_decision_17_keeps():
    assert entries() == KEPT


@pytest.mark.parametrize(
    ("module", "options"),
    [
        ("filmkit.soundtrack.fit", ["--language", "--variants"]),
        ("filmkit.picture.repair", ["--language", "--attempts"]),
    ],
)
def test_the_commands_moved_out_of_the_production_command_name_their_options(module, options):
    done = subprocess.run(
        [sys.executable, "-I", "-B", "-m", module, "--help"],
        cwd=repository.ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith(f"usage: python -m {module} ")
    assert all(option in done.stdout for option in options)
