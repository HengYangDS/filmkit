"""Write each edition's independent reviewer prompt for one review round.

The film declares the prompt as a `str.format` template (`review.prompt`), which each round fills
for each edition with the exact packaged films and their SHA-256, the round's own inputs, the
canonical source, the concept contract and the reading occurrence plans, the delivery format, the
pause, level and clarity policies the film declares, and the previous round's review. A film that
declares a concept contract gets prompts only when its template cites the contract and the
reading occurrence plans and its dimensions score concept fidelity.

`{previous_review}` states the previous round's review, its findings and that each repair is to
be verified, or, for a film's first production review, that no earlier production review exists;
it cites no previous review then. A template may instead cite `{previous}` and `{findings}`
itself, and is then filled only from a previous round.
"""

from __future__ import annotations

import string
from pathlib import Path

import filmkit.repository as repository
import filmkit.sources as sources
import filmkit.specification as specification
from filmkit.film import FILM
from filmkit.narration.readings import plan_path
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError
from filmkit.review.files import cited, edition_review, present
from filmkit.review.record import DIMENSIONS

# The round's own inputs that each reviewer prompt names.
ROUND_INPUTS = (
    "pronunciation-listening-plan.json",
    "measurements.json",
    "player-check-artifacts.json",
)
# The reviewer prompt, filled per edition: the str.format template the film declares.
TEMPLATE = (repository.ROOT / FILM.review.prompt).read_text(encoding="utf-8")
# How the prompt names an optional field that the film or a script does not declare.
NOT_DECLARED = "none declared"
# The dimension that scores a declared concept contract, and the prompt fields that cite it
# and the reading occurrence plans.
CONCEPT_DIMENSION = "concept_fidelity"
CONTRACT_FIELDS = ("concepts", "readings")
# The fields that cite the previous round's review itself, which a first round cannot fill.
PREVIOUS_FIELDS = ("previous", "findings")
FIRST_ROUND = (
    "This is the first production review of these films; no earlier production review "
    "exists. Judge everything independently."
)


def template_fields(template: str) -> set[str]:
    """The names of the fields a template cites."""
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


def contract_gaps(template: str, dimensions: dict[str, str]) -> list[str]:
    """What a film's review configuration leaves out of the concept contract it declares.

    A film that declares a contract cites it and the reading occurrence plans in its prompt
    template and scores concept fidelity; a film without one owes neither.
    """
    if not FILM.concepts:
        return []
    fields = template_fields(template)
    gaps = [
        f"{FILM.review.prompt} never cites {{{name}}}"
        for name in CONTRACT_FIELDS
        if name not in fields
    ]
    if CONCEPT_DIMENSION not in dimensions:
        gaps.append(f"review.dimensions has no {CONCEPT_DIMENSION}")
    return gaps


def declared_seconds(policy: dict, key: str) -> str:
    """A script's declared duration, or "none declared" for an optional one it omits."""
    value = policy.get(key)
    return NOT_DECLARED if value is None else f"{value:.2f} s"


def inner_caps(policy: dict) -> str:
    marks = policy.get("inner_pause_caps_seconds") or {}
    names = {",": "commas", "，": "commas", "、": "enumeration commas"}
    extra = ", ".join(f"{value:.2f} s at {names.get(mark, mark)}" for mark, value in marks.items())
    cap = declared_seconds(policy, "inner_pause_cap_seconds")
    return f"{cap} ({extra})" if extra else cap


def inner_floors(policy: dict) -> str:
    floors = policy.get("inner_pause_floors_seconds")
    if not floors:
        return NOT_DECLARED
    return ", ".join(f"{marks} {value:.3g} s" for marks, value in floors.items())


def inner_breath(policy: dict) -> str:
    breath = policy.get("inner_breath")
    if not breath:
        return NOT_DECLARED
    seconds, pause = breath["longest_group_seconds"], breath["pause_seconds"]
    return f"{seconds:g} s with a {pause:g} s pause"


def boundary(policy: dict) -> str:
    """A script's declared thought boundary ratio and the margin each floored boundary adds."""
    if policy.get("thought_boundary_ratio") is None:
        return NOT_DECLARED
    margin = policy.get("thought_boundary_margin_seconds", 0)
    return f"{policy['thought_boundary_ratio']} and {margin:.2f} s"


def clarity_floors() -> str:
    """The voice-clarity floors the film declares, in dB for each edition."""
    floors = FILM.review.clarity_minimum_db
    if not floors:
        return NOT_DECLARED
    return f"{floors['zh']:g} dB Chinese, {floors['en']:g} dB English"


def finding_index(findings: list[dict]) -> str:
    """Finding identifiers grouped by severity, in order of first appearance."""
    groups: dict[str, list[str]] = {}
    for finding in findings:
        groups.setdefault(finding["severity"], []).append(finding["id"])
    return "; ".join(f"{severity} {', '.join(ids)}" for severity, ids in groups.items())


def previous_review(previous: Path | None, code: str, findings: str) -> str:
    """The sentence that cites the previous round's review, or states that a round is the first."""
    if previous is None:
        return FIRST_ROUND
    return (
        f"The previous review is in {cited(previous)}/{code}-review.md and "
        f"{cited(previous)}/review-{code}.json ({findings}). Verify on these media whether each "
        "repair landed, and judge everything independently."
    )


def prompt_context(out_dir: Path, previous: Path | None, changes: Path | None) -> dict:
    """The template fields both editions' prompts share.

    They name the canonical source, the film's concept contract and the readings' occurrence
    plans, the round's places, the delivery format and the pause, level and clarity policies the
    current scripts, assemblies and declaration hold; the previous round's directory only when
    there is one.
    """
    zh, en = (repository.read(Edition(code).script)["voice_performance"] for code in CODES)
    manifest = sources.manifest()
    assemblies = [repository.read(Edition(code).audio_assembly) for code in CODES]
    levels = {item["program_level"]["policy"]["integrated_lufs"] for item in assemblies}
    if len(levels) != 1:
        msg = f"the soundtracks declare different program levels: {sorted(levels)}"
        raise ReviewError(msg)
    return {
        "root": repository.ROOT,
        "source": sources.location(),
        "documents": ", ".join(Path(member["path"]).stem for member in manifest["members"]),
        "concepts": cited(repository.ROOT / FILM.concepts) if FILM.concepts else NOT_DECLARED,
        "readings": " and ".join(cited(repository.ROOT / plan_path(code)) for code in CODES),
        "out": cited(out_dir),
        **({} if previous is None else {"previous": cited(previous)}),
        "changes": "" if changes is None else changes.read_text().strip() + "\n",
        "duration": specification.DURATION,
        "fps": specification.FPS,
        "rate": f"{specification.RATE / 1000:g}",
        "program": f"{levels.pop():g}",
        "caps": f"{inner_caps(zh)} Chinese; {inner_caps(en)} English",
        "floors": f"Chinese {inner_floors(zh)}; English {inner_floors(en)}",
        "breath": f"Chinese {inner_breath(zh)}; English {inner_breath(en)}",
        "tolerances": f"{zh['thought_level_tolerance_db']} dB Chinese, "
        f"{en['thought_level_tolerance_db']} dB English",
        "ratios": f"{boundary(zh)} Chinese, {boundary(en)} English",
        "codas": f"{declared_seconds(zh, 'coda_thought_pause_seconds')} Chinese, "
        f"{declared_seconds(en, 'coda_thought_pause_seconds')} English",
        "clarity": clarity_floors(),
        "dimensions": "\n".join(
            f"{index}. {name}: {text}" for index, (name, text) in enumerate(DIMENSIONS.items(), 1)
        ),
    }


def previous_context(previous: Path | None, code: str) -> dict:
    """An edition's fields from the previous round: its review, findings and working files.

    A first round has no previous review, so its prompt states that none exists.
    """
    if previous is None:
        return {"previous_review": FIRST_ROUND, "findings": "", "scripts": ""}
    review = present([previous / f"review-{code}.json", previous / f"{code}-review.md"])[0]
    found = edition_review(review, code)[1]["findings"]
    findings = f"findings: {finding_index(found)}" if found else "no findings"
    working = previous / code
    scripts = (
        f" The previous reviewer's working files are in {cited(working)}/; you may "
        "copy and adapt its scripts under your own output directory."
        if working.is_dir()
        else ""
    )
    return {
        "previous_review": previous_review(previous, code, findings),
        "findings": findings,
        "scripts": scripts,
    }


def prompts(previous: Path | None, out_dir: Path, changes: Path | None = None) -> dict:
    """Write each edition's independent reviewer prompt for one round.

    Each prompt names the exact packaged films with their SHA-256, the previous round's
    review and its findings, or that the round is the first, the round's own inputs and the
    policies the film declares. changes holds Markdown context bullets for this round, such
    as the repairs since the previous review and their dispositions. The previous review is
    context to verify, never a score to inherit. Nothing is written unless both editions'
    films, the previous reviews when a previous round is named and the round's inputs exist,
    a first round's template cites no previous review, and the review configuration keeps the
    concept contract the film declares (`contract_gaps`).
    """
    gaps = contract_gaps(TEMPLATE, DIMENSIONS)
    if gaps:
        msg = "the review omits the concept contract the film declares: " + "; ".join(gaps)
        raise ReviewError(msg)
    unfilled = sorted(template_fields(TEMPLATE).intersection(PREVIOUS_FIELDS))
    if previous is None and unfilled:
        cites = " and ".join(f"{{{name}}}" for name in unfilled)
        msg = (
            f"{FILM.review.prompt} cites {cites}, which only a previous round fills; a first "
            "round's template cites {previous_review}"
        )
        raise ReviewError(msg)
    present([out_dir / name for name in ROUND_INPUTS])
    context = prompt_context(out_dir, previous, changes)
    texts = {}
    for code in CODES:
        edition = Edition(code)
        other = next(name for name in CODES if name != code)
        media = "\n".join(
            f"- {film} (SHA-256 {repository.sha(film)})" for film in present(edition.films)
        )
        texts[code] = TEMPLATE.format(
            **context,
            **previous_context(previous, code),
            language=edition.language,
            code=code,
            other=other,
            other_language=Edition(other).language,
            media=media,
        )
    written = []
    for code, text in texts.items():
        path = out_dir / f"prompt-{code}.md"
        path.write_text(text)
        written.append(repository.relative(path))
    return {"prompts": written}
