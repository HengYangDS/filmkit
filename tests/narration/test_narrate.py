"""Narrating, aligning and transcribing one edition through the production commands."""

import json
import sys

import pytest

import filmkit.narration.narrate as narration_narrate
import filmkit.repository as repository
from filmkit.graph import records

BASE = "build/evidence/editions/zh/ear-first"
RECEIPT = f"{BASE}/narration-receipt-06-07.json"
PYTHON = [sys.executable, "-B"]
NARRATION = [
    *PYTHON,
    "-m",
    "filmkit.narration.synthesis",
    "--language",
    "zh",
    "--script",
    "content/zh/film-script.json",
    "--cast",
    "content/zh/voice-reference.json",
    "--folder",
    f"{BASE}/recordings",
    "--receipt",
    RECEIPT,
    "--ids",
    "06,07",
]
ALIGNMENT = [
    *PYTHON,
    "-m",
    "filmkit.narration.alignment",
    "--model",
    "build/runtime/tool-cache/narration-aligner",
    "--receipt",
    RECEIPT,
    "--output",
    f"{BASE}/alignment-06-07.json",
    "--language",
    "Chinese",
]
TRANSCRIPTION = [
    *PYTHON,
    "-m",
    "filmkit.narration.transcription",
    "--receipt",
    RECEIPT,
    "--output",
    f"{BASE}/asr-06-07.json",
    "--language",
    "Chinese",
]


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        (
            narration_narrate.Scope.ALL,
            [("narration", NARRATION), ("alignment", ALIGNMENT), ("transcription", TRANSCRIPTION)],
        ),
        (narration_narrate.Scope.PLAN, [("narration", [*NARRATION, "--dry-run"])]),
        (
            narration_narrate.Scope.CHECKS,
            [("alignment", ALIGNMENT), ("transcription", TRANSCRIPTION)],
        ),
    ],
)
def test_narrate_edition_plans_receipts_named_after_the_selected_segments(scope, expected):
    assert narration_narrate.steps("zh", "06,07", scope) == expected


@pytest.fixture
def commands(monkeypatch, tmp_path) -> list:
    """The commands a run starts, below a root of its own, where the run's duration record goes."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    calls = []
    monkeypatch.setattr(
        narration_narrate.child_processes,
        "run",
        lambda command, **options: calls.append((command, options)),
    )
    return calls


def test_narrate_edition_runs_the_whole_edition_from_the_root(commands, capsys):
    narration_narrate.main(["--language", "en"])
    base = "build/evidence/editions/en/ear-first"
    run = [command for command, _ in commands]
    assert [command[2:4] for command in run] == [
        ["-m", "filmkit.narration.synthesis"],
        ["-m", "filmkit.narration.alignment"],
        ["-m", "filmkit.narration.transcription"],
    ]
    assert run[0][4:9] == ["--language", "en", "--script", "content/en/film-script.json", "--cast"]
    assert run[0][-1] == f"{base}/narration-receipt.json"
    assert run[1][-3:] == [f"{base}/alignment.json", "--language", "English"]
    assert run[2][-3:] == [f"{base}/asr.json", "--language", "English"]
    assert [options for _, options in commands] == [{"cwd": repository.ROOT}] * 3
    # The film's sources are no question of the narration's (`filmkit check`): it prints its
    # steps alone.
    printed = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [line["step"] for line in printed] == ["narration", "alignment", "transcription"]


@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        ("--dry-run", [("filmkit.narration.synthesis", "--dry-run")]),
        (
            "--skip-generation",
            [
                ("filmkit.narration.alignment", "Chinese"),
                ("filmkit.narration.transcription", "Chinese"),
            ],
        ),
    ],
)
def test_a_mode_flag_runs_only_its_steps(commands, flag, expected):
    narration_narrate.main(["--language", "zh", flag])
    assert [(command[3], command[-1]) for command, _ in commands] == expected


def test_a_retake_is_recorded_as_a_partial_run_with_each_step_as_a_phase(commands):
    narration_narrate.main(["--language", "zh", "--ids", "06,07"])
    record = records.read(records.place("narrate", "zh", partial=True))
    assert record.outcome == "pass"
    assert [*record.phases] == ["narration", "alignment", "transcription"]
    assert not records.place("narrate", "zh").exists()
    assert len(commands) == 3


def test_a_check_only_run_is_recorded_as_a_partial_run_and_leaves_the_narrations_record(
    commands,
):
    narration_narrate.main(["--language", "zh"])
    narrated = records.place("narrate", "zh").read_bytes()
    # The checks alone, as a film runs them after narrating chosen segments by hand.
    narration_narrate.main(["--language", "zh", "--skip-generation"])
    assert records.place("narrate", "zh").read_bytes() == narrated
    record = records.read(records.place("narrate", "zh", partial=True))
    assert (record.outcome, [*record.phases]) == ("pass", ["alignment", "transcription"])
    assert sorted(path.name for path in records.place("narrate", "zh").parent.iterdir()) == [
        "narrate.json",
        "narrate.partial.json",
    ]


def test_a_narration_by_hand_is_refused_before_any_step_while_the_plan_holds_it(
    commands, monkeypatch
):
    line = "narrate:zh is not ready, so it is not narrated: check: stale (filmkit build check)"
    asked = []
    monkeypatch.setattr(
        narration_narrate, "judged", lambda code: asked.append(code) or (line, False)
    )
    with pytest.raises(SystemExit) as refused:
        narration_narrate.main(["--language", "zh", "--ids", "06,07"])
    assert (refused.value.code, commands, asked) == (line, [], ["zh"])
    # The convergence's narration, which `filmkit narrate` asked the plan for, and a dry run,
    # which loads no model, do not ask again.
    narration_narrate.main(["--language", "zh", "--converging"])
    narration_narrate.main(["--language", "zh", "--dry-run"])
    assert (asked, len(commands)) == (["zh"], 4)


def test_a_dry_run_writes_no_record(commands):
    narration_narrate.main(["--language", "zh", "--dry-run"])
    assert not (repository.ROOT / "build/evidence").exists()
    assert len(commands) == 1
