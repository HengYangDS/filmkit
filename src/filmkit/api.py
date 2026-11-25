"""The engine's interface for a film's own tests and tools (design decision 16 of
build-a-film-by-its-verbs).

A film's suites import only this module and the Node test entry `TEST_ENTRY`
(`filmkit/picture/testing.mjs`); every other module of the engine may change behind them. The
names are the loaded film and its root, its editions and their places, the timeline the checks
before narration draw a picture over, the anchors a timeline of other words takes, the caption
typesetter, the composition staging reads, and the reproduction's read-only release record with
the film-bound sources that differ from it. `import filmkit` and the installed package's version
stay the package's identity.
"""

from __future__ import annotations

from pathlib import Path

import filmkit.film as _film
import filmkit.repository as _repository
from filmkit.captions.timing import typeset
from filmkit.delivery.reproduction import Release
from filmkit.delivery.reproduction import changed_sources as _changed_sources
from filmkit.delivery.reproduction import load as _load
from filmkit.narration import anchors as _anchors
from filmkit.picture.rendering import COMPOSITION_SCRIPT as _COMPOSITION
from filmkit.production import CODES as _CODES
from filmkit.production import Edition

__all__ = [
    "ROOT",
    "film",
    "editions",
    "Edition",
    "derived_timeline",
    "place_anchors",
    "typeset",
    "composition",
    "release",
    "changed_sources",
    "TEST_ENTRY",
]

# The film's root, where the engine found the film.
ROOT = _repository.ROOT
# The Node module a film's tests import: `openComposition`, `openModules`, `derivedTimeline`.
TEST_ENTRY = Path(_film.__file__).resolve().parent / "picture" / "testing.mjs"


def film() -> _film.Film:
    """The film's loaded declaration."""
    return _film.FILM


def editions() -> tuple[str, ...]:
    """The codes of the film's editions, in the order the declaration states them."""
    return _CODES


def derived_timeline(code: str) -> dict:
    """The timeline that the checks before narration draw the edition's picture over, derived
    from its script alone (`filmkit.narration.anchors.derived_timeline`)."""
    script = _repository.read(Edition(code).script)
    return _anchors.derived_timeline(script, code)


def place_anchors(timeline: dict, code: str) -> dict:
    """A timeline of other words given what the engine derives for every timeline and the
    anchors its marks take from those words (`filmkit.narration.anchors.place`); the timeline
    given is not changed."""
    placed = _film.timeline_values(timeline, _film.FILM)
    _anchors.place(placed, code)
    return placed


def composition() -> Path:
    """The composition's script that staging reads, below the film's root."""
    return ROOT / _COMPOSITION


def release() -> Release:
    """The film's release record, refused unless it records exactly what the editions publish
    (`filmkit.delivery.reproduction.load`)."""
    return _load()


def changed_sources(record: Release) -> list[str]:
    """Each film-bound source whose tracked bytes differ from those the release record states."""
    return _changed_sources(record)
