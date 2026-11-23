"""Narrating, aligning and transcribing one edition through the production commands."""

import json
import sys

import pytest

import filmkit.narration.narrate as narration_narrate
import filmkit.repository as repository
from filmkit.concepts import Place

# The register check itself, kept before a fixture stands in for it.
REGISTER_CHECK = narration_narrate.register.check
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
def gates(monkeypatch) -> list:
    """The editions the narration gate checked, through checks that pass."""
    checked = []
    monkeypatch.setattr(narration_narrate.concepts, "check", lambda: {"concepts": 2})
    monkeypatch.setattr(narration_narrate.register, "check", lambda: {"warnings": ["我们"]})
    monkeypatch.setattr(
        narration_narrate.readings, "check", lambda code: checked.append(code) or {"edition": code}
    )
    monkeypatch.setattr(narration_narrate.anchors, "require_editions", dict)
    return checked


@pytest.fixture
def commands(monkeypatch, gates, tmp_path) -> list:
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
    out = capsys.readouterr().out
    # A Chinese form reaches the author as written.
    assert "我们" in out.splitlines()[0]
    printed = [json.loads(line) for line in out.splitlines()]
    assert printed[0] == {
        "edition": "en",
        "gate": {
            "concepts": {"concepts": 2},
            "register": {"warnings": ["我们"]},
            "readings": {"edition": "en"},
            # A film without a composition is not asked what its picture reads of its anchors.
            "picture_reads": "not asked: the film has no composition",
        },
    }
    assert [line["step"] for line in printed[1:]] == ["narration", "alignment", "transcription"]


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


def test_the_gate_runs_before_narration_and_its_plan_but_not_before_the_checks(commands, gates):
    narration_narrate.main(["--language", "zh", "--dry-run"])
    narration_narrate.main(["--language", "zh", "--skip-generation"])
    narration_narrate.main(["--language", "en"])
    assert gates == ["zh", "en"]


def test_a_refused_gate_stops_narration_before_any_step(commands, monkeypatch):
    def refuse(code):
        message = f"zh 04.2 at 9: 重 in “代码和日期去重。” has no declared reading ({code})"
        raise narration_narrate.readings.ReadingError(message)

    monkeypatch.setattr(narration_narrate.readings, "check", refuse)
    with pytest.raises(SystemExit, match="Narration refused before synthesis:\nzh 04.2 at 9"):
        narration_narrate.main(["--language", "zh", "--dry-run"])
    assert commands == []

    def contract_refuses():
        message = "zh 03 declares rebuild but says none of: 重建"
        raise narration_narrate.concepts.ConceptError(message)

    monkeypatch.setattr(narration_narrate.concepts, "check", contract_refuses)
    with pytest.raises(SystemExit, match="declares rebuild but says none of"):
        narration_narrate.main(["--language", "en"])
    assert commands == []


def test_a_run_records_its_duration_with_each_step_as_a_phase(commands):
    narration_narrate.main(["--language", "zh", "--ids", "06,07"])
    record = repository.read("build/evidence/editions/zh/durations/narrate-06-07.json")
    assert (record["command"], record["completed"]) == ("narrate-06-07", True)
    assert [*record["phases"]] == ["narration", "alignment", "transcription"]
    assert len(commands) == 3


def test_a_check_only_run_is_recorded_as_such_and_leaves_the_narrations_record(commands):
    durations = repository.ROOT / "build/evidence/editions/zh/durations"
    narration_narrate.main(["--language", "zh"])
    narrated = (durations / "narrate.json").read_bytes()
    # The checks alone, as a film runs them after narrating chosen segments by hand.
    narration_narrate.main(["--language", "zh", "--skip-generation"])
    assert (durations / "narrate.json").read_bytes() == narrated
    record = repository.read(durations / "narrate-checks.json")
    assert (record["command"], record["completed"]) == ("narrate-checks", True)
    assert [*record["phases"]] == ["alignment", "transcription"]
    narration_narrate.main(["--language", "zh", "--skip-generation", "--ids", "06,07"])
    assert repository.read(durations / "narrate-checks-06-07.json")["command"] == (
        "narrate-checks-06-07"
    )
    assert sorted(path.name for path in durations.iterdir()) == [
        "narrate-checks-06-07.json",
        "narrate-checks.json",
        "narrate.json",
    ]


def test_a_dry_run_writes_no_duration_record(commands):
    narration_narrate.main(["--language", "zh", "--dry-run"])
    assert not (repository.ROOT / "build/evidence/editions/zh/durations").exists()
    assert len(commands) == 1


def test_a_form_the_register_refuses_stops_narration_before_any_step(commands, monkeypatch):
    monkeypatch.setattr(narration_narrate.register, "check", REGISTER_CHECK)
    held = {"zh": [Place("zh 01.1", "你们先看。")]}
    monkeypatch.setattr(narration_narrate.concepts, "places", lambda: held)
    with pytest.raises(SystemExit) as refusal:
        narration_narrate.main(["--language", "zh", "--dry-run"])
    assert str(refusal.value) == (
        "Narration refused before synthesis:\nzh 01.1: '你们' addresses the audience (R1)\n"
        "A film keeps a standard word or a quotation at its place by declaring it in "
        "[[register.exceptions]]: its place, its form, the text the form stands within there "
        "(within) and a reason"
    )
    assert commands == []
