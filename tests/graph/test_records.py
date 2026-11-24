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
