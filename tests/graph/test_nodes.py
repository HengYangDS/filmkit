"""The node table: the chain's commands as data, the edges derived from paths, and its refusals."""

from pathlib import Path

import pytest

import filmkit.produce as produce
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.graph import nodes
from filmkit.graph.records import Folder
from filmkit.narration import converge, readings
from filmkit.production import Edition


@pytest.fixture(scope="module")
def table():
    return nodes.chain()


def test_the_order_respects_every_derived_edge(table):
    position = {name: index for index, name in enumerate(table.order)}
    assert set(position) == {nodes.key(n.name, c) for n in nodes.TABLE for c in table.codes}
    for name, before in table.edges.items():
        assert all(position[earlier] < position[name] for earlier in before), name


def test_each_node_follows_the_writers_of_what_it_reads(table):
    for code in table.codes:
        up = {name: table.upstream(nodes.key(name, code)) for name in table.nodes}
        assert nodes.key("assemble", code) in up["refresh-captions"]
        assert {nodes.key("assemble", code), nodes.key("refresh-captions", code)} <= up[
            "check-sound"
        ]
        assert {nodes.key("check-picture", code), nodes.key("stage-picture", code)} <= up[
            "render-picture"
        ]
        assert nodes.key("compare-pictures", code) in up["package-film"]
        assert nodes.key("narrate", code) in up["select"]
    zh, en = (nodes.key("package-metadata", code) for code in ("zh", "en"))
    assert zh not in table.upstream(en)
    assert en not in table.upstream(zh)
    # Every edition's entry link names its runtime, so the page waits for every timeline.
    assert nodes.key("refresh-captions", "en") in table.upstream(zh)


def test_each_reader_follows_every_writer_of_its_inputs(table):
    for name in table.order:
        node, edition = table.node(name)
        outputs = {nodes.place(p) for p in node.outputs(edition).values()}
        reads = {nodes.place(p) for way in node.ways.values() for p in way(edition).values()}
        for other in table.order:
            if other == name:
                continue
            writer, of = table.node(other)
            for output, written in writer.outputs(of).items():
                path = nodes.place(written)
                # A rewriter declared to follow the reader comes after it.
                later = nodes.follows(writer.name, output, node.name, table.shared)
                if path in outputs or later:
                    continue
                if any(nodes.overlaps(path, read) for read in reads):
                    assert other in table.upstream(name), (name, other, path)


def stand_in(name, reads=(), writes=()):
    root = Path(repository.ROOT)
    return nodes.Node(
        name,
        {"default": lambda e: {r: root / r for r in reads}},
        lambda e: {w: root / w for w in writes},
        "light",
    )


def test_a_table_with_a_cycle_is_refused_naming_its_nodes():
    looped = (stand_in("a", reads=["y"], writes=["x"]), stand_in("b", reads=["x"], writes=["y"]))
    with pytest.raises(nodes.TableError, match=r"cycle: .*a:zh.*b:zh|cycle: .*b:zh.*a:zh"):
        nodes.load(looped, {}, ("zh",))


def test_an_undeclared_second_writer_is_refused_naming_the_path():
    both = (stand_in("a", writes=["page"]), stand_in("b", writes=["page"]))
    with pytest.raises(
        nodes.TableError, match=r"page is written by a:zh, b:zh with no declaration"
    ):
        nodes.load(both, {}, ("zh",))
    declared = {"page": (nodes.Writer("a", nodes.REPLACES), nodes.Writer("b", nodes.REPLACES))}
    assert nodes.load(both, declared, ("zh",)).edges == {"a:zh": set(), "b:zh": set()}


def test_a_node_whose_places_bind_one_name_to_two_places_is_refused_naming_it():
    root = Path(repository.ROOT)
    owner = {"composition": root / "picture/film.js", "script": root / "script.json"}
    clashing = nodes.Node(
        "a",
        {"default": lambda e: nodes.Places(composition=Folder(root / "picture", "**/*")) | owner},
        lambda e: {},
        "light",
    )
    with pytest.raises(nodes.TableError, match=r"bind composition to two places"):
        nodes.load([clashing], {}, ("zh",))
    # The same place under one name twice is no clash.
    same = nodes.Places(script=root / "script.json")
    assert same | owner == {**owner}
    same |= {"script": root / "script.json"}
    assert same == {"script": root / "script.json"}


def test_a_rewriter_follows_the_writers_it_names():
    rewritten = (stand_in("a", writes=["t"]), stand_in("b", reads=["t"], writes=["t"]))
    shared = {"t": (nodes.Writer("a", nodes.REPLACES), nodes.Writer("b", nodes.REWRITES, ("a",)))}
    assert nodes.load(rewritten, shared, ("zh",)).order == ("a:zh", "b:zh")


def test_every_command_with_a_duration_record_is_a_node_or_named_with_its_reason(table):
    commands = {
        *produce.EDITION_ACTIONS,
        *(f"{action}-uncaptioned" for action in produce.PICTURE_ACTIONS),
        *tools.BUILD_RUNS.values(),
        "narrate",
        "narrate-checks",
        converge.COMMAND,
        "verify",
        "reproduce",
    }
    unnamed = commands - set(table.nodes) - set(nodes.NOT_NODES)
    assert unnamed == set()
    assert set(table.nodes).isdisjoint(nodes.NOT_NODES)


def test_the_uncaptioned_picture_reads_the_inputs_of_its_way(table):
    node, edition = table.node("render-picture-uncaptioned:zh")
    derived, native = node.inputs(edition, "derived"), node.inputs(edition, "native")
    assert derived["captioned_picture"] == edition.picture
    assert "stage" not in derived
    assert native["stage"] == Folder(edition.rendered(captions=False).stage, "**/*")
    assert node.way(edition, "native") == "native"


def test_the_occurrence_plan_is_no_output_of_any_node(table):
    # The readings check writes it before a narration's run opens, a dry run's too (design
    # decision 8), so no record binds it.
    for code in table.codes:
        plan = (repository.ROOT / readings.plan_path(code)).resolve()
        for node in table.nodes.values():
            outputs = {nodes.place(p) for p in node.outputs(Edition(code)).values()}
            assert plan not in outputs, node.name
