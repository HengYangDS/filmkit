"""Anchors: named spans of a script's own words, refused before anything is written when broken."""

import json

import pytest

import filmkit.captions.refresh as refresh
import filmkit.narration.anchors as anchors
import filmkit.narration.narrate as narrate
import filmkit.narration.script_edits as script_edits
import filmkit.picture.gates as gates
import filmkit.picture.renderer as renderer
import filmkit.picture.rendering as rendering
import filmkit.preflight as preflight
import filmkit.repository as repository
import filmkit.soundtrack.assembly as assembly
from filmkit.narration.anchors import AnchorError
from filmkit.picture.errors import PictureError
from filmkit.production import Edition


def segment(sid: str, *written: str) -> dict:
    """A segment whose anchored thoughts are `written`, its plain fields filled from them."""
    groups = anchors.plain(list(written))
    return {
        "id": sid,
        "anchored_groups": list(written),
        "utterance_groups": groups,
        "text": "".join(groups),
    }


def script(*segments: dict) -> dict:
    return {"segments": list(segments)}


def refusal(value: dict, code: str = "zh") -> str:
    with pytest.raises(AnchorError) as raised:
        anchors.require(value, code)
    return str(raised.value)


def spans(marked: dict) -> dict:
    """Each segment's anchors as (id, thought, words, units)."""
    return {
        sid: [(a.id, a.thought, a.words, a.units) for a in found] for sid, found in marked.items()
    }


def test_anchors_that_nest_cross_and_share_words_are_read_with_their_units():
    marked = anchors.require(
        script(
            segment("03", "这是第一句。", "{a}依据{b}有{/a}先后{/b}。"),
            segment("04", "最先是{law}{first-rank}法律{/first-rank}{/law}，其次是规章。"),
        ),
        "zh",
    )
    assert spans(marked) == {
        # The second thought's units start after the first's five.
        "03": [("a", 2, "依据有", (5, 8)), ("b", 2, "有先后", (7, 10))],
        "04": [("law", 1, "法律", (3, 5)), ("first-rank", 1, "法律", (3, 5))],
    }


def test_a_script_without_anchored_groups_has_no_anchors():
    plain = {"segments": [{"id": "01", "utterance_groups": ["甲。"], "text": "甲。"}]}
    assert anchors.require(plain, "zh") == {}


def test_english_units_are_letters_and_digits_of_the_text():
    marked = anchors.require(script(segment("02", "The {next}next steps{/next} follow.")), "en")
    assert spans(marked) == {"02": [("next", 1, "next steps", (3, 12))]}


@pytest.mark.parametrize(
    ("written", "named"),
    [
        (["依据{order}有先后。"], "zh 03.1 order: opens and does not close in its thought"),
        (["依据有先后{/order}。"], "zh 03.1 order: closes without opening in its thought"),
        (["{Order_2}依据{/Order_2}。"], "zh 03.1 Order_2: is not a kebab-case id"),
        (["{order-}依据{/order-}。"], "zh 03.1 order-: is not a kebab-case id"),
        (["{constructor}依据{/constructor}。"], "zh 03.1 constructor: is a name every JavaScript"),
        (["依据{order}，{/order}有先后。"], "zh 03.1 order: marks no spoken unit"),
        (["依据{order}有{order}先后{/order}。"], "zh 03.1 order: opens twice"),
        (["依据{有先后。"], "zh 03.1: a brace that is no mark"),
    ],
)
def test_a_broken_anchor_is_named_by_edition_segment_thought_and_id(written, named):
    assert named in refusal(script(segment("03", *written)))


def test_an_anchor_across_thoughts_is_named_in_both():
    message = refusal(script(segment("03", "依据{order}有先", "后{/order}。")))
    assert "zh 03.1 order: opens and does not close in its thought" in message
    assert "zh 03.2 order: closes without opening in its thought" in message


def test_one_id_on_two_anchors_of_a_segment_names_both_thoughts():
    message = refusal(script(segment("05", "{law}法律{/law}。", "还是{law}法律{/law}。")))
    assert "zh 05.1 and 05.2 law: marks two anchors of one segment" in message


def test_one_id_in_two_segments_is_two_anchors():
    both = script(segment("05", "{law}法律{/law}。"), segment("06", "{law}法律{/law}。"))
    assert sorted(anchors.require(both, "zh")) == ["05", "06"]


def test_plain_thoughts_edited_by_hand_are_refused_with_the_way_to_change_words():
    edited = segment("07", "{order}有先后{/order}。")
    edited["utterance_groups"] = ["有前后。"]
    edited["text"] = "有前后。"
    message = refusal(script(edited), "en")
    assert message.startswith("The en script's anchors break their rules:")
    assert "en 07: its utterance_groups and text are not its anchored_groups" in message
    assert "filled from its anchored ones" in message
    assert "python -m filmkit.narration.script_edits" in message


def test_every_broken_rule_is_named_at_once():
    message = refusal(
        script(segment("01", "{a}甲。", "{B}乙{/B}。"), segment("02", "丙{/c}。")), "zh"
    )
    assert [line.split(":")[0] for line in message.splitlines()[1:]] == [
        "zh 01.1 a",
        "zh 01.2 B",
        "zh 02.1 c",
    ]


def test_marks_are_written_back_as_they_were_read():
    written = "{a}依据{b}有{/a}先后{/b}。{law}{first-rank}法律{/first-rank}{/law}"
    thought = anchors.Thought.parse(written)
    assert thought.text == "依据有先后。法律"
    assert thought.written() == written


def put(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False))


def tree(root) -> dict:
    """Every path below a root, with each file's bytes."""
    return {path: path.read_bytes() if path.is_file() else None for path in root.rglob("*")}


@pytest.fixture
def broken(tmp_path, monkeypatch):
    """A film root whose Chinese script and timeline mark an anchor that never closes, with what
    each command reads before its anchors; the words checks of narration pass."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    for check in ("concepts", "register"):
        monkeypatch.setattr(getattr(narrate, check), "check", lambda: {})
    monkeypatch.setattr(narrate.readings, "check", lambda code: {})
    unclosed = segment("01", "依据{order}有先后。")
    english = {"id": "01", "utterance_groups": ["One."], "text": "One."}
    for code, scripted in (("zh", unclosed), ("en", english)):
        edition = Edition(code)
        put(root / edition.script, {"segments": [scripted]})
        put(edition.timeline, {"segments": [{**scripted, "words": []}], "duration": 9})
    package = {"name": renderer.RENDERER_NAME, "version": renderer.RENDERER_VERSION}
    put(root / "node_modules" / renderer.RENDERER_PACKAGE, package)
    put(root / "edits.json", {"replace": {"zh": [["01.1", "依据", "根据"]]}})
    return root


@pytest.mark.parametrize(
    "command",
    [
        lambda zh: assembly.assemble(zh),
        lambda zh: refresh.refresh_captions(zh),
        lambda zh: rendering.stage_picture(zh, None, 9, 3840, 2160),
        lambda zh: gates.check_picture(zh),
        lambda zh: preflight.preflight(zh),
        lambda zh: narrate.gate("zh"),
        lambda zh: script_edits.main(["--edits", "edits.json"]),
    ],
    ids=[
        "assemble",
        "refresh-captions",
        "stage-picture",
        "check-picture",
        "preflight",
        "narration",
        "script_edits",
    ],
)
def test_each_command_refuses_a_broken_anchor_before_it_writes(broken, command):
    before = tree(broken)
    with pytest.raises((AnchorError, PictureError, SystemExit), match="zh 01.1 order: opens"):
        command(Edition("zh"))
    assert tree(broken) == before
