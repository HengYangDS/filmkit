"""The commands a refusal of a rendered pair names: the uncaptioned picture is rendered again by
`render-picture --uncaptioned --native`, since without `--native` that command may derive."""

import filmkit.picture.faults as faults


def test_the_uncaptioned_picture_of_a_rendered_pair_is_rendered_again_natively():
    render = "python -m filmkit.produce render-picture --language en"
    assert faults.render_again("en", "captioned") == render
    assert faults.render_again("en", "uncaptioned") == f"{render} --uncaptioned --native"


def test_a_fault_of_the_uncaptioned_picture_names_the_native_render():
    row = {"frame": 77, "time": 1.283, "peak": 150, "box": [40, 10, 44, 14]}
    row |= {"picture": "uncaptioned", "caption_band": False, "residue": False}
    report = {"faults": [row], "fault_frames": 1, "lasting": [], "lasting_runs": 0}
    found = faults.findings(report, "zh")[0]
    assert found.endswith(
        "render it again with python -m filmkit.produce render-picture --language zh "
        "--uncaptioned --native"
    )
