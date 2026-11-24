"""The recorder of what each run opens and its check against the node table (design decision 4)."""

import json
import os
import shutil
import subprocess
import sys

import pytest
import sample_sound

import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.graph import chain, nodes, opens

# A Node child that reads a declared and an undeclared file, writes in the temporary folder,
# opens a socket to a closed port and runs to its end.
NODE_CHILD = """
const fs = require("node:fs"), net = require("node:net"), os = require("node:os");
const path = require("node:path");
const root = process.argv[2];
fs.readFileSync(path.join(root, "in.txt"));
fs.readFileSync(path.join(root, "secret.txt"));
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), "opens-"));
fs.writeFileSync(path.join(scratch, "note.txt"), "x");
fs.rmSync(scratch, { recursive: true });
const socket = net.connect(1, "127.0.0.1");
socket.on("error", (error) => { console.log("done " + error.code); });
"""


def stand_in(name, reads=(), writes=()):
    return nodes.Node(
        name,
        {"default": lambda e: {f: repository.ROOT / f for f in reads}},
        lambda e: {f: repository.ROOT / f for f in writes},
        "light",
    )


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root with one declared input, one undeclared file and a stand-in table."""
    root = (tmp_path / "film").resolve()
    (root / "content").mkdir(parents=True)
    (root / repository.DECLARATION).write_text("")
    (root / "in.txt").write_text("in")
    (root / "secret.txt").write_text("secret")
    monkeypatch.setattr(repository, "ROOT", root)
    table = nodes.load(
        [stand_in("stand", ["in.txt"], ["out.json"]), stand_in("other", ["out.json"])],
        {},
        ("zh",),
    )
    return root, tmp_path / "opens.jsonl", table


def python_child(root, log, code, node="stand:zh"):
    """Run Python code in a child that imports the engine, as a node's run with the log set."""
    environment = {**os.environ, repository.ROOT_VARIABLE: str(root), opens.NODE: node}
    if log is not None:
        environment[opens.VARIABLE] = str(log)
    prelude = "import filmkit, filmkit.repository as repository\n"
    subprocess.run(
        [sys.executable, "-I", "-B", "-c", prelude + code],
        env=environment,
        cwd=root,
        check=True,
        timeout=60,
    )


def test_an_undeclared_read_by_a_python_child_fails_naming_the_file(film):
    root, log, table = film
    python_child(root, log, "open(repository.ROOT / 'in.txt').read()\n")
    python_child(root, log, "open(repository.ROOT / 'secret.txt').read()\n")
    report = opens.check(log, table)
    assert report.seen == {"stand:zh"}
    assert len(report.findings) == 1
    assert "stand:zh" in report.findings[0]
    assert "read secret.txt, which its declaration does not name" in report.findings[0]


def test_a_record_written_through_repository_write_counts_as_its_target(film):
    root, log, table = film
    python_child(root, log, "repository.write(repository.ROOT / 'out.json', {})\n")
    assert opens.check(log, table).ok
    kinds = {entry["kind"] for entry in map(json.loads, log.read_text().splitlines())}
    assert {"write", "source", "rename"} <= kinds
    python_child(root, log, "repository.write(repository.ROOT / 'else.json', {})\n")
    (finding,) = opens.check(log, table).findings
    assert "wrote else.json, which its outputs do not name" in finding


def test_work_below_runtime_is_exempted_and_reported_with_its_node(film):
    root, log, table = film
    code = "p = repository.ROOT / 'build/runtime/work/x.txt'\n"
    code += "p.parent.mkdir(parents=True)\np.write_text('x')\n"
    python_child(root, log, code)
    report = opens.check(log, table)
    assert report.ok
    assert report.exempted == {f"work: {opens.EXEMPT['work']}": {"stand:zh"}}


def test_a_label_that_names_no_node_fails_the_check(film):
    root, log, table = film
    python_child(root, log, "open(repository.ROOT / 'in.txt').read()\n", node="ghost:zh")
    report = opens.check(log, table)
    assert report.unjudged == {"ghost:zh"}
    assert not report.ok


def node_child(root, script, monkeypatch, log):
    monkeypatch.setenv(opens.VARIABLE, str(log))
    monkeypatch.setenv(opens.NODE, "stand:zh")
    node = shutil.which("node")
    assert node, "the suite runs in the film's Mise environment, which supplies Node"
    environment = {**os.environ, **opens.node_options()}
    return subprocess.run(
        [node, str(script), str(root)],
        env=environment,
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )


def test_an_undeclared_read_by_a_node_child_fails_and_the_child_runs_to_its_end(
    film, tmp_path, monkeypatch
):
    root, log, table = film
    script = tmp_path / "child.cjs"
    script.write_text(NODE_CHILD)
    done = node_child(root, script, monkeypatch, log)
    assert done.stdout.strip() == "done ECONNREFUSED"
    assert "--permission-audit" in opens.node_options()["NODE_OPTIONS"]
    report = opens.check(log, table)
    (finding,) = report.findings
    assert finding.startswith("stand:zh: node (pid ")
    assert "read secret.txt, which its declaration does not name" in finding


def test_nothing_is_recorded_and_node_starts_unaudited_when_the_variable_is_unset(
    film, monkeypatch
):
    root, log, _ = film
    monkeypatch.delenv(opens.VARIABLE, raising=False)
    python_child(root, None, "open(repository.ROOT / 'secret.txt').read()\n")
    assert not log.exists()
    monkeypatch.setenv(opens.NODE, "stand:zh")
    assert opens.node_options() == {}
    started = []

    class Started:
        def __init__(self, command, env, **_):
            started.append(env)

        def wait(self):
            return 0

    monkeypatch.setattr(tools.picture_renderer, "require_renderer", lambda: None)
    monkeypatch.setattr(tools.picture_browser, "browser_path", lambda: root / "chrome")
    monkeypatch.setattr(tools, "stage_tools", lambda: root)
    monkeypatch.setattr(tools, "MEASURING", ())
    monkeypatch.setattr(tools.subprocess, "Popen", Started)
    monkeypatch.delenv("NODE_OPTIONS", raising=False)
    assert tools.run(next(iter(tools.TOOLS)), []) == 0
    assert "--permission-audit" not in started[0].get("NODE_OPTIONS", "")


@pytest.mark.ffmpeg
def test_every_node_the_light_suite_runs_reads_and_writes_only_what_it_declares(built, monkeypatch):
    root, log = built
    monkeypatch.setattr(repository, "ROOT", root)
    report = opens.check(log)
    assert report.findings == []
    assert report.unjudged == set()
    assert report.seen == {nodes.key(command, code) for command, code in sample_sound.CHAIN}
    # The nodes whose tools are seen only through their arguments are named with them.
    named = report.unseen
    for code in sample_sound.NARRATED:
        assert named[nodes.key("assemble", code)] == chain.MEDIA
        assert named[nodes.key("check-sound", code)] == chain.MEDIA
    assert named[nodes.key("preflight", "zh")] == chain.BROWSER
    # Each exemption is reported with the nodes it covered.
    records = f"records: {opens.EXEMPT['records']}"
    assert report.exempted[records] == report.seen


@pytest.mark.ffmpeg
def test_the_engine_s_start_up_reads_in_a_child_are_exempted_as_start_up(
    built, tmp_path, monkeypatch
):
    root, _ = built
    monkeypatch.setattr(repository, "ROOT", root)
    log = tmp_path / "opens.jsonl"
    # A child of a node's run starts the engine: the film loader validates every file the
    # declaration names (the other edition's sources, the review prompt, the entry page, readings
    # that do not stand) and the delivery format reads every script for the chapter count.
    code = "from filmkit.film import FILM\nimport filmkit.specification\n"
    python_child(root, log, code, node="check-sound:zh")
    report = opens.check(log)
    assert report.findings == []
    assert report.exempted[f"start-up: {opens.EXEMPT['start-up']}"] == {"check-sound:zh"}
    kinds = {entry["kind"] for entry in map(json.loads, log.read_text().splitlines())}
    assert kinds == {"load"}


@pytest.mark.ffmpeg
def test_a_file_looked_for_and_not_found_is_judged_as_a_probe(built, tmp_path, monkeypatch):
    root, _ = built
    monkeypatch.setattr(repository, "ROOT", root)
    log = tmp_path / "opens.jsonl"
    # The Chinese edition has no readings, which the table names as select's input only where
    # they stand; a look for them is let through, a look for anything else is not.
    code = "from filmkit.film import FILM\n"
    for name in ("content/zh/readings.json", "content/zh/nothing.json"):
        code += f"try:\n    open(repository.ROOT / {name!r})\nexcept FileNotFoundError:\n    pass\n"
    python_child(root, log, code, node="select:zh")
    (finding,) = opens.check(log).findings
    assert "looked for content/zh/nothing.json, which its declaration does not name" in finding


@pytest.mark.ffmpeg
def test_the_recorder_s_own_reads_of_the_table_are_no_reads_of_the_run(
    built, tmp_path, monkeypatch
):
    root, _ = built
    monkeypatch.setattr(repository, "ROOT", root)
    log = tmp_path / "opens.jsonl"
    # A function of the table that reads a file, as the way of a derived picture reads its
    # receipt, read while the recorder states Node's allowances inside the run.
    code = "from filmkit.graph import chain, opens\nfrom filmkit.production import Edition\n"
    code += "real = chain.derived_uncaptioned\n"
    code += "def reading(edition):\n"
    code += "    (repository.ROOT / Edition('en').script).read_bytes()\n"
    code += "    return real(edition)\n"
    code += "chain.derived_uncaptioned = reading\nassert opens.node_options()\n"
    python_child(root, log, code, node="compare-pictures:zh")
    assert opens.check(log).findings == []


def fresh_copy(tmp_path):
    """A copy of the sample's sources alone, which a test may write below."""
    return sample_sound.copy_film((tmp_path / "film").resolve())


def test_a_failed_packaging_s_receipt_is_an_output_of_package_film(tmp_path, monkeypatch):
    root = fresh_copy(tmp_path)
    monkeypatch.setattr(repository, "ROOT", root)
    log = tmp_path / "opens.jsonl"
    # An encode that fails writes what it was bound to, as package-film's encodes do.
    code = "import subprocess\nimport filmkit.delivery.packaging as packaging\n"
    code += "from filmkit.production import Edition\n"
    code += "work = repository.ROOT / 'build/runtime/work/failed.mp4'\n"
    code += "Edition('zh').evidence.mkdir(parents=True)\n"
    code += "try:\n    packaging.encode(Edition('zh'), {'editions': []}, ['false'], 60, work)\n"
    code += "except subprocess.CalledProcessError:\n    pass\n"
    python_child(root, log, code, node="package-film:zh")
    assert (root / "build/evidence/editions/zh/packaging-failure.json").is_file()
    assert opens.check(log).findings == []


def test_the_narration_s_caches_are_outputs_of_narrate(tmp_path, monkeypatch):
    root = fresh_copy(tmp_path)
    monkeypatch.setattr(repository, "ROOT", root)
    log = tmp_path / "opens.jsonl"
    # A narration caches each recording's alignment and transcript at its owner's place.
    code = "from filmkit.narration.alignment_records import alignment_record\n"
    code += "from filmkit.narration.transcript_records import transcript_record\n"
    code += "from filmkit.production import Edition\n"
    code += "language, sha = Edition('zh').language, 'a' * 64\n"
    code += "aligned = repository.ROOT / alignment_record(language, '01', sha, 'b' * 64)\n"
    code += "heard = transcript_record(language, '01', sha, {'repo': 'recognizer'})\n"
    code += "for path in (aligned, heard):\n"
    code += "    path.parent.mkdir(parents=True, exist_ok=True)\n"
    code += "    repository.write(path, {})\n"
    python_child(root, log, code, node="narrate:zh")
    assert opens.check(log).findings == []


def test_a_virtual_environment_named_whole_is_an_environment(film):
    root, log, table = film
    (root / ".venv").mkdir()
    (root / ".venv/pyvenv.cfg").write_text("home = /usr/bin\n")
    # `uv run` names the film's environment in VIRTUAL_ENV, which a child's environment carries.
    code = "import os, subprocess, sys\n"
    code += "environment = {**os.environ, 'VIRTUAL_ENV': str(repository.ROOT / '.venv')}\n"
    code += "subprocess.run([sys.executable, '-c', 'pass'], env=environment, check=True)\n"
    python_child(root, log, code)
    report = opens.check(log, table)
    assert report.ok, report.findings
    assert report.exempted == {f"environment: {opens.EXEMPT['environment']}": {"stand:zh"}}


def test_a_tree_removed_is_one_removal_and_a_rename_s_source_is_judged(film):
    root, log, table = film
    (root / "tree/sub").mkdir(parents=True)
    (root / "tree/sub/a.log").write_text("a")
    # shutil.rmtree names each member through a folder's descriptor; the tree is what it removes.
    python_child(root, log, "import shutil\nshutil.rmtree(repository.ROOT / 'tree')\n")
    (finding,) = opens.check(log, table).findings
    assert "removed tree, which its outputs do not name" in finding
    # A rename that moves a file another process wrote takes it from its place: a removal there.
    log.unlink()
    code = "import os\nos.replace(repository.ROOT / 'in.txt', repository.ROOT / 'out.json')\n"
    python_child(root, log, code)
    (finding,) = opens.check(log, table).findings
    assert "removed in.txt, which its outputs do not name" in finding


@pytest.mark.ffmpeg
def test_a_read_in_a_module_body_passes_only_for_a_file_the_engine_reads_at_start_up(
    built, tmp_path, monkeypatch
):
    root, _ = built
    monkeypatch.setattr(repository, "ROOT", root)
    log = tmp_path / "opens.jsonl"
    # Two reads from the body of an engine module, as a module imported during a run makes them:
    # the review prompt, which the engine reads as it starts, and the composition, which it does
    # not, and which check-sound does not declare.
    code = "from filmkit.film import FILM\nbody = '''\n"
    code += "(repository.ROOT / 'content/review/prompt.md').read_bytes()\n"
    code += "(repository.ROOT / 'picture/film.js').read_bytes()\n'''\n"
    module = "{'__name__': 'filmkit.probe', 'repository': repository}"
    code += f"exec(compile(body, 'probe', 'exec'), {module})\n"
    python_child(root, log, code, node="check-sound:zh")
    (finding,) = opens.check(log).findings
    assert "read picture/film.js, which its declaration does not name" in finding
