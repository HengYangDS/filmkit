"""The `filmkit` console command: its ten verbs and their options, `deliver`'s order of asking,
one-line refusals, and `plan` on the sample's sound chain (design decision 10 of
record-every-run, 17 of build-a-film-by-its-verbs)."""

import json
import re

import pytest
import sample_sound

import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.release as release
import filmkit.delivery.verification as delivery_verification
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


@pytest.mark.ffmpeg
def test_plan_prints_each_node_of_the_sound_chain_as_json(sound_chain, capsys):
    cli.main(["plan", "check-sound:zh", "--json"])
    planned = json.loads(capsys.readouterr().out)
    found = {entry["node"]: entry for entry in planned["nodes"]}
    assert list(found) == ["narrate:zh", *(f"{name}:zh" for name in sample_sound.SOUND)]
    for entry in found.values():
        assert set(entry) == {"node", "state", "reasons", "class", "expected", "seconds", "ready"}
        assert (entry["state"], entry["reasons"], entry["ready"]) == ("fresh", [], True)
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
