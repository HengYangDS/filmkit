"""The plan on stand-in nodes and files: each node's state, reasons, class and readiness, judged
from its run records as decisions 5 and 6 of record-every-run say, and nothing written."""

import os
import time

import pytest

import filmkit.durations as durations
import filmkit.repository as repository
from filmkit.graph import nodes, opens, plan, runs
from filmkit.production import Edition

CODES = ("zh", "en")


def stand_in(name, reads, writes, expected="light"):
    """A node that reads and writes files below the root, each by its name; `{code}` in a file
    names the edition's own."""

    def places(files):
        return lambda e: {n: repository.ROOT / f.format(code=e.code) for n, f in files.items()}

    return nodes.Node(name, {"default": places(reads)}, places(writes), expected)


TABLE = (
    stand_in("assemble", {"script": "{code}/script.txt"}, {"timeline": "{code}/timeline.json"}),
    stand_in(
        "refresh-captions",
        {"script": "{code}/script.txt", "timeline": "{code}/timeline.json"},
        {"timeline": "{code}/timeline.json", "srt": "{code}/captions.srt"},
    ),
    stand_in("check-sound", {"timeline": "{code}/timeline.json"}, {"gate": "{code}/gate.json"}),
    stand_in("package-metadata", {"gate": "{code}/gate.json"}, {"page": "page.html"}),
    stand_in("stage", {"script": "{code}/script.txt"}, {"stage": "{code}/stage.txt"}),
    stand_in("render", {"stage": "{code}/stage.txt"}, {"picture": "{code}/picture"}, "heavy"),
)
SHARED = {
    "timeline": (
        nodes.Writer("assemble", nodes.REPLACES),
        nodes.Writer("refresh-captions", nodes.REWRITES, ("assemble",)),
    ),
    "page": (nodes.Writer("package-metadata", nodes.REPLACES),),
}
# What each stand-in command writes: refresh-captions rewrites the timeline as it read it.
WRITES = {
    "assemble": lambda root, code: {"timeline": "timeline of " + read(root, f"{code}/script.txt")},
    "refresh-captions": lambda root, code: {
        "timeline": read(root, f"{code}/timeline.json"),
        "srt": "captions",
    },
    "check-sound": lambda root, code: {"gate": "gate of " + read(root, f"{code}/timeline.json")},
    "package-metadata": lambda root, code: {"page": f"page of {code}"},
    "stage": lambda root, code: {"stage": "stage of " + read(root, f"{code}/script.txt")},
}


def read(root, name):
    return (root / name).read_text()


@pytest.fixture
def build(tmp_path, monkeypatch):
    """A film root of both editions' scripts, whose node table is the stand-in one."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in TABLE})
    monkeypatch.delenv(opens.NODE, raising=False)
    for code in CODES:
        (root / code).mkdir()
        (root / code / "script.txt").write_text(f"the {code} script")
    return nodes.load(TABLE, SHARED, CODES)


def ran(name, code="zh", *, refuse=None, whole=True):
    """Run a stand-in command as the chain runs it, after the last one has ended."""
    time.sleep(0.005)
    node = {node.name: node for node in TABLE}[name]
    with durations.run(code, name, whole=whole):
        if refuse:
            raise SystemExit(refuse)
        written = WRITES[name](repository.ROOT, code)
        for output, path in node.outputs(Edition(code)).items():
            path.write_text(written[output])


def chain(*codes):
    for code in codes or ("zh",):
        for name in ("assemble", "refresh-captions", "check-sound"):
            ran(name, code)


def judged(table, *targets, full=False):
    planned = plan.plan(table, targets, full=full)
    return planned, {entry.key: entry for entry in planned.entries}


def texts(entry):
    return [reason.text for reason in entry.reasons]


def test_a_chain_that_ran_in_order_is_fresh_and_ready_and_nothing_is_hashed(build):
    chain()
    planned, found = judged(build, "check-sound:zh")
    assert list(found) == ["assemble:zh", "refresh-captions:zh", "check-sound:zh"]
    for entry in found.values():
        assert (entry.state, entry.reasons, entry.ready) == ("fresh", [], True), entry.key
        assert (entry.host_class, entry.expected) == ("light", "light")
        assert entry.seconds is not None
    assert planned.hashed == 0


def test_a_touched_source_is_hashed_once_and_its_readers_stay_fresh(build):
    chain()
    script = repository.ROOT / "zh/script.txt"
    later = script.stat().st_mtime_ns + 10**9
    os.utime(script, ns=(later, later))
    planned, found = judged(build, "check-sound:zh")
    assert planned.hashed == 1
    assert {entry.state for entry in found.values()} == {"fresh"}


def test_an_edited_source_makes_its_readers_stale_and_the_nodes_after_them_behind(build):
    chain()
    (repository.ROOT / "zh/script.txt").write_text("the zh script, edited")
    _, found = judged(build, "check-sound:zh")
    assert found["assemble:zh"].state == found["refresh-captions:zh"].state == "stale"
    assert texts(found["assemble:zh"]) == ["input script changed: zh/script.txt"]
    assert [r.kind for r in found["assemble:zh"].reasons] == ["input"]
    assert (found["check-sound:zh"].state, found["check-sound:zh"].ready) == ("behind", False)


def test_a_node_after_a_failed_node_is_behind_and_not_ready(build):
    chain()
    ran("package-metadata")
    with pytest.raises(SystemExit):
        ran("check-sound", refuse="check-sound: the gate refused")
    _, found = judged(build, "package-metadata:zh")
    assert texts(found["check-sound:zh"]) == ["its run ended with the outcome refuse"]
    assert (found["package-metadata:zh"].state, found["package-metadata:zh"].ready) == (
        "behind",
        False,
    )


def test_a_node_after_a_partial_run_is_stale_as_changed_by_a_partial_run(build):
    ran("stage")
    (repository.ROOT / "zh/script.txt").write_text("the zh script, a part")
    ran("stage", whole=False)
    (repository.ROOT / "zh/script.txt").write_text("the zh script")
    _, found = judged(build, "stage:zh")
    assert texts(found["stage:zh"]) == ["changed by a partial run"]


def test_two_replacing_writers_of_a_page_are_fresh_until_a_hand_edit(build):
    chain(*CODES)
    ran("package-metadata", "zh")
    ran("package-metadata", "en")
    _, found = judged(build, "package-metadata:all")
    assert found["package-metadata:zh"].state == found["package-metadata:en"].state == "fresh"
    (repository.ROOT / "page.html").write_text("edited by hand")
    _, found = judged(build, "package-metadata:all")
    for code in CODES:
        entry = found[nodes.key("package-metadata", code)]
        assert texts(entry) == ["page.html changed by no declared writer"]
        assert [r.kind for r in entry.reasons] == ["unaccounted"]


def test_assemble_run_again_after_refresh_captions_leaves_it_stale_and_check_sound_behind(build):
    chain()
    before = (repository.ROOT / "zh/timeline.json").read_bytes()
    ran("assemble")
    assert (repository.ROOT / "zh/timeline.json").read_bytes() == before
    _, found = judged(build, "check-sound:zh")
    assert found["assemble:zh"].state == "fresh"
    assert texts(found["refresh-captions:zh"]) == [
        "its output timeline replaced by an earlier writer's run (assemble:zh)"
    ]
    assert (found["check-sound:zh"].state, found["check-sound:zh"].ready) == ("behind", False)


def test_a_node_is_ready_only_when_every_node_upstream_passed_and_its_inputs_exist(build):
    _, found = judged(build, "check-sound:zh")
    assert found["assemble:zh"].ready
    assert not found["refresh-captions:zh"].ready
    chain()
    (repository.ROOT / "zh/script.txt").unlink()
    _, found = judged(build, "check-sound:zh")
    assert not found["assemble:zh"].ready
    assert texts(found["assemble:zh"]) == ["input script missing: zh/script.txt"]


def test_a_node_without_a_record_is_unmeasured_with_its_expected_class(build):
    _, found = judged(build, "render:zh")
    render = found["render:zh"]
    assert (render.state, texts(render)) == ("stale", ["no record"])
    assert (render.host_class, render.expected, render.seconds) == ("unmeasured", "heavy", None)


def test_the_plan_writes_nothing(build):
    chain(*CODES)
    ran("package-metadata", "zh")
    (repository.ROOT / "zh/script.txt").write_text("edited")

    def listing():
        found = sorted(repository.ROOT.rglob("*"))
        return [(path, path.stat().st_size, path.stat().st_mtime_ns) for path in found]

    before = listing()
    judged(build)
    judged(build, full=True)
    assert listing() == before
