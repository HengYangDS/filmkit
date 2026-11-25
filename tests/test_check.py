"""`filmkit check`, the film's light gates on its sources: every finding at once, the verdict and
the occurrence plans it writes (design decision 6 of build-a-film-by-its-verbs)."""

import os
import shutil
import sys
from pathlib import Path

import pytest

import filmkit.check as check
import filmkit.concepts as concepts
import filmkit.film as film
import filmkit.register as register
import filmkit.released as released
import filmkit.repository as repository
from filmkit.graph import cli
from filmkit.narration import anchors, readings
from filmkit.picture import anchor_reads
from filmkit.production import Edition

# The sample's tracked sources, which the check reads.
SOURCES = ("VERSION", "assets", "content", "picture")
SAMPLE = repository.ROOT


@pytest.fixture
def copied(tmp_path, monkeypatch):
    """A copy of the sample's sources as the film's root, with the engine's npm packages beside
    them; the pins and locks, which stand above the sample in the engine's repository, are asked
    of the sample there."""
    root = (tmp_path / "film").resolve()
    root.mkdir()
    for name in SOURCES:
        source = SAMPLE / name
        if source.is_dir():
            shutil.copytree(source, root / name)
        else:
            shutil.copy2(source, root / name)
    (root / "node_modules").symlink_to(repository.node_modules())
    monkeypatch.setattr(repository, "ROOT", root)
    npm, lock = check.npm_packages, check.python_lock
    monkeypatch.setattr(check, "npm_packages", lambda _root: npm(SAMPLE))
    monkeypatch.setattr(check, "python_lock", lambda _root, not_read: lock(SAMPLE, not_read))
    return root


def test_the_sample_passes_every_question():
    verdict = check.asked(repository.ROOT, write=False)
    assert verdict["findings"] == dict.fromkeys(check.QUESTIONS, [])
    assert verdict["outcome"] == "pass"
    reads = verdict["picture_reads"]
    assert (reads["verdict"], reads["not_loaded"]) == ("pass", {})


def refusing(error: type[Exception], line: str):
    def refuse(*_args, **_options):
        raise error(line)

    return refuse


def test_one_run_names_a_finding_of_every_question(copied, monkeypatch):
    read = film.read
    monkeypatch.setattr(film, "read", lambda root: (read(root)[0], ["declaration finding"]))
    monkeypatch.setattr(concepts, "check", refusing(concepts.ConceptError, "concept finding"))
    monkeypatch.setattr(register, "check", refusing(register.RegisterError, "register finding"))
    monkeypatch.setattr(readings, "check", refusing(readings.ReadingError, "reading finding"))
    monkeypatch.setattr(anchors, "require_editions", refusing(anchors.AnchorError, "anchor rule"))
    monkeypatch.setattr(anchor_reads, "check", refusing(anchors.AnchorError, "unmarked read"))
    for name in ("npm_packages", "picture_template", "runtime"):
        monkeypatch.setattr(check, name, lambda _root, n=name: [f"{n} finding"])
    monkeypatch.setattr(check, "python_lock", lambda _root, read: ["python_lock finding"])
    verdict = check.asked(repository.ROOT, write=False)
    assert verdict["findings"] == {
        "declaration": ["declaration finding"],
        "concepts": ["concept finding"],
        "register": ["register finding"],
        "readings": ["zh: reading finding", "en: reading finding"],
        "anchors": ["anchor rule"],
        "picture_reads": ["unmarked read"],
        "npm_packages": ["npm_packages finding"],
        "python_lock": ["python_lock finding"],
        "template": ["picture_template finding"],
        "runtime": ["runtime finding"],
    }
    assert verdict["outcome"] == "refuse"
    with pytest.raises(SystemExit) as refused:
        check.run()
    line = str(refused.value.code)
    assert "\n" not in line and line.startswith("check: 11 findings: declaration: ")
    assert "| runtime: runtime finding" in line


def test_another_vale_is_refused_naming_both_versions_and_the_pin(copied, tmp_path, monkeypatch):
    other = tmp_path / "bin/vale"
    other.parent.mkdir()
    other.write_text(f"#!{sys.executable}\nprint('vale version 9.9.9')\n")
    other.chmod(0o755)
    monkeypatch.setenv("PATH", f"{other.parent}:{os.environ['PATH']}")
    verdict = check.asked(repository.ROOT, write=False)
    (line,) = verdict["findings"]["register"]
    assert "reports Vale 9.9.9" in line
    assert f"runs Vale {released.vale()}" in line
    assert line.endswith(f"mise use github:vale-cli/vale@{released.vale()}")
    assert verdict["outcome"] == "refuse"


def test_a_picture_that_does_not_load_is_not_judged_and_refuses_nothing(copied):
    (copied / "picture/film.js").write_text('throw Error("broken\\nwhile it loads");')
    verdict = check.asked(repository.ROOT, write=False)
    reads = verdict["picture_reads"]
    assert reads["verdict"] == "not judged"
    loaded = "The composition does not load: broken"
    assert reads["not_loaded"] == {"zh": loaded, "en": loaded}
    assert verdict["findings"]["picture_reads"] == []


def test_a_passing_run_writes_the_same_verdict_after_an_edit_of_one_script(copied):
    assert check.run()["outcome"] == "pass"
    written = (copied / check.VERDICT).read_bytes()
    plans = {code: (copied / readings.plan_path(code)).is_file() for code in ("zh", "en")}
    assert plans == {"zh": True, "en": True}
    script = copied / Edition("zh").script
    script.write_text(script.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    check.run()
    assert (copied / check.VERDICT).read_bytes() == written


def listing(root) -> dict[str, bytes]:
    """Every file below a film's root with its bytes, `build/` included, the npm packages' link
    not followed."""
    found = {}
    for folder, _, files in os.walk(root):
        for name in files:
            path = os.path.join(folder, name)
            found[os.path.relpath(path, root)] = Path(path).read_bytes()
    return found


def test_a_read_only_check_writes_no_file_whether_it_passes_or_refuses(copied, capsys):
    before = listing(copied)
    cli.main(["check", "--read-only"])
    assert "filmkit check passes" in capsys.readouterr().out
    assert listing(copied) == before
    (copied / "picture/index.html").unlink()
    before = listing(copied)
    with pytest.raises(SystemExit) as refused:
        cli.main(["check", "--read-only"])
    assert refused.value.code == 1
    said = capsys.readouterr().out.splitlines()
    assert said[0].startswith("template: no ") and said[-1].startswith("filmkit check refuses")
    assert listing(copied) == before


def test_a_form_the_register_refuses_is_named_with_its_place(copied, monkeypatch):
    # Narration's gate asked this before synthesis until the source check took it over.
    held = {"zh": [concepts.Place("zh 01.1", "你们先看。")], "en": []}
    monkeypatch.setattr(concepts, "places", lambda *_: held)
    verdict = check.asked(repository.ROOT, write=False)
    assert verdict["findings"]["register"] == ["zh 01.1: '你们' addresses the audience (R1)"]
    assert verdict["outcome"] == "refuse"


def test_a_reading_the_edition_does_not_declare_is_named_with_its_edition(copied, monkeypatch):
    def refuse(code, *, write):
        message = f"{code} 04.2 at 9: 重 in “代码和日期去重。” has no declared reading"
        raise readings.ReadingError(message)

    monkeypatch.setattr(readings, "check", refuse)
    found = check.asked(repository.ROOT, write=False)["findings"]["readings"]
    assert found == [
        "zh: zh 04.2 at 9: 重 in “代码和日期去重。” has no declared reading",
        "en: en 04.2 at 9: 重 in “代码和日期去重。” has no declared reading",
    ]
