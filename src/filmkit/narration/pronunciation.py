"""Spoken text, pronunciation targets, narration language and the thoughts each segment speaks.

Each edition's pronunciation, `content/<code>/pronunciation.json` (`filmkit.places.places`), owns
how its display text is spoken: its normalization rules derive every spoken text. Before any
speech provider loads, its lexical stress targets must agree with their ARPAbet phones, in a
language that holds its stress to CMUdict, and every source its targets cite must stand in it or
among the sources every edition shares, in the declaration's `[pronunciation]` table. A
recording's request binds the SHA-256 of its own edition's pronunciation and of no other.
"""

from __future__ import annotations

import json
import re

import filmkit.languages as languages
import filmkit.narration.cmudict as cmudict
import filmkit.repository as repository
from filmkit.narration.thought_groups import authored_groups

# One Han character, as a regular expression (`filmkit.languages`).
HAN = f"[{languages.pattern('han')}]"


class PronunciationError(ValueError):
    """An edition's pronunciation is missing, contradicts its own stress or cites an unlisted
    source."""


def pronunciation(code: str) -> tuple[dict, str]:
    """An edition's pronunciation and its file's SHA-256, checked before it is used.

    Raises:
        PronunciationError: the file does not exist, a stress target contradicts itself, or a target
            cites a source that neither the file nor the declaration lists.
    """
    # The film is read here, when a pronunciation is, and not as the module loads: a command
    # that stands in for the narration imports it with no film below its root.
    from filmkit.film import FILM
    from filmkit.places import places

    path = places(code, FILM.slug).pronunciation
    try:
        raw = (repository.ROOT / path).read_bytes()
    except FileNotFoundError:
        msg = f"{code}: {path} does not exist; write the edition's pronunciation there"
        raise PronunciationError(msg) from None
    part = json.loads(raw)
    shared = FILM.pronunciation.sources
    validate_part(code, part, path, {source.id for source in shared})
    return part, repository.content_sha(raw)


def validate_part(code: str, part: dict, path: str, shared: set[str] = frozenset()) -> None:
    """Reject an edition's contradictory lexical stress, where its language holds its stress to
    CMUdict (`filmkit.languages`), and every source its targets cite that neither its own
    sources nor the shared ones (`shared`, their ids) list, naming each target and source."""
    targets = part.get("targets", [])
    if languages.checks(code, languages.CMUDICT_STRESS):
        for target in targets:
            _check_stress(target.get("lexical_stress", {}), target["term"])
    listed = {source.get("id") for source in part.get("sources", [])} | shared
    unlisted = [
        f"{path}: the target {target['term']} cites the source {source!r}, which neither {path} "
        "nor the declaration's [pronunciation] sources list; list it in one of them"
        for target in targets
        for source in _cited(target.get("source"))
        if source not in listed
    ]
    if unlisted:
        raise PronunciationError("\n".join(unlisted))


def _cited(source: object) -> list:
    """The sources a target cites: none, one or a list."""
    if source is None:
        return []
    return source if isinstance(source, list) else [source]


def _check_stress(value: object, term: str) -> None:
    """Check each stress target in a value: one target, its variants or its senses."""
    if isinstance(value, list):
        for member in value:
            _check_stress(member, term)
        return
    if not isinstance(value, dict):
        return
    if "syllable_count" in value:
        _check_syllables(value, term)
        if "arpabet" in value:
            _check_arpabet(value, term)
    for member in value.values():
        _check_stress(member, term)


def _check_syllables(value: dict, term: str) -> None:
    """Check that the stressed syllables are distinct places within the syllable count."""
    count = value["syllable_count"]
    primary = value.get("primary_syllable")
    secondary = value.get("secondary_syllables", [])

    def place(index: object) -> bool:
        return type(index) is int and 1 <= index <= count

    if (
        type(count) is not int
        or count < 1
        or (count > 1 and not place(primary))
        or (count == 1 and primary is not None and not place(primary))
        or not isinstance(secondary, list)
        or any(not place(index) for index in secondary)
        or len(set(secondary)) != len(secondary)
        or primary in secondary
    ):
        msg = f"Invalid lexical stress target for {term}"
        raise PronunciationError(msg)


def _check_arpabet(value: dict, term: str) -> None:
    """Check that the phones' vowels and stress marks agree with the declared syllables."""
    count = value["syllable_count"]
    vowels = [phone for phone in value["arpabet"] if phone[-1:].isdigit()]
    primary = [index for index, phone in enumerate(vowels, 1) if phone.endswith("1")]
    secondary = [index for index, phone in enumerate(vowels, 1) if phone.endswith("2")]
    if (
        len(vowels) != count
        or (count > 1 and primary != [value.get("primary_syllable")])
        or secondary != value.get("secondary_syllables", [])
    ):
        msg = f"Contradictory lexical stress phones for {term}"
        raise PronunciationError(msg)


def declared_readings(part: dict) -> dict[str, tuple[tuple[str, ...], ...]]:
    """The readings an edition's pronunciation declares by word, lowercased, as a transcript's
    word is heard against them (`filmkit.narration.recognition`): every ARPAbet its target states
    under `lexical_stress`, one reading or one per part of speech, read as CMUdict's are
    (`cmudict.phones`), in the order the target states them; and none, (), for a word it declares
    by its letter names. A target that states no phones declares no reading."""
    found = {}
    for target in part.get("targets", []):
        word = target["term"].lower()
        if target.get("kind") == "letter-name":
            found[word] = ()
            continue
        stated = tuple(dict.fromkeys(_arpabets(target.get("lexical_stress", {}))))
        if stated:
            found[word] = stated
    return found


def _arpabets(value: object):
    """Each pronunciation a stress target states: one target, its variants or its senses."""
    if isinstance(value, list):
        for member in value:
            yield from _arpabets(member)
        return
    if not isinstance(value, dict):
        return
    if "arpabet" in value:
        yield cmudict.phones(" ".join(value["arpabet"]))
    for key, member in value.items():
        if key != "arpabet":
            yield from _arpabets(member)


def pronunciation_text(section: dict, contract: dict) -> str:
    """Derive speech copy from an edition's pronunciation."""
    derived = section["text"]
    for rule in contract["normalization"]:
        derived = _normalized(derived, rule)
    if section.get("spoken_text", derived) != derived:
        msg = "Speech text differs from the declared pronunciation mapping"
        raise ValueError(msg)
    return derived


def _normalized(text: str, rule: dict) -> str:
    """Apply one normalization rule: a 1:1 homophone, or an English name as a whole word."""
    display, spoken = rule["display"], rule["spoken"]
    if not display or not spoken:
        msg = "Pronunciation normalization requires complete words"
        raise ValueError(msg)
    if rule["kind"] == "homophone":
        if len(display) < 2 or len(display) != len(spoken):
            msg = "Homophone normalization must be word-scoped and 1:1"
            raise ValueError(msg)
        return text.replace(display, spoken)
    if rule["kind"] == "english-name":
        return re.sub(
            rf"(?<![A-Za-z]){re.escape(display)}(?![A-Za-z])",
            lambda _match: spoken,
            text,
            flags=re.IGNORECASE,
        )
    msg = "Unknown pronunciation normalization kind"
    raise ValueError(msg)


def validate_language_reference(narration: dict, cast: dict, code: str) -> str:
    """Hold an edition's text and its cast's reference transcript to the edition's language.

    The text holds no character of a script that the language neither writes nor reads as
    another language (`filmkit.languages`), and the reference transcript holds a character of a
    script the language writes. Every refusal names the segment and the script, or the cast.

    Returns:
        The language's name as the speech models take it.
    """
    language = languages.language(code)
    read = {*language.scripts, *language.embedded}
    others = [name for name in languages.classes()["scripts"] if name not in read]
    for item in narration["segments"]:
        for field in ("text", "spoken_text"):
            for script in others:
                found = languages.compiled(script).search(item.get(field, ""))
                if found:
                    msg = (
                        f"{code} {item['id']}: its {field} holds {found[0]!r} of the {script} "
                        f"script, which {language.english_name} neither writes nor reads as "
                        "another language"
                    )
                    raise ValueError(msg)
    transcript = cast.get("reference_text", "")
    if not languages.compiled(*language.scripts).search(transcript):
        msg = (
            f"{code}: the cast's reference transcript holds no character of the "
            f"{', '.join(language.scripts)} script that {language.english_name} writes"
        )
        raise ValueError(msg)
    return language.english_name


def native_utterance_plan(section: dict, contract: dict) -> list[dict]:
    """The section's authored thoughts and their spoken text, before any model or write."""
    plans = [
        {"text": text, "spoken_text": pronunciation_text({"text": text}, contract)}
        for text in authored_groups(section)
    ]
    if "".join(item["spoken_text"] for item in plans) != section["spoken_text"]:
        msg = "Utterance groups change the declared speech mapping"
        raise ValueError(msg)
    return plans
