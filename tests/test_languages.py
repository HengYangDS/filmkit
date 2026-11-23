"""The engine's language declarations: each loaded with its values, refused when it misses or adds a
field or names a kind the engine does not hold, and the test languages equal to theirs but for
their codes, tags and names."""

import re
from pathlib import Path

import derived_languages
import pytest

import filmkit.languages as languages
from filmkit.delivery.player import WORDS

REPOSITORY = Path(__file__).resolve().parents[1]
BREAKS = REPOSITORY / "src/filmkit/picture/frame-audit/typography/breaks.mjs"


def test_the_engine_declares_chinese_and_english():
    assert sorted(languages.LANGUAGES) == ["en", "zh"]


def test_chinese_holds_the_values_of_its_table():
    zh = languages.language("zh")
    assert (zh.code, zh.tag, zh.iso639_2, zh.english_name, zh.name) == (
        "zh",
        "zh-CN",
        "zho",
        "Chinese",
        "中文",
    )
    assert zh.byline.format(minutes=1) == "1 分钟"
    assert (zh.scripts, zh.embedded, zh.spaced, zh.unit) == (
        ("han",),
        {"latin": "en"},
        False,
        "characters",
    )
    assert zh.number.kind == "counted-by-words"
    assert zh.number.singular == "一"
    assert (zh.captions.phrasing, zh.captions.limit) == ("full-width-punctuation", 33)
    assert (zh.captions.reading_rate, zh.captions.hold) == ("none", "none")
    assert (zh.readings, zh.stemmer, zh.lead_words) == (("pinyin-readings",), "none", ())
    assert "contractions" not in zh.rules and "colloquial" in zh.rules


def test_english_holds_the_values_of_its_table():
    en = languages.language("en")
    assert (en.code, en.tag, en.iso639_2, en.english_name, en.name) == (
        "en",
        "en",
        "eng",
        "English",
        "English",
    )
    assert en.byline.format(minutes=1) == "1 min"
    assert (en.scripts, en.embedded, en.spaced, en.unit) == (("latin",), {}, True, "words")
    assert (en.number.kind, en.number.suffixes) == ("plural-suffix", ("s", "es"))
    assert (en.captions.phrasing, en.captions.limit) == ("english-grammar", 66)
    assert (en.captions.reading_rate, en.captions.hold) == (25, "full-interval")
    assert (en.readings, en.stemmer) == (("cmudict-stress",), "snowball-english")
    assert "colloquial" not in en.rules and "contractions" in en.rules


def test_the_lead_words_are_those_the_frame_audit_names():
    listed = re.search(r"LEAD_WORDS = new Set\(\s*\((.*?)\)\.split", BREAKS.read_text(), re.S)
    words = "".join(re.findall(r'"([^"]*)"', listed.group(1))).split(" ")
    assert languages.language("en").lead_words == tuple(words)


@pytest.mark.parametrize("code", ["zh", "en"])
def test_the_player_words_are_those_of_the_player_page(code):
    page = {key: value for key, value in WORDS[code].items() if key not in ("lang", "language")}
    assert languages.language(code).player.model_dump() == page
    assert (WORDS[code]["lang"], WORDS[code]["language"]) == (
        languages.language(code).tag,
        languages.language(code).name,
    )


@pytest.mark.parametrize(("code", "source"), [("xa", "zh"), ("xb", "en")])
def test_a_test_language_equals_its_source_but_for_its_code_tags_and_names(code, source):
    derived, held = derived_languages.derived(code), languages.language(source)
    replaced = {"code", "tag", "iso639_2", "english_name", "name"}
    assert derived.model_dump(exclude=replaced) == held.model_dump(exclude=replaced)
    assert (derived.code, derived.iso639_2) == (code, {"xa": "qaa", "xb": "qab"}[code])
    assert derived.tag != held.tag and derived.english_name != held.english_name


def test_the_fixture_declares_the_test_languages_beside_the_engines(test_languages):
    assert sorted(languages.LANGUAGES) == ["en", "xa", "xb", "zh"]
    assert languages.language("xa") == test_languages["xa"]


def test_a_code_without_a_declaration_is_refused_naming_the_declared_languages():
    with pytest.raises(languages.LanguageError) as refusal:
        languages.language("xq")
    assert str(refusal.value) == (
        "The engine holds no language declaration for 'xq'; it declares en, zh"
    )


def declared(**changes) -> dict:
    data = derived_languages.declaration("zh")
    for key, value in changes.items():
        if value is None:
            data.pop(key)
        else:
            data[key] = value
    return data


@pytest.mark.parametrize(
    ("data", "named"),
    [
        (declared(stemmer=None), "stemmer: Field required"),
        (declared(accent="none"), "accent: Extra inputs are not permitted"),
        (declared(code="zh"), "states code; its file's name is its code"),
        (
            declared(captions={**declared()["captions"], "phrasing": "japanese-kinsoku"}),
            "captions.phrasing: Input should be 'full-width-punctuation' or 'english-grammar'",
        ),
        (declared(readings=["ipa-readings"]), "readings.0: Input should be 'pinyin-readings'"),
        (declared(stemmer="snowball-german"), "stemmer: Input should be 'snowball-english'"),
        (declared(number={"kind": "dual"}), "number: Input tag 'dual' found using 'kind'"),
        (declared(scripts=["cyrillic"]), "scripts names cyrillic: the scripts are han, latin"),
        (declared(embedded={"han": "zh"}), "embedded names han, which is no other script"),
        (declared(register=["slang"]), "register names slang; the register holds address"),
    ],
)
def test_a_declaration_that_misses_adds_or_names_an_unknown_kind_is_refused(data, named):
    with pytest.raises(languages.LanguageError, match="^The language declaration xq.toml") as error:
        languages.parse("xq", data)
    assert named in str(error.value)


def test_a_folder_whose_language_reads_a_script_in_an_undeclared_one_is_refused(tmp_path):
    (tmp_path / "zh.toml").write_text((languages.FOLDER / "zh.toml").read_text())
    with pytest.raises(languages.LanguageError) as refusal:
        languages.load(tmp_path)
    assert str(refusal.value) == (
        "The language declaration zh.toml reads a script in en, which no declaration holds"
    )
