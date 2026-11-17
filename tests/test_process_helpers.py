"""What the tests of real processes rest on: a deadline that fails a wait that hangs, and an end
that kills what a test left running."""

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
