"""The reading of every watched Chinese character, and the spoken form of every name.

A pronunciation contract of schema version 2 declares how the narration is read wherever a
narrator could read it more than one way. The engine's watch list names the Mandarin characters
whose readings a narrator confuses, in two classes: an occurrence of a word character must lie
in a declared word of two or more characters, and one of the other class may also lie in a
declared single character. Each watched occurrence in the Chinese narration takes its reading
from the longest declared word that covers it.

pypinyin checks the declarations. A declared word's reading must divide into one dictionary
reading per character, or after a word's first character that reading in the neutral tone,
written with or without spaces.
Where the dictionary's contextual reading of an occurrence differs from the declared one, the
declaring word, which must then have two or more characters, records the reason in
`dictionary_disagreement`. A declared word the narration never says, and a reason no occurrence
needs, are refused as stale.

Every Latin word in the Chinese narration must be one of the names the Chinese contract lists in
`embedded_english_targets`, and every word of the English narration written with two or more
capitals an English target. Every language's normalization must give each Latin-script term the
film declares in `[[narration.terms]]` the term's declared spoken form, whatever the contract's
schema version, and the text of each edition that says the term must hold its declared reference
occurrence (`narration.terms`, which also measures how the recordings say it).

The check writes each edition's occurrence plan, a view derived on every check, below
build/evidence/readings/. Every failure is reported at once, and thoughts are numbered from 1
within their segment.

With --propose, the check instead writes proposed declarations for the Chinese narration: for each
watched occurrence that no declaration resolves, the dictionary's word around it, widened to two
characters for a word character, with the dictionary's contextual reading. A proposal declares
nothing; the author reads it and declares what the narration means.

Usage: python -m filmkit.narration.readings [--language zh|en | --propose]
"""

from __future__ import annotations

import argparse
import json
import re
import tomllib
import unicodedata
from pathlib import Path
from typing import NamedTuple

from pypinyin import Style, pinyin
from pypinyin.constants import PHRASES_DICT
from pypinyin.seg.mmseg import seg

import filmkit.narration.terms as terms
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.narration.pronunciation import HAN, native_utterance_plan
from filmkit.production import CODES, Edition

# The schema version whose contracts the check applies to.
SCHEMA = 2
WATCH_LIST = Path(__file__).with_name("watched-characters.toml")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:['’.-][A-Za-z0-9]+)*")
# The characters around an occurrence that a refusal quotes, on each side.
CONTEXT = 6
# The combining marks of the four Mandarin tones; a syllable without one is in the neutral tone.
TONE_MARKS = "\u0300\u0301\u0304\u030c"


class ReadingError(ValueError):
    """A watched character or a name in the narration has no declared reading."""


class Word(NamedTuple):
    """A declared word, its reading by character, and why it overrules the dictionary if it does."""

    term: str
    syllables: tuple[str, ...]
    reason: str | None


class Thought(NamedTuple):
    """One thought's spoken text, and where it stands: segment id and number from 1."""

    where: str
    text: str


def watch_list() -> dict[str, str]:
    """Each watched character and its class, "word" or "character"."""
    listed = tomllib.loads(WATCH_LIST.read_text(encoding="utf-8"))
    return {char: kind for kind in ("word", "character") for char in listed[kind]["characters"]}


def dictionary_readings(char: str) -> list[str]:
    """Every reading the dictionary gives one character."""
    return pinyin(char, style=Style.TONE, heteronym=True)[0]


def spoken_readings(char: str, *, neutral: bool) -> set[str]:
    """Each dictionary reading of a character, and with neutral, each in the neutral tone too."""
    readings = set(dictionary_readings(char))
    if not neutral:
        return readings
    return readings | {
        unicodedata.normalize(
            "NFC",
            "".join(
                mark for mark in unicodedata.normalize("NFD", reading) if mark not in TONE_MARKS
            ),
        )
        for reading in readings
    }


def syllables(term: str, reading: str) -> tuple[str, ...] | None:
    """A declared reading divided into one dictionary reading per character, or None."""
    if not re.fullmatch(f"{HAN}+", term):
        return None
    parts = reading.lower().split()
    if len(parts) > 1:
        fits = len(parts) == len(term) and all(
            part in spoken_readings(char, neutral=index > 0)
            for index, (char, part) in enumerate(zip(term, parts, strict=True))
        )
        return tuple(parts) if fits else None

    def divide(index: int, rest: str) -> tuple[str, ...] | None:
        if index == len(term):
            return () if not rest else None
        options = spoken_readings(term[index], neutral=index > 0)
        for option in sorted(options, key=len, reverse=True):
            if rest.startswith(option):
                tail = divide(index + 1, rest[len(option) :])
                if tail is not None:
                    return (option, *tail)
        return None

    return divide(0, "".join(parts))


def contextual(text: str) -> dict[int, str]:
    """The dictionary's reading of each Han character of a text in context, by position."""
    readings = {}
    for run in re.finditer(f"{HAN}+", text):
        for offset, item in enumerate(pinyin(run.group(), style=Style.TONE)):
            readings[run.start() + offset] = item[0]
    return readings


def declared_words(contract: dict) -> tuple[list[Word], list[str]]:
    """The contract's declared Chinese words, and the declarations the dictionary refuses."""
    words, failures, seen = [], [], set()
    for target in contract.get("targets", []):
        if target.get("kind") != "contextual-mandarin-word":
            continue
        term, reading, reason = (
            target["term"],
            target["target_reading"],
            target.get("dictionary_disagreement"),
        )
        divided = syllables(term, reading)
        if term in seen:
            failures.append(f"{term} is declared more than once")
        elif divided is None:
            failures.append(f"{term} {reading}: not one dictionary reading per character")
        elif reason is not None and len(term) < 2:
            failures.append(f"{term}: a single character cannot record a dictionary disagreement")
        else:
            words.append(Word(term, divided, reason))
        seen.add(term)
    return words, failures


def coverage(text: str, words: list[Word]) -> dict[int, tuple[Word, int, int]]:
    """For each position, the longest declared word covering it, its start and the offset."""
    spans = [
        (match.start(), word) for word in words for match in re.finditer(re.escape(word.term), text)
    ]
    covered: dict[int, tuple[Word, int, int]] = {}
    for start, word in sorted(spans, key=lambda span: (-len(span[1].term), span[0])):
        for offset in range(len(word.term)):
            covered.setdefault(start + offset, (word, start, offset))
    return covered


def context(text: str, position: int) -> str:
    """The text around a position, as a refusal quotes it."""
    return text[max(0, position - CONTEXT) : position + CONTEXT + 1]


def resolve(thoughts: list[Thought], words: list[Word]) -> tuple[list[dict], list[str]]:
    """Resolve each watched occurrence of the Chinese narration to its declared reading.

    Returns:
        The occurrence plan's rows and the failures, including stale declarations.
    """
    watched, rows, failures = watch_list(), [], []
    said, needed = set(), set()
    for thought in thoughts:
        covered, dictionary = coverage(thought.text, words), contextual(thought.text)
        said.update(word.term for word, _start, _offset in covered.values())
        for position, char in enumerate(thought.text):
            kind = watched.get(char)
            if kind is None:
                continue
            place = (
                f"zh {thought.where} at {position}: {char} in “{context(thought.text, position)}”"
            )
            word, start, offset = covered.get(position, (None, 0, 0))
            if word is None or (kind == "word" and len(word.term) < 2):
                failures.append(
                    f"{place} has no declared reading; the dictionary reads it "
                    f"{dictionary[position]} here"
                )
                continue
            reading, heard = word.syllables[offset], dictionary[position]
            if reading != heard:
                if word.reason is None:
                    failures.append(
                        f"{place} is declared {reading} by {word.term}, the dictionary reads "
                        f"{heard}; record why in dictionary_disagreement or declare the word"
                    )
                needed.add(word.term)
            rows.append(
                {
                    "thought": thought.where,
                    "position": position,
                    "character": char,
                    "word": word.term,
                    "word_start": start,
                    "reading": reading,
                    "dictionary": heard,
                    "class": kind,
                    "context": context(thought.text, position),
                }
            )
    failures += [
        f"{word.term} is declared but the Chinese narration never says it"
        for word in words
        if word.term not in said
    ]
    failures += [
        f"{word.term} records a dictionary disagreement that no occurrence has"
        for word in words
        if word.reason is not None and word.term not in needed
    ]
    return rows, failures


def undeclared_names(thoughts: list[Thought], declared: set[str], *, chinese: bool) -> list[str]:
    """Each name the narration says without a declared spoken form, with where it is said."""
    places: dict[str, list[str]] = {}
    for thought in thoughts:
        for match in LATIN_WORD.finditer(thought.text):
            name = match.group()
            is_name = chinese or sum(char.isupper() for char in name) >= 2
            if is_name and name not in declared:
                places.setdefault(name, []).append(thought.where)
    return [
        f"{name} has no declared spoken form; it is said in {', '.join(sorted(set(where)))}"
        for name, where in sorted(places.items())
    ]


def edition_thoughts(script: dict, contract: dict) -> list[Thought]:
    """Each thought's spoken text, in narration order."""
    return [
        Thought(f"{segment['id']}.{number}", plan["spoken_text"])
        for segment in script["segments"]
        for number, plan in enumerate(native_utterance_plan(segment, contract), 1)
    ]


def plan_path(code: str) -> str:
    """Where the readings check writes an edition's occurrence plan."""
    return f"build/evidence/readings/{code}-plan.json"


PROPOSALS = "build/evidence/readings/zh-proposals.json"


def segments(text: str) -> list[tuple[int, int]]:
    """The dictionary's words in each run of Han characters, as spans of the text."""
    spans = []
    for run in re.finditer(f"{HAN}+", text):
        start = run.start()
        for word in seg.cut(run.group()):
            spans.append((start, start + len(word)))
            start += len(word)
    return spans


def widened(text: str, position: int) -> tuple[int, int]:
    """Two characters around a word character: a dictionary phrase if one is, else the preceding."""
    han = re.compile(HAN)
    candidates = [
        (start, start + 2)
        for start, neighbour in ((position - 1, position - 1), (position, position + 1))
        if 0 <= neighbour < len(text) and han.fullmatch(text[neighbour])
    ]
    phrases = [span for span in candidates if text[span[0] : span[1]] in PHRASES_DICT]
    return (phrases or candidates or [(position, position + 1)])[0]


def proposals(thoughts: list[Thought], words: list[Word]) -> list[dict]:
    """A proposed declaration for each watched occurrence that no declared word resolves.

    Returns:
        One row per proposed word and dictionary reading, most frequent first.
    """
    watched, grouped = watch_list(), {}
    for thought in thoughts:
        covered, dictionary = coverage(thought.text, words), contextual(thought.text)
        spans = segments(thought.text)
        for position, char in enumerate(thought.text):
            kind = watched.get(char)
            word = covered.get(position, (None, 0, 0))[0]
            if kind is None or (word is not None and (kind == "character" or len(word.term) > 1)):
                continue
            start, end = next(span for span in spans if span[0] <= position < span[1])
            if kind == "word" and end - start < 2:
                start, end = widened(thought.text, position)
            term = thought.text[start:end]
            reading = " ".join(dictionary[index] for index in range(start, end))
            row = grouped.setdefault(
                (term, reading),
                {"term": term, "target_reading": reading, "occurrences": 0, "said_in": []},
            )
            row["occurrences"] += 1
            if thought.where not in row["said_in"]:
                row["said_in"].append(thought.where)
    return sorted(grouped.values(), key=lambda row: (-row["occurrences"], row["term"]))


def propose() -> dict:
    """Write the proposed declarations for the Chinese narration, whatever its schema version.

    Returns:
        The report: the contract, the proposals' path and their counts.
    """
    edition = Edition("zh")
    script = repository.read(edition.script)
    path = script["pronunciation_contract"]
    contract = repository.read(path)["pronunciation"]["languages"][edition.language]
    words, _failures = declared_words(contract)
    rows = proposals(edition_thoughts(script, contract), words)
    report = {
        "edition": "zh",
        "contract": path,
        "contract_sha256": repository.sha(path),
        "proposals": len(rows),
        "occurrences": sum(row["occurrences"] for row in rows),
        "path": PROPOSALS,
    }
    repository.write(PROPOSALS, {**report, "rows": rows})
    return report


def term_failures(code: str, script: dict, performance: dict, contract: str) -> list[str]:
    """What the contract and an edition's text leave wrong in the film's declared terms."""
    declared = FILM.narration.terms
    if not declared:
        return []
    languages = performance["languages"]
    thoughts = edition_thoughts(script, languages[Edition(code).language])
    return terms.parity_failures(declared, languages, contract) + terms.declaration_failures(
        declared, [tuple(thought) for thought in thoughts], code
    )


def check(code: str) -> dict:
    """Check one edition's readings and names, write its occurrence plan, refuse every gap.

    Returns:
        The report: the contract, its schema version and the occurrences resolved.
    """
    edition = Edition(code)
    script = repository.read(edition.script)
    path = script["pronunciation_contract"]
    performance = repository.read(path)["pronunciation"]
    declared = term_failures(code, script, performance, path)
    version = performance.get("schema_version")
    if version != SCHEMA and declared:
        raise ReadingError("\n".join(declared))
    if version != SCHEMA:
        return {
            "edition": code,
            "contract": path,
            "schema_version": version,
            "status": "not_applicable",
        }
    contract = performance["languages"][edition.language]
    thoughts = edition_thoughts(script, contract)
    if code == "zh":
        words, failures = declared_words(contract)
        rows, gaps = resolve(thoughts, words)
        names = set(contract.get("embedded_english_targets", []))
        failures += gaps + undeclared_names(thoughts, names, chinese=True)
    else:
        rows = []
        names = {target["term"] for target in contract.get("targets", [])}
        failures = undeclared_names(thoughts, names, chinese=False)
    failures += declared
    if failures:
        raise ReadingError("\n".join(failures))
    report = {
        "edition": code,
        "contract": path,
        "contract_sha256": repository.sha(path),
        "schema_version": version,
        "occurrences": len(rows),
        "plan": plan_path(code),
    }
    repository.write(plan_path(code), {**report, "rows": rows})
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Check every declared reading and name.")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--language", choices=CODES)
    choice.add_argument("--propose", action="store_true", help="Propose Chinese declarations")
    options = parser.parse_args(argv)
    if options.propose:
        print(json.dumps(propose(), ensure_ascii=False))
        return
    reports, failures = [], []
    for code in (options.language,) if options.language else CODES:
        try:
            reports.append(check(code))
        except ReadingError as error:
            failures.append(f"{code}: {error}")
    if failures:
        message = "readings: " + "\n".join(failures)
        raise SystemExit(message)
    print(json.dumps(reports, ensure_ascii=False))


if __name__ == "__main__":
    main()
