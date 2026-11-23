"""The verifier's reading of an edition whose uncaptioned picture is derived: both receipts
through the pictures' own validation, on a derived pair with its passing comparison record."""

import pytest
import test_derived_pair

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.equivalence as equivalence
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.specification import FPS

pair = test_derived_pair.pair
compared = test_derived_pair.compared


@pytest.fixture
def verified(compared):
    """A derived pair, compared, with the geometry record and shot plan the verifier reads."""
    edition, _ = compared
    equivalence.compare_pictures(edition)
    sha = repository.sha
    geometry = {
        "format": "picture-geometry",
        "passed": True,
        "findings": [],
        "errors": [],
        "index_sha256": sha(edition.rendered().page),
        "width": 3840,
        "height": 2160,
        "duration": edition.runtime,
        "fps": FPS,
        "step_frames": 2,
        "checked": edition.runtime * FPS // 2,
        "browser": "Chromium",
    }
    repository.write(edition.picture_geometry, geometry)
    plan = {
        "script_sha256": sha(edition.script),
        "composition_sha256": sha(picture_rendering.COMPOSITION_SCRIPT),
        "timeline_sha256": sha(edition.timeline),
    }
    repository.write(repository.ROOT / edition.shot_plan, plan)
    return edition


def test_the_verifier_reads_a_derived_pair_and_reports_its_ground_frames(verified):
    report = delivery_verification.verify_picture(verified)
    assert report["caption_equivalence"] == {
        "composition_instants": 7,
        "derived": True,
        "ground_frames": 99,
    }
    uncaptioned = verified.rendered(False)
    assert report["uncaptioned_picture_sha256"] == repository.sha(uncaptioned.file)
    assert report["picture_sha256"] == repository.sha(verified.rendered(True).file)


def changed_picture(edition):
    edition.rendered(False).file.write_text("another picture")


def unproven(edition):
    receipt = repository.read(edition.rendered(False).receipt)
    receipt["derived"]["edge_check"] = {"verdict": "refuse"}
    repository.write(edition.rendered(False).receipt, receipt)


def stale_source(edition):
    # The captioned picture rendered again, with a receipt that binds the new bytes.
    captioned = edition.rendered(True)
    captioned.file.write_text("rendered again")
    receipt = repository.read(captioned.receipt) | {"output_sha256": repository.sha(captioned.file)}
    repository.write(captioned.receipt, receipt)


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        (changed_picture, "derived picture differs from its receipt"),
        (unproven, "records no completed derivation"),
        (stale_source, "binds another source_sha256"),
    ],
)
def test_the_verifier_refuses_a_derived_picture_that_no_longer_stands(verified, change, refusal):
    change(verified)
    with pytest.raises(PictureError, match=refusal):
        delivery_verification.verify_picture(verified)
