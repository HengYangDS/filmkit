"""The plan on stand-in nodes and files: each node's state, reasons, class and readiness, judged
from its run records as decisions 5 and 6 of record-every-run say, and nothing written."""

import os

import pytest
from stand_ins import CODES, chain, ran, selecting

import filmkit.repository as repository
from filmkit.graph import nodes, plan


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
