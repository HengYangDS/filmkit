"""The sample film built as far as the light suite builds it, which the graph's tests share."""

import pytest
import sample_sound

import filmkit.repository as repository


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
