"""Duration records: one for each command and edition, written when the run ends, and printed."""

import json
import sys
import threading

import pytest

import filmkit.durations as durations
import filmkit.produce as produce
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError


@pytest.fixture
def root(tmp_path, monkeypatch):
    """An empty film root."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return tmp_path.resolve()


def record_of(root, code, command):
    return json.loads(
        (root / f"build/evidence/editions/{code}/durations/{command}.json").read_text()
    )


def test_a_run_writes_its_command_its_seconds_and_each_phase(root):
    with durations.run("zh", "compare-pictures") as run:
        with durations.phase("validation"):
            pass
        with durations.phase("scan"):
            pass
        with durations.phase("scan"):
            pass
        assert durations.current() is run
    record = record_of(root, "zh", "compare-pictures")
    keys = ["command", "edition", "started_at", "seconds", "completed", "phases", "settings"]
    assert [*record] == keys
    assert record["settings"] == {}
    assert (record["command"], record["edition"], record["completed"]) == (
        "compare-pictures",
        "zh",
        True,
    )
    assert [*record["phases"]] == ["validation", "scan"]
    assert record["seconds"] >= record["phases"]["scan"] >= 0
    assert durations.current() is None


def test_a_run_that_raises_is_recorded_as_not_completed_and_raises(root):
    with pytest.raises(PictureError, match="refused"), durations.run("en", "package-film"):
        with durations.phase("uhd"):
            message = "refused"
            raise PictureError(message)
    record = record_of(root, "en", "package-film")
    assert record["completed"] is False
    assert [*record["phases"]] == ["uhd"]


def test_a_phase_outside_a_run_measures_nothing(root):
    with durations.phase("alone"):
        pass
    assert not (root / "build").exists()


def test_another_thread_adds_its_seconds_to_the_run_it_was_given(root):
    with durations.run("zh", "check-picture") as run:
        workers = [
            threading.Thread(target=run.add, args=(name, 1.5)) for name in ("frame", "motion")
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
    assert record_of(root, "zh", "check-picture")["phases"] == {"frame": 1.5, "motion": 1.5}


@pytest.mark.usefixtures("root")
def test_the_command_lists_the_records_in_starting_order_with_the_sum_of_the_completed(capsys):
    for started, command, seconds, completed in (
        ("2026-11-17T02:00:00+00:00", "render-picture", 900.0, True),
        ("2026-11-17T01:00:00+00:00", "check-picture", 139.25, True),
        ("2026-11-17T03:00:00+00:00", "package-film", 12.0, False),
    ):
        repository.write(
            f"build/evidence/editions/zh/durations/{command}.json",
            {
                "command": command,
                "edition": "zh",
                "started_at": started,
                "seconds": seconds,
                "completed": completed,
                "phases": {"frame-audit": 46.1} if command == "check-picture" else {},
            },
        )
    durations.main(["--language", "all"])
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == "zh:"
    assert [line.split()[1] for line in printed[1:4]] == [
        "check-picture",
        "render-picture",
        "package-film",
    ]
    assert printed[1].endswith("139.2 s  (frame-audit 46.1)")
    assert printed[3].endswith("12.0 s  not completed")
    assert printed[4] == "  sum of the completed commands: 1039.2 s"
    assert printed[5] == "en: no duration record"
    durations.main(["--language", "zh", "--json"])
    assert [r["command"] for r in json.loads(capsys.readouterr().out)["zh"]] == [
        "check-picture",
        "render-picture",
        "package-film",
    ]


def test_every_action_writes_its_duration_record(root, monkeypatch):
    monkeypatch.setattr(produce, "check_sound", lambda edition: None)
    monkeypatch.setattr(sys, "argv", ["produce.py", "check-sound", "--language", "en"])
    produce.main()
    assert record_of(root, "en", "check-sound")["completed"] is True


def test_a_refused_action_records_that_it_did_not_complete(root, monkeypatch):
    def refuse(edition, *, captions):
        message = "no receipt"
        raise PictureError(message)

    monkeypatch.setattr(produce, "validate_picture", refuse)
    monkeypatch.setattr(
        sys, "argv", ["produce.py", "validate-picture", "--language", "zh", "--uncaptioned"]
    )
    with pytest.raises(SystemExit, match="validate-picture: no receipt"):
        produce.main()
    assert record_of(root, "zh", "validate-picture-uncaptioned")["completed"] is False
