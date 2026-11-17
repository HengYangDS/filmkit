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


def test_a_stop_is_not_cut_short_by_a_second_request():
    """A request that arrives while the children are being stopped waits until they have ended."""
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    sent = []

    class Asking:
        """The child, which asks this process to end as soon as it is itself asked to."""

        pid = child.pid

        def poll(self):
            return child.poll()

        def send_signal(self, number):
            os.kill(os.getpid(), signal.SIGTERM)
            sent.append(number)
            child.send_signal(number)

        def wait(self, timeout=None):
            return child.wait(timeout=timeout)

    with pytest.raises(Terminated), child_processes.terminable():
        child_processes.stop([Asking()], signal.SIGTERM)
        time.sleep(5)
    # The second request was raised only after the child had been waited for.
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
        """A child whose start is when the request to end arrives."""

        pid = 0

        def __init__(self, command, cwd):
            os.kill(os.getpid(), signal.SIGTERM)

        def poll(self):
            return -signal.SIGTERM if signals else None

        def send_signal(self, number):
            signals.append(number)

        def wait(self, timeout=None):
            return -signal.SIGTERM

    monkeypatch.setattr(child_processes.subprocess, "Popen", Started)
    with pytest.raises(Terminated), child_processes.terminable():
        child_processes.run(["a-step"], cwd=tmp_path)
    assert signals == [signal.SIGTERM]
