"""The register check: the film's exceptions, and the forms it refuses wherever a viewer meets a
film's words."""

import json
import re
import runpy
import shutil
from pathlib import Path

import pytest
import yaml
from placing import KEEP, STANDARD, listed, placed, refused, refused_lines
from pydantic import ValidationError

import filmkit.concepts as concepts
import filmkit.film as film
import filmkit.register as register
import filmkit.released as released
import filmkit.repository as repository
from filmkit.production import Edition
from filmkit.register import RegisterError

# The engine's base style.
STYLE = Path(register.__file__).with_name("styles") / "register"
# The inflections of the standard's listed forms that the style refuses beside them.
INFLECTIONS = ("yours", "yourself", "yourselves")
COLLOQUIAL, ADDRESS = "is colloquial (R3)", "addresses the audience (R1)"
# A quotation a film keeps at one place, as its declaration states it.
QUOTED = {"place": "zh 01.1", "form": "搞", "within": "先搞清楚", "reason": "a quoted remark"}


def with_register(*exceptions: dict) -> film.Film:
    """The sample film declaring these register exceptions, as the declaration is loaded."""
    return film.Film.model_validate(
        {**film.FILM.model_dump(by_alias=True), "register": {"exceptions": list(exceptions)}}
    )


def test_the_sample_film_passes_and_its_review_asks_for_the_formal_register():
    # The sample's words hold nothing the check refuses or reports, and it declares nothing.
    report = register.check()
    assert (report["warnings"], report["excused"]) == ([], [])
    # Its two declarations of language ask for the standard's register: the dimension that
    # scores each edition's language, and the level that holds it.
    review, asked = film.FILM.review, "formal standard written language"
    assert asked in review.dimensions["language_quality"]
    assert asked in review.levels["雅"].asks
    assert "language_quality" in review.levels["雅"].dimensions
    # Its template cites the field that carries the report and the rules to the reviewers.
    template = (repository.ROOT / review.prompt).read_text(encoding="utf-8")
    assert "{register}" in template


def test_a_film_excuses_a_form_within_a_text_and_one_without_register_keeps_none():
    # The sample declares no [register]: the engine's style holds with no exception.
    assert film.FILM.formal_register == film.Register()
    (kept,) = with_register(QUOTED).formal_register.exceptions
    assert (kept.place, kept.form, kept.within, kept.reason) == tuple(QUOTED.values())
    # One form at one place may stand within two texts.
    assert len(with_register(QUOTED, {**QUOTED, "within": "别搞"}).formal_register.exceptions) == 2


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ({"reason": " "}, r"register\.exceptions\.0\.reason"),
        ({"form": ""}, r"register\.exceptions\.0\.form"),
        ({"within": ""}, r"register\.exceptions\.0\.within"),
        ({"within": "帮我做好"}, "'帮我做好' is no text the form stands within: it must hold '搞'"),
        ({"count": 1}, r"register\.exceptions\.0\.count"),
    ],
)
def test_a_malformed_exception_refuses_naming_its_field(change, refusal):
    with pytest.raises(ValidationError, match=refusal):
        with_register({**QUOTED, **change})


# Texts a form stands within: whether a film may declare them, by what they add to the form.
TEXTS = [
    ("吧", "吧。", False),
    ("其实", "，其实", False),
    ("你", "「你」", False),
    ("you", "you.", False),
    ("搞", "搞", False),
    ("其实", "名副其实", True),
    ("搞", "先搞清楚", True),
    ("you", "thank-you note", True),
    ("!", "Yahoo! Inc.", True),
    ("-", "10 - 2", True),
]


@pytest.mark.parametrize(("form", "within", "declared"), TEXTS)
def test_a_text_must_add_a_letter_or_a_digit_to_its_form(form, within, declared):
    exception = {"place": "zh 01.1", "form": form, "within": within, "reason": "a case"}
    if declared:
        assert with_register(exception).formal_register.exceptions[0].within == within
    else:
        said = f"{within!r} is no text the form stands within: it must hold {form!r} and a letter"
        with pytest.raises(ValidationError, match=re.escape(said)):
            with_register(exception)


def test_two_exceptions_of_one_form_within_one_text_at_one_place_refuse():
    with pytest.raises(ValidationError, match="two exceptions name the same form within one text"):
        with_register(QUOTED, {**QUOTED, "reason": "again"})
    # A text that another declared text of the same form and place holds adds nothing.
    idiom = {"place": "zh title", "form": "其实", "within": "名副其实", "reason": "an idiom"}
    said = (
        "two exceptions of '其实' at zh title name '名副其实' and '副其实', and one holds the other"
    )
    with pytest.raises(ValidationError, match=re.escape(said)):
        with_register(idiom, {**idiom, "within": "副其实"})


@pytest.fixture
def words(tmp_path, monkeypatch):
    """A copy of the sample film's content below a new root, whose words a test rewrites."""
    shutil.copytree(repository.ROOT / "content", tmp_path / "content")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    return tmp_path


def say(root, code: str, *thoughts: str, title: str | None = None) -> None:
    """Rewrite the first thoughts of an edition's first segment, and its title if given."""
    path = root / Edition(code).script
    script = json.loads(path.read_text(encoding="utf-8"))
    first = script["segments"][0]
    first["utterance_groups"][: len(thoughts)] = thoughts
    first["text"] = "".join(first["utterance_groups"])
    script["title"] = script["title"] if title is None else title
    path.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def refusal(*lines: str) -> None:
    """The lines with which the check refuses the film's words."""
    assert refused_lines() == list(lines)


def test_errors_refuse_naming_every_place_and_warnings_are_returned(words):
    say(words, "zh", "你们先看，迷你主机为家庭供电。")
    say(words, "en", "We read it, and you see it.")
    refusal(f"zh 01.1: '你们' {ADDRESS}", f"zh 01.1: '你' {ADDRESS}", f"en 01.1: 'you' {ADDRESS}")
    say(words, "zh", "先看，主机为家庭供电。")
    say(words, "en", "We read it.")
    report = register.check()
    assert sorted(report) == ["excused", "places", "vale", "warnings"]
    assert report["vale"] == released.vale()
    assert report["places"] == sum(len(held) for held in concepts.places().values())
    assert report["excused"] == []
    assert report["warnings"] == [
        {
            "place": "en 01.1",
            "form": "We",
            "rule": "register.we",
            "message": "'We' is a first person plural: only for a party the film has named (R2)",
        }
    ]


def test_the_check_reads_the_entry_page_and_the_caption_terms(words, monkeypatch):
    page = words / concepts.FILM.entry
    page.write_text(
        page.read_text(encoding="utf-8").replace("从源文件到成片", "你们从源文件到成片")
    )
    en = concepts.FILM.editions["en"]
    terms = en.model_copy(update={"caption_terms": (*en.caption_terms, "your build")})
    editions = {**concepts.FILM.editions, "en": terms}
    monkeypatch.setattr(concepts, "FILM", concepts.FILM.model_copy(update={"editions": editions}))
    refusal(
        f"en caption term 'your build': 'your' {ADDRESS}",
        f"entry page: '你们' {ADDRESS}",
    )


def test_a_place_is_one_paragraph_whose_lines_join_by_their_script(words):
    # Chinese lines join by nothing and Latin lines by a space.
    say(words, "zh", "其\n实不难。", "大家\n看。")
    say(words, "en", "Your\nself.")
    refusal(
        f"zh 01.1: '其实' {COLLOQUIAL}", f"zh 01.2: '大家' {ADDRESS}", f"en 01.1: 'Your' {ADDRESS}"
    )


@pytest.mark.parametrize(
    ("chinese", "english"),
    [("{form}。", "{form}."), ("他说{form}就好。", "Then {form} stand here.")],
)
def test_every_form_the_standard_lists_is_refused(monkeypatch, chinese, english):
    zh, en = listed()
    assert {"你们", "其实", "呀"} <= set(zh)
    assert en == ["you", "your", "doesn't"]
    texts = [chinese.format(form=form) for form in zh] + [english.format(form=form) for form in en]
    placed(monkeypatch, *texts)
    lines = refused_lines()
    for index, form in enumerate(zh + en, 1):
        assert any(line.startswith(f"zh 01.{index}: '{form}' ") for line in lines), form


def test_every_error_of_the_r1_and_r3_rules_is_a_listed_form_or_its_inflection(monkeypatch):
    rules = [
        yaml.safe_load((STYLE / f"{name}.yml").read_text()) for name in ("address", "colloquial")
    ]
    lines = [line for rule in rules for case in rule["tests"] for line in case["input"].split("\n")]
    zh, en = listed()
    allowed = {form.casefold() for form in (*zh, *en, *INFLECTIONS)}
    placed(monkeypatch, *filter(None, lines))
    either = f"(?:{re.escape(ADDRESS)}|{re.escape(COLLOQUIAL)})"
    said = [re.fullmatch(rf"zh 01\.\d+: '(.+)' {either}", line) for line in refused_lines()]
    forms = {found[1] for found in said if found}
    assert forms
    assert sorted(form for form in forms if form.casefold() not in allowed) == []


def test_the_rules_of_a_class_quote_the_sentence_of_the_standard_they_render():
    standard = " ".join(re.sub(r"\*\*", "", STANDARD.read_text(encoding="utf-8")).split())
    for name in ("contractions", "marks"):
        lines = (STYLE / f"{name}.yml").read_text(encoding="utf-8").splitlines()
        quoted = " ".join(line[len("#   > ") :] for line in lines if line.startswith("#   > "))
        assert quoted, name
        assert " ".join(quoted.split()) in standard, name


def test_the_rules_the_reviewers_read_are_the_standards_own_lines(tmp_path, monkeypatch):
    document = STANDARD.read_text(encoding="utf-8")
    rules = register.rules()
    # Its lines from R1 to the document's end, as they stand there, and nothing restated.
    assert document.endswith(rules)
    assert rules.startswith("- **R1. The film does not address its audience.**")
    assert re.findall(r"^- \*\*(R\d)\. ", rules, re.M) == ["R1", "R2", "R3", "R4", "R5", "R6"]
    # A document that no longer states one of the six is refused by name, never cut short.
    short = tmp_path / "standard.md"
    short.write_text(document.replace("- **R4. ", "- **Fourth. "), encoding="utf-8")
    monkeypatch.setattr(register, "_STANDARD", short)
    with pytest.raises(RegisterError) as refusal:
        register.rules()
    assert str(refusal.value) == (
        f"The engine's standard at {short} states the rules R1, R2, R3, R5, R6, not R1 to R6; "
        "install the engine again"
    )
    short.unlink()
    with pytest.raises(RegisterError, match="cannot be read: .*install the engine again"):
        register.rules()


# One form of each rule of the base style, and whether the rule refuses it or reports it.
LEVELS = {
    "address": ("你们先看。", "你们", "error"),
    "audience": ("各位请看。", "各位", "warning"),
    "colloquial": ("再搞一次。", "搞", "error"),
    "contractions": ("It doesn't.", "doesn't", "error"),
    "informal": ("到底怎么样。", "到底", "warning"),
    "marks": ("Stop!", "!", "error"),
    "questions": ("为什么？又如何？", "？", "warning"),
    "we": ("我们先看。", "我们", "warning"),
}


def test_every_rule_of_the_style_has_its_level_stated():
    assert sorted(LEVELS) == sorted(path.stem for path in STYLE.glob("*.yml"))


@pytest.mark.parametrize("rule", sorted(LEVELS))
def test_each_rule_refuses_or_reports_at_its_level(monkeypatch, rule):
    text, form, level = LEVELS[rule]
    placed(monkeypatch, text)
    if level == "error":
        message = yaml.safe_load((STYLE / f"{rule}.yml").read_text(encoding="utf-8"))["message"]
        refusal(f"zh 01.1: {message % form}")
    else:
        (warning,) = register.check()["warnings"]
        assert (warning["place"], warning["form"], warning["rule"]) == (
            "zh 01.1",
            form,
            f"register.{rule}",
        )


def test_a_form_is_excused_within_its_declared_text_and_nowhere_else(words, monkeypatch):
    monkeypatch.setattr(register, "FILM", with_register(QUOTED))
    say(words, "zh", "「先搞清楚」是一个例子。")
    assert register.check()["excused"] == [QUOTED]
    say(words, "zh", "「先搞清楚」是一个例子，不要再搞。")
    refusal(f"zh 01.1: '搞' {COLLOQUIAL}")
    say(words, "zh", "这是一个例子，不要再搞。")
    refusal(
        f"zh 01.1: '搞' {COLLOQUIAL}",
        "The register exception of '搞' at zh 01.1 is stale: the place does not hold '先搞清楚'",
    )


def test_a_standard_word_is_refused_until_the_film_declares_it(words, monkeypatch):
    say(words, "zh", title="示例跑道")
    refusal = refused()
    assert str(refusal).splitlines() == [f"zh title: '跑' {COLLOQUIAL}", KEEP]
    assert list(refusal.lines) == [f"zh title: '跑' {COLLOQUIAL}"]
    kept = {"place": "zh title", "form": "跑", "within": "跑道", "reason": "a standard word"}
    monkeypatch.setattr(register, "FILM", with_register(kept))
    assert register.check()["excused"] == [kept]


def test_a_fixed_idiom_the_style_states_needs_no_declaration_and_refuses_one(words, monkeypatch):
    say(words, "zh", title="这个示例名副其实")
    assert register.check()["excused"] == []
    idiom = {"place": "zh title", "form": "其实", "within": "名副其实", "reason": "an idiom"}
    monkeypatch.setattr(register, "FILM", with_register(idiom))
    refusal(
        "The register exception of '其实' at zh title excuses no refusal: no error-level occurrence"
        " stands within '名副其实'"
    )


def test_an_exception_answers_errors_only_and_any_letter_case(monkeypatch):
    kept = {"place": "zh 01.1", "form": "YOU", "within": "THANK-YOU NOTE", "reason": "a name"}
    ours = {"place": "zh 01.2", "form": "我们", "within": "我们先看", "reason": "a named party"}
    monkeypatch.setattr(register, "FILM", with_register(kept, ours))
    placed(monkeypatch, "Write a thank-you note.", "我们先看。")
    refusal(
        "The register exception of '我们' at zh 01.2 excuses no refusal: the form stands there as"
        " a warning, which no exception removes"
    )
    monkeypatch.setattr(register, "FILM", with_register(kept))
    report = register.check()
    assert report["excused"] == [kept]
    assert [warning["form"] for warning in report["warnings"]] == ["我们"]


def test_the_cli_prints_the_report_and_refuses_with_every_failure(monkeypatch, capsys):
    monkeypatch.setattr(register, "check", lambda: {"warnings": []})
    register.main()
    assert json.loads(capsys.readouterr().out) == {"warnings": []}

    def refuse():
        message = "zh 01.1: one\nen 01.1: two"
        raise RegisterError(message)

    monkeypatch.setattr(register, "check", refuse)
    with pytest.raises(SystemExit, match=re.escape("register: zh 01.1: one\nen 01.1: two")):
        register.main()


def test_running_the_package_as_a_module_runs_the_cli(monkeypatch, capsys):
    # Run here as `python -m filmkit.register` runs it.
    monkeypatch.setattr(register, "check", lambda: {"warnings": []})
    runpy.run_module("filmkit.register", run_name="__main__")
    assert json.loads(capsys.readouterr().out) == {"warnings": []}

    def refuse():
        message = "zh 01.1: one"
        raise RegisterError(message)

    monkeypatch.setattr(register, "check", refuse)
    with pytest.raises(SystemExit, match=re.escape("register: zh 01.1: one")):
        runpy.run_module("filmkit.register", run_name="__main__")


@pytest.mark.parametrize(
    ("page", "lines"),
    [
        ("<p>其<em>实</em>不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        ("<p>其<wbr>实不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        ("<p>其<s>实</s>不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        ("<p><ruby>其</ruby>实不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        ("<p>其<rt>qí</rt>实不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        (
            "<p><ruby>其<rp>(</rp><rt>qí</rt><rp>)</rp></ruby><ruby>实<rt>shí</rt></ruby>不难</p>",
            [f"entry page: '其实' {COLLOQUIAL}"],
        ),
        ("<p><ruby>其<rt>qí</ruby>实不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        ("<p>其<x-term>实</x-term>不难</p>", [f"entry page: '其实' {COLLOQUIAL}"]),
        ("<h1>开始吧</h1><p>下一步</p>", [f"entry page: '吧' {COLLOQUIAL}"]),
        ("<ul><li>第一</li><li>下游系统</li></ul>", []),
        ("<p>口径统一<br>下面三项</p>", []),
        ("<p>口径统一<br/>下面三项</p>", []),
        (
            "<main><p hidden>隐藏<p>你们看<p>您看</main><footer>咱们</footer>",
            [f"entry page: '{form}' {ADDRESS}" for form in ("你们", "您", "咱们")],
        ),
        (
            "<p hidden>隐藏<h1>你们看</h1><p>您看</p><footer>大家好</footer>",
            [f"entry page: '{form}' {ADDRESS}" for form in ("你们", "您", "大家")],
        ),
    ],
)
def test_the_entry_page_is_read_as_a_viewer_meets_it(words, page, lines):
    entry = words / concepts.FILM.entry
    entry.write_text(entry.read_text(encoding="utf-8").replace("<footer>", page + "<footer>"))
    if lines:
        refusal(*lines)
    else:
        register.check()


@pytest.mark.parametrize("br", ["<br>", "<br/>"])
def test_two_questions_either_side_of_a_line_break_are_one_runs(words, br):
    entry = words / concepts.FILM.entry
    page = f"<p>为什么？{br}又如何？</p><footer>"
    entry.write_text(entry.read_text(encoding="utf-8").replace("<footer>", page))
    (warning,) = register.check()["warnings"]
    assert (warning["place"], warning["rule"]) == ("entry page", "register.questions")


def test_an_entry_page_that_is_no_utf8_text_is_refused_in_one_line(words):
    (words / concepts.FILM.entry).write_bytes(b"<p>\xff</p>")
    assert str(refused()) == (
        "The entry page content/index.html is no UTF-8 text: byte 3 cannot be read"
    )


def test_an_exception_answers_its_own_form_at_its_own_place(monkeypatch):
    quoted = {"place": "zh 01.1", "form": "搞", "within": "你们搞定", "reason": "a quoted request"}
    monkeypatch.setattr(register, "FILM", with_register(quoted))
    # The declared text holds a second listed form, which stays refused.
    placed(monkeypatch, "「你们搞定」是一个例子。")
    refusal(f"zh 01.1: '你们' {ADDRESS}")
    # The declared text standing at a second place is refused there.
    placed(monkeypatch, "「你们搞定」", "「你们搞定」")
    refusal(
        f"zh 01.1: '你们' {ADDRESS}", f"zh 01.2: '你们' {ADDRESS}", f"zh 01.2: '搞' {COLLOQUIAL}"
    )


def test_every_occurrence_inside_overlapping_occurrences_of_the_text_is_excused(monkeypatch):
    kept = {"place": "zh 01.1", "form": "吧", "within": "吧吧", "reason": "a sound"}
    held = {"place": "zh 01.2", "form": "其实", "within": "哈其实哈", "reason": "a quotation"}
    monkeypatch.setattr(register, "FILM", with_register(kept, held))
    # Three 吧 and two 其实 stand at the two places, each inside an occurrence of its text.
    placed(monkeypatch, "吧吧吧", "哈其实哈其实哈")
    assert register.check()["excused"] == [kept, held]


@pytest.mark.parametrize(
    ("texts", "advised"),
    [
        (("你们先看。",), True),
        (("再搞一次。",), True),
        (("It doesn't.",), True),
        (("Stop!",), False),
        (("Stop!", "再搞一次。"), True),
    ],
)
def test_the_advice_on_keeping_a_word_follows_only_a_listed_form(monkeypatch, texts, advised):
    placed(monkeypatch, *texts)
    refusal = refused()
    assert str(refusal).splitlines() == [*refusal.lines, *([KEEP] if advised else [])]


def test_a_stale_exception_alone_brings_no_advice(monkeypatch):
    monkeypatch.setattr(register, "FILM", with_register(QUOTED))
    placed(monkeypatch, "这是一个例子。")
    refusal = refused()
    stale = "The register exception of '搞' at zh 01.1 is stale: the place does not hold '先搞清楚'"
    assert (str(refusal), list(refusal.lines)) == (stale, [stale])


def test_each_place_meets_the_rules_of_the_languages_its_words_are_in(words):
    contraction = "is a contraction (R3)"
    # A contraction is English's: refused in an English thought and in a Chinese one, which reads
    # Latin script as English; 其实 is Chinese's: refused in a Chinese thought, and not looked for
    # in an English one.
    say(words, "zh", "其实这一步不复杂，don't 跳过它。")
    say(words, "en", "It reads 其实 here, so don't skip it.")
    refusal(
        f"zh 01.1: '其实' {COLLOQUIAL}",
        f"zh 01.1: 'don't' {contraction}",
        f"en 01.1: 'don't' {contraction}",
    )
    say(words, "zh", "这一步不复杂。")
    say(words, "en", "It reads 其实 here, so do not skip it.")
    assert register.check()["places"] > 0
