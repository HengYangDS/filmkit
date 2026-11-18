"""What the suite asks of its host before it runs the tests that need it."""

from types import SimpleNamespace

import pytest


@pytest.fixture
def suite(request):
    """The suite's configuration module, found by what it holds: two modules are named conftest."""
    plugins = request.config.pluginmanager.get_plugins()
    return [plugin for plugin in plugins if hasattr(plugin, "HOST_TOOLS")][0]


@pytest.mark.parametrize(("status", "evaluates"), [(0, True), (1, False)])
def test_the_device_is_asked_for_an_evaluation_in_a_child_process(
    suite, monkeypatch, status, evaluates
):
    asked = []

    def run(command, **options):
        asked.append((command, options))
        return SimpleNamespace(returncode=status)

    monkeypatch.setattr(suite, "collect_ignore", [])
    monkeypatch.setattr(suite.subprocess, "run", run)
    assert suite.metal_evaluates() is evaluates
    [(command, options)] = asked
    assert "mx.eval" in command[-1]
    assert options["timeout"] == 120


def test_a_probe_that_does_not_end_is_a_device_that_does_not_evaluate(suite, monkeypatch):
    def run(command, **options):
        raise suite.subprocess.TimeoutExpired(command, options["timeout"])

    monkeypatch.setattr(suite, "collect_ignore", [])
    monkeypatch.setattr(suite.subprocess, "run", run)
    assert suite.metal_evaluates() is False


def test_a_host_whose_speech_runtime_does_not_load_is_not_asked(suite, monkeypatch):
    monkeypatch.setattr(suite, "collect_ignore", ["narration/test_synthesis.py"])
    monkeypatch.setattr(suite.subprocess, "run", lambda *_, **__: pytest.fail("asked"))
    assert suite.metal_evaluates() is False


def test_a_test_marked_metal_is_skipped_and_named_where_the_device_evaluates_nothing(
    suite, monkeypatch
):
    class Item:
        nodeid = "tests/narration/test_synthesis.py::evaluates"

        def __init__(self, marked):
            self.marked, self.added = marked, []

        def get_closest_marker(self, name):
            return object() if name in self.marked else None

        def add_marker(self, marker):
            self.added.append(marker)

    absent = suite.HOST_TOOLS["metal"]._replace(present=False)
    monkeypatch.setattr(suite, "HOST_TOOLS", {"metal": absent})
    monkeypatch.setattr(suite, "host_skipped", {"metal": []})
    evaluates, other = Item({"metal"}), Item({"ffmpeg"})
    suite.pytest_collection_modifyitems([evaluates, other])
    [skip] = evaluates.added
    assert skip.kwargs["reason"] == "the host Metal evaluation fails"
    assert other.added == []
    assert suite.host_skipped == {"metal": [Item.nodeid]}
