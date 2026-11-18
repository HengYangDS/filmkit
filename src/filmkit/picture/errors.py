"""The refusal every part of the picture raises, in a module that imports none of them."""

from __future__ import annotations


class PictureError(ValueError):
    """A stage, render or receipt differs from what the picture's contract requires."""
