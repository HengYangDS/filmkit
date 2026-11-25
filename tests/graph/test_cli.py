"""The `filmkit` console command: its ten verbs and their options, `deliver`'s order of asking,
one-line refusals, and `plan` on the sample's sound chain (design decision 10 of
record-every-run, 17 of build-a-film-by-its-verbs)."""

import json
import os
import re
import subprocess
import sys

import pytest
import sample_sound

import filmkit.child_processes as child_processes
import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.release as release
import filmkit.delivery.verification as delivery_verification
import filmkit.repository as repository
import filmkit.supply as supply
from filmkit.delivery.reproduction import ReproductionError
from filmkit.graph import cli, verify

VERBS = (
    "supply",
    "check",
    "edit",
    "narrate",
    "plan",
    "build",
    "verify",
    "review",
    "deliver",
    "release",
)
# Each verb's options as design decision 17 states them.
OPTIONS = {
    "supply": [],
    "check": ["--read-only"],
    "edit": ["--edits", "--dry-run"],
    "narrate": ["--edition", "--rounds", "--takes"],
    "plan": ["TARGET", "--json"],
    "build": ["TARGET"],
    "verify": ["--technical-only", "--release"],
    "review": ["{prepare,record,set-aside}"],
    "deliver": ["--to", "--dry-run"],
    "release": ["--replace", "--dry-run"],
}


def ended(capsys, *argv: str) -> tuple[int | str | None, str]:
    """The command's exit status or refusal, and what it printed: 0 where it returned."""
    try:
        cli.main(list(argv))
    except SystemExit as stopped:
        return stopped.code, capsys.readouterr().out
    return 0, capsys.readouterr().out


def test_the_help_lists_its_ten_verbs(capsys):
    status, said = ended(capsys, "--help")
    assert status == 0
    # Each verb begins a line of the listing, indented by four; its wrapped help, by more.
    listed = [found[1] for line in said.splitlines() if (found := re.match(r"    (\w+)", line))]
    assert listed == list(VERBS)


@pytest.mark.parametrize("verb", VERBS)
def test_each_verb_states_its_options(verb, capsys):
    status, said = ended(capsys, verb, "--help")
    assert status == 0
    words = {word.strip("[]") for word in said.split()}
    assert set(OPTIONS[verb]) <= words
    stated = {word for word in words if word.startswith("--")} - {"--help"}
    assert stated == {option for option in OPTIONS[verb] if option.startswith("--")}


def test_a_review_command_states_its_own_options_under_the_verb(capsys):
    status, said = ended(capsys, "review", "record", "--help")
    assert status == 0
    assert said.startswith("usage: filmkit review record ")
    assert "--round-dir" in said


def test_deliver_asks_the_records_then_the_films_and_review_before_it_plans_a_copy(
    capsys, monkeypatch, tmp_path
):
    asked = []
    monkeypatch.setattr(verify, "check", lambda: asked.append("records"))

    def qualified(*, technical_only):
        asked.append(("films and review", technical_only))
        yield {}

    monkeypatch.setattr(delivery_verification, "qualified", qualified)
    monkeypatch.setattr(delivery_folder, "delivery_destination", lambda to: (tmp_path, "--to"))

    def planned(root, folder, *, dry_run, rule):
        asked.append(("copy", dry_run))
        return {"destination": str(folder), "destination_rule": rule, "dry_run": True}

    monkeypatch.setattr(delivery_folder, "deliver", planned)
    status, said = ended(capsys, "deliver", "--dry-run", "--to", str(tmp_path))
    assert status == 0
    assert asked == ["records", ("films and review", False), ("copy", True)]
    assert json.loads(said)["dry_run"] is True
    # A refusal of the records, or of an edition's films, stops before anything else is asked.
    asked.clear()

    def refused(_table=None):
        raise verify.VerifyError("filmkit verify refuses: no record: assemble:zh")

    monkeypatch.setattr(verify, "check", refused)
    status, _ = ended(capsys, "deliver", "--dry-run")
    assert status == "filmkit verify refuses: no record: assemble:zh"
    assert asked == []
    monkeypatch.setattr(verify, "check", lambda: asked.append("records"))

    def unscanned(*, technical_only):
        raise SystemExit("zh: The zh film has no still scan record; run filmkit build scan-film:zh")
        yield {}

    monkeypatch.setattr(delivery_verification, "qualified", unscanned)
    status, _ = ended(capsys, "deliver", "--dry-run")
    assert status.startswith("zh: The zh film has no still scan record")
    assert asked == ["records"]


def stand_in(error):
    def refuse(*_args, **_kwargs):
        raise error

    return refuse


@pytest.mark.parametrize(
    ("argv", "patch", "line"),
    [
        (
            ["narrate", "--edition", "fr"],
            None,
            "The film declares no edition fr: it declares zh, en, or all",
        ),
        (["narrate", "--takes", "0"], None, "filmkit narrate: --rounds is 0 or more and --takes"),
        (["edit", "--edits", "absent.json"], None, "filmkit edit: [Errno 2] No such file"),
        (["build", "pictures:zh"], None, "filmkit build: pictures:zh names no node or group"),
        (
            ["supply"],
            (supply, "supply", supply.SupplyError("The CMUdict differs from the pinned SHA-256")),
            "The CMUdict differs from the pinned SHA-256",
        ),
        (
            ["release", "--dry-run"],
            (release, "write", ReproductionError("release.json is not a release manifest")),
            "release.json is not a release manifest",
        ),
    ],
)
def test_a_refusal_is_one_line(argv, patch, line, capsys, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    if patch:
        owner, attribute, error = patch
        monkeypatch.setattr(owner, attribute, stand_in(error))
    status, _ = ended(capsys, *argv)
    assert isinstance(status, str) and "\n" not in status
    assert status.startswith(line)


MISSING = "No node on PATH; run the tools in the film's Mise environment"


@pytest.mark.parametrize(
    ("error", "status", "said"),
    [
        (None, child_processes.FINISHED, ""),
        (supply.SupplyError("The CMUdict differs"), child_processes.REFUSED, ""),
        (child_processes.MissingToolError(MISSING), child_processes.UNFINISHED, f"{MISSING}\n"),
        (
            FileNotFoundError(2, "No such file or directory", "ffprobe"),
            child_processes.UNFINISHED,
            "No ffprobe on the path; install it as Homebrew does: brew install ffmpeg\n",
        ),
        (RuntimeError("the disk is gone"), child_processes.UNFINISHED, "Traceback"),
    ],
)
def test_the_exit_status_tells_a_refusal_from_a_failure_to_finish(
    error, status, said, capsys, monkeypatch
):
    # Done is 0; a refusal, one line that Python prints as it exits, is 1; an owner's exception
    # is 2, with its traceback, and a tool the host lacks is 2, named in one line.
    monkeypatch.setattr(supply, "supply", stand_in(error) if error else dict)
    try:
        cli.main(["supply"])
        code = child_processes.FINISHED
    except SystemExit as stopped:
        code = stopped.code
    assert (child_processes.REFUSED if isinstance(code, str) else code) == status
    err = capsys.readouterr().err
    if said == "Traceback":
        assert err.startswith(said) and err.endswith("RuntimeError: the disk is gone\n")
    else:
        assert err == said


@pytest.fixture(scope="module")
def moved_too_late(tmp_path_factory):
    """A copy of the sample that still holds its release record at `content/release.json`, the
    place the loader now refuses."""
    root = sample_sound.copy_film((tmp_path_factory.mktemp("moved") / "film").resolve())
    (root / "content/release.json").write_text("{}\n")
    return root


@pytest.mark.parametrize("argv", [["plan"], ["build", "check"], ["verify"], ["check"]])
def test_a_declaration_the_loader_refuses_is_a_refusal_of_every_verb(moved_too_late, argv):
    environment = {**os.environ, repository.ROOT_VARIABLE: str(moved_too_late)}
    ran = subprocess.run(
        [sys.executable, "-I", "-B", "-c", f"from filmkit.graph import cli; cli.main({argv!r})"],
        env=environment,
        cwd=moved_too_late,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    (line,) = ran.stderr.splitlines()
    assert ran.returncode == child_processes.REFUSED
    # The source check prints each finding and ends with its count, as its read-only mode does;
    # every other verb refuses with the loader's line.
    said = ran.stdout if argv == ["check"] else line
    assert "content/release.json" in said and "release.json at the film's root" in said
    assert not (moved_too_late / "build/evidence/records").exists()


@pytest.mark.ffmpeg
def test_plan_prints_each_node_of_the_sound_chain_as_json(sound_chain, capsys):
    cli.main(["plan", "check-sound:zh", "--json"])
    planned = json.loads(capsys.readouterr().out)
    found = {entry["node"]: entry for entry in planned["nodes"]}
    chain = ["narrate:zh", *(f"{name}:zh" for name in sample_sound.SOUND)]
    # The narration waits for the source check, which the light suite does not run: each node
    # of the chain is fresh by its own record and waits for it.
    assert list(found) == ["check", *chain]
    fields = {"node", "state", "reasons", "class", "expected", "seconds", "ready", "waits"}
    fields.add("standing")
    assert all(set(entry) == fields for entry in found.values())
    assert (found["check"]["state"], found["check"]["class"]) == ("stale", "unmeasured")
    for key in chain:
        entry = found[key]
        assert (entry["state"], entry["reasons"], entry["ready"]) == ("waiting", [], False)
        assert (entry["waits"], entry["standing"]) == ([{"node": "check", "state": "stale"}], None)
        assert entry["seconds"] > 0
    assert (found["narrate:zh"]["class"], found["narrate:zh"]["expected"]) == ("gpu", "gpu")
    assert found["check-sound:zh"]["class"] == "light"
    assert planned["hashed"] == 0


@pytest.mark.ffmpeg
def test_an_unknown_target_is_refused_in_one_line_naming_the_nodes(sound_chain):
    with pytest.raises(SystemExit) as refused:
        cli.main(["plan", "pictures:zh"])
    line = refused.value.code
    assert isinstance(line, str) and "\n" not in line
    assert line.startswith("filmkit plan: pictures:zh names no node or group of the plan; ")
    assert "check-sound" in line and "package-film" in line
