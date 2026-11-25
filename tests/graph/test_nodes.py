"""The node table: the chain's commands as data, the edges derived from paths, and its refusals."""

import tomllib
from pathlib import Path

import pytest
import sample_sound

import filmkit.film as film
import filmkit.produce as produce
import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.graph import chain, nodes
from filmkit.graph.records import Folder
from filmkit.narration import converge, readings
from filmkit.production import Edition


@pytest.fixture(scope="module")
def table():
    return chain.table()


def test_the_order_respects_every_derived_edge(table):
    position = {name: index for index, name in enumerate(table.order)}
    keys = {named for n in chain.TABLE for named, _ in n.instances(table.codes)}
    assert set(position) == keys
    for name, before in table.edges.items():
        assert all(position[earlier] < position[name] for earlier in before), name


def test_each_node_follows_the_writers_of_what_it_reads(table):
    for code in table.codes:
        up = {
            name: table.upstream(nodes.key(name, code))
            for name, node in table.nodes.items()
            if code in node.codes(table.codes)
        }
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


def test_a_film_wide_node_comes_before_the_edition_nodes_that_read_its_output():
    root = Path(repository.ROOT)
    check = nodes.Node(
        "check",
        {"default": lambda e: {"script": root / "script.json"}},
        lambda e: {"verdict": root / "verdict.json"},
        "light",
        per=nodes.FILM,
    )
    loaded = nodes.load((stand_in("narrate", reads=["verdict.json"]), check), {}, ("zh", "en"))
    # One run for the film, keyed by its name alone, before each edition's reader.
    assert set(loaded.edges) == {"check", "narrate:zh", "narrate:en"}
    assert loaded.edges["narrate:zh"] == loaded.edges["narrate:en"] == {"check"}
    assert loaded.order[0] == "check"
    assert loaded.node("check") == (check, None)
    assert loaded.node("narrate:en")[1] == Edition("en")
    # A film-wide node has no edition's key, and an edition's node no key without one.
    for named in ("check:zh", "narrate"):
        with pytest.raises(KeyError):
            loaded.node(named)
    assert (nodes.key("check", None), nodes.split("check")) == ("check", ("check", None))


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


def test_every_command_the_seam_measures_is_a_node_or_named_with_its_reason(table):
    commands = {
        *produce.EDITION_ACTIONS,
        *(f"{action}-uncaptioned" for action in produce.PICTURE_ACTIONS),
        *tools.BUILD_RUNS.values(),
        "narrate",
        converge.COMMAND,
        "verify",
        "reproduce",
    }
    unnamed = commands - set(table.nodes) - set(chain.NOT_NODES)
    assert unnamed == set()
    assert set(table.nodes).isdisjoint(chain.NOT_NODES)


def test_the_uncaptioned_picture_reads_the_inputs_of_its_way(table):
    node, edition = table.node("render-picture-uncaptioned:zh")
    derived, native = node.inputs(edition, "derived"), node.inputs(edition, "native")
    assert derived["captioned_picture"] == edition.picture
    # The derived way reads the captioned picture's stage, which its validation reads, and no
    # stage of its own.
    assert derived["stage"] == Folder(edition.rendered().stage, "**/*")
    own = edition.rendered(captions=False).stage
    assert nodes.place(own) not in {nodes.place(path) for path in derived.values()}
    assert native["stage"] == Folder(own, "**/*")
    assert node.way(edition, "native") == "native"


def test_the_occurrence_plans_are_outputs_of_the_source_check_alone(table):
    # The film-wide node `check` writes each edition's occurrence plan (design decision 6 of
    # build-a-film-by-its-verbs), and no other node does.
    for code in table.codes:
        plan = (repository.ROOT / readings.plan_path(code)).resolve()
        writers = [
            named
            for node in table.nodes.values()
            for named, edition in node.instances(table.codes)
            if plan in {nodes.place(p) for p in node.outputs(edition).values()}
        ]
        assert writers == ["check"], code


def test_the_derived_picture_reads_what_the_validation_of_the_captioned_picture_reads(table):
    # Deriving begins with the captioned picture's validation (`derivation.derive_uncaptioned`
    # calls `rendering.validate_picture`), so the derived way reads every input of that node.
    for code in table.codes:
        edition = Edition(code)
        derived = table.nodes["render-picture-uncaptioned"].inputs(edition, "derived").values()
        validated = table.nodes["validate-picture"].inputs(edition).values()
        missing = {nodes.place(p) for p in validated} - {nodes.place(p) for p in derived}
        assert not missing, sorted(str(path) for path in missing)


def test_the_table_loads_beside_a_receipt_that_cannot_be_read(tmp_path, monkeypatch):
    root = sample_sound.copy_film((tmp_path / "film").resolve())
    monkeypatch.setattr(repository, "ROOT", root)
    receipt = Edition("zh").rendered(captions=False).receipt
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{damaged")
    # A receipt that cannot be read is no derived picture's, as the way of the picture takes it.
    compared = chain.table().nodes["compare-pictures"].inputs(Edition("zh"))
    assert "uncaptioned_stage" in compared


def test_the_renderer_is_qualified_once_a_build_for_the_first_edition(table):
    # `picture/qualification.py`: every engine release qualifies the canvas build it pins, once.
    first, *others = table.codes
    assert nodes.key("qualify-renderer", first) in table.edges
    assert not any(nodes.key("qualify-renderer", code) in table.edges for code in others)
    # The sample declares drafts, so each edition renders its draft.
    assert all(nodes.key("render-draft", code) in table.edges for code in table.codes)


def test_the_renderer_is_qualified_for_the_edition_the_film_declares(monkeypatch):
    # A film that declares English first and qualifies its renderer on the Chinese edition.
    picture = chain.FILM.picture.model_copy(update={"qualified_edition": "zh"})
    film = chain.FILM.model_copy(update={"picture": picture})
    monkeypatch.setattr(chain, "FILM", film)
    table = nodes.load(chain.TABLE, chain.SHARED, ("en", "zh"))
    assert nodes.key("qualify-renderer", "zh") in table.edges
    assert nodes.key("qualify-renderer", "en") not in table.edges


def test_a_qualified_edition_the_film_does_not_declare_is_refused():
    declared = tomllib.loads((repository.ROOT / repository.DECLARATION).read_text())
    declared["picture"]["qualified_edition"] = "fr"
    with pytest.raises(ValueError, match="picture.qualified_edition names the edition fr"):
        film.Film.model_validate(declared)
