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


def stated_method(samples):
    """The reviewers' steps 2 to 7, frame by frame, with NumPy's own least squares."""
    starts = range(0, len(samples) - 1023, 256)
    frames = [samples[start : start + 1024] for start in starts]
    energy = np.array([10 * np.log10(np.sum(frame**2) + 1e-20) for frame in frames])
    window = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(1024) / 1024)
    bins = np.arange(40, 267)
    values = []
    for frame, level in zip(frames, energy, strict=True):
        if level < np.percentile(energy, 95) - 18:
            continue
        spectrum = 10 * np.log10(np.abs(np.fft.rfft(frame * window)) ** 2 + 1e-20)
        cepstrum = np.fft.irfft(spectrum, n=1024)
        peaks = 20 * np.log10(np.abs(cepstrum[40:267]) + 1e-20)
        design = np.vstack([bins, np.ones(len(bins))]).T
        (slope, intercept), *_ = np.linalg.lstsq(design, peaks, rcond=None)
        top = int(np.argmax(peaks))
        values.append(peaks[top] - (slope * bins[top] + intercept))
    return float(np.median(values)), len(values)


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
            {"id": "01", "words": [{"start": 0.0, "end": 0.5}, {"start": 0.5, "end": 1.0}]},
            {"id": "02", "words": [{"start": 1.5, "end": 2.5}]},
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
    # The command's summary prints the soundtrack's clarity beside its floor.
    assert review_clarity.summary(report) == {
        **report["soundtrack"],
        "floor_db": 18.0,
        "segments_below_floor": ["02"],
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
