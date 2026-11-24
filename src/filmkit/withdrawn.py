"""Every key a film may no longer declare, in one table, each with what to do instead.

The loader refuses each where it finds it, all at once and beside the declaration's other
problems (`filmkit.declared_sources.withdrawn_problems`), and the adoption command's
`declaration` question names them so. A key leaves when the engine derives its value from one
source, as decision 10 of treat-languages-as-equals lists: an edition's code, the layout, the
engine's own pins, or the declaration.
"""

from __future__ import annotations

from typing import NamedTuple

from filmkit.places import places
from filmkit.repository import DECLARATION, EVIDENCE


class Withdrawn(NamedTuple):
    """A key a film may no longer declare: the kind of place that held it (`declaration`, an
    `edition`'s table there or its `review` table, its `script`, a script's `performance` table
    `voice_performance`, a `segment` of it, its `cast` or its pronunciation `part`), the key, and
    what to do instead."""

    kind: str
    key: str
    instead: str


# Every edition's places, as the place rule gives them, by the code and file prefix they take.
PLACE = places("<code>", "<slug>")
# What the refusal of each key an edition's code derives says to do.
BY_CODE = "remove it: the engine takes the edition's language from its code"

WITHDRAWN = (
    Withdrawn(
        "script",
        "duration",
        "remove it: an edition lasts as long as its narration, which the assembly counts",
    ),
    Withdrawn(
        "script",
        "credits_duration",
        f"state the credits' length once, as credits_duration in {DECLARATION}",
    ),
    Withdrawn("script", "language", BY_CODE),
    Withdrawn(
        "script",
        "author",
        f"remove it and state the films' author once, as author in {DECLARATION}",
    ),
    Withdrawn(
        "script",
        "fps",
        "remove it: the engine renders and encodes every film at its one frame rate "
        "(filmkit.film.FPS)",
    ),
    *(
        Withdrawn(
            "segment",
            key,
            "remove it: the engine takes a segment's chapter index and title from the script's "
            "chapters, through the segment's chapter",
        )
        for key in ("chapter_index", "chapter_title")
    ),
    Withdrawn("segment", "language", BY_CODE),
    *(
        Withdrawn(
            "performance",
            key,
            "remove it: no step reads it; move any words that record how the voice, its "
            "reference or its takes were made or approved into the edition's cast derivation, "
            "each under its own key",
        )
        for key in ("performance_intent", "energy_curve", "pacing_profile", "provider_notes")
    ),
    Withdrawn(
        "cast",
        "runtime_fit",
        "remove it: nothing reads it, since an edition lasts as long as its narration",
    ),
    *(
        Withdrawn("cast", key, BY_CODE)
        for key in ("narration_language", "language", "reference_language")
    ),
    Withdrawn(
        "cast",
        "performance_recording",
        "remove it: the edition's narration receipt and alignment stand where the narration "
        f"writes them, below {EVIDENCE.as_posix()}/<code>/ (filmkit.production.Edition.ear_first)",
    ),
    Withdrawn(
        "cast",
        "reference_audio",
        f"remove it and move the reference recording to {PLACE.reference}, the place the "
        "edition's code derives",
    ),
    Withdrawn(
        "cast",
        "reference_text_sha256",
        "remove it: the engine takes the SHA-256 of the cast's reference_text",
    ),
    Withdrawn("cast", "provider", "remove it: the engine narrates with its one provider, MLX"),
    *(
        Withdrawn("cast", key, f"remove it: every request takes the engine's {pin}")
        for key, pin in (
            ("model", "voice model (filmkit.narration.voice_model.MODEL)"),
            ("revision", "model revision (filmkit.narration.voice_model.REVISION)"),
            ("reference_mode", "one reference mode, ICL"),
        )
    ),
    Withdrawn(
        "cast",
        "scope",
        "move its text into the cast's derivation, as derivation.scope, which the engine keeps "
        "unread",
    ),
    Withdrawn(
        "script",
        "pronunciation_contract",
        "remove it and split the contract by edition: each edition's normalization, targets, own "
        f"sources and status into {PLACE.pronunciation}, the place its code derives, "
        f"and the schema version, control boundary, acceptance and shared sources into "
        f"[pronunciation] in {DECLARATION}",
    ),
    Withdrawn("part", "language", "remove it: the folder's code states the edition's language"),
    Withdrawn(
        "part",
        "occurrence_plan",
        "remove it: the readings check derives the occurrence plan under build/",
    ),
    Withdrawn(
        "review",
        "readings",
        f"remove it and move each edition's analyst readings to {PLACE.readings}, the "
        "place its code derives",
    ),
    Withdrawn(
        "edition",
        "sources",
        f"remove it and move the edition's files to {PLACE.folder}/, the folder its code derives",
    ),
    Withdrawn(
        "edition",
        "cover",
        f"remove it and move the cover to {PLACE.cover}, the place the "
        "file prefix and the edition's code derive",
    ),
)


def keys(kind: str) -> dict[str, str]:
    """The keys a kind of place may no longer declare, each with what to do instead."""
    return {entry.key: entry.instead for entry in WITHDRAWN if entry.kind == kind}
