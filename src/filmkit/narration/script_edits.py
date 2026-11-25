"""Apply exact text edits to the film scripts and keep mirrors, speech, retakes and anchors bound.

An edits file maps each kind of edit to per-edition lists. A replacement [thought, old, new]
replaces a phrase that occurs exactly once in the thought's text; a split [thought, seam] cuts the
thought after a seam that occurs exactly once inside it; a rewrite [segment, [thoughts]] replaces a
segment's thoughts whole; an anchor [thought, [first, after], id, words] marks the units first to
after of the thought's text, which must say `words`; an unanchor [segment, id] removes an id's
marks. A thought is "segment.index" (1-based), indexed as before the edits, and a phrase, a seam
and a span are read on the thought's text without its marks. A file's unanchors apply first, then
its anchors, its replacements, its splits from the last thought and its rewrites; a segment that a
rewrite names takes no other edit of the same file.

A segment that marks anchors (`filmkit.narration.anchors`) is edited in its anchored thoughts,
from which its plain thoughts are filled. A replacement keeps an anchor whose words it leaves, and
one whose words are its phrase or hold it, on the new words; it is refused, naming the anchor and
its words, when its phrase holds an anchor's boundary and reaches beyond it, unless its new text
restates the anchor's marks. A split is refused when its seam falls inside an anchor. A rewrite
moves each anchor whose words, compared by their units, its new thoughts say exactly once, or as
often as the old thoughts did, to that occurrence or the one of the same rank; where spaces
delimit the language's words, as in English, an occurrence begins and ends at a word's edge. Its
thoughts must be a nonempty list of strings, each saying a spoken unit. Every other anchor is
refused by name, with its words and their new occurrences, unless the new thoughts restate it.
Marks that an edit places stand immediately before their first unit and after their last.

Each segment whose thoughts changed has its text rebuilt from its plain thoughts and its spoken
text derived through the edition's pronunciation, and each bound retake follows its
exact text to its new index; a retake whose text no longer occurs exactly once is released. An
edit of marks alone is written and keeps the text, the speech and every retake. Nothing is
written unless every edit of every edition applies, and a script that breaks an anchor's rule
is refused before and after its edits. The report names each changed segment's thoughts and
retakes and, for a segment that marks anchors, each anchor marked, restated, removed, reworded,
moved, moved by rank and moved to another thought, each kind apart; a move by rank into another
thought is named among both.

Run by `filmkit edit --edits FILE [--dry-run]` (`apply_edits`).
An edits file: {"replace": {"en": [["13.5", "proves no", "does not prove"]]},
    "split": {"en": [["07.2", "the evidence."]]}, "rewrite": {"zh": [["03", ["…", "…"]]]},
    "anchor": {"zh": [["03.2", [4, 7], "order", "有先后"]]}, "unanchor": {"zh": [["03", "law"]]}}
Paths are relative to the repository root.
"""

import copy
from dataclasses import replace as replaced

import filmkit.languages as languages
import filmkit.repository as repository
from filmkit.narration import anchors
from filmkit.narration.anchors import Mark, Thought
from filmkit.narration.pronunciation import pronunciation, pronunciation_text
from filmkit.narration.retakes import rebind
from filmkit.narration.spoken_units import units
from filmkit.production import CODES, Edition

# The kinds of edit an edits file holds.
KINDS = ("replace", "split", "rewrite", "anchor", "unanchor")
# What a report names of a segment's anchors, each kind apart.
ANOTHER_THOUGHT = "moved_to_another_thought"
ANCHOR_REPORT = ("marked", "restated", "removed", "reworded", "moved", "moved_by_rank")
# Characters that continue an English word, so that an occurrence beside one is inside a word.
WORD_JOINS = "'’-"


def edit(
    script: dict,
    cast: dict,
    replace: list = (),
    split: list = (),
    *,
    contract: dict,
    code: str,
    rewrite: list = (),
    anchor: list = (),
    unanchor: list = (),
) -> tuple[dict, dict, list[dict]]:
    """Apply one edition's edits to copies of its script and cast.

    Args:
        script: The edition's script.
        cast: The edition's cast, whose thought retakes follow their text.
        replace: The [thought, old, new] replacements.
        split: The [thought, seam] splits.
        contract: The edition's pronunciation, which derives each spoken text.
        code: The edition's code, which names it in a refusal.
        rewrite: The [segment, thoughts] rewrites.
        anchor: The [thought, [first, after], id, words] marks.
        unanchor: The [segment, id] removals.

    Returns:
        The edited script and cast, and a report of each changed segment.
    """
    script, cast = copy.deepcopy(script), copy.deepcopy(cast)
    marked = anchors.require(script, code)
    thoughts = {segment["id"]: _thoughts(segment) for segment in script["segments"]}
    before = {sid: list(found) for sid, found in thoughts.items()}
    notes = {sid: {kind: [] for kind in (*ANCHOR_REPORT, ANOTHER_THOUGHT)} for sid in thoughts}
    _require_rewrites_alone(rewrite, [*replace, *split, *anchor], unanchor, code)
    for sid, name in unanchor:
        _unanchor(thoughts, sid, name, code)
        notes[sid]["removed"].append(name)
    for key, span, name, words in anchor:
        _anchor(thoughts, key, span, name, words, code)
        notes[key.split(".")[0]]["marked"].append(name)
    for key, old, new in replace:
        _replace(thoughts, key, old, new, code, notes)
    # Split later thoughts first so that the indices of earlier ones stay valid.
    for key, seam in sorted(
        split, key=lambda item: (item[0].split(".")[0], -int(item[0].split(".")[1]))
    ):
        _split(thoughts, key, seam, code)
    for sid, written in rewrite:
        _rewrite(thoughts, sid, written, marked.get(sid, []), code, notes.get(sid, {}))
    changed = []
    for segment in script["segments"]:
        sid, found = segment["id"], thoughts[segment["id"]]
        if found == before[sid]:
            continue
        changed.append(_write_segment(segment, found, before[sid], cast, contract))
        if sid in marked or "anchored_groups" in segment:
            changed[-1].update({f"anchors_{kind}": items for kind, items in notes[sid].items()})
    anchors.require(script, code)
    return script, cast, changed


def _thoughts(segment: dict) -> list[Thought]:
    """A segment's thoughts as edits read them: its anchored ones, or its plain ones unmarked."""
    if "anchored_groups" in segment:
        return [Thought.parse(text) for text in segment["anchored_groups"]]
    return [Thought(text, ()) for text in segment.get("utterance_groups", [])]


def _write_segment(
    segment: dict, found: list[Thought], before: list[Thought], cast: dict, contract: dict
) -> dict:
    """Fill a changed segment from its thoughts, in place, and report its thoughts and retakes.

    A segment left without a mark is plain again; one whose plain thoughts are unchanged keeps
    its text, its spoken text and its retakes.
    """
    sid, groups = segment["id"], [thought.text for thought in found]
    plain = [thought.text for thought in before]
    if any(thought.marks for thought in found):
        segment["anchored_groups"] = [thought.written() for thought in found]
    else:
        segment.pop("anchored_groups", None)
    bound = cast.get("retakes", {}).get(sid, {}).get("groups", {})
    moved, released = rebind(bound, groups)
    if groups != plain:
        segment["utterance_groups"] = groups
        segment["text"] = "".join(groups)
        segment["spoken_text"] = pronunciation_text({"text": segment["text"]}, contract)
        if bound:
            cast["retakes"][sid]["groups"] = moved
    return _change_report(sid, plain, groups, moved, released)


def _require_rewrites_alone(rewrite: list, keyed: list, unanchor: list, code: str) -> None:
    """Refuse a rewrite of a segment that another edit of the same file names."""
    named = {edit[0].split(".")[0] for edit in keyed} | {sid for sid, _ in unanchor}
    for sid in [sid for sid, _ in rewrite if sid in named]:
        msg = f"{code} {sid}: a rewritten segment takes no other edit of the same file"
        raise ValueError(msg)


def _thought(thoughts: dict, key: str, code: str) -> tuple[list[Thought], int]:
    """The thoughts of the segment a key names, and the key's 0-based place among them."""
    segment, index = key.split(".")
    groups = thoughts.get(segment, [])
    if not 1 <= int(index) <= len(groups):
        msg = f"{code} {key}: no such thought"
        raise ValueError(msg)
    return groups, int(index) - 1


def _segment_ids(groups: list[Thought]) -> set[str]:
    """The ids a segment's thoughts mark."""
    return {mark.id for thought in groups for mark in thought.marks}


def _replace(thoughts: dict, key: str, old: str, new: str, code: str, report: dict) -> None:
    """Replace a phrase that occurs exactly once in a thought, keeping its anchors on their words
    or refusing one whose boundary the phrase holds and reaches beyond."""
    groups, at = _thought(thoughts, key, code)
    notes = report[key.split(".")[0]]
    thought, fresh = groups[at], Thought.parse(new)
    if thought.text.count(old) != 1:
        msg = f"{code} {key}: phrase not found exactly once: {old}"
        raise ValueError(msg)
    start = thought.text.index(old)
    end = start + len(old)
    existing, restated = _segment_ids(groups), {mark.id for mark in fresh.marks}
    for name, first, last in thought.spans()[0]:
        if name in restated:
            continue
        if first <= start and end <= last:
            after = thought.text[first:start] + fresh.text + thought.text[end:last]
            if after != thought.text[first:last]:
                notes["reworded"].append(
                    {"id": name, "before": thought.text[first:last], "after": after}
                )
        elif not (last <= start or first >= end):
            msg = (
                f"{code} {key}: the replacement reaches beyond anchor {name}"
                f" ({thought.text[first:last]}); restate its marks in its new text"
            )
            raise ValueError(msg)
    kept, shift = [m for m in thought.marks if m.id not in restated], len(fresh.text) - len(old)
    marks = [
        *(mark for mark in kept if mark.at <= start),
        *(replaced(mark, at=mark.at + start) for mark in fresh.marks),
        *(replaced(mark, at=mark.at + shift) for mark in kept if mark.at >= end),
    ]
    groups[at] = Thought(thought.text[:start] + fresh.text + thought.text[end:], tuple(marks))
    notes["restated"] += sorted(restated & existing)
    notes["marked"] += sorted(restated - existing)


def _split(thoughts: dict, key: str, seam: str, code: str) -> None:
    """Cut a thought in two after a seam that occurs exactly once inside it and inside no
    anchor; the marks at the cut that close stay with the first part, those that open go on."""
    groups, at = _thought(thoughts, key, code)
    thought = groups[at]
    text = thought.text
    if text.count(seam) != 1 or text.endswith(seam):
        msg = f"{code} {key}: seam not found exactly once inside the thought: {seam}"
        raise ValueError(msg)
    cut = text.index(seam) + len(seam)
    for name, first, last in thought.spans()[0]:
        if first < cut < last:
            msg = f"{code} {key}: the seam falls inside anchor {name} ({text[first:last]})"
            raise ValueError(msg)
    head = [m.at < cut or (m.at == cut and m.closes) for m in thought.marks]
    first_marks = tuple(m for m, kept in zip(thought.marks, head, strict=True) if kept)
    rest = tuple(
        replaced(m, at=m.at - cut) for m, kept in zip(thought.marks, head, strict=True) if not kept
    )
    groups[at : at + 1] = [Thought(text[:cut], first_marks), Thought(text[cut:], rest)]


def unit_places(text: str) -> list[int]:
    """The place in a text of each of its units, in order."""
    return [place for place, character in enumerate(text) if units(character)]


def _marked(thought: Thought, first: int, after: int, name: str) -> Thought:
    """A thought with an anchor marked on its units first to after: the open mark immediately
    before the first unit, after any mark already there, and the close mark immediately after
    the last, before any mark already there."""
    places = unit_places(thought.text)
    opens, closes = places[first], places[after - 1] + 1
    marks = list(thought.marks)
    marks.insert(sum(mark.at <= opens for mark in marks), Mark(opens, False, name))
    marks.insert(sum(mark.at < closes for mark in marks), Mark(closes, True, name))
    return Thought(thought.text, tuple(marks))


def _anchor(thoughts: dict, key: str, span: list, name: str, words: str, code: str) -> None:
    """Mark an anchor on a span of a thought's units that says the words the edit expects."""
    groups, at = _thought(thoughts, key, code)
    if name in _segment_ids(groups):
        msg = f"{code} {key.split('.')[0]} {name}: is marked already"
        raise ValueError(msg)
    text, (first, after) = groups[at].text, span
    places = unit_places(text)
    if not (type(first) is int and type(after) is int and 0 <= first < after <= len(places)):
        msg = f"{code} {key}: the units {first}-{after} are not a span of its {len(places)} units"
        raise ValueError(msg)
    said = text[places[first] : places[after - 1] + 1]
    if units(said) != units(words):
        msg = f"{code} {key}: the units {first}-{after} say {said}, not {words}"
        raise ValueError(msg)
    groups[at] = _marked(groups[at], first, after, name)


def _unanchor(thoughts: dict, sid: str, name: str, code: str) -> None:
    """Remove an id's marks from a segment that marks it."""
    groups = thoughts.get(sid, [])
    if name not in _segment_ids(groups):
        msg = f"{code} {sid} {name}: is not marked"
        raise ValueError(msg)
    thoughts[sid] = [Thought(t.text, tuple(m for m in t.marks if m.id != name)) for t in groups]


def occurrences(groups: list[Thought], words: str, code: str) -> list[tuple[int, int]]:
    """Each place in a segment's thoughts where words are said, compared by their units, as
    (thought, first unit), both from 0, in order; in a language whose words spaces delimit, only
    those that begin and end at a word's edge."""
    wanted, found = units(words), []
    for index, thought in enumerate(groups):
        text, places = thought.text, unit_places(thought.text)
        spoken = units(text)
        for first in range(len(spoken) - len(wanted) + 1):
            if spoken[first : first + len(wanted)] != wanted:
                continue
            begin, end = places[first], places[first + len(wanted) - 1] + 1
            inside = (begin > 0 and _joins(text[begin - 1])) or (
                end < len(text) and _joins(text[end])
            )
            if not languages.language(code).spaced or not inside:
                found.append((index, first))
    return found


def _joins(character: str) -> bool:
    """Whether a character beside a word continues it: a letter, a digit or a word join."""
    return bool(units(character)) or character in WORD_JOINS


def _rewrite(thoughts: dict, sid: str, written: list, old: list, code: str, notes: dict) -> None:
    """Replace a segment's thoughts whole and move each anchor to the words it still says, or
    refuse every anchor it cannot move, each with its words and their new occurrences."""
    if sid not in thoughts:
        msg = f"{code} {sid}: no such segment"
        raise ValueError(msg)
    if not isinstance(written, list) or not written or not all(isinstance(t, str) for t in written):
        msg = f"{code} {sid}: a rewrite's thoughts are a nonempty list of strings"
        raise ValueError(msg)
    before, groups = thoughts[sid], [Thought.parse(text) for text in written]
    for index, thought in enumerate(groups, 1):
        if not units(thought.text):
            msg = f"{code} {sid}.{index}: a rewritten thought says no spoken unit"
            raise ValueError(msg)
    restated, refusals = _segment_ids(groups), []
    for anchor in [anchor for anchor in old if anchor.id not in restated]:
        then = occurrences(before, anchor.words, code)
        now = occurrences(groups, anchor.words, code)
        own = (anchor.thought - 1, anchor.units[0] - _offset(before, anchor.thought - 1))
        if len(now) == 1:
            kinds = ["moved"]
        elif len(now) == len(then) and own in then:
            now, kinds = [now[then.index(own)]], ["moved_by_rank"]
        else:
            found = " and ".join(f"{sid}.{index + 1}:{first}" for index, first in now)
            refusals.append(
                f"{code} {sid} {anchor.id}: {anchor.words} is said {_times(len(then))} before"
                f" and {len(now)} after" + (f", at {found}" if found else "")
            )
            continue
        index, first = now[0]
        groups[index] = _marked(groups[index], first, first + len(units(anchor.words)), anchor.id)
        # A move into another thought is named apart, whatever rule moved it.
        if index != own[0]:
            kinds = [kind for kind in kinds if kind != "moved"] + [ANOTHER_THOUGHT]
        move = {"id": anchor.id, "words": anchor.words, "from": f"{sid}.{anchor.thought}"}
        for kind in kinds:
            notes[kind].append({**move, "to": f"{sid}.{index + 1}"})
    if refusals:
        msg = "A rewrite leaves anchors without their words; restate them:\n" + "\n".join(refusals)
        raise ValueError(msg)
    existing = {anchor.id for anchor in old}
    notes["restated"] += sorted(restated & existing)
    notes["marked"] += sorted(restated - existing)
    thoughts[sid] = groups


def _offset(groups: list[Thought], index: int) -> int:
    """The units of the thoughts before the one at `index`."""
    return sum(len(units(thought.text)) for thought in groups[:index])


def _times(count: int) -> str:
    return f"{count} time" + "s" * (count != 1)


def _change_report(
    segment: str, before: list[str], after: list[str], moved: dict, released: list[str]
) -> dict:
    """What an edit changed in one segment: its thoughts and its retakes."""
    return {
        "segment": segment,
        "thoughts_before": len(before),
        "thoughts_after": len(after),
        "new_thoughts": [index for index, text in enumerate(after, 1) if text not in before],
        "retakes_moved": {index: take["seed"] for index, take in moved.items()},
        "retakes_released": released,
    }


def apply_edits(edits: dict, *, dry_run: bool = False) -> dict:
    """Apply an edits file's edits to every edition's script and cast, or with `dry_run` only
    report them (`filmkit edit`): the report of each edition's changed segments. Nothing is
    written unless every edit of every edition applies; a refused edit raises `ValueError`."""
    if set(edits) - set(KINDS) or any(set(lists) - set(CODES) for lists in edits.values()):
        msg = f"An edits file maps {', '.join(KINDS)} to editions"
        raise ValueError(msg)
    edited = {}
    for code in CODES:
        asked = {kind: edits.get(kind, {}).get(code, []) for kind in KINDS}
        if any(asked.values()):
            edition = Edition(code)
            script = repository.read(edition.script)
            anchors.require(script, code)
            contract, _ = pronunciation(code)
            cast = repository.read(edition.cast)
            edited[code] = edit(script, cast, contract=contract, code=code, **asked)
    if not dry_run:
        for code, (script, cast, changed) in edited.items():
            if changed:
                _write(Edition(code), script, cast)
    report = {code: changed for code, (_, _, changed) in edited.items()}
    return {"dry_run": dry_run, "editions": report}


def _write(edition: Edition, script: dict, cast: dict) -> None:
    """Write an edition's edited script and cast, the one copy of its narration."""
    repository.write(edition.script, script)
    repository.write(edition.cast, cast)
