"""Measure sound-picture sync: when each label is legible against when it is spoken.

Reads a label trace written by frame-audit.mjs (TRACE=<file>) and the timeline it ran
on. A label is legible in a frame where its contrast reaches 3:1, and each run of its legible
frames that begins after at least 1 s illegible in its scene is an appearance. Labels and their
" · " parts are judged at each appearance against the spoken occurrence of their letters that
starts nearest its first legible frame, within 8 s, and that no earlier appearance took; an
English label with no such occurrence is matched by the Snowball stems of its words in its
thought, and the match is recorded as inflected (`filmkit.picture.label_matches`). A label is
out of sync when it is legible more than 0.3 s before the clause that speaks it begins, more
than 1.5 s ahead of its words within that clause, or more than 0.5 s after its words end. Labels
with no spoken match are listed and counted, not judged, as is a first appearance whose words
are said only farther away; a later appearance without its words is listed as a recall. The
report also lists speech that runs over 1.0 s without a legible name, thoughts that keep the
previous picture over 1.0 s, and caption cues that labels repeat: a cue drawn whole as one
label, or mostly as labels drawn during it.
Given the mark trace that frame-audit.mjs writes (MARKS=<file>), it also lists seats: a
mark that stands in speech for more than 0.6 s before a name is legible at it. A segment
whose aligned words do not spell its text raises `PictureError`.

Usage: python -m filmkit.picture.sync_audit <timeline.json> <trace.tsv> [--out report.json]
    [--tolerance 0.3] [--step 0.0333333] [--bind source-timeline.json] [--marks marks.tsv]
--step is the trace's sampling step, as given to frame-audit.mjs. --bind records the
SHA-256 of the production timeline the audited timeline derives from, and of the
composition script whose frames the trace samples.
"""

from __future__ import annotations

import argparse
import bisect
import json
from pathlib import Path
from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.picture.label_matches import (
    english,
    exact_matches,
    inflected_matches,
    spoken_index,
    thought_words,
    units,
    words,
)
from filmkit.picture.rendering import COMPOSITION_SCRIPT, PictureError

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from filmkit.picture.label_matches import Occurrence

# A label is legible from the first frame its contrast reaches this ratio.
LEGIBLE_CONTRAST = 3
# A label legible again after more than this many seconds without a legible frame in its scene
# appears again.
APPEARANCE_GAP = 1.0
# Seconds a label may lead its words within their clause, and trail their end.
AHEAD_IN_CLAUSE = 1.5
AFTER_WORDS = 0.5
# A spoken match farther than this many seconds from its label names something else.
FAR_FROM_WORDS = 8
# Seconds into a thought within which the previous picture gives way.
HOLD_WINDOW = 4
# A caption cue of at least this many words is listed when one label legible during it holds
# exactly its words, or labels drawn during it repeat at least this share of them.
ECHO_WORDS = 3
ECHO_SHARE = 0.8
# The quotation marks that open and close a cue that is itself one quotation.
QUOTATION_MARKS = {"“": "”", "‘": "’", "「": "」", '"': '"'}
# The verdicts of a label out of sync, and the report's counts that reviews read.
VERDICTS = ("before-clause", "ahead-in-clause", "after-words")
SUMMARY_KEYS = ("tolerance", "labels_judged", "labels_unmatched", "out_of_sync", *VERDICTS)


def trace_rows(lines: Iterable[str], width: int) -> Iterator[tuple[float, str, list[str]]]:
    """Each trace line's time, scene and remaining tab-separated fields.

    A label row continues with its contrast, a field this audit does not read and its text;
    a mark row with its box and whether a name stands at it. A line with fewer than `width`
    fields, such as a partial last line, is skipped.
    """
    for line in lines:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= width:
            yield float(parts[0]), parts[1], parts[2:]


def legible_labels(trace_lines: Iterable[str]) -> dict[tuple[str, str], list[float]]:
    """The first legible time of each appearance of each label of each scene, whole and by its
    " · " parts: of each run of its legible frames that begins after at least 1 s illegible."""
    seen: dict[tuple[str, str], set[float]] = {}
    for t, scene, fields in trace_rows(trace_lines, 5):
        contrast, text = float(fields[0]), fields[2]
        if contrast < LEGIBLE_CONTRAST:
            continue
        # A label is judged whole and by its " · " parts; spacing is not part of a name.
        pieces = {text.strip()} | {p.strip() for p in text.split("·") if p.strip()}
        for piece in pieces:
            seen.setdefault((scene, piece), set()).add(t)
    appearances = {}
    for key, times in seen.items():
        ordered = sorted(times)
        appearances[key] = [
            t for k, t in enumerate(ordered) if not k or t - ordered[k - 1] > APPEARANCE_GAP + 1e-9
        ]
    return appearances


def nearest(found: list[Occurrence], shown: float, taken: set[Occurrence]) -> Occurrence | None:
    """The occurrence that starts nearest `shown`, within 8 s, of those no appearance took."""
    free = [o for o in found if o not in taken and abs(shown - o[0]) <= FAR_FROM_WORDS]
    return min(free, key=lambda occurrence: abs(shown - occurrence[0]), default=None)


def verdict(shown: float, start: float, end: float, clause: float, tolerance: float) -> str:
    """Whether a label legible at `shown` anticipates its clause, or leads or trails its words.

    Before its clause begins, a label anticipates the voice; after its words end, it trails
    them.
    """
    if shown < clause - tolerance:
        return "before-clause"
    if shown - start < -AHEAD_IN_CLAUSE:
        return "ahead-in-clause"
    if shown > end + AFTER_WORDS:
        return "after-words"
    return "in-sync"


def summarize(
    judged: list[dict],
    far: list[dict],
    unmatched: list[dict],
    recalls: list[dict],
    tolerance: float,
) -> dict:
    """An audit's report: its counts, the labels out of sync, unspoken and far from words, and
    the recalls.

    A label counts as unmatched when it is listed as unspoken or as far from its words; a
    recall is neither judged nor unmatched.
    """
    out = [row for row in judged if row["verdict"] != "in-sync"]
    return {
        "tolerance": tolerance,
        "labels_judged": len(judged),
        "labels_unmatched": len(unmatched) + len(far),
        "out_of_sync": len(out),
        **{name: sum(row["verdict"] == name for row in out) for name in VERDICTS},
        "findings": out,
        "unmatched": unmatched,
        "far_from_words": far,
        "recalls": recalls,
        "by_scene": {
            scene: sum(1 for row in out if row["scene"] == scene)
            for scene in sorted({row["scene"] for row in out})
        },
    }


def audit(
    timeline: dict, trace_lines: Iterable[str], tolerance: float = 0.3
) -> tuple[dict, list[dict]]:
    """Judge each appearance of each legible label against its spoken words; return a report.

    An appearance takes the nearest exact occurrence of its label's words within 8 s that no
    earlier appearance took, and an English label without one its nearest inflected occurrence
    in its thought, as `filmkit.picture.label_matches` finds them. A label its scene never says
    is unspoken, a first appearance whose words are said only farther away is far from them,
    and a later appearance without its words is a recall.
    """
    segments = {segment["id"]: segment for segment in timeline["segments"]}
    index = {key: spoken_index(segment) for key, segment in segments.items()}
    judged, far, unmatched, recalls = [], [], [], []
    for (scene, label), appearances in legible_labels(trace_lines).items():
        needle = units(label)
        # A label grown part by part is judged by its parts, each at its own first
        # legible frame.
        if scene not in index or len(needle) < 2 or "·" in label:
            continue
        exact, taken = exact_matches(index[scene], needle), set()
        for number, shown in enumerate(appearances):
            row = {"scene": scene, "label": label, "legible": round(shown, 3)}
            kind, found = "exact", exact
            match = nearest(found, shown, taken)
            if match is None and english(label):
                kind = "inflected"
                found = inflected_matches(segments[scene], index[scene], label, shown)
                match = nearest(found, shown, taken)
            if match is None:
                # A spoken match more than 8 s away names something else: a recap, a heading
                # or another reference. It is listed, because a cue taken from an earlier
                # occurrence of its words shows the same way.
                if number:
                    recalls.append(row)
                elif exact:
                    far.append({**row, "spoken": [round(o[0], 3) for o in exact]})
                else:
                    unmatched.append(row)
                continue
            taken.add(match)
            start, end, clause = match
            judged.append(
                {
                    **row,
                    "spoken": round(start, 3),
                    "spoken_end": round(end, 3),
                    "clause_start": round(clause, 3),
                    "delta": round(shown - start, 3),
                    "occurrences": len(found),
                    "verdict": verdict(shown, start, end, clause, tolerance),
                    "match": kind,
                }
            )
    lists = [
        sorted(rows, key=lambda row: (row["scene"], row["legible"], row["label"]))
        for rows in (judged, far, unmatched, recalls)
    ]
    return summarize(*lists, tolerance), lists[0]


def thought_spans(segment: dict) -> list[tuple[str, float, float]]:
    """Each thought of a segment as "<id>.<n>", the start of its first word and the end of its last.

    A segment without utterance groups is one thought.
    """
    spoken = segment["words"]
    return [
        (f"{segment['id']}.{index}", spoken[first]["start"], spoken[last]["end"])
        for index, (first, last) in enumerate(thought_words(segment), 1)
    ]


def legible_frames(trace_lines: Iterable[str]) -> dict[float, dict[str, set[str]]]:
    """The names legible at each sampled time by scene: labels of 3:1 contrast with a letter."""
    frames = {}
    for t, scene, fields in trace_rows(trace_lines, 5):
        contrast, text = float(fields[0]), fields[2]
        if contrast < LEGIBLE_CONTRAST or not any(ch.isalpha() for ch in text):
            continue
        frames.setdefault(round(t, 3), {}).setdefault(scene, set()).add(text)
    return frames


def nearest_frame(
    frames: dict[float, dict[str, set[str]]], times: list[float], t: float, step: float
) -> dict[str, set[str]]:
    """The names legible at the sample nearest `t`; none without a sample within half a step."""
    i = bisect.bisect_left(times, t)
    near = min(
        (times[j] for j in (i - 1, i) if 0 <= j < len(times)),
        default=None,
        key=lambda v: abs(v - t),
    )
    return frames[near] if near is not None and abs(near - t) <= step / 2 + 1e-9 else {}


def unnamed_runs(
    frames: dict[float, dict[str, set[str]]],
    times: list[float],
    scene: str,
    span: tuple[float, float],
    step: float,
    limit: float,
) -> list[tuple[float, float]]:
    """The runs of a thought's samples longer than `limit` at which its scene shows no name."""
    a, b = span
    runs, run = [], None
    for t in (round(a + k * step, 3) for k in range(int((b - a) / step) + 1)):
        if nearest_frame(frames, times, t, step).get(scene):
            if run and run[1] - run[0] > limit:
                runs.append(run)
            run = None
        else:
            run = (run[0] if run else t, t)
    if run and run[1] - run[0] > limit:
        runs.append(run)
    return runs


def held_over(
    frames: dict[float, dict[str, set[str]]],
    times: list[float],
    span: tuple[float, float],
    step: float,
    limit: float,
) -> float | None:
    """How long a thought keeps the picture it began under, when that is longer than `limit`.

    The picture gives way at the first sample, within `HOLD_WINDOW` seconds and the thought,
    that has lost at least half the names it began under and shows a new one.
    """
    a, b = span
    before = set().union(*nearest_frame(frames, times, a, step).values())
    if not before:
        return None
    later = times[
        bisect.bisect_right(times, a + step / 2) : bisect.bisect_right(
            times, min(b, a + HOLD_WINDOW)
        )
    ]
    for v in later:
        now = set().union(*frames[v].values())
        if len(before - now) >= max(1, len(before) // 2) and now - before:
            return round(v - a, 2) if v - a > limit else None
    return None


def quotation(text: str) -> bool:
    """Whether a cue is itself one quotation: it opens with a quotation mark, and the matching
    mark first closes it at its end."""
    text = text.strip()
    close = QUOTATION_MARKS.get(text[:1])
    return close is not None and len(text) > 1 and text.find(close, 1) == len(text) - 1


def label_runs(trace_lines: Iterable[str], step: float) -> dict[str, list[tuple[float, float]]]:
    """Each label's runs of legible samples, from its first to its last; a gap ends a run."""
    seen: dict[str, set[float]] = {}
    for t, _scene, fields in trace_rows(trace_lines, 5):
        if float(fields[0]) >= LEGIBLE_CONTRAST:
            seen.setdefault(fields[2].strip(), set()).add(round(t, 3))
    runs = {}
    for label, times in seen.items():
        spans: list[list[float]] = []
        for t in sorted(times):
            if spans and t - spans[-1][1] <= 1.5 * step + 1e-9:
                spans[-1][1] = t
            else:
                spans.append([t, t])
        runs[label] = [(a, b) for a, b in spans]
    return runs


def repeated(said: list[str], label: list[str]) -> set[int]:
    """The positions of the cue's words that the label repeats as one run of them."""
    n = len(label)
    return {
        k + i for k in range(len(said) - n + 1) if n and said[k : k + n] == label for i in range(n)
    }


def caption_echoes(timeline: dict, trace_lines: Iterable[str], step: float) -> list[dict]:
    """The caption cues of three words or more that labels repeat while the cue shows.

    A cue is a whole echo when one label legible at a sample within it holds exactly its
    words, in order, unless the cue is itself one quotation: the narration then reads out what
    the picture shows, and the cue is listed as quoted. Otherwise it is listed when the labels
    drawn during it, legible from a sample within it, repeat at least 80% of its words, each
    label as one run of them.
    """
    runs, found = label_runs(trace_lines, step), []
    for cue in timeline.get("captions", []):
        said, a, b = words(cue["text"]), cue["start"], cue["end"]
        if len(said) < ECHO_WORDS:
            continue
        whole = sorted(
            label
            for label, spans in runs.items()
            if words(label) == said and any(s < b and e >= a for s, e in spans)
        )
        drawn = {
            label: repeated(said, words(label))
            for label, spans in runs.items()
            if any(a <= s < b for s, _ in spans)
        }
        drawn = {label: places for label, places in drawn.items() if places}
        share = len(set().union(*drawn.values())) / len(said)
        if whole or share >= ECHO_SHARE:
            quoted = quotation(cue["text"])
            found.append(
                {
                    "start": round(a, 3),
                    "segment": cue.get("segment"),
                    "text": cue["text"].strip(),
                    "whole": bool(whole) and not quoted,
                    "quoted": quoted,
                    "share": 1.0 if whole else round(share, 2),
                    "labels": whole or sorted(drawn),
                }
            )
    return found


def continuity(
    timeline: dict, trace_lines: Iterable[str], step: float = 1 / 30, limit: float = 1.0
) -> dict:
    """Speech left without a legible name, a previous picture held into a thought, and echoes.

    The trace samples the film every `step` seconds and lists only frames that paint a
    label, so a sample with no legible name in its scene is absent. A run of a thought's
    speech longer than `limit` without a legible name of its scene is unnamed speech. A
    thought that begins under names that at least half give way to new ones more than
    `limit` into it, within 4 s and the thought, holds the previous picture over. The
    caption cues that labels repeat are listed by `caption_echoes`.
    """
    trace_lines = list(trace_lines)
    frames = legible_frames(trace_lines)
    times = sorted(frames)
    unnamed, held = [], []
    for segment in timeline["segments"]:
        for key, a, b in thought_spans(segment):
            unnamed += [
                {"thought": key, "from": start, "to": end}
                for start, end in unnamed_runs(frames, times, segment["id"], (a, b), step, limit)
            ]
            seconds = held_over(frames, times, (a, b), step, limit)
            if seconds is not None:
                held.append({"thought": key, "held": seconds})
    echoes = caption_echoes(timeline, trace_lines, step)
    return {"unnamed_speech": unnamed, "held_over": held, "caption_echoes": echoes}


def overlap(a: list[int], b: list[int]) -> float:
    """The intersection of two boxes over their union, counting their edge pixels.

    Counting edge pixels lets a ruled row of no height be followed too.
    """
    w = max(0, min(a[2], b[2]) - max(a[0], b[0]) + 1)
    h = max(0, min(a[3], b[3]) - max(a[1], b[1]) + 1)
    areas = [(r[2] - r[0] + 1) * (r[3] - r[1] + 1) for r in (a, b)]
    return w * h / (sum(areas) - w * h)


def seats(
    timeline: dict, mark_lines: Iterable[str], step: float = 1 / 30, limit: float = 0.6
) -> list[dict]:
    """Marks that stand in speech before a name is legible at them.

    Each mark row is one firm mark of a voiced frame: its time, scene, box and whether a
    legible name stands at it. A mark is followed from frame to frame by its overlapping
    box. A mark that stands more than `limit` before its name arrives waits for the name
    in its place: a seat. A mark that is never named is an illustration, not a seat.
    """
    spans = [span for segment in timeline["segments"] for span in thought_spans(segment)]
    frames = {}
    for t, scene, fields in trace_rows(mark_lines, 7):
        box = [int(v) for v in fields[:4]]
        frames.setdefault(round(t, 3), []).append((scene, box, fields[4] == "1"))
    live, ended = [], []
    for t in sorted(frames):
        ended += [mark for mark in live if t - mark["last"] > step * 1.5]
        live = [mark for mark in live if t - mark["last"] <= step * 1.5]
        for scene, box, named in frames[t]:
            known = [m for m in live if m["scene"] == scene and m["last"] < t]
            mark = max(known, key=lambda m: overlap(m["box"], box), default=None)
            if mark is None or overlap(mark["box"], box) <= 0.4:
                mark = {"scene": scene, "first": t, "named": None}
                live.append(mark)
            mark.update(last=t, box=box)
            if named and mark["named"] is None:
                mark["named"] = t
    found = []
    for mark in ended + live:
        if mark["named"] is not None and mark["named"] - mark["first"] > limit + 1e-9:
            thought = next(
                (key for key, a, b in spans if a - 0.3 <= mark["first"] <= b + 0.3), None
            )
            found.append(
                {
                    "thought": thought,
                    "at": round(mark["first"], 3),
                    "lag": round(mark["named"] - mark["first"], 2),
                    "box": mark["box"],
                }
            )
    return sorted(found, key=lambda row: (row["at"], row["box"]))


def print_report(report: dict) -> None:
    """Print the report's counts as JSON, then one line per finding."""
    lists = ("findings", "far_from_words", "recalls", "continuity")
    summary = {k: v for k, v in report.items() if k not in lists}
    counts = {k: len(v) for k, v in report["continuity"].items()}
    listed = {k: len(report[k]) for k in ("far_from_words", "recalls")}
    print(json.dumps({**summary, **listed, **counts}))
    for row in report["findings"]:
        print(
            f"{row['scene']}  {row['verdict']:15s} {row['delta']:+.2f}s"
            f"  legible {row['legible']:.2f}  spoken {row['spoken']:.2f}"
            f"  {row['label']}"
        )
    for row in report["far_from_words"]:
        spoken = ", ".join(f"{t:.2f}" for t in row["spoken"])
        print(
            f"{row['scene']}  far-from-words  legible {row['legible']:.2f}"
            f"  spoken {spoken}  {row['label']}"
        )
    for row in report["recalls"]:
        print(f"{row['scene']}  recall  legible {row['legible']:.2f}  {row['label']}")
    for row in report["continuity"]["unnamed_speech"]:
        print(f"{row['thought']}  unnamed-speech  {row['from']:.2f}-{row['to']:.2f}")
    for row in report["continuity"]["held_over"]:
        print(f"{row['thought']}  held-over  {row['held']:.2f}s")
    for row in report["continuity"]["caption_echoes"]:
        kind = "whole" if row["whole"] else f"{row['share']:.0%}"
        print(f"{row['segment']}  caption-echo  {row['start']:.2f}  {kind}  {row['text']}")
    for row in report["continuity"].get("seats", []):
        print(f"{row['thought']}  seat  {row['at']:.2f}  waits {row['lag']:.2f}s  {row['box']}")


def read_trace(path: Path) -> list[str]:
    """The lines of a trace that frame-audit.mjs wrote."""
    with path.open(encoding="utf-8") as handle:
        return handle.readlines()


def full_report(timeline: dict, trace: Path, marks: Path | None, step: float) -> dict:
    """The audit of a trace at the default tolerance, as the command writes its report.

    The report adds the trace's continuity, the seats of the mark trace when one is given, and
    every judged label.
    """
    lines = read_trace(trace)
    report, judged = audit(timeline, lines)
    report["continuity"] = continuity(timeline, lines, step)
    if marks is not None:
        report["continuity"]["seats"] = seats(timeline, read_trace(marks), step)
    return {**report, "judged": judged}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("timeline", type=Path, help="the timeline the trace ran on")
    parser.add_argument("trace", type=Path, help="the label trace frame-audit.mjs wrote")
    parser.add_argument("--out", type=Path, metavar="FILE", help="the report to write")
    parser.add_argument("--tolerance", type=float, default=0.3, metavar="SECONDS")
    parser.add_argument(
        "--step", type=float, default=1 / 30, metavar="SECONDS", help="the trace's sampling step"
    )
    parser.add_argument(
        "--bind", metavar="FILE", help="the production timeline the audited timeline derives from"
    )
    parser.add_argument("--marks", type=Path, metavar="FILE", help="the mark trace to judge")
    options = parser.parse_args(argv)
    timeline = json.loads(options.timeline.read_text(encoding="utf-8"))
    lines = read_trace(options.trace)
    try:
        report, judged = audit(timeline, lines, options.tolerance)
    except PictureError as error:
        msg = f"sync audit: {error}"
        raise SystemExit(msg) from None
    report["continuity"] = continuity(timeline, lines, options.step)
    if options.marks is not None:
        report["continuity"]["seats"] = seats(timeline, read_trace(options.marks), options.step)
    if options.bind is not None:
        bound = repository.sha(Path(options.bind).resolve())
        report["bound_timeline"] = {"path": options.bind, "sha256": bound}
        report["composition_sha256"] = repository.sha(repository.ROOT / COMPOSITION_SCRIPT)
    if options.out is not None:
        with options.out.open("w", encoding="utf-8") as handle:
            json.dump({**report, "judged": judged}, handle, ensure_ascii=False, indent=1)
    print_report(report)


if __name__ == "__main__":
    main()
