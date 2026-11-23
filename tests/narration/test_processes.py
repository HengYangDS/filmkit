"""Narration in several processes: the count, the division of segments, the children's commands,
and what a failed child leaves for the refusal."""

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


GB = 1024**3


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A film root on a host of 32 GB, which narrates in two processes, with no count named."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.delenv(processes.VARIABLE, raising=False)
    monkeypatch.setattr(processes, "host_memory", lambda: 32 * GB)
    return tmp_path.resolve()


class Child:
    """A stand-in child that has written its log and exits with the status given; one whose
    status is an exception raises it when the narration looks whether it has ended. As with a
    real child, the look that finds it ended reaps it: its return code is set from then on."""

    def __init__(self, status):
        self.status, self.returncode = status, None

    def poll(self):
        if isinstance(self.status, BaseException):
            raise self.status
        self.returncode = self.status
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


@pytest.mark.parametrize(
    ("memory", "count"),
    [(8, 1), (16, 1), (24, 1), (32, 2), (36, 2), (48, 3), (64, 3), (128, 3), (None, 1), (0, 1)],
)
def test_the_count_comes_from_the_hosts_memory_one_for_every_16_gb_up_to_three(
    monkeypatch, memory, count
):
    monkeypatch.delenv(processes.VARIABLE, raising=False)
    monkeypatch.setattr(processes, "host_memory", lambda: None if memory is None else memory * GB)
    assert processes.count() == count


@pytest.mark.parametrize(("named", "count"), [("", 3), ("1", 1), ("2", 2), ("4", 4)])
def test_a_count_the_variable_names_replaces_the_hosts(monkeypatch, named, count):
    monkeypatch.setattr(processes, "host_memory", lambda: 128 * GB)
    monkeypatch.setenv(processes.VARIABLE, named)
    assert processes.count() == count
    # A host too small for a second process narrates in what the variable names all the same.
    monkeypatch.setattr(processes, "host_memory", lambda: 8 * GB)
    assert processes.count() == (count if named else 1)


def test_the_hosts_memory_is_read_once_and_is_none_where_it_cannot_be_read(monkeypatch):
    processes.host_memory.cache_clear()
    reads = []

    def sysconf(name):
        reads.append(name)
        return {"SC_PHYS_PAGES": 4 * 1024 * 1024, "SC_PAGE_SIZE": 16384}[name]

    monkeypatch.setattr(processes.os, "sysconf", sysconf)
    assert processes.host_memory() == 64 * GB
    assert processes.host_memory() == 64 * GB
    assert reads == ["SC_PHYS_PAGES", "SC_PAGE_SIZE"]
    processes.host_memory.cache_clear()

    def unknown(name):
        message = "unrecognized configuration name"
        raise ValueError(message)

    monkeypatch.setattr(processes.os, "sysconf", unknown)
    assert processes.host_memory() is None
    processes.host_memory.cache_clear()


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
    # The children's logs stay in the work folder after a run that passes.
    assert sorted(path.name for path in (root / work).iterdir()) == [
        "process-1.log",
        "process-2.log",
    ]


def test_the_work_folder_is_named_after_the_receipts_whole_path_from_the_root(root):
    work = root / processes.WORK
    assert processes.work_folder(root / RECEIPT) == (
        work / "build-evidence-editions-zh-ear-first-narration-receipt"
    )
    # Two receipts that differ only high in their paths do not share a folder.
    first = processes.work_folder(root / "build/one/a/b/c/d/e/receipt.json")
    second = processes.work_folder(root / "build/two/a/b/c/d/e/receipt.json")
    assert first == work / "build-one-a-b-c-d-e-receipt" != second
    # A receipt outside the root, which the synthesis refuses, names no folder.
    with pytest.raises(ValueError, match="is not in the subpath"):
        processes.work_folder(root.parent / "receipt.json")


def test_a_failed_child_is_named_with_its_segments_its_log_and_its_last_lines(root, monkeypatch):
    refusal = "RetainedUtteranceError: Unresolved native utterance; inspect before replay"
    # What a library prints as the process ends stands after the exception.
    warning = "resource_tracker: There appear to be 1 leaked semaphore objects to clean up"
    trace = ["Traceback (most recent call last):", '  File "synthesis.py", line 1, in <module>']
    trace += ["    main()", '  File "synthesis.py", line 2, in main', "    raise error"]
    failed = "\n".join(['{"id": "02"}', *trace, "", refusal, "", warning, "", ""])
    started = starting(monkeypatch, statuses=(0, 1), written=['{"id": "01"}\n', failed])
    with pytest.raises(ProcessesError) as refused:
        processes.narrate(SOURCES, [["01"], ["02", "03"]], root / RECEIPT)
    message = str(refused.value)
    assert message.startswith("A narration process failed: segments 02, 03 exited 1 (build/")
    # The last five lines that are not empty, in their order.
    quoted = [trace[2].strip(), trace[3].strip(), trace[4].strip(), refusal, warning]
    assert message.endswith("process-2.log: " + " | ".join(quoted) + ")")
    # Both children were started and waited for, and their logs stay for inspection.
    assert len(started) == 2
    assert all(log.is_file() for _, log in started)


def test_clearing_the_work_of_a_receipt_removes_what_an_earlier_run_left(root, monkeypatch):
    starting(monkeypatch, statuses=(0, 1))
    with pytest.raises(ProcessesError):
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    work = processes.work_folder(root / RECEIPT)
    other = processes.work_folder(root / "build/other/narration-receipt.json")
    other.mkdir(parents=True)
    (other / "process-1.log").write_text("another receipt's run\n")
    assert len(list(work.iterdir())) == 2
    processes.clear_work(root / RECEIPT)
    # The folder is gone with what it held, another receipt's is untouched, and clearing a
    # receipt that has no work is no failure.
    assert not work.exists()
    assert [path.name for path in other.iterdir()] == ["process-1.log"]
    processes.clear_work(root / RECEIPT)


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
    starting(monkeypatch, statuses=(child_processes.Terminated(signal.SIGINT), 0))
    with pytest.raises(child_processes.Terminated) as asked:
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    # The request goes on as it came, with the narration's refusal for the command to print.
    assert (asked.value.number, asked.value.status) == (signal.SIGINT, 130)
    assert asked.value.said.startswith(
        "The narration was stopped by an interrupt; every narration process it had started (2) "
        "was ended with it; their logs are in build/runtime/work/narration-processes/"
    )
    ((children, asking, groups),) = stopped
    assert [type(child) for child in children] == [Child, Child]
    assert (asking, groups) == (signal.SIGTERM, True)


def test_a_child_that_had_ended_and_was_reaped_is_not_handed_on_to_be_stopped(
    root, monkeypatch, stopped
):
    """A reaped child's number is no longer its own: the kernel may have given it to another
    process since, whose group a stop would then end."""
    starting(monkeypatch, statuses=(0, child_processes.Terminated(signal.SIGTERM)))
    with pytest.raises(child_processes.Terminated):
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    ((children, _, _),) = stopped
    assert [child.returncode for child in children] == [None]


def test_a_request_to_end_while_a_child_starts_waits_until_the_child_is_held(
    root, monkeypatch, stopped
):
    started = []

    def start(command, log):
        if started:
            # The request arrives while the second child starts: inside the block that defers it.
            child_processes.receive(signal.SIGTERM)
        started.append(Child(None))
        return started[-1]

    monkeypatch.setattr(processes, "start", start)
    with pytest.raises(child_processes.Terminated) as asked:
        processes.narrate(SOURCES, [["01"], ["02"]], root / RECEIPT)
    assert "a request to end (SIGTERM); every narration process it had started (2)" in (
        asked.value.said
    )
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
    monkeypatch.setattr(narration_narrate.register, "check", lambda: {})
    monkeypatch.setattr(narration_narrate.readings, "check", lambda code: {})
    monkeypatch.setattr(narration_narrate.anchors, "require_editions", dict)
    steps = []
    monkeypatch.setattr(
        narration_narrate.child_processes, "run", lambda command, **options: steps.append(command)
    )
    return steps


def test_a_narration_records_the_count_of_processes_it_may_use(narrating, monkeypatch):
    narration_narrate.main(["--language", "zh"])
    record = repository.read("build/evidence/editions/zh/durations/narrate.json")
    assert record["settings"] == {"narration_processes": 2}
    monkeypatch.setattr(processes, "host_memory", lambda: 128 * GB)
    narration_narrate.main(["--language", "zh"])
    record = repository.read("build/evidence/editions/zh/durations/narrate.json")
    assert record["settings"] == {"narration_processes": 3}
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


def test_a_narration_asked_to_end_says_so_and_is_recorded_as_not_completed(
    narrating, monkeypatch, capsys
):
    def asked(command, **options):
        raise child_processes.Terminated(signal.SIGTERM)

    monkeypatch.setattr(narration_narrate.child_processes, "run", asked)
    with pytest.raises(SystemExit) as left:
        narration_narrate.main(["--language", "zh"])
    # One line, and the status a shell gives a command that SIGTERM ended.
    assert left.value.code == 143
    assert capsys.readouterr().err == (
        "The narration was stopped by a request to end (SIGTERM); its running step was ended "
        "with it\n"
    )
    record = repository.read("build/evidence/editions/zh/durations/narrate.json")
    assert record["completed"] is False
