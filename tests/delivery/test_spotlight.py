"""The keywords and authors of a film as Spotlight's importer reports them."""

from pathlib import Path

import filmkit.delivery.spotlight as delivery_spotlight

# What `mdimport -t -d2` printed on 2026-11-12 (macOS 27.2.1) for a 1 s probe film carrying the
# sample's Chinese QuickTime keys with the keywords value DDWG,数据质量,人与人工智能的协作.
REPORT = Path(__file__).with_name("mdimport-report.txt").read_text(encoding="utf-8")


def test_a_test_import_report_gives_the_keywords_and_authors_spotlight_imported():
    assert delivery_spotlight.parse(REPORT) == {
        "keywords": ["DDWG", "数据质量", "人与人工智能的协作"],
        "authors": ["Yang HENG"],
    }


def test_each_escape_of_a_quoted_string_is_decoded():
    # As the importer printed a keyword holding a tab, and authors holding quotation marks, a
    # backslash, an emoji as two UTF-16 units, an accented letter and control characters.
    report = r"""    kMDItemAuthors =     (
        "Yang \"Q\" HENG",
        "Yang\\HENG \Ud83d\Ude00 \U00e9",
        "YangHENG\nXY\fZ"
    );
    kMDItemKeywords =     (
        "\U5236\U8868\t\U7b26"
    );
"""
    assert delivery_spotlight.parse(report) == {
        "keywords": ["制表\t符"],
        "authors": ['Yang "Q" HENG', "Yang\\HENG 😀 é", "YangHENG\nXY\fZ"],
    }


def test_a_report_without_keywords_or_authors_gives_neither():
    header = REPORT.split("{", 1)[0]
    assert delivery_spotlight.parse(header + "{\n}\n") == {"keywords": [], "authors": []}
