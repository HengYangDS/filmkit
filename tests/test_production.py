"""Where each edition's generated plans, pictures and records live, and the films it delivers."""

import filmkit.repository as repository
from filmkit.production import CODES, RENDITIONS, Edition


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
