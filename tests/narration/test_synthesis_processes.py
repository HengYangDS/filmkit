"""The synthesis narrating in several processes: the division it asks for, the one receipt it
writes from the retained recordings, the single process it keeps, and a child that fails."""

import json

import pytest
import test_synthesis

import filmkit.narration.processes as processes
import filmkit.narration.synthesis as narration_synthesis
import filmkit.repository as repository
from filmkit.narration.processes import ProcessesError

# The synthesis tests' sources and voice double, the fixture under its own name.
ARGUMENTS, GROUPS, write_sources = (
    test_synthesis.ARGUMENTS,
    test_synthesis.GROUPS,
    test_synthesis.write_sources,
)
voice = test_synthesis.voice
LONG = ["这一段说得更长一些，好让它排在前面。", "再补一句。"]
SEGMENTS = {"01": GROUPS, "02": LONG, "03": GROUPS, "04": ["短句。", "又一句。"]}


class Child:
    def __init__(self, status):
        self.status = status

    def wait(self):
        return self.status


def children(monkeypatch, fail=()):
    """Stand in for the children: each runs the synthesis itself, in this process and with the
    voice double, on its own segments as a single narration process; one whose segments are in
    `fail` writes a refusal and exits 1 instead."""
    started = []

    def start(command, log):
        arguments = command[4:]
        ids = arguments[arguments.index("--ids") + 1]
        started.append({"ids": ids, "arguments": arguments})
        if ids in fail:
            log.write_text("RuntimeError: Invalid generated narration\n")
            return Child(1)
        with monkeypatch.context() as single:
            single.setenv(processes.VARIABLE, "1")
            narration_synthesis.main(arguments)
        log.write_text("narrated\n")
        return Child(0)

    monkeypatch.setattr(processes, "start", start)
    return started


def printed(capsys) -> list[dict]:
    return [json.loads(line) for line in capsys.readouterr().out.splitlines()]


@pytest.fixture
def sources(tmp_path, voice, monkeypatch):
    monkeypatch.delenv(processes.VARIABLE, raising=False)
    write_sources(tmp_path, SEGMENTS)
    return voice


def test_segments_to_generate_are_divided_and_the_one_receipt_is_in_segment_order(
    tmp_path, sources, monkeypatch, capsys
):
    started = children(monkeypatch)
    narration_synthesis.main(ARGUMENTS)
    # The longest spoken text opens the first share; the others balance the two, 30 characters
    # of spoken text against 34.
    assert [child["ids"] for child in started] == ["02,04", "01,03"]
    for child in started:
        receipt = child["arguments"][child["arguments"].index("--receipt") + 1]
        assert receipt.startswith("build/runtime/work/narration-processes/receipt/process-")
        assert child["arguments"][:6] == ARGUMENTS[:6]
    records = repository.read("receipt.json")["records"]
    assert [record["id"] for record in records] == ["01", "02", "03", "04"]
    assert all((tmp_path / record["path"]).is_file() for record in records)
    assert not (tmp_path / "build/runtime/work/narration-processes/receipt").exists()
    lines = printed(capsys)
    reports = [line["process"] for line in lines if "process" in line]
    assert [(report["ids"], report["exit"]) for report in reports] == [
        (["02", "04"], 0),
        (["01", "03"], 0),
    ]
    # Once the children have ended, the synthesis finds every segment retained.
    reused = [line["id"] for line in lines if line.get("state") == "reused"]
    assert reused == ["01", "02", "03", "04"]


def test_the_receipt_equals_a_single_process_runs_but_for_what_each_take_measured(
    tmp_path, sources, monkeypatch
):
    children(monkeypatch)
    narration_synthesis.main(ARGUMENTS)
    several = repository.read("receipt.json")["records"]
    plans = {record["id"]: (record["fingerprint"], record["path"]) for record in several}
    for path in (tmp_path / "audio").rglob("*"):
        if path.is_file():
            path.unlink()
    (tmp_path / "receipt.json").unlink()
    monkeypatch.setenv(processes.VARIABLE, "1")
    monkeypatch.setattr(processes, "start", None)
    narration_synthesis.main(ARGUMENTS)
    single = repository.read("receipt.json")["records"]
    assert {record["id"]: (record["fingerprint"], record["path"]) for record in single} == plans
    assert [[*record] for record in single] == [[*record] for record in several]


def test_one_segment_to_generate_stays_in_this_process(tmp_path, sources, monkeypatch):
    started = children(monkeypatch)
    narration_synthesis.main([*ARGUMENTS, "--ids", "02"])
    assert started == []
    assert [record["id"] for record in repository.read("receipt.json")["records"]] == ["02"]
    # With one segment retained and three to generate, only those three are divided.
    narration_synthesis.main(ARGUMENTS)
    assert sorted(",".join(child["ids"] for child in started).split(",")) == ["01", "03", "04"]


def test_a_dry_run_starts_no_process(sources, monkeypatch, capsys):
    started = children(monkeypatch)
    narration_synthesis.main([*ARGUMENTS, "--dry-run"])
    assert started == []
    assert [line["state"] for line in printed(capsys)] == ["generate"] * 4


def test_a_failed_child_refuses_and_leaves_the_edition_receipt_as_it_was(
    tmp_path, sources, monkeypatch, capsys
):
    repository.write("receipt.json", {"records": [{"id": "00", "earlier": True}]})
    before = (tmp_path / "receipt.json").read_bytes()
    started = children(monkeypatch, fail=("02,04",))
    with pytest.raises(ProcessesError, match="segments 02, 04 exited 1 .*Invalid generated"):
        narration_synthesis.main(ARGUMENTS)
    # The other child ran to its end, and no model was loaded here to narrate what failed.
    assert [child["ids"] for child in started] == ["02,04", "01,03"]
    assert (tmp_path / "receipt.json").read_bytes() == before
    work = tmp_path / "build/runtime/work/narration-processes/receipt"
    assert (work / "process-1.log").read_text().startswith("RuntimeError")
    # The next run divides only the failed child's segments and reuses what the other retained.
    capsys.readouterr()
    again = children(monkeypatch)
    narration_synthesis.main(ARGUMENTS)
    assert [child["ids"] for child in again] == ["02", "04"]
    assert not work.exists()
    assert [record["id"] for record in repository.read("receipt.json")["records"]] == [
        "01",
        "02",
        "03",
        "04",
    ]


def test_a_child_that_ends_well_without_its_recording_is_refused(sources, monkeypatch):
    def start(command, log):
        log.write_text("nothing narrated\n")
        return Child(0)

    monkeypatch.setattr(processes, "start", start)
    with pytest.raises(RuntimeError, match="ended without the recordings of 01, 02, 03, 04"):
        narration_synthesis.main(ARGUMENTS)
    assert not (repository.ROOT / "receipt.json").exists()


def test_a_value_that_is_no_count_refuses_before_any_effect(tmp_path, sources, monkeypatch):
    monkeypatch.setenv(processes.VARIABLE, "many")
    started = children(monkeypatch)
    with pytest.raises(ProcessesError, match="FILMKIT_NARRATION_PROCESSES names 'many'"):
        narration_synthesis.main(ARGUMENTS)
    assert started == []
    assert not (tmp_path / "audio").exists()
