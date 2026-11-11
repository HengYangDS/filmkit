"""The one-frame faults: compare-pictures compares every frame of an edition's two pictures outside
the caption band, scans each picture's caption band against its own neighbouring frames, and names
the picture to render again."""

import subprocess

import numpy as np
import pytest

import filmkit.picture.equivalence as equivalence
import filmkit.produce as produce
import filmkit.repository as repository
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError
from filmkit.production import Edition

# The equivalence tests' pictures: two seconds at 60 fps of 96x54 frames on a ground of full-range
# grey 20, the captioned one with a white caption from 0.5 s to 1 s in rows 44-49. The caption band
# leaves rows 32-54 out of the comparison of the two pictures, and the sampled frames are 0, 30, 45,
# 60 and 90.
SIZE, SECONDS = (96, 54), 2
GROUND = "0x0F1519"
CAPTION = "drawbox=x=30:y=44:w=36:h=6:color=white:t=fill:enable='between(t,0.5,1)'"
LABEL = "drawbox=x=8:y=6:w=24:h=8:color=white:t=fill:enable='between(t,0.5,1)'"
BAND = {"left": 600, "top": 880, "right": 1320, "bottom": 1000}
CUES = [{"start": 0.5, "end": 1.0, "text": "One."}]
RENDER = "python -m filmkit.produce render-picture --language zh"
# The next step a refusal names when repair-pictures can answer each of its findings.
NEXT = "; next: python -m filmkit.produce repair-pictures --language zh"


def square(x, y, grey, frames):
    """A 4x4 square of full-range `grey` at (x, y), drawn in the frames the expression selects."""
    colour = f"0x{grey:02X}{grey:02X}{grey:02X}"
    return f"drawbox=x={x}:y={y}:w=4:h=4:color={colour}:t=fill:enable='{frames}'"


# A glyph fragment 150 levels lighter than the ground above the caption band at frame 77, which is
# not sampled, and a fragment 150 levels darker than the caption inside it at frame 50.
FRAGMENT = square(40, 10, 170, "eq(n,77)")
BROKEN = square(40, 44, 105, "eq(n,50)")


def encode(path, *boxes):
    """A lossless picture of the ground with the given boxes drawn on it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    picture = f"color=c={GROUND}:s={SIZE[0]}x{SIZE[1]}:r=60:d={SECONDS}"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "lavfi", "-i", picture]
        + (["-vf", ",".join(boxes)] if boxes else [])
        + ["-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(path)],
        check=True,
        capture_output=True,
        timeout=60,
    )


def draw(edition, captioned=(), uncaptioned=()):
    """Render the edition's pictures: the captioned one with its caption, each with its boxes."""
    encode(edition.rendered(True).file, CAPTION, *captioned)
    encode(edition.rendered(False).file, *uncaptioned)


def reporting(band):
    """The caption-equivalence tool, reporting that the compositions differ only by their
    captions, whose paints cover `band`."""

    def run(_tool, _arguments, *, stdout, environment=None):
        report = {"instants": 7, "band": band, "differing_instants": 0, "findings": []}
        repository.write(stdout, report)
        return 0

    return run


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """The Chinese edition with valid pictures, its timeline, its composition and a composition
    report that finds no paint apart from the captions."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.setattr(equivalence, "PICTURE_SIZE", SIZE)
    monkeypatch.setattr(equivalence, "DURATION", SECONDS)
    monkeypatch.setattr(equivalence, "validate_picture", lambda _edition, captions: {})
    monkeypatch.setattr(equivalence.tools, "run", reporting(BAND))
    edition = Edition("zh")
    repository.write(edition.timeline, {"duration": SECONDS, "captions": CUES})
    (tmp_path / COMPOSITION_SCRIPT).parent.mkdir(parents=True)
    (tmp_path / COMPOSITION_SCRIPT).write_text("/* film */")
    for captions in (True, False):
        rendered = edition.rendered(captions)
        rendered.stage.mkdir(parents=True)
        (rendered.stage / "index.html").write_text(f"<html>{rendered.name}</html>")
        repository.write(rendered.receipt, {"picture": rendered.name})
    return edition


def refusal(edition):
    """compare-pictures' refusal of the edition and the record it wrote."""
    with pytest.raises(PictureError) as refused:
        equivalence.compare_pictures(edition)
    return str(refused.value), repository.read(edition.caption_equivalence)


@pytest.mark.ffmpeg
def test_a_glyph_fragment_for_one_frame_between_the_sampled_frames_is_refused(edition):
    draw(edition, captioned=[FRAGMENT])
    message, record = refusal(edition)
    fault = (
        "encoded frame 77 at 1.283 s: the captioned picture holds a one-frame fault of 150 levels "
        f"in box [40, 10, 44, 14] outside the caption band; render it again with {RENDER}"
    )
    assert message == f"The zh pictures differ beyond their captions: {fault}{NEXT}"
    assert (record["findings"], record["verdict"]) == ([fault], "refuse")
    # The sampled frames pass; the comparison of every frame finds the fragment.
    assert record["encoded"]["failing_frames"] == 0
    every = record["encoded"]["every_frame"]
    assert (every["frames"], every["differing_frames"], every["lasting"]) == (120, 1, [])
    assert every["faults"] == [
        {
            "frame": 77,
            "time": 1.283,
            "box": [40, 10, 44, 14],
            "peak": 150,
            "picture": "captioned",
            "caption_band": False,
            "residue": False,
        }
    ]


@pytest.mark.ffmpeg
def test_a_caption_glyph_broken_for_one_frame_is_refused_in_the_caption_band(edition):
    draw(edition, captioned=[BROKEN])
    message, record = refusal(edition)
    assert message.endswith(
        "encoded frame 50 at 0.833 s: the captioned picture holds a one-frame fault of 150 levels "
        f"in box [40, 44, 44, 48] in the caption band; render it again with {RENDER}{NEXT}"
    )
    every = record["encoded"]["every_frame"]
    # The two pictures are not compared in the band; each is judged by its own frames.
    assert every["differing_frames"] == 0
    assert every["band_changes"] == {"captioned": 1, "uncaptioned": 0}
    assert every["faults"] == [
        {
            "frame": 50,
            "time": 0.833,
            "box": [40, 44, 44, 48],
            "peak": 150,
            "picture": "captioned",
            "caption_band": True,
            "residue": False,
        }
    ]


@pytest.mark.ffmpeg
def test_differences_under_ninety_levels_spread_over_frames_pass(edition):
    # Squares 80 levels from what stands around them, at frames none of which is sampled: lighter
    # than the ground above the band at frames 20 and 22 and from frame 100 to 104 and in the band
    # at frame 40 in the uncaptioned picture, and darker than the caption at frame 50.
    draw(
        edition,
        captioned=[square(50, 44, 175, "eq(n,50)")],
        uncaptioned=[
            square(60, 20, 100, "eq(n,20)+eq(n,22)+between(n,100,104)"),
            square(10, 46, 100, "eq(n,40)"),
        ],
    )
    record = equivalence.compare_pictures(edition)
    assert (record["verdict"], record["findings"]) == ("pass", [])
    every = record["encoded"]["every_frame"]
    assert (every["frames"], every["differing_frames"], every["fault_frames"]) == (120, 0, 0)
    assert every["band_changes"] == {"captioned": 0, "uncaptioned": 0}
    assert every["residue_frames"] == 0


@pytest.mark.ffmpeg
def test_a_caption_that_appears_and_leaves_passes(edition):
    # Beside the caption of 0.5 s to 1 s, a second caption stands for two frames only.
    draw(edition, captioned=[square(70, 44, 255, "between(n,80,81)")])
    record = equivalence.compare_pictures(edition)
    assert record["verdict"] == "pass"
    assert record["encoded"]["every_frame"] == {
        "frames": 120,
        "threshold": 90,
        "tolerance": 30,
        "cell_pixels": 8,
        "differing_frames": 0,
        "lasting": [],
        "lasting_runs": 0,
        "band_changes": {"captioned": 0, "uncaptioned": 0},
        "faults": [],
        "fault_frames": 0,
        "residue_frames": 0,
    }


@pytest.mark.ffmpeg
def test_a_fault_in_the_uncaptioned_picture_names_its_render_command(edition):
    draw(edition, uncaptioned=[FRAGMENT])
    message, record = refusal(edition)
    command = f"{RENDER} --uncaptioned"
    assert message.endswith(
        "encoded frame 77 at 1.283 s: the uncaptioned picture holds a one-frame fault of 150 "
        f"levels in box [40, 10, 44, 14] outside the caption band; render it again with {command}"
        f"{NEXT}"
    )
    faults = record["encoded"]["every_frame"]["faults"]
    assert [(fault["frame"], fault["picture"]) for fault in faults] == [(77, "uncaptioned")]
    # The production command takes the command the refusal names.
    options = produce.arguments().parse_args(command.split()[3:])
    assert (options.action, options.language, options.uncaptioned) == ("render-picture", "zh", True)


@pytest.mark.ffmpeg
def test_a_difference_that_lasts_names_its_frames_and_no_picture(edition):
    draw(edition, uncaptioned=[LABEL])
    message, record = refusal(edition)
    assert message.endswith(
        "encoded frames 30-60: the pictures differ by more than 90 levels in box [8, 0, 32, 16] "
        "outside the caption band"
    )
    every = record["encoded"]["every_frame"]
    assert every["lasting"] == [{"first": 30, "last": 60, "box": [8, 0, 32, 16]}]
    assert (every["differing_frames"], every["lasting_runs"], every["faults"]) == (31, 1, [])


def moving_bar(edition, edge):
    """Render both pictures with a bar of grey 200, 4 px wide and 8 high above the band, moving
    2 px a frame from x 10 at frame 60 to frame 80, so each sample it covers stands for two frames.
    At frame 70 the captioned picture draws one sample of the bar's trailing edge in grey `edge`,
    as two encodes may draw a moving edge apart; its frames 69 and 71 there, 200 and 20,
    disagree."""
    bar = [
        f"drawbox=x={10 + 2 * (n - 60)}:y=8:w=4:h=8:color=0xC8C8C8:t=fill:enable='eq(n,{n})'"
        for n in range(60, 81)
    ]
    sample = f"0x{edge:02X}{edge:02X}{edge:02X}"
    residue = f"drawbox=x=30:y=10:w=1:h=1:color={sample}:t=fill:enable='eq(n,70)'"
    draw(edition, captioned=[*bar, residue], uncaptioned=bar)


@pytest.mark.ffmpeg
def test_a_moving_mark_s_residue_for_one_frame_is_recorded_and_passes(edition):
    # 93 levels apart, as the DDWG film's two Chinese encodes drew a moving mark at frame 30306.
    moving_bar(edition, 107)
    record = equivalence.compare_pictures(edition)
    assert (record["verdict"], record["findings"]) == ("pass", [])
    every = record["encoded"]["every_frame"]
    assert (every["differing_frames"], every["fault_frames"], every["residue_frames"]) == (1, 0, 1)
    assert every["faults"] == [
        {
            "frame": 70,
            "time": 1.167,
            "box": [30, 10, 31, 11],
            "peak": 93,
            "picture": None,
            "caption_band": False,
            "residue": True,
        }
    ]


@pytest.mark.ffmpeg
def test_a_one_frame_difference_above_the_ceiling_that_no_picture_holds_is_refused(edition):
    moving_bar(edition, 50)
    message, record = refusal(edition)
    assert message.endswith(
        "encoded frame 70 at 1.167 s: the pictures differ for one frame by 150 levels in box "
        "[30, 10, 31, 11] outside the caption band, above a residue's ceiling of 120, and no one "
        "picture alone departs from its neighbouring frames"
    )
    assert "render-picture" not in message
    every = record["encoded"]["every_frame"]
    faults = [(row["frame"], row["picture"], row["residue"]) for row in every["faults"]]
    assert (faults, every["fault_frames"], every["residue_frames"]) == ([(70, None, False)], 1, 0)


@pytest.mark.ffmpeg
def test_without_a_caption_band_every_row_is_compared(edition, monkeypatch):
    # A composition that paints no caption reports no band: the pictures are compared in every
    # row, and no band is scanned.
    monkeypatch.setattr(equivalence.tools, "run", reporting(None))
    encode(edition.rendered(True).file)
    encode(edition.rendered(False).file, square(40, 44, 170, "eq(n,50)"))
    message, record = refusal(edition)
    assert message.endswith(
        "encoded frame 50 at 0.833 s: the uncaptioned picture holds a one-frame fault of 150 "
        f"levels in box [40, 44, 44, 48] outside the caption band; render it again with {RENDER} "
        f"--uncaptioned{NEXT}"
    )
    encoded = record["encoded"]
    assert (encoded["excluded_rows"], encoded["every_frame"]["band_changes"]) == ([0, 0], {})


def test_the_band_scan_finds_only_a_frame_far_from_both_neighbours_that_agree():
    band = equivalence.faults.Band(top=32)
    frames = np.full((9, 4, 16), 20, dtype=np.uint8)
    # A mark three samples wide moves one sample a frame along row 0, so each sample it covers
    # stands for three frames.
    for n, frame in enumerate(frames):
        frame[0, n : n + 3] = 200
    # A caption appears at frame 2 and leaves after frame 6; at frame 4 four of its samples are
    # 150 levels darker.
    frames[2:7, 1:3, 2:10] = 255
    frames[4, 1:3, 4:6] = 105
    # A mark fades in by 40 levels a frame, and one flickers by 60 levels for one frame.
    frames[:, 3, 12:14] = np.minimum(255, 20 + 40 * np.arange(9))[:, None]
    frames[7, 3, 0:2] = 80
    for n, frame in enumerate(frames):
        band.add(n, frame)
    assert band.changes == [{"frame": 4, "box": [4, 33, 6, 35], "peak": 150}]


def test_the_twin_cells_leave_the_caption_band_out_and_join_consecutive_frames():
    twin = equivalence.faults.Twin((96, 54), (32, 54))
    assert twin.shape == (7, 12)
    lit = {3: [(1, 5)], 4: [(1, 5), (2, 6)], 6: [(5, 3)], 8: [(0, 0), (3, 11)]}
    for frame in range(10):
        cells = np.zeros((7, 12), dtype=np.uint8)
        for row, column in lit.get(frame, []):
            cells[row, column] = 4
        twin.add(frame, cells)
    # Frame 6 differs only in the cells of the caption band's rows.
    assert twin.frames == 3
    assert twin.runs == [
        {"first": 3, "last": 4, "box": [40, 8, 56, 24]},
        {"first": 8, "last": 8, "box": [0, 0, 96, 32]},
    ]


def test_a_frame_departs_from_the_neighbouring_frames_it_has():
    departs, where = equivalence.faults.departs, np.ones((2, 2), dtype=bool)
    ground = np.full((3, 2, 2), 20, dtype=np.uint8)
    flash, step, ramp = ground.copy(), ground.copy(), ground.copy()
    flash[1], step[1:], ramp[1:] = 170, 170, [[[150]], [[255]]]
    assert departs(flash, 1, where) and not departs(ground, 1, where)
    # A frame that its next frame keeps, and one between neighbours that disagree, do not depart.
    assert not departs(step, 1, where) and not departs(ramp, 1, where)
    # The first and last frames have one neighbouring frame each.
    assert departs(flash[1:], 0, where) and departs(flash[:2], 1, where)
    assert not departs(flash, 1, np.zeros((2, 2), dtype=bool))


def test_the_findings_leave_residues_out_and_count_the_differences_not_listed():
    residue = {
        "frame": 7,
        "time": 0.117,
        "box": [0, 0, 1, 1],
        "peak": 93,
        "picture": None,
        "caption_band": False,
        "residue": True,
    }
    fault = {**residue, "frame": 9, "time": 0.15, "peak": 200, "picture": "captioned"}
    report = {"threshold": 90, "faults": [fault | {"residue": False}, residue], "fault_frames": 3}
    assert equivalence.faults.findings({**report, "lasting": [], "lasting_runs": 0}, "en") == [
        "encoded frame 9 at 0.150 s: the captioned picture holds a one-frame fault of 200 levels "
        "in box [0, 0, 1, 1] outside the caption band; render it again with "
        "python -m filmkit.produce render-picture --language en",
        "encoded: 2 more one-frame differences",
    ]
