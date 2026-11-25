"""`filmkit build` on stand-in nodes and files: the closure run in the derived order, each node
judged again at its turn and run only where stale (design decision 3 of
build-a-film-by-its-verbs)."""

from dataclasses import replace

import pytest
import stand_ins
from stand_ins import CODES

import filmkit.repository as repository
from filmkit.graph import build, nodes, plan, records, runs
from filmkit.soundtrack.assembly import AssemblyError


def owner(name):
    """A stand-in node's owner: it writes what the node writes (`stand_ins.WRITES`)."""
    return lambda edition: stand_ins.wrote(name, edition.code)


@pytest.fixture
def table(stand_in_table, monkeypatch):
    """The stand-in table with each node's owner as its run, but the narration's, and the render
    waiting for its edition's sound gate; every node light, so that one invocation runs them all
    (the scheduling of heavy work is `test_build_schedule.py`'s)."""
    held = tuple(
        replace(
            node,
            run=None if node.name == "narrate" else owner(node.name),
            waits=(nodes.Wait("check-sound"),) if node.name == "render" else (),
            expected="gpu" if node.name == "narrate" else "light",
        )
        for node in stand_ins.TABLE
    )
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in held})
    return nodes.load(held, stand_ins.SHARED, CODES)


def keys(*names, codes=CODES):
    return {nodes.key(name, code) for name in names for code in codes}


EVERY = ("assemble", "refresh-captions", "check-sound", "package-metadata", "stage", "render")
EVERY += ("compare",)


def states(table):
    return {entry.key: entry.state for entry in plan.plan(table).entries}


def test_a_chain_is_built_from_nothing_in_the_derived_order_and_a_second_build_runs_nothing(table):
    built = build.build(table, ["all"])
    assert set(built.ran) == keys(*EVERY)
    assert built.ran == [key for key in table.order if key in built.ran]
    assert (built.refused, built.held, built.status) == ([], [], 0)
    assert {key for key, state in states(table).items() if state != "fresh"} == keys("narrate")
    # A node first run is recorded with the class it measured at.
    assert records.read(records.place("assemble", "zh")).host_class == "light"
    again = build.build(table, ["all"])
    assert (again.ran, again.refused, again.status) == ([], [], 0)


def test_an_edited_input_reruns_only_the_nodes_whose_inputs_then_change(table):
    build.build(table, ["all"])
    (repository.ROOT / "en/script.txt").write_text("the en script, edited")
    built = build.build(table, ["all"])
    assert set(built.ran) == keys(*EVERY, codes=("en",))
    assert build.build(table, ["all"]).ran == []


def test_a_gate_run_again_with_unchanged_inputs_downstream_leaves_the_waiting_node_unrun(table):
    build.build(table, ["all"])
    before = records.place("check-sound", "zh").read_bytes()
    stand_ins.ran("check-sound", "zh")
    assert records.place("check-sound", "zh").read_bytes() != before
    assert build.build(table, ["render:zh"]).ran == []


def test_a_refused_gate_holds_what_follows_it_and_the_other_edition_is_built(table, monkeypatch):
    def refuse(edition):
        if edition.code == "zh":
            raise AssemblyError("the soundtrack has 1 gated finding")
        stand_ins.wrote("check-sound", edition.code)

    gate = replace(table.nodes["check-sound"], run=refuse)
    held = {**table.nodes, "check-sound": gate}
    monkeypatch.setattr(runs, "table", lambda: held)
    table = nodes.load(held.values(), stand_ins.SHARED, CODES)
    built = build.build(table, ["all"])
    assert built.refused == ["check-sound:zh: the soundtrack has 1 gated finding"]
    assert records.read(records.place("check-sound", "zh")).outcome == "refuse"
    # The render waits for the gate, and the page reads its output: neither runs.
    assert {"render:zh", "compare:zh", "package-metadata:zh"} <= set(built.held)
    assert not ({"render:zh", "compare:zh"} & set(built.ran))
    assert keys(*EVERY, codes=("en",)) <= set(built.ran)
    assert built.status == 1


def test_an_interrupt_runs_no_further_node(table, monkeypatch):
    def interrupted(edition):
        raise KeyboardInterrupt

    stage = replace(table.nodes["stage"], run=interrupted)
    held = {**table.nodes, "stage": stage}
    monkeypatch.setattr(runs, "table", lambda: held)
    table = nodes.load(held.values(), stand_ins.SHARED, CODES)
    with pytest.raises(KeyboardInterrupt):
        build.build(table, ["all"])
    # The interrupted node's record says it did not pass; no node after it has one.
    first = next(k for k in table.order if k.startswith("stage:"))
    assert records.read(records.place(*nodes.split(first))).outcome == "error"
    recorded = {key for key in table.order if records.place(*nodes.split(key)).exists()}
    assert recorded <= set(table.order[: table.order.index(first) + 1])


def test_a_build_writes_its_nodes_outputs_and_records_alone(table):
    build.build(table, ["all"])
    written = {
        path.relative_to(repository.ROOT).as_posix()
        for path in repository.ROOT.rglob("*")
        if path.is_file()
    }
    declared = {
        records.below_root(nodes.place(path))
        for node in table.nodes.values()
        for _, edition in node.instances(table.codes)
        for path in [*node.outputs(edition).values(), *node.inputs(edition).values()]
    }
    assert {name for name in written if not name.startswith("build/evidence/records/")} <= declared
