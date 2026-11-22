"""A listed form is refused wherever it stands, in plain speech, inside a standard word, joined
to another English word or parted by a character the viewer does not see; the grade of each
sentence is stated here."""

import pytest
from placing import placed, refused_lines

import filmkit.register as register

COLLOQUIAL, ADDRESS, CONTRACTION = (
    "is colloquial (R3)",
    "addresses the audience (R1)",
    "is a contraction (R3)",
)
# Each text holds one occurrence of a listed form, and the refusal names it: the second and third
# reviews' plain sentences, standard words, English forms joined to a word, apostrophes and unseen
# characters.
ROWS = [
    *(
        (text, f"'大家' {ADDRESS}")
        for text in ("通过大家的努力", "提高大家的效率", "尊重大家的时间")
    ),
    *((text, f"'大家' {ADDRESS}") for text in ("大家电脑上都装了", "大家电话联系", "大家庭")),
    *(
        (text, f"'其实' {COLLOQUIAL}")
        for text in (
            "不过其实没那么复杂",
            "比如其实可以这样",
            "其实测试早就通过了",
            "其实效果一般",
            "其实体验并不好",
            "其实质量问题一直存在",
            "其实验收标准早就写清楚了",
            "其实力度不够",
            "其实例子很多",
            "让数据名副其实",
        )
    ),
    *(
        (text, f"'一下' {COLLOQUIAL}")
        for text in (
            "先规划一下",
            "请配合一下",
            "看一下发布记录",
            "试一下降级方案",
            "看一下属性",
            "确认一下限制",
            "点一下载",
            "查一下线程",
            "统一下发",
        )
    ),
    *(
        (text, f"'跑' {COLLOQUIAL}")
        for text in (
            "测试跑通了",
            "每晚跑表",
            "一起跑测试",
            "把两个任务合并跑一遍",
            "协助跑批",
            "最长跑了三小时",
            "缩短跑批时间",
            "任务太慢跑不完",
            "跑步骤一的脚本",
            "跑题库",
            "跑道路数据清洗",
            "跑车联网数据",
            "先小跑一批数据",
            "跑道",
        )
    ),
    *(
        (text, f"'弄' {COLLOQUIAL}")
        for text in (
            "在脚本里弄了个开关",
            "把工作弄完",
            "操作弄错了",
            "微调弄好了",
            "直播弄砸了",
            "游戏弄坏了",
            "先弄权限",
            "弄虚作假",
        )
    ),
    *(
        (text, f"'吧' {COLLOQUIAL}")
        for text in ("喝点水吧。", "读读这本书吧。", "先上网吧。", "酒吧")
    ),
    *((text, f"'呢' {COLLOQUIAL}") for text in ("什么时候上线呢？", "这钱怎么花呢？", "呢绒")),
    *((text, f"'现查' {COLLOQUIAL}") for text in ("只能现查明细", "现查实际值")),
    ("迷你主机", f"'你' {ADDRESS}"),
    ("Write a thank-you note.", f"'you' {ADDRESS}"),
    ("Thank you-all.", f"'you' {ADDRESS}"),
    ("Then _you_ decide.", f"'you' {ADDRESS}"),
    ("Ask your-team.", f"'your' {ADDRESS}"),
    ("It goes to-you.", f"'you' {ADDRESS}"),
    ("It doesn´t hold.", f"'doesn´t' {CONTRACTION}"),
    ("It doesn`t hold.", f"'doesn`t' {CONTRACTION}"),
    ("Then itʼs late.", f"'itʼs' {CONTRACTION}"),
    # Characters a viewer does not see, inside a form: a soft hyphen, a left-to-right mark, a
    # variation selector, a zero-width space, a combining grapheme joiner, a Mongolian variation
    # selector, an ideographic variation selector and a word joiner.
    *(
        (f"其{unseen}实不难", f"'其实' {COLLOQUIAL}")
        for unseen in ("\u00ad", "\u200e", "\ufe00", "\u200b", "\u034f", "\u180b")
    ),
    *((f"大{unseen}家好", f"'大家' {ADDRESS}") for unseen in ("\u00ad", "\U000e0100", "\u2060")),
]


def test_every_listed_form_is_refused_wherever_it_stands(monkeypatch):
    placed(monkeypatch, *(text for text, _ in ROWS))
    lines = refused_lines()
    assert lines == [f"zh 01.{index}: {said}" for index, (_, said) in enumerate(ROWS, 1)]


def test_every_occurrence_in_one_place_is_refused(monkeypatch):
    placed(monkeypatch, "其实不难，名副其实。再跑一遍，跑道。")
    lines = refused_lines()
    assert lines == [f"zh 01.1: '其实' {COLLOQUIAL}"] * 2 + [f"zh 01.1: '跑' {COLLOQUIAL}"] * 2


@pytest.mark.parametrize(
    "texts",
    [
        ("它说明了什么？", "又能证明什么？"),
        ("–5 degrees", "-5 degrees", "--dry-run"),
        ("先看。", "–5 degrees", "-5 degrees", "--dry-run"),
        ("Young people read it.", "Call it you2."),
    ],
)
def test_a_place_is_judged_alone_and_letters_beside_a_form_hold_none(monkeypatch, texts):
    placed(monkeypatch, *texts)
    assert register.check()["warnings"] == []
