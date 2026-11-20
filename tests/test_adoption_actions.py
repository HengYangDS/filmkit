"""The actions the adoption command knows: read from the command's source, where the command
cannot be imported, and held to the command's own table."""

import pytest

import filmkit.adoption as adoption
import filmkit.produce as produce

# How the command of a made-up engine imports the module that states an action's name.
OWNER = "import filmkit.picture.owner as owner\n"


def command_with(folder, source):
    """A command's source in a made-up engine, beside a module and a package that state names."""
    (folder / "picture").mkdir()
    (folder / "picture/__init__.py").write_text('ACTION = "scan"\n')
    (folder / "picture/owner.py").write_text(
        'COUNT = 1\nACTION = "scan"\nTWICE = "scan"\nTWICE = "film"\n'
        'GROWN = "scan"\nGROWN += "-film"\nif COUNT:\n    BRANCH = "scan"\n'
    )
    (folder / "produce.py").write_text(source)
    return folder / "produce.py"


def table(entries):
    return f"EDITION_ACTIONS: dict = {{{entries}}}\n"


def test_the_actions_read_from_the_command_are_the_commands_own():
    assert adoption.engine_actions() == set(produce.EDITION_ACTIONS)


def test_an_action_named_through_a_module_is_read_where_the_module_states_it(tmp_path):
    command = command_with(tmp_path, OWNER + table('"select": None, owner.ACTION: None'))
    assert adoption.engine_actions(command) == {"select", "scan"}


@pytest.mark.parametrize(
    "source",
    [
        # A key that is no string and no name of an imported module of the engine.
        OWNER + table('"select": None, 1: None'),
        OWNER + table('"select": None, "scan".strip(): None'),
        OWNER + table('"select": None, ACTION: None'),
        OWNER + table('"select": None, other.ACTION: None'),
        OWNER + table('"select": None, **others'),
        # A name that its module states as no string, nowhere, twice, by steps or in a branch.
        OWNER + table("owner.COUNT: None"),
        OWNER + table("owner.MISSING: None"),
        OWNER + table("owner.TWICE: None"),
        OWNER + table("owner.GROWN: None"),
        OWNER + table("owner.BRANCH: None"),
        # A module that is not the engine's, a package, an import in another form or place, and a
        # name the command binds again.
        "import other.picture.owner as owner\n" + table("owner.ACTION: None"),
        "import filmkit.picture as owner\n" + table("owner.ACTION: None"),
        "from filmkit.picture import owner\n" + table("owner.ACTION: None"),
        "if True:\n    " + OWNER + table("owner.ACTION: None"),
        OWNER + "owner = None\n" + table("owner.ACTION: None"),
        # A table stated twice, added to, stated below the top level, or stated as no table.
        table('"select": None') + table('"scan": None'),
        table('"select": None') + 'EDITION_ACTIONS |= {"scan": None}\n',
        "def actions():\n    " + table('"select": None'),
        "EDITION_ACTIONS: dict = dict(select=None)\n",
        "ACTIONS: dict = {}\n",
    ],
)
def test_a_form_the_adoption_command_cannot_read_is_refused_never_left_out(tmp_path, source):
    with pytest.raises(LookupError, match="adoption command"):
        adoption.engine_actions(command_with(tmp_path, source))
