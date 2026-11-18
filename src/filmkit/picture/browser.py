"""The browser that the picture's and the players' checks run. No render runs a browser.

The cover, the geometry check, the whole-turn gate and the players' checks paint the staged
document in the browser build the supply task installs (`filmkit.supply`), or in the one
FILM_CHROMIUM_PATH names (`filmkit.tools`). A film's frames are drawn by the engine's renderer,
a native canvas (`filmkit.picture.renderer`).
"""

from __future__ import annotations

import os
from pathlib import Path

import filmkit.repository as repository

# The tools and models the supply task installs, below the repository root.
TOOL_CACHE = Path("build/runtime/tool-cache")
# The browser build as the supply task installs it, and the SHA-256 of its executable.
BROWSER = ("chrome-headless-shell", "152.0.7977.30")
BROWSER_EXECUTABLE = "chrome-headless-shell-mac-arm64/chrome-headless-shell"
BROWSER_SHA256 = "ed7c5c6aff7cc4dd88ee7746c0df97f08a454180b62b7063fc961ba42e10b6a1"


def supplied_browser() -> Path:
    """The executable of the browser build that the supply task installs."""
    product, version = BROWSER
    browsers = repository.ROOT / TOOL_CACHE / "browsers"
    return browsers / product / f"mac_arm-{version}" / BROWSER_EXECUTABLE


def browser_path() -> Path:
    """The browser the checks run: FILM_CHROMIUM_PATH, or the supplied build."""
    named = os.environ.get("FILM_CHROMIUM_PATH")
    return Path(named) if named else supplied_browser()
