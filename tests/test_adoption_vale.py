"""The adoption command's Vale question: the one tool name it reads, in the one file the film's
tasks are read from, and what its finding says of what stands there."""

import shutil

import pytest
import test_adoption as base

import filmkit.released as released

# A film that holds what the release asks, its findings, and the tasks its Mise file states.
project, found, TASKS = base.project, base.found, base.TASKS
# The tool the engine pins, the version its record states, and how a finding names both.
TOOL, ASKED = released.VALE, released.vale()
ON = f"the engine was released on Vale {ASKED}"
PINNED = f'[tools]\n"{TOOL}" = "{ASKED}"\n'
# How a finding that names no pin ends: the record's version and the entry to add.
ADD = f'{ON}: pin "{TOOL}" = "{ASKED}" under [tools]'
# The finding for a Mise file that holds no version under the tool's name: it names the file it
# read and the name it looked under, and does not say that the film pins none.
ABSENT = f'{{file}} holds no "{TOOL}" version under [tools]; {ADD}'
# What a film's Mise configuration states of Vale, and the finding that names it: its pin, or its
# absence under the tool's name, with the version the release record states. A pin under another
# name, in another form or of no one version is not the release's.
PINS = [
    (PINNED, None),
    (f'[tools."{TOOL}"]\nversion = "{ASKED}"\n', None),
    (f'[tools]\n"{TOOL}" = "9.9.9"\n', f"config.toml pins Vale 9.9.9; {ON}"),
    (f'[tools."{TOOL}"]\nversion = "9.9.8"\n', f"config.toml pins Vale 9.9.8; {ON}"),
    (f'[tools]\n"{TOOL}" = ["{ASKED}"]\n', f"config.toml pins Vale ['{ASKED}']; {ON}"),
    ('[tools]\nnode = "26.13.1"\n', ABSENT.format(file="config.toml")),
    (f'[tools]\nvale = "{ASKED}"\n', ABSENT.format(file="config.toml")),
    (f'[tools]\n"aqua:errata-ai/vale" = "{ASKED}"\n', ABSENT.format(file="config.toml")),
    ("", ABSENT.format(file="config.toml")),
]


@pytest.mark.parametrize(("tools", "finding"), PINS)
def test_a_film_that_pins_another_vale_or_none_under_the_tools_name_is_named(
    project, tools, finding
):
    (project / ".config/mise/config.toml").write_text(TASKS + tools)
    assert found(project)["vale"] == ([finding] if finding else [])


@pytest.mark.parametrize("name", ["mise.toml", ".mise.toml"])
def test_the_pin_is_read_in_whichever_of_mises_files_holds_the_tasks(project, name):
    # A film whose one Mise file bears another of Mise's names is read there, and named by it.
    shutil.rmtree(project / ".config")
    (project / name).write_text(TASKS + PINNED)
    assert found(project)["vale"] == []
    (project / name).write_text(TASKS)
    assert found(project)["vale"] == [ABSENT.format(file=name)]


def test_a_pin_in_another_of_mises_files_is_not_read_and_the_finding_says_where_it_looked(project):
    # The tasks stand in .config/mise/config.toml, the one file read: a pin in mise.toml beside it
    # is not the release's, and the finding names the file that holds none.
    (project / ".config/mise/config.toml").write_text(TASKS)
    (project / "mise.toml").write_text(PINNED)
    assert found(project)["vale"] == [ABSENT.format(file="config.toml")]


def test_a_film_without_a_mise_configuration_is_told_the_version_and_the_entry_to_add(project):
    shutil.rmtree(project / ".config")
    assert found(project)["vale"] == [
        "the film has no Mise configuration (.config/mise/config.toml, mise.toml, .mise.toml) at "
        f"or above it; {ADD}"
    ]


def test_tools_that_are_no_table_are_a_finding_of_the_question(project):
    (project / ".config/mise/config.toml").write_text('tools = "vale"\n' + TASKS)
    assert found(project)["vale"] == ["config.toml: tools holds no table where one is read"]
