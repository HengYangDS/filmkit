"""The commands a refusal of a rendered pair names: the uncaptioned picture is rendered again from
its own stage, which the film declares in `[picture] native_uncaptioned`, since without it the
node may derive the picture."""

import filmkit.picture.faults as faults


def test_the_uncaptioned_picture_of_a_rendered_pair_is_rendered_again_natively():
    assert faults.render_again("en", "captioned") == "filmkit build render-picture:en"
    assert faults.render_again("en", "uncaptioned") == (
        "filmkit build render-picture-uncaptioned:en with en in [picture] native_uncaptioned"
    )


def test_a_fault_of_the_uncaptioned_picture_names_the_native_render():
    row = {"frame": 77, "time": 1.283, "peak": 150, "box": [40, 10, 44, 14]}
    row |= {"picture": "uncaptioned", "caption_band": False, "residue": False}
    report = {"faults": [row], "fault_frames": 1, "lasting": [], "lasting_runs": 0}
    found = faults.findings(report, "zh")[0]
    assert found.endswith(
        "render it again with filmkit build render-picture-uncaptioned:zh with zh in [picture] "
        "native_uncaptioned"
    )
