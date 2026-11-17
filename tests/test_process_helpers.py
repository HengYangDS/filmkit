"""What the tests of real processes rest on: a deadline that fails a wait that hangs, and an end
that kills what a test left running."""

import os
import subprocess
import sys
import time

import pytest
import real_processes
from real_processes import alive, gone

SLEEPER = """
import time
note("sleeper")
time.sleep(60)
"""


def test_a_wait_that_hangs_fails_at_the_deadline_and_the_earlier_alarm_stands_again():
    earlier = real_processes.signal.getsignal(real_processes.signal.SIGALRM)
    started = time.monotonic()
    with (
        pytest.raises(TimeoutError, match="did not end within 0.3 s"),
        real_processes.deadline(0.3),
    ):
        subprocess.run([sys.executable, "-c", "import time; time.sleep(60)"], check=False)
    assert time.monotonic() - started < 5
    assert real_processes.signal.getsignal(real_processes.signal.SIGALRM) is earlier
    # A block that ends in time leaves no alarm behind: one that rang would be recorded here,
    # where by its default action it would end the test run.
    rang = []
    signal = real_processes.signal
    before = signal.signal(signal.SIGALRM, lambda *_: rang.append("an alarm"))
    try:
        with real_processes.deadline(0.2):
            pass
        time.sleep(0.4)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, before)
    assert rang == []


def test_the_end_kills_what_was_started_and_what_a_note_named(tmp_path):
    processes = real_processes.Processes(tmp_path)
    try:
        started = processes.python(processes.script("sleeper", SLEEPER), session=True)
        named = processes.noted("sleeper")["pid"]
        other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        (processes.notes / "other.json").write_text(f'{{"pid": {other.pid}}}')
        # Notes set aside for a next run still name what is to be ended.
        processes.forget()
        assert alive(named) and alive(other.pid)
    finally:
        processes.end()
    other.wait()
    assert started.returncode is not None
    assert gone([named, other.pid], 0)


def test_the_end_leaves_a_number_that_is_no_longer_the_named_process(tmp_path):
    processes = real_processes.Processes(tmp_path)
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        (processes.notes / "ended.json").write_text(f'{{"pid": {other.pid}}}')
        # The note was read while its process ran; the number is then another process's, which
        # is what a start at another time says.
        processes.pids()
        processes.named[other.pid] = "Thu Jan  1 00:00:00 1970"
        processes.end()
        assert alive(other.pid)
    finally:
        other.kill()
        other.wait()


def test_a_whole_number_names_a_process_only_in_a_fact_that_names_one(tmp_path):
    processes = real_processes.Processes(tmp_path)
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        # A running process's number under a fact that names none, as a signal's number stands.
        (processes.notes / "asked.json").write_text(f'{{"number": {other.pid}, "signals": [2]}}')
        assert processes.pids() == []
        processes.end()
        assert alive(other.pid)
    finally:
        other.kill()
        other.wait()


def test_the_end_goes_on_past_a_named_process_it_may_not_signal(tmp_path, monkeypatch):
    processes = real_processes.Processes(tmp_path)
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    kill = os.kill

    def refusing(pid, number):
        if pid == other.pid:
            raise PermissionError(1, "Operation not permitted")
        kill(pid, number)

    try:
        started = processes.python(processes.script("sleeper", SLEEPER))
        processes.noted("sleeper")
        (processes.notes / "other.json").write_text(f'{{"pid": {other.pid}}}')
        monkeypatch.setattr(real_processes.os, "kill", refusing)
        # The one it may not signal does not keep the end from the rest of its work.
        processes.end()
        assert started.returncode is not None
    finally:
        monkeypatch.undo()
        other.kill()
        other.wait()


def test_a_process_started_here_dies_of_a_closed_pipe_as_any_process_does(tmp_path):
    processes = real_processes.Processes(tmp_path)
    try:
        shell = processes.start(
            ["/bin/sh", "-c", "kill -PIPE $$; echo went-on"], stdout=subprocess.PIPE, text=True
        )
        printed, _ = shell.communicate(timeout=20)
    finally:
        processes.end()
    assert (shell.returncode, printed) == (-real_processes.signal.SIGPIPE, "")
