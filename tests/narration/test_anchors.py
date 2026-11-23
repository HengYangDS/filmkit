"""Anchors: named spans of a script's own words, refused before anything is written when broken."""

import json
from itertools import pairwise

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
import filmkit.tools as tools
from filmkit.narration.anchors import AnchorError
from filmkit.narration.spoken_units import units
from filmkit.picture import anchor_reads
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
        lambda zh: anchors.main(["--timeline", "build/derived"]),
    ],
    ids=[
        "assemble",
        "refresh-captions",
        "stage-picture",
        "check-picture",
        "preflight",
        "narration",
        "script_edits",
        "report",
    ],
)
def test_each_command_refuses_a_broken_anchor_before_it_writes(broken, command):
    before = tree(broken)
    with pytest.raises((AnchorError, PictureError, SystemExit), match="zh 01.1 order: opens"):
        command(Edition("zh"))
    assert tree(broken) == before


@pytest.mark.parametrize(
    "command",
    [
        lambda zh: rendering.stage_picture(zh, None, 9, 3840, 2160),
        lambda zh: gates.check_picture(zh),
    ],
    ids=["stage-picture", "check-picture"],
)
def test_a_timeline_whose_anchors_are_not_its_words_times_is_refused(broken, command):
    marked = segment("01", "依据{order}有先后{/order}。")
    words = [
        {"text": unit, "start": index, "end": index + 1} for index, unit in enumerate("依据有先后")
    ]
    zh = Edition("zh")
    put(broken / zh.script, {"segments": [marked]})
    hand = {"order": {"start": 0, "end": 5, "units": [2, 5], "thought": 1}}
    put(zh.timeline, {"segments": [{**marked, "words": words, "anchors": hand}], "duration": 9})
    before = tree(broken)
    with pytest.raises((AnchorError, PictureError), match="run produce refresh-captions"):
        command(zh)
    assert tree(broken) == before


@pytest.fixture
def editions(tmp_path, monkeypatch):
    """Two editions: the Chinese marks `order` in segment 03 and `fails` in 26, the English
    `order` only."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    scripts = {
        "zh": script(
            segment("03", "依据{order}有先后{/order}。"), segment("26", "{fails}失败{/fails}。")
        ),
        "en": script(
            segment("03", "There is an {order}order{/order}."), segment("26", "It fails.")
        ),
    }
    for code, value in scripts.items():
        put(tmp_path / Edition(code).script, value)
    return scripts


def test_the_report_lists_each_editions_anchors_and_the_ids_one_edition_marks(editions, capsys):
    anchors.main(["--json"])
    report = json.loads(capsys.readouterr().out)
    assert report["editions"]["zh"] == {
        "timeline": None,
        "stale": False,
        "segments": {
            "03": [{"id": "order", "thought": 1, "words": "有先后", "units": [2, 5]}],
            "26": [{"id": "fails", "thought": 1, "words": "失败", "units": [0, 2]}],
        },
    }
    assert report["editions"]["en"]["segments"] == {
        "03": [{"id": "order", "thought": 1, "words": "order", "units": [9, 14]}]
    }
    assert report["one_edition"] == [{"edition": "zh", "segment": "26", "id": "fails"}]
    anchors.main([])
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == "zh: 2 anchors in 2 segments; no timeline holds their times"
    assert printed[1].split() == ["03.1", "order", "units", "2-5", "有先后"]
    assert printed[-2:] == ["Marked in one edition only:", "  zh 26 fails"]


def test_the_report_gives_the_times_an_editions_timeline_holds(editions, capsys):
    zh = Edition("zh")
    timeline = anchors.derived_timeline(editions["zh"], "zh")
    put(zh.timeline, timeline)
    anchors.main(["--json"])
    listed = json.loads(capsys.readouterr().out)["editions"]["zh"]
    assert listed["timeline"] == repository.relative(zh.timeline)
    order = timeline["segments"][0]["anchors"]["order"]
    assert listed["segments"]["03"][0] | order == {
        **listed["segments"]["03"][0],
        "start": order["start"],
        "end": order["end"],
    }
    anchors.main([])
    assert f"{order['start']:.2f}-{order['end']:.2f} s" in capsys.readouterr().out
    # A marks edit that no refresh adopted leaves the timeline's times stale: none is given.
    marked = editions["zh"]
    marked["segments"][1] = segment("26", "失败。")
    put(repository.ROOT / zh.script, marked)
    anchors.main(["--json"])
    listed = json.loads(capsys.readouterr().out)["editions"]["zh"]
    assert listed["stale"] is True and "start" not in listed["segments"]["03"][0]
    anchors.main([])
    assert "are stale: run produce refresh-captions --language zh" in capsys.readouterr().out


def test_the_engine_places_the_anchors_on_a_timeline_of_other_words(editions, tmp_path):
    words = [
        {"text": unit, "start": index, "end": index + 1} for index, unit in enumerate("依据有先后")
    ]
    timed = {"segments": [{**editions["zh"]["segments"][0], "words": words}]}
    put(tmp_path / "own.json", timed)
    anchors.main(["--place", str(tmp_path / "own.json"), "--language", "zh"])
    placed = json.loads((tmp_path / "own.json").read_text())["segments"][0]["anchors"]
    assert placed == {"order": {"start": 2, "end": 5, "units": [2, 5], "thought": 1}}


def test_the_derived_timeline_is_the_same_twice_and_times_each_anchor_by_its_words(
    editions, tmp_path, capsys
):
    for folder in ("first", "second"):
        anchors.main(["--timeline", str(tmp_path / folder)])
    capsys.readouterr()
    for code in ("zh", "en"):
        first, second = (tmp_path / folder / f"{code}.json" for folder in ("first", "second"))
        assert first.read_bytes() == second.read_bytes()
    derived = json.loads((tmp_path / "first/zh.json").read_text())
    words = derived["segments"][0]["words"]
    # One word per Han character, 0.2 s each, after the 1.0 s before the segment.
    assert [(w["text"], w["start"], w["end"]) for w in words[:3]] == [
        ("依", 1.0, 1.2),
        ("据", 1.2, 1.4),
        ("有", 1.4, 1.6),
    ]
    assert derived["segments"][0]["anchors"]["order"] == {
        "start": words[2]["start"],
        "end": words[4]["end"],
        "units": [2, 5],
        "thought": 1,
    }
    assert derived["captions"] == []


def test_the_sample_films_derived_timelines_time_every_unit_of_its_thoughts():
    for code in ("zh", "en"):
        source = repository.read(Edition(code).script)
        derived = anchors.derived_timeline(source, code)
        previous_end = 0.0
        for timed, scripted in zip(derived["segments"], source["segments"], strict=True):
            assert {key: timed[key] for key in scripted} == scripted
            spoken = "".join(units(word["text"]) for word in timed["words"])
            assert spoken == units(scripted["text"])
            assert timed["start"] == previous_end and timed["voice_start"] == timed["start"] + 1.0
            # Thoughts are 0.5 s apart; words within one follow each other.
            gaps = {round(b["start"] - a["end"], 3) for a, b in pairwise(timed["words"])}
            assert gaps <= {0.0, 0.5}
            previous_end = timed["end"]
        assert derived["duration"] == derived["segments"][-1]["end"] + derived["credits_duration"]
        assert derived["captions"] == []


# A composition that reads `order` in segment 03 of each edition and `fails` in segment 26 of the
# Chinese one alone; THROWS makes segment 03 throw once it has read `order`.
COMPOSITION = """var P = {};
const film = window.FILM;
const scenes = {
  "03": (s) => { s.anchors.order.start; THROWS },
  "26": (s) => (film.edition === "zh" ? s.anchors.fails.start : 0),
};
window.renderFrame = (t) => {
  const s = film.segments.find((v) => v.start <= t && t < v.end);
  if (s) { window.__sceneId = s.id; scenes[s.id](s); window.__sceneId = null; }
  window.__filmLayout = { time: t, texts: [] };
};
"""


@pytest.fixture
def drawing(editions, tmp_path, monkeypatch):
    """The two editions with a composition and the canvas package, narration's words checks
    passing, and a model loader that records each step it would start."""
    for check in ("concepts", "register"):
        monkeypatch.setattr(getattr(narrate, check), "check", lambda: {})
    monkeypatch.setattr(narrate.readings, "check", lambda code: {})
    package = {"name": renderer.RENDERER_NAME, "version": renderer.RENDERER_VERSION}
    put(tmp_path / "node_modules" / renderer.RENDERER_PACKAGE, package)
    (tmp_path / "picture").mkdir()
    (tmp_path / "picture/film.js").write_text(COMPOSITION.replace("THROWS", ""))
    started = []
    monkeypatch.setattr(
        narrate.child_processes, "run", lambda command, **_: started.append(command)
    )
    return started


@pytest.mark.parametrize("mode", [["--dry-run"], []])
def test_narration_refuses_an_anchor_the_english_picture_reads_and_its_script_lacks(
    drawing, editions, tmp_path, mode
):
    english = editions["en"]
    english["segments"][0] = segment("03", "There is an order.")
    put(tmp_path / Edition("en").script, english)
    with pytest.raises(SystemExit, match="Narration refused before synthesis") as refused:
        narrate.main(["--language", "zh", *mode])
    assert "en 03 order: the en picture reads it from segment 03" in str(refused.value)
    assert "zh 03" not in str(refused.value) and "26" not in str(refused.value)
    assert drawing == []


def test_an_anchor_one_editions_picture_reads_is_asked_of_that_edition_alone(drawing, capsys):
    # Only the Chinese script marks `fails`, which only the Chinese picture reads.
    narrate.main(["--language", "en", "--dry-run"])
    gate = json.loads(capsys.readouterr().out.splitlines()[0])["gate"]
    assert gate["picture_reads"] == {
        "verdict": "pass",
        "not_judged": {"zh": [], "en": []},
        "not_loaded": {},
    }
    assert len(drawing) == 1


def test_a_scene_that_throws_is_named_as_not_judged_and_narration_goes_on(
    drawing, tmp_path, capsys
):
    thrown = COMPOSITION.replace("THROWS", 'throw Error("Missing spoken cue 03:依据");')
    (tmp_path / "picture/film.js").write_text(thrown)
    narrate.main(["--language", "zh", "--dry-run"])
    judged = json.loads(capsys.readouterr().out.splitlines()[0])["gate"]["picture_reads"]
    scene = {"scene": "03", "segment": "03", "error": "Missing spoken cue 03:依据", "from": 0}
    scene["reads"] = ["order"]
    assert judged["not_judged"]["zh"] == [scene]
    assert judged["verdict"] == "not judged"
    assert len(drawing) == 1


def test_an_unmarked_id_a_scene_reads_before_it_throws_is_refused(drawing, tmp_path):
    thrown = 's.anchors.missing.start; throw Error("Missing spoken cue 03:依据");'
    (tmp_path / "picture/film.js").write_text(COMPOSITION.replace("THROWS", thrown))
    with pytest.raises(SystemExit, match="zh 03 missing: the zh picture reads it"):
        narrate.main(["--language", "zh", "--dry-run"])
    assert drawing == []


def test_the_reads_tool_takes_its_step_from_the_check(drawing, editions, tmp_path):
    put(tmp_path / "zh.json", anchors.derived_timeline(editions["zh"], "zh"))
    out = tmp_path / "reads.json"
    assert tools.run("anchor-reads", [str(tmp_path / "zh.json")], stdout=out) == 2


def test_a_composition_that_does_not_load_is_not_judged_and_narration_goes_on(
    drawing, tmp_path, capsys
):
    # Both editions' scripts mark anchors; the composition throws as it loads.
    (tmp_path / "picture/film.js").write_text('throw Error("broken\\nwhile it loads");')
    narrate.main(["--language", "zh", "--dry-run"])
    judged = json.loads(capsys.readouterr().out.splitlines()[0])["gate"]["picture_reads"]
    assert judged["verdict"] == "not judged"
    loaded = "The composition does not load: broken"
    assert judged["not_loaded"] == {"zh": loaded, "en": loaded}
    assert len(drawing) == 1


def test_a_check_whose_packages_are_missing_refuses_with_its_reason(drawing, tmp_path):
    (tmp_path / "node_modules" / renderer.RENDERER_PACKAGE).unlink()
    with pytest.raises(SystemExit, match=f"cannot draw it: .*no {renderer.RENDERER_NAME}"):
        narrate.main(["--language", "zh", "--dry-run"])
    assert drawing == []


def test_a_film_without_a_composition_is_not_asked(drawing, tmp_path):
    (tmp_path / "picture/film.js").unlink()
    assert narrate.gate("zh")["picture_reads"] == anchor_reads.NOT_ASKED
