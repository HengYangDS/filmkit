"""`filmkit verify` on stand-in nodes and files: a refusal only for bytes no declared writer
accounts for and for a change that kept a file's size and time, every other stale node listed,
and nothing written (design decision 6 of record-every-run)."""

import os

import pytest
from stand_ins import CODES, chain, ran, wrote

import filmkit.durations as durations
import filmkit.repository as repository
from filmkit.graph import plan, verify


def verified(table, capsys):
    """The command's exit status and its lines."""
    status = verify.run(table)
    return status, capsys.readouterr().out.splitlines()


def listing():
    found = sorted(repository.ROOT.rglob("*"))
    return [(path, path.stat().st_size, path.stat().st_mtime_ns) for path in found]


def test_a_change_that_kept_size_and_time_is_fresh_to_the_plan_and_refused(stand_in_table, capsys):
    chain()
    timeline = repository.ROOT / "zh/timeline.json"
    held = timeline.stat()
    timeline.write_text(timeline.read_text().upper())
    os.utime(timeline, ns=(held.st_atime_ns, held.st_mtime_ns))
    found = {
        entry.key: entry.state for entry in plan.plan(stand_in_table, ["check-sound:zh"]).entries
    }
    assert set(found.values()) == {"fresh"}
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert (
        "refused: zh/timeline.json: it changed while keeping its size and time; it is bound by "
        "assemble:zh, check-sound:zh, refresh-captions:zh"
    ) in lines
    with pytest.raises(verify.VerifyError, match="zh/timeline.json: it changed while keeping"):
        verify.check(stand_in_table)


def test_rewrites_replacements_repairs_and_retakes_pass(stand_in_table, capsys):
    chain(*CODES)
    ran("package-metadata", "zh")
    ran("package-metadata", "en")
    for name in ("stage", "render", "compare", "narrate"):
        ran(name)
    # A repair renders the picture again and compares again, each as its node.
    with durations.run("zh", "repair"):
        with durations.node("zh", "render"):
            (repository.ROOT / "zh/picture").write_text("the repaired picture")
        with durations.node("zh", "compare"):
            wrote("compare", "zh")
    # A retake narrates part of the edition again.
    (repository.ROOT / "zh/takes.txt").write_text("a retaken thought")
    ran("narrate", whole=False)
    status, lines = verified(stand_in_table, capsys)
    assert status == 0, lines
    assert "narrate:zh: stale: changed by a partial run" in lines
    assert lines[-1].startswith("filmkit verify passes")


def test_an_earlier_writer_run_again_and_an_edited_script_are_listed(stand_in_table, capsys):
    chain()
    ran("assemble")
    status, lines = verified(stand_in_table, capsys)
    assert status == 0
    assert (
        "refresh-captions:zh: stale: its output timeline replaced by an earlier writer's run "
        "(assemble:zh)"
    ) in lines
    assert "check-sound:zh: behind" in lines
    (repository.ROOT / "zh/script.txt").write_text("the zh script, edited")
    status, lines = verified(stand_in_table, capsys)
    assert status == 0
    assert "assemble:zh: stale: input script changed: zh/script.txt" in lines


def test_a_hand_edit_that_a_rewriter_carried_forward_is_refused(stand_in_table, capsys):
    ran("assemble")
    (repository.ROOT / "zh/timeline.json").write_text("HAND-EDITED timeline")
    ran("refresh-captions")
    ran("check-sound")
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert (
        "refused: zh/timeline.json: its bytes are accounted for by no record of a declared "
        "writer; it is bound by assemble:zh, refresh-captions:zh"
    ) in lines


def test_a_hand_edit_of_the_entry_page_is_refused(stand_in_table, capsys):
    chain(*CODES)
    ran("package-metadata", "zh")
    ran("package-metadata", "en")
    (repository.ROOT / "page.html").write_text("edited by hand")
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert (
        "refused: page.html: its bytes are accounted for by no record of a declared writer; it "
        "is bound by package-metadata:en, package-metadata:zh"
    ) in lines


def test_a_build_with_no_record_passes_and_verify_writes_nothing(stand_in_table, capsys):
    status, lines = verified(stand_in_table, capsys)
    assert status == 0
    assert lines[0].startswith("no record: assemble:zh, ")
    chain()
    before = listing()
    verified(stand_in_table, capsys)
    assert listing() == before
