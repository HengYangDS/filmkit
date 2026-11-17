"""A narration's children as real processes: a parent process that divides its shares among
stand-in children, which load no model and use no GPU.

The parent is the engine's own `filmkit.narration.processes.narrate` in a process of its own,
with a request to end handled as the synthesis handles it; only the child's command is replaced,
by a script that notes its process id under its share's name, starts a process of its own,
writes what it is told to and exits as it is told to. A test waits for a child's note or for
the parent's exit, and every process is ended with its test (`processes`).
"""

import json
import signal

import pytest
from real_processes import alive, gone

# Every test here has the deadline of a test that starts real processes, and their end.
pytestmark = pytest.mark.usefixtures("processes")

# The stand-in child: `--ids` names its share, and CHILDREN says what each share does.
CHILD = """
import subprocess, sys, time
arguments = sys.argv[1:]
ids = arguments[arguments.index("--ids") + 1]
does = json.loads(os.environ["CHILDREN"]).get(ids, {})
own = subprocess.Popen(["/bin/sleep", "60"])
note(ids, own=own.pid)
for line in does.get("lines", []):
    print(line, flush=True)
time.sleep(does.get("seconds", 0))
own.kill()
raise SystemExit(does.get("exit", 0))
"""
# The parent: the engine's narration in processes, with the stand-in as each child's command.
PARENT = """
import signal, sys
if os.environ.get("IGNORING_HANG_UPS"):
    # As under nohup: the process ignores a hang-up before the engine is loaded.
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
import filmkit.child_processes as child_processes
import filmkit.narration.processes as processes
child, shares = sys.argv[1], json.loads(sys.argv[2])
processes.child_command = lambda sources, ids, receipt: [
    sys.executable, "-B", child, "--receipt", str(receipt), "--ids", ",".join(ids)
]
receipt = processes.repository.ROOT / "build/evidence/narration-receipt.json"
# A request to end is handled as the synthesis handles it.
with child_processes.ending("The narration was stopped by {request}"):
    try:
        ended = processes.narrate(("script", "cast", "folder"), shares, receipt)
    except processes.ProcessesError as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(ended))
"""
WORK = "build/runtime/work/narration-processes/build-evidence-narration-receipt"
SLOW = {"seconds": 60}


class Narration:
    """A film root and a parent process that narrates shares in stand-in children."""

    def __init__(self, processes):
        self.processes, self.root = processes, processes.folder
        (self.root / "content").mkdir()
        (self.root / "content/film.toml").write_text("")
        self.child = processes.script("child", CHILD)
        self.parent = processes.script("parent", PARENT)

    def start(self, shares, children, **variables):
        """Start the parent on the shares; `children` says what each share's child does."""
        does = {"FILMKIT_ROOT": str(self.root), "CHILDREN": json.dumps(children), **variables}
        return self.processes.python(self.parent, str(self.child), json.dumps(shares), **does)

    def child_of(self, *ids) -> dict:
        """The process id of the child that narrates this share, and that of the process it
        started, once the child has noted them."""
        return self.processes.noted(",".join(ids))

    def everyone(self, *shares) -> list[int]:
        """Every process of the shares' children, each child and what it started."""
        children = [self.child_of(*ids) for ids in shares]
        return [pid for child in children for pid in (child["pid"], child["own"])]


@pytest.fixture
def narration(processes):
    return Narration(processes)


def test_each_child_of_a_passing_division_is_stamped_with_its_own_seconds(narration):
    children = {"01,04": {"seconds": 2.0, "lines": ['{"id": "01"}', '{"id": "04"}']}}
    parent = narration.start([["01", "04"], ["02", "03"]], children)
    printed, refusal = parent.communicate(timeout=40)
    assert (parent.returncode, refusal) == (0, "")
    first, second = json.loads(printed)
    assert (first["ids"], first["exit"]) == (["01", "04"], 0)
    assert (second["ids"], second["exit"]) == (["02", "03"], 0)
    # The second child ended at once and is not given the first child's two seconds.
    assert first["seconds"] >= 2.0
    assert second["seconds"] < first["seconds"] - 0.5


def test_a_failing_child_is_named_once_the_other_has_run_to_its_end(narration):
    failing = {"exit": 3, "lines": ["Traceback (most recent call last):", "RuntimeError: no take"]}
    children = {"01,04": failing, "02,03": {"seconds": 1.0, "lines": ['{"id": "02"}']}}
    parent = narration.start([["01", "04"], ["02", "03"]], children)
    printed, refusal = parent.communicate(timeout=40)
    assert (parent.returncode, printed) == (1, "")
    assert refusal.strip() == (
        f"A narration process failed: segments 01, 04 exited 3 ({WORK}/process-1.log: "
        "Traceback (most recent call last): | RuntimeError: no take)"
    )
    # The other child was not stopped: it wrote its line and ended by itself, and both logs stay.
    assert (narration.root / WORK / "process-2.log").read_text() == '{"id": "02"}\n'
    assert (narration.root / WORK / "process-1.log").read_text().endswith("no take\n")
    assert gone(narration.everyone(["01", "04"], ["02", "03"]), 5)


def test_a_child_that_is_killed_is_named_by_its_signal(narration):
    parent = narration.start([["01"], ["02"]], {"02": SLOW})
    # The slow child is the one that narrates 02, whichever of the two is still running.
    slow = narration.child_of("02")
    narration.processes.kill(slow["pid"])
    _, refusal = parent.communicate(timeout=40)
    assert parent.returncode == 1
    assert f"A narration process failed: segments 02 exited -9 ({WORK}/process-2.log" in refusal
    assert "segments 01" not in refusal


@pytest.mark.parametrize(
    ("number", "request_"),
    [(signal.SIGTERM, "a request to end (SIGTERM)"), (signal.SIGHUP, "a hang-up (SIGHUP)")],
)
def test_a_narration_asked_to_end_ends_every_child_and_what_each_started(
    narration, number, request_
):
    """The parent alone is asked to end, as a kit ends a run by its process id, or is hung up
    on, as by a terminal that closes. The children lead sessions of their own, so the signal
    does not reach them: the narration ends them."""
    shares = [["01", "04"], ["02", "03"]]
    parent = narration.start(shares, {"01,04": SLOW, "02,03": SLOW})
    everyone = narration.everyone(*shares)
    assert all(alive(pid) for pid in everyone)
    parent.send_signal(number)
    _, refusal = parent.communicate(timeout=40)
    assert parent.returncode == 128 + number
    assert refusal.strip() == (
        f"The narration was stopped by {request_}; every narration process it had started (2) "
        f"was ended with it; their logs are in {WORK}"
    )
    assert not any(alive(pid) for pid in everyone)


def test_a_narration_that_ignores_hang_ups_as_under_nohup_narrates_on(narration):
    shares = [["01", "04"], ["02", "03"]]
    children = {"01,04": SLOW, "02,03": SLOW}
    parent = narration.start(shares, children, IGNORING_HANG_UPS="1")
    everyone = narration.everyone(*shares)
    parent.send_signal(signal.SIGHUP)
    parent.send_signal(signal.SIGTERM)
    _, refusal = parent.communicate(timeout=40)
    # Had the hang-up been taken, it would be the request the narration names: of two requests
    # that wait, the lower number is handed over first. It stayed ignored.
    assert parent.returncode == 143
    assert "stopped by a request to end (SIGTERM)" in refusal
    assert not any(alive(pid) for pid in everyone)
