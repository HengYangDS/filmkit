"""Phrase and time the subtitles of each edition.

A caption that cannot keep the exact narration in readable one-line cues bound to its aligned
words raises `CaptionError`; so does a value of the film that the chapter metadata cannot keep
(`filmkit.captions.documents.require_metadata_values`).
"""


class CaptionError(ValueError):
    """Captions that cannot keep the exact narration within readable, word-bound cues, or
    subtitle documents that cannot keep a value of the film."""
