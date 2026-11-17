"""Narration in several processes: the count, the division of segments, the children's commands,
and what a failed child leaves for the refusal."""

import os
import signal
import sys

import pytest

import filmkit.child_processes as child_processes
import filmkit.narration.narrate as narration_narrate
import filmkit.narration.processes as processes
import filmkit.repository as repository
from filmkit.narration.processes import ProcessesError

SOURCES = ("content/film-script.json", "content/voice-reference.json", "build/recordings")
RECEIPT = "build/evidence/editions/zh/ear-first/narration-receipt.json"


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.delenv(processes.VARIABLE, raising=False)
    return tmp_path.resolve()


class Child:
    """A stand-in child that has written its log and exits with the status given; one whose
    status is an exception raises it when it is waited for."""

    def __init__(self, status):
        self.status = status

    def wait(self):
        if isinstance(self.status, BaseException):
            raise self.status
        return self.status


def starting(monkeypatch, statuses=(), written="{}"):
    """Have each start record its command and log, write the log and exit with its status."""
    started = []

    def start(command, log):
        log.write_text(written if isinstance(written, str) else written[len(started)])
        started.append((command, log))
        return Child(statuses[len(started) - 1] if len(started) <= len(statuses) else 0)

    monkeypatch.setattr(processes, "start", start)
    return started


@pytest.mark.parametrize(("named", "count"), [(None, 2), ("", 2), ("1", 1), ("4", 4)])
def test_the_count_is_two_unless_the_variable_names_another(monkeypatch, named, count):
    if named is None:
        monkeypatch.delenv(processes.VARIABLE, raising=False)
    else:
        monkeypatch.setenv(processes.VARIABLE, named)
    assert processes.count() == count


@pytest.mark.parametrize("named", ["two", "0", "-1", "1.5", "２"])
def test_a_value_that_is_no_count_is_refused_by_the_variable(monkeypatch, named):
    monkeypatch.setenv(processes.VARIABLE, named)
    with pytest.raises(ProcessesError, match="FILMKIT_NARRATION_PROCESSES names"):
        processes.count()


def test_the_longest_segment_goes_first_and_each_to_the_least_loaded_share():
    segments = [("01", 34), ("02", 35), ("03", 67), ("04", 73)]
    # 04 and 03 open the two shares; 02 joins 03, the lighter, and 01 then joins 04.
    assert processes.divide(segments, 2) == [["01", "04"], ["02", "03"]]
    assert processes.divide(segments, 1) == [["01", "02", "03", "04"]]
    assert processes.divide(segments, 4) == [["04"], ["03"], ["02"], ["01"]]
    # More processes than segments leave no share empty, and equal lengths keep their order.
    assert processes.divide(segments[:2], 4) == [["02"], ["01"]]
    assert processes.divide([("a", 5), ("b", 5), ("c", 5)], 2) == [["a", "c"], ["b"]]


def test_each_child_is_the_synthesis_itself_on_its_segments_with_a_receipt_of_its_own(
    root, monkeypatch
):
    started = starting(monkeypatch)
    receipt = root / RECEIPT
    ended = processes.narrate(SOURCES, [["01", "04"], ["02", "03"]], receipt)
    work = "build/runtime/work/narration-processes"
    work += "/build-evidence-editions-zh-ear-first-narration-receipt"
    synthesis = [sys.executable, "-B", "-m", "filmkit.narration.synthesis"]
    synthesis += ["--script", SOURCES[0], "--cast", SOURCES[1], "--folder", SOURCES[2]]
    assert [command for command, _ in started] == [
        [*synthesis, "--receipt", f"{work}/process-1.json", "--ids", "01,04"],
        [*synthesis, "--receipt", f"{work}/process-2.json", "--ids", "02,03"],
    ]
    assert [(child["ids"], child["exit"]) for child in ended] == [
        (["01", "04"], 0),
        (["02", "03"], 0),
    ]
    # No child's receipt stands where the edition's does, and a run that passes leaves no work.
    assert not receipt.exists()
    assert not (root / work).exists()


def test_a_failed_child_is_named_with_its_segments_its_log_and_its_last_line(root, monkeypatch):
    refusal = "RetainedUtteranceError: Unresolved native utterance; inspect before replay"
    logs = ['{"id": "01"}\n', f"Traceback (most recent call last):\n  ...\n{refusal}\n\n"]
    started = starting(monkeypatch, statuses=(0, 1), written=logs)
    with pytest.raises(ProcessesError) as refused:
        processes.narrate(SOURCES, [["01"], ["02", "03"]], root / RECEIPT)
    message = str(refused.value)
    assert message.startswith("A narration process failed: segments 02, 03 exited 1 (build/")
    assert message.endswith(f"process-2.log: {refusal})")
    # Both children were started and waited for, and their logs stay for inspection.
    assert len(started) == 2
    assert all(log.is_file() for _, log in started)
    # The next run clears what the last one left before it starts its own children.
    starting(monkeypatch)
    processes.narrate(SOURCES, [["02"], ["03"]], root / RECEIPT)
    assert not started[0][1].parent.exists()


@pytest.fixture
def stopped(monkeypatch):
    """The children the narration ends, with the signal and whether it goes to their groups."""
    calls = []
    monkeypatch.setattr(
        processes.child_processes,
        "stop",
        lambda children, asking, *, groups: calls.append((children, asking, groups)),
    )
    return calls


def test_an_interrupted_wait_ends_every_childs_process_group_and_refuses(
    root, monkeypatch, stopped
):
    starting(monkeypatch, statuses=(KeyboardInterrupt(), 0))
    with pytest.raises(ProcessesError) as refused:
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    assert str(refused.value).startswith(
        "The narration was stopped by an interrupt; every narration process it had started (2) "
        "was ended with it; their logs are in build/runtime/work/narration-processes/"
    )
    ((children, asking, groups),) = stopped
    assert [type(child) for child in children] == [Child, Child]
    assert (asking, groups) == (signal.SIGTERM, True)


def test_a_request_to_end_while_a_child_starts_waits_until_the_child_is_held(
    root, monkeypatch, stopped
):
    started = []

    def start(command, log):
        if started:
            # The request arrives while the second child starts.
            os.kill(os.getpid(), signal.SIGTERM)
        started.append(Child(None))
        return started[-1]

    monkeypatch.setattr(processes, "start", start)
    with pytest.raises(ProcessesError, match=r"request to end \(SIGTERM\); every .* \(2\) was"):
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    # Both children were held when the request was acted on, so both were ended.
    ((children, _, _),) = stopped
    assert children == started and len(started) == 2


def test_a_child_that_cannot_be_started_ends_the_ones_already_started(root, monkeypatch, stopped):
    first = Child(0)

    def start(command, log):
        if "--ids" in command and command[-1] == "02":
            message = "Resource temporarily unavailable"
            raise BlockingIOError(message)
        return first

    monkeypatch.setattr(processes, "start", start)
    with pytest.raises(ProcessesError, match=r"stopped by BlockingIOError: Resource .* \(1\)"):
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    assert stopped == [([first], signal.SIGTERM, True)]


def test_a_child_starts_at_the_films_root_as_a_single_process(root, monkeypatch):
    seen = {}

    def popen(command, *, cwd, env, stdin, stdout, stderr, start_new_session):
        seen.update(command=command, cwd=cwd, env=env, stdin=stdin, stderr=stderr)
        seen["session"] = start_new_session
        return Child(0)

    monkeypatch.setattr(processes.subprocess, "Popen", popen)
    monkeypatch.setenv(processes.VARIABLE, "4")
    log = root / "process-1.log"
    processes.start(["python", "-m", "filmkit.narration.synthesis"], log)
    assert seen["cwd"] == root
    assert seen["env"][processes.VARIABLE] == "1"
    assert seen["env"]["FILMKIT_ROOT"] == str(root)
    devnull, merged = processes.subprocess.DEVNULL, processes.subprocess.STDOUT
    assert (seen["stdin"], seen["stderr"]) == (devnull, merged)
    # The child leads a session of its own, so its whole process group can be ended.
    assert seen["session"] is True
    assert log.is_file()


@pytest.fixture
def narrating(root, monkeypatch):
    """A narration whose gate passes and whose steps are recorded instead of run."""
    monkeypatch.setattr(narration_narrate.concepts, "check", lambda: {})
    monkeypatch.setattr(narration_narrate.readings, "check", lambda code: {})
    steps = []
    monkeypatch.setattr(
        narration_narrate.child_processes, "run", lambda command, **options: steps.append(command)
    )
    return steps


def test_a_narration_records_the_count_of_processes_it_may_use(narrating, monkeypatch):
    narration_narrate.main(["--language", "zh"])
    record = repository.read("build/evidence/editions/zh/durations/narrate.json")
    assert record["settings"] == {"narration_processes": 2}
    monkeypatch.setenv(processes.VARIABLE, "1")
    narration_narrate.main(["--language", "zh"])
    record = repository.read("build/evidence/editions/zh/durations/narrate.json")
    assert record["settings"] == {"narration_processes": 1}
    # The checks alone narrate nothing, so their record names no count.
    narration_narrate.main(["--language", "en", "--skip-generation"])
    checks = repository.read("build/evidence/editions/en/durations/narrate-checks.json")
    assert checks["settings"] == {}


def test_a_value_that_is_no_count_refuses_the_narration_before_any_step(narrating, monkeypatch):
    monkeypatch.setenv(processes.VARIABLE, "many")
    with pytest.raises(SystemExit, match="FILMKIT_NARRATION_PROCESSES names 'many'"):
        narration_narrate.main(["--language", "zh"])
    assert narrating == []
    assert not (repository.ROOT / "build").exists()


def test_a_narration_asked_to_end_refuses_and_is_recorded_as_not_completed(narrating, monkeypatch):
    def asked(command, **options):
        raise child_processes.Terminated(signal.SIGTERM)

    monkeypatch.setattr(narration_narrate.child_processes, "run", asked)
    with pytest.raises(SystemExit, match=r"asked to end \(SIGTERM\); its running step was ended"):
        narration_narrate.main(["--language", "zh"])
    record = repository.read("build/evidence/editions/zh/durations/narrate.json")
    assert record["completed"] is False
