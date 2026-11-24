"""Exact script edits that keep the narration mirrors, spoken texts and retakes bound."""

import copy
import hashlib
import json

import pytest

import filmkit.narration.script_edits as narration_script_edits
import filmkit.repository as repository

OPEN_SPEC = {"display": "OpenSpec", "spoken": "Open Spec", "kind": "english-name"}


def retake(seed: int, text: str) -> dict:
    return {"seed": seed, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}


SCRIPT = {"01": ["第一句。", "第二句。"], "02": ["甲句。乙句。", "丙句。"]}
RETAKES = {
    "01": {"groups": {"1": retake(7, "第一句。"), "2": retake(5, "第二句。")}},
    "02": {"seed": 9228, "groups": {"2": retake(9, "丙句。")}},
}


def write_edits(root, edits: dict) -> None:
    (root / "edits.json").write_text(json.dumps(edits, ensure_ascii=False))


def test_edit_script_replaces_and_splits_thoughts_and_rebinds_retakes(
    tmp_path, write_edition, capsys
):
    paths = write_edition("zh", SCRIPT, RETAKES)
    write_edits(
        tmp_path,
        {"replace": {"zh": [["01.1", "第一", "首"]]}, "split": {"zh": [["02.1", "甲句。"]]}},
    )
    before = {name: path.read_bytes() for name, path in paths.items()}
    narration_script_edits.main(["--edits", "edits.json", "--dry-run"])
    planned = json.loads(capsys.readouterr().out)
    assert {name: path.read_bytes() for name, path in paths.items()} == before

    narration_script_edits.main(["--edits", "edits.json"])
    report = json.loads(capsys.readouterr().out)
    assert report["dry_run"] is False
    assert report["editions"] == planned["editions"]
    assert report["editions"] == {
        "zh": [
            {
                "segment": "01",
                "thoughts_before": 2,
                "thoughts_after": 2,
                "new_thoughts": [1],
                "retakes_moved": {"2": 5},
                "retakes_released": ["1"],
            },
            {
                "segment": "02",
                "thoughts_before": 2,
                "thoughts_after": 3,
                "new_thoughts": [1, 2],
                "retakes_moved": {"3": 9},
                "retakes_released": [],
            },
        ]
    }
    segments = repository.read(paths["script"])["segments"]
    assert [s["utterance_groups"] for s in segments] == [
        ["首句。", "第二句。"],
        ["甲句。", "乙句。", "丙句。"],
    ]
    assert [(s["text"], s["spoken_text"]) for s in segments] == [
        ("首句。第二句。", "首句。第二句。"),
        ("甲句。乙句。丙句。", "甲句。乙句。丙句。"),
    ]
    # The edit writes the script and the cast alone: the edition's folder holds no copy of its
    # narration.
    assert sorted(path.name for path in paths["script"].parent.iterdir()) == [
        "film-script.json",
        "voice-reference.json",
    ]
    assert repository.read(paths["cast"])["retakes"] == {
        "01": {"groups": {"2": retake(5, "第二句。")}},
        "02": {"seed": 9228, "groups": {"3": retake(9, "丙句。")}},
    }


def test_an_edited_segment_speaks_through_the_pronunciation_contract(tmp_path, write_edition):
    paths = write_edition("zh", SCRIPT, RETAKES, normalization=[OPEN_SPEC])
    write_edits(tmp_path, {"replace": {"zh": [["01.1", "第一", "OpenSpec "]]}})
    narration_script_edits.main(["--edits", "edits.json"])
    segment = repository.read(paths["script"])["segments"][0]
    assert segment["text"] == "OpenSpec 句。第二句。"
    assert segment["spoken_text"] == "Open Spec 句。第二句。"


@pytest.mark.parametrize(
    ("edits", "refusal"),
    [
        (
            {"replace": {"zh": [["01.1", "第一", "首"]], "en": [["01.1", "Two", "2"]]}},
            "en 01.1: phrase not found exactly once",
        ),
        ({"split": {"zh": [["01.2", "第二句。"]]}}, "zh 01.2: seam not found"),
        ({"replace": {"zh": [["01.3", "第", "首"]]}}, "zh 01.3: no such thought"),
        ({"replace": {"fr": []}}, "maps"),
    ],
)
def test_edit_script_refuses_without_writing_either_edition(
    tmp_path, write_edition, edits, refusal
):
    paths = [
        *write_edition("zh", SCRIPT, RETAKES).values(),
        *write_edition("en", {"01": ["One.", "Three."]}, {}).values(),
    ]
    write_edits(tmp_path, edits)
    before = [path.read_bytes() for path in paths]
    with pytest.raises(ValueError, match=refusal):
        narration_script_edits.main(["--edits", "edits.json"])
    assert [path.read_bytes() for path in paths] == before


def test_an_edit_returns_new_documents_and_leaves_its_inputs_unchanged():
    script = {
        "segments": [
            {
                "id": "02",
                "text": "甲句。乙句。丙句。",
                "spoken_text": "甲句。乙句。丙句。",
                "utterance_groups": ["甲句。乙句。", "丙句。"],
            }
        ]
    }
    cast = {"retakes": copy.deepcopy(RETAKES)}
    inputs = copy.deepcopy((script, cast))
    edited, recast, changed = narration_script_edits.edit(
        script,
        cast,
        [["02.2", "丙", "丁"]],
        [["02.1", "甲句。"]],
        contract={"normalization": []},
        code="zh",
    )
    assert (script, cast) == inputs
    assert edited["segments"][0]["utterance_groups"] == ["甲句。", "乙句。", "丁句。"]
    assert edited["segments"][0]["text"] == "甲句。乙句。丁句。"
    assert recast["retakes"]["02"] == {"seed": 9228, "groups": {}}
    assert changed == [
        {
            "segment": "02",
            "thoughts_before": 2,
            "thoughts_after": 3,
            "new_thoughts": [1, 2, 3],
            "retakes_moved": {},
            "retakes_released": ["2"],
        }
    ]


def apply(tmp_path, capsys, edits: dict) -> dict:
    """Apply an edits file and return its report of the Chinese edition."""
    write_edits(tmp_path, edits)
    narration_script_edits.main(["--edits", "edits.json"])
    return json.loads(capsys.readouterr().out)["editions"]


def segment_of(paths, sid: str) -> dict:
    return next(s for s in repository.read(paths["script"])["segments"] if s["id"] == sid)


def refused(tmp_path, paths, edits: dict, named: str) -> None:
    """An edits file refused by name, which writes no script or cast."""
    write_edits(tmp_path, edits)
    before = [path.read_bytes() for path in paths.values()]
    with pytest.raises(ValueError, match=named):
        narration_script_edits.main(["--edits", "edits.json"])
    assert [path.read_bytes() for path in paths.values()] == before


ANCHORED = {
    "03": ["依据{order}有先后{/order}。", "最先是{law}法律{/law}。"],
    "04": ["如果{reversible}后果是否可逆{/reversible}，就选{tier}轻量档{/tier}。"],
}


def test_a_rewording_outside_an_anchor_keeps_it_and_names_none(tmp_path, write_edition, capsys):
    paths = write_edition("zh", ANCHORED, {})
    report = apply(tmp_path, capsys, {"replace": {"zh": [["03.2", "最先是", "首先是"]]}})
    segment = segment_of(paths, "03")
    assert segment["anchored_groups"] == ["依据{order}有先后{/order}。", "首先是{law}法律{/law}。"]
    # The plain thoughts, the text and the spoken text are filled from them.
    assert segment["utterance_groups"] == ["依据有先后。", "首先是法律。"]
    assert segment["text"] == segment["spoken_text"] == "依据有先后。首先是法律。"
    moves = {key: value for key, value in report["zh"][0].items() if key.startswith("anchors_")}
    assert moves and not any(moves.values())


@pytest.mark.parametrize(
    ("old", "new", "after"),
    [
        ("轻量档", "低风险档", "{tier}低风险档{/tier}"),
        ("轻量", "低风险", "{tier}低风险档{/tier}"),
    ],
)
def test_a_rewording_of_an_anchors_words_keeps_it_on_them(
    tmp_path, write_edition, capsys, old, new, after
):
    paths = write_edition("zh", ANCHORED, {})
    report = apply(tmp_path, capsys, {"replace": {"zh": [["04.1", old, new]]}})
    assert after in segment_of(paths, "04")["anchored_groups"][0]
    assert report["zh"][0]["anchors_reworded"] == [
        {"id": "tier", "before": "轻量档", "after": "低风险档"}
    ]


def test_a_rewording_beyond_an_anchor_is_refused_unless_it_restates_it(
    tmp_path, write_edition, capsys
):
    paths = write_edition("zh", ANCHORED, {})
    beyond = {"replace": {"zh": [["04.1", "如果后果是否可逆", "或者后果"]]}}
    refused(tmp_path, paths, beyond, "zh 04.1: the replacement reaches beyond anchor reversible")
    restated = {
        "replace": {"zh": [["04.1", "如果后果是否可逆", "或者{reversible}后果{/reversible}"]]}
    }
    report = apply(tmp_path, capsys, restated)
    assert segment_of(paths, "04")["anchored_groups"][0].startswith(
        "或者{reversible}后果{/reversible}，"
    )
    assert report["zh"][0]["anchors_restated"] == ["reversible"]


def test_a_split_inside_an_anchor_is_refused_and_one_at_its_edge_keeps_it(
    tmp_path, write_edition, capsys
):
    paths = write_edition("zh", ANCHORED, {})
    refused(tmp_path, paths, {"split": {"zh": [["03.1", "依据有"]]}}, "inside anchor order")
    apply(tmp_path, capsys, {"split": {"zh": [["03.1", "依据"]]}})
    assert segment_of(paths, "03")["anchored_groups"][:2] == ["依据", "{order}有先后{/order}。"]


def test_a_refused_edit_among_several_writes_nothing(tmp_path, write_edition):
    paths = write_edition("zh", ANCHORED, {})
    edits = [["03.2", "最先是", "首先是"], ["04.1", "就选", "便选"], ["04.1", "如果后果", "若后果"]]
    refused(tmp_path, paths, {"replace": {"zh": edits}}, "reaches beyond anchor reversible")


def test_a_first_anchor_is_written_and_keeps_the_thoughts_and_their_retake(
    tmp_path, write_edition, capsys
):
    paths = write_edition("zh", SCRIPT, RETAKES)
    plain = {key: segment_of(paths, "01")[key] for key in ("utterance_groups", "text")}
    report = apply(tmp_path, capsys, {"anchor": {"zh": [["01.2", [1, 3], "second", "二句"]]}})
    segment = segment_of(paths, "01")
    assert segment["anchored_groups"] == ["第一句。", "第{second}二句{/second}。"]
    assert {key: segment[key] for key in plain} == plain
    assert segment["spoken_text"] == segment["text"]
    assert repository.read(paths["cast"])["retakes"]["01"] == RETAKES["01"]
    assert report["zh"][0]["anchors_marked"] == ["second"]


def test_an_anchor_edit_marks_its_span_with_the_marks_inside_it(tmp_path, write_edition, capsys):
    paths = write_edition("zh", {"05": ["工作计划、临时约定，再往下。"]}, {})
    apply(tmp_path, capsys, {"anchor": {"zh": [["05.1", [0, 8], "plans", "工作计划临时约定"]]}})
    assert segment_of(paths, "05")["anchored_groups"] == [
        "{plans}工作计划、临时约定{/plans}，再往下。"
    ]


@pytest.mark.parametrize(
    ("edits", "named"),
    [
        (
            {"anchor": {"zh": [["03.1", [1, 4], "rank", "有先后"]]}},
            "units 1-4 say 据有先, not 有先后",
        ),
        ({"anchor": {"zh": [["03.2", [3, 5], "law", "法律"]]}}, "zh 03 law: is marked already"),
        ({"unanchor": {"zh": [["03", "apart"]]}}, "zh 03 apart: is not marked"),
    ],
)
def test_marks_on_other_words_or_ids_are_refused(tmp_path, write_edition, edits, named):
    paths = write_edition("zh", ANCHORED, {})
    refused(tmp_path, paths, edits, named)


def test_an_unanchor_edit_removes_an_ids_marks(tmp_path, write_edition, capsys):
    paths = write_edition("zh", ANCHORED, {})
    report = apply(tmp_path, capsys, {"unanchor": {"zh": [["03", "order"], ["03", "law"]]}})
    # A segment left without a mark is plain again.
    assert "anchored_groups" not in segment_of(paths, "03")
    assert report["zh"][0]["anchors_removed"] == ["order", "law"]


def test_a_rewrite_moves_each_anchor_to_the_words_it_still_says(tmp_path, write_edition, capsys):
    thoughts = {"03": ["{law}法律{/law}在前，{apart}规章{/apart}在后。", "依据只有一条。"]}
    paths = write_edition("zh", thoughts, {})
    rewritten = ["先讲依据。", "最先是法律。"]
    refused(tmp_path, paths, {"rewrite": {"zh": [["03", rewritten]]}}, "zh 03 apart: 规章")
    restated = [rewritten[0], "最先是法律，{apart}其次{/apart}。"]
    report = apply(tmp_path, capsys, {"rewrite": {"zh": [["03", restated]]}})
    assert segment_of(paths, "03")["anchored_groups"] == [
        "先讲依据。",
        "最先是{law}法律{/law}，{apart}其次{/apart}。",
    ]
    assert report["zh"][0]["anchors_moved_to_another_thought"] == [
        {"id": "law", "words": "法律", "from": "03.1", "to": "03.2"}
    ]


def test_a_rewrite_moves_by_rank_or_names_new_occurrences(tmp_path, write_edition, capsys):
    paths = write_edition("zh", {"03": ["依据在先，{basis}依据{/basis}在后。"]}, {})
    twice = {"rewrite": {"zh": [["03", ["依据有二：", "一是依据甲，二是依据乙。"]]]}}
    refused(tmp_path, paths, twice, "zh 03 basis: 依据 is said 2 times before and 3 after")
    report = apply(
        tmp_path, capsys, {"rewrite": {"zh": [["03", ["一是依据甲，", "二是依据乙。"]]]}}
    )
    assert segment_of(paths, "03")["anchored_groups"] == [
        "一是依据甲，",
        "二是{basis}依据{/basis}乙。",
    ]
    # A move by rank into another thought is named among both kinds.
    assert [move["id"] for move in report["zh"][0]["anchors_moved_by_rank"]] == ["basis"]
    assert [m["to"] for m in report["zh"][0]["anchors_moved_to_another_thought"]] == ["03.2"]


def test_a_rewrite_with_new_occurrences_of_words_said_once_names_them(tmp_path, write_edition):
    paths = write_edition("zh", {"03": ["{basis}依据{/basis}在先。"]}, {})
    edits = {"rewrite": {"zh": [["03", ["依据在先，", "依据在后。"]]]}}
    refused(tmp_path, paths, edits, r"said 1 time before and 2 after, at 03\.1:0 and 03\.2:0")


def test_an_english_anchor_does_not_move_into_a_longer_word(tmp_path, write_edition, capsys):
    paths = write_edition("en", {"02": ["It was {night}last night{/night}."]}, {})
    edits = {"rewrite": {"en": [["02", ["It was last night's work."]]]}}
    refused(tmp_path, paths, edits, "en 02 night: last night is said 1 time before and 0 after")
    report = apply(tmp_path, capsys, {"rewrite": {"en": [["02", ["Since last night, work."]]]}})
    assert segment_of(paths, "02")["anchored_groups"] == ["Since {night}last night{/night}, work."]
    assert report["en"][0]["anchors_moved"] == [
        {"id": "night", "words": "last night", "from": "02.1", "to": "02.1"}
    ]


@pytest.mark.parametrize(
    ("thoughts", "named"),
    [
        ("一是依据甲。", "zh 03: a rewrite's thoughts are a nonempty list of strings"),
        ([], "zh 03: a rewrite's thoughts are a nonempty list of strings"),
        (["一是依据甲，", ""], "zh 03.2: a rewritten thought says no spoken unit"),
        (["一是依据甲，", "。"], "zh 03.2: a rewritten thought says no spoken unit"),
    ],
)
def test_a_rewrite_refuses_thoughts_that_say_nothing(tmp_path, write_edition, thoughts, named):
    paths = write_edition("zh", {"03": ["依据在先，{basis}依据{/basis}在后。"]}, {})
    refused(tmp_path, paths, {"rewrite": {"zh": [["03", thoughts]]}}, named)


def test_a_replacement_in_an_unknown_segment_is_refused_by_name(tmp_path, write_edition):
    paths = write_edition("zh", ANCHORED, {})
    refused(
        tmp_path, paths, {"replace": {"zh": [["99.1", "甲", "乙"]]}}, "zh 99.1: no such thought"
    )


@pytest.mark.usefixtures("test_languages")
def test_a_test_language_finds_words_at_their_edges_as_its_source():
    from filmkit.narration.anchors import Thought

    english = [Thought("It was last night's work, last night.", ())]
    chinese = [Thought("昨晚的工作，昨晚。", ())]
    assert narration_script_edits.occurrences(english, "last night", "xb") == (
        narration_script_edits.occurrences(english, "last night", "en")
    )
    assert (
        narration_script_edits.occurrences(chinese, "昨晚", "xa")
        == (narration_script_edits.occurrences(chinese, "昨晚", "zh"))
        == [(0, 0), (0, 5)]
    )
