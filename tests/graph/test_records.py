"""The run record of schema 1 and the partial record: written, read back and refused."""

import json
import os
import shutil

import pytest

import filmkit.film as film
import filmkit.repository as repository
from filmkit.graph import nodes, opens, plan, records, runs


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


def test_a_film_wide_node_s_record_is_written_and_read_back_at_its_place(root):
    record = run_record(root).model_copy(update={"node": "check", "edition": None})
    records.write(record)
    place = records.place("check", None)
    assert place == root / "build/evidence/records/film/check.json"
    assert records.read(place) == record
    assert json.loads(place.read_text())["edition"] is None
    assert not (root / records.FOLDER).exists()


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
        **record.model_dump(exclude={"inputs", "carried", "schema_", "partial"}),
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


HEARD = f"""
[[narration.heard]]
edition = "en"
thought = "13.2"
take = "{"a" * 64}"
lines = ["units"]
listener = "Yang HENG"
date = "2026-11-24"
note = "He heard labelled said as written."
"""


@pytest.fixture
def declared(tmp_path, monkeypatch):
    """A copy of the sample's declaration and every file it names below a new root, and a
    stand-in table of two nodes, one that reads the declaration's `picture` table and one that
    reads its `narration` table, each run once; the declaration and the table."""
    root = tmp_path.resolve()
    for path in (repository.DECLARATION, *(named for _, named in film.named_files(film.FILM))):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, root / path)
    monkeypatch.setattr(repository, "ROOT", root)
    declaration = root / repository.DECLARATION

    def reader(name):
        table = records.DeclarationTable(declaration, name)
        places = {f"declaration.{name}": table}
        return nodes.Node(name, {"default": lambda e: places}, lambda e: {}, "light")

    readers = (reader("picture"), reader("narration"))
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in readers})
    monkeypatch.delenv(opens.NODE, raising=False)
    for node in readers:
        with runs.run("zh", node.name):
            pass
    return declaration, nodes.load(readers, {}, ("zh",))


def test_a_hearing_recorded_leaves_a_node_that_reads_only_the_picture_fresh(declared, monkeypatch):
    declaration, table = declared
    loaded, read = [], film.read
    monkeypatch.setattr(film, "read", lambda root: loaded.append(root) or read(root))
    # An unchanged declaration is judged by its size and time: no table is hashed.
    states = {entry.key: entry.state for entry in plan.plan(table).entries}
    assert (states, loaded) == ({"picture:zh": "fresh", "narration:zh": "fresh"}, [])
    stated = records.read(records.place("narration", "zh")).inputs["declaration.narration"]
    assert stated.path == "content/film.toml#narration"
    declaration.write_text(declaration.read_text() + HEARD)
    found = {entry.key: entry for entry in plan.plan(table).entries}
    assert found["picture:zh"].state == "fresh"
    assert found["narration:zh"].state == "stale"
    assert [reason.text for reason in found["narration:zh"].reasons] == [
        "input declaration.narration changed: content/film.toml#narration"
    ]
    # The changed declaration was loaded once to state both nodes' tables.
    assert loaded == [declaration.parents[1]]
