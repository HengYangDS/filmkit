"""A narration's children as real processes: a parent process that divides its shares among
stand-in children, which load no model and use no GPU.

The parent is the engine's own `filmkit.narration.processes.narrate` in a process of its own;
only the child's command is replaced, by a script that notes its process id, starts a process of
its own, writes what it is told to and exits as it is told to.
"""

import json
import os
import signal
import subprocess
import sys
import textwrap
import time

import pytest

# The stand-in child: `--ids` names its share, and CHILDREN says what each share does.
CHILD = """
    import json, os, pathlib, subprocess, sys, time
    arguments = sys.argv[1:]
    ids = arguments[arguments.index("--ids") + 1]
    notes = pathlib.Path(os.environ["NOTES"])
    does = json.loads(os.environ["CHILDREN"]).get(ids, {})
    own = subprocess.Popen(["/bin/sleep", "60"])
    (notes / f"{ids}.json").write_text(json.dumps({"pid": os.getpid(), "own": own.pid}))
    for line in does.get("lines", []):
        print(line, flush=True)
    time.sleep(does.get("seconds", 0))
    own.kill()
    raise SystemExit(does.get("exit", 0))
"""
# The parent: the engine's narration in processes, with the stand-in as each child's command.
PARENT = """
    import json, sys
    import filmkit.narration.processes as processes
    child, shares = sys.argv[1], json.loads(sys.argv[2])
    processes.child_command = lambda sources, ids, receipt: [
        sys.executable, child, "--receipt", str(receipt), "--ids", ",".join(ids)
    ]
    receipt = processes.repository.ROOT / "build/evidence/narration-receipt.json"
    try:
        ended = processes.narrate(("script", "cast", "folder"), shares, receipt)
    except processes.ProcessesError as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(ended))
"""


def alive(pid: int) -> bool:
    """Whether a process still runs; one that ended and awaits its parent's wait does not."""
    listed = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    return bool(listed.stdout.strip()) and not listed.stdout.strip().startswith("Z")


def wait_for(condition, seconds=20.0) -> bool:
    ends = time.monotonic() + seconds
    while time.monotonic() < ends:
        if condition():
            return True
        time.sleep(0.05)
    return condition()


class Narration:
    """A film root and a parent process that narrates shares in stand-in children."""

    def __init__(self, root):
        self.root = root
        (root / "content").mkdir()
        (root / "content/film.toml").write_text("")
        self.notes = root / "notes"
        self.notes.mkdir()
        self.child, self.parent = root / "child.py", root / "parent.py"
        self.child.write_text(textwrap.dedent(CHILD))
        self.parent.write_text(textwrap.dedent(PARENT))
        self.work = root / "build/runtime/work/narration-processes"

    def start(self, shares, children) -> subprocess.Popen:
        environment = {**os.environ, "FILMKIT_ROOT": str(self.root), "NOTES": str(self.notes)}
        environment["CHILDREN"] = json.dumps(children)
        command = [sys.executable, "-B", str(self.parent), str(self.child), json.dumps(shares)]
        return subprocess.Popen(
            command,
            cwd=self.root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def noted(self, count) -> list[dict]:
        """Each child's process id and that of the process it started, once all have noted."""
        assert wait_for(lambda: len(list(self.notes.glob("*.json"))) == count)
        time.sleep(0.2)
        return [json.loads(path.read_text()) for path in sorted(self.notes.glob("*.json"))]


@pytest.fixture
def narration(tmp_path):
    return Narration(tmp_path.resolve())


def test_each_child_of_a_passing_division_is_stamped_with_its_own_seconds(narration):
    children = {"01,04": {"seconds": 2.0, "lines": ['{"id": "01"}', '{"id": "04"}']}}
    parent = narration.start([["01", "04"], ["02", "03"]], children)
    printed, refusal = parent.communicate(timeout=60)
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
    printed, refusal = parent.communicate(timeout=60)
    assert (parent.returncode, printed) == (1, "")
    work = "build/runtime/work/narration-processes/build-evidence-narration-receipt"
    assert refusal.strip() == (
        f"A narration process failed: segments 01, 04 exited 3 ({work}/process-1.log: "
        "RuntimeError: no take)"
    )
    # The other child was not stopped: it wrote its line and ended by itself, and both logs stay.
    assert (narration.root / work / "process-2.log").read_text() == '{"id": "02"}\n'
    assert (narration.root / work / "process-1.log").read_text().endswith("no take\n")
    assert not any(alive(child["pid"]) for child in narration.noted(2))


def test_a_child_that_is_killed_is_named_by_its_signal(narration):
    parent = narration.start([["01"], ["02"]], {"02": {"seconds": 60}})
    children = narration.noted(2)
    slow = next(child for child in children if alive(child["pid"]))
    os.kill(slow["pid"], signal.SIGKILL)
    _, refusal = parent.communicate(timeout=60)
    assert parent.returncode == 1
    assert "A narration process failed: segments 02 exited -9 (" in refusal
    # What the killed child had started is none of the narration's to end; it ends by itself.
    os.kill(slow["own"], signal.SIGKILL)


def test_a_narration_asked_to_end_ends_every_child_and_what_each_started(narration):
    slow = {"seconds": 60}
    parent = narration.start([["01", "04"], ["02", "03"]], {"01,04": slow, "02,03": slow})
    children = narration.noted(2)
    everyone = [pid for child in children for pid in (child["pid"], child["own"])]
    assert all(alive(pid) for pid in everyone)
    # The parent alone is asked to end, as a kit ends a run by its process id.
    parent.send_signal(signal.SIGTERM)
    _, refusal = parent.communicate(timeout=30)
    assert parent.returncode == 1
    assert refusal.strip().startswith(
        "The narration was stopped by a request to end (SIGTERM); every narration process it "
        "had started (2) was ended with it; their logs are in build/runtime/work/"
    )
    assert wait_for(lambda: not any(alive(pid) for pid in everyone), 10)
