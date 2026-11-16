"""`render-picture --language all`: one child for each edition, the rendered pictures side by side
with the renderer's lock off, derivations in a row, and a failing edition named once both ended."""

import json
import signal
import sys

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.picture.together as together
import filmkit.produce as produce
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError


class Children:
    """Stand in for the children: each start is recorded with what had ended before it, and each
    child exits with the status set for its edition."""

    def __init__(self, monkeypatch, statuses=None):
        self.statuses = statuses or {}
        self.started = []
        self.ended = []
        self.signals = []
        monkeypatch.setattr(together.subprocess, "Popen", self.popen)

    def popen(self, command, *, cwd, env, stdin):
        code = command[command.index("--language") + 1]
        start = {"code": code, "command": command, "cwd": cwd, "env": env, "stdin": stdin}
        self.started.append({**start, "ended_before": list(self.ended)})
        children = self

        class Child:
            def wait(self, timeout=None):
                if code not in children.ended:
                    children.ended.append(code)
                status = children.statuses.get(code, 0)
                if isinstance(status, BaseException):
                    # The interrupt reaches the wait once; afterwards the child has ended.
                    children.statuses[code] = 130
                    raise status
                return status

            def poll(self):
                return None

            def send_signal(self, number):
                children.signals.append((code, number))

        return Child()


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.delenv("HYPERFRAMES_RENDER_LOCK", raising=False)
    return tmp_path.resolve()


def test_both_captioned_pictures_render_side_by_side_with_the_renderers_lock_off(
    root, monkeypatch, capsys
):
    children = Children(monkeypatch)
    assert together.render_all(deadline=900) == {"zh": 0, "en": 0}
    produce_command = [sys.executable, "-B", "-m", "filmkit.produce", "render-picture"]
    assert [start["command"] for start in children.started] == [
        [*produce_command, "--language", "zh", "--deadline", "900"],
        [*produce_command, "--language", "en", "--deadline", "900"],
    ]
    # Both children had started before either ended, each with the lock off and the film's root.
    assert [start["ended_before"] for start in children.started] == [[], []]
    for start in children.started:
        assert start["env"]["HYPERFRAMES_RENDER_LOCK"] == "off"
        assert start["env"]["FILMKIT_ROOT"] == str(root)
        assert start["cwd"] == root
    printed = json.loads(capsys.readouterr().out)
    assert (printed["pictures"], printed["side_by_side"]) == ("captioned", True)
    assert printed["exits"] == {"zh": 0, "en": 0}


def test_two_derivations_run_in_a_row_without_the_switch(root, monkeypatch):
    children = Children(monkeypatch)
    together.render_all(uncaptioned=True)
    assert [start["command"][-3:] for start in children.started] == [
        ["--language", "zh", "--uncaptioned"],
        ["--language", "en", "--uncaptioned"],
    ]
    assert [start["ended_before"] for start in children.started] == [[], ["zh"]]
    assert all("HYPERFRAMES_RENDER_LOCK" not in start["env"] for start in children.started)


def test_two_native_uncaptioned_renders_run_side_by_side(root, monkeypatch):
    children = Children(monkeypatch)
    together.render_all(uncaptioned=True, native=True)
    assert [start["command"][-2:] for start in children.started] == [
        ["--uncaptioned", "--native"]
    ] * 2
    assert [start["ended_before"] for start in children.started] == [[], []]
    assert all(start["env"]["HYPERFRAMES_RENDER_LOCK"] == "off" for start in children.started)


def test_a_film_of_another_capture_renders_its_uncaptioned_pictures_side_by_side(root, monkeypatch):
    picture = FILM.picture.model_copy(update={"capture": "fast"})
    monkeypatch.setattr(picture_rendering, "FILM", FILM.model_copy(update={"picture": picture}))
    children = Children(monkeypatch)
    together.render_all(uncaptioned=True)
    assert [start["command"][-1] for start in children.started] == ["--uncaptioned"] * 2
    assert [start["ended_before"] for start in children.started] == [[], []]
    assert all(start["env"]["HYPERFRAMES_RENDER_LOCK"] == "off" for start in children.started)


@pytest.mark.parametrize("uncaptioned", [False, True])
def test_a_failing_edition_is_named_once_the_other_has_ended(root, monkeypatch, uncaptioned):
    children = Children(monkeypatch, {"zh": 1})
    pictures = "uncaptioned" if uncaptioned else "captioned"
    with pytest.raises(PictureError, match=rf"{pictures} picture was made: zh \(exit 1\)$"):
        together.render_all(uncaptioned=uncaptioned)
    assert children.ended == ["zh", "en"]
    assert [start["code"] for start in children.started] == ["zh", "en"]


def test_an_interrupt_reaches_the_children_so_each_stops_its_renderer(root, monkeypatch):
    children = Children(monkeypatch, {"zh": KeyboardInterrupt()})
    with pytest.raises(KeyboardInterrupt):
        together.render_all()
    assert children.signals == [("zh", signal.SIGINT), ("en", signal.SIGINT)]
    assert children.ended == ["zh", "en"]


def test_the_command_makes_both_editions_and_writes_no_duration_record_of_its_own(
    root, monkeypatch
):
    calls = []
    monkeypatch.setattr(produce, "render_all", lambda **options: calls.append(options))
    produce.main(["render-picture", "--language", "all"])
    produce.main(["render-picture", "--language", "all", "--uncaptioned", "--deadline", "600"])
    produce.main(["render-picture", "--language", "all", "--uncaptioned", "--native"])
    assert calls == [
        {"uncaptioned": False, "native": False, "deadline": None},
        {"uncaptioned": True, "native": False, "deadline": 600},
        {"uncaptioned": True, "native": True, "deadline": None},
    ]
    assert not (root / "build").exists()


def test_the_commands_refusal_names_the_action(root, monkeypatch):
    def refuse(**options):
        message = "Not every edition's captioned picture was made: en (exit 1)"
        raise PictureError(message)

    monkeypatch.setattr(produce, "render_all", refuse)
    with pytest.raises(SystemExit, match="^render-picture: Not every edition's captioned"):
        produce.main(["render-picture", "--language", "all"])


@pytest.mark.parametrize("action", ["validate-picture", "compare-pictures", "stage-picture"])
def test_all_applies_only_to_render_picture(root, action, capsys):
    with pytest.raises(SystemExit) as refused:
        produce.main([action, "--language", "all"])
    assert refused.value.code == 2
    assert "--language all applies only to render-picture" in capsys.readouterr().err
