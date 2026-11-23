"""The delivery format's values that the editions' scripts and the film's declaration state."""

import json
import os
import subprocess
import sys

import pytest
import test_film

import filmkit.film as film
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.film import FILM, FilmError
from filmkit.production import CODES, Edition

declared, rewrite = test_film.declared, test_film.rewrite


def test_scripts_that_disagree_refuse(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for code, author in zip(CODES, ("One Author", "Another Author"), strict=True):
        script = tmp_path / Edition(code).script
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(json.dumps({"author": author, "chapters": [{}, {}]}))
    assert specification.declared("chapters", len) == 2
    with pytest.raises(ValueError, match="different author values"):
        specification.declared("author", str)


def test_the_engine_renders_60_fps_only():
    assert specification.rendered_rate(60) == 60
    with pytest.raises(ValueError, match="60 fps films, not the 30 fps"):
        specification.rendered_rate(30)


# A film refused while the engine loads, and the one line that the refusal ends in: the
# declaration's keys and a script's withdrawn keys.
LOAD_REFUSALS = {
    "a declaration without the credits": (
        lambda root: rewrite(root, "credits_duration = 3\n", ""),
        "filmkit.film.FilmError: content/film.toml declares no credits_duration; declare the "
        "credits' length there once, in whole seconds",
    ),
    "a script that declares the credits": (
        lambda root: declare(root / Edition("zh").script, credits_duration=3),
        "ValueError: content/zh/film-script.json declares credits_duration; state the credits' "
        "length once, as credits_duration in content/film.toml",
    ),
    "a script that declares a duration": (
        lambda root: declare(root / Edition("zh").script, duration=1500),
        "ValueError: content/zh/film-script.json declares duration; remove it: an edition lasts as "
        "long as its narration, which the assembly counts",
    ),
}


def declare(path, **fields) -> None:
    """Add fields to a JSON file."""
    path.write_text(json.dumps({**json.loads(path.read_text()), **fields}, ensure_ascii=False))


@pytest.mark.parametrize("case", LOAD_REFUSALS)
def test_a_refusal_at_load_ends_what_a_command_prints_in_its_one_line(declared, case):
    # The refusal comes while the engine's modules load, before a command's own error path,
    # which prints its refusals in one line, is reached: the command prints the traceback of
    # the import, and its last line is the refusal's one line. It writes nothing.
    change, line = LOAD_REFUSALS[case]
    change(declared)
    command = [sys.executable, "-I", "-B", "-m", "filmkit.produce", "select", "--language", "zh"]
    environment = {**os.environ, "FILMKIT_ROOT": str(declared)}
    ran = subprocess.run(
        command,
        cwd=declared,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert (ran.returncode, ran.stdout, ran.stderr.splitlines()[-1]) == (1, "", line)
    assert not (declared / "build").exists()


def test_the_credits_are_the_declarations(tmp_path, monkeypatch):
    assert specification.CREDITS_DURATION == FILM.credits_duration == 3
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for code in CODES:
        script = tmp_path / Edition(code).script
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(json.dumps({"author": "One Author"}))
    specification.refuse_withdrawn()
    (tmp_path / Edition("en").script).write_text(json.dumps({"credits_duration": 3}))
    with pytest.raises(ValueError) as refused:
        specification.refuse_withdrawn()
    assert str(refused.value) == (
        "content/en/film-script.json declares credits_duration; state the credits' length once, "
        "as credits_duration in content/film.toml"
    )


def test_the_declaration_states_the_credits_once_in_whole_seconds(declared):
    for stated in ("credits_duration = 3.5", "credits_duration = true", "credits_duration = -1"):
        rewrite(declared, "credits_duration = 3", stated)
        with pytest.raises(FilmError, match="credits_duration"):
            film.load(declared)
        rewrite(declared, stated, "credits_duration = 3")


def test_a_declaration_without_the_credits_is_refused_in_one_line_and_never_loads(declared):
    one = (
        "content/film.toml declares no credits_duration; declare the credits' length there "
        "once, in whole seconds"
    )
    rewrite(declared, "credits_duration = 3\n", "")
    assert film.problems(declared) == [one]
    # It fails closed: the reader gives no film, and loading refuses with that one line.
    assert film.read(declared)[0] is None
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert str(refusal.value) == one
    # Another field's problem keeps pydantic's words, and they do not name the credits again.
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    first, other = film.problems(declared)
    assert first == one
    assert other.startswith("content/film.toml is not a film declaration: 1 validation error")
    assert "\nslug\n" in other and "credits_duration" not in other


def test_a_script_that_declares_a_duration_is_refused_when_the_engine_loads(tmp_path, monkeypatch):
    # An edition lasts as long as its narration: no script states a runtime, and the engine
    # holds none of its own.
    assert not hasattr(specification, "DURATION")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for code in CODES:
        script = tmp_path / Edition(code).script
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(json.dumps({"author": "One Author"}))
    (tmp_path / Edition("zh").script).write_text(json.dumps({"duration": 1500}))
    with pytest.raises(ValueError) as refused:
        specification.refuse_withdrawn()
    assert str(refused.value) == (
        "content/zh/film-script.json declares duration; remove it: an edition lasts as long as its "
        "narration, which the assembly counts"
    )
