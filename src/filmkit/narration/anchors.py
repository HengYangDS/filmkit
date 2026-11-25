"""Anchors: named spans of a script's own words, which a picture names instead of quoting them.

A segment may hold `anchored_groups`: its thoughts with anchors marked in them, each anchor written
as its id in braces before its words and the id after a slash in braces after them, as in
`{order}有先后{/order}`. Anchors may nest and cross, and two ids may mark the same words. An id is
kebab-case (lowercase ASCII letters and digits, single hyphens between words, a letter first), not
`constructor`, which every JavaScript object inherits, and names one anchor of its segment in its
edition; an anchor opens and closes in one thought and marks
a spoken unit of it. A segment that holds `anchored_groups` has its `utterance_groups` and `text`
filled from them without their marks, so every reader of the narration reads the plain words as
before; `filmkit.narration.script_edits` fills them, and is the way to change an anchored
segment's words.

An anchor's `units` are its first unit's index among the units of the segment's text and the index
after its last; units are the text's Han characters, Latin letters and digits, the units the
aligner covers (`filmkit.narration.spoken_units`). "Anchor" here is not the template's
substitution point (`filmkit.picture.template.ANCHORS`) nor a text's anchor point in the
typography audits.

`require` holds every rule: each command that reads a script's anchors calls it before it writes
anything, and it names every broken rule at once, by edition, segment, thought and id. `place`
gives every segment of a timeline whose script marks any anchor its `anchors`, each id in the
order of its open mark with the times of its words: `start`, the start of the aligned word that
holds its first unit; `end`, the end of the word that holds its last; its `units`; and its
`thought`, counted from 1. A segment that marks none holds an empty object, and a timeline whose
script marks none holds no `anchors`.

`derived_timeline` derives, from an edition's script alone, the timeline that the checks before
narration draw the picture over: the script's fields; for each segment one word per Han character
and per run of Latin letters and digits of its text, each 0.2 s long, 0.5 s between thoughts and
1.0 s before each segment; its anchors as `place` gives them; and no captions. The command prints
each edition's anchors with their thought, words and units and, where the edition's timeline holds
them, their times, and names each id that one edition marks in a segment and the other does not,
which refuses nothing; times that are stale, of other marks than the script's, are named stale and
not given. With --json it prints the same as one document, and with --timeline it writes each
edition's derived timeline as <folder>/<code>.json, so that a film's own tests draw the timeline
that narration's check draws. With --place it gives a timeline that other code built, of its own
words, what the engine derives for every timeline (`filmkit.film.timeline_values`) and the
anchors its marks take from those words, as `place` does, and writes it back, so that a test that
times its words otherwise still takes its anchors and those values from this module.

Usage: python -m filmkit.narration.anchors [--json] [--timeline FOLDER]
       python -m filmkit.narration.anchors --place TIMELINE --language <code>
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import filmkit.repository as repository
from filmkit.film import FILM, timeline_values
from filmkit.graph import target
from filmkit.narration.spoken_units import HAN, LATIN, units
from filmkit.production import CODES, Edition

# A mark: an id in braces, after a slash when it closes its anchor.
MARK = re.compile(r"\{(/?)([^{}]*)\}")
# An anchor's id: lowercase ASCII letters and digits, single hyphens between words, a letter first.
ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
# The ids that pattern allows and that every JavaScript object inherits: a composition's read of one
# cannot be told from a read of the object's own member, so no anchor takes it.
INHERITED = frozenset({"constructor"})
# The way to change an anchored segment's words, which the refusal of a hand edit names.
SCRIPT_EDITS = "python -m filmkit.narration.script_edits"
# The derived timeline's words: a Han character, or a run of Latin letters and digits; and its
# times in milliseconds: each word, the pause between thoughts and the gap before each segment.
WORD = re.compile(f"[{HAN}]|[{LATIN}]+")
WORD_MS, THOUGHT_MS, SEGMENT_MS = 200, 500, 1000
DERIVED = "Derived from the script for the checks before narration, not from any recording"


class AnchorError(ValueError):
    """A script or timeline whose anchors break their rules."""


@dataclass(frozen=True)
class Mark:
    """A mark of an anchored thought: its place in the plain text, whether it closes, its id."""

    at: int
    closes: bool
    id: str


@dataclass(frozen=True)
class Thought:
    """An anchored thought: its plain text and its marks in the order they are written."""

    text: str
    marks: tuple[Mark, ...]

    @classmethod
    def parse(cls, written: str) -> Thought:
        """Read a written thought into its plain text and its marks."""
        plain, marks, cursor = "", [], 0
        for match in MARK.finditer(written):
            plain += written[cursor : match.start()]
            marks.append(Mark(len(plain), bool(match[1]), match[2]))
            cursor = match.end()
        return cls(plain + written[cursor:], tuple(marks))

    def written(self) -> str:
        """The thought as a script writes it, each mark where it stands."""
        parts, cursor = [], 0
        for mark in self.marks:
            parts += [self.text[cursor : mark.at], "{" + "/" * mark.closes + mark.id + "}"]
            cursor = mark.at
        return "".join(parts) + self.text[cursor:]

    def spans(self) -> tuple[list[tuple[str, int, int]], list[tuple[str, str]]]:
        """The thought's anchors as (id, start, end) in the plain text, in the order of their open
        marks, and its broken rules as (id, problem)."""
        opened: dict[str, int] = {}
        found, problems = {}, []
        if "{" in self.text or "}" in self.text:
            problems.append(("", "a brace that is no mark"))
        for order, mark in enumerate(self.marks):
            if not mark.closes and mark.id in opened:
                problems.append((mark.id, "opens twice"))
            elif not mark.closes:
                opened[mark.id] = order
            elif mark.id not in opened:
                problems.append((mark.id, "closes without opening in its thought"))
            else:
                start = self.marks[opened[mark.id]].at
                found[opened.pop(mark.id)] = (mark.id, start, mark.at)
        problems += [(name, "opens and does not close in its thought") for name in opened]
        spans = [found[order] for order in sorted(found)]
        for name, start, end in spans:
            if not ID.fullmatch(name):
                problems.append((name, "is not a kebab-case id"))
            elif name in INHERITED:
                problems.append((name, "is a name every JavaScript object inherits"))
            if not units(self.text[start:end]):
                problems.append((name, "marks no spoken unit"))
        return spans, problems


@dataclass(frozen=True)
class Anchor:
    """An anchor of a segment: its id, its thought (from 1), its place in that thought's plain
    text, its units among those of the segment's text and the words it marks."""

    id: str
    thought: int
    start: int
    end: int
    units: tuple[int, int]
    words: str


def plain(written: list[str]) -> list[str]:
    """Anchored thoughts without their marks: the utterance groups they fill."""
    return [Thought.parse(thought).text for thought in written]


def segment_anchors(segment: dict, code: str) -> tuple[list[Anchor], list[str]]:
    """A segment's anchors in the order of their open marks, and its broken rules, each named."""
    sid, written = segment["id"], segment["anchored_groups"]
    if not isinstance(written, list) or not all(isinstance(t, str) for t in written):
        return [], [f"{code} {sid}: its anchored_groups are not a list of thoughts"]
    found, problems, offset = [], [], 0
    for index, thought in enumerate(map(Thought.parse, written), 1):
        spans, broken = thought.spans()
        problems += [f"{code} {sid}.{index}{' ' * bool(name)}{name}: {why}" for name, why in broken]
        for name, start, end in spans:
            first = offset + len(units(thought.text[:start]))
            span = (first, first + len(units(thought.text[start:end])))
            found.append(Anchor(name, index, start, end, span, thought.text[start:end]))
        offset += len(units(thought.text))
    groups = plain(written)
    if segment.get("utterance_groups") != groups or segment.get("text") != "".join(groups):
        problems.append(
            f"{code} {sid}: its utterance_groups and text are not its anchored_groups without"
            " marks; an anchored segment's plain thoughts are filled from its anchored ones, so"
            f" change its words with {SCRIPT_EDITS}"
        )
    for name in dict.fromkeys(anchor.id for anchor in found):
        places = [anchor.thought for anchor in found if anchor.id == name]
        if len(places) > 1:
            where = " and ".join(f"{sid}.{place}" for place in places)
            problems.append(f"{code} {where} {name}: marks two anchors of one segment")
    return found, problems


def require(script: dict, code: str) -> dict[str, list[Anchor]]:
    """The anchors of each segment that marks any, by segment id, refusing every broken rule.

    A script or timeline is read alike: each segment that holds `anchored_groups`. A segment
    without them has no anchors and is read as before.
    """
    marked, problems = {}, []
    for segment in script.get("segments", []):
        if "anchored_groups" in segment:
            found, broken = segment_anchors(segment, code)
            marked[segment["id"]] = found
            problems += broken
    if problems:
        msg = "\n".join([f"The {code} script's anchors break their rules:", *problems])
        raise AnchorError(msg)
    return marked


def timed(found: list[Anchor], segment: dict, code: str) -> dict:
    """A segment's anchors with the times of their words, refused unless the segment's words
    hold exactly the units of its text, so that every anchor's units are its words'."""
    words = segment.get("words", [])
    stream, owners = "", []
    for index, word in enumerate(words):
        spoken = units(word["text"])
        stream += spoken
        owners += [index] * len(spoken)
    if found and stream != units(segment["text"]):
        msg = f"{code} {segment['id']}: its words are not the units of its text"
        raise AnchorError(msg)
    placed = {}
    for anchor in found:
        first, after = anchor.units
        if stream[first:after] != units(anchor.words):
            msg = (
                f"{code} {segment['id']}.{anchor.thought} {anchor.id}: its units are not its words'"
            )
            raise AnchorError(msg)
        placed[anchor.id] = {
            "start": words[owners[first]]["start"],
            "end": words[owners[after - 1]]["end"],
            "units": [first, after],
            "thought": anchor.thought,
        }
    return placed


def place(timeline: dict, code: str) -> None:
    """Give every segment of a timeline the `anchors` its marks take from its words, in place;
    a timeline whose segments mark none keeps none."""
    marked = require(timeline, code)
    for segment in timeline["segments"]:
        if any(marked.values()):
            segment["anchors"] = timed(marked.get(segment["id"], []), segment, code)
        else:
            segment.pop("anchors", None)


def require_placed(timeline: dict, code: str) -> None:
    """Refuse a timeline whose marks break their rules or whose `anchors` are not those its marks
    take from its words."""
    placed = {**timeline, "segments": [dict(segment) for segment in timeline["segments"]]}
    place(placed, code)
    if [s.get("anchors") for s in placed["segments"]] != [
        s.get("anchors") for s in timeline["segments"]
    ]:
        msg = (
            f"The {code} timeline's anchors are not those its marks take from its words; run"
            f" {target('refresh-captions', code)}"
        )
        raise AnchorError(msg)


def require_editions() -> dict[str, dict[str, list[Anchor]]]:
    """Every edition's anchors by edition code, refusing every broken rule of any script."""
    found, refusals = {}, []
    for code in CODES:
        try:
            found[code] = require(repository.read(Edition(code).script), code)
        except AnchorError as error:
            refusals.append(str(error))
    if refusals:
        raise AnchorError("\n".join(refusals))
    return found


def derived_timeline(script: dict, code: str) -> dict:
    """The timeline that the checks before narration draw an edition's picture over, derived from
    its script alone, with what the engine derives for every timeline (`film.timeline_values`);
    the same script gives the same bytes."""
    script = timeline_values(script, FILM)
    segments, cursor = [], 0
    for segment in script["segments"]:
        start = cursor
        cursor += SEGMENT_MS
        voice, words = cursor, []
        for index, thought in enumerate(segment.get("utterance_groups") or [segment["text"]]):
            cursor += THOUGHT_MS * bool(index)
            for word in WORD.findall(thought):
                words.append(
                    {"text": word, "start": cursor / 1000, "end": (cursor + WORD_MS) / 1000}
                )
                cursor += WORD_MS
        times = {"start": start / 1000, "voice_start": voice / 1000, "voice_end": cursor / 1000}
        segments.append({**segment, **times, "gap_before": SEGMENT_MS / 1000, "words": words})
    credits = FILM.credits_duration
    duration = math.ceil(cursor / 1000) + credits
    for index, segment in enumerate(segments):
        last = index + 1 == len(segments)
        segment["end"] = duration - credits if last else segments[index + 1]["start"]
    timeline = {
        **script,
        "segments": segments,
        "timing_state": DERIVED,
        "duration": duration,
        "credits_duration": credits,
        "captions": [],
        "edition": code,
        "render_offset": 0,
    }
    place(timeline, code)
    return timeline


def held(code: str, script: dict) -> tuple[dict, str | None, bool]:
    """The anchors an edition's timeline holds, by segment, the timeline's place where it holds
    any or the script marks any, and whether they are stale: not of the script's marks, or not
    those its marks take from its words."""
    path = Edition(code).timeline
    if not path.is_file():
        return {}, None, False
    timeline = repository.read(path)
    found = {s["id"]: s.get("anchors", {}) for s in timeline["segments"]}
    marks = [(s["id"], s.get("anchored_groups")) for s in timeline["segments"]]
    stale = marks != [(s["id"], s.get("anchored_groups")) for s in script["segments"]]
    try:
        require_placed(timeline, code)
    except AnchorError:
        stale = True
    named = any(found.values()) or any("anchored_groups" in s for s in script["segments"])
    return ({} if stale else found), (repository.relative(path) if named else None), stale


def report(marked: dict[str, dict[str, list[Anchor]]], scripts: dict[str, dict]) -> dict:
    """Each edition's anchors by segment, with the times its timeline holds unless they are
    stale, and each id that one edition marks in a segment and the other does not."""
    editions = {}
    for code, found in marked.items():
        times, place, stale = held(code, scripts[code])
        segments = {
            sid: [
                {
                    "id": a.id,
                    "thought": a.thought,
                    "words": a.words,
                    "units": list(a.units),
                    **_times(times.get(sid, {}).get(a.id)),
                }
                for a in listed
            ]
            for sid, listed in found.items()
            if listed
        }
        editions[code] = {"timeline": place, "stale": stale, "segments": segments}
    ids = {
        code: {(sid, a.id) for sid, ls in found.items() for a in ls}
        for code, found in marked.items()
    }
    alone = [
        {"edition": code, "segment": sid, "id": name}
        for code in CODES
        for sid, name in sorted(ids[code] - set().union(*(ids[c] for c in CODES if c != code)))
    ]
    return {"editions": editions, "one_edition": alone}


def _times(placed: dict | None) -> dict:
    return {} if placed is None else {"start": placed["start"], "end": placed["end"]}


def printed(listed: dict) -> list[str]:
    """The report as lines: each edition's anchors, then the ids one edition alone marks."""
    lines = []
    for code, edition in listed["editions"].items():
        rows = [(sid, row) for sid, rows in edition["segments"].items() for row in rows]
        source = edition["timeline"]
        if edition["stale"]:
            times = f"the times in {source} are stale: run {target('refresh-captions', code)}"
        else:
            times = f"times from {source}" if source else "no timeline holds their times"
        count = f"{len(rows)} anchor{'s' * (len(rows) != 1)} in {len(edition['segments'])} segment"
        lines.append(f"{code}: {count}{'s' * (len(edition['segments']) != 1)}; {times}")
        for sid, row in rows:
            first, after = row["units"]
            times = f"  {row['start']:.2f}-{row['end']:.2f} s" if "start" in row else ""
            name = f"{sid}.{row['thought']}"
            lines.append(f"  {name}  {row['id']}  units {first}-{after}{times}  {row['words']}")
    lines.append("Marked in one edition only:")
    lines += [f"  {r['edition']} {r['segment']} {r['id']}" for r in listed["one_edition"]] or [
        "  none"
    ]
    return lines


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Report every edition's anchors.")
    parser.add_argument("--json", action="store_true", help="Print the report as one document")
    parser.add_argument("--timeline", type=Path, help="Write each edition's derived timeline here")
    parser.add_argument(
        "--place", type=Path, help="Give a timeline of other words its anchors, in place"
    )
    parser.add_argument("--language", choices=CODES, help="--place: the timeline's edition")
    options = parser.parse_args(argv)
    if (options.place is None) != (options.language is None):
        parser.error("--place and --language go together")
    if options.place is not None:
        # A timeline other code built takes what the engine derives for every timeline.
        timeline = timeline_values(repository.read(repository.ROOT / options.place), FILM)
        try:
            place(timeline, options.language)
        except AnchorError as error:
            raise SystemExit(str(error)) from None
        repository.write(repository.ROOT / options.place, timeline)
        return
    try:
        marked = require_editions()
    except AnchorError as error:
        raise SystemExit(str(error)) from None
    if options.timeline is not None:
        folder = repository.ROOT / options.timeline
        for code in CODES:
            derived = derived_timeline(repository.read(Edition(code).script), code)
            repository.write(folder / f"{code}.json", derived)
    listed = report(marked, {code: repository.read(Edition(code).script) for code in CODES})
    print(json.dumps(listed, ensure_ascii=False) if options.json else "\n".join(printed(listed)))


if __name__ == "__main__":
    main()
