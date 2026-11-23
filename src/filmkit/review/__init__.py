"""Measure the editions and run an independent review round.

A review tool that refuses its inputs raises `ReviewError`, which each command reports as
its refusal.
"""

# The field of a review prompt's template that each edition's prompt fills with that edition's own
# runtime (`filmkit.review.prompts`), which a film's adoption reads (`filmkit.adoption`).
RUNTIME_FIELD = "duration"


class ReviewError(ValueError):
    """A review input or record differs from what the review tools require."""
