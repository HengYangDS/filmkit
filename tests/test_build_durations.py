"""A build's durations: which records the printed sum covers, and the tools' runs."""

import json

import pytest

import filmkit.durations as durations
import filmkit.repository as repository
import filmkit.tools as tools


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return tmp_path.resolve()


def record(code, command, started, seconds, completed=True):
    repository.write(
        f"build/evidence/editions/{code}/durations/{command}.json",
        {
            "command": command,
            "edition": code,
            "started_at": started,
            "seconds": seconds,
            "completed": completed,
            "phases": {},
            "settings": {},
        },
    )


def printed(capsys, *arguments) -> list[str]:
    durations.main(list(arguments))
    return capsys.readouterr().out.splitlines()


@pytest.mark.usefixtures("root")
def test_the_sum_covers_what_started_at_or_after_the_latest_whole_narration(capsys):
    # Last week's repair and a retake of two segments, then today's build from its narration.
    record("zh", "repair-pictures", "2026-11-10T08:00:00+00:00", 600.0)
    record("zh", "narrate-06-07", "2026-11-16T09:00:00+00:00", 80.0)
    record("zh", "narrate", "2026-11-17T01:00:00+00:00", 99.0)
    record("zh", "check-picture", "2026-11-17T01:05:00+00:00", 40.5)
    record("zh", "render-picture", "2026-11-17T01:06:00+00:00", 900.0)
    record("zh", "package-film", "2026-11-17T01:30:00+00:00", 12.0, completed=False)
    lines = printed(capsys, "--language", "zh")
    assert lines[0] == "zh:"
    assert [line.split()[1] for line in lines[1:7]] == [
        "repair-pictures",
        "narrate-06-07",
        "narrate",
        "check-picture",
        "render-picture",
        "package-film",
    ]
    # The two records of earlier work are listed as earlier and left out.
    assert lines[1].endswith("600.0 s  earlier") and lines[2].endswith("80.0 s  earlier")
    assert lines[3].endswith("99.0 s")
    assert lines[7] == (
        "  sum of the 3 commands completed since the narration started at "
        "2026-11-17T01:00:00+00:00: 1039.5 s; 2 earlier records are not counted"
    )


@pytest.mark.usefixtures("root")
def test_a_check_only_narration_neither_starts_a_build_nor_drops_what_ran_before_it(capsys):
    # A build narrates, renders, runs the narration's checks again and packages.
    record("zh", "narrate", "2026-11-17T01:00:00+00:00", 700.0)
    record("zh", "render-picture", "2026-11-17T01:12:00+00:00", 600.0)
    record("zh", "narrate-checks", "2026-11-17T01:23:00+00:00", 60.0)
    record("zh", "narrate-checks-06-07", "2026-11-17T01:24:30+00:00", 20.0)
    record("zh", "package-film", "2026-11-17T01:25:00+00:00", 300.0)
    lines = printed(capsys, "--language", "zh")
    assert not [line for line in lines if line.endswith("earlier")]
    assert lines[-2] == (
        "  sum of the 5 commands completed since the narration started at "
        "2026-11-17T01:00:00+00:00: 1680.0 s"
    )


@pytest.mark.usefixtures("root")
def test_since_names_another_start_and_no_narration_counts_every_record(capsys):
    record("en", "check-picture", "2026-11-17T01:05:00+00:00", 40.0)
    record("en", "render-picture", "2026-11-17T01:06:00+00:00", 900.0)
    lines = printed(capsys, "--language", "en")
    assert lines[-2] == (
        "  sum of the 2 commands completed (no whole narration is recorded, so every record "
        "counts): 940.0 s"
    )
    lines = printed(capsys, "--language", "en", "--since", "2026-11-17T01:06:00+00:00")
    assert lines[1].endswith("40.0 s  earlier")
    assert lines[-2] == (
        "  sum of the 1 commands completed since 2026-11-17T01:06:00+00:00: 900.0 s; "
        "1 earlier records are not counted"
    )
    with pytest.raises(SystemExit):
        durations.main(["--since", "yesterday"])


@pytest.mark.usefixtures("root")
def test_commands_at_the_same_time_count_once_in_the_time_one_of_them_was_running(capsys):
    # Each edition's narration in a row, both renders at once, then the packages; the English
    # package was refused and its repair is last week's.
    record("zh", "narrate", "2026-11-17T01:00:00+00:00", 60.0)
    record("en", "narrate", "2026-11-17T01:01:00+00:00", 60.0)
    record("zh", "render-picture", "2026-11-17T01:02:00.000+00:00", 170.0)
    record("en", "render-picture", "2026-11-17T01:02:00.500+00:00", 172.0)
    record("zh", "package-film", "2026-11-17T01:10:00+00:00", 30.0)
    record("en", "package-film", "2026-11-17T01:11:00+00:00", 30.0, completed=False)
    record("en", "repair-pictures", "2026-11-10T08:00:00+00:00", 600.0)
    assert printed(capsys)[-1] == (
        "build: one of the 5 counted commands was running for 322.5 s; their seconds add up to "
        "492.0 s (commands that ran at the same time count once in the first figure)"
    )
    # Commands in a row: the two figures are equal.
    assert printed(capsys, "--language", "zh")[-2:] == [
        "  sum of the 3 commands completed since the narration started at "
        "2026-11-17T01:00:00+00:00: 260.0 s",
        "build: one of the 3 counted commands was running for 260.0 s; their seconds add up to "
        "260.0 s (commands that ran at the same time count once in the first figure)",
    ]


@pytest.mark.parametrize(
    ("arguments", "code"),
    [
        (["build/runtime/work/final-delivery-zh-uhd", "build/evidence/x.json", "2"], "zh"),
        (["cover", "build/runtime/work/final-delivery-en-uhd", "assets/cover.png", "c.png"], "en"),
        (["build/artifacts/film/en/timeline.json", "0.5"], "en"),
        (["{root}/build/evidence/editions/zh/picture-geometry.json"], "zh"),
        # Another film's stage is no edition of this film.
        (["/elsewhere/build/evidence/editions/zh/picture-geometry.json"], None),
        (["../other-film/build/runtime/work/final-delivery-zh-uhd"], None),
        (["players", "binding.json", "receipt.json"], None),
        (["build/runtime/work/final-delivery-zh-uhd", "build/evidence/editions/en/x.json"], None),
    ],
)
def test_a_tools_edition_is_read_from_its_arguments_when_they_name_one(root, arguments, code):
    named = [argument.format(root=root) for argument in arguments]
    assert tools.edition_of(named) == code


STAGE = "build/runtime/work/final-delivery-zh-uhd"
GEOMETRY = "build/evidence/editions/zh/picture-geometry.json"


@pytest.mark.parametrize(
    ("command", "record"),
    [
        (["geometry-check", STAGE, GEOMETRY, "2"], "geometry-check"),
        (["player-check", "cover", STAGE, "cover.png", "painting.png"], "player-check-cover"),
        # Any other tool, and the player check in another mode, is a run by hand.
        (["frame-audit", "build/artifacts/film/zh/timeline.json", "0.0333333"], None),
        (["caption-equivalence", "build/artifacts/film/zh/timeline.json", "0.5"], None),
        (["band-audit", "build/artifacts/film/zh/timeline.json", "936", "1024", "30"], None),
        (["player-check", "players", "build/evidence/editions/zh/binding.json", "r.json"], None),
        # The two checks of a build, for no single edition of this film.
        (["geometry-check", "/elsewhere/" + STAGE, "/elsewhere/" + GEOMETRY], None),
    ],
)
def test_only_the_checks_a_build_runs_from_the_command_line_write_a_duration_record(
    root, monkeypatch, command, record
):
    monkeypatch.setattr(tools, "run", lambda tool, arguments: 0)
    with pytest.raises(SystemExit) as ended:
        tools.main(command)
    assert ended.value.code == 0
    written = sorted(path.stem for path in root.rglob("durations/*.json"))
    assert written == ([] if record is None else [record])
    assert tools.recorded(command[0], command[1:]) == (None if record is None else ("zh", record))


def test_a_check_of_a_build_is_recorded_whether_it_passes_or_fails(root, monkeypatch):
    ran = []
    monkeypatch.setattr(tools, "run", lambda tool, arguments: ran.append(tool) or 0)
    durations_folder = root / "build/evidence/editions/zh/durations"
    with pytest.raises(SystemExit) as ended:
        tools.main(["geometry-check", STAGE, GEOMETRY])
    assert ended.value.code == 0
    written = json.loads((durations_folder / "geometry-check.json").read_text())
    assert (written["command"], written["completed"]) == ("geometry-check", True)
    # A start is recorded to the millisecond, so that runs in a row never seem to overlap.
    assert len(written["started_at"]) == len("2026-11-17T01:00:00.000+00:00")
    # A failing check's run is recorded as not completed, and the command exits with its status.
    monkeypatch.setattr(tools, "run", lambda tool, arguments: ran.append(tool) or 1)
    with pytest.raises(SystemExit) as ended:
        tools.main(["player-check", "cover", STAGE, "cover.png", "painting.png"])
    assert ended.value.code == 1
    written = json.loads((durations_folder / "player-check-cover.json").read_text())
    assert (written["command"], written["completed"]) == ("player-check-cover", False)
    # A run that is no check of a build leaves both records byte for byte and adds none.
    before = {path.name: path.read_bytes() for path in root.rglob("durations/*.json")}
    for command in (
        ["player-check", "players", GEOMETRY, "receipt.json"],
        ["frame-audit", "build/artifacts/film/zh/timeline.json", "0.0333333"],
        ["geometry-check", "binding.json", "receipt.json"],
    ):
        with pytest.raises(SystemExit):
            tools.main(command)
    assert {path.name: path.read_bytes() for path in root.rglob("durations/*.json")} == before
    assert sorted(before) == ["geometry-check.json", "player-check-cover.json"]
    assert ran[2:] == ["player-check", "frame-audit", "geometry-check"]
