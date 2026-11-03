"""The cast's retakes: the seeds that narrate each segment and thought, bound to exact text.

A segment's retake may declare its seed and temperature. A thought's retake is an entry
`{"seed", "text_sha256", "spoken_sha256"}` under its segment's "groups", keyed by the thought's
1-based index, and may add the "run_on" that its take reads on into and is cut from (see
run_on). It binds while the thought's text and spoken text have those SHA-256: an audition binds
it to the text and the speech it narrated, synthesis refuses it for any other text or speech, and
a script edit moves it with its exact text to the thought's new index or releases it. An entry
bound before filmkit 0.6.0 records no spoken text and binds by its text alone.
"""

from __future__ import annotations

import copy
import re

import filmkit.repository as repository
from filmkit.narration.pronunciation import pronunciation_text
from filmkit.narration.run_on import valid_run_on

# A segment's seed is the cast's full-narration seed plus the segment number.
DEFAULT_SEED = 227
DEFAULT_TEMPERATURE = 0.46
# The keys every thought retake holds, and those it may add.
ENTRY_KEYS = {"seed", "text_sha256"}
OPTIONAL_KEYS = {"spoken_sha256", "run_on"}


def retake_entry(
    seed: int, text: str, run_on: dict | None = None, *, spoken_text: str | None = None
) -> dict:
    """A thought's retake: its seed, bound to its text and auditioned speech, and any run-on."""
    entry = {"seed": seed, "text_sha256": repository.content_sha(text)}
    if spoken_text is not None:
        entry["spoken_sha256"] = repository.content_sha(spoken_text)
    return entry if run_on is None else {**entry, "run_on": dict(run_on)}


def apply_retakes(plans: list[dict], takes: dict, seed: int, segment: str = "") -> list[dict]:
    """Apply declared per-thought retake seeds and run-ons, each bound to its exact text.

    A retake that records the spoken text it was auditioned on also binds that speech; the
    segment names the refused thought.
    """
    if not takes:
        return plans
    if not isinstance(takes, dict) or len(plans) < 2:
        msg = "Group retakes require authored utterance groups"
        raise ValueError(msg)
    plans = [dict(plan) for plan in plans]
    for key, take in takes.items():
        if not re.fullmatch(r"[1-9][0-9]*", key) or int(key) > len(plans):
            msg = "Group retake index differs"
            raise ValueError(msg)
        plan = plans[int(key) - 1]
        if (
            not isinstance(take, dict)
            or not ENTRY_KEYS <= set(take) <= ENTRY_KEYS | OPTIONAL_KEYS
            or type(take["seed"]) is not int
            or take["seed"] == seed
            or take["text_sha256"] != repository.content_sha(plan["text"])
            or ("run_on" in take and not valid_run_on(take["run_on"]))
        ):
            msg = "Group retake differs from its declared thought"
            raise ValueError(msg)
        if "spoken_sha256" in take and take["spoken_sha256"] != repository.content_sha(
            plan["spoken_text"]
        ):
            msg = (
                f"{segment}.{key}: the retake was auditioned on other spoken text; "
                "audition the thought again"
            )
            raise ValueError(msg)
        plan["seed"] = take["seed"]
        if "run_on" in take:
            plan["run_on"] = dict(take["run_on"])
    return plans


def segment_take(segment: dict, cast: dict, thoughts: list[dict]) -> tuple[int, float, list[dict]]:
    """The seed and temperature that narrate a segment, and its thoughts with retake seeds.

    The segment's retake may declare its seed and temperature; otherwise the cast's
    full-narration seed plus the segment number and the cast's temperature apply.
    """
    retake = cast.get("retakes", {}).get(segment["id"], {})
    seed = retake.get("seed", cast.get("full_narration_seed", DEFAULT_SEED) + int(segment["id"]))
    temperature = retake.get(
        "temperature", cast.get("full_narration_temperature", DEFAULT_TEMPERATURE)
    )
    return seed, temperature, apply_retakes(thoughts, retake.get("groups", {}), seed, segment["id"])


def thought_text(script: dict, segment: str, index: int) -> str | None:
    """The current text of a segment's thought (1-based), or None if it has none."""
    for item in script["segments"]:
        if item["id"] == segment:
            groups = item.get("utterance_groups", [])
            return groups[index - 1] if 1 <= index <= len(groups) else None
    return None


def bind_proposals(
    script: dict, cast: dict, rows: list[dict], contract: dict
) -> tuple[dict, list[str], list[str]]:
    """Bind each proposed seed and its run-on into the cast's thought retakes, refusing stale text.

    Each proposal must record the spoken text its audition narrated, and that text must be the
    one the edition's pronunciation contract derives from the thought's current text.

    Returns:
        The cast with the bound retakes, the bound "segment.index=seed" entries and the
        thoughts without a proposal.
    """
    cast = copy.deepcopy(cast)
    retakes = cast.setdefault("retakes", {})
    bound, skipped = [], []
    for row in rows:
        key = f"{row['segment']}.{row['index']}"
        if row["proposed_seed"] is None:
            skipped.append(key)
            continue
        if thought_text(script, row["segment"], row["index"]) != row["text"]:
            msg = f"{key}: the auditioned text is not the current thought"
            raise ValueError(msg)
        if row.get("spoken_text") != pronunciation_text({"text": row["text"]}, contract):
            msg = f"{key}: the auditioned speech is not the current thought's spoken text"
            raise ValueError(msg)
        groups = retakes.setdefault(row["segment"], {}).setdefault("groups", {})
        groups[str(row["index"])] = retake_entry(
            row["proposed_seed"],
            row["text"],
            row.get("proposed_run_on"),
            spoken_text=row["spoken_text"],
        )
        bound.append(f"{key}={row['proposed_seed']}")
    return cast, bound, skipped


def rebind(bound: dict, thoughts: list[str]) -> tuple[dict, list[str]]:
    """Move each bound retake to the one thought that still has its text, or release it.

    Returns:
        The moved retakes by their new index, in index order, and the released indices.
    """
    moved, released = {}, []
    for index, take in bound.items():
        matches = [
            place
            for place, text in enumerate(thoughts, 1)
            if repository.content_sha(text) == take["text_sha256"]
        ]
        if len(matches) == 1:
            moved[str(matches[0])] = take
        else:
            released.append(index)
    return dict(sorted(moved.items(), key=lambda item: int(item[0]))), released
