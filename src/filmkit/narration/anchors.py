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
anything, and it names every broken rule at once, by edition, segment, thought and id.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import filmkit.repository as repository
from filmkit.narration.spoken_units import units
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


def require_editions() -> dict[str, dict[str, list[Anchor]]]:
    """Both editions' anchors by edition code, refusing every broken rule of either script."""
    found, refusals = {}, []
    for code in CODES:
        try:
            found[code] = require(repository.read(Edition(code).script), code)
        except AnchorError as error:
            refusals.append(str(error))
    if refusals:
        raise AnchorError("\n".join(refusals))
    return found
