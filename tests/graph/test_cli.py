"""The `filmkit` console command: `plan` on the sample's sound chain and its refusal of a target
that names no node, and its help (design decision 10 of record-every-run)."""

import json

import pytest
import sample_sound

from filmkit.graph import cli


def test_the_help_lists_its_verbs(capsys):
    with pytest.raises(SystemExit) as ended:
        cli.main(["--help"])
    assert ended.value.code == 0
    said = capsys.readouterr().out
    assert "{check,plan,verify}" in said
    assert [verb for verb in ("plan", "verify") if f"    {verb} " in said] == ["plan", "verify"]


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
