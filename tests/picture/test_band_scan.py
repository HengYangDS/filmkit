"""The caption band's one-frame scan in a derivation: the captioned picture's band rows, judged at
every frame by the comparison's own rule for a caption band, in the derivation's own decode."""

import pytest
from test_derivation import CAPTION, FRAMES, FREE, LABEL, ROWS, SIZE, encode

import filmkit.picture.derivation as derivation
import filmkit.picture.faults as faults
import filmkit.repository as repository
from filmkit.graph import runs
from filmkit.picture.derivation import BandFault

pytestmark = pytest.mark.ffmpeg

# A fragment of a glyph inside the caption for one frame, as a render's one-frame fault draws
# one: a dark square on the white caption at frame 50.
FRAGMENT = "drawbox=x=150:y=154:w=4:h=4:color=0x202020:t=fill:enable='eq(n,50)'"
# A second caption that takes the first one's place at once, in the frame after its last.
CHANGING = "drawbox=x=60:y=152:w=200:h=8:color=white:t=fill:enable='between(n,91,110)'"


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A film root for the work of a derivation, whose encodes use two threads."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.setattr(derivation, "ENCODER", ("-threads", "2", *derivation.ENCODER))
    return tmp_path.resolve()


def derived(root, *boxes, code=None, free=FREE):
    source, target = root / "captioned.mp4", root / "uncaptioned.mp4"
    encode(source, *boxes)
    work = root / "work"
    made = derivation.derive(source, target, SIZE, ROWS, free, work, edges=(8, 8), code=code)
    return made, target


def test_a_clean_picture_passes_with_its_band_scanned_at_every_frame(root):
    with runs.run("zh", "render-picture-uncaptioned", record=False) as run:
        made, target = derived(root, LABEL, CAPTION)
    assert made["band_scan"] == {
        "frames": FRAMES,
        "threshold": faults.THRESHOLD,
        "tolerance": faults.TOLERANCE,
        "changes": 0,
        "faults": [],
        "verdict": "pass",
    }
    assert target.is_file()
    # The scan's own seconds are a phase of the run, inside the encode's.
    assert 0 < run.phases["band-scan"] <= run.phases["encode"]
    command = made["command"]
    assert command[-7:] == ["-map", "[band]", *faults.RAW[:-1], "pipe:1"][-7:]
    graph = command[command.index("-filter_complex") + 1]
    assert f"crop={SIZE[0]}:{ROWS[1] - ROWS[0]}:0:{ROWS[0]},{faults.GREY}[band]" in graph


def test_a_caption_that_appears_leaves_and_changes_passes(root):
    # The first caption appears at frame 30; the second takes its place at frame 91 and leaves
    # after frame 110. The frames that read the ground end before it.
    made, target = derived(root, LABEL, CAPTION, CHANGING, free=[(2, 25), (114, 117)])
    assert (made["band_scan"]["changes"], made["band_scan"]["verdict"]) == (0, "pass")
    assert target.is_file()


def test_a_one_frame_fragment_in_the_band_refuses_naming_the_frame_and_the_captioned_render(root):
    with pytest.raises(BandFault) as refused:
        derived(root, LABEL, CAPTION, FRAGMENT, code="zh")
    assert str(refused.value) == (
        "The captioned picture's caption band changes for one frame: encoded frame 50 at 0.833 s: "
        "the captioned picture holds a one-frame fault of 219 levels in box [150, 154, 154, 158] "
        "in the caption band; render it again with filmkit build render-picture:zh"
    )
    # Nothing was put in place, and the work holds no picture.
    assert not (root / "uncaptioned.mp4").exists()
    assert not (root / "work/derived.mp4").exists()
    # Without an edition the refusal names the frame and no command.
    with pytest.raises(BandFault, match=r"frame 50 at 0\.833 s: .* in the caption band$"):
        derived(root, LABEL, CAPTION, FRAGMENT)
