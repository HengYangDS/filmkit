"""Stopping the children a command started: the signal to each child or to its whole process
group, the wait, the kill of what does not end, and a request to end as an exception.

The children are real processes, which report when they are ready and are ended with their test
(`processes`). What must take a real signal runs in a process of its own, never in the test
run's: a test that hands this process a request does so as the interpreter does, by a call.
"""

import json
import os
import signal
import subprocess
import sys
import time

import pytest
from real_processes import alive, gone

import filmkit.child_processes as child_processes
import filmkit.tools as tools
from filmkit.child_processes import Terminated

# Every test here has the deadline of a test that starts real processes, and their end.
pytestmark = pytest.mark.usefixtures("processes")

# A child that leads a session of its own, starts a worker and waits for it. IGNORING says who
# ignores a request to end, "both" or "worker"; with LEAVING the leader exits once the worker
# runs. The worker reports only once it ignores what it is to ignore.
LEADER = """
import signal, subprocess, sys, time
if os.environ.get("IGNORING") == "both":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
worker = subprocess.Popen([sys.executable, "-B", sys.argv[1]])
while not (pathlib.Path(os.environ["NOTES"]) / "worker.json").is_file():
    time.sleep(0.01)
note("leader")
if os.environ.get("LEAVING"):
    raise SystemExit(0)
worker.wait()
"""
WORKER = """
import signal, time
if os.environ.get("IGNORING"):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
note("worker")
time.sleep(60)
"""
# A child that ends by its own handling of an interrupt, as a render child stops its renderer.
INTERRUPTIBLE = """
import signal, sys, time
signal.signal(signal.SIGINT, lambda *_: sys.exit(7))
note("child")
time.sleep(60)
"""
# A step that runs until it is ended.
STEP = """
import time
note("step")
time.sleep(60)
"""
# A bystander in a session of its own: it keeps each signal it gets, and notes them when it is
# sent SIGUSR1, which ends it.
BYSTANDER = """
import signal, sys, time
got = []
def told(number, frame):
    got.append(number)
    if number == signal.SIGUSR1:
        note("bystander-got", signals=got)
        raise SystemExit(0)
signal.signal(signal.SIGTERM, told)
signal.signal(signal.SIGUSR1, told)
note("bystander")
time.sleep(60)
"""
# A block that takes the requests to end, in a process of its own: it prints what the request
# was, whether the requests stay taken after the block, since the command is then ending, and
# whether the handlers that stood before stand again once the caller goes on (`restore`).
BLOCK = """
import signal, time
import filmkit.child_processes as child_processes
earlier = {number: signal.getsignal(number) for number in child_processes.REQUESTS}
def stand(handlers):
    wanted = {number: handlers.get(number, handlers.get(0)) for number in earlier}
    return all(signal.getsignal(number) is handler for number, handler in wanted.items())
try:
    with child_processes.terminable():
        taken = stand({0: child_processes.receive})
        note("inside")
        time.sleep(30)
except child_processes.Terminated as asked:
    kept = stand({0: child_processes.receive})
    child_processes.restore()
    said = {"number": asked.number, "request": asked.request, "status": asked.status}
    print(json.dumps({**said, "taken": taken, "kept": kept, "restored": stand(earlier)}))
"""
# A block that ends with no request: the handlers that stood before stand again after it.
QUIET = """
import signal
import filmkit.child_processes as child_processes
earlier = {number: signal.getsignal(number) for number in child_processes.REQUESTS}
with child_processes.terminable():
    with child_processes.terminable():
        pass
    inner = all(signal.getsignal(n) is child_processes.receive for n in earlier)
print(json.dumps({"inner": inner, "restored": all(
    signal.getsignal(number) is handler for number, handler in earlier.items()
)}))
"""
# A block that defers a request outside any block that takes them: it leaves the block only
# once the request has arrived, and notes that it did.
DEFERRING = """
import time
import filmkit.child_processes as child_processes
with child_processes.held():
    note("inside")
    while child_processes._REQUESTS.deferred is None:
        time.sleep(0.01)
    note("still-inside")
note("after")
"""
# A child that takes 0.3 s over its own ending when it is asked to end, and exits with 7.
CLOSING = """
import signal, sys, time
def closing(*_):
    time.sleep(0.3)
    sys.exit(7)
signal.signal(signal.SIGTERM, closing)
print(1, flush=True)
time.sleep(60)
"""
# A command that is asked to end while its standard output holds 6,000 bytes it has not written;
# given a descriptor's number, it closes that descriptor of its own first.
UNWRITTEN = """
import os, sys, time
import filmkit.child_processes as child_processes
with child_processes.ending("unwritten: stopped by {request}"):
    with child_processes.terminable():
        sys.stdout.write("y" * 6000)
        if len(sys.argv) > 1:
            os.close(int(sys.argv[1]))
        note("unwritten")
        time.sleep(30)
"""
# A command that runs one step, which takes the requests to end itself while the step runs, and
# prints the request that cut its wait short.
RUN = """
import sys
import filmkit.child_processes as child_processes
try:
    child_processes.run([sys.executable, "-B", sys.argv[1]], cwd=pathlib.Path.cwd())
except child_processes.Terminated as asked:
    print(json.dumps({"number": asked.number}))
"""


def group(processes, **variables):
    """A child that leads a session of its own and the worker it started, both ready: the
    leader, and the worker's process id."""
    worker = processes.script("worker", WORKER)
    leader = processes.script("leader", LEADER)
    started = processes.python(leader, str(worker), session=True, **variables)
    processes.noted("leader")
    return started, processes.noted("worker")["pid"]


def test_a_group_is_stopped_with_everything_its_leader_started(processes):
    leader, worker = group(processes)
    ended = processes.start([sys.executable, "-c", "pass"], start_new_session=True)
    ended.wait()
    child_processes.stop([leader, ended], signal.SIGTERM, groups=True)
    assert leader.returncode == -signal.SIGTERM
    assert not alive(worker)
    assert ended.returncode == 0


def test_what_ignores_the_request_is_killed_after_the_wait(processes, monkeypatch):
    monkeypatch.setattr(child_processes, "STOP_SECONDS", 0.3)
    leader, worker = group(processes, IGNORING="both")
    started = time.monotonic()
    child_processes.stop([leader], signal.SIGTERM, groups=True)
    assert leader.returncode == -signal.SIGKILL
    assert gone([worker], 3)
    assert 0.3 <= time.monotonic() - started < 5


def test_a_straggler_of_a_group_whose_leader_ended_is_killed_too(processes, monkeypatch):
    monkeypatch.setattr(child_processes, "STOP_SECONDS", 0.3)
    # The worker ignores the request and has said so; the leader ends by it.
    leader, straggler = group(processes, IGNORING="worker")
    started = time.monotonic()
    child_processes.stop([leader], signal.SIGTERM, groups=True)
    assert leader.returncode == -signal.SIGTERM
    assert gone([straggler], 3)
    # It took the kill after the wait to end it.
    assert time.monotonic() - started >= 0.3


def test_the_group_of_a_leader_that_has_ended_and_is_not_reaped_is_stopped(processes):
    leader, worker = group(processes, LEAVING="1")
    # The leader's end is waited for without reaping it, so its number is still its own.
    assert child_processes.ended(leader, 10)
    assert leader.returncode is None
    assert alive(worker)
    # What it started still runs in its group, as a renderer's workers do.
    child_processes.stop([leader], signal.SIGTERM, groups=True)
    assert gone([worker], 3)
    assert leader.returncode == 0


def test_a_wait_for_a_childs_end_does_not_reap_it_and_tells_when_it_has_not_ended(processes):
    child = processes.start([sys.executable, "-c", "raise SystemExit(3)"])
    assert child_processes.ended(child) is True
    # Not reaped: the process is still there as one that has ended, and the look is repeatable.
    assert child.returncode is None
    assert child_processes.ended(child, 0) is True
    assert child.wait() == 3
    assert child_processes.ended(child) is True
    running = processes.start([sys.executable, "-c", "import time; time.sleep(60)"])
    assert child_processes.ended(running, 0.2) is False
    assert running.poll() is None


def test_a_reaped_child_is_never_signalled_though_its_number_names_a_running_group(processes):
    bystander = processes.python(processes.script("bystander", BYSTANDER), session=True)
    processes.noted("bystander")
    reaped = processes.start([sys.executable, "-c", "pass"], start_new_session=True)
    assert reaped.wait(timeout=10) == 0
    # The kernel is free to give a reaped child's number to another process: here the number
    # is set to that of a process that leads a group of its own and runs.
    reaped.pid = bystander.pid
    child_processes.stop([reaped], signal.SIGTERM, groups=True, seconds=0.2)
    bystander.send_signal(signal.SIGUSR1)
    assert processes.noted("bystander-got")["signals"] == [signal.SIGUSR1]


def test_without_groups_the_signal_goes_to_the_child_alone(processes):
    child = processes.python(processes.script("interruptible", INTERRUPTIBLE))
    processes.noted("child")
    child_processes.stop([child])
    # The child ended by its own handling of the interrupt.
    assert child.returncode == 7


@pytest.mark.parametrize("number", list(child_processes.REQUESTS))
def test_a_request_to_end_is_an_exception_inside_the_block_and_stays_taken_after_it(
    processes, number
):
    block = processes.python(processes.script("block", BLOCK))
    processes.noted("inside")
    block.send_signal(number)
    printed, _ = block.communicate(timeout=20)
    assert block.returncode == 0
    assert json.loads(printed) == {
        "number": number,
        "request": child_processes.REQUESTS[number],
        "status": 128 + number,
        "taken": True,
        "kept": True,
        "restored": True,
    }


def test_a_block_that_ends_with_no_request_puts_the_earlier_handlers_back(processes):
    quiet = processes.python(processes.script("quiet", QUIET))
    printed, _ = quiet.communicate(timeout=20)
    assert json.loads(printed) == {"inner": True, "restored": True}


class Queue:
    """A kernel queue that answers a registration with the events given."""

    def __init__(self, events):
        self.events = events

    def control(self, changes, room, seconds):
        return self.events

    def close(self):
        pass


@pytest.mark.skipif(not hasattr(child_processes.select, "kqueue"), reason="no kernel queue")
def test_an_event_that_is_an_error_is_the_childs_end_only_when_it_says_no_such_process(
    processes, monkeypatch
):
    select = child_processes.select
    child = processes.start([sys.executable, "-c", "import time; time.sleep(60)"])

    def answering(*events):
        monkeypatch.setattr(select, "kqueue", lambda: Queue(list(events)))

    def error(number):
        return select.kevent(child.pid, flags=select.KQ_EV_ERROR, data=number)

    # A registration for a child that has ended already comes back as "no such process".
    answering(error(child_processes.errno.ESRCH))
    assert child_processes.ended(child, 0) is True
    # Any other error says nothing of the child: it is raised, not read as the child's end.
    answering(error(child_processes.errno.EACCES))
    with pytest.raises(OSError, match="Permission denied") as failed:
        child_processes.ended(child, 0)
    assert failed.value.errno == child_processes.errno.EACCES
    # No event within the wait: the child has not ended. An exit event: it has.
    answering()
    assert child_processes.ended(child, 0) is False
    answering(select.kevent(child.pid, filter=select.KQ_FILTER_PROC, fflags=select.KQ_NOTE_EXIT))
    assert child_processes.ended(child, 0) is True


def test_a_child_whose_end_cannot_be_waited_for_is_killed_and_reaped(processes, monkeypatch):
    ignore = "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN)"
    child = processes.start(
        [sys.executable, "-c", f"{ignore}; print(1, flush=True); time.sleep(60)"],
        stdout=subprocess.PIPE,
        text=True,
    )
    # The child ignores the request to end by now.
    assert processes.line(child) == "1"

    def failing(_child, _seconds=None):
        raise OSError(child_processes.errno.EACCES, "the wait failed")

    monkeypatch.setattr(child_processes, "ended", failing)
    # The failed wait does not leave the stop: the child is killed and reaped, after its grace.
    asked = time.monotonic()
    child_processes.stop([child], signal.SIGTERM, seconds=0.4)
    assert child.returncode == -signal.SIGKILL
    assert 0.4 <= time.monotonic() - asked < 5


def test_a_child_whose_end_cannot_be_waited_for_is_given_its_grace_to_end(processes, monkeypatch):
    child = processes.python(processes.script("closing", CLOSING))
    assert processes.line(child) == "1"

    def failing(_child, _seconds=None):
        raise OSError(child_processes.errno.EACCES, "the wait failed")

    monkeypatch.setattr(child_processes, "ended", failing)
    asked = time.monotonic()
    child_processes.stop([child], signal.SIGTERM, seconds=10)
    # It took 0.3 s over its own ending and was not killed: its exit status is its own.
    assert child.returncode == 7
    assert 0.3 <= time.monotonic() - asked < 5


def test_a_group_whose_leaders_end_cannot_be_waited_for_is_given_its_grace_too(
    processes, monkeypatch
):
    leader = processes.python(processes.script("closing", CLOSING), session=True)
    assert processes.line(leader) == "1"

    def failing(_child, _seconds=None):
        raise OSError(child_processes.errno.EACCES, "the wait failed")

    monkeypatch.setattr(child_processes, "ended", failing)
    asked = time.monotonic()
    child_processes.stop([leader], signal.SIGTERM, groups=True, seconds=3)
    # The leader was looked at by its group's number, not reaped, until it had ended by its own
    # handling; it was not killed. Where a kernel counts an ended leader that is not reaped as
    # a member of its group, the look runs the full time and the status is still its own.
    assert leader.returncode == 7
    assert time.monotonic() - asked >= 0.3


def test_a_stream_that_holds_more_than_its_pipe_has_room_for_does_not_keep_the_command(processes):
    read, write = os.pipe()
    try:
        # The pipe is filled to the brim and then given 600 bytes of room; nobody reads it.
        os.set_blocking(write, False)
        filled = 0
        for size in (65536, 4096, 512, 64, 8, 1):
            try:
                while True:
                    filled += os.write(write, b"x" * size)
            except BlockingIOError:
                pass
        os.set_blocking(write, True)
        assert os.read(read, 600) == b"x" * 600
        command = processes.start(
            [sys.executable, "-B", str(processes.script("unwritten", UNWRITTEN))],
            env={**os.environ, "NOTES": str(processes.notes)},
            stdin=subprocess.DEVNULL,
            stdout=write,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        os.close(write)
    try:
        processes.noted("unwritten")
        command.send_signal(signal.SIGTERM)
        # The command did not wait for a reader of what it held: it ended with its status.
        assert command.wait(timeout=15) == 143
        # The pipe is as its other holders left it: it waits on a write again.
        assert os.get_blocking(read)
        held = b""
        while part := os.read(read, 65536):
            held += part
    finally:
        os.close(read)
    # The pipe took what it had room for, at most, and the rest was dropped.
    assert held[: filled - 600] == b"x" * (filled - 600)
    assert held[filled - 600 :] == b"y" * (len(held) - filled + 600)
    assert len(held) <= filled
    assert command.stderr.read() == "unwritten: stopped by a request to end (SIGTERM)\n"


@pytest.mark.parametrize("closed", [1, 2])
def test_a_command_that_closed_a_standard_descriptor_still_exits_with_its_status(processes, closed):
    command = processes.python(processes.script("unwritten", UNWRITTEN), str(closed))
    processes.noted("unwritten")
    command.send_signal(signal.SIGTERM)
    # The null device took the closed descriptor's number and stayed open under it.
    assert command.wait(timeout=20) == 143


def test_a_request_deferred_outside_a_block_that_takes_them_is_raised_again_after_it(processes):
    deferring = processes.python(processes.script("deferring", DEFERRING))
    processes.noted("inside")
    deferring.send_signal(signal.SIGTERM)
    assert deferring.wait(timeout=20) == -signal.SIGTERM
    # The block ran to its end with the request pending, and nothing after it ran.
    processes.noted("still-inside", 0)
    assert not (processes.notes / "after.json").exists()


def test_a_request_that_arrives_during_a_stop_is_acted_on_once_the_children_have_ended(
    processes, monkeypatch
):
    child = processes.start([sys.executable, "-c", "import time; time.sleep(60)"])
    send, sent = child_processes.send, []

    def asking(child, number, *, group):
        # The request arrives as the child is asked to end, handed over as the interpreter does.
        child_processes.receive(signal.SIGTERM)
        sent.append(number)
        send(child, number, group=group)

    monkeypatch.setattr(child_processes, "send", asking)
    with pytest.raises(Terminated), child_processes.terminable():
        child_processes.stop([child], signal.SIGTERM)
    # The request was raised only after the child had been waited for, and nothing was killed.
    assert sent == [signal.SIGTERM]
    assert child.returncode == -signal.SIGTERM


def test_run_refuses_a_failed_exit(tmp_path):
    child_processes.run([sys.executable, "-c", "pass"], cwd=tmp_path)
    with pytest.raises(subprocess.CalledProcessError) as failed:
        child_processes.run([sys.executable, "-c", "raise SystemExit(3)"], cwd=tmp_path)
    assert failed.value.returncode == 3


def test_run_stops_its_child_when_its_wait_is_cut_short(processes):
    step = processes.script("step", STEP)
    command = processes.python(processes.script("run", RUN), str(step))
    child = processes.noted("step")["pid"]
    command.send_signal(signal.SIGTERM)
    printed, _ = command.communicate(timeout=20)
    # The step had ended before the request went on.
    assert not alive(child)
    assert json.loads(printed) == {"number": signal.SIGTERM}


def test_a_request_that_arrives_while_run_starts_its_child_still_ends_that_child(
    tmp_path, monkeypatch
):
    signals = []

    class Started:
        """A child whose start is when the request to end arrives, handed over as the
        interpreter does; it ends when it is asked to."""

        pid, returncode = 0, None

        def __init__(self, command, cwd):
            child_processes.receive(signal.SIGTERM)

        def send_signal(self, number):
            signals.append(number)
            self.returncode = -number

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(child_processes.subprocess, "Popen", Started)
    with pytest.raises(Terminated), child_processes.terminable():
        child_processes.run(["a-step"], cwd=tmp_path)
    assert signals == [signal.SIGTERM]


def test_a_request_that_arrives_while_a_tool_starts_still_has_that_tool_asked_to_end(
    tmp_path, monkeypatch
):
    signals = []

    class Started:
        """A tool whose start is when the request to end arrives; it ends when it is asked to."""

        pid, returncode = 0, None

        def __init__(self, command, **options):
            child_processes.receive(signal.SIGTERM)

        def send_signal(self, number):
            signals.append(number)
            self.returncode = -number

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(tools.picture_renderer, "require_renderer", lambda: None)
    monkeypatch.setattr(tools.picture_browser, "browser_path", lambda: "no-browser")
    monkeypatch.setattr(tools.shutil, "which", lambda name: "node")
    monkeypatch.setattr(tools, "stage_tools", lambda: tmp_path)
    monkeypatch.setattr(tools, "TOOLS", {"standin": tools.Tool("standin.mjs")})
    monkeypatch.setattr(tools.subprocess, "Popen", Started)
    with pytest.raises(Terminated), child_processes.terminable():
        tools.run("standin", [])
    assert signals == [signal.SIGTERM]
