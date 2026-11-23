"""The delivery index, the runtime label, the film's version and the viewing members."""

import os
import re

import pytest

import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.player as delivery_player
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.packaging import PackagingError

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


def test_an_edition_whose_cover_is_not_painted_refuses_naming_its_field(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = production.Edition("zh")
    with pytest.raises(PackagingError, match=rf"editions\.zh\.cover: {re.escape(edition.cover)}"):
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
    source.write_bytes(template.replace(b'href="en/index.html"', b'href="en.html"'))
    with pytest.raises(PackagingError, match="both sibling language links"):
        delivery_packaging.package_language_index("1.3.0")
    source.write_bytes(template.replace(b"<nav", b"<div").replace(b"</nav>", b"</div>"))
    with pytest.raises(PackagingError, match="language links in a <nav>"):
        delivery_packaging.package_language_index("1.3.0")


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
