"""`filmkit build`'s scheduling under the host's rules 2, 3 and 7 (design decision 5 of
build-a-film-by-its-verbs): narration is no build's, light work that can run now runs first,
and heavy work of several kinds shares a ticket only when measured within 30 minutes."""

from dataclasses import replace

import pytest
import stand_ins
from stand_ins import CODES

import filmkit.graph.chain as engine_chain
import filmkit.repository as repository
from filmkit.graph import build, nodes, plan, records, runs


def entry(key, state="stale", expected="light", measured=None, seconds=None, standing=None):
    """A node as the plan judged it: unmeasured unless `measured` names its class."""
    found = plan.Entry(key, state, [], measured or plan.UNMEASURED, expected, seconds, True)
    return replace(found, standing=standing)


@pytest.fixture
def table(stand_in_table, monkeypatch):
    """The stand-in table, its render heavy and its narration GPU work without a run, and each
    other node's owner as its run."""
    held = tuple(
        replace(node, run=None if node.name == "narrate" else stand_in_owner(node.name))
        for node in stand_ins.TABLE
    )
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in held})
    return nodes.load(held, stand_ins.SHARED, CODES)


def stand_in_owner(name):
    return lambda edition: stand_ins.wrote(name, edition.code)


def test_a_stale_narration_is_refused_naming_the_narration_verb(table):
    found = build.refusals(table, [entry("narrate:zh", expected="gpu")])
    assert found == [
        "narrate:zh is stale and narration is no build's: filmkit narrate --edition zh"
    ]


def test_light_work_that_can_run_now_is_named_before_heavy_work(table):
    found = build.refusals(
        table,
        [
            entry("stage:en"),
            entry("render:en", "behind", "heavy"),
            entry("compare:en", "behind"),
            entry("assemble:zh"),
        ],
    )
    # The comparison comes after the render: it runs inside the heavy work's invocation.
    assert found == [
        "light work can run now and runs first, outside any ticket: "
        "filmkit build stage:en assemble:zh"
    ]


def test_a_light_build_runs_the_named_nodes_and_then_the_heavy_work_runs_in_one_invocation(
    table,
):
    refused = build.build(table, ["all"])
    assert refused.ran == [] and refused.status == 1
    (line,) = refused.refused
    named = line.removeprefix(
        "light work can run now and runs first, outside any ticket: filmkit build "
    ).split()
    assert {"assemble:zh", "check-sound:en", "stage:zh", "package-metadata:en"} <= set(named)
    light = build.build(table, named)
    assert set(light.ran) == set(named) and light.status == 0
    heavy = build.build(table, ["all"])
    assert {"render:zh", "render:en", "compare:zh"} <= set(heavy.ran) and heavy.status == 0
    assert records.read(records.place("stage", "zh")).host_class == "light"


def test_unmeasured_heavy_work_of_two_kinds_is_printed_as_two_invocations(table):
    found = build.refusals(
        table,
        [entry("render:zh", expected="heavy"), entry("compare:zh", "behind", "heavy")],
    )
    assert found == [
        "heavy work of 2 kinds that will run takes one ticket each, in this order: "
        "filmkit build render:zh (heavy, unmeasured); filmkit build compare:zh (heavy, unmeasured)"
    ]


@pytest.mark.parametrize(("seconds", "one"), [(899, True), (901, False)])
def test_measured_heavy_work_shares_a_ticket_within_thirty_minutes(table, seconds, one):
    found = build.refusals(
        table,
        [
            entry("render:zh", expected="heavy", measured="heavy", seconds=900),
            entry("compare:zh", "behind", "light", measured="heavy", seconds=seconds),
        ],
    )
    assert (found == []) is one
    if not one:
        assert found[0].endswith(
            "filmkit build render:zh (heavy, 900.0 s); filmkit build compare:zh (heavy, 901.0 s)"
        )


def test_a_waiting_node_is_not_counted_as_heavy_work_that_will_run(table):
    found = build.refusals(
        table,
        [entry("render:zh", "waiting", "heavy"), entry("compare:zh", "stale", "heavy")],
    )
    assert found == []


def test_a_refusal_that_stands_and_what_follows_it_are_no_work_that_will_run(table):
    # The gate refused with nothing it reads changed, and the page reads its output: neither is
    # light work to run first, so the render alone is the heavy work, in one invocation.
    entries = [
        entry("check-sound:zh", standing="check-sound:zh: 1 gated finding"),
        entry("package-metadata:zh", "behind"),
        entry("render:zh", expected="heavy"),
    ]
    assert [e.key for e in build.standing(entries)] == ["check-sound:zh"]
    assert [e.key for e in build.will_run(table, entries)] == ["render:zh"]
    assert build.refusals(table, entries) == []


def test_a_gate_behind_a_node_that_will_run_is_scheduled_as_if_it_had_not_refused(
    table, monkeypatch
):
    # The review of `68e0cc6..b1467a2`, finding 1: the sound gate refused, and the render waits for
    # it. The Chinese script is then edited, so the assembly upstream of the gate will run first
    # and change what the gate reads: the gate's refusal cannot stand, since the build would run it
    # at its turn and, were it to pass, the render behind it in the same invocation. The stage
    # reads a source of its own here, so that the render is held by the gate alone.
    def refuse(edition):
        if edition.code == "zh":
            raise build.REFUSALS[0]("the soundtrack has 1 gated finding")
        stand_ins.wrote("check-sound", edition.code)

    staging = stand_ins.stand_in(
        "stage", {"source": "{code}/source.txt"}, {"stage": "{code}/stage.txt"}
    )
    held = {
        **table.nodes,
        "check-sound": replace(table.nodes["check-sound"], run=refuse, judges="its inputs alone"),
        "stage": replace(staging, run=stand_in_owner("stage")),
        "render": replace(table.nodes["render"], waits=(nodes.Wait("check-sound"),)),
    }
    monkeypatch.setattr(runs, "table", lambda: held)
    table = nodes.load(held.values(), stand_ins.SHARED, CODES)
    for code in CODES:
        (repository.ROOT / code / "source.txt").write_text(f"the {code} picture's source")
    (line,) = build.build(table, ["all"]).refused
    light = line.removeprefix("light work can run now and runs first, outside any ticket: ")
    lit = build.build(table, light.removeprefix("filmkit build ").split())
    assert lit.refused == ["check-sound:zh: the soundtrack has 1 gated finding"]
    # The English render runs; the Chinese one is held by the gate, which stands.
    assert "render:en" in build.build(table, ["all"]).ran
    (gate,) = [e for e in plan.plan(table, ["render:zh"]).entries if e.key == "check-sound:zh"]
    assert gate.standing is not None
    (repository.ROOT / "zh/script.txt").write_text("the zh script, edited")
    judged = plan.plan(table, ["all"]).entries
    (gate,) = [e for e in judged if e.key == "check-sound:zh"]
    assert (gate.state, gate.standing) == ("stale", None)
    assert {"check-sound:zh", "render:zh"} <= {e.key for e in build.will_run(table, judged)}
    (line,) = build.refusals(table, judged)
    named = line.removeprefix("light work can run now and runs first, outside any ticket: ")
    assert {"assemble:zh", "refresh-captions:zh", "check-sound:zh"} <= set(named.split()[2:])


def judging(monkeypatch, stale: set[str]) -> nodes.Table:
    """The engine's table over the sample, each node judged by a stand-in record: stale where
    `stale` names it, fresh otherwise; every input standing."""
    reason = [plan.Reason("record", "a stand-in record")]
    monkeypatch.setattr(
        plan, "judged", lambda s, settled, key, running, full: reason if key in stale else []
    )
    monkeypatch.setattr(plan, "exists", lambda path: True)
    return engine_chain.table()


def test_the_sample_after_its_narration_names_its_light_work_before_its_heavy_work(monkeypatch):
    # After `filmkit narrate`, every node but the narration and the source check has no record.
    table = engine_chain.table()
    unbuilt = {k for k in table.edges if k != "check" and not k.startswith("narrate:")}
    table = judging(monkeypatch, unbuilt)
    found = build.refusals(table, plan.judge_all(table, plan.wanted(table, ["all"]), False))
    (line,) = found
    named = set(line.split("filmkit build ")[1].split())
    sound = {f"{name}:{code}" for name in engine_chain.GROUPS["sound"] for code in CODES}
    assert sound <= named
    assert {"stage-picture:zh", "player-check-cover:en", "package-metadata:zh"} <= named
    assert not {"check-picture:zh", "render-picture:zh", "validate-picture:zh"} & named


def test_an_english_retake_asks_no_chinese_render_and_names_the_chinese_package(monkeypatch):
    # After the English narration ran again, its sound is stale; once the light work it names
    # has run, the heavy work that will run is the English picture's and both packages, the
    # Chinese package reading the English timeline (design decision 5, as its owner amended it).
    table = judging(monkeypatch, {"select:en"})
    judged = plan.judge_all(table, plan.wanted(table, ["all"]), False)
    done = [
        replace(e, state="fresh") if e.state != "fresh" and not build.heavy(e) else e
        for e in judged
    ]
    (line,) = build.refusals(table, done)
    invocations = {
        frozenset(part.split(" (")[0].removeprefix("filmkit build ").split())
        for part in line.split(": ", 1)[1].split("; ")
    }
    assert {"package-film:zh", "package-film:en"} in invocations
    assert {"scan-film:zh", "scan-film:en"} in invocations
    chinese = ("render-picture", "render-picture-uncaptioned", "check-picture", "qualify-renderer")
    assert not any(f"{name}:zh" in line for name in chinese)
