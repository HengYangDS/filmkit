"""Stopping the children a command started: the signal to each child or to its whole process
group, the wait, the kill of what does not end, and a termination turned into an exception."""

import os
import signal
import subprocess
import sys
import time

import pytest

import filmkit.child_processes as child_processes
from filmkit.child_processes import Terminated


def alive(pid: int) -> bool:
    """Whether a process still runs; one that ended and awaits its parent's wait does not."""
    listed = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    return bool(listed.stdout.strip()) and not listed.stdout.strip().startswith("Z")


def wait_for(condition, seconds=10.0) -> bool:
    ends = time.monotonic() + seconds
    while time.monotonic() < ends:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


def leader_with_a_grandchild(tmp_path, *, ignoring=False):
    """A child that leads a session of its own and has started a process of its own, whose
    process id it has written; with `ignoring`, both ignore the request to end."""
    noted = tmp_path / "grandchild.pid"
    trap = "trap '' TERM; " if ignoring else ""
    script = f"{trap}/bin/sleep 60 & echo $! > {noted}; wait"
    leader = subprocess.Popen(["/bin/sh", "-c", script], start_new_session=True)
    assert wait_for(lambda: noted.is_file() and noted.read_text().strip())
    return leader, int(noted.read_text())


def test_a_group_is_stopped_with_everything_its_leader_started(tmp_path):
    leader, grandchild = leader_with_a_grandchild(tmp_path)
    ended = subprocess.Popen([sys.executable, "-c", "pass"], start_new_session=True)
    ended.wait()
    child_processes.stop([leader, ended], signal.SIGTERM, groups=True)
    assert leader.returncode == -signal.SIGTERM
    assert wait_for(lambda: not alive(grandchild))
    assert ended.returncode == 0


def test_what_ignores_the_request_is_killed_after_the_wait(tmp_path, monkeypatch):
    monkeypatch.setattr(child_processes, "STOP_SECONDS", 0.3)
    leader, grandchild = leader_with_a_grandchild(tmp_path, ignoring=True)
    started = time.monotonic()
    child_processes.stop([leader], signal.SIGTERM, groups=True)
    assert leader.returncode == -signal.SIGKILL
    assert wait_for(lambda: not alive(grandchild))
    assert time.monotonic() - started < 5


def test_a_straggler_of_a_group_whose_leader_ended_is_killed_too(tmp_path, monkeypatch):
    monkeypatch.setattr(child_processes, "STOP_SECONDS", 0.3)
    noted = tmp_path / "straggler.pid"
    script = f"(trap '' TERM; exec /bin/sleep 60) & echo $! > {noted}; wait"
    leader = subprocess.Popen(["/bin/sh", "-c", script], start_new_session=True)
    assert wait_for(lambda: noted.is_file() and noted.read_text().strip())
    straggler = int(noted.read_text())
    # Give the straggler the moment it needs to ignore the request before it is sent.
    time.sleep(0.2)
    child_processes.stop([leader], signal.SIGTERM, groups=True)
    assert leader.returncode == -signal.SIGTERM
    assert wait_for(lambda: not alive(straggler), 3)


def test_the_group_of_a_leader_that_has_ended_and_is_not_reaped_is_stopped(tmp_path):
    noted = tmp_path / "worker.pid"
    script = f"/bin/sleep 60 & echo $! > {noted}"
    leader = subprocess.Popen(["/bin/sh", "-c", script], start_new_session=True)
    # The leader's end is waited for without reaping it, so its number is still its own.
    assert child_processes.ended(leader, 10)
    assert leader.returncode is None
    worker = int(noted.read_text())
    assert alive(worker)
    # What it started still runs in its group, as a renderer's workers do.
    child_processes.stop([leader], signal.SIGTERM, groups=True)
    assert wait_for(lambda: not alive(worker), 3)
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


# A bystander in a session of its own: it notes each signal it gets, and what it got when it
# is sent SIGUSR1, which ends it.
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


def test_a_reaped_child_is_never_signalled_though_its_number_names_a_running_group(processes):
    bystander = processes.python(processes.script("bystander", BYSTANDER), session=True)
    processes.noted("bystander")
    reaped = processes.start([sys.executable, "-c", "pass"], start_new_session=True)
    assert reaped.wait(timeout=10) == 0
    # The kernel is free to give a reaped child's number to another process: here the number
    # is set to that of a process that leads a group of its own and runs.
    reaped.pid = bystander.pid
    child_processes.stop([reaped], signal.SIGTERM, groups=True, seconds=0.2)
    os.kill(bystander.pid, signal.SIGUSR1)
    assert processes.noted("bystander-got")["signals"] == [signal.SIGUSR1]


def test_without_groups_the_signal_goes_to_the_child_alone():
    code = "import signal, sys, time\n"
    code += "signal.signal(signal.SIGINT, lambda *_: sys.exit(7))\n"
    code += "print('ready', flush=True)\ntime.sleep(60)\n"
    child = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE)
    assert child.stdout.readline() == b"ready\n"
    child_processes.stop([child])
    # The child ended by its own handling of the interrupt, as a render child stops its renderer.
    assert child.returncode == 7
    child.stdout.close()


def test_a_termination_is_an_exception_inside_the_block_and_the_handler_is_restored():
    earlier = signal.getsignal(signal.SIGTERM)
    with pytest.raises(Terminated), child_processes.terminable():
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(5)
    assert signal.getsignal(signal.SIGTERM) is earlier


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


def test_run_refuses_a_failed_exit_and_stops_its_child_when_the_wait_is_cut_short(tmp_path):
    child_processes.run([sys.executable, "-c", "pass"], cwd=tmp_path)
    with pytest.raises(subprocess.CalledProcessError) as failed:
        child_processes.run([sys.executable, "-c", "raise SystemExit(3)"], cwd=tmp_path)
    assert failed.value.returncode == 3
    # The child tells this process to end once it runs; the wait is cut short and the child is
    # stopped before the termination goes on.
    noted = tmp_path / "child.pid"
    code = "import os, signal, sys, time\n"
    code += f"open({str(noted)!r}, 'w').write(str(os.getpid()))\n"
    code += "os.kill(os.getppid(), signal.SIGTERM)\ntime.sleep(60)\n"
    with pytest.raises(Terminated), child_processes.terminable():
        child_processes.run([sys.executable, "-c", code], cwd=tmp_path)
    assert not alive(int(noted.read_text()))


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
