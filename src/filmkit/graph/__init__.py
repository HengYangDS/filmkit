"""The engine's build graph: one record of every run of a node, the node table, and the plan,
the build and the verification that read the records (the OpenSpec capability `run-records`)."""


def target(node: str, code: str | None = None) -> str:
    """The command that builds one node of an edition, or the film-wide one, as a refusal names
    the step to run (design decision 18 of build-a-film-by-its-verbs)."""
    return f"filmkit build {node}:{code}" if code else f"filmkit build {node}"
