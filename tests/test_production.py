"""Where each edition's generated plans, pictures and records live, the films it delivers, and
its runtime as its timeline states it."""

import json

import pytest

import filmkit.repository as repository
from filmkit.production import CODES, RENDITIONS, Edition, UnassembledError


def test_generated_plans_and_records_live_under_build():
    for code in CODES:
        edition = Edition(code)
        for path in (edition.shot_plan, edition.production_review):
            assert path.is_relative_to(repository.ROOT / "build"), path


def test_each_picture_has_its_own_stage_file_and_receipt():
    edition = Edition("en")
    captioned, uncaptioned = edition.rendered(), edition.rendered(captions=False)
    assert (captioned.name, uncaptioned.name) == ("captioned", "uncaptioned")
    assert (edition.picture_stage, edition.picture, edition.render_receipt) == (
        captioned.stage,
        captioned.file,
        captioned.receipt,
    )
    root = repository.ROOT
    assert uncaptioned.stage == root / "build/runtime/work/final-delivery-en-uhd-uncaptioned"
    assert uncaptioned.page == (
        root / "build/runtime/work/final-delivery-en-uhd-uncaptioned/index.html"
    )
    assert uncaptioned.file == edition.artifacts / "sample-reel-final-picture-uncaptioned.mp4"
    assert uncaptioned.receipt == edition.evidence / "render/receipt-uncaptioned.json"
    assert edition.caption_equivalence == edition.evidence / "caption-equivalence.json"


def test_each_edition_delivers_both_sizes_with_and_without_captions():
    edition = Edition("zh")
    assert [film.name for film in edition.films] == [
        "sample-reel-zh-uhd.mp4",
        "sample-reel-zh-1080p-captioned.mp4",
        "sample-reel-zh-uhd-uncaptioned.mp4",
        "sample-reel-zh-1080p-uncaptioned.mp4",
    ]
    renditions = list(RENDITIONS.values())
    assert [(r.width, r.height, r.reencoded, r.captions) for r in renditions] == [
        (3840, 2160, False, True),
        (1920, 1080, True, True),
        (3840, 2160, False, False),
        (1920, 1080, True, False),
    ]
    # The two films of a size are made alike, each from its own picture.
    assert renditions[0].video == renditions[2].video
    assert (renditions[1].decoding, renditions[1].video) == (
        renditions[3].decoding,
        renditions[3].video,
    )


def test_an_edition_s_runtime_is_the_whole_seconds_its_timeline_states(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = Edition("en")
    edition.timeline.parent.mkdir(parents=True)
    edition.timeline.write_text(json.dumps({"duration": 1477, "segments": []}))
    assert edition.runtime == 1477
    assert edition.runtime_in({"duration": 1636}) == 1636


def test_an_edition_without_a_timeline_has_no_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    with pytest.raises(UnassembledError) as refused:
        _ = Edition("zh").runtime
    assert str(refused.value) == (
        "The zh edition has no timeline at build/artifacts/film/zh/timeline.json, so no runtime: "
        "run produce assemble --language zh"
    )


@pytest.mark.parametrize(
    "stated",
    [
        "[]",
        "{}",
        '{"duration": 1476.5}',
        '{"duration": 1476.0}',
        '{"duration": 0}',
        '{"duration": true}',
        '{"duration": "1476"}',
        '{"duration": NaN}',
        '{"duration": 14',
    ],
)
def test_a_timeline_that_states_no_whole_number_of_seconds_is_refused(
    tmp_path, monkeypatch, stated
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    edition = Edition("zh")
    edition.timeline.parent.mkdir(parents=True)
    edition.timeline.write_text(stated)
    with pytest.raises(UnassembledError) as refused:
        _ = edition.runtime
    assert str(refused.value) == (
        "build/artifacts/film/zh/timeline.json states no runtime in whole seconds: "
        "run produce assemble --language zh"
    )
