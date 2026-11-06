"""Derive the pronunciation listening plan of both editions.

The plan lists every dictionary target occurrence of the scripts' pronunciation contract
and every English heteronym of the film's readings with the part of speech its clause gives
it, so a reviewer and the later human listening check each one in context. A heteronym
occurrence takes the part of speech the film's readings record for it, or the derivation
refuses, so an edit that moves or adds one is re-read before the next review. A refusal
raises `ReviewError`, which the command reports.

For each assembled edition the plan also names the moments of its soundtrack a person should
hear, bound to its timeline and soundtrack: the unmarked pauses from 0.15 s up to their limits
and those the film keeps by an exception, the largest rate, pitch and level steps between
adjacent thoughts (`filmkit.narration.flow`), and each declared Latin-script term's
occurrences with their first vowels (`filmkit.narration.terms`).

Usage: python -m filmkit.review.listening_plan --out <file>
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field

import filmkit.narration.flow as narration_flow
import filmkit.narration.terms as narration_terms
import filmkit.repository as repository
import filmkit.sources as sources
from filmkit.film import FILM, Declared
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

if TYPE_CHECKING:
    from collections.abc import Iterator

BASIS = (
    "Analyst-stated CMU-convention reading; not read from the pinned dictionary; listening confirms"
)
MANDARIN_BASIS = (
    "Analyst-stated Hanyu Pinyin reading in context; not read from the pinned "
    "dictionary; listening confirms"
)
READING = "See target dictionary reading and admissible lexical-stress variants"
PLAN_AUTHORITY = (
    "Derived review aid; the contract and the recordings remain the owners. Listening decides."
)


def arpabet(phones: str, primary: int, secondary=(), weak=()) -> dict:
    """An analyst-stated reading in the contract's lexical-stress shape."""
    values = phones.split()
    return {
        "arpabet": values,
        "syllable_count": sum(phone[-1].isdigit() for phone in values),
        "primary_syllable": primary,
        "secondary_syllables": list(secondary),
        "weak_syllables": list(weak),
        "basis": BASIS,
    }


class Reading(Declared):
    """An analyst-stated reading: its ARPAbet phones and its stressed and weak syllables."""

    phones: str = Field(min_length=1)
    primary: int
    secondary: tuple[int, ...] = ()
    weak: tuple[int, ...] = ()

    def stress(self) -> dict:
        """The reading in the contract's lexical-stress shape."""
        return arpabet(self.phones, self.primary, self.secondary, self.weak)


class Readings(Declared):
    """The film's analyst readings for its listening plan.

    `mandarin` holds Chinese words whose reading depends on context and that the contract's
    targets do not cover, each with the reading its sentence gives it; `heteronyms` holds
    the English heteronyms with a reading for each part of speech or tense; `variants` holds
    the variants that the dictionary-sourced homograph targets lack; `grammar` holds the
    part of speech of each heteronym occurrence, keyed by "<segment>:<offset>" in the
    English segment text. A script edit that moves or adds an occurrence makes the plan
    refuse until its entry is recorded again.
    """

    mandarin: dict[str, str] = {}
    heteronyms: dict[str, dict[str, Reading]] = {}
    variants: dict[str, dict[str, Reading]] = {}
    grammar: dict[str, dict[str, str]] = {}


def film_readings() -> Readings:
    """The analyst readings the film declares, or none when it declares no readings file."""
    if FILM.review.readings is None:
        return Readings()
    return Readings.model_validate_json((repository.ROOT / FILM.review.readings).read_bytes())


def occurrences(term: str, text: str, code: str) -> Iterator[tuple[int, int]]:
    """Spans of a term in a segment's text: substrings in Chinese, words in English."""
    if code == "zh":
        start = text.find(term)
        while start >= 0:
            yield start, start + len(term)
            start = text.find(term, start + 1)
        return
    flags = 0 if term.isupper() else re.IGNORECASE
    for match in re.finditer(rf"\b{re.escape(term)}\b", text, flags):
        yield match.start(), match.end()


def analyst_contract(contract: dict, readings: Readings) -> dict:
    """The pronunciation contract with the film's analyst-stated readings and variants."""
    chinese = contract["languages"]["Chinese"]
    if not any(source["id"] == "analyst-mandarin" for source in contract["sources"]):
        contract["sources"].append({"id": "analyst-mandarin", "qualification": MANDARIN_BASIS})
    known = {target["term"] for target in chinese["targets"]}
    for term, reading in readings.mandarin.items():
        if term not in known:
            chinese["targets"].append(
                {
                    "term": term,
                    "kind": "contextual-mandarin-word",
                    "target_reading": reading,
                    "source": "analyst-mandarin",
                    "status": "planned-not-listened",
                }
            )
    english = contract["languages"]["English"]
    known = {target["term"] for target in english["targets"]}
    if not any(source["id"] == "analyst-inference" for source in contract["sources"]):
        contract["sources"].append({"id": "analyst-inference", "qualification": BASIS})
    for term, variants in readings.heteronyms.items():
        if term not in known:
            english["targets"].append(
                {
                    "term": term,
                    "kind": "contextual-homograph",
                    "lexical_stress": {
                        part: reading.stress() for part, reading in variants.items()
                    },
                    "source": "analyst-inference",
                }
            )
    # A variant the target already holds keeps its own source; only an added one is the
    # analyst's inference.
    for target in english["targets"]:
        for variant, reading in readings.variants.get(target["term"], {}).items():
            if variant not in target["lexical_stress"]:
                target["lexical_stress"][variant] = reading.stress()
                target["variant_sources"] = {
                    **target.get("variant_sources", {}),
                    variant: "analyst-inference",
                }
    return contract


def target_entries(
    code: str, target: dict, segments: list[dict], grammar: dict[str, dict[str, str]]
) -> list[dict]:
    """Every occurrence of one pronunciation target in a script, with its clause.

    A heteronym's lexical stress maps each part of speech to a reading; an occurrence
    takes the reading of the part of speech that `grammar` records for it, or is refused.
    """
    term, stress = target["term"], target.get("lexical_stress", {})
    heteronym = (
        isinstance(stress, dict)
        and bool(stress)
        and "arpabet" not in stress
        and "basis" not in stress
    )
    entries = []
    for segment in segments:
        text, offset, groups = segment["text"], 0, []
        for group in segment["utterance_groups"]:
            groups.append((offset, offset + len(group), group))
            offset += len(group)
        for start, end in occurrences(term, text, code):
            clause = next((group for a, b, group in groups if a <= start < b), None)
            if clause is None:
                msg = f"{segment['id']}: {term} at {start} lies outside every thought"
                raise ReviewError(msg)
            entry = {
                "locale": code,
                "section": segment["id"],
                "display_span": [start, end],
                "display_word": text[start:end],
                "target_owner_term": term,
                "grammar": target["kind"],
                "clause": clause,
            }
            if code == "zh":
                entry |= {
                    "target_reading": target["target_reading"],
                    "target_stress": {},
                }
            else:
                reading = stress
                if heteronym:
                    key = f"{segment['id']}:{start}"
                    entry["grammar"] = grammar.get(term, {}).get(key)
                    if entry["grammar"] not in stress:
                        msg = f"{term} at {key}: record its part of speech before rebinding"
                        raise ReviewError(msg)
                    reading = stress[entry["grammar"]]
                entry |= {"target_reading": READING, "target_stress": reading}
            entries.append(entry | {"waveform": None, "status": "planned-not-listened"})
    return entries


def heard_moments(edition: Edition) -> dict:
    """The moments of an edition's assembled soundtrack a person should hear, bound to it."""
    if not (edition.timeline.is_file() and edition.soundtrack.is_file()):
        return {"status": "not-assembled"}
    timeline = repository.read(edition.timeline)
    narrated = narration_flow.soundtrack(edition.soundtrack, timeline)
    return {
        "status": "planned-not-listened",
        **{
            name: {"path": repository.relative(path), "sha256": repository.sha(path)}
            for name, path in (("timeline", edition.timeline), ("soundtrack", edition.soundtrack))
        },
        **narration_flow.listening(edition.code, narrated, FILM.narration.flow),
        "narration_terms": narration_terms.records(edition.code, FILM.narration.terms, narrated),
    }


def listening_plan(out: Path) -> dict:
    """Derive the pronunciation listening plan from the contract and current scripts.

    Both editions' scripts name one pronunciation contract, which stays unchanged: its
    hash is part of every recording's fingerprint, and the narrator consumes only its
    normalization. The derived, planned-not-listened plan for the human listener lists
    every dictionary-sourced target, the context-dependent Chinese readings the targets
    do not cover, the film's English heteronyms with analyst-stated CMU-convention
    readings, and each occurrence in the current spoken text with its clause and, for a
    heteronym, the part of speech the film's readings record for that clause, bound to
    the current script, cast and reference hashes. An occurrence without a recorded part
    of speech, or a recorded one that names no current occurrence, is refused, so a script
    edit cannot silently inherit a stale reading.
    """
    scripts = {code: repository.read(Edition(code).script) for code in CODES}
    named = {script.get("pronunciation_contract") for script in scripts.values()}
    if len(named) != 1 or None in named:
        names = sorted(map(str, named))
        msg = f"the editions' scripts name different pronunciation contracts: {names}"
        raise ReviewError(msg)
    contract_file = named.pop()
    contract_path = repository.ROOT / contract_file
    manifest = repository.ROOT / sources.MANIFEST
    readings = film_readings()
    contract = analyst_contract(repository.read(contract_path)["pronunciation"], readings)
    entries, bindings = [], []
    for code in CODES:
        edition = Edition(code)
        language, script_path, cast_path = edition.language, edition.script, edition.cast
        script, cast = scripts[code], repository.read(cast_path)
        bindings.append(
            {
                "locale": code,
                "path": script_path,
                "sha256": repository.sha(script_path),
                "source_manifest": {
                    "path": sources.MANIFEST,
                    "sha256": repository.sha(manifest),
                },
                "cast": {"path": cast_path, "sha256": repository.sha(cast_path)},
                "selected_reference": {
                    "path": cast["reference_audio"],
                    "sha256": cast["reference_sha256"],
                    "transcript_sha256": cast["reference_text_sha256"],
                },
                "status": "planned-not-listened",
            }
        )
        for target in contract["languages"][language]["targets"]:
            entries += target_entries(code, target, script["segments"], readings.grammar)
    current = {
        (entry["target_owner_term"], f"{entry['section']}:{entry['display_span'][0]}")
        for entry in entries
        if entry["locale"] == "en"
    }
    stale = {
        term: sorted(key for key in keys if (term, key) not in current)
        for term, keys in readings.grammar.items()
    }
    stale = {term: keys for term, keys in stale.items() if keys}
    if stale:
        msg = f"recorded parts of speech name no current occurrence: {stale}"
        raise ReviewError(msg)
    repository.write(
        out,
        {
            "status": "planned-not-listened",
            "derived_from": {"path": contract_file, "sha256": repository.sha(contract_path)},
            "authority": PLAN_AUTHORITY,
            "sources": contract["sources"],
            "control_boundary": contract["control_boundary"],
            "acceptance": contract["acceptance"],
            "languages": contract["languages"],
            "script_bindings": bindings,
            "occurrence_plan": {"count": len(entries), "entries": entries},
            "heard_moments": {code: heard_moments(Edition(code)) for code in CODES},
        },
    )
    return {
        "output": repository.relative(out),
        "occurrences": {code: sum(entry["locale"] == code for entry in entries) for code in CODES},
        "english_targets": len(contract["languages"]["English"]["targets"]),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True, metavar="FILE")
    options = parser.parse_args(argv)
    try:
        result = listening_plan(options.out.resolve())
    except ReviewError as error:
        msg = f"listening plan: {error}"
        raise SystemExit(msg) from None
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
