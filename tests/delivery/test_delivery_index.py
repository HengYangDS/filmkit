"""The delivery index, the runtime label and the viewing members."""

import re

import pytest

import filmkit.delivery.packaging as delivery_packaging
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.delivery.packaging import PackagingError


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
    observed = delivery_packaging.package_language_index()
    output = (root / "index.html").read_text()
    assert 'href="zh/index.html"' in output
    assert 'href="en/index.html"' in output
    runtime = f"{specification.DURATION // 60:02d}:{specification.DURATION % 60:02d}"
    assert "<base " not in output
    assert runtime in output
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
        delivery_packaging.package_language_index()
