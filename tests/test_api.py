"""The films' interface (design decision 16 of build-a-film-by-its-verbs): every name a film's
own tests and tools may import, each on the sample."""

import json

import pytest

import filmkit.api as api
import filmkit.repository as repository
from filmkit.captions.timing import typeset
from filmkit.delivery.reproduction import Release
from filmkit.film import FILM
from filmkit.production import CODES, Edition

NAMES = [
    "ROOT",
    "film",
    "editions",
    "Edition",
    "derived_timeline",
    "place_anchors",
    "typeset",
    "composition",
    "release",
    "changed_sources",
    "TEST_ENTRY",
]


def test_the_interface_states_its_names_and_no_other():
    assert api.__all__ == NAMES


def test_the_film_its_root_and_its_editions():
    assert api.ROOT == repository.ROOT
    assert api.film() is FILM
    assert api.editions() == CODES == ("zh", "en")
    assert api.Edition is Edition
    assert api.Edition("zh").script == Edition("zh").script


def test_the_derived_timeline_and_the_anchors_of_a_timeline_of_other_words():
    derived = api.derived_timeline("zh")
    assert derived["captions"] == [] and derived["fps"] == 60
    assert json.dumps(api.derived_timeline("zh")) == json.dumps(derived)
    # A timeline of the derived words, built elsewhere, takes the same anchors.
    script = repository.read(Edition("zh").script)
    words = {s["id"]: s["words"] for s in derived["segments"]}
    own = {**script, "segments": [{**s, "words": words[s["id"]]} for s in script["segments"]]}
    placed = api.place_anchors(own, "zh")
    assert [s.get("anchors") for s in placed["segments"]] == [
        s.get("anchors") for s in derived["segments"]
    ]


def test_the_typesetter_the_composition_and_the_test_entry():
    assert api.typeset is typeset
    assert api.typeset('It "is".') == "It “is”."
    assert api.composition() == repository.ROOT / "picture/film.js"
    assert api.composition().is_file()
    assert api.TEST_ENTRY.name == "testing.mjs"


def test_the_release_record_and_its_changed_sources():
    # The sample records no release: there is no record at its root to read.
    with pytest.raises(FileNotFoundError, match="release.json"):
        api.release()
    stated = Release.model_construct(sources={"content/zh/film-script.json": "0" * 64})
    assert api.changed_sources(stated) == ["content/zh/film-script.json"]
