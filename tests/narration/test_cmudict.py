"""The pinned CMUdict: read in its file's order, secondary stress as none, and refused where the
supply step has not placed its bytes."""

import json
from pathlib import Path

import pronounced
import pytest

import filmkit.narration.cmudict as cmudict
import filmkit.narration.recognition as recognition
import filmkit.repository as repository

ENGINE = Path(__file__).resolve().parents[2]
SAMPLE = ENGINE / "examples/sample-film/content/en/film-script.json"

FIXTURE = (
    b";;; # comment lines and comments after a pronunciation are dropped\n"
    b"tears T EH1 R Z\n"
    b"tears(2) T IH1 R Z # the noun\n"
    b"catalog K AE1 T AH0 L AO0 G\n"
    b"catalogue K AE1 T AH0 L AO2 G\n"
)


def test_a_headwords_pronunciations_keep_the_files_order_and_read_secondary_stress_as_none():
    read = cmudict.parse(FIXTURE)
    assert read["tears"] == (("T", "EH1", "R", "Z"), ("T", "IH1", "R", "Z"))
    assert read["catalogue"] == read["catalog"] == (("K", "AE1", "T", "AH0", "L", "AO0", "G"),)
    assert set(read) == {"tears", "catalog", "catalogue"}


def test_a_numbered_variant_follows_its_headwords_first_wherever_it_stands():
    read = cmudict.parse(b"a(2) EY1\na AH0\n")
    assert read["a"] == (("AH0",), ("EY1",))


def test_the_supplied_file_is_read_at_its_place_when_it_holds_the_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    expected = pronounced.supplied(monkeypatch)
    assert cmudict.supplied() == expected


@pytest.mark.parametrize("bytes_in_place", [None, b"other bytes\n"])
def test_a_missing_or_altered_file_is_refused_in_one_line_that_names_the_supply(
    tmp_path, monkeypatch, bytes_in_place
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    pronounced.supplied(monkeypatch)
    path = tmp_path / cmudict.PLACE
    if bytes_in_place is None:
        path.unlink()
    else:
        path.write_bytes(bytes_in_place)
    with pytest.raises(cmudict.DictionaryError) as refusal:
        cmudict.supplied()
    said = str(refusal.value)
    assert "\n" not in said and "python -m filmkit.supply" in said
    assert cmudict.PLACE in said
    assert ("is missing" if bytes_in_place is None else "differs from the pinned SHA-256") in said


def test_the_pin_is_the_commit_the_films_cite():
    assert cmudict.URL == (
        "https://raw.githubusercontent.com/cmusphinx/cmudict/"
        "74790861f652b15e4ac49015a90074ad62a27690/cmudict.dict"
    )
    assert cmudict.SHA256 == "81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22"
    assert (cmudict.BYTES, cmudict.PLACE) == (
        3_618_488,
        "build/runtime/tool-cache/cmudict/cmudict.dict",
    )


def let_through(words: list[str], found: recognition.Pronunciations) -> dict[str, list[str]]:
    """For each text word, the other spellings a transcript may hold that the engine's own
    comparison passes for it (`recognition.reading_distance`): every headword in other letters
    that a recognition unit can spell, asked of the rule itself, not of a copy of it. The
    candidates are the headwords whose first pronunciation is one of the word's readings."""
    names = recognition.Names(pronounced=found)
    by_first: dict[tuple[str, ...], list[str]] = {}
    for headword, said in found.said.items():
        if recognition.recognition_units(headword) == [headword]:
            by_first.setdefault(said[0], []).append(headword)
    listed = {}
    for word in words:
        own, _ = found.of(word.lower())
        candidates = {other for said in own for other in by_first.get(said, ())}
        listed[word] = sorted(
            other
            for other in candidates
            if other.replace("'", "") != word.lower().replace("'", "")
            and recognition.reading_distance(word, other, (), names) == 0
        )
    return listed


def test_the_spellings_the_rule_takes_for_a_text_word_over_the_fixture():
    said = recognition.Pronunciations(cmudict.parse(pronounced.RAW), {"ai": ()})
    words = ["labelled", "tiers", "their", "catalogue", "AI", "to", "eye"]
    assert let_through(words, said) == {
        "labelled": ["labeled"],
        # tears is first the verb tear: no spelling has tiers' sound first.
        "tiers": [],
        "their": ["there", "they're"],
        "catalogue": ["catalog"],
        # Declared by its letter names, AI has no pronunciation.
        "AI": [],
        "to": ["thuy", "too", "tu", "tue", "two"],
        # "ai" says "eye" first, but is declared by its letter names: the comparison refuses it.
        "eye": ["i"],
    }


# The spellings the rule takes for each English word of the sample film and of the Change's
# scenarios over the pinned file, from the design's appendix (probe-6 and probe-7) and the
# scenarios; a word not listed takes none.
PINNED = {
    "build": ["bild", "billed"],
    "check": ["chek", "cheque", "czech"],
    "draws": ["draus"],
    "file": ["pfeil", "phyle"],
    "first": ["furst"],
    "frame": ["fraim"],
    "from": ["frum"],
    "how": ["hao", "hau", "howe"],
    "joins": ["joines", "joynes"],
    "made": ["maid", "mayde"],
    "match": ["mache", "matsch"],
    "matches": ["matsch's"],
    "none": ["nuhn", "nun", "nunn"],
    "one": ["won"],
    "part": ["parte"],
    "same": ["sejm"],
    "seed": ["cede"],
    "short": ["shortt"],
    "so": ["sew"],
    "steps": ["steppes"],
    "these": ["thee's"],
    "to": ["thuy", "too", "tu", "tue", "two"],
    "was": ["waas", "wah's"],
    "when": ["wen"],
    "labelled": ["labeled"],
    "their": ["there", "they're"],
    "catalogue": ["catalog"],
    "tiers": [],
    "an": ["ahn", "ann", "anne"],
    "or": ["oar", "ohr", "ore", "orr"],
    "delivery's": [],
}


@pytest.mark.cmudict
def test_the_spellings_the_rule_takes_over_the_pinned_file():
    script = json.loads(SAMPLE.read_text(encoding="utf-8"))
    sample = {
        unit
        for segment in script["segments"]
        for unit in recognition.recognition_units(segment.get("spoken_text") or segment["text"])
    }
    words = sorted(sample | set(PINNED))
    # The supply step places the file below the film's root: the sample's, which the tests build.
    place = repository.ROOT / cmudict.PLACE
    said = recognition.Pronunciations(cmudict.parse(place.read_bytes()), {})
    found = let_through(words, said)
    assert {word: others for word, others in found.items() if others} == {
        word: others for word, others in PINNED.items() if others
    }
