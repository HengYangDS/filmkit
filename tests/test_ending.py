"""A command that is asked to end, as real processes: the engine's own code in a process of its
own over stand-in children, which load no model, no renderer and no browser. The commands
themselves are run for what they say and how they exit; the many trials of a second request run
what a command does with a request, without the rest of the command's imports.

Each scenario asks what a second request, at whatever interval after the first, must not change:
the children are ended and reaped, and the command says so in one line and exits with 128 and
the signal's number.
"""

import json
import os
import signal

import pytest
from real_processes import alive, gone, twice

# A stand-in for a narration process or a renderer: it notes that it runs and waits to be ended.
# With LINGER it takes that many seconds to end once it is asked to, and notes that it was asked.
STANDIN = """
import os, signal, sys, time
def asked(number, frame):
    note(sys.argv[1] + "-asked")
    time.sleep(float(os.environ["LINGER"]))
    raise SystemExit(0)
if os.environ.get("LINGER"):
    signal.signal(signal.SIGTERM, asked)
note(sys.argv[1])
time.sleep(30)
"""
# What the synthesis does with a request to end, around the engine's narration in processes with
# the stand-in as each process's command; `synthesis.main` is these two calls (SYNTHESIS).
NARRATION = """
import json, pathlib, sys
import filmkit.child_processes as child_processes
import filmkit.narration.processes as processes
root, standin, shares = pathlib.Path(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3])
processes.repository.ROOT = root
processes.child_command = lambda sources, ids, receipt: [
    sys.executable, "-B", standin, "process-" + "-".join(ids)
]
def narrate(argv=None):
    return processes.narrate(("script", "cast", "folder"), shares, root / "build/receipt.json")
if __name__ == "__main__":
    with child_processes.ending("The narration was stopped by {request}"):
        narrate()
"""
# The synthesis command itself over the same narration.
SYNTHESIS = """
import narration
import filmkit.narration.synthesis as synthesis
synthesis.narrate = narration.narrate
synthesis.main([])
"""
# The narration command itself, its one step the script given.
NARRATE = """
import pathlib, sys
import filmkit.narration.narrate as narrate
narrate.repository.ROOT = pathlib.Path(sys.argv[1])
narrate.gate = lambda code: {}
narrate.steps = lambda code, ids, scope: [("narration", [sys.executable, "-B", *sys.argv[2:]])]
narrate.main(["--language", "zh"])
"""
# What a production action does with a request to end, around the engine's own run of a
# stand-in renderer; `produce.main` is this around its action (PRODUCE).
RENDER = """
import pathlib, sys
import filmkit.child_processes as child_processes
import filmkit.picture.rendering as rendering
rendering.repository.ROOT = pathlib.Path(sys.argv[1])
renderer = [sys.executable, "-B", sys.argv[2], "renderer"]
def render(edition=None, options=None):
    return rendering.run_renderer(renderer, 120)
if __name__ == "__main__":
    with child_processes.ending("render-picture: stopped by {request}"):
        render()
"""
# The production command itself, its render the same run.
PRODUCE = """
import render
import filmkit.produce as produce
produce.EDITION_ACTIONS["render-picture"] = render.render
produce.main(["render-picture", "--language", "zh"])
"""
SHARES = [["01", "04"], ["02", "03"]]
CHILDREN = ("process-01-04", "process-02-03")
STOPPED = (
    "The narration was stopped by {request}; every narration process it had started (2) was "
    "ended with it; their logs are in build/runtime/work/narration-processes/build-receipt"
)
REQUESTS = {
    signal.SIGINT: "an interrupt",
    signal.SIGTERM: "a request to end (SIGTERM)",
    signal.SIGHUP: "a hang-up (SIGHUP)",
}
# Microseconds between a first and a second request: across the interval in which a second one
# used to end the command at once (about 50 to 230), and well to both sides of it.
DELAYS = (0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 300, 400, 600, 1000, 3000, 10000)


def narration(processes, command="narration", **variables):
    """The narration, or the synthesis command over it, with two stand-in processes running."""
    standin = processes.script("standin", STANDIN)
    for name, text in (("narration", NARRATION), ("synthesis", SYNTHESIS)):
        processes.script(name, text)
    arguments = (str(processes.folder), str(standin), json.dumps(SHARES))
    started = processes.python(processes.folder / f"{command}.py", *arguments, **variables)
    return started, [processes.noted(name)["pid"] for name in CHILDREN]


def ended(processes, command, seconds: float = 30) -> tuple[int, list[str]]:
    """A command's exit status and the lines it wrote to standard error, once it has ended; the
    notes of its run are set aside for the next one."""
    _, said = command.communicate(timeout=seconds)
    processes.forget()
    return command.returncode, said.splitlines()


@pytest.mark.parametrize("number", list(REQUESTS))
def test_a_request_to_end_ends_the_children_and_the_command_with_one_line(processes, number):
    command, children = narration(processes, "synthesis")
    command.send_signal(number)
    status, said = ended(processes, command)
    assert said == [STOPPED.format(request=REQUESTS[number])]
    assert status == 128 + number
    assert gone(children)


def test_a_second_request_at_any_interval_changes_nothing_for_a_narration(processes):
    failed = []
    for trial, delay in enumerate(DELAYS * 3):
        command, children = narration(processes)
        twice(command.pid, signal.SIGTERM, signal.SIGTERM, delay)
        status, said = ended(processes, command)
        left = not gone(children, 5)
        if left or status != 143 or said != [STOPPED.format(request=REQUESTS[signal.SIGTERM])]:
            failed.append({"trial": trial, "microseconds": delay, "status": status, "left": left})
    assert failed == []


@pytest.mark.parametrize("second", list(REQUESTS))
def test_a_request_while_the_children_are_being_ended_does_not_cut_their_end_short(
    processes, second
):
    command, children = narration(processes, LINGER="0.5")
    command.send_signal(signal.SIGTERM)
    # Both children have been asked to end and take their time: the command is waiting for them.
    for name in CHILDREN:
        processes.noted(f"{name}-asked")
    command.send_signal(second)
    command.wait(timeout=30)
    # The command exited only once both had ended, by the request it had acted on.
    assert not any(alive(child) for child in children)
    assert ended(processes, command) == (143, [STOPPED.format(request=REQUESTS[signal.SIGTERM])])


def test_two_different_requests_end_the_command_once_by_the_one_it_acted_on(processes):
    """Two requests that both arrive before the process has acted on either are handed to it
    lowest number first, so an interrupt sent right after a SIGTERM may be the one it names."""
    for delay in (0, 100, 200, 1000, 50000):
        command, children = narration(processes)
        twice(command.pid, signal.SIGTERM, signal.SIGINT, delay)
        status, said = ended(processes, command)
        assert status in (130, 143)
        assert said == [STOPPED.format(request=REQUESTS[status - 128])]
        assert gone(children, 5)
    assert status == 143


def test_a_request_to_the_narrations_group_which_the_narration_relays_leaves_no_child(processes):
    """`narrate` and its step share a process group. A request to the group reaches both, and
    `narrate` then asks its step to end as well: the step gets the request twice."""
    standin = processes.script("standin", STANDIN)
    step = processes.script("narration", NARRATION)
    narrate = processes.script("narrate", NARRATE)
    root = str(processes.folder)
    expected = [
        STOPPED.format(request=REQUESTS[signal.SIGTERM]),
        "The narration was stopped by a request to end (SIGTERM); its running step was ended "
        "with it",
    ]
    failed = []
    for trial in range(10):
        command = processes.python(
            narrate, root, str(step), root, str(standin), json.dumps(SHARES), session=True
        )
        children = [processes.noted(name)["pid"] for name in CHILDREN]
        os.killpg(command.pid, signal.SIGTERM)
        status, said = ended(processes, command)
        left = not gone(children, 5)
        if left or status != 143 or said != expected:
            failed.append({"trial": trial, "status": status, "left": left, "said": said})
    assert failed == []
    record = processes.folder / "build/evidence/editions/zh/durations/narrate.json"
    assert json.loads(record.read_text())["completed"] is False


def render(processes, command="render"):
    """The render, or the production command over it, with the stand-in renderer running."""
    standin = processes.script("standin", STANDIN)
    for name, text in (("render", RENDER), ("produce", PRODUCE)):
        processes.script(name, text)
    script = processes.folder / f"{command}.py"
    started = processes.python(script, str(processes.folder), str(standin))
    return started, processes.noted("renderer")["pid"]


@pytest.mark.parametrize("number", list(REQUESTS))
def test_a_request_to_end_ends_the_renderer_and_the_render_with_one_line(processes, number):
    command, renderer = render(processes, "produce")
    command.send_signal(number)
    status, said = ended(processes, command)
    assert said == [f"render-picture: stopped by {REQUESTS[number]}"]
    assert status == 128 + number
    assert gone([renderer])
    record = processes.folder / "build/evidence/editions/zh/durations/render-picture.json"
    assert json.loads(record.read_text())["completed"] is False


def test_a_second_request_at_any_interval_changes_nothing_for_a_render(processes):
    failed = []
    for trial, delay in enumerate(DELAYS * 2):
        command, renderer = render(processes)
        twice(command.pid, signal.SIGTERM, signal.SIGTERM, delay)
        status, said = ended(processes, command)
        left = not gone([renderer], 5)
        expected = ["render-picture: stopped by a request to end (SIGTERM)"]
        if left or status != 143 or said != expected:
            failed.append({"trial": trial, "microseconds": delay, "status": status, "left": left})
    assert failed == []
