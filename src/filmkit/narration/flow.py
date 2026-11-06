"""How the narration flows: the pause heard at every word boundary, and the steps between thoughts.

The heard pause between two adjacent aligned words of a take or a soundtrack is the longest run
of 10 ms frames, between the middles of the two words, whose RMS level lies at least 24 dB below
the speech median, the median level of the frames above -45 dBFS. The aligner may give the quiet
between two words to either of them, and the middles bound it whichever word holds it. Words
meet their text by their spoken units, as `spoken_units.item_joins` matches them, so a hyphen or
an apostrophe inside a written word stays inside its aligned word ("Crossrole" for "Cross-role"),
and the text written between two words is the boundary's marks. Each boundary also records
whether its words switch between Chinese characters and Latin letters or digits.

A boundary whose marks hold no pause mark joins its words inside a phrase; a quotation mark is not
a pause of its own. Its heard pause may not exceed its limit: by default 0.2 s where the script
switches, where Chinese speech synthesis hesitates, and 0.4 s elsewhere, which spares the clause
boundaries a text leaves unmarked. A film declares other limits, and each boundary it keeps above
them with its reason, in `[narration.flow]`; selection and assembly refuse every other boundary
above its limit and each exception that no boundary of its edition matches. The unmarked pauses
from 0.15 s up to their limits are listed for human listening.

Between adjacent thoughts of one segment, the steps of speaking rate, median pitch and level are
recorded for listening and never refuse: a question raises the pitch on purpose, and a short
thought gives a noisy rate. A thought spans its aligned words, read at 16 kHz in 40 ms windows
every 10 ms, and a window of at least -40 dBFS is voiced. Its rate counts Chinese characters, with
each Latin word's syllables by its vowel groups, or English syllables, per voiced second; its
pitch is the median F0 of its voiced windows by autocorrelation over 70-400 Hz at a clarity of at
least 0.45; and its level is the mean RMS of its voiced windows, in dB.
"""

from __future__ import annotations

import dataclasses
import functools
import math
import re
import wave
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING

import numpy as np

from filmkit.narration.spoken_units import (
    PHRASE_END_MARKS,
    AlignmentError,
    item_joins,
    thought_spans,
)
from filmkit.soundtrack.quiet import FRAME_SECONDS, longest_run

if TYPE_CHECKING:
    from pathlib import Path

    from filmkit.film import Flow, FlowException

FLOW_METHOD = (
    "heard pause: the longest run of 10 ms RMS frames at least 24 dB below the speech median "
    "(the median of frames above -45 dBFS) between the middles of two adjacent aligned words; "
    "a boundary without a pause mark is held to its limit, quotation marks are not pauses"
)
CONTINUITY_METHOD = (
    "each thought from its first aligned word to its last at 16 kHz, 40 ms windows every 10 ms, "
    "voiced at -40 dBFS or more; rate in Chinese characters plus Latin syllables by vowel "
    "groups, or English syllables, per voiced second; median F0 by autocorrelation over "
    "70-400 Hz at a clarity of at least 0.45; level as the mean RMS of the voiced windows"
)
# The frames above this level are speech, and their median is the speech median.
SPEECH_DBFS = -45.0
# A frame at least this far below the speech median is heard as quiet.
QUIET_BELOW_SPEECH_DB = 24.0
# Marks a reader pauses at. Quotation marks are not pauses of their own, and a hyphen or a slash
# joins its words.
PAUSE_MARKS = PHRASE_END_MARKS | frozenset("…—–()（）[]【】")
# Unmarked pauses from this long up to their limits are listed for human listening.
LISTENING_SECONDS = 0.15
# The largest steps of each continuity measure that the listening plan lists.
LISTED_STEPS = 5
LATIN = re.compile(r"[A-Za-z0-9]")
HAN_CHARACTER = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD = re.compile(r"[A-Za-z]+")
VOWEL_GROUP = re.compile(r"[aeiouy]+")
# The continuity windows: their rate, length and voicing floor, the F0 range and the clarity
# floor, and the low-pass filter that decimates to their rate.
PITCH_RATE = 16000
PITCH_WINDOW_SECONDS = 0.04
VOICED_DBFS = -40.0
F0_RANGE_HZ = (70, 400)
CLARITY = 0.45
PITCH_TAPS = 61


@dataclass(frozen=True, eq=False)
class Recording:
    """A recording's mono samples in [-1, 1) and their rate, and the 10 ms frames heard quiet."""

    mono: np.ndarray
    rate: int

    @classmethod
    def of(cls, pcm: np.ndarray, rate: int) -> Recording:
        """A recording of 16-bit samples, by sample or by sample and channel, channels averaged."""
        mono = pcm.mean(axis=1, dtype=np.float32) if pcm.ndim > 1 else pcm.astype(np.float32)
        mono /= 32768
        return cls(mono, rate)

    @classmethod
    def read(cls, path: Path) -> Recording:
        """The recording of a 16-bit WAV file."""
        with wave.open(str(path)) as audio:
            pcm = np.frombuffer(audio.readframes(audio.getnframes()), dtype="<i2")
            return cls.of(pcm.reshape(-1, audio.getnchannels()), audio.getframerate())

    @property
    def hop(self) -> int:
        """The samples of one 10 ms frame."""
        return round(FRAME_SECONDS * self.rate)

    def frame(self, seconds: float) -> int:
        """The 10 ms frame that holds a time."""
        return round(seconds * self.rate) // self.hop

    @functools.cached_property
    def quiet(self) -> np.ndarray:
        """Whether each 10 ms frame lies at least 24 dB below the speech median."""
        count = len(self.mono) // self.hop
        frames = self.mono[: count * self.hop].reshape(count, self.hop)
        power = np.empty(count)
        for begin in range(0, count, 8192):
            chunk = frames[begin : begin + 8192].astype(np.float64)
            power[begin : begin + len(chunk)] = np.mean(chunk * chunk, axis=1)
        levels = 10 * np.log10(power + 1e-12)
        speech = levels[levels > SPEECH_DBFS]
        median = float(np.median(speech)) if len(speech) else SPEECH_DBFS
        return levels <= median - QUIET_BELOW_SPEECH_DB

    def lowpassed(self, taps: int, step: int, begin: int, end: int) -> np.ndarray:
        """Every `step`-th sample from `begin` up to `end`, low-passed below the decimated band.

        The windowed-sinc filter of `taps` taps cuts at 0.45 of the decimated rate. Only the
        samples around the span are filtered, which gives the same values as filtering the
        whole recording.
        """
        offsets = np.arange(taps) - (taps - 1) / 2
        kernel = np.sinc(2 * (0.45 / step) * offsets) * np.hamming(taps)
        lead = taps // 2
        first, last = max(0, begin - lead), min(len(self.mono), end + lead)
        part = np.convolve(self.mono[first:last].astype(np.float64), kernel / kernel.sum(), "same")
        return part[begin - first : end - first : step]


@dataclass(frozen=True)
class Narrated:
    """One segment's text, its thoughts and aligned words, and the recording that speaks them.

    Each word holds its `text` and its `start` and `end` in seconds of the recording. The
    thoughts are numbered from `first_thought`, so a take of one thought keeps its number.
    """

    segment: str
    text: str
    groups: list[str]
    words: list[dict]
    recording: Recording
    first_thought: int = 1

    def label(self, thought: int) -> str:
        """The name of a thought by its index in the groups: segment and number."""
        return f"{self.segment}.{self.first_thought + thought}"


def timed(items: list[dict]) -> list[dict]:
    """Aligned items as words with their text, start and end."""
    return [
        {"text": item["text"], "start": item["start_time"], "end": item["end_time"]}
        for item in items
    ]


def segments_of(recording: Recording, segments: list[dict]) -> list[Narrated]:
    """The timeline segments of one recording, such as a soundtrack."""
    return [
        Narrated(
            segment["id"],
            segment["text"],
            segment.get("utterance_groups") or [segment["text"]],
            segment["words"],
            recording,
        )
        for segment in segments
    ]


def soundtrack(path: Path, timeline: dict) -> list[Narrated]:
    """Every segment of an assembled timeline, spoken by its soundtrack."""
    return segments_of(Recording.read(path), timeline["segments"])


@dataclass(frozen=True)
class Boundary:
    """The pause heard between two adjacent aligned words, the marks between them, and their script.

    `thought` names the thought that holds the left word, `at` is where that word ends in its
    recording, and `switch` tells whether one word is Latin and the other is not.
    """

    thought: str
    left: str
    right: str
    at: float
    pause_s: float
    marks: str
    switch: bool


def _latin(word: str) -> bool:
    return bool(LATIN.search(word))


def boundaries(narrated: Narrated) -> list[Boundary]:
    """The heard pause at every boundary between adjacent aligned words of a segment."""
    words, recording = narrated.words, narrated.recording
    try:
        joins = item_joins(narrated.text, words, narrated.groups)
    except AlignmentError as error:
        msg = f"{narrated.segment}: {error}"
        raise AlignmentError(msg) from error
    found = []
    for join in joins:
        left, right = words[join.left], words[join.right]
        begin = recording.frame((left["start"] + left["end"]) / 2)
        end = recording.frame((right["start"] + right["end"]) / 2)
        run = longest_run(recording.quiet[begin:end])
        frames = run[1] - run[0] if run else 0
        found.append(
            Boundary(
                thought=narrated.label(join.thought),
                left=left["text"],
                right=right["text"],
                at=round(left["end"], 2),
                pause_s=round(frames * FRAME_SECONDS, 2),
                marks=join.marks,
                switch=_latin(left["text"]) != _latin(right["text"]),
            )
        )
    return found


def limit(boundary: Boundary, policy: Flow) -> float | None:
    """The longest pause a boundary may hold, or None where its text marks a pause."""
    if PAUSE_MARKS & set(boundary.marks):
        return None
    return policy.switch_limit_s if boundary.switch else policy.unmarked_limit_s


def _matches(exception: FlowException, boundary: Boundary) -> bool:
    return (exception.thought, exception.left.casefold(), exception.right.casefold()) == (
        boundary.thought,
        boundary.left.casefold(),
        boundary.right.casefold(),
    )


@dataclass(frozen=True)
class Judged:
    """A narration's unmarked boundaries above their limits, kept by an exception, or to hear.

    `stale` holds the edition's exceptions that no boundary matches, judged only on a whole
    narration.
    """

    refused: list[dict]
    declared: list[dict]
    listen: list[dict]
    stale: list[FlowException]


def judge(code: str, found: list[Boundary], policy: Flow, *, whole: bool = True) -> Judged:
    """Judge each unmarked boundary of an edition's narration against its limit.

    A boundary above its limit is refused unless an exception the film declares for the
    edition names its thought and words. `whole` tells whether the boundaries are the whole
    narration's, where an exception that matches none is stale.
    """
    exceptions = [exception for exception in policy.exceptions if exception.edition == code]
    matched, refused, declared, listen = set(), [], [], []
    for boundary in found:
        kept = next((e for e in exceptions if _matches(e, boundary)), None)
        if kept is not None:
            matched.add(kept)
        bound = limit(boundary, policy)
        if bound is None:
            continue
        row = {**dataclasses.asdict(boundary), "limit_s": bound}
        if boundary.pause_s > bound and kept is None:
            refused.append(row)
        elif boundary.pause_s > bound:
            declared.append({**row, "reason": kept.reason})
        elif boundary.pause_s >= LISTENING_SECONDS:
            listen.append(row)
    stale = [exception for exception in exceptions if exception not in matched] if whole else []
    return Judged(refused, declared, listen, stale)


def refusals(code: str, judged: Judged) -> list[str]:
    """What the gates refuse: each pause above its limit and each stale exception, by name."""
    pauses = [
        f"{code} {row['thought']}: a {row['pause_s']:.2f} s pause between {row['left']} and "
        f"{row['right']}, where the text "
        + (f"holds only {row['marks']}" if row["marks"] else "has no mark")
        + (" and the script switches" if row["switch"] else "")
        + f", exceeds its {row['limit_s']:.2f} s limit"
        for row in judged.refused
    ]
    stale = [
        f"{code}: the [narration.flow] exception {exception.thought} between {exception.left} "
        f"and {exception.right} matches no boundary of the narration"
        for exception in judged.stale
    ]
    return pauses + stale


def take_flow(
    code: str, thought: str, text: str, words: list[dict], recording: Recording, policy: Flow
) -> dict:
    """How a take of one thought flows: its longest unmarked pause, and whether it is fluent.

    A fluent take holds no unmarked pause above its limit that an exception does not keep; a
    take whose alignment misses its text is not known to be fluent.
    """
    segment, number = thought.rsplit(".", 1)
    try:
        found = boundaries(Narrated(segment, text, [text], words, recording, int(number)))
    except AlignmentError:
        return {"longest_unmarked_pause": None, "fluent": False}
    unmarked = [boundary for boundary in found if limit(boundary, policy) is not None]
    longest = max(unmarked, key=lambda boundary: boundary.pause_s, default=None)
    return {
        "longest_unmarked_pause": None
        if longest is None
        else {**dataclasses.asdict(longest), "limit_s": limit(longest, policy)},
        "fluent": not judge(code, found, policy, whole=False).refused,
    }


def gate(code: str, narrated: list[Narrated], policy: Flow) -> list[str]:
    """The refusals of a whole narration's boundaries under the film's limits."""
    found = [boundary for item in narrated for boundary in boundaries(item)]
    return refusals(code, judge(code, found, policy))


def _spread(values: list[float]) -> dict:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "median": round(float(np.median(values)), 2),
        "p99": round(float(np.percentile(values, 99)), 2),
        "max": round(max(values), 2),
    }


def flow_record(code: str, narrated: list[Narrated], policy: Flow) -> dict:
    """The heard pauses of a narration by the marks between their words, and its judgement.

    Marked pauses are summarized by their marks and unmarked ones by whether the script
    switches; the boundaries above their limits, those an exception keeps and those to hear
    are listed in full.
    """
    found = [boundary for item in narrated for boundary in boundaries(item)]
    judged = judge(code, found, policy)
    marked: dict[str, list[float]] = {}
    unmarked: dict[str, list[float]] = {"switch": [], "other": []}
    for boundary in found:
        if limit(boundary, policy) is None:
            marked.setdefault(boundary.marks, []).append(boundary.pause_s)
        else:
            unmarked["switch" if boundary.switch else "other"].append(boundary.pause_s)
    return {
        "method": FLOW_METHOD,
        "limits_seconds": {"switch": policy.switch_limit_s, "other": policy.unmarked_limit_s},
        "boundaries": len(found),
        "unmarked_pause_seconds": {kind: _spread(values) for kind, values in unmarked.items()},
        "marked_pause_seconds": {marks: _spread(marked[marks]) for marks in sorted(marked)},
        "above_limit": judged.refused,
        "declared": judged.declared,
        "stale_exceptions": [exception.model_dump() for exception in judged.stale],
        "listen": judged.listen,
    }


def syllables(text: str, code: str) -> int:
    """A text's spoken syllables: Chinese characters, and each Latin word's vowel groups."""
    latin = sum(max(1, len(VOWEL_GROUP.findall(word.lower()))) for word in LATIN_WORD.findall(text))
    return latin + (len(HAN_CHARACTER.findall(text)) if code == "zh" else 0)


def _windows(recording: Recording, start: float, end: float) -> tuple[np.ndarray, np.ndarray]:
    """The RMS and the F0 (NaN where unvoiced or unclear) of a span's 40 ms pitch windows."""
    step = max(1, recording.rate // PITCH_RATE)
    rate = recording.rate / step
    size, hop = round(PITCH_WINDOW_SECONDS * rate), round(FRAME_SECONDS * rate)
    first, last = int(start * rate), int(end * rate) - size
    count = len(range(first, last, hop))
    if count <= 0:
        return np.empty(0), np.empty(0)
    samples = recording.lowpassed(PITCH_TAPS, step, first * step, (last + size) * step)
    frames = np.lib.stride_tricks.sliding_window_view(samples, size)[::hop][:count]
    rms = np.sqrt(np.mean(frames**2, axis=1))
    centred = frames - frames.mean(axis=1, keepdims=True)
    spectrum = np.fft.rfft(centred * np.hanning(size), n=2 * size, axis=1)
    auto = np.fft.irfft(np.abs(spectrum) ** 2, axis=1)[:, :size]
    auto /= auto[:, :1] + 1e-12
    low, high = int(rate / F0_RANGE_HZ[1]), int(rate / F0_RANGE_HZ[0])
    lag = low + np.argmax(auto[:, low:high], axis=1)
    clear = auto[np.arange(count), lag] >= CLARITY
    voiced = rms >= 10 ** (VOICED_DBFS / 20)
    return rms, np.where(voiced & clear, rate / lag, np.nan)


@dataclass(frozen=True)
class Thought:
    """One thought's span, speaking rate, median F0 and level; None where nothing is voiced."""

    segment: str
    name: str
    start: float
    rate: float
    f0_hz: float | None
    level_db: float | None


def thoughts(code: str, narrated: list[Narrated]) -> list[Thought]:
    """Each thought's rate, pitch and level over its aligned span, in narration order."""
    measured = []
    for item in narrated:
        spans = thought_spans(item.text, item.words, item.groups)
        for index, (span, text) in enumerate(zip(spans, item.groups, strict=True)):
            start, end = item.words[span.first]["start"], item.words[span.last]["end"]
            rms, f0 = _windows(item.recording, start, end)
            voiced = rms[rms >= 10 ** (VOICED_DBFS / 20)]
            pitched = f0[~np.isnan(f0)]
            measured.append(
                Thought(
                    item.segment,
                    item.label(index),
                    start,
                    syllables(text, code) / max(len(voiced) * FRAME_SECONDS, 0.1),
                    float(np.median(pitched)) if len(pitched) else None,
                    float(20 * np.log10(np.mean(voiced))) if len(voiced) else None,
                )
            )
    return measured


def _step(value: float | None, digits: int) -> float | None:
    """A step rounded as it is recorded, never as negative zero."""
    return None if value is None else round(value, digits) + 0.0


def steps(measured: list[Thought]) -> list[dict]:
    """The rate ratio and the pitch and level steps between adjacent thoughts of each segment."""
    found = []
    for before, after in pairwise(measured):
        if before.segment != after.segment:
            continue
        pitched = before.f0_hz is not None and after.f0_hz is not None
        levelled = before.level_db is not None and after.level_db is not None
        found.append(
            {
                "thoughts": f"{before.name}>{after.name}",
                "at": round(after.start, 2),
                "rate_ratio": _step(after.rate / before.rate if before.rate else None, 2),
                "pitch_semitones": _step(
                    12 * math.log2(after.f0_hz / before.f0_hz) if pitched else None, 1
                ),
                "level_db": _step(after.level_db - before.level_db if levelled else None, 1),
            }
        )
    return found


def _size(measure: str, step: dict) -> float:
    """How large a step is: a rate ratio by its logarithm, a pitch or level step by its size."""
    value = step[measure]
    return abs(math.log(value)) if measure == "rate_ratio" else abs(value)


def largest(found: list[dict]) -> dict[str, list[dict]]:
    """The largest steps of each measure, largest first."""
    measures = ("rate_ratio", "pitch_semitones", "level_db")
    return {
        measure: sorted(
            (step for step in found if step[measure]),
            key=functools.partial(_size, measure),
            reverse=True,
        )[:LISTED_STEPS]
        for measure in measures
    }


def continuity_record(code: str, narrated: list[Narrated]) -> dict:
    """Every step between adjacent thoughts of a part, and the largest of each measure."""
    measured = thoughts(code, narrated)
    found = steps(measured)
    return {
        "method": CONTINUITY_METHOD,
        "thoughts": len(measured),
        "steps": found,
        "largest": largest(found),
    }


def listening(code: str, narrated: list[Narrated], policy: Flow) -> dict:
    """The moments of a narration that a person should hear, for the listening plan.

    They are the pauses that exceptions keep above their limits, the unmarked pauses from
    0.15 s up to their limits, longest first, and the largest steps between thoughts.
    """
    found = [boundary for item in narrated for boundary in boundaries(item)]
    judged = judge(code, found, policy)
    return {
        "pauses": sorted(judged.declared + judged.listen, key=lambda row: -row["pause_s"]),
        "steps": largest(steps(thoughts(code, narrated))),
    }
