"""The ground's measures: the edge rows a derivation measures at every frame, and the reader of
the measures its decode writes."""

import pytest

import filmkit.picture.ground as ground
from filmkit.picture.rendering import PictureError

GROUND = {"y": 21, "u": 129, "v": 125}


def measured(frames, changed=None, fps=60):
    """The measures as the decode writes them, each frame at the ground but for `changed`, a
    frame and the text its block gains or loses."""
    blocks = []
    for count, frame in enumerate(frames):
        block = f"frame:{count}    pts:{frame * 256}   pts_time:{frame / fps:.6f}\n"
        block += "".join(
            f"lavfi.signalstats.{plane}{end}={value}\n"
            for plane, value in zip("YUV", (21, 129, 125), strict=True)
            for end in ("MIN", "MAX")
        )
        block += "lavfi.signalstats.YAVG=21\n"
        if changed and changed[0] == frame:
            block = block.replace(*changed[1])
        blocks.append(block)
    return "".join(blocks)


@pytest.mark.parametrize(
    ("rows", "caption", "edges"),
    [
        ((1872, 2048), [960, 1000], (16, 16)),
        # A caption 5 and 3 rows of the composition from the painted rows' edges leaves 10 and 6.
        ((1872, 2048), [941, 1021], (10, 6)),
        # An odd count of free rows is brought down to an even one, for the chroma rows.
        ((1872, 2048), [939.6, 1020.4], (6, 6)),
        ((1872, 2048), [936, 1024], (0, 0)),
        ((1872, 2160), [960, 1080], (16, 0)),
    ],
)
def test_the_edge_rows_are_those_between_the_painted_edge_and_the_captions(rows, caption, edges):
    assert ground.edge_rows(rows, caption, 2.0) == edges


def test_the_filter_stacks_both_edges_or_crops_the_one_that_exists(tmp_path):
    both = ground.edge_filter("edge", (3840, 2160), (1872, 2048), (16, 8), tmp_path / "e.txt")
    assert both == (
        "[edge]split=2[edgetop][edgebottom];[edgetop]crop=3840:16:0:1872[top];"
        "[edgebottom]crop=3840:8:0:2040[bottom];[top][bottom]vstack=inputs=2,"
        f"signalstats,metadata=mode=print:file={tmp_path / 'e.txt'}[edges]"
    )
    one = ground.edge_filter("edge", (3840, 2160), (1872, 2160), (16, 0), tmp_path / "e.txt")
    printed = f"signalstats,metadata=mode=print:file={tmp_path / 'e.txt'}[edges]"
    assert one == f"[edge]crop=3840:16:0:1872,{printed}"


def test_every_frame_from_the_first_is_checked_and_the_largest_departure_kept(tmp_path):
    stats = tmp_path / "edge-stats.txt"
    stats.write_text(measured(range(6), (4, ("UMAX=129", "UMAX=131"))))
    assert ground.edge_check(stats, GROUND, 3, 60) == {
        "frames": 6,
        "largest_departure": 2,
        "verdict": "pass",
    }
    stats.write_text(measured(range(6), (3, ("YMIN=21", "YMIN=45"))))
    refusal = "another ground at the edge of the painted rows.* at frame 3: .* 24 levels"
    with pytest.raises(PictureError, match=refusal):
        ground.edge_check(stats, GROUND, 3, 60)
    stats.write_text(measured([0, 1, 3, 4]))
    with pytest.raises(PictureError, match="measured at frame 3 where frame 2 was due"):
        ground.edge_check(stats, GROUND, 3, 60)
    stats.write_text("")
    assert ground.edge_check(stats, GROUND, 3, 60)["frames"] == 0


def test_a_measure_without_all_six_extremes_is_not_readable(tmp_path):
    stats = tmp_path / "stats.txt"
    stats.write_text(measured(range(3), (1, ("lavfi.signalstats.VMAX=125\n", ""))))
    with pytest.raises(PictureError, match="measure of frame 1 is not readable"):
        list(ground.departures(stats, GROUND, 60))
