"""The delivery index, the runtime label, the film's version and the viewing members."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import filmkit.delivery.entry as delivery_entry
import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.player as delivery_player
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.packaging import PackagingError
from filmkit.film import FILM

# The line under the entry page's title at version 1.3.0.
ENTRY_VERSION = (
    '<p class="version"><span lang="zh-CN">版本号</span> / <span lang="en">Version</span> 1.3.0</p>'
)


def test_the_runtime_and_viewing_members_follow_the_edition():
    assert [delivery_player.runtime_label(seconds) for seconds in (1636, 1476, 60)] == [
        "27:16",
        "24:36",
        "01:00",
    ]
    assert delivery_packaging.viewing_members(production.Edition("en")) == (
        "sample-reel-cover.png",
        "sample-reel-cover.jpg",
        "sample-reel-en.srt",
        "sample-reel-en.vtt",
        "sample-reel-en-transcript.md",
        "chapters.json",
        "chapters.ffmeta",
        "index.html",
    )


def test_an_edition_whose_cover_is_not_painted_refuses_naming_its_place(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition("zh")
    with pytest.raises(PackagingError, match=rf"zh edition's cover {re.escape(edition.cover)} is"):
        delivery_packaging.package_metadata(edition)
    assert not (tmp_path / "build").exists()


def test_the_version_is_the_semantic_version_the_repositorys_version_file_holds(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    for held, version in (("1.3.0\n", "1.3.0"), (" 2.0.0-rc.1 \n", "2.0.0-rc.1")):
        (tmp_path / "VERSION").write_text(held)
        assert delivery_packaging.film_version() == version


@pytest.mark.parametrize(
    "held", [None, "1.3", "v1.3.0", "1.3.0+build"], ids=["missing", "1.3", "v1.3.0", "build"]
)
def test_packaging_refuses_a_film_without_a_valid_version_naming_it(tmp_path, monkeypatch, held):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition("zh")
    (tmp_path / edition.cover).parent.mkdir(parents=True)
    (tmp_path / edition.cover).write_bytes(b"cover png")
    if held is not None:
        (tmp_path / "VERSION").write_text(f"{held}\n")
    found = "is missing" if held is None else f"holds {held!r}"
    with pytest.raises(PackagingError, match=re.escape(f"The film's VERSION {found}")):
        delivery_packaging.package_metadata(edition)
    assert not (tmp_path / "build").exists()


def test_delivery_index_uses_sibling_languages_and_preserves_language_players(
    tmp_path,
    monkeypatch,
):
    """Exercise the actual root-template producer, independent of edition depth."""
    template = (repository.ROOT / delivery_packaging.INDEX).read_bytes()
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    source = tmp_path / delivery_packaging.INDEX
    source.parent.mkdir(parents=True)
    source.write_bytes(template)
    root = tmp_path / "build/artifacts/film"
    for code, runtime in (("zh", 1636), ("en", 1476)):
        player = root / code / "index.html"
        player.parent.mkdir(parents=True)
        player.write_text(f"Existing {code} player")
        repository.write(production.Edition(code).timeline, {"duration": runtime})
    observed = delivery_packaging.package_language_index("1.3.0")
    output = (root / "index.html").read_text()
    assert 'href="zh/index.html"' in output
    assert 'href="en/index.html"' in output
    assert "<base " not in output
    # Each language link shows its own edition's runtime.
    assert '<a href="zh/index.html" lang="zh-CN"><strong>中文</strong><span>27:16 · ' in output
    assert '<a href="en/index.html" lang="en"><strong>English</strong><span>24:36 · ' in output
    assert "/*RUNTIME*/" not in output
    # The version stands under the film's title and its subtitle, above the language links.
    assert output.index("</h1>") < output.index("</p>") < output.index(ENTRY_VERSION)
    assert output.index(ENTRY_VERSION) < output.index("<nav")
    assert output.count("1.3.0") == 1
    assert observed == {
        "source": "content/index.html",
        "source_sha256": repository.sha(source),
        "path": "build/artifacts/film/index.html",
        "sha256": repository.sha(root / "index.html"),
        "languages": ["zh", "en"],
    }
    for code in ("zh", "en"):
        assert (root / code / "index.html").read_text() == f"Existing {code} player"
    # The page is replaced whole: while it is written again, a reader, such as the other
    # edition's packaging hashing it, finds the complete earlier page.
    seen, flush = [], os.fsync
    monkeypatch.setattr(os, "fsync", lambda file: seen.append((root / "index.html").read_text()))
    assert delivery_packaging.package_language_index("1.3.1")["sha256"] != observed["sha256"]
    assert seen == [output]
    monkeypatch.setattr(os, "fsync", flush)
    # The page's own rule, its links in their order and its root, is the loader's to refuse
    # (`filmkit.delivery.entry`); packaging asks it no more.
    assert "both sibling" not in Path(delivery_packaging.__file__).read_text()


def test_the_entry_page_waits_for_both_editions_runtimes(tmp_path, monkeypatch):
    template = (repository.ROOT / delivery_packaging.INDEX).read_bytes()
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    source = tmp_path / delivery_packaging.INDEX
    source.parent.mkdir(parents=True)
    source.write_bytes(template)
    repository.write(production.Edition("zh").timeline, {"duration": 1636})
    with pytest.raises(production.UnassembledError) as refused:
        delivery_packaging.package_language_index("1.3.0")
    assert str(refused.value) == (
        "The en edition has no timeline at build/artifacts/film/en/timeline.json, so no runtime: "
        "run produce assemble --language en"
    )
    assert not (tmp_path / delivery_packaging.LANGUAGE_INDEX).exists()
    # An anchor outside the language links names no edition's runtime.
    repository.write(production.Edition("en").timeline, {"duration": 1476})
    source.write_bytes(template.replace(b"<footer>", b"<footer>/*RUNTIME*/ "))
    with pytest.raises(PackagingError, match=re.escape("outside its language links")):
        delivery_packaging.package_language_index("1.3.0")


def test_the_entry_module_loads_no_declaration_and_judges_a_page_by_its_rule():
    entry = subprocess.run(
        [sys.executable, "-I", "-B", "-c", ENTRY_ALONE],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
        env={"PYTHONPATH": str(Path(delivery_entry.__file__).parents[2])},
        cwd="/",
    )
    assert entry.returncode == 0, entry.stderr
    sample = (repository.ROOT / FILM.entry).read_text(encoding="utf-8")
    tags = {"zh": "zh-CN", "en": "en"}
    assert delivery_entry.problems(sample, tags, "index.html") == []
    reordered = sample.replace('href="zh/', 'href="tmp/').replace('href="en/', 'href="zh/')
    reordered = reordered.replace('href="tmp/', 'href="en/')
    faults = delivery_entry.problems(
        reordered.replace('lang="mul"', 'lang="zh-CN"', 1) + "<base href=x>",
        {**tags, "xb": "xb"},
        "index.html",
    )
    assert faults == [
        'index.html opens with lang="zh-CN"; its root is <html lang="mul">',
        "index.html links no xb/index.html in its <nav>",
        "index.html links en/index.html with lang='zh-CN', not lang=\"en\"",
        "index.html links zh/index.html with lang='en', not lang=\"zh-CN\"",
        "index.html holds a <base>, which would choose one language for every link",
    ]
    assert delivery_entry.problems(reordered, tags, "index.html")[0] == (
        "index.html links the editions as en/index.html, zh/index.html, not in the declared order"
    )


# Imports the entry module alone, with no film to load: it needs no declaration.
ENTRY_ALONE = (
    "import filmkit.delivery.entry as e; assert 'filmkit.film' not in __import__('sys').modules"
)


def test_an_entry_page_that_links_an_edition_twice_or_an_undeclared_one_is_refused():
    sample = (repository.ROOT / FILM.entry).read_text(encoding="utf-8")
    tags = {"zh": "zh-CN", "en": "en"}
    nav = sample.index("</nav>")
    extra = (
        '<a href="zh/index.html" lang="zh-CN">中文</a><a href="ja/index.html" lang="ja">日本語</a>'
    )
    assert delivery_entry.problems(sample[:nav] + extra + sample[nav:], tags, "index.html") == [
        "index.html links zh/index.html 2 times in its <nav>; link each edition once",
        "index.html links ja/index.html, which names no declared edition",
    ]
    # The order is judged on each edition's first link once every declared edition is linked.
    swapped = sample.replace('href="zh/', 'href="tmp/').replace('href="en/', 'href="zh/')
    swapped = swapped.replace('href="tmp/', 'href="en/').replace('lang="zh-CN">', 'lang="en">')
    nav = swapped.index("</nav>")
    twice = swapped[:nav] + '<a href="en/index.html" lang="en">English</a>' + swapped[nav:]
    assert "not in the declared order" in "\n".join(delivery_entry.problems(twice, tags, "x"))
