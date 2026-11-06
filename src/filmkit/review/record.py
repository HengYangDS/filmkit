"""The production review record: its schema, scored dimensions, mean and thresholds.

`filmkit.review.round` writes each edition's record from a finished review round, and
`filmkit.delivery.verification` accepts it; both read these definitions. The film declares
its scored dimensions and floors. The record lives at `Edition.production_review`.

A film that declares review levels, 信, 达 and 雅 (`[review.levels]`), is accepted level by
level: every level has a verdict, and passes only when every dimension it holds meets the floor
and no material finding remains in it; every finding names its level, and every sentence of the
edition (`filmkit.review.sentences`) has a verdict, `ok` or the ids of the findings that concern
it. A film without levels keeps the overall and dimension floors alone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.review.sentences import sentences

if TYPE_CHECKING:
    from filmkit.production import Edition

SCHEMA_VERSION = 2
# The scored dimensions in record order, with what each one asks reviewers to judge.
DIMENSIONS = dict(FILM.review.dimensions)
# The verifier's floor: the overall score and every dimension at least this.
OVERALL_MINIMUM = FILM.review.overall_minimum
DIMENSION_MINIMUM = FILM.review.dimension_minimum
# The levels the review passes one by one, or None for a film that declares none.
LEVELS = FILM.review.levels
VERDICTS = ("pass", "fail")


def overall(scores: dict[str, float]) -> float:
    """The record's overall score: the mean of its dimension scores to one decimal."""
    return round(sum(scores.values()) / len(scores), 1)


def level_problems(entry: dict, scores: dict[str, float], findings: list[dict]) -> list[str]:
    """Why a review's levels do not pass, or nothing for a film without levels.

    Every level has a verdict, pass or fail, with the ids of its findings; a level fails, or
    passes while a dimension it holds is below the floor or a material finding is among its own.
    Every finding names a level and stands among that level's findings.
    """
    if LEVELS is None:
        return []
    verdicts = entry.get("levels") or {}
    problems = []
    for name, level in LEVELS.items():
        verdict = verdicts.get(name)
        if not isinstance(verdict, dict) or verdict.get("verdict") not in VERDICTS:
            problems.append(f"no verdict for level {name}")
            continue
        if verdict["verdict"] == "fail":
            problems.append(f"{name} fails")
            continue
        problems += [
            f"{name} passes with {dimension} at {scores[dimension]:g}, below the floor of "
            f"{DIMENSION_MINIMUM}"
            for dimension in level.dimensions
            if scores.get(dimension, DIMENSION_MINIMUM) < DIMENSION_MINIMUM
        ]
        held = set(verdict.get("findings") or ())
        problems += [
            f"{name} passes with material finding {finding['id']}"
            for finding in findings
            if finding.get("severity") == "material" and finding.get("id") in held
        ]
    for finding in findings:
        level = finding.get("level")
        if level not in LEVELS:
            problems.append(f"finding {finding.get('id')} names no level")
        elif finding.get("id") not in (verdicts.get(level) or {}).get("findings", ()):
            problems.append(
                f"finding {finding.get('id')} is not among the findings of level {level}"
            )
    return problems


def sentence_ids(edition: Edition) -> list[str]:
    """The ids of the edition's sentences, from its current timeline."""
    return [row["id"] for row in sentences(repository.read(edition.timeline), edition.code)]


def sentence_problems(entry: dict, findings: list[dict], edition: Edition) -> list[str]:
    """Why a review's sentence verdicts are incomplete, or nothing for a film without levels.

    Every sentence of the edition has a verdict, `ok` or a list of the ids of the review's
    findings that concern it, and no verdict names a sentence the edition does not hold.
    """
    if LEVELS is None:
        return []
    judged = entry.get("sentences") or {}
    expected = sentence_ids(edition)
    held = {finding.get("id") for finding in findings}
    problems = [f"no verdict for sentence {name}" for name in expected if name not in judged]
    problems += [
        f"no sentence {name} in the {edition.code} edition"
        for name in judged
        if name not in expected
    ]
    for name, verdict in judged.items():
        if name not in expected or verdict == "ok":
            continue
        if (
            not isinstance(verdict, list)
            or not verdict
            or not all(isinstance(v, str) for v in verdict)
        ):
            problems.append(f"sentence {name} is neither ok nor a list of finding ids")
            continue
        problems += [
            f"sentence {name} names finding {item}, which the review does not hold"
            for item in verdict
            if item not in held
        ]
    return problems
