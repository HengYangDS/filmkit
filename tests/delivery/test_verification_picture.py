"""The verifier's binding of both rendered pictures, their equivalence, the captioned picture's
geometry and its shot plan."""

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.delivery.verification import VerificationError
from filmkit.picture.rendering import PictureError


def test_the_current_picture_passes(inputs, monkeypatch):
    edition = inputs.edition
    bound = []
    monkeypatch.setattr(
        picture_rendering,
        "validate_picture_binding",
        lambda _edition, receipt, captions=True: bound.append((receipt["picture"], captions)),
    )
    assert delivery_verification.verify_picture(edition) == {
        "picture_sha256": repository.sha(edition.picture),
        "uncaptioned_picture_sha256": repository.sha(edition.rendered(captions=False).file),
        "caption_equivalence": {"composition_instants": 5, "encoded_frames": 4},
        "geometry_frames": 60,
        "browser": "Chromium",
    }
    # Each receipt is bound to its own picture.
    assert bound == [("captioned", True), ("uncaptioned", False)]


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("verdict", "did not pass"),
        ("timeline_sha256", "binds another timeline_sha256"),
        ("pictures", "binds another pictures"),
    ],
)
def test_pictures_without_their_current_passing_equivalence_are_refused(inputs, change, reason):
    inputs.change(inputs.edition.caption_equivalence, change, value="refuse")
    with pytest.raises(PictureError, match=reason):
        delivery_verification.verify_picture(inputs.edition)
    inputs.edition.caption_equivalence.unlink()
    with pytest.raises(PictureError, match="no equivalence record; run compare-pictures"):
        delivery_verification.verify_picture(inputs.edition)


# The short films last two seconds at 60 fps, so geometry of every second frame checks 60.
@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("format", "frame-audit"),
        ("passed", False),
        ("findings", [{"frame": 12}]),
        ("errors", ["timeout"]),
        ("index_sha256", "0" * 64),
        ("width", 1920),
        ("duration", 3),
        ("fps", 30),
        ("step_frames", 3),
        ("checked", 120),
    ],
)
def test_geometry_that_does_not_cover_the_staged_film_is_refused(inputs, key, value):
    inputs.change(inputs.edition.picture_geometry, key, value=value)
    with pytest.raises(VerificationError, match="does not cover the current staged film"):
        delivery_verification.verify_picture(inputs.edition)


def test_a_restaged_picture_is_refused(inputs):
    (inputs.edition.picture_stage / "index.html").write_text("<html>restaged</html>")
    with pytest.raises(VerificationError, match="does not cover the current staged film"):
        delivery_verification.verify_picture(inputs.edition)


@pytest.mark.parametrize("key", ["script_sha256", "composition_sha256", "timeline_sha256"])
def test_a_shot_plan_of_other_picture_inputs_is_refused(inputs, key):
    inputs.change(inputs.root / inputs.edition.shot_plan, key, value="0" * 64)
    with pytest.raises(VerificationError, match="Shot plan differs"):
        delivery_verification.verify_picture(inputs.edition)
