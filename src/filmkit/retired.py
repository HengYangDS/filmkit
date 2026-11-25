"""The module commands that `build-a-film-by-its-verbs` retired, each with the verb that
replaced it.

Each such module stays, since the verbs call its functions, but run as `python -m` it refuses in
one line that names its verb and exits 1: a film's task or gate that still runs it fails, and
never passes by doing nothing. The modules that left with their commands (the production command,
the pre-render check, the adoption command, the media server and the duration records) are no
module any more, so Python refuses them by itself.
"""

from __future__ import annotations

from typing import NoReturn

# Each retired module command and the verb that replaced it.
VERBS = {
    "filmkit.supply": "filmkit supply",
    "filmkit.concepts": "filmkit check",
    "filmkit.register": "filmkit check",
    "filmkit.tools": "filmkit build",
    "filmkit.narration.converge": "filmkit narrate",
    "filmkit.narration.script_edits": "filmkit edit",
    "filmkit.delivery.verification": "filmkit verify --technical-only",
    "filmkit.delivery.reproduction": "filmkit verify --release",
    "filmkit.delivery.release": "filmkit release",
    "filmkit.delivery.folder": "filmkit deliver",
    "filmkit.review.round": "filmkit review",
    "filmkit.graph.cli": "filmkit",
}


def refuse(module: str) -> NoReturn:
    """End a retired module command in one line that names the verb that replaced it."""
    name = module.removesuffix(".__main__")
    msg = f"python -m {name} is retired: run {VERBS[name]}"
    raise SystemExit(msg)
