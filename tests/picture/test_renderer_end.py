"""How a run of a renderer ends: the renderer's end is waited for without reaping it, and what is
left of its process group is ended while its number is still its own. Stand-in renderers, which
render nothing."""

import sys

import pytest
from real_processes import gone

import filmkit.picture.rendering as rendering

# A renderer that starts a worker, waits until the worker runs and exits with the status given.
RENDERER = """
import subprocess, sys, time
subprocess.Popen([sys.executable, "-B", sys.argv[1]])
while not (pathlib.Path(os.environ["NOTES"]) / "worker.json").is_file():
    time.sleep(0.01)
raise SystemExit(int(sys.argv[2]))
"""
WORKER = """
import time
note("worker")
time.sleep(60)
"""


@pytest.fixture
def run(processes, tmp_path, monkeypatch):
    """Run a stand-in renderer that leaves a worker running and exits with the status given:
    what the run returned and the worker's process id."""
    monkeypatch.setattr(rendering.repository, "ROOT", tmp_path)
    monkeypatch.setenv("NOTES", str(processes.notes))
    renderer, worker = processes.script("renderer", RENDERER), processes.script("worker", WORKER)

    def started(status: int):
        command = [sys.executable, "-B", str(renderer), str(worker), str(status)]
        returned = rendering.run_renderer(command, 30)
        return returned, processes.noted("worker")["pid"]

    return started


@pytest.mark.parametrize("status", [0, 3])
def test_what_a_renderer_left_running_is_ended_whatever_its_exit(run, status):
    returned, worker = run(status)
    assert returned == (status, False)
    assert gone([worker], 5)


def test_the_renderer_is_not_reaped_before_its_group_is_stopped(run, monkeypatch):
    stop, handed = rendering.child_processes.stop, []

    def stopping(children, asking, **options):
        handed.extend(child.returncode for child in children)
        stop(children, asking, **options)

    monkeypatch.setattr(rendering.child_processes, "stop", stopping)
    returned, worker = run(3)
    # Its return code was unknown when it was handed over: it had ended and was not reaped.
    assert handed == [None]
    assert returned == (3, False)
    assert gone([worker], 5)
