"""The deadline of a decode: a timer that never keeps the interpreter from exiting and that is
cancelled whatever cuts the wait for the decode short, a request to end among it."""

import signal

import pytest

import filmkit.picture.equivalence as equivalence
import filmkit.picture.faults as faults
from filmkit.child_processes import Terminated


class Timer:
    """A timer that records how it was started and whether it was cancelled."""

    made: list["Timer"] = []

    def __init__(self, seconds, action):
        self.seconds, self.daemon, self.started, self.cancelled = seconds, False, None, False
        Timer.made.append(self)

    def start(self):
        # What the thread would be when it starts.
        self.started = "daemon" if self.daemon else "thread"

    def cancel(self):
        self.cancelled = True


class Output:
    """A decode's output that ends at once."""

    def read(self, length):
        return b""

    def close(self):
        pass


class Decode:
    """A decode whose wait is cut short by a request to end, as one that arrives while the
    decoder is ending."""

    returncode = None

    def __init__(self, command, **options):
        self.stdout = Output()

    def wait(self):
        raise Terminated(signal.SIGTERM)

    def kill(self):
        pass


@pytest.fixture
def decoding(tmp_path, monkeypatch):
    Timer.made = []
    for module in (faults, equivalence):
        monkeypatch.setattr(module.threading, "Timer", Timer)
        monkeypatch.setattr(module.subprocess, "Popen", Decode)
        monkeypatch.setattr(module.repository, "ROOT", tmp_path)
    return tmp_path


def test_a_request_while_a_decode_ends_cancels_its_deadline(decoding):
    with pytest.raises(Terminated):
        faults.decode(["a-decoder"], 6, decoding / "decode.log", 3, lambda frame, plane: None)
    (timer,) = Timer.made
    assert (timer.started, timer.cancelled) == ("daemon", True)


def test_a_request_while_two_decodes_end_cancels_their_deadline(decoding, monkeypatch):
    monkeypatch.setattr(equivalence, "decode_command", lambda path, frames: ["a-decoder"])
    pictures = {"captioned": decoding / "a.mp4", "uncaptioned": decoding / "b.mp4"}
    with pytest.raises(Terminated):
        equivalence.compare_decoded(pictures, (2, 2), [0, 1], (0, 2), decoding)
    (timer,) = Timer.made
    assert (timer.started, timer.cancelled) == ("daemon", True)
