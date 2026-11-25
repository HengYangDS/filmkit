"""The pinned CMUdict, by which a language that declares `cmudict-pronunciations` hears a
transcript's Latin-script words (`filmkit.narration.recognition`).

The supply step downloads the file from CMUdict's repository at its pinned commit into the tool
cache and checks its size and SHA-256 (`filmkit.supply`); no package carries it, and the engine
does not redistribute it. A judgment reads only that file: one missing or of other bytes is
refused in one line that names the supply step, before any model loads.

Each headword keeps its pronunciations in the file's order, its unnumbered line first and its
numbered variants (`word(2)`) after it, so its first is CMUdict's usual pronunciation. Comments,
after `#`, are dropped. A pronunciation is read with its primary stress kept and its secondary
stress read as none (design decision 2 of hear-a-take-as-a-listener-does): stress 2 against 0 on
one vowel tells no English word from another that the films say (catalogue, catalog), while
primary stress keeps a word's weak and strong forms apart ("uh" and "a").
"""

from __future__ import annotations

import re

import filmkit.repository as repository

# The file at CMUdict's latest commit, 74790861 of 24 October 2025, under Carnegie Mellon's
# two-clause BSD notice; the three films' pronunciations cite the same URL, SHA-256 and size.
COMMIT = "74790861f652b15e4ac49015a90074ad62a27690"
URL = f"https://raw.githubusercontent.com/cmusphinx/cmudict/{COMMIT}/cmudict.dict"
SHA256 = "81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22"
BYTES = 3_618_488
# Where the supply step places it, below the film's root.
PLACE = "build/runtime/tool-cache/cmudict/cmudict.dict"
SUPPLY = "filmkit supply"
VARIANT = re.compile(r"\(\d+\)$")

# Each headword's pronunciations, each a tuple of ARPAbet phones.
Dictionary = dict[str, tuple[tuple[str, ...], ...]]


class DictionaryError(ValueError):
    """The supplied dictionary is missing or differs from its pin."""


def phones(pronunciation: str) -> tuple[str, ...]:
    """A pronunciation's phones, its secondary stress read as none."""
    return tuple(
        phone[:-1] + "0" if phone.endswith("2") else phone for phone in pronunciation.split()
    )


def parse(raw: bytes) -> Dictionary:
    """Each headword's pronunciations in the file's order, its first before its variants."""
    found: dict[str, list[tuple[bool, tuple[str, ...]]]] = {}
    for line in raw.decode("utf-8").splitlines():
        body = line.split("#", 1)[0].strip()
        if not body or body.startswith(";;;"):
            continue
        head, said = body.split(maxsplit=1)
        word = VARIANT.sub("", head)
        found.setdefault(word, []).append((word != head, phones(said)))
    # A stable sort puts the unnumbered line first and keeps the variants in the file's order.
    return {
        word: tuple(said for _, said in sorted(lines, key=lambda line: line[0]))
        for word, lines in found.items()
    }


# The file read once a process, by its SHA-256: a convergence judges its edition in every round.
_READ: dict[str, Dictionary] = {}


def supplied() -> Dictionary:
    """The dictionary the supply step placed, refused in one line where it is missing or differs
    from its pinned SHA-256. Its bytes are checked at every call and parsed once a process."""
    path = repository.ROOT / PLACE
    if not path.is_file():
        msg = f"The pinned CMUdict is missing at {PLACE}; run {SUPPLY}"
        raise DictionaryError(msg)
    raw = path.read_bytes()
    if len(raw) != BYTES or repository.content_sha(raw) != SHA256:
        msg = f"The CMUdict at {PLACE} differs from the pinned SHA-256 {SHA256}; run {SUPPLY}"
        raise DictionaryError(msg)
    if SHA256 not in _READ:
        _READ[SHA256] = parse(raw)
    return _READ[SHA256]
