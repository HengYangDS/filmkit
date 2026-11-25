"""The commands a refusal of a rendered pair names: the uncaptioned picture is rendered again from
its own stage, which the film declares in `[picture] native_uncaptioned`, since without it the
node may derive the picture."""

import filmkit.picture.faults as faults


def test_the_uncaptioned_picture_of_a_rendered_pair_is_rendered_again_natively():
    # The picture's node is fresh, so its file goes first and the build then renders it.
    picture = "build/artifacts/film/en/sample-reel-final-picture"
    assert faults.render_again("en", "captioned") == (
        f"filmkit build render-picture:en, after removing {picture}.mp4"
    )
    assert faults.render_again("en", "uncaptioned") == (
        "filmkit build render-picture-uncaptioned:en with en in [picture] native_uncaptioned, "
        f"after removing {picture}-uncaptioned.mp4"
    )


def test_a_fault_of_the_uncaptioned_picture_names_the_native_render():
    row = {"frame": 77, "time": 1.283, "peak": 150, "box": [40, 10, 44, 14]}
    row |= {"picture": "uncaptioned", "caption_band": False, "residue": False}
    report = {"faults": [row], "fault_frames": 1, "lasting": [], "lasting_runs": 0}
    found = faults.findings(report, "zh")[0]
    assert found.endswith(
        "render it again with filmkit build render-picture-uncaptioned:zh with zh in [picture] "
        "native_uncaptioned, after removing build/artifacts/film/zh/"
        "sample-reel-final-picture-uncaptioned.mp4"
    )
