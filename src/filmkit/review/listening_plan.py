"""Derive the pronunciation listening plan of every edition.

The plan lists every target occurrence of each edition's pronunciation and every English
heteronym of its readings with the part of speech its clause gives it, so a reviewer and the
later human listening check each one in context. A heteronym occurrence takes the part of speech
the edition's readings, `content/<code>/readings.json`, record for it, or the derivation refuses,
so an edit that moves or adds one is re-read before the next review. A refusal
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

import filmkit.languages as languages
import filmkit.narration.flow as narration_flow
import filmkit.narration.terms as narration_terms
import filmkit.repository as repository
import filmkit.sources as sources
from filmkit.film import FILM, Declared
from filmkit.narration.pronunciation import PronunciationError, pronunciation
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
    "Derived review aid; the pronunciations and recordings remain the owners. Listening decides."
)


def arpabet(phones: str, primary: int, secondary=(), weak=()) -> dict:
    """An analyst-stated reading in a pronunciation's lexical-stress shape."""
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
        """The reading in a pronunciation's lexical-stress shape."""
        return arpabet(self.phones, self.primary, self.secondary, self.weak)


class Readings(Declared):
    """An edition's analyst readings for its listening plan.

    `mandarin` holds Chinese words whose reading depends on context and that its pronunciation's
    targets do not cover, each with the reading its sentence gives it; `heteronyms` holds
    the English heteronyms with a reading for each part of speech or tense; `variants` holds
    the variants that the dictionary-sourced homograph targets lack; `grammar` holds the
    part of speech of each heteronym occurrence, keyed by "<segment>:<offset>" in the
    edition's segment text. A script edit that moves or adds an occurrence makes the plan
    refuse until its entry is recorded again.
    """

    mandarin: dict[str, str] = {}
    heteronyms: dict[str, dict[str, Reading]] = {}
    variants: dict[str, dict[str, Reading]] = {}
    grammar: dict[str, dict[str, str]] = {}


def edition_readings(code: str) -> Readings:
    """The analyst readings an edition records in its folder, or none where it records none."""
    path = repository.ROOT / Edition(code).places.readings
    if not path.is_file():
        return Readings()
    return Readings.model_validate_json(path.read_bytes())


def occurrences(term: str, text: str, code: str) -> Iterator[tuple[int, int]]:
    """Spans of a term in a segment's text: substrings in a language whose words spaces do not
    delimit, as Chinese, and words in one whose words they delimit, as English."""
    if not languages.language(code).spaced:
        start = text.find(term)
        while start >= 0:
            yield start, start + len(term)
            start = text.find(term, start + 1)
        return
    flags = 0 if term.isupper() else re.IGNORECASE
    for match in re.finditer(rf"\b{re.escape(term)}\b", text, flags):
        yield match.start(), match.end()


def analyst_part(code: str, part: dict, readings: Readings) -> dict:
    """An edition's pronunciation with its analyst-stated readings and variants: the Mandarin
    readings where its language reads Han characters by their pinyin, the heteronyms and variants
    where it holds stress to CMUdict, each analyst source added to its own sources once."""
    part.setdefault("sources", [])
    part.setdefault("targets", [])
    if languages.checks(code, languages.PINYIN_READINGS):
        _add_mandarin(part, readings)
    if languages.checks(code, languages.CMUDICT_STRESS):
        _add_heteronyms(part, readings)
    return part


def _add_mandarin(part: dict, readings: Readings) -> None:
    """Add each analyst-stated Mandarin reading a part does not declare, and its source once."""
    if not any(source["id"] == "analyst-mandarin" for source in part["sources"]):
        part["sources"].append({"id": "analyst-mandarin", "qualification": MANDARIN_BASIS})
    known = {target["term"] for target in part["targets"]}
    for term, reading in readings.mandarin.items():
        if term not in known:
            part["targets"].append(
                {
                    "term": term,
                    "kind": "contextual-mandarin-word",
                    "target_reading": reading,
                    "source": "analyst-mandarin",
                    "status": "planned-not-listened",
                }
            )


def _add_heteronyms(english: dict, readings: Readings) -> None:
    """Add each analyst-stated heteronym a part does not declare and each variant of its targets,
    and their source once."""
    known = {target["term"] for target in english["targets"]}
    if not any(source["id"] == "analyst-inference" for source in english["sources"]):
        english["sources"].append({"id": "analyst-inference", "qualification": BASIS})
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
            if languages.checks(code, languages.PINYIN_READINGS):
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
    """Derive the pronunciation listening plan from each edition's pronunciation and script.

    Each edition's pronunciation stays unchanged: its hash is part of every recording of that
    edition, and the narrator consumes only its normalization. The derived, planned-not-listened
    plan for the human listener lists every target of each edition's pronunciation, the
    context-dependent Chinese readings and the English heteronyms with analyst-stated
    CMU-convention readings that the edition's readings record, and each occurrence in the
    current spoken text with its clause and, for a heteronym, the part of speech its readings
    record for that clause, bound to the current script, cast and reference hashes. An occurrence
    without a recorded part of speech, or a recorded one that names no current occurrence, is
    refused, so a script edit cannot silently inherit a stale reading.
    """
    shared = FILM.pronunciation
    manifest = repository.ROOT / sources.MANIFEST
    entries, bindings, derived, parts = [], [], [], {}
    for code in CODES:
        edition = Edition(code)
        try:
            part, digest = pronunciation(code)
        except PronunciationError as error:
            raise ReviewError(str(error)) from None
        script_path, cast_path = edition.script, edition.cast
        script, cast = repository.read(script_path), repository.read(cast_path)
        readings = edition_readings(code)
        parts[edition.language] = analyst_part(code, part, readings)
        derived.append({"path": edition.places.pronunciation, "sha256": digest})
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
                    "path": edition.places.reference,
                    "sha256": cast["reference_sha256"],
                    "transcript_sha256": repository.content_sha(cast["reference_text"]),
                },
                "status": "planned-not-listened",
            }
        )
        found = [
            entry
            for target in part["targets"]
            for entry in target_entries(code, target, script["segments"], readings.grammar)
        ]
        entries += found
        _refuse_stale(code, found, readings)
    repository.write(
        out,
        {
            "status": "planned-not-listened",
            "derived_from": derived,
            "authority": PLAN_AUTHORITY,
            "sources": [source.model_dump(exclude_defaults=True) for source in shared.sources],
            "control_boundary": shared.control_boundary,
            "acceptance": list(shared.acceptance),
            "languages": parts,
            "script_bindings": bindings,
            "occurrence_plan": {"count": len(entries), "entries": entries},
            "heard_moments": {code: heard_moments(Edition(code)) for code in CODES},
        },
    )
    return {
        "output": repository.relative(out),
        "occurrences": {code: sum(entry["locale"] == code for entry in entries) for code in CODES},
        "stress_targets": sum(
            len(parts[Edition(code).language]["targets"])
            for code in CODES
            if languages.checks(code, languages.CMUDICT_STRESS)
        ),
    }


def _refuse_stale(code: str, entries: list[dict], readings: Readings) -> None:
    """Refuse an edition's recorded part of speech that names no current heteronym occurrence."""
    current = {
        (entry["target_owner_term"], f"{entry['section']}:{entry['display_span'][0]}")
        for entry in entries
        if languages.checks(code, languages.CMUDICT_STRESS)
    }
    stale = {
        term: sorted(key for key in keys if (term, key) not in current)
        for term, keys in readings.grammar.items()
    }
    stale = {term: keys for term, keys in stale.items() if keys}
    if stale:
        msg = f"{code}: recorded parts of speech name no current occurrence: {stale}"
        raise ReviewError(msg)


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
