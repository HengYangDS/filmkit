"""The refusals that name a step to run name the verb that runs it (design decision 18 of
build-a-film-by-its-verbs): `filmkit build <node>:<code>` for a node, `filmkit review set-aside`
for the set-aside, and never the retired `produce` command."""

import ast
import re
from pathlib import Path

import filmkit.picture.faults as faults
from filmkit.graph import chain, target
from filmkit.production import Edition
from filmkit.review import set_aside

SOURCE = Path(chain.__file__).resolve().parents[1]


def texts() -> list[tuple[str, str]]:
    """Every string the engine's Python modules hold, each with its file: whole literals and the
    literal parts of f-strings."""
    found = []
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.append((path.relative_to(SOURCE).as_posix(), node.value))
    return found


def test_a_node_is_named_by_the_verb_that_builds_it():
    assert target("check-picture", "zh") == "filmkit build check-picture:zh"
    assert target("check") == "filmkit build check"
    assert Edition("zh").unassembled().args[0].endswith("run filmkit build assemble:zh")
    assert faults.render_again("en", "captioned").startswith("filmkit build render-picture:en, ")
    assert faults.REPAIR.format(code="zh") == "python -m filmkit.picture.repair --language zh"
    assert set_aside.SET_ASIDE_COMMAND.startswith("filmkit review set-aside --round {number}")


def test_no_string_of_the_engine_names_a_node_to_run_without_its_verb_or_names_produce():
    names = "|".join(re.escape(node.name) for node in chain.TABLE)
    bare = re.compile(rf"\brun ({names})\b")
    found = [
        (path, text)
        for path, text in texts()
        if bare.search(text) or re.search(r"\bproduce\b", text)
    ]
    assert found == []
