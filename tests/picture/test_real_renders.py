"""A render as real processes: the engine's own run of a renderer in a process of its own, over a
stand-in renderer that ignores a request to end, as a renderer at its worst does, notes every
signal it gets and renders nothing. A test waits for what the renderer notes, and both processes
are ended with their test (`processes`)."""

import signal

import pytest
from real_processes import alive

# Every test here has the deadline of a test that starts real processes, and their end.
pytestmark = pytest.mark.usefixtures("processes")

# The stand-in renderer: it notes each signal it gets, ignores SIGTERM and sleeps until it is
# killed. It reports that it runs only once it ignores the request.
RENDERER = """
import signal, time
got = []
def asked(number, frame):
    got.append(number)
    note("renderer-asked", signals=got)
signal.signal(signal.SIGTERM, asked)
note("renderer")
while True:
    time.sleep(60)
"""
# The command: the engine's own run of a renderer, with its grace shortened, which notes how the
# run ended.
COMMAND = """
import sys
import filmkit.picture.renderer as renderer
renderer.STOP_GRACE_SECONDS = float(sys.argv[2])
try:
    renderer.run_renderer([sys.executable, "-B", sys.argv[1]], 120)
except BaseException as error:
    note("command-ended", how=type(error).__name__)
    raise
"""
GRACE = 1.0


@pytest.fixture
def render(processes):
    """A command that runs the stand-in renderer, which runs: the command and the renderer's
    process id."""
    renderer = processes.script("renderer", RENDERER)
    command = processes.python(processes.script("command", COMMAND), str(renderer), str(GRACE))
    return command, processes.noted("renderer")["pid"]


def test_a_render_asked_to_end_ends_its_renderer(processes, render):
    command, renderer = render
    command.send_signal(signal.SIGTERM)
    assert command.wait(timeout=30) != 0
    # The renderer was asked once to end and, having ignored that, was killed after the grace.
    assert not alive(renderer)
    assert processes.noted("renderer-asked", 0)["signals"] == [signal.SIGTERM]
    assert processes.noted("command-ended", 0)["how"] == "Terminated"


def test_a_second_interrupt_does_not_cut_the_renderers_end_short(processes, render):
    command, renderer = render
    command.send_signal(signal.SIGINT)
    # The renderer has been asked to end: the command now waits out its grace, and the second
    # interrupt arrives in that wait.
    processes.noted("renderer-asked")
    command.send_signal(signal.SIGINT)
    assert command.wait(timeout=30) != 0
    assert not alive(renderer)
    assert processes.noted("renderer-asked", 0)["signals"] == [signal.SIGTERM]
    # An interrupt ends the run as every request to end does, by `Terminated`.
    assert processes.noted("command-ended", 0)["how"] == "Terminated"
