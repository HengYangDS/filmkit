"""The engine's build graph: one record of every run of a node, the node table, and the plan,
the build and the verification that read the records (the OpenSpec capability `run-records`).

A refusal that names a step to run names it as the verb that runs it, from the functions here
(design decision 18 of build-a-film-by-its-verbs): a node's run as the plan names it (`key`), the
build of one node or of several (`target`, `build_command`) and an edition's narration
(`narrate_command`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def key(node: str, code: str | None = None) -> str:
    """A node's run as the plan names it: `<node>:<code>` for an edition's, the node's name for
    the film's."""
    return node if code is None else f"{node}:{code}"


def build_command(keys: Iterable[str]) -> str:
    """The command that builds the nodes the keys name, in one invocation."""
    return " ".join(["filmkit build", *keys])


def target(node: str, code: str | None = None) -> str:
    """The command that builds one node of an edition, or the film-wide one."""
    return build_command([key(node, code)])


def narrate_command(code: str) -> str:
    """The command that narrates an edition, the narration being no build's."""
    return f"filmkit narrate --edition {code}"
