"""The browser that draws a film's pictures, as a record names it.

The engine pins one browser build, which the supply task installs and whose executable it
checks by SHA-256 (`filmkit.picture.rendering.BROWSER`), and each release qualifies that build:
two renders of one stage show the same under software capture (`filmkit.picture.qualification`).
A film may name another browser in `FILM_CHROMIUM_PATH`. A record that rests on which browser
drew a picture therefore states the browser that ran, read when it runs, and never the engine's
constants: every render receipt and the qualification record carry `identity`.
"""

from __future__ import annotations

import filmkit.picture.rendering as rendering
import filmkit.repository as repository


def identity() -> dict:
    """The browser a render runs now: its executable, the executable's SHA-256 and, when those
    are the pinned build's bytes, that build's name. Where no executable stands, both are None."""
    executable = rendering.browser_path()
    digest = repository.sha(executable) if executable.is_file() else None
    product, version = rendering.BROWSER
    pinned = f"{product}@{version}" if digest == rendering.BROWSER_SHA256 else None
    place = repository.relative(executable)
    return {"executable": place, "sha256": digest, "pinned_build": pinned}


def unqualified(receipt: dict) -> str | None:
    """Why a render's receipt does not show that the pinned build drew its picture, or None when
    it names that build."""
    drawn = receipt.get("browser")
    product, version = rendering.BROWSER
    if not isinstance(drawn, dict):
        return "its receipt names no browser"
    if drawn.get("sha256") != rendering.BROWSER_SHA256:
        return (
            f"it was drawn by another browser than the build the engine pins, {product}@{version} "
            f"({drawn.get('executable')})"
        )
    return None
