"""The seam's measurement of a run (`filmkit.graph.runs`): a completed, a refused and a failed run
of a node, each recorded with its seconds, load, phases and settings in the node's run record, and
no other record of its duration (design decision 10)."""

import contextlib
import os
import threading
from pathlib import Path

import pytest
import stand_ins

from filmkit.graph import opens, records, runs


def loads(monkeypatch, *readings):
    """Have the host state these 1-minute loads, one for each time it is asked; an exception in
    their place is raised."""
    asked = iter(readings)

    def getloadavg():
        reading = next(asked)
        if isinstance(reading, Exception):
            raise reading
        return (reading, 1.0, 2.0)

    monkeypatch.setattr(os, "getloadavg", getloadavg, raising=False)


def read():
    return records.read(records.place("stand", "zh"))


def refuse(run):
    raise SystemExit("stand: the input is not ready")


def fail(run):
    raise RuntimeError("the disk went away")


@pytest.mark.parametrize(
    ("block", "outcome", "line"),
    [
        (lambda run: None, "pass", None),
        (refuse, "refuse", "stand: the input is not ready"),
        (fail, "error", "RuntimeError: the disk went away"),
    ],
)
def test_a_run_is_recorded_with_its_seconds_load_phases_and_settings(
    one_node, monkeypatch, block, outcome, line
):
    loads(monkeypatch, 6.5234, 33.8049)
    with pytest.raises((SystemExit, RuntimeError)) if line else contextlib.nullcontext():
        stand_ins.run_stand(one_node, block)
    record = read()
    assert isinstance(record, records.RunRecord)
    assert (record.outcome, record.refusal) == (outcome, line)
    assert record.inputs["in"].path == "in.txt"
    assert record.outputs["out"].sha256 == records.digest(one_node / "out.txt")
    # The load is the host's, not the verdict's: a refused or failed run states it as well.
    assert record.load_1m == {"start": 6.52, "end": 33.8}
    assert (record.settings, [*record.phases]) == ({"count": 2}, ["work"])
    assert record.seconds >= record.phases["work"] >= 0
    assert len(record.started_at) == len("2026-11-17T01:00:00.000+00:00")
    assert record.host_class == "light"
    assert opens.NODE not in os.environ
    # The run record is the one file the run writes: no record of its duration beside it.
    written = sorted(
        p.relative_to(one_node) for p in (one_node / "build").rglob("*") if p.is_file()
    )
    assert written == [Path("build/evidence/records/editions/zh/stand.json")]


def test_a_phase_named_again_holds_the_sum_and_the_run_is_current_inside_it(one_node):
    with runs.run("zh", "stand") as run:
        for name in ("validation", "scan", "scan"):
            with runs.phase(name):
                pass
        assert runs.current() is run
    assert runs.current() is None
    record = read()
    assert [*record.phases] == ["validation", "scan"]
    assert record.seconds >= record.phases["scan"] >= 0


def test_a_phase_outside_a_run_measures_nothing_and_writes_nothing(one_node):
    with runs.phase("alone"):
        pass
    assert not (one_node / "build").exists()


def test_another_thread_adds_its_seconds_to_the_run_it_was_given(one_node):
    with runs.run("zh", "stand") as run:
        workers = [
            threading.Thread(target=run.add, args=(name, 1.5)) for name in ("frame", "motion")
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
    assert read().phases == {"frame": 1.5, "motion": 1.5}


@pytest.mark.parametrize("host", ["cannot be read", "has none"])
def test_a_host_that_states_no_load_average_is_recorded_all_the_same(one_node, monkeypatch, host):
    if host == "cannot be read":
        loads(monkeypatch, OSError("unobtainable"), OSError("unobtainable"))
    else:
        monkeypatch.delattr(os, "getloadavg", raising=False)
    with runs.run("zh", "stand"), runs.phase("gates"):
        pass
    record = read()
    assert record.load_1m == {"start": None, "end": None}
    assert (record.outcome, [*record.phases]) == ("pass", ["gates"])


def test_a_command_that_names_no_node_is_measured_and_writes_nothing(one_node):
    with runs.run("zh", "verify") as run, runs.phase("media"):
        pass
    assert [*run.phases] == ["media"]
    assert not (one_node / "build").exists()
