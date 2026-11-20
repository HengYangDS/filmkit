"""One decode for both phases of the still scan: the frames FFmpeg is asked to keep and how they
are dealt to their phases, on a stand-in for the FFmpeg process, so that the form is held where
FFmpeg is absent."""

import re
import subprocess

import numpy as np
import pytest

import filmkit.picture.still_scan as still_scan
import filmkit.repository as repository

TERM = re.compile(r"eq\(mod\(n\\,(\d+)\)\\,(\d+)\)")
WORDS = {"segments": [{"words": [{"start": 0.5, "end": 5.5}]}]}


def picture(n: int) -> bytes:
    """Frame `n` of a film: its number in its first row, outside the scan's band, and a square
    in the band that moves on some frames and stands on others."""
    frame = np.full((still_scan.HEIGHT, still_scan.WIDTH), 15, dtype=np.uint8)
    frame[0, :4] = np.frombuffer(n.to_bytes(4, "little"), np.uint8)
    x = 60 + 7 * ((n // 37) % 40) + (3 if (n // 5) % 9 == 0 else 0)
    frame[100:120, x : x + 20] = 200
    return frame.tobytes()


class Film:
    """Stand in for `subprocess.Popen` on a film of `frames` frames: each process started gives
    the frames that the select expression of its command keeps, in the film's order."""

    def __init__(self, frames: int) -> None:
        self.frames, self.commands = frames, []

    def __call__(self, command, **_):
        self.commands.append(command)
        select, filters = re.fullmatch(r"select='([^']*)',(.*)", command[-6]).groups()
        assert (command[-7], filters) == ("-vf", still_scan.DECODE)
        terms = [(int(every), int(phase)) for every, phase in TERM.findall(select)]
        assert still_scan.sampling(terms[0][0], tuple(phase for _, phase in terms)) == select
        kept = [n for n in range(self.frames) if any(n % e == p for e, p in terms)]
        return Process(kept)


class Process:
    def __init__(self, kept: list[int]) -> None:
        self.kept, self.returncode, self.stdout = iter(kept), None, self

    def read(self, _size: int) -> bytes:
        return picture(n) if (n := next(self.kept, None)) is not None else b""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.returncode = 0


def test_the_select_expression_keeps_one_frame_of_each_distinct_phase():
    assert still_scan.sampling(6, (0, 3)) == "eq(mod(n\\,6)\\,0)+eq(mod(n\\,6)\\,3)"
    assert still_scan.sampling(6, (3,)) == "eq(mod(n\\,6)\\,3)"
    # At 30 fps and at the scan's own rate both phases select the same frames.
    assert still_scan.sampling(3, (0, 3)) == "eq(mod(n\\,3)\\,0)"
    assert still_scan.sampling(1, (0, 3)) == "eq(mod(n\\,1)\\,0)"


@pytest.mark.parametrize(
    ("rate", "frames"), [(60, 360), (60, 361), (60, 365), (60, 7), (30, 181), (20, 41), (10, 60)]
)
def test_one_decode_deals_each_phase_the_frames_a_decode_of_its_own_reads(
    tmp_path, monkeypatch, rate, frames
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.setattr(still_scan, "frame_rate", lambda _movie: rate)
    film = Film(frames)
    monkeypatch.setattr(subprocess, "Popen", film)
    dealt = []

    class Noting(still_scan.Stills):
        """A phase's still flags, with the number of each frame it was dealt."""

        def __init__(self) -> None:
            super().__init__()
            self.numbers = []
            dealt.append(self.numbers)

        def add(self, frame) -> None:
            self.numbers.append(int.from_bytes(frame[0, :4].tobytes(), "little"))
            super().add(frame)

    every = rate // still_scan.FPS
    offsets = [phase % every for phase in still_scan.PHASES]
    reads = {offset: [n for n in range(frames) if n % every == offset] for offset in offsets}
    with monkeypatch.context() as patch:
        patch.setattr(still_scan, "Stills", Noting)
        together = still_scan.phase_reports(tmp_path / "film.mp4", WORDS)
    # One process decodes the film once, and each distinct phase is dealt its own frames.
    assert len(film.commands) == 1
    assert dealt == [reads[offset] for offset in sorted(set(offsets))]
    assert [report["frames"] for report in together] == [len(reads[offset]) for offset in offsets]
    alone = [
        still_scan.scan(still_scan.decode(tmp_path / "film.mp4", (phase,)), WORDS)
        for phase in still_scan.PHASES
    ]
    assert together == alone
