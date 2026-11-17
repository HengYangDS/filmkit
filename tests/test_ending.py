"""A command that is asked to end, as real processes: the engine's own code in a process of its
own over stand-in children, which load no model, no renderer and no browser. The commands
themselves are run for what they say and how they exit; the many trials of a second request run
what a command does with a request, without the rest of the command's imports.

Each scenario asks what a second request, at whatever interval after the first, must not change:
the children are ended and reaped, and the command says so in one line and ends as a shell
expects: with 128 and the signal's number after SIGTERM or a hang-up, and by the interrupt
itself after an interrupt. Where a command holds no child, a request has its usual effect.
"""

import json
import os
import pty
import signal
import subprocess
import sys
from pathlib import Path

import pytest
from real_processes import alive, gone, twice

# Every test here has the deadline of a test that starts real processes, and their end.
pytestmark = pytest.mark.usefixtures("processes")

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
# A command that holds no child while it runs: it takes no request.
IDLE = """
import time
import filmkit.child_processes as child_processes
with child_processes.ending("idle: stopped by {request}"):
    note("idle")
    time.sleep(30)
    note("idle-went-on")
"""
# A command that goes on unwinding after the block that took the request, until it is told to.
BETWEEN = """
import pathlib, sys, time
import filmkit.child_processes as child_processes
with child_processes.ending("between: stopped by {request}"):
    try:
        with child_processes.terminable():
            note("inside")
            time.sleep(30)
    finally:
        note("between")
        while not pathlib.Path(sys.argv[1]).exists():
            time.sleep(0.01)
        note("unwound")
"""
# A check that runs a tool by the engine's own run of one (`tools.run`) under `ending`, the tool a
# stand-in script that Python runs where the engine runs Node; and the tool, which ends what it
# started by its own handling of a request, taking CLOSING seconds over it, as a tool that
# drives a browser closes it. With DEAF it ignores the request to end.
CHECK = """
import pathlib, sys
import filmkit.child_processes as child_processes
import filmkit.tools as tools
tool = pathlib.Path(sys.argv[1])
tools.repository.ROOT = tool.parent
tools.picture_rendering.require_renderer = lambda: None
tools.picture_rendering.browser_path = lambda: "no-browser"
tools.shutil.which = lambda name: sys.executable
tools.stage_tools = lambda: tool.parent
tools.TOOLS = {"standin": tool.name}
if len(sys.argv) > 2:
    tools.STOP_SECONDS = float(sys.argv[2])
with child_processes.ending("check: stopped by {request}"):
    tools.run("standin", [])
"""
TOOL = """
import os, signal, sys, time
def closing(number, frame):
    note("tool-asked", number=number)
    time.sleep(float(os.environ.get("CLOSING", "0")))
    note("tool-closed-its-browser")
    raise SystemExit(0)
for number in (signal.SIGINT, signal.SIGTERM):
    signal.signal(number, signal.SIG_IGN if os.environ.get("DEAF") else closing)
note("tool")
time.sleep(30)
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


def exit_of(number: int) -> int:
    """How a command that acted on the request ends, as `Popen.returncode` reads it: by the
    interrupt itself, or with 128 and the number of SIGTERM or of a hang-up."""
    return -signal.SIGINT if number == signal.SIGINT else 128 + number


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
    command, children = narration(processes)
    command.send_signal(number)
    status, said = ended(processes, command)
    assert said == [STOPPED.format(request=REQUESTS[number])]
    assert status == exit_of(number)
    assert gone(children)


@pytest.mark.usefixtures("speech")
def test_the_synthesis_command_itself_ends_the_same_way(processes):
    command, children = narration(processes, "synthesis")
    command.send_signal(signal.SIGTERM)
    status, said = ended(processes, command)
    assert (status, said) == (143, [STOPPED.format(request=REQUESTS[signal.SIGTERM])])
    assert gone(children)


@pytest.mark.parametrize("number", [signal.SIGTERM, signal.SIGHUP])
def test_where_a_command_holds_no_child_a_request_to_end_has_its_usual_effect(processes, number):
    command = processes.python(processes.script("idle", IDLE))
    processes.noted("idle")
    command.send_signal(number)
    # The command ended by the signal's default action, as one that takes no request does.
    assert ended(processes, command) == (-number, [])


def test_an_interrupt_anywhere_ends_the_command_with_its_line_and_by_the_interrupt(processes):
    command = processes.python(processes.script("idle", IDLE))
    processes.noted("idle")
    command.send_signal(signal.SIGINT)
    assert ended(processes, command) == (-signal.SIGINT, ["idle: stopped by an interrupt"])
    assert not (processes.notes / "idle-went-on.json").exists()


@pytest.mark.parametrize("shell", ["/bin/sh", "/bin/bash"])
def test_a_shell_ends_its_script_when_the_command_it_ran_is_interrupted(processes, shell):
    if not Path(shell).exists():
        pytest.skip(f"no {shell}")
    idle, marker = processes.script("idle", IDLE), processes.folder / "next"
    script = f'"{sys.executable}" -B "{idle}"; echo next > "{marker}"'
    # A terminal's interrupt goes to the whole foreground group: the shell and the command.
    started = processes.start(
        [shell, "-c", script],
        env={**os.environ, "NOTES": str(processes.notes)},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    processes.noted("idle")
    os.killpg(started.pid, signal.SIGINT)
    _, said = started.communicate(timeout=30)
    assert said.splitlines() == ["idle: stopped by an interrupt"]
    # The command died by the interrupt, so the shell did not go on to the script's next line.
    assert not marker.exists()
    assert started.returncode in (-signal.SIGINT, 130)


def test_an_interrupted_check_lets_its_tool_end_what_the_tool_started(processes):
    tool = processes.script("tool", TOOL)
    check = processes.script("check", CHECK)
    command = processes.python(check, str(tool), session=True, CLOSING="1")
    processes.noted("tool")
    # A terminal's interrupt goes to the whole foreground group: the command and its tool.
    os.killpg(command.pid, signal.SIGINT)
    # The tool took the interrupt itself and needed a second for its own ending, longer than the
    # quarter second a wait used to give it; the command waited and did not kill it.
    assert processes.noted("tool-asked")["number"] == signal.SIGINT
    processes.noted("tool-closed-its-browser", 10)
    assert ended(processes, command) == (-signal.SIGINT, ["check: stopped by an interrupt"])


def test_an_interrupt_of_the_command_alone_has_its_tool_asked_to_end_and_waited_for(processes):
    tool = processes.script("tool", TOOL)
    command = processes.python(processes.script("check", CHECK), str(tool), CLOSING="1")
    asked = processes.noted("tool")["pid"]
    # The interrupt reaches the command and not its tool, as `kill -INT` of the command does.
    command.send_signal(signal.SIGINT)
    # The command asked the tool to end; the tool ran its own ending and was not killed.
    assert processes.noted("tool-asked")["number"] == signal.SIGTERM
    processes.noted("tool-closed-its-browser", 10)
    assert ended(processes, command) == (-signal.SIGINT, ["check: stopped by an interrupt"])
    assert gone([asked])


def test_a_tool_that_does_not_end_when_asked_is_killed_after_the_grace(processes):
    tool = processes.script("tool", TOOL)
    command = processes.python(processes.script("check", CHECK), str(tool), "0.3", DEAF="1")
    deaf = processes.noted("tool")["pid"]
    command.send_signal(signal.SIGINT)
    assert ended(processes, command) == (-signal.SIGINT, ["check: stopped by an interrupt"])
    # The tool ignored the request to end and was killed: it never ran its own ending.
    assert gone([deaf])
    assert not (processes.notes / "tool-closed-its-browser.json").exists()


def test_a_hang_up_whose_terminal_is_gone_still_exits_with_its_status(processes):
    standin = processes.script("standin", STANDIN)
    script = processes.script("narration", NARRATION)
    try:
        master, slave = pty.openpty()
    except OSError as error:
        pytest.skip(f"this host opens no pseudo-terminal: {error}")
    try:
        command = processes.start(
            [sys.executable, "-B", str(script), str(processes.folder), str(standin)]
            + [json.dumps(SHARES)],
            env={**os.environ, "NOTES": str(processes.notes)},
            stdin=subprocess.DEVNULL,
            stdout=slave,
            stderr=slave,
        )
    finally:
        os.close(slave)
    try:
        children = [processes.noted(name)["pid"] for name in CHILDREN]
    finally:
        # The terminal goes away: what the command writes to it from now on fails.
        os.close(master)
    command.send_signal(signal.SIGHUP)
    assert command.wait(timeout=30) == 129
    assert gone(children)


def test_requests_between_the_block_and_the_exit_do_not_end_the_command_early(processes):
    go = processes.folder / "go"
    command = processes.python(processes.script("between", BETWEEN), str(go))
    processes.noted("inside")
    command.send_signal(signal.SIGTERM)
    # The block that took the request has ended, and the command is still unwinding.
    processes.noted("between")
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        command.send_signal(number)
    assert command.poll() is None
    go.write_text("go on\n")
    assert ended(processes, command) == (143, ["between: stopped by a request to end (SIGTERM)"])


@pytest.mark.deadline(240)
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
    lowest number first, so an interrupt sent right after a SIGTERM may be the one it names.
    Which of the two a given interval gives is the host's to say; that a later request never
    replaces the one acted on is shown where the command says it is waiting (the test above)."""
    for delay in (0, 100, 200, 1000):
        command, children = narration(processes)
        twice(command.pid, signal.SIGTERM, signal.SIGINT, delay)
        status, said = ended(processes, command)
        acted = {exit_of(number): number for number in (signal.SIGINT, signal.SIGTERM)}[status]
        assert said == [STOPPED.format(request=REQUESTS[acted])]
        assert gone(children, 5)


@pytest.mark.deadline(240)
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
    assert status == exit_of(number)
    assert gone([renderer])
    record = processes.folder / "build/evidence/editions/zh/durations/render-picture.json"
    assert json.loads(record.read_text())["completed"] is False


@pytest.mark.deadline(240)
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
