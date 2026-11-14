"""Exercise the voice clarity measure on small synthetic signals."""

import wave

import numpy as np
import pytest

import filmkit.review.clarity as review_clarity

RATE = review_clarity.RATE


def harmonic(seconds, f0=150.0, rate=RATE):
    """A clear voice: every harmonic of f0 up to 4 kHz at one level."""
    t = np.arange(round(seconds * rate)) / rate
    return sum(np.sin(2 * np.pi * k * f0 * t) for k in range(1, int(4000 // f0) + 1)) / 20


def noise(seconds, rate=RATE, seed=1):
    """Breath: white noise without a pitch period."""
    return np.random.default_rng(seed).normal(0, 0.1, round(seconds * rate))


def stated_frames(samples, phase=0, threshold=None):
    """The reviewers' steps 2 to 6, frame by frame, with NumPy's own least squares: each kept
    frame's centre in seconds and its prominence, on the grid that starts `phase` samples in,
    and the threshold, which is that grid's own unless one is given."""
    starts = range(phase, len(samples) - 1023, 256)
    frames = [samples[start : start + 1024] for start in starts]
    energy = np.array([10 * np.log10(np.sum(frame**2) + 1e-20) for frame in frames])
    if threshold is None:
        threshold = np.percentile(energy, 95) - 18
    window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(1024) / 1024)
    bins = np.arange(40, 267)
    kept = []
    for start, frame, level in zip(starts, frames, energy, strict=True):
        if level < threshold:
            continue
        spectrum = 10 * np.log10(np.abs(np.fft.rfft(frame * window)) ** 2 + 1e-20)
        cepstrum = np.fft.irfft(spectrum, n=1024)
        peaks = 20 * np.log10(np.abs(cepstrum[40:267]) + 1e-20)
        design = np.vstack([bins, np.ones(len(bins))]).T
        (slope, intercept), *_ = np.linalg.lstsq(design, peaks, rcond=None)
        top = int(np.argmax(peaks))
        kept.append(((start + 512) / 16000, peaks[top] - (slope * bins[top] + intercept)))
    return kept, threshold


def stated_method(samples):
    """The reviewers' steps 2 to 7: the median prominence over the kept frames, and their count."""
    kept, _ = stated_frames(samples)
    return float(np.median([value for _, value in kept])), len(kept)


def stated_span(kept, start, end):
    """The prominences of the kept frames whose centres lie in [start, end) seconds."""
    return [value for centre, value in kept if start <= centre < end]


def test_clarity_follows_the_stated_method_and_keeps_only_the_loud_frames():
    voice = np.concatenate([harmonic(1.0) + 0.5 * noise(1.0), np.zeros(RATE)])
    measured = review_clarity.prominence(voice.astype(np.float32))
    expected, kept = stated_method(voice.astype(np.float32).astype(np.float64))
    assert measured.median_db == pytest.approx(expected, abs=1e-9)
    # The 59 frames inside the voice and the 4 that overlap its end; the silence is not kept.
    assert measured.frames == kept == 63
    assert review_clarity.prominence(np.zeros(1000)) == (None, 0)


def test_a_clear_voice_stands_above_a_breathy_one():
    clear = review_clarity.prominence(harmonic(1.0)).median_db
    breathy = review_clarity.prominence(harmonic(1.0) + 3 * noise(1.0)).median_db
    breath = review_clarity.prominence(noise(1.0)).median_db
    assert clear > 25 > 20 > breathy > breath


def segment(name, start, end, words, groups=None):
    """A timeline segment from `start` to `end` seconds: its words as (text, start, end), and
    its thoughts, one unless `groups` names more."""
    text = " ".join(word for word, _, _ in words) + " "
    return {
        "id": name,
        "start": start,
        "end": end,
        "text": text,
        "utterance_groups": groups or [text],
        "words": [{"text": word, "start": a, "end": b} for word, a, b in words],
    }


def breathy(seconds, level=1.0, seed=1):
    """A voice under breath, at a level."""
    return level * (harmonic(seconds) + 2 * noise(seconds, seed=seed))


def test_a_segment_takes_the_soundtracks_threshold_and_grid():
    # 01 is loud; 02 opens 20 dB below it, under the soundtrack's threshold, then rises to 6 dB
    # below. Neither segment starts on the frame grid.
    samples = np.concatenate(
        [
            np.zeros(1700),
            breathy(1.0),
            np.zeros(5000),
            breathy(0.5, 0.1, seed=2),
            breathy(0.8, 0.5, seed=3),
            np.zeros(4000),
        ]
    )
    first_end, quiet, last_end = 1700 + RATE, 22700, 22700 + round(1.3 * RATE)
    cut = 1.3
    timeline = {
        "segments": [
            segment("01", 0.0, cut, [("One.", 1700 / RATE, first_end / RATE)]),
            segment("02", cut, 3.0, [("Two.", quiet / RATE, last_end / RATE)]),
        ]
    }
    report = review_clarity.report(samples, timeline, 18.0)
    kept, _ = stated_frames(samples)
    for row, (start, end) in zip(report["segments"], [(0.0, cut), (cut, 3.0)], strict=True):
        values = stated_span(kept, start, end)
        assert row["frames"] == len(values)
        assert row["cpp_db"] == round(float(np.median(values)), 2)
    # Every kept frame belongs to one segment, and the soundtrack's figure is the whole grid's.
    assert sum(row["frames"] for row in report["segments"]) == len(kept)
    assert report["soundtrack"]["frames"] == len(kept)
    # Cut out and measured alone, 02 would keep its quiet opening by its own threshold.
    alone = review_clarity.prominence(samples[quiet:last_end])
    assert report["segments"][1]["frames"] < alone.frames - 20
    # A segment without a kept frame has no value and no verdict.
    silent = {"segments": [segment("01", 0.0, 0.05, [("One.", 0.0, 0.05)])]}
    assert review_clarity.report(samples, silent, 18.0)["segments"] == [
        {"id": "01", "cpp_db": None, "frames": 0, "below_floor": None}
    ]


def test_a_thought_is_judged_by_its_median_over_the_grids_phases():
    # A thought of two seconds and one of three, in one segment.
    samples = np.concatenate(
        [np.zeros(3000), breathy(2.0), np.zeros(9000), breathy(3.0, seed=4), np.zeros(5000)]
    )
    spans = [(3000 / RATE, 35000 / RATE), (44000 / RATE, 92000 / RATE)]
    words = [("One.", *spans[0]), ("Two.", *spans[1])]
    timeline = {"segments": [segment("01", 0.0, 6.0, words, ["One. ", "Two. "])]}
    report = review_clarity.report(samples, timeline, None)
    assert review_clarity.PHASES == tuple(range(0, 256, 16))
    _, threshold = stated_frames(samples)
    grids = [stated_frames(samples, phase, threshold)[0] for phase in review_clarity.PHASES]
    for row, name, (start, end) in zip(report["thoughts"], ["01.1", "01.2"], spans, strict=True):
        phases = [float(np.median(stated_span(kept, start, end))) for kept in grids]
        assert row == {
            "id": name,
            "cpp_db": round(float(np.median(phases)), 2),
            "frames": len(stated_span(grids[0], start, end)),
            "below_floor": None,
            "grid_db": round(phases[0], 2),
            "lowest_db": round(min(phases), 2),
            "highest_db": round(max(phases), 2),
            "short": name == "01.1",
        }
        assert row["lowest_db"] < row["highest_db"]
    # Fewer than 150 kept frames, about 2.4 s of voice, make a thought short.
    assert [row["frames"] for row in report["thoughts"]] == [125, 188]
    assert review_clarity.SHORT_FRAMES == 150


def test_a_thought_stands_below_its_floor_by_its_phase_median():
    grid, *others = (review_clarity.Clarity(value, 94) for value in (17.88, 18.2, 18.4, 18.72))
    assert review_clarity.phased([grid, *others], 18.0) == {
        "cpp_db": 18.3,
        "frames": 94,
        "below_floor": False,
        "grid_db": 17.88,
        "lowest_db": 17.88,
        "highest_db": 18.72,
        "short": True,
    }
    assert review_clarity.phased([grid, *others], 18.5)["below_floor"] is True
    # A thought without a kept frame on any grid has no value and no verdict.
    assert review_clarity.phased([review_clarity.Clarity(None, 0)] * 2, 18.0) == {
        "cpp_db": None,
        "frames": 0,
        "below_floor": None,
        "grid_db": None,
        "lowest_db": None,
        "highest_db": None,
        "short": True,
    }


def write_soundtrack(path, mono, rate=48000):
    """A 16-bit stereo soundtrack of mono samples."""
    pcm = np.round(np.stack([mono, mono], axis=1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(pcm.tobytes())
    return path


@pytest.mark.ffmpeg
def test_each_soundtrack_and_segment_is_recorded_against_its_floor(tmp_path):
    rate = 48000
    clear, breathy = harmonic(1.0, rate=rate), harmonic(1.0, rate=rate) + 3 * noise(1.0, rate)
    mono = np.concatenate([clear, np.zeros(rate // 2), breathy, np.zeros(rate // 2)])
    soundtrack = write_soundtrack(tmp_path / "narration.wav", mono)
    timeline = {
        "segments": [
            segment("01", 0.0, 1.25, [("One", 0.0, 0.5), ("two.", 0.5, 1.0)]),
            segment("02", 1.25, 3.0, [("Three.", 1.5, 2.5)]),
        ]
    }
    # The sample film declares 18 dB for its Chinese edition.
    report = review_clarity.voice_clarity("zh", soundtrack, timeline)
    assert report["method"] == review_clarity.METHOD
    assert report["floor_db"] == 18.0
    first, second = report["segments"]
    assert first["id"] == "01" and first["cpp_db"] > 25 and first["below_floor"] is False
    assert second["id"] == "02" and second["cpp_db"] < 18 and second["below_floor"] is True
    assert report["segments_below_floor"] == ["02"]
    assert set(report["soundtrack"]) == {"cpp_db", "frames", "below_floor"}
    # Each value is recorded to 0.01 dB, and judged as recorded.
    assert report["soundtrack"]["cpp_db"] == round(report["soundtrack"]["cpp_db"], 2)
    whole = review_clarity.prominence(review_clarity.decode(soundtrack))
    assert report["soundtrack"]["cpp_db"] == round(whole.median_db, 2)
    assert report["soundtrack"]["frames"] == whole.frames
    # Each thought is recorded by its median over the grid's phases; one second is short.
    assert [row["id"] for row in report["thoughts"]] == ["01.1", "02.1"]
    assert [row["below_floor"] for row in report["thoughts"]] == [False, True]
    assert report["thoughts_below_floor"] == ["02.1"]
    assert report["short_thoughts"] == ["01.1", "02.1"]
    # The command's summary prints the soundtrack's clarity beside its floor.
    assert review_clarity.summary(report) == {
        **report["soundtrack"],
        "floor_db": 18.0,
        "segments_below_floor": ["02"],
        "thoughts_below_floor": ["02.1"],
    }


def test_a_film_without_floors_records_none():
    clarity = review_clarity.Clarity(17.004, 120)
    assert review_clarity.judged(clarity, None) == {
        "cpp_db": 17.0,
        "frames": 120,
        "below_floor": None,
    }
    assert review_clarity.judged(clarity, 17.0)["below_floor"] is False
    assert review_clarity.judged(review_clarity.Clarity(None, 0), 17.0)["below_floor"] is None
