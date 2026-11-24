"""Give each segment its caption phrases: authored cue boundaries, or its language's own.

A script may author a segment's cue boundaries; otherwise the phrasing that the edition's
language declares sets them (`filmkit.languages`): `full-width-punctuation` or `english-grammar`,
each held once in its module, with the edition's declared caption terms. Either way the phrases
must hold the exact narration, each on one line within the language's caption limit, and, in a
phrasing bounded by sentences, no phrase may cross the end of a caption sentence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import filmkit.captions.english_grammar as english_grammar
import filmkit.captions.full_width_punctuation as full_width_punctuation
import filmkit.languages as languages
from filmkit.captions import CaptionError
from filmkit.film import FILM

if TYPE_CHECKING:
    from collections.abc import Callable

# Each phrasing a declaration may name: the function that phrases a text within a limit and with
# the edition's terms, and the caption sentences no phrase may cross, where it is bounded by them.
PHRASINGS: dict[str, tuple[Callable, Callable | None]] = {
    "full-width-punctuation": (full_width_punctuation.phrases, None),
    "english-grammar": (english_grammar.phrases, english_grammar.sentences),
}


def _crosses_sentence(sentences: Callable, text: str, phrases: list[str], limit: int) -> bool:
    """Whether a phrase's words cross the end of a caption sentence."""
    boundaries, position = [], 0
    for sentence in sentences(text, limit):
        boundaries.append(position + len(sentence.rstrip()))
        position += len(sentence)
    position = 0
    for phrase in phrases:
        start = position + len(phrase) - len(phrase.lstrip())
        end = position + len(phrase.rstrip())
        if any(start < boundary < end for boundary in boundaries):
            return True
        position += len(phrase)
    return False


def caption_terms(code: str) -> tuple[str, ...]:
    """The caption terms an edition declares, or none."""
    edition = FILM.editions.get(code)
    return edition.caption_terms if edition else ()


def segment_caption_phrases(segment: dict, code: str) -> list[str]:
    """Keep authored cue boundaries and preserve the complete spoken copy of an edition."""
    captions = languages.language(code).captions
    if captions.phrasing not in PHRASINGS:
        msg = f"The engine holds no caption phrasing {captions.phrasing}, which {code} declares"
        raise CaptionError(msg)
    phrase, sentences = PHRASINGS[captions.phrasing]
    limit = captions.limit
    phrases = segment.get("caption_phrases") or phrase(segment["text"], limit, caption_terms(code))
    if not phrases or "".join(phrases) != segment["text"]:
        msg = "Authored captions must preserve the complete exact narration"
        raise CaptionError(msg)
    if any("\n" in phrase or len(phrase) > limit for phrase in phrases):
        msg = "Authored captions require readable single-line semantic cues"
        raise CaptionError(msg)
    if sentences is not None and _crosses_sentence(sentences, segment["text"], phrases, limit):
        msg = "Authored captions cross a caption sentence's boundary"
        raise CaptionError(msg)
    return phrases
