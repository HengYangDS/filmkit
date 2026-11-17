"""A render as real processes: the engine's own run of a renderer in a process of its own, over a
stand-in renderer that ignores a request to end, as a renderer at its worst does, notes every
signal it gets and renders nothing."""

import os
import signal
import subprocess
import sys
import textwrap
import time

import pytest

# The stand-in renderer: it notes itself, ignores SIGTERM and sleeps until it is killed.
RENDERER = """
    import os, pathlib, signal, sys, time
    notes = pathlib.Path(sys.argv[1])
    got = lambda number, frame: open(notes / "renderer.signals", "a").write(f"{number}\\n")
    signal.signal(signal.SIGTERM, got)
    (notes / "renderer.pid").write_text(str(os.getpid()))
    time.sleep(120)
"""
# The command: the engine's own run of a renderer, with its grace shortened, which notes how the
# run ended.
COMMAND = """
    import pathlib, sys
    import filmkit.picture.rendering as rendering
    rendering.STOP_GRACE_SECONDS = float(sys.argv[3])
    renderer, notes = sys.argv[1:3]
    try:
        rendering.run_renderer([sys.executable, renderer, notes], 120)
    except BaseException as error:
        (pathlib.Path(notes) / "command.ended").write_text(type(error).__name__)
        raise
"""
GRACE = 1.0


def alive(pid: int) -> bool:
    """Whether a process still runs; one that ended and awaits its parent's wait does not."""
    listed = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    return bool(listed.stdout.strip()) and not listed.stdout.strip().startswith("Z")


def wait_for(condition, seconds=30.0) -> bool:
    ends = time.monotonic() + seconds
    while time.monotonic() < ends:
        if condition():
            return True
        time.sleep(0.05)
    return condition()


class Render:
    """A command that runs a stand-in renderer, and what both noted."""

    def __init__(self, folder):
        self.notes = folder / "notes"
        self.notes.mkdir(parents=True)
        for name, text in (("renderer", RENDERER), ("command", COMMAND)):
            (folder / f"{name}.py").write_text(textwrap.dedent(text))
        command = [sys.executable, "-B", str(folder / "command.py"), str(folder / "renderer.py")]
        self.process = subprocess.Popen(
            [*command, str(self.notes), str(GRACE)],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert wait_for((self.notes / "renderer.pid").is_file)
        time.sleep(0.3)
        self.renderer = int((self.notes / "renderer.pid").read_text())

    def signals(self) -> list[str]:
        noted = self.notes / "renderer.signals"
        return noted.read_text().split() if noted.is_file() else []

    def ended(self) -> str:
        return (self.notes / "command.ended").read_text()

    def clear(self) -> None:
        """Kill whatever a failed test left."""
        if alive(self.renderer):
            os.kill(self.renderer, signal.SIGKILL)
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()


@pytest.fixture
def render(tmp_path):
    started = Render(tmp_path)
    yield started
    started.clear()


def test_a_render_asked_to_end_ends_its_renderer(render):
    render.process.send_signal(signal.SIGTERM)
    assert render.process.wait(timeout=30) != 0
    # The renderer was asked once to end and, having ignored that, was killed after the grace.
    assert not alive(render.renderer)
    assert render.signals() == [str(int(signal.SIGTERM))]
    assert render.ended() == "Terminated"


def test_a_second_interrupt_does_not_cut_the_renderers_end_short(render):
    render.process.send_signal(signal.SIGINT)
    # The second interrupt arrives while the command waits out the renderer's grace.
    time.sleep(0.6)
    render.process.send_signal(signal.SIGINT)
    assert render.process.wait(timeout=30) != 0
    assert not alive(render.renderer)
    assert render.signals() == [str(int(signal.SIGTERM))]
    # An interrupt ends the run as every request to end does, by `Terminated`.
    assert render.ended() == "Terminated"
