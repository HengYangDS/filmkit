"""The delivery index, the runtime label, the film's version and the viewing members."""

import re

import pytest

import filmkit.delivery.packaging as delivery_packaging
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.delivery.packaging import PackagingError

# The line under the entry page's title at version 1.3.0.
ENTRY_VERSION = (
    '<p class="version"><span lang="zh-CN">版本号</span> / <span lang="en">Version</span> 1.3.0</p>'
)


def test_the_runtime_and_viewing_members_follow_the_edition():
    minutes, seconds = divmod(specification.DURATION, 60)
    assert delivery_packaging.runtime_label() == f"{minutes:02d}:{seconds:02d}"
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
    for code in ("zh", "en"):
        player = root / code / "index.html"
        player.parent.mkdir(parents=True)
        player.write_text(f"Existing {code} player")
    observed = delivery_packaging.package_language_index("1.3.0")
    output = (root / "index.html").read_text()
    assert 'href="zh/index.html"' in output
    assert 'href="en/index.html"' in output
    runtime = f"{specification.DURATION // 60:02d}:{specification.DURATION % 60:02d}"
    assert "<base " not in output
    assert runtime in output
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
    source.write_bytes(template.replace(b'href="en/index.html"', b'href="en.html"'))
    with pytest.raises(PackagingError, match="both sibling language links"):
        delivery_packaging.package_language_index("1.3.0")
    source.write_bytes(template.replace(b"<nav", b"<div").replace(b"</nav>", b"</div>"))
    with pytest.raises(PackagingError, match="language links in a <nav>"):
        delivery_packaging.package_language_index("1.3.0")
