"""The sample film built as far as the light suite builds it, which the graph's tests share."""

import pytest
import sample_sound
import stand_ins

import filmkit.repository as repository
from filmkit.graph import opens, runs


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """A copy of the sample after the commands of `sample_sound.CHAIN`, each run as the film's
    task runs it on stand-in takes, with what each opened recorded: its root and the log."""
    out = tmp_path_factory.mktemp("sample")
    root = sample_sound.copy_film((out / "film").resolve())
    log = out / "opens.jsonl"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(repository, "ROOT", root)
        for code in sample_sound.NARRATED:
            # The stand-in narration runs through the seam, as `narrate` does, and is recorded.
            with runs.run(code, "narrate"):
                sample_sound.narrate(code)
    for command, code in sample_sound.CHAIN:
        sample_sound.run(root, command, code, log)
    return root, log


@pytest.fixture
def sound_chain(built, monkeypatch):
    """The built sample as the film's root, read and never written by a test."""
    root, _ = built
    monkeypatch.setattr(repository, "ROOT", root)
    return root


@pytest.fixture
def stand_in_table(tmp_path, monkeypatch):
    """A scratch film root whose node table is the stand-in one (`stand_ins`); the loaded table."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in stand_ins.TABLE})
    monkeypatch.delenv(opens.NODE, raising=False)
    return stand_ins.scratch(root)


@pytest.fixture
def one_node(tmp_path, monkeypatch):
    """A scratch film root whose table is the engine's with one stand-in node, `stand`, which
    reads in.txt and writes out.txt (`stand_ins.run_stand`); the root."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    (root / "in.txt").write_text("in")
    table = {"stand": stand_ins.stand_in("stand", {"in": "in.txt"}, {"out": "out.txt"})}
    table |= {name: node for name, node in runs.table().items() if name != "stand"}
    monkeypatch.setattr(runs, "table", lambda: table)
    monkeypatch.delenv(opens.NODE, raising=False)
    return root
