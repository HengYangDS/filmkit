"""The plan on stand-in nodes and files: each node's state, reasons, class and readiness, judged
from its run records as decisions 5 and 6 of record-every-run say, and nothing written."""

import os
from dataclasses import replace

import pytest
import stand_ins
from stand_ins import CODES, chain, ran, selecting

import filmkit.graph.chain as engine_chain
import filmkit.repository as repository
from filmkit.graph import nodes, plan, records, runs, verify


def judged(table, *targets, full=False):
    planned = plan.plan(table, targets, full=full)
    return planned, {entry.key: entry for entry in planned.entries}


def texts(entry):
    return [reason.text for reason in entry.reasons]


def test_a_chain_that_ran_in_order_is_fresh_and_ready_and_nothing_is_hashed(stand_in_table):
    chain()
    planned, found = judged(stand_in_table, "check-sound:zh")
    assert list(found) == ["assemble:zh", "refresh-captions:zh", "check-sound:zh"]
    for entry in found.values():
        assert (entry.state, entry.reasons, entry.ready) == ("fresh", [], True), entry.key
        assert (entry.host_class, entry.expected) == ("light", "light")
        assert entry.seconds is not None
    assert planned.hashed == 0


def test_a_touched_source_is_hashed_once_and_its_readers_stay_fresh(stand_in_table):
    chain()
    script = repository.ROOT / "zh/script.txt"
    later = script.stat().st_mtime_ns + 10**9
    os.utime(script, ns=(later, later))
    planned, found = judged(stand_in_table, "check-sound:zh")
    assert planned.hashed == 1
    assert {entry.state for entry in found.values()} == {"fresh"}


def test_an_edited_source_makes_its_readers_stale_and_the_nodes_after_them_behind(stand_in_table):
    chain()
    (repository.ROOT / "zh/script.txt").write_text("the zh script, edited")
    _, found = judged(stand_in_table, "check-sound:zh")
    assert found["assemble:zh"].state == found["refresh-captions:zh"].state == "stale"
    assert texts(found["assemble:zh"]) == ["input script changed: zh/script.txt"]
    assert [r.kind for r in found["assemble:zh"].reasons] == ["input"]
    assert (found["check-sound:zh"].state, found["check-sound:zh"].ready) == ("behind", False)


def test_a_node_after_a_failed_node_is_behind_and_not_ready(stand_in_table):
    chain()
    ran("package-metadata")
    with pytest.raises(SystemExit):
        ran("check-sound", refuse="check-sound: the gate refused")
    _, found = judged(stand_in_table, "package-metadata:zh")
    assert texts(found["check-sound:zh"]) == ["its run ended with the outcome refuse"]
    assert (found["package-metadata:zh"].state, found["package-metadata:zh"].ready) == (
        "behind",
        False,
    )


def test_a_node_after_a_partial_run_is_stale_as_changed_by_a_partial_run(stand_in_table):
    ran("stage")
    (repository.ROOT / "zh/script.txt").write_text("the zh script, a part")
    ran("stage", whole=False)
    (repository.ROOT / "zh/script.txt").write_text("the zh script")
    _, found = judged(stand_in_table, "stage:zh")
    assert texts(found["stage:zh"]) == ["changed by a partial run"]


def test_a_partial_run_that_left_the_node_s_outputs_as_recorded_leaves_it_fresh(stand_in_table):
    # A stage written elsewhere, or made again from the same sources, changes none of the node's
    # outputs: its partial record states them with the digests its record states.
    ran("stage")
    ran("stage", whole=False)
    _, found = judged(stand_in_table, "stage:zh")
    assert (found["stage:zh"].state, texts(found["stage:zh"])) == ("fresh", [])


def test_two_replacing_writers_of_a_page_are_fresh_until_a_hand_edit(stand_in_table):
    chain(*CODES)
    ran("package-metadata", "zh")
    ran("package-metadata", "en")
    _, found = judged(stand_in_table, "package-metadata:all")
    assert found["package-metadata:zh"].state == found["package-metadata:en"].state == "fresh"
    (repository.ROOT / "page.html").write_text("edited by hand")
    _, found = judged(stand_in_table, "package-metadata:all")
    for code in CODES:
        entry = found[nodes.key("package-metadata", code)]
        assert texts(entry) == ["page.html changed by no declared writer"]
        assert [r.kind for r in entry.reasons] == ["unaccounted"]


def test_assemble_run_again_after_refresh_captions_leaves_it_stale_and_check_sound_behind(
    stand_in_table,
):
    chain()
    before = (repository.ROOT / "zh/timeline.json").read_bytes()
    ran("assemble")
    assert (repository.ROOT / "zh/timeline.json").read_bytes() == before
    _, found = judged(stand_in_table, "check-sound:zh")
    assert found["assemble:zh"].state == "fresh"
    assert texts(found["refresh-captions:zh"]) == [
        "its output timeline replaced by an earlier writer's run (assemble:zh)"
    ]
    assert (found["check-sound:zh"].state, found["check-sound:zh"].ready) == ("behind", False)


def test_a_hand_edit_that_a_rewriter_carried_forward_is_changed_by_no_declared_writer(
    stand_in_table,
):
    ran("assemble")
    (repository.ROOT / "zh/timeline.json").write_text("HAND-EDITED timeline")
    ran("refresh-captions")
    ran("check-sound")
    _, found = judged(stand_in_table, "check-sound:zh")
    for key in ("assemble:zh", "refresh-captions:zh"):
        assert [(r.kind, r.text) for r in found[key].reasons] == [
            (
                "unaccounted",
                "zh/timeline.json changed by no declared writer before the run of "
                "refresh-captions:zh",
            )
        ], key
    assert found["check-sound:zh"].state == "behind"


def test_a_reader_binding_holds_only_through_a_rewriter_whose_own_binding_holds(
    stand_in_table, monkeypatch
):
    table = selecting(monkeypatch)
    for name in ("select", "assemble", "refresh-captions"):
        ran(name)
    _, found = judged(table, "refresh-captions:zh")
    assert {entry.state for entry in found.values()} == {"fresh"}
    # The selection is made again from another script: the reader's binding of the old selection
    # holds no longer, though the rewriter read the bytes the reader read.
    (repository.ROOT / "zh/script.txt").write_text("the zh script, selected again")
    ran("select")
    _, found = judged(table, "refresh-captions:zh")
    assert texts(found["assemble:zh"]) == ["input selected changed: zh/selected.txt"]
    assert texts(found["refresh-captions:zh"]) == [
        "its output selected replaced by an earlier writer's run (select:zh)"
    ]


def test_a_node_is_ready_only_when_every_node_upstream_passed_and_its_inputs_exist(stand_in_table):
    _, found = judged(stand_in_table, "check-sound:zh")
    assert found["assemble:zh"].ready
    assert not found["refresh-captions:zh"].ready
    chain()
    (repository.ROOT / "zh/script.txt").unlink()
    _, found = judged(stand_in_table, "check-sound:zh")
    assert not found["assemble:zh"].ready
    assert texts(found["assemble:zh"]) == ["input script missing: zh/script.txt"]


def test_a_node_without_a_record_is_unmeasured_with_its_expected_class(stand_in_table):
    _, found = judged(stand_in_table, "render:zh")
    render = found["render:zh"]
    assert (render.state, texts(render)) == ("stale", ["no record"])
    assert (render.host_class, render.expected, render.seconds) == ("unmeasured", "heavy", None)


def test_the_plan_writes_nothing(stand_in_table):
    chain(*CODES)
    ran("package-metadata", "zh")
    (repository.ROOT / "zh/script.txt").write_text("edited")

    def listing():
        found = sorted(repository.ROOT.rglob("*"))
        return [(path, path.stat().st_size, path.stat().st_mtime_ns) for path in found]

    before = listing()
    judged(stand_in_table)
    judged(stand_in_table, full=True)
    assert listing() == before


def test_a_node_of_one_edition_is_asked_of_that_edition_alone(stand_in_table, monkeypatch):
    # A node that the film runs once a build, for its first declared edition, as the renderer's
    # qualification: neither the plan nor verify asks for it in the other edition.
    qualify = replace(
        stand_ins.stand_in("qualify", {"stage": "{code}/stage.txt"}, {"q": "{code}/q.json"}),
        editions=lambda codes: codes[:1],
    )
    table = nodes.load((*stand_ins.TABLE, qualify), stand_ins.SHARED, CODES)
    monkeypatch.setattr(runs, "table", lambda: {n.name: n for n in (*stand_ins.TABLE, qualify)})
    assert nodes.key("qualify", "en") not in table.edges
    for code in CODES:
        ran("stage", code)
    with runs.run("zh", "qualify"):
        (repository.ROOT / "zh/q.json").write_text("qualified")
    # A run of it for another edition is measured and writes no run record.
    with runs.run("en", "qualify"):
        pass
    assert not records.place("qualify", "en").exists()
    _, found = judged(table, "qualify:all", "stage:all")
    assert list(found) == ["stage:zh", "stage:en", "qualify:zh"]
    assert {entry.state for entry in found.values()} == {"fresh"}
    lines = verify.verify(table).refusals
    assert not any("qualify:en" in line for line in lines), lines


def test_a_rewriter_run_twice_keeps_its_earlier_writers_fresh(stand_in_table, monkeypatch):
    write = stand_ins.WRITES["refresh-captions"]
    monkeypatch.setitem(
        stand_ins.WRITES,
        "refresh-captions",
        lambda root, code: {**write(root, code), "timeline": write(root, code)["timeline"] + "+"},
    )
    chain()
    ran("refresh-captions")
    _, found = judged(stand_in_table, "check-sound:zh")
    assert found["assemble:zh"].state == found["refresh-captions:zh"].state == "fresh"
    assert texts(found["check-sound:zh"]) == ["input timeline changed: zh/timeline.json"]


def test_a_film_wide_node_is_planned_and_asked_for_by_its_name(stand_in_table, monkeypatch):
    root = repository.ROOT
    check = nodes.Node(
        "check",
        {"default": lambda e: {"scripts": root / "zh/script.txt"}},
        lambda e: {"verdict": root / "verdict.json"},
        "light",
        per=nodes.FILM,
    )
    narrate = stand_ins.stand_in(
        "narrate",
        {"script": "{code}/script.txt", "verdict": "verdict.json"},
        {"takes": "{code}/takes.txt"},
        "gpu",
    )
    held = (*(n for n in stand_ins.TABLE if n.name != "narrate"), narrate, check)
    table = nodes.load(held, stand_ins.SHARED, CODES)
    monkeypatch.setattr(runs, "table", lambda: {n.name: n for n in held})
    with runs.run(None, "check"):
        (root / "verdict.json").write_text("pass")
    assert records.place("check", None) == root / "build/evidence/records/film/check.json"
    planned, found = judged(table, "check")
    assert [entry.stated()["node"] for entry in planned.entries] == ["check"]
    assert (found["check"].state, found["check"].ready) == ("fresh", True)
    # Each edition's narration reads the verdict, so the film's check is upstream of it.
    _, found = judged(table, "narrate:all")
    assert list(found) == ["check", "narrate:zh", "narrate:en"]
    with pytest.raises(ValueError, match="check:zh names no node or group of the plan"):
        judged(table, "check:zh")


@pytest.fixture
def judging(monkeypatch):
    """The engine's table over the sample, each node judged by a stand-in record: fresh, or stale
    where the test names it; every input standing. The table and the stale keys to fill."""
    stale: set[str] = set()

    def judged(s, settled, key, running, full):
        return [plan.Reason("record", "a stand-in record")] if key in stale else []

    monkeypatch.setattr(plan, "judged", judged)
    monkeypatch.setattr(plan, "exists", lambda path: True)
    return engine_chain.table(), stale


def entries(table, *targets):
    return {entry.key: entry for entry in plan.plan(table, targets).entries}


GATES = (
    "check-sound:zh",
    "player-check-cover:zh",
    "check-picture:en",
    "geometry-check:en",
    "render-draft:en",
    "check",
)


@pytest.mark.parametrize("gate", GATES)
def test_a_render_waits_while_a_gate_it_waits_for_did_not_pass(judging, gate):
    table, stale = judging
    stale.add(gate)
    render = entries(table, "render-picture:zh")["render-picture:zh"]
    assert (render.state, render.ready) == ("waiting", False)
    assert render.held[gate] == "stale"
    assert {"node": gate, "state": "stale"} in render.stated()["waits"]


def test_a_package_waits_while_its_sound_gate_did_not_pass(judging):
    table, stale = judging
    stale.add("check-sound:zh")
    found = entries(table, "package-film:zh")
    assert (found["package-film:zh"].state, found["package-film:zh"].ready) == ("waiting", False)


def test_a_stale_source_check_leaves_every_other_node_waiting_or_fresh(judging):
    table, stale = judging
    stale.add("check")
    found = entries(table)
    assert found["check"].state == "stale"
    others = {entry.state for key, entry in found.items() if key != "check"}
    assert others <= {"waiting", "fresh"} and "waiting" in others
    assert found["narrate:zh"].state == "waiting"


def test_an_english_retake_leaves_the_chinese_pictures_waiting_not_behind(judging):
    table, stale = judging
    stale.add("narrate:en")
    found = entries(table)
    assert found["check-picture:en"].state == "behind"
    pictured = ("render-picture", "render-picture-uncaptioned", "validate-picture")
    pictured += ("validate-picture-uncaptioned", "qualify-renderer", "compare-pictures")
    for key in (f"{name}:zh" for name in pictured):
        assert found[key].state == "waiting", key
        assert found[key].held["check-picture:en"] == "behind"
    # The Chinese package metadata, films and scan read every edition's timeline by a path (the
    # entry page and the viewing package list both editions), so they are behind the English
    # sound and will run: a dependency decision 5 accepts, not a wait.
    package = ("package-metadata:zh", "package-film:zh", "scan-film:zh")
    behind = {
        key for key, entry in found.items() if key.endswith(":zh") and entry.state == "behind"
    }
    assert behind == set(package)


def test_a_render_is_fresh_once_its_gates_ran_again_and_passed(judging):
    table, stale = judging
    stale |= {"check", "check-sound:zh"}
    assert entries(table, "render-picture:zh")["render-picture:zh"].state == "waiting"
    # Run again and passed with changed records, which no render binds: the render is fresh.
    stale.clear()
    render = entries(table, "render-picture:zh")["render-picture:zh"]
    assert (render.state, render.ready, render.held) == ("fresh", True, {})


def test_a_film_without_drafts_loads_with_no_wait_on_a_draft(monkeypatch):
    picture = engine_chain.FILM.picture.model_copy(update={"drafts": False})
    declared = engine_chain.FILM.model_copy(update={"picture": picture})
    monkeypatch.setattr(engine_chain, "FILM", declared)
    table = engine_chain.table()
    assert not any(key.startswith("render-draft") for key in table.edges)
    assert not any(
        gate.startswith("render-draft") for held in table.waits.values() for gate in held
    )


def test_every_input_the_pre_render_check_read_holds_each_render_and_package():
    # What R2a's node `preflight` read (build/evidence/build-a-film-by-its-verbs/research.md,
    # item 2): each edition's stages, sound gate and cover check, every edition's picture gate,
    # geometry check and draft, and the film's source check.
    table = engine_chain.table()
    for code in table.codes:
        own = {f"{n}:{code}" for n in ("stage-picture", "check-sound", "player-check-cover")}
        every = {
            f"{n}:{c}"
            for n in ("check-picture", "geometry-check", "render-draft")
            for c in table.codes
        }
        for render in ("render-picture", "render-picture-uncaptioned", "package-film"):
            assert own | every | {"check"} <= table.closure(f"{render}:{code}"), (render, code)
        assert f"stage-picture-uncaptioned:{code}" in table.closure(f"package-film:{code}")


def test_a_hearing_reruns_the_picture_gate_and_the_renders_until_outputs_are_keyed(judging):
    # Until key-outputs-by-their-inputs retires it, the picture gate's own record binds the
    # declaration whole (`picture/gates.py`, `bound_inputs`), so the node `check-picture` binds
    # it too and a hearing recorded in the declaration makes it stale (design decision 4).
    table, stale = judging
    read = set()
    for key in table.edges:
        node, edition = table.node(key)
        if set(node.inputs(edition)) & {"declaration", "declaration.narration"}:
            read.add(key)
    assert {"check", "check-sound:zh", "check-picture:zh", "check-picture:en"} <= read
    pictured = ("render-", "validate-", "qualify-", "compare-", "package-", "scan-")
    assert not [key for key in read if key.startswith(pictured)]
    stale |= read
    found = entries(table)
    # Each render is after its edition's picture gate by a path: behind it, so it will run.
    for code in table.codes:
        for name in ("render-picture", "render-picture-uncaptioned"):
            assert found[f"{name}:{code}"].state == "behind", (name, code)


def test_an_edit_the_renders_do_not_bind_holds_them_until_the_picture_gate_has_judged_it(judging):
    # The review of `68e0cc6..b1467a2`, finding 5: an edit of the release's sources, a table no
    # node binds, makes stale only the nodes that bind the declaration whole, the picture gate
    # among them. Each render reads the declaration aside, to hold the gate's record to it, and
    # binds no part of it, yet is held while the gate has not judged the edit: before the gate
    # runs again it is not fresh and not ready, and after it, its input, the gate's record, has
    # changed.
    table, stale = judging
    whole = set()
    for key in table.edges:
        node, edition = table.node(key)
        if "declaration" in node.inputs(edition):
            whole.add(key)
    assert {"check", "check-sound:zh", "check-picture:zh", "check-picture:en"} <= whole
    stale |= whole
    found = entries(table)
    for code in table.codes:
        for name in ("render-picture", "render-picture-uncaptioned"):
            node, edition = table.node(f"{name}:{code}")
            assert "declaration" not in node.inputs(edition), name
            assert engine_chain.aside(name, edition)["declaration"] == node_declaration()
            # The gate's record, or for a derived picture the captioned one, rendered after it.
            assert {"picture_gates", "captioned_picture"} & set(node.inputs(edition)), name
            render = found[f"{name}:{code}"]
            assert (render.state != "fresh", render.ready) == (True, False), (name, code)


def node_declaration():
    """The film's declaration as a node's places name it."""
    return repository.ROOT / repository.DECLARATION


def test_a_group_s_target_lists_its_nodes_and_every_node_upstream_by_path_and_wait(judging):
    table, _ = judging
    listed = set(entries(table, "picture:zh"))
    picture = {
        f"{name}:zh"
        for name in engine_chain.GROUPS["picture"]
        if f"{name}:zh" in table.edges  # the qualification where the film qualifies Chinese
    }
    assert picture <= listed
    assert {"render-picture:zh", "compare-pictures:zh"} <= picture
    # Upstream by a path (the stage, the sound, the narration) and by a wait (every edition's
    # picture gate, the film's source check).
    assert {"stage-picture:zh", "assemble:zh", "narrate:zh"} <= listed
    assert {"check-picture:en", "geometry-check:en", "check-sound:zh", "check"} <= listed
    assert listed == set().union(picture, *(table.closure(key) for key in picture))
    # `<group>:all` names the group's nodes of every edition.
    assert {"render-picture:zh", "render-picture:en"} <= set(entries(table, "picture:all"))


def test_all_lists_every_node_but_the_narration(judging):
    table, _ = judging
    listed = set(entries(table, "all"))
    assert listed == {key for key in table.edges if not key.startswith("narrate:")}
    assert "check" in listed and "package-film:en" in listed


def test_an_unknown_group_is_refused_in_one_line_naming_the_groups_and_nodes(judging):
    table, _ = judging
    with pytest.raises(ValueError) as refused:
        plan.plan(table, ["pictures:zh"])
    line = str(refused.value)
    assert "\n" not in line and line.startswith("pictures:zh names no node or group of the plan;")
    assert "its groups are sound, audit, picture, package" in line
    assert "check-sound" in line and "package-film" in line
