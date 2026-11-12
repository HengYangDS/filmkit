"""The verifier's Spotlight readback: the keywords and authors each delivered film imports, where
the host has `mdimport`."""

import re
import sys
import textwrap
from pathlib import Path

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.delivery.verification import VerificationError

# What `mdimport -t -d2` printed for a probe film whose keywords value was the first below, and
# the keywords array it printed for each value, item by item (2026-11-12, macOS 27.2.1).
REPORT = Path(__file__).with_name("mdimport-report.txt").read_text(encoding="utf-8")
PRINTED = {
    "DDWG,数据质量,人与人工智能的协作": [
        "DDWG",
        r'"\U6570\U636e\U8d28\U91cf"',
        r'"\U4eba\U4e0e\U4eba\U5de5\U667a\U80fd\U7684\U534f\U4f5c"',
    ],
    # A mostly Chinese value splits only at its commas, and keeps each space after one.
    "DDWG, 数据质量, 人与人工智能的协作": [
        "DDWG",
        r'" \U6570\U636e\U8d28\U91cf"',
        r'" \U4eba\U4e0e\U4eba\U5de5\U667a\U80fd\U7684\U534f\U4f5c"',
    ],
    # A mostly Latin value splits at every space too.
    "DDWG,人与 Agent 协作,authority to act": [
        "DDWG",
        r'"\U4eba\U4e0e"',
        "Agent",
        r'"\U534f\U4f5c"',
        "authority",
        "to",
        "act",
    ],
    "DDWG,authority to act": ["DDWG", "authority", "to", "act"],
    # An importer that reads no keywords prints no keywords array.
    "": [],
}


def keywords_array(items: list[str]) -> str:
    """A keywords array laid out as the importer prints it, and none for none."""
    lines = ",\n".join(f"        {item}" for item in items)
    return f"    kMDItemKeywords =     (\n{lines}\n    );" if items else ""


def authors_array(count: int) -> str:
    """The authors array laid out as the importer prints the declared author read `count` times,
    and none for none. A film carrying the author under its Author and Artist keys both imports it
    twice, and one carrying no author key imports none (2026-11-12)."""
    lines = ",\n".join([f'        "{specification.AUTHOR}"'] * count)
    return f"    kMDItemAuthors =     (\n{lines}\n    );\n" if count else ""


def report_of(value: str, authors: int) -> str:
    """The importer's report of a film carrying a keywords value and the declared author read
    `authors` times: the recorded report, which reads it once, with the arrays printed for those."""
    keywords = keywords_array(PRINTED["DDWG,数据质量,人与人工智能的协作"])
    assert keywords in REPORT and authors_array(1) in REPORT
    printed = REPORT.replace(keywords, keywords_array(PRINTED[value]))
    return printed.replace(authors_array(1), authors_array(authors))


def importer(folder: Path, printed: str) -> None:
    """A stand-in `mdimport` that records its arguments beside it and prints a report."""
    body = f"""
        import sys
        with open({str(folder / "calls.txt")!r}, "a", encoding="utf-8") as calls:
            calls.write(" ".join(sys.argv[1:]) + "\\n")
        sys.stdout.write({printed!r})
        """
    tool = folder / "mdimport"
    tool.write_text(f"#!{sys.executable}\n{textwrap.dedent(body)}", encoding="utf-8")
    tool.chmod(0o755)


@pytest.fixture
def verify(tmp_path, monkeypatch):
    """Verify an edition declaring some keywords, its other checks passing, on a host whose PATH
    holds only a stand-in `mdimport` that prints the report of a film carrying a keywords value
    and the declared author read some times, once by default, or no `mdimport` for None; returns
    the verifier's report and the stand-in's calls."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for name in ("sources", "narration", "picture", "package", "media", "review"):
        monkeypatch.setattr(delivery_verification, f"verify_{name}", lambda *_: {})
    tools = tmp_path / "bin"
    tools.mkdir()
    monkeypatch.setenv("PATH", str(tools))

    def verified(code: str, keywords: list[str], value: str | None, authors: int = 1):
        edition = production.Edition(code)
        repository.write(edition.script, {"release": {"keywords": keywords}})
        if value is not None:
            importer(tools, report_of(value, authors))
        qualified = delivery_verification.qualify(edition, edition.films)
        calls = tools / "calls.txt"
        return qualified, calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []

    return verified


def test_chinese_keywords_joined_by_commas_alone_import_whole(verify):
    keywords = ["DDWG", "数据质量", "人与人工智能的协作"]
    report, calls = verify("zh", keywords, "DDWG,数据质量,人与人工智能的协作")
    films = sorted(production.Edition("zh").films)
    assert report["spotlight"] == {
        "readback": "mdimport",
        "films": [
            {
                "path": str(film.relative_to(repository.ROOT)),
                "keywords": keywords,
                "authors": [specification.AUTHOR],
                "split_into_words": [],
            }
            for film in films
        ],
    }
    # Each film is imported in test mode, which stores nothing in the Spotlight index.
    assert calls == [f"-t -d2 {film}" for film in films]


def test_a_keyword_imported_with_a_leading_space_is_refused(verify):
    keywords = ["DDWG", "数据质量", "人与人工智能的协作"]
    with pytest.raises(VerificationError, match='sample-reel-zh-1080p-captioned.mp4.*" 数据质量"'):
        verify("zh", keywords, "DDWG, 数据质量, 人与人工智能的协作")


def test_a_chinese_keyword_the_importer_splits_is_refused(verify):
    keywords = ["DDWG", "人与 Agent 协作", "authority to act"]
    with pytest.raises(VerificationError, match='"人与 Agent 协作" does not import whole'):
        verify("zh", keywords, "DDWG,人与 Agent 协作,authority to act")


def test_an_english_phrase_split_into_words_is_recorded_and_passes(verify):
    report, _ = verify("en", ["DDWG", "authority to act"], "DDWG,authority to act")
    films = report["spotlight"]["films"]
    assert [film["keywords"] for film in films] == [["DDWG", "authority", "to", "act"]] * 4
    assert [film["split_into_words"] for film in films] == [["authority to act"]] * 4
    assert report["verdict"] == "pass"


def test_a_film_whose_keywords_import_none_is_refused(verify):
    # With no keyword read back, a viewer finds the film by none of its declared keywords.
    with pytest.raises(VerificationError, match="no keyword imports"):
        verify("en", ["DDWG", "authority to act"], "")


def test_the_declared_author_imported_once_passes_and_is_recorded(verify):
    keywords = ["DDWG", "数据质量", "人与人工智能的协作"]
    report, _ = verify("zh", keywords, "DDWG,数据质量,人与人工智能的协作")
    authors = [film["authors"] for film in report["spotlight"]["films"]]
    assert authors == [[specification.AUTHOR]] * 4


@pytest.mark.parametrize(
    ("count", "read"),
    [(2, f'"{specification.AUTHOR}", "{specification.AUTHOR}"'), (0, "none")],
    ids=["twice", "none"],
)
def test_authors_other_than_the_declared_author_once_are_refused(verify, count, read):
    # The author under both the Author and the Artist key imports twice, and Finder shows "(2)".
    keywords = ["DDWG", "数据质量", "人与人工智能的协作"]
    named = f'authors read are {read}, not "{specification.AUTHOR}" alone'
    with pytest.raises(VerificationError, match=re.escape(named)):
        verify("zh", keywords, "DDWG,数据质量,人与人工智能的协作", authors=count)


def test_a_host_without_mdimport_records_the_readback_as_unavailable(verify):
    report, calls = verify("zh", ["DDWG", "数据质量"], None)
    assert report["spotlight"] == {"readback": "unavailable"}
    assert (report["verdict"], calls) == ("pass", [])
