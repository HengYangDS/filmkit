"""The verifier's report of an edition whose uncaptioned picture is derived."""

import filmkit.delivery.verification as delivery_verification
import filmkit.picture.rendering as picture_rendering


def test_a_derived_pair_reports_the_frames_its_ground_was_checked_at(inputs, monkeypatch):
    edition = inputs.edition
    derived = {"rows": [1872, 2048], "ground_check": {"frames": 47, "verdict": "pass"}}
    inputs.change(edition.caption_equivalence, "encoded", value={"derived": derived})
    monkeypatch.setattr(
        picture_rendering, "validate_picture_binding", lambda _edition, receipt, captions=True: None
    )
    report = delivery_verification.verify_picture(edition)
    assert report["caption_equivalence"] == {
        "composition_instants": 5,
        "derived": True,
        "ground_frames": 47,
    }
