"""The declared reading of every watched Chinese character, and every name's spoken form."""

import json
import shutil
from pathlib import Path

import pytest
from pypinyin import Style, pinyin

import filmkit.film as film_declaration
import filmkit.narration.readings as readings
import filmkit.repository as repository
from filmkit.narration.readings import Thought, Word


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A copy of the sample film's sources below a new root, and its pronunciation contract."""
    shutil.copytree(repository.ROOT / "content", tmp_path / "content")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    path = tmp_path / "content/voice-performance.json"

    def edit(change) -> None:
        performance = json.loads(path.read_text(encoding="utf-8"))
        change(performance["pronunciation"])
        path.write_text(json.dumps(performance, ensure_ascii=False, indent=2) + "\n")

    return tmp_path, edit


def test_every_watched_character_has_more_than_one_dictionary_reading():
    watched = readings.watch_list()
    assert {"重", "行", "只", "得", "为"} <= {
        char for char, kind in watched.items() if kind == "word"
    }
    assert {"还", "的", "了"} <= {char for char, kind in watched.items() if kind == "character"}
    for char in watched:
        assert len(set(readings.dictionary_readings(char))) > 1, char


def test_the_watch_list_ships_inside_the_package():
    package = Path(str(readings.__file__)).parent
    assert readings.WATCH_LIST.parent == package
    assert readings.WATCH_LIST.is_file()


@pytest.mark.parametrize(
    ("term", "reading", "expected"),
    [
        ("重新", "chóngxīn", ("chóng", "xīn")),
        ("重新", "chóng xīn", ("chóng", "xīn")),
        ("去重", "Qù Chóng", ("qù", "chóng")),
        ("还是", "hái shi", ("hái", "shi")),
        ("还是", "háishi", ("hái", "shi")),
        ("还是", "hai shì", None),
        ("重新", "chongxin", None),
        ("重新", "chóng xīn yī", None),
        ("重a", "chóng a", None),
    ],
)
def test_a_declared_reading_divides_into_dictionary_readings(term, reading, expected):
    assert readings.syllables(term, reading) == expected


def test_contextual_readings_follow_each_run_of_han_characters():
    assert readings.contextual("ETHOS 重新编译") == {6: "chóng", 7: "xīn", 8: "biān", 9: "yì"}


def test_a_watched_character_without_a_declared_word_refuses():
    thought = Thought("04.2", "按股票代码和日期去重。")
    rows, failures = readings.resolve([thought], [Word("重", ("chóng",), None)])
    assert rows == []
    assert failures == [
        "zh 04.2 at 5: 和 in “按股票代码和日期去重。” has no declared reading; "
        "the dictionary reads it hé here",
        "zh 04.2 at 9: 重 in “代码和日期去重。” has no declared reading; "
        "the dictionary reads it zhòng here",
    ]


def test_a_declared_reading_the_dictionary_contradicts_needs_its_reason():
    thought = Thought("04.2", "按股票代码和日期去重。")
    words = [Word("和", ("hé",), None), Word("去重", ("qù", "chóng"), None)]
    assert readings.resolve([thought], words)[1] == [
        "zh 04.2 at 9: 重 in “代码和日期去重。” is declared chóng by 去重, "
        "the dictionary reads zhòng; record why in dictionary_disagreement or declare the word"
    ]
    words[1] = Word(
        "去重", ("qù", "chóng"), "去重 deduplicates; the dictionary reads it as weight."
    )
    rows, failures = readings.resolve([thought], words)
    assert failures == []
    assert rows[1] == {
        "thought": "04.2",
        "position": 9,
        "character": "重",
        "word": "去重",
        "word_start": 8,
        "reading": "chóng",
        "dictionary": "zhòng",
        "class": "word",
        "context": "代码和日期去重。",
    }


def test_a_single_character_never_covers_a_word_the_dictionary_reads_otherwise():
    thought = Thought("01.1", "还原数据。")
    words = [Word("还", ("hái",), None), Word("数据", ("shù", "jù"), None)]
    assert readings.resolve([thought], words)[1] == [
        "zh 01.1 at 0: 还 in “还原数据。” is declared hái by 还, the dictionary reads huán; "
        "record why in dictionary_disagreement or declare the word"
    ]
    words.append(Word("还原", ("huán", "yuán"), None))
    assert readings.resolve([thought], words)[1] == [
        "还 is declared but the Chinese narration never says it"
    ]


def test_stale_declarations_refuse():
    thought = Thought("01.1", "数据。")
    words = [
        Word("数据", ("shù", "jù"), "No disagreement here."),
        Word("行情", ("háng", "qíng"), None),
    ]
    assert readings.resolve([thought], words)[1] == [
        "行情 is declared but the Chinese narration never says it",
        "数据 records a dictionary disagreement that no occurrence has",
    ]


def test_declared_words_refuse_readings_repeats_and_single_character_reasons():
    contract = {
        "targets": [
            {"term": "重新", "kind": "contextual-mandarin-word", "target_reading": "chóngxīn"},
            {"term": "重新", "kind": "contextual-mandarin-word", "target_reading": "chóngxīn"},
            {"term": "行情", "kind": "contextual-mandarin-word", "target_reading": "xíngqíngg"},
            {
                "term": "得",
                "kind": "contextual-mandarin-word",
                "target_reading": "děi",
                "dictionary_disagreement": "must",
            },
            {"term": "lead", "kind": "lexical"},
        ]
    }
    words, failures = readings.declared_words(contract)
    assert words == [Word("重新", ("chóng", "xīn"), None)]
    assert failures == [
        "重新 is declared more than once",
        "行情 xíngqíngg: not one dictionary reading per character",
        "得: a single character cannot record a dictionary disagreement",
    ]


def test_proposals_cover_each_unresolved_occurrence_with_the_dictionarys_word():
    thoughts = [Thought("01.1", "按股票代码和日期去重。"), Thought("02.1", "先去重，再核对。")]
    assert readings.proposals(thoughts, []) == [
        {
            "term": "去重",
            "target_reading": "qù zhòng",
            "occurrences": 2,
            "said_in": ["01.1", "02.1"],
        },
        {"term": "和", "target_reading": "hé", "occurrences": 1, "said_in": ["01.1"]},
    ]
    declared = [Word("去重", ("qù", "chóng"), "去重 deduplicates.")]
    assert [row["term"] for row in readings.proposals(thoughts, declared)] == ["和"]


def test_a_word_character_is_widened_to_a_dictionary_phrase_or_its_predecessor():
    assert readings.widened("只是数据。", 0) == (0, 2)
    assert readings.widened("做得更好。", 1) == (0, 2)
    assert readings.widened("得", 0) == (0, 1)


def test_the_cli_proposes_without_changing_the_contract(film, capsys):
    root, edit = film
    path = root / "content/voice-performance.json"

    def drop_a_word(pronunciation):
        pronunciation["languages"]["Chinese"]["targets"] = [
            target
            for target in pronunciation["languages"]["Chinese"]["targets"]
            if target["term"] != "参考"
        ]

    edit(drop_a_word)
    before = path.read_bytes()
    readings.main(["--propose"])
    assert json.loads(capsys.readouterr().out)["proposals"] == 1
    written = json.loads((root / readings.PROPOSALS).read_text(encoding="utf-8"))
    assert written["rows"] == [
        {"term": "参考", "target_reading": "cān kǎo", "occurrences": 1, "said_in": ["01.2"]}
    ]
    assert path.read_bytes() == before


def test_names_need_one_declared_spoken_form():
    zh = [Thought("01.1", "一个 Agent 交回来。"), Thought("05.1", "GitLab 和 GitHub 上。")]
    assert readings.undeclared_names(zh, {"Agent", "GitHub"}, chinese=True) == [
        "GitLab has no declared spoken form; it is said in 05.1"
    ]
    en = [Thought("03.1", "ETHOS keeps One OpenSpec Change. Then ETHOS checks.")]
    assert readings.undeclared_names(en, {"ETHOS"}, chinese=False) == [
        "OpenSpec has no declared spoken form; it is said in 03.1"
    ]


def test_the_sample_film_resolves_every_reading_and_writes_its_plans(film):
    root, _edit = film
    zh = readings.check("zh")
    assert zh["schema_version"] == readings.SCHEMA
    assert zh["occurrences"] == 38
    plan = json.loads((root / readings.plan_path("zh")).read_text(encoding="utf-8"))
    assert plan["occurrences"] == len(plan["rows"]) == 38
    match = next(row for row in plan["rows"] if row["word"] == "得上")
    assert (match["reading"], match["dictionary"]) == ("de", "dé")
    assert readings.check("en")["occurrences"] == 0
    assert (root / readings.plan_path("en")).is_file()


def test_the_chinese_contract_lists_its_names_as_terms(film):
    root, edit = film
    path = root / "content/film-script.json"
    script = json.loads(path.read_text(encoding="utf-8"))
    segment = script["segments"][2]
    groups = segment["utterance_groups"]
    groups[0] = groups[0].replace("接着渲染", "接着用 HyperFrames 渲染")
    segment["text"] = segment["spoken_text"] = "".join(groups)
    path.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    edit(lambda contract: contract["languages"]["Chinese"].update(embedded_english_targets=[]))
    refusal = "HyperFrames has no declared spoken form; it is said in 03.1"
    with pytest.raises(readings.ReadingError, match=refusal):
        readings.check("zh")
    names = ["HyperFrames"]
    edit(lambda contract: contract["languages"]["Chinese"].update(embedded_english_targets=names))
    assert readings.check("zh")["occurrences"] == 38


def test_a_version_1_contract_is_not_checked(film):
    root, edit = film

    def first_version(pronunciation):
        pronunciation["schema_version"] = 1
        pronunciation["languages"]["Chinese"]["targets"] = []

    edit(first_version)
    assert readings.check("zh")["status"] == "not_applicable"
    assert not (root / readings.plan_path("zh")).exists()


def test_the_cli_refuses_with_every_edition_failure(film, capsys):
    _root, edit = film
    readings.main(["--language", "zh"])
    assert json.loads(capsys.readouterr().out)[0]["edition"] == "zh"

    def drop_a_word(pronunciation):
        pronunciation["languages"]["Chinese"]["targets"] = [
            target
            for target in pronunciation["languages"]["Chinese"]["targets"]
            if target["term"] != "参考"
        ]
        pronunciation["languages"]["English"]["targets"] = []

    edit(drop_a_word)
    with pytest.raises(SystemExit, match="readings: zh: zh 01.2 at 9: 参"):
        readings.main([])


def test_dictionary_readings_match_pypinyin():
    assert readings.dictionary_readings("重") == pinyin("重", style=Style.TONE, heteronym=True)[0]


def test_a_declared_term_is_spelled_alike_and_its_reference_is_in_the_text(film, monkeypatch):
    root, edit = film
    path = root / "content/film-script.json"
    script = json.loads(path.read_text(encoding="utf-8"))
    segment = script["segments"][2]
    segment["utterance_groups"][0] = segment["utterance_groups"][0].replace(
        "接着渲染", "接着用 HyperFrames 渲染"
    )
    segment["text"] = segment["spoken_text"] = "".join(segment["utterance_groups"])
    path.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    edit(
        lambda contract: contract["languages"]["Chinese"].update(
            embedded_english_targets=["HyperFrames"]
        )
    )

    def declare(**reference) -> None:
        term = film_declaration.NarrationTerm(
            term="HyperFrames", spoken="HyperFrames", ipa="ˈhaɪpərfreɪmz", reference=reference
        )
        narration = film_declaration.Narration(terms=(term,))
        monkeypatch.setattr(
            readings, "FILM", film_declaration.FILM.model_copy(update={"narration": narration})
        )

    def spell(chinese: str, english: str) -> None:
        def spelled(contract) -> None:
            for language, spoken in (("Chinese", chinese), ("English", english)):
                rule = {"display": "HyperFrames", "spoken": spoken, "kind": "english-name"}
                contract["languages"][language]["normalization"] = [rule]

        edit(spelled)

    declare(zh={"thought": "03.1", "index": 0})
    # Every language's normalization must give the term its declared spoken form.
    with pytest.raises(readings.ReadingError) as refusal:
        readings.check("en")
    assert str(refusal.value).splitlines() == [
        f"content/voice-performance.json: the {language} normalization gives HyperFrames no "
        "spoken form; the film declares HyperFrames in [[narration.terms]]"
        for language in ("Chinese", "English")
    ]
    spell("HyperFrames", "HyperFrames")
    assert readings.check("zh")["occurrences"] == 38
    assert readings.check("en")["occurrences"] == 0
    spell("HyperFrames", "Hyperframes")
    other = "the English normalization gives HyperFrames the spoken form Hyperframes"
    with pytest.raises(readings.ReadingError, match=other):
        readings.check("zh")
    # The contract's schema version does not spare a term its spelling.
    edit(lambda contract: contract.update(schema_version=1))
    with pytest.raises(readings.ReadingError, match=other):
        readings.check("zh")
    edit(lambda contract: contract.update(schema_version=readings.SCHEMA))
    spell("HyperFrames", "HyperFrames")
    declare(zh={"thought": "03.1", "index": 1})
    with pytest.raises(readings.ReadingError, match="03.1 #1 is not in the narration; 03.1 says"):
        readings.check("zh")
    declare(zh={"thought": "03.1", "index": 0}, en={"thought": "03.1", "index": 0})
    with pytest.raises(readings.ReadingError, match="reference for en, but the narration never"):
        readings.check("en")
