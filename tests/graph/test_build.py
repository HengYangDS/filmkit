"""`filmkit build` on stand-in nodes and files: the closure run in the derived order, each node
judged again at its turn and run only where stale (design decision 3 of
build-a-film-by-its-verbs)."""

import signal
from dataclasses import replace

import pytest
import stand_ins
from stand_ins import CODES

import filmkit.child_processes as child_processes
import filmkit.repository as repository
from filmkit.graph import build, chain, cli, nodes, plan, records, runs
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


def failing(table, monkeypatch, name, fault):
    """The table with a node whose owner raises `fault` for the Chinese edition."""

    def fails(edition):
        if edition.code == "zh":
            raise fault
        stand_ins.wrote(name, edition.code)

    held = {**table.nodes, name: replace(table.nodes[name], run=fails)}
    monkeypatch.setattr(runs, "table", lambda: held)
    loaded = nodes.load(held.values(), stand_ins.SHARED, CODES)
    monkeypatch.setattr(chain, "table", lambda: loaded)
    return loaded


GATED = "check-sound:zh: the soundtrack has 1 gated finding"


def test_a_refused_gate_holds_what_follows_it_and_the_other_edition_is_built(table, monkeypatch):
    fault = AssemblyError(GATED.removeprefix("check-sound:zh: "))
    table = failing(table, monkeypatch, "check-sound", fault)
    built = build.build(table, ["all"])
    assert built.refused == [GATED]
    assert records.read(records.place("check-sound", "zh")).outcome == "refuse"
    # The render waits for the gate, and the page reads its output: neither runs.
    assert {"render:zh", "compare:zh", "package-metadata:zh"} <= set(built.held)
    assert not ({"render:zh", "compare:zh"} & set(built.ran))
    assert keys(*EVERY, codes=("en",)) <= set(built.ran)
    assert built.status == 1


def test_a_refusal_stands_until_what_its_node_reads_changes(table, monkeypatch):
    fault = AssemblyError(GATED.removeprefix("check-sound:zh: "))
    table = failing(table, monkeypatch, "check-sound", fault)
    build.build(table, ["all"])
    (gate,) = [e for e in plan.plan(table, ["render:zh"]).entries if e.key == "check-sound:zh"]
    assert (gate.state, gate.refused) == ("stale", GATED)
    # Run again it would refuse the same: the build runs nothing and gives the gate's line.
    again = build.build(table, ["render:zh"])
    assert (again.ran, again.status) == ([], 1)
    assert again.refused == [
        f"{GATED} (its last run's refusal; nothing it reads has changed, so it was not run)"
    ]
    assert "render:zh" in again.held
    # Once what it reads changes, it runs again.
    (repository.ROOT / "zh/script.txt").write_text("the zh script, edited")
    edited = build.build(table, ["render:zh"])
    assert "check-sound:zh" in edited.ran and edited.refused == [GATED]


@pytest.mark.parametrize(
    ("fault", "said", "traced"),
    [
        (RuntimeError("the disk is gone"), "stage:zh: RuntimeError: the disk is gone", True),
        (child_processes.MissingToolError("No node on PATH"), "stage:zh: No node on PATH", False),
        (
            FileNotFoundError(2, "No such file or directory", "ffmpeg"),
            "stage:zh: No ffmpeg on the path; install it as Homebrew does: brew install ffmpeg",
            False,
        ),
    ],
)
def test_a_node_that_cannot_finish_fails_and_the_build_exits_2(
    table, monkeypatch, capsys, fault, said, traced
):
    failing(table, monkeypatch, "stage", fault)
    with pytest.raises(SystemExit) as ended:
        cli.main(["build", "all"])
    assert ended.value.code == child_processes.UNFINISHED
    # The failure is no refusal: its record says `error`, what follows it is held, and the other
    # edition is built.
    assert records.read(records.place("stage", "zh")).outcome == "error"
    assert not records.place("render", "zh").exists()
    assert records.read(records.place("render", "en")).outcome == "pass"
    err = capsys.readouterr().err
    assert err.endswith(f"{said}\n") and ("Traceback" in err) is traced


def test_a_request_to_end_a_node_ends_the_build_with_its_status(table, monkeypatch, capsys):
    failing(table, monkeypatch, "stage", child_processes.Terminated(signal.SIGTERM))
    with pytest.raises(SystemExit) as ended:
        cli.main(["build", "all"])
    assert ended.value.code == 143
    assert "stopped by a request to end (SIGTERM)" in capsys.readouterr().err


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
