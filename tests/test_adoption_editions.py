"""The adoption command's bridge question `editions`: each line of a film's tracked text, but the
sources the loader reads, that names a file this release moves or removes by its former path."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import filmkit.adoption as adoption

DECLARATION = """\
slug = "reel"
[editions.zh]
sources = "content"
cover = "assets/cover/reel-cover.png"
[editions.en]
sources = "content/en"
"""


def put(root: Path, path: str, text: str) -> None:
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_text(text, encoding="utf-8")


@pytest.fixture
def film(tmp_path) -> Path:
    """A film that has not moved: its Chinese files in content/, named by its tracked text."""
    put(tmp_path, "content/film.toml", DECLARATION)
    put(tmp_path, "content/voice-reference.json", json.dumps({"reference_audio": "assets/a.wav"}))
    put(tmp_path, "content/en/voice-reference.json", "{}")
    put(tmp_path, "NOTICE", "Scripts:\ncontent/film-script.json, the Chinese script.\n")
    put(tmp_path, ".config/mise/config.toml", '[tasks.say]\nrun = "say assets/a.wav"\n')
    put(tmp_path, "tests/picture/page.mjs", 'const copy = "content/narration.md";\n')
    put(tmp_path, "assets/cover/reel-cover.png", "\0png")
    return tmp_path


def asked(root: Path) -> list[str]:
    """The question's findings, over the files Git tracks below the root."""
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, timeout=30)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, timeout=30)
    return adoption.report(root)["findings"]["editions"]


# What the question names in the film of the fixture.
FOUND = [
    ".config/mise/config.toml:2 names assets/a.wav; write assets/audio/zh/narration-reference.wav",
    "NOTICE:2 names content/film-script.json; write content/zh/film-script.json",
    "tests/picture/page.mjs:1 names content/narration.md; this release removes it",
]


def test_each_former_path_is_named_with_its_file_its_line_and_what_to_write(film):
    assert asked(film) == FOUND


@pytest.mark.parametrize("ignore", ["/build/\n", ""])
def test_a_copy_inside_another_work_tree_that_tracks_none_of_it_is_read_whole(
    film, tmp_path_factory, ignore
):
    # A copy that `git archive` extracted below another repository's folder, ignored there or
    # untracked, as task 10.3 places its copies below the engine's build/.
    engine = tmp_path_factory.mktemp("engine")
    put(engine, ".gitignore", ignore)
    subprocess.run(["git", "init", "-q"], cwd=engine, check=True, timeout=30)
    copy = engine / "build" / "film"
    shutil.copytree(film, copy)
    if ignore:
        # One file added past the ignore rule leaves the rest of the ignored copy untracked.
        command = ["git", "add", "-f", "build/film/NOTICE"]
        subprocess.run(command, cwd=engine, check=True, timeout=30)
    assert adoption.report(copy)["findings"]["editions"] == FOUND


def test_the_declaration_s_former_cover_is_the_declaration_question_s(film):
    findings = adoption.report(film)["findings"]
    assert not any("reel-cover.png" in finding for finding in asked(film))
    assert any("declares cover" in finding for finding in findings["declaration"])


def test_a_film_with_everything_done_has_no_finding(film):
    put(film, "content/film.toml", 'slug = "reel"\n[editions.zh]\n[editions.en]\n')
    put(film, "content/voice-reference.json", "{}")
    put(film, "NOTICE", "Scripts: content/zh/film-script.json.\n")
    assert asked(film) == []


def test_a_declaration_that_does_not_load_is_still_read(film):
    # A field the loader refuses hides no former path; a declaration that is no TOML is named.
    put(film, "content/film.toml", DECLARATION + "unknown_field = 1\n")
    assert "NOTICE:2 names content/film-script.json; write content/zh/film-script.json" in asked(
        film
    )
    put(film, "content/film.toml", "slug = \n")
    assert asked(film) == []
    (finding,) = adoption.report(film)["findings"]["declaration"]
    assert finding.startswith("content/film.toml is not a film declaration")


def test_an_unreadable_file_is_named(film):
    (film / "NOTICE").write_bytes(b"Scripts: \xff\n")
    assert "NOTICE cannot be read as text: " in "\n".join(asked(film))


def test_the_recording_a_cast_s_derivation_cites_is_named_with_the_identity_s_place(film):
    # Every film's NOTICE names the recording its Chinese cast's derivation cites.
    cast = {"reference_audio": "assets/a.wav", "derivation": {"path": "assets/audio/voice.wav"}}
    put(film, "content/voice-reference.json", json.dumps(cast))
    put(film, "NOTICE", "Its identity recording, assets/audio/voice.wav, was generated.\n")
    assert "NOTICE:1 names assets/audio/voice.wav; write assets/audio/narrator-identity.wav" in (
        asked(film)
    )
