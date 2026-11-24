"""Run records at the seam: each run of a node recorded with its outcome from the same measurement
as its duration record, partial runs as partial records (design decisions 2 and 8)."""

import json
import os
import signal
import subprocess
import sys

import pytest
import sample_sound

import filmkit.durations as durations
import filmkit.narration.fitting as fitting
import filmkit.narration.narrate as narrate
import filmkit.picture.repair as picture_repair
import filmkit.produce as produce
import filmkit.repository as repository
import filmkit.soundtrack.gates as sound_gates
from filmkit.graph import nodes, opens, records, runs
from filmkit.production import Edition

SAMPLE_ROOT = repository.ROOT


def stand_in(name, reads, writes):
    """A node that reads and writes files below the root, each by its name."""
    return nodes.Node(
        name,
        {"default": lambda e: {n: repository.ROOT / f for n, f in reads.items()}},
        lambda e: {n: repository.ROOT / f for n, f in writes.items()},
        "light",
    )


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A film root whose table is one stand-in node that reads in.txt and writes out.txt."""
    found = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", found)
    (found / "in.txt").write_text("in")
    table = {"stand": stand_in("stand", {"in": "in.txt"}, {"out": "out.txt"})}
    table |= {name: node for name, node in runs.table().items() if name != "stand"}
    monkeypatch.setattr(runs, "table", lambda: table)
    monkeypatch.delenv(opens.NODE, raising=False)
    return found


def stand_in_run(root, block=lambda run: None, **options):
    with durations.run("zh", "stand", **options) as run:
        run.settings["count"] = 2
        with run.phase("work"):
            (root / "out.txt").write_text("out")
            # A run that records nothing opens no node's run.
            expected = "stand:zh" if options.get("record", True) else None
            assert os.environ.get(opens.NODE) == expected
        block(run)


def read(node, *, partial=False):
    return records.read(records.place(node, "zh", partial=partial))


def test_a_completed_run_is_recorded_from_the_measurement_of_its_duration_record(root):
    stand_in_run(root)
    record = read("stand")
    assert isinstance(record, records.RunRecord)
    assert (record.outcome, record.refusal) == ("pass", None)
    assert record.inputs["in"].path == "in.txt"
    assert record.outputs["out"].sha256 == records.digest(root / "out.txt")
    duration = repository.read(Edition("zh").evidence / durations.FOLDER / "stand.json")
    stated = record.model_dump(mode="json", by_alias=True)
    for key in records.FROM_DURATION:
        assert stated[key] == duration[key], key
    assert record.host_class == "light"
    assert opens.NODE not in os.environ


def test_a_refused_and_a_failed_run_are_recorded_with_their_outcome_and_line(root):
    def refuse(run):
        raise SystemExit("stand: the input is not ready")

    def fail(run):
        raise RuntimeError("the disk went away")

    with pytest.raises(SystemExit):
        stand_in_run(root, refuse)
    assert (read("stand").outcome, read("stand").refusal) == (
        "refuse",
        "stand: the input is not ready",
    )
    with pytest.raises(RuntimeError):
        stand_in_run(root, fail)
    assert (read("stand").outcome, read("stand").refusal) == (
        "error",
        "RuntimeError: the disk went away",
    )


def test_a_run_that_records_nothing_writes_no_run_record(root):
    stand_in_run(root, record=False)
    assert not records.place("stand", "zh").exists()


def test_a_run_that_a_signal_ends_writes_no_record(root):
    child = """
import sys, time
from pathlib import Path
import filmkit.durations as durations
import filmkit.repository as repository
from filmkit.graph import nodes, runs
# The declaration is the sample's, loaded at import; every file is written below the scratch root.
repository.ROOT = Path(sys.argv[1])
stand = nodes.Node("stand", {"default": lambda e: {}}, lambda e: {}, "light")
runs.table = lambda: {"stand": stand}
with durations.run("zh", "stand"):
    print("ready", flush=True)
    time.sleep(60)
"""
    environment = {**os.environ, repository.ROOT_VARIABLE: str(SAMPLE_ROOT)}
    process = subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", child, str(root)],
        env=environment,
        stdout=subprocess.PIPE,
        text=True,
    )
    with process:
        try:
            assert process.stdout.readline().strip() == "ready"
            process.send_signal(signal.SIGTERM)
            assert process.wait(timeout=30) == -signal.SIGTERM
        finally:
            process.kill()
            process.wait()
    assert not (root / "build").exists()


def test_an_unchanged_input_is_not_hashed_when_the_run_opens(root, monkeypatch):
    stand_in_run(root)
    hashed = []
    digest = records.digest
    monkeypatch.setattr(records, "digest", lambda path: hashed.append(path) or digest(path))
    stand_in_run(root)
    assert root / "in.txt" not in hashed
    (root / "in.txt").write_text("changed")
    stand_in_run(root)
    assert hashed.count(root / "in.txt") == 1
    assert read("stand").inputs["in"].sha256 == digest(root / "in.txt")


def test_a_retake_writes_narrate_s_partial_record_and_leaves_its_record(root, monkeypatch):
    monkeypatch.setattr(narrate.processes, "count", lambda: 1)
    monkeypatch.setattr(narrate, "run_steps", lambda code, ids, scope: None)
    narrate.narrate("zh", "", narrate.Scope.ALL)
    whole = records.place("narrate", "zh").read_bytes()
    assert isinstance(read("narrate"), records.RunRecord)
    assert read("narrate").engine.pins  # the model snapshots, by repository and revision
    narrate.narrate("zh", "24", narrate.Scope.ALL)
    narrate.narrate("zh", "", narrate.Scope.CHECKS)
    assert records.place("narrate", "zh").read_bytes() == whole
    assert isinstance(read("narrate", partial=True), records.PartialRecord)


def test_a_stage_written_elsewhere_writes_a_partial_record(root, monkeypatch):
    staged = []
    monkeypatch.setitem(
        produce.EDITION_ACTIONS, "stage-picture", lambda edition, options: staged.append(options)
    )
    produce.main(["stage-picture", "--language", "zh"])
    whole = records.place("stage-picture", "zh").read_bytes()
    trial = ["--output", "build/runtime/work/trial"]
    produce.main(["stage-picture", "--language", "zh", *trial])
    assert records.place("stage-picture", "zh").read_bytes() == whole
    partial = json.loads(records.place("stage-picture", "zh", partial=True).read_text())
    assert partial["partial"] is True
    assert "inputs" not in partial
    assert len(staged) == 2


@pytest.fixture
def repairable(root, monkeypatch):
    """The Chinese edition's two pictures, their receipts and a refused comparison of them, with
    the repair's owners replaced by stand-ins that write what each writes: a render its picture
    and receipt, the comparison its record, which passes."""
    edition, named = Edition("zh"), iter([{"captioned": ["a"], "uncaptioned": ["a"]}, {}])

    def render(edition, deadline, captions=True, made=b"repaired"):
        picture = edition.rendered(captions)
        picture.file.parent.mkdir(parents=True, exist_ok=True)
        picture.file.write_bytes(made + picture.name.encode())
        repository.write(picture.receipt, {"exit": 0, "timed_out": False, "made": made.decode()})

    def compare(edition):
        repository.write(edition.caption_equivalence, {"verdict": "pass", "findings": []})
        return repository.read(edition.caption_equivalence)

    for captions in (True, False):
        render(edition, 60, captions, b"faulty")
    repository.write(edition.caption_equivalence, {"verdict": "refuse", "findings": ["a"]})
    monkeypatch.setattr(
        picture_repair, "current_record", lambda e: repository.read(e.caption_equivalence)
    )
    monkeypatch.setattr(picture_repair.faults, "repairable", lambda record, code: next(named))
    monkeypatch.setattr(picture_repair, "require_renderable", lambda e, named: None)
    monkeypatch.setattr(picture_repair.rendering, "render_picture", render)
    monkeypatch.setattr(
        picture_repair.derivation, "render_uncaptioned", lambda e, d: render(e, d, False)
    )
    monkeypatch.setattr(picture_repair.equivalence, "compare_pictures", compare)
    return edition


def test_a_repair_writes_the_records_of_the_renders_and_the_comparison_it_runs(repairable):
    edition = repairable
    produce.main(["repair-pictures", "--language", "zh"])
    captioned, uncaptioned = read("render-picture"), read("render-picture-uncaptioned")
    compared = read("compare-pictures")
    for record, captions in ((captioned, True), (uncaptioned, False)):
        assert record.outputs["picture"].sha256 == records.digest(edition.rendered(captions).file)
        assert record.outcome == "pass"
    assert uncaptioned.settings["way"] == "native"
    assert compared.outcome == "pass"
    assert compared.outputs["caption_equivalence"].sha256 == records.digest(
        edition.caption_equivalence
    )
    # The repair's duration record is the only one it writes, which counts its seconds once.
    written = sorted(path.name for path in (edition.evidence / durations.FOLDER).iterdir())
    assert written == ["repair-pictures.json"]
    assert opens.NODE not in os.environ


def test_a_convergence_s_selection_writes_the_record_of_select(root, monkeypatch):
    edition, paths = Edition("zh"), narrate.evidence_paths("zh")
    for name in ("receipt", "alignment"):
        repository.write(paths[name], {"records": []})
    repository.write(edition.script, {"voice_performance": {"assembly_mode": "designed"}})

    def select(asked):
        repository.write(asked.narration_selected, {"records": []})
        repository.write(asked.alignment_selected, {"records": []})

    monkeypatch.setattr(fitting, "select", select)
    monkeypatch.setattr(
        fitting.soundtrack_fit, "asked", lambda e: [({"verdict": "too long"}, "too long")]
    )
    with durations.run("zh", "converge"):
        fitting.read("zh")
    record = read("select")
    assert (record.outcome, record.refusal) == ("pass", None)
    selected = record.outputs["narration_selected"].sha256
    assert selected == records.digest(edition.narration_selected)
    assert not (edition.evidence / durations.FOLDER / "select.json").exists()


def below_root(places):
    """Declared places by name, each as a record states its path."""
    return {name: records.below_root(nodes.place(path)) for name, path in places.items()}


@pytest.mark.ffmpeg
def test_the_sample_s_sound_chain_records_each_node_as_its_table_entry_declares(sound_chain):
    edition, table = Edition("zh"), runs.table()
    found = {name: read(name) for name in sample_sound.SOUND}
    for name, record in found.items():
        assert record.outcome == "pass", name
        assert {n: s.path for n, s in record.inputs.items()} == below_root(
            table[name].inputs(edition)
        )
        assert {n: s.path for n, s in record.outputs.items()} == below_root(
            table[name].outputs(edition)
        )
    # The sound gate's record is bound by its digest; none of its fields stands in a run record.
    gate, checked = repository.read(edition.sound_gates), found["check-sound"]
    assert checked.outputs["sound_gates"].sha256 == records.digest(edition.sound_gates)
    for record in found.values():
        text = record.model_dump_json(by_alias=True)
        assert [key for key in gate if f'"{key}"' in text] == []
    for key, path in sound_gates.bound_inputs(edition).items():
        stated = checked.inputs[key.removesuffix("_sha256")]
        assert (stated.path, stated.sha256) == (records.below_root(path), gate[key])
    # What assemble wrote, and the selected narration it read, hold through refresh-captions'
    # record, which read them as they stood and wrote them again.
    assembled, refreshed = found["assemble"], found["refresh-captions"]
    for name in ("timeline", "assembly"):
        assert refreshed.inputs[name].sha256 == assembled.outputs[name].sha256
        assert refreshed.outputs[name].sha256 == records.digest(
            nodes.place(table["refresh-captions"].outputs(edition)[name])
        )
    selected = found["select"].outputs["narration_selected"].sha256
    assert assembled.inputs["narration_selected"].sha256 == selected
    assert refreshed.inputs["narration_selected"].sha256 == selected


def test_a_failure_of_the_seam_reaches_no_command_and_leaves_the_last_record(
    root, monkeypatch, capsys
):
    stand_in_run(root)
    before = read("stand")
    table = runs.table()

    def damaged(edition):
        raise ValueError("a receipt that cannot be read")

    def inputs(edition):
        return {"in": root / "in.txt"}

    # The opening fails, then the close: the command runs and ends with its own line each time.
    for broken in (
        nodes.Node("stand", {"default": damaged}, damaged, "light"),
        nodes.Node("stand", {"default": inputs}, damaged, "light"),
    ):
        monkeypatch.setattr(runs, "table", lambda broken=broken: {**table, "stand": broken})
        with pytest.raises(SystemExit, match="^stand: the input is not ready$"):
            with durations.run("zh", "stand"):
                (root / "out.txt").write_text("other")
                raise SystemExit("stand: the input is not ready")
        error = capsys.readouterr().err
        assert "the run record of stand:zh was not written: ValueError: a receipt" in error
        assert read("stand") == before
        assert opens.NODE not in os.environ
