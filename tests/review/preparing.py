"""What the tests of a review round's preparation share: the round they prepare, the command
as they run it and its refusal, a round's entries and files, and the stand-in for the player check.

The fixtures that use it import it when they are asked for (`conftest.py`: `ready`).
"""

import json

import pytest

import filmkit.repository as repository
import filmkit.review.files as review_files
import filmkit.review.round as review_round
from filmkit.production import CODES

# The round the preparation tests prepare, and its number.
ROUND = 19
PREPARED = "build/evidence/reviews/round-19"
# What the stand-in for the register check reports: a film whose words hold nothing to report.
REGISTER_REPORT = {"vale": "0.0.0", "places": 0, "warnings": [], "excused": []}


def names(folder):
    """The names of a round's entries, sorted."""
    return sorted(path.name for path in folder.iterdir())


def tree(folder):
    """Every file below a round's directory with its bytes."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def prepare(*options):
    """Run `prepare` for round 19 and return the round's directory."""
    review_round.run(["prepare", "--round", str(ROUND), *map(str, options)])
    return review_files.round_directory(ROUND)


def refusal(*options):
    """The one line with which `prepare` refuses round 19."""
    with pytest.raises(SystemExit) as stopped:
        prepare(*options)
    assert "\n" not in str(stopped.value)
    return str(stopped.value)


def passing_players(binding, receipt, name="player-{code}.png"):
    """Stand in for the player check: every page passes, and one screenshot a player lies beside
    the receipt, which lists it, as the check writes them; `name` is the name the check gives
    a player's screenshot."""
    shots = [receipt.with_name(name.format(code=code)) for code in CODES]
    for shot in shots:
        shot.write_text(f"{shot.name}\n")
    pages = [
        {"page": page, "verdict": "pass", "problems": []}
        for page in ("index.html", "zh/index.html", "en/index.html")
    ]
    named = [{"path": str(shot), "sha256": repository.sha(shot)} for shot in shots]
    receipt.write_text(json.dumps({"pass": True, "pages": pages, "screenshots": named}))
    return 0
