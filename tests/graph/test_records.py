"""The run record of schema 1 and the partial record: written, read back and refused."""

import json
import os

import pytest

import filmkit.repository as repository
from filmkit.graph import records


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    return tmp_path


def write(path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def measured():
    return records.Measured(cpu_seconds=0.5, cpu_per_wall=0.25, samples=0, above=0)


def run_record(root) -> records.RunRecord:
    script = write(root / "content/zh/film-script.json", b'{"segments": []}')
    gate = write(root / "build/evidence/editions/zh/sound-gates.json", b'{"verdict": "pass"}')
    stage = root / "build/runtime/work/final-delivery-zh-uhd"
    write(stage / "index.html", b"<html></html>")
    write(stage / "fonts/a.woff2", b"font")
    return records.RunRecord(
        node="check-sound",
        edition="zh",
        engine=records.Engine(version="0.32.0", released_sha256="0" * 64, pins={}),
        inputs={
            "script": records.state(script),
            "stage": records.folder_state(records.Folder(stage, "**/*")),
        },
        outputs={"sound_gates": records.state(gate)},
        outcome="refuse",
        refusal="check-sound: a finding",
        started_at="2026-11-24T01:00:00.000+00:00",
        seconds=1.5,
        load_1m={"start": 3.2, "end": None},
        phases={"measure": 1.25},
        settings={"way": "default"},
        measured=measured(),
        host_class="light",
    )


def test_a_record_and_a_partial_record_are_read_back_equal(root):
    record = run_record(root)
    records.write(record)
    path = records.place("check-sound", "zh")
    assert path == root / "build/evidence/records/editions/zh/check-sound.json"
    assert records.read(path) == record
    stated = json.loads(path.read_text())
    assert stated["schema"] == 1
    assert stated["class"] == "light"
    assert stated["inputs"]["script"]["path"] == "content/zh/film-script.json"
    folder = stated["inputs"]["stage"]
    assert [m["path"] for m in folder["members"]] == ["fonts/a.woff2", "index.html"]
    partial = records.PartialRecord(
        **record.model_dump(exclude={"inputs", "schema_", "partial"}),
    )
    records.write(partial)
    partial_path = records.place("check-sound", "zh", partial=True)
    assert partial_path.name == "check-sound.partial.json"
    assert records.read(partial_path) == partial
    assert "inputs" not in json.loads(partial_path.read_text())


def test_a_folder_digest_follows_its_members_bytes_alone(root):
    stage = root / "stage"
    member = write(stage / "index.html", b"<html></html>")
    write(stage / "film.json", b"{}")
    folder = records.Folder(stage, "*.html")
    first = records.folder_state(folder)
    stat = member.stat()
    os.utime(member, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000_000))
    touched = records.folder_state(folder)
    assert touched.sha256 == first.sha256
    assert touched.members[0].mtime_ns != first.members[0].mtime_ns
    write(stage / "notes.txt", b"not named by the pattern")
    assert records.folder_state(folder).sha256 == first.sha256
    member.write_bytes(b"<html>changed</html>")
    assert records.folder_state(folder).sha256 != first.sha256


def test_a_record_of_another_schema_is_unreadable(root):
    record = run_record(root)
    records.write(record)
    path = records.place("check-sound", "zh")
    stated = json.loads(path.read_text())
    path.write_text(json.dumps({**stated, "schema": 2}))
    with pytest.raises(records.Unreadable, match="schema"):
        records.read(path)
    path.write_text("{not json")
    with pytest.raises(records.Unreadable):
        records.read(path)


@pytest.fixture
def counted(monkeypatch):
    """The core's hasher, counting the files it hashes."""
    hashed = []
    real = records.digest

    def counting(path):
        hashed.append(path)
        return real(path)

    monkeypatch.setattr(records, "digest", counting)
    return hashed


def judged(record, counted, *, full=False, declared=None):
    counted.clear()
    stated = {name: state.path for name, state in record.inputs.items()}
    return records.judge(
        record, declared=stated if declared is None else declared, running=record.engine, full=full
    )


def test_unchanged_files_are_not_hashed_and_a_touch_is_hashed_once(root, counted):
    record = run_record(root).model_copy(update={"outcome": "pass", "refusal": None})
    assert judged(record, counted).reasons == ()
    assert counted == []
    script = root / "content/zh/film-script.json"
    stat = script.stat()
    os.utime(script, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    judgment = judged(record, counted)
    assert judgment.reasons == ()
    assert counted == [script]
    assert [f.result for f in judgment.files if f.name == "script"] == ["touched"]


def test_each_reason_of_a_stale_record_is_named(root, counted):
    record = run_record(root)
    assert judged(record, counted).reasons == ("its run ended with the outcome refuse",)
    record = record.model_copy(update={"outcome": "pass", "refusal": None})
    (root / "content/zh/film-script.json").write_bytes(b'{"segments": [1]}')
    (root / "build/evidence/editions/zh/sound-gates.json").unlink()
    other = record.engine.model_copy(update={"version": "0.33.0"})
    reasons = records.judge(
        record, declared={"script": "content/zh/film-script.json"}, running=other
    ).reasons
    assert reasons == (
        "another engine: recorded 0.32.0, running 0.33.0",
        "the inputs its way declares differ from those it recorded: stage",
        "input script changed: content/zh/film-script.json",
        "output sound_gates missing: build/evidence/editions/zh/sound-gates.json",
    )
    assert records.judge(None, declared={}, running=other).reasons == ("no record",)
    unreadable = records.Unreadable("x.json is of schema 2, not 1")
    assert records.judge(unreadable, declared={}, running=other).reasons == (
        "unreadable record: x.json is of schema 2, not 1",
    )


def test_a_change_that_keeps_size_and_time_is_fresh_until_every_file_is_hashed(root, counted):
    record = run_record(root).model_copy(update={"outcome": "pass", "refusal": None})
    script = root / "content/zh/film-script.json"
    stat = script.stat()
    script.write_bytes(b'{"segments": {}}')
    os.utime(script, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert judged(record, counted).reasons == ()
    full = judged(record, counted, full=True)
    assert full.reasons == (
        "input script changed while keeping its size and time: content/zh/film-script.json",
    )
    assert [f.result for f in full.files if f.name == "script"] == ["blind"]
