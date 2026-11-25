"""The picture gate's audits run at the same time and refuse as they do in sequence."""

import threading

import pytest

import filmkit.picture.gates as gates
import filmkit.repository as repository
from filmkit.graph import runs
from filmkit.picture.rendering import PictureError


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return tmp_path.resolve()


def test_the_audits_run_at_the_same_time_and_each_is_a_phase_of_the_run(root, monkeypatch):
    barrier = threading.Barrier(3, timeout=20)

    def run(tool, arguments, *, environment=None, stdout=None):
        # Each audit waits here until all three have started: in sequence this would time out.
        barrier.wait()
        return 0

    monkeypatch.setattr(gates.tools, "run", run)
    audits = [(tool, [], root / f"{tool}.json", None) for tool in ("frame", "motion", "detail")]
    with runs.run("zh", "check-picture", record=False) as measured:
        gates.run_audits(audits)
    assert sorted(measured.phases) == ["detail", "frame", "motion"]


def test_the_first_failed_audit_in_the_order_given_refuses_once_all_have_ended(root, monkeypatch):
    ended = []

    def run(tool, arguments, *, environment=None, stdout=None):
        ended.append(tool)
        return {"frame": 0, "motion": 3, "detail": 4}[tool]

    monkeypatch.setattr(gates.tools, "run", run)
    audits = [(tool, [], root / f"{tool}.json", None) for tool in ("frame", "motion", "detail")]
    with pytest.raises(PictureError, match="The motion exited with status 3; its report is"):
        gates.run_audits(audits)
    assert sorted(ended) == ["detail", "frame", "motion"]
