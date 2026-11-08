"""The sentences a viewer hears, as a review judges them one by one.

Every thought of every segment is split into sentences at its sentence marks, 。？！ in Chinese and
. ? ! in English, together with any closing quotes and brackets after the mark, and a mark
inside a quotation does not end a sentence, so a quoted sentence stays whole. A quotation opens
at “ ‘ 「 or 『 and closes at its closing mark, or opens at a straight double quote and closes at
the next one; a quotation that closes after a sentence mark ends its sentence. A thought that
ends without a mark is one sentence. Each sentence has the id `segment.thought.sentence`,
numbered from 1, its text without the spaces around it, and its start and end in the timeline:
the start of the aligned word that holds its first spoken unit and the end of the one that holds
its last.

Usage, from `filmkit.review.prompts`: `sentences(timeline, code)` for one edition's timeline.
"""

from __future__ import annotations

import filmkit.narration.spoken_units as spoken_units
from filmkit.review import ReviewError

# Marks that end a sentence, closing marks that stay with it, and the quotation marks that open
# and close a quotation, in which no mark ends a sentence.
SENTENCE_MARKS = frozenset(spoken_units.SENTENCE_ENDS)
CLOSING_MARKS = frozenset(spoken_units.CLOSING_MARKS)
OPENING_QUOTES = frozenset(spoken_units.OPENING_QUOTES)
CLOSING_QUOTES = frozenset(spoken_units.CLOSING_QUOTES)


def split(text: str) -> list[str]:
    """A thought's sentences: its text cut after each sentence mark outside a quotation, with the
    closing marks after it, each without its outer spaces."""
    found, start, depth, straight, index = [], 0, 0, False, 0
    while index < len(text):
        character = text[index]
        closes = (character in CLOSING_QUOTES and depth) or (character == '"' and straight)
        if character in OPENING_QUOTES:
            depth += 1
        elif character in CLOSING_QUOTES and depth:
            depth -= 1
        elif character == '"':
            straight = not straight
        index += 1
        outside = not depth and not straight
        if character in SENTENCE_MARKS and outside:
            while index < len(text) and text[index] in CLOSING_MARKS:
                index += 1
        elif not (closes and outside and text[index - 2 : index - 1] in SENTENCE_MARKS):
            continue
        found.append(text[start:index])
        start = index
    found.append(text[start:])
    return [sentence.strip() for sentence in found if spoken_units.units(sentence)]


def sentences(timeline: dict, code: str) -> list[dict]:
    """Every sentence of an edition's timeline, in order, with its id, text and times.

    `code` names the edition only for the refusal; both languages split at their own marks.
    Refused, naming the segment, when its aligned words do not cover its text exactly.
    """
    found = []
    for segment in timeline["segments"]:
        words = segment["words"]
        groups = segment.get("utterance_groups") or [segment["text"]]
        try:
            spans = spoken_units.thought_spans(segment["text"], words, groups)
        except spoken_units.AlignmentError as error:
            msg = f"{segment['id']}: {error}"
            raise ReviewError(msg) from error
        # Each unit of the thought, in order, is held by one aligned word.
        owners = [
            index for index, word in enumerate(words) for _ in spoken_units.units(word["text"])
        ]
        offset = 0
        for number, (span, group) in enumerate(zip(spans, groups, strict=True), 1):
            for count, text in enumerate(split(group), 1):
                size = len(spoken_units.units(text))
                first, last = owners[offset], owners[offset + size - 1]
                offset += size
                found.append(
                    {
                        "id": f"{segment['id']}.{number}.{count}",
                        "text": text,
                        "start": words[first]["start"],
                        "end": words[last]["end"],
                    }
                )
            if owners[offset - 1] != span.last:
                msg = f"{code} {segment['id']}.{number}: its sentences do not end with its words"
                raise ReviewError(msg)
    return found
