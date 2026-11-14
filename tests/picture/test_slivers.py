"""The edge slivers: the block measure of an edition's two pictures at every frame, its one-frame
transients, the slivers the record lists and the frames beyond the declared bound, which
compare-pictures refuses."""

import numpy as np
import pytest
from test_faults import NEXT, NO_SLIVERS, RENDER, box, draw, prepared, refusal

import filmkit.picture.equivalence as equivalence
import filmkit.picture.slivers as slivers

# The equivalence tests' picture: 96x54, whose caption band leaves rows 32-54 out, in cells of 8
# pixels: 7 rows of 12 cells, of which the first 4 rows are compared, in 3 blocks of 32 pixels.
SIZE, ROWS, CELL = (96, 54), (32, 54), 8


# The clause of a finding beyond the bound for edge slivers, of a dim mark of 24 by 8 samples.
DENSE = (
    f", at 192 samples of one block where at most {slivers.BOUND} may lie more than 40 levels apart"
)


def dim_mark(frames):
    """A mark 60 levels lighter than the ground, 24 by 8 samples in the first block above the
    caption band: under the fault scan's threshold at every sample."""
    return box(8, 6, 24, 8, 80, frames)


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """The Chinese edition, prepared for a comparison of the pictures a test draws."""
    return prepared(tmp_path, monkeypatch)


def cells(*held):
    """The plane the scan reads: for each cell, the share of its samples more than LEVEL levels
    apart as a byte, from (row, column, samples) of the cells that hold any."""
    plane = np.zeros((7, 12), dtype=np.uint8)
    for row, column, samples in held:
        plane[row, column] = round(255 * samples / CELL**2)
    return plane


def measured(series, rows=ROWS):
    """Blocks fed one frame after another with its densest block's samples, held in the first
    cells of the first block."""
    blocks = slivers.Blocks(SIZE, rows, CELL)
    for frame, samples in enumerate(series):
        full, rest = divmod(samples, 64)
        held = [(n // 4, n % 4, 64) for n in range(full)]
        held += [(full // 4, full % 4, rest)] if rest else []
        blocks.add(frame, cells(*held))
    return blocks


def test_the_block_measure_is_the_samples_of_the_densest_block_outside_the_caption_band():
    blocks = slivers.Blocks(SIZE, ROWS, CELL)
    # Nothing differs; then 16 and 8 samples in two cells of the second block and 20 in the third;
    # then only cells of the caption band's rows, which hold every sample.
    blocks.add(0, cells())
    blocks.add(1, cells((1, 5, 16), (0, 4, 8), (3, 11, 20)))
    blocks.add(2, cells((4, 0, 64), (5, 3, 64), (6, 11, 64)))
    assert blocks.samples == [0, 24, 0]
    assert blocks.box(blocks.densest[1]) == [32, 0, 64, 32]
    # The last block of a row or a column holds the pixels that are left.
    whole = slivers.Blocks((100, 54), (0, 0), CELL)
    assert [whole.box(index) for index in (3, 7)] == [[96, 0, 100, 32], [96, 32, 100, 54]]


def test_a_cell_s_byte_gives_back_its_samples_within_the_scaler_s_rounding():
    blocks = slivers.Blocks(SIZE, ROWS, CELL)
    for frame, samples in enumerate(range(65)):
        plane = cells((0, 0, samples))
        # The scaler may round a share one step either way.
        for step in (-1, 0, 1):
            rounded = np.clip(plane.astype(int) + step * (samples > 0), 0, 255)
            blocks.add(3 * frame + step + 1, rounded.astype(np.uint8))
    assert blocks.samples == [samples for samples in range(65) for _ in range(3)]


def test_a_one_frame_transient_exceeds_both_frames_beside_it_while_those_agree():
    #         0  1   2  3  4   5   6   7   8   9  10  11  12  13  14  15 16
    series = [0, 0, 40, 0, 0, 20, 60, 22, 10, 50, 30, 64, 64, 64, 11, 5, 17]
    # Frame 2 stands alone and frame 6 exceeds neighbours that agree within AGREEMENT; frame 9's
    # neighbours disagree, a sliver that lasts has no frame above its neighbours, frame 14 exceeds
    # frame 15 by less than JUMP, and the last frame has one neighbour only.
    assert slivers.transients(series) == [2, 6]
    assert slivers.transients([40, 0]) == [] and slivers.transients([]) == []
    assert (slivers.JUMP, slivers.AGREEMENT) == (12, 6)


def test_noted_frames_join_into_slivers_over_a_gap_of_one_frame():
    #         0   1   2   3   4   5  6   7  8  9 10 11  12 13
    series = [0, 33, 40, 12, 64, 32, 0, 50, 0, 0, 0, 0, 96, 0]
    blocks = measured(series)
    assert blocks.samples == series
    # Frames 1, 2 and 4 are one sliver, since one frame under NOTED lies between them; frame 7
    # lies two such frames from it and stands alone, as does frame 12. The densest frame of the
    # first exceeds neighbours that disagree, so it is no transient.
    assert blocks.events() == [
        {"first": 1, "last": 4, "frames": 4, "frame": 4, "samples": 64, "transient": False},
        {"first": 7, "last": 7, "frames": 1, "frame": 7, "samples": 50, "transient": True},
        {"first": 12, "last": 12, "frames": 1, "frame": 12, "samples": 96, "transient": True},
    ]
    assert slivers.NOTED == 33


def test_frames_beyond_the_bound_are_handed_to_the_fault_scan_in_runs():
    bound = slivers.BOUND
    series = [0, bound, bound + 1, 0, 0, 200, 300, 250, 0, 500, 0, 400, 0]
    blocks = measured(series)
    # Frame 2 and frame 11 stand alone, frames 5 to 7 last; frame 9 already differs by more than
    # the fault scan's own threshold, which judges it.
    held = [{"first": 9, "last": 9, "box": [0, 0, 8, 8]}]
    assert blocks.refused(held) == [
        {"first": 2, "last": 2, "box": [0, 0, 32, 32], "samples": bound + 1, "level": 40},
        {"first": 5, "last": 7, "box": [0, 0, 32, 32], "samples": 300, "level": 40},
        {"first": 11, "last": 11, "box": [0, 0, 32, 32], "samples": 400, "level": 40},
    ]
    assert measured([0, bound, 64, 0]).refused([]) == []


def test_a_refused_frame_s_box_covers_each_block_beyond_the_bound():
    blocks = slivers.Blocks(SIZE, ROWS, CELL)
    # Two cells of the first block and three of the third hold every sample; the second block
    # holds 64, within the bound.
    full = [(0, 0, 64), (0, 1, 64), (1, 8, 64), (1, 9, 64), (2, 10, 64)]
    blocks.add(0, cells(*full, (0, 5, 64)))
    assert blocks.samples == [192]
    assert blocks.refused([]) == [
        {"first": 0, "last": 0, "box": [0, 0, 96, 32], "samples": 192, "level": 40}
    ]


def test_the_report_lists_the_largest_slivers_with_their_measured_levels():
    # The caption band starts in the first block's rows.
    series, rows = [0, 0, 40, 0, 0, 64, 64, 64, 0, 0, 20, 0, 0], (16, 54)
    blocks = measured(series, rows)
    asked = []

    def difference(frame, box):
        """The pictures' difference within a box: 47 levels in the compared rows, and more in
        the rows of the caption band, which a block's box may reach."""
        asked.append((frame, box))
        plane = np.full((box[3] - box[1], box[2] - box[0]), 47, dtype=np.int16)
        plane[rows[0] - box[1] :] = 200
        return plane

    report = blocks.report(60, difference)
    assert report == {
        "level": 40,
        "block_pixels": 32,
        "bound": slivers.BOUND,
        "noted_from": 33,
        "jump": 12,
        "agreement": 6,
        "largest": 64,
        "transient_frames": 2,
        "events": [
            {
                "first": 5,
                "last": 7,
                "frames": 3,
                "time": 0.083,
                "frame": 5,
                "block": [0, 0, 32, 32],
                "samples": 64,
                "level": 47,
                "transient": False,
            },
            {
                "first": 2,
                "last": 2,
                "frames": 1,
                "time": 0.033,
                "frame": 2,
                "block": [0, 0, 32, 32],
                "samples": 40,
                "level": 47,
                "transient": True,
            },
        ],
        "event_runs": 2,
        "frames_beyond_the_bound": 0,
    }
    # Only the listed slivers are decoded again, each at its densest frame.
    assert asked == [(5, [0, 0, 32, 32]), (2, [0, 0, 32, 32])]
    many = measured([0, 0, 50] * 30)
    listed = many.report(60, difference)
    assert (len(listed["events"]), listed["event_runs"]) == (slivers.LISTED, 30)
    assert slivers.Blocks(SIZE, ROWS, CELL).report(60, difference)["largest"] == 0


@pytest.mark.ffmpeg
def test_a_dim_mark_missing_for_one_frame_is_refused_and_names_its_picture(edition):
    # The mark stands from frame 60 in both pictures; the uncaptioned one lacks it at frame 77.
    draw(
        edition,
        captioned=[dim_mark("gte(n,60)")],
        uncaptioned=[dim_mark("gte(n,60)*not(eq(n,77))")],
    )
    message, record = refusal(edition)
    fault = (
        "encoded frame 77 at 1.283 s: the uncaptioned picture holds a one-frame fault of 60 levels "
        f"in box [8, 6, 32, 14] outside the caption band{DENSE}; render it again with {RENDER} "
        "--uncaptioned"
    )
    assert message == f"The zh pictures differ beyond their captions: {fault}{NEXT}"
    every = record["encoded"]["every_frame"]
    # No sample lies more than 90 levels apart: the block measure alone finds the frame.
    assert (every["differing_frames"], every["fault_frames"], every["lasting"]) == (0, 1, [])
    assert every["faults"] == [
        {
            "frame": 77,
            "time": 1.283,
            "box": [8, 6, 32, 14],
            "peak": 60,
            "picture": "uncaptioned",
            "caption_band": False,
            "residue": False,
            "samples": 192,
        }
    ]
    assert every["slivers"] == {
        **NO_SLIVERS,
        "largest": 192,
        "transient_frames": 1,
        "events": [
            {
                "first": 77,
                "last": 77,
                "frames": 1,
                "frame": 77,
                "samples": 192,
                "transient": True,
                "time": 1.283,
                "block": [0, 0, 32, 32],
                "level": 60,
            }
        ],
        "event_runs": 1,
        "frames_beyond_the_bound": 1,
    }


@pytest.mark.ffmpeg
def test_edge_slivers_within_the_bound_are_recorded_and_pass(edition):
    # As the DDWG film's two English masters drew a rail on five frames apart: two rows across the
    # second block, 45 levels lighter, in the captioned picture from frame 70 to 74. And one row
    # for one frame, at frame 20, a transient under the samples from which a sliver is listed.
    draw(
        edition,
        captioned=[box(32, 10, 32, 2, 65, "between(n,70,74)"), box(32, 20, 32, 1, 65, "eq(n,20)")],
    )
    record = equivalence.compare_pictures(edition)
    assert (record["verdict"], record["findings"]) == ("pass", [])
    every = record["encoded"]["every_frame"]
    assert (every["differing_frames"], every["fault_frames"], every["faults"]) == (0, 0, [])
    assert every["slivers"] == {
        **NO_SLIVERS,
        "largest": 64,
        "transient_frames": 1,
        "events": [
            {
                "first": 70,
                "last": 74,
                "frames": 5,
                "frame": 70,
                "samples": 64,
                "transient": False,
                "time": 1.167,
                "block": [32, 0, 64, 32],
                "level": 45,
            }
        ],
        "event_runs": 1,
    }


@pytest.mark.ffmpeg
def test_a_dim_difference_beyond_the_bound_that_lasts_names_its_frames(edition):
    draw(
        edition,
        captioned=[dim_mark("gte(n,60)")],
        uncaptioned=[dim_mark("gte(n,60)*not(between(n,70,74))")],
    )
    message, record = refusal(edition)
    assert message.endswith(
        "encoded frames 70-74: the pictures differ by more than 40 levels in box [0, 0, 32, 32] "
        f"outside the caption band{DENSE}"
    )
    every = record["encoded"]["every_frame"]
    run = {"first": 70, "last": 74, "box": [0, 0, 32, 32], "samples": 192, "level": 40}
    assert (every["lasting"], every["lasting_runs"], every["faults"]) == ([run], 1, [])
    assert every["slivers"]["frames_beyond_the_bound"] == 5


def test_the_findings_name_the_bound_of_a_dim_difference_that_no_one_picture_holds():
    row = {
        "frame": 9,
        "time": 0.15,
        "box": [8, 6, 32, 14],
        "peak": 60,
        "picture": None,
        "caption_band": False,
        "residue": False,
        "samples": 192,
    }
    report = {"threshold": 90, "faults": [row], "fault_frames": 1, "lasting": [], "lasting_runs": 0}
    assert equivalence.faults.findings(report, "en") == [
        "encoded frame 9 at 0.150 s: the pictures differ for one frame by 60 levels in box "
        f"[8, 6, 32, 14] outside the caption band{DENSE}, and no one picture alone departs from "
        "its neighbouring frames"
    ]
