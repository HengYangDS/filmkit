"""`filmkit verify` on stand-in nodes and files: a refusal for bytes no declared writer accounts
for, for a change that kept a file's size and time, and for every node that is not fresh and
passed, and nothing written (design decision 6 of record-every-run, 11 of
build-a-film-by-its-verbs)."""

import json
import os
import shutil
from dataclasses import replace

import pytest
import sample_sound
import stand_ins
from stand_ins import CODES, chain, ran, read, wrote

import filmkit.graph.nodes as nodes
import filmkit.repository as repository
from filmkit.graph import plan, runs, verify
from filmkit.production import Edition


def verified(table, capsys):
    """The command's exit status and its lines."""
    status = verify.run(table)
    return status, capsys.readouterr().out.splitlines()


def whole():
    """Run every stand-in node of both editions, in an order the table allows."""
    chain(*CODES)
    for code in CODES:
        for name in ("package-metadata", "stage", "render", "compare", "narrate"):
            ran(name, code)


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
    whole()
    # A repair renders the picture again and compares again, each as its node.
    with runs.run("zh", "repair"):
        with runs.node("zh", "render"):
            (repository.ROOT / "zh/picture").write_text("the repaired picture")
        with runs.node("zh", "compare"):
            wrote("compare", "zh")
    # A retake narrates part of the edition again, changing its takes.
    with runs.run("zh", "narrate", whole=False):
        (repository.ROOT / "zh/takes.txt").write_text("a retaken thought")
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    # The retake leaves the narration stale, which a whole build may not be; no byte is refused.
    assert [line for line in lines if line.startswith("refused: ")] == [
        "refused: narrate:zh: stale: changed by a partial run"
    ]


def test_an_earlier_writer_run_again_and_an_edited_script_are_refused(stand_in_table, capsys):
    whole()
    ran("assemble")
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert (
        "refused: refresh-captions:zh: stale: its output timeline replaced by an earlier "
        "writer's run (assemble:zh)"
    ) in lines
    assert "refused: check-sound:zh: behind" in lines
    (repository.ROOT / "zh/script.txt").write_text("the zh script, edited")
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert "refused: assemble:zh: stale: input script changed: zh/script.txt" in lines


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


def test_a_build_without_records_is_refused_and_verify_writes_nothing(stand_in_table, capsys):
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert lines[0].startswith("refused: no record: assemble:zh, ")
    chain()
    before = listing()
    verified(stand_in_table, capsys)
    assert listing() == before


def test_a_whole_build_passes_and_writes_nothing(stand_in_table, capsys):
    whole()
    before = listing()
    status, lines = verified(stand_in_table, capsys)
    assert (status, len(lines)) == (0, 1)
    assert lines[0].startswith("filmkit verify passes")
    assert listing() == before


def test_a_refused_run_and_a_waiting_render_are_refused_naming_the_node(
    stand_in_table, capsys, monkeypatch
):
    held = [
        replace(node, waits=(nodes.Wait("check-sound"),)) if node.name == "render" else node
        for node in stand_ins.TABLE
    ]
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in held})
    table = nodes.load(held, stand_ins.SHARED, CODES)
    whole()
    with pytest.raises(SystemExit):
        ran("check-sound", refuse="check-sound: a gated finding")
    status, lines = verified(table, capsys)
    assert status == 1
    refused = "refused: check-sound:zh: stale: its run ended with the outcome refuse"
    assert any(line.startswith(refused) for line in lines), lines
    assert "refused: render:zh: waiting for check-sound:zh (stale)" in lines


def refreshing(monkeypatch):
    """Let the stand-in refresh-captions change the timeline at each run, as a refresh after a
    caption edit does."""
    write = stand_ins.WRITES["refresh-captions"]

    def changed(root, code):
        return {**write(root, code), "timeline": read(root, f"{code}/timeline.json") + " +"}

    monkeypatch.setitem(stand_ins.WRITES, "refresh-captions", changed)


def test_a_rewriter_run_again_on_its_own_output_passes(stand_in_table, capsys, monkeypatch):
    refreshing(monkeypatch)
    whole()
    ran("refresh-captions")
    ran("check-sound")
    ran("package-metadata")
    status, lines = verified(stand_in_table, capsys)
    assert status == 0, lines


def test_a_hand_edit_between_two_runs_of_a_rewriter_is_refused(stand_in_table, capsys, monkeypatch):
    refreshing(monkeypatch)
    chain()
    (repository.ROOT / "zh/timeline.json").write_text("HAND-EDITED timeline")
    ran("refresh-captions")
    status, lines = verified(stand_in_table, capsys)
    assert status == 1
    assert any(line.startswith("refused: zh/timeline.json: its bytes") for line in lines), lines


@pytest.mark.ffmpeg
def test_two_caption_edits_each_refreshed_verify_on_the_sample(built, tmp_path, monkeypatch):
    # The reviewer's case on the real engine: a copy of the built sample, its Chinese script
    # edited twice for presentation only, refresh-captions and check-sound run after each.
    root = (tmp_path / "film").resolve()
    shutil.copytree(built[0], root, symlinks=True)
    monkeypatch.setattr(repository, "ROOT", root)
    script = root / Edition("zh").script
    for tail in (0.2, 0.15):
        value = json.loads(script.read_text())
        value["caption_timing"]["tail_seconds"] = tail
        script.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        for command in ("refresh-captions", "check-sound"):
            sample_sound.run(root, command, "zh")
    # The light suite builds part of the sample: no byte is refused, though nodes it did not
    # build are.
    refused = [r for r in verify.verify().refusals if "its bytes" in r or "keeping its size" in r]
    assert refused == []
