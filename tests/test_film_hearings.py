"""The film's records of the owner's hearing (`[[narration.heard]]`): one take each, by its audio,
heard by the film's author, settling the lines it names and refused where it says less."""

import pytest

import filmkit.film as film
from filmkit.film import FilmError

TAKE = "a" * 64
HEARD = f"""
[[narration.heard]]
edition = "en"
thought = "13.2"
take = "{TAKE}"
lines = ["units"]
listener = "Yang HENG"
date = "2026-11-24"
note = "He heard labelled said as written."
"""


def with_records(root, *records: str) -> None:
    """Append records of hearing to the declaration at a root."""
    path = root / film.DECLARATION
    path.write_text(path.read_text() + "".join(records))


def test_a_record_of_hearing_loads_with_its_fields(declared):
    with_records(declared, HEARD)
    (heard,) = film.load(declared).narration.heard
    assert (heard.edition, heard.thought, heard.take) == ("en", "13.2", TAKE)
    assert (heard.lines, heard.listener, heard.date) == (("units",), "Yang HENG", "2026-11-24")
    assert heard.note == "He heard labelled said as written."
    assert film.FILM.narration.heard == ()


def test_a_listener_who_is_not_the_owner_is_refused_naming_the_record_and_the_author(declared):
    with_records(declared, HEARD.replace('"Yang HENG"', '"A Reviewer"'))
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    said = str(refusal.value)
    assert "narration.heard en 13.2" in said and "A Reviewer" in said
    assert "the film's author, Yang HENG" in said


@pytest.mark.parametrize(
    ("old", "new", "named"),
    [
        (TAKE, "A" * 64, "take"),
        (TAKE, "a" * 63, "take"),
        ('["units"]', "[]", "lines"),
        ('["units"]', '["pause"]', "lines"),
        ('["units"]', '["units", "units"]', "narration.heard en 13.2 names a line twice"),
        ('note = "He heard labelled said as written."', 'note = " "', "note"),
        ('date = "2026-11-24"\n', "", "date"),
        ('edition = "en"', 'edition = "fr"', "narration.heard names the edition fr"),
    ],
)
def test_a_record_that_names_no_audio_or_no_line_is_refused_naming_the_record(
    declared, old, new, named
):
    with_records(declared, HEARD.replace(old, new))
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    # The loader names the record by its place among the records, and the field.
    said = str(refusal.value)
    assert "narration.heard" in said and named in said


def test_a_second_record_of_one_take_is_refused(declared):
    with_records(declared, HEARD, HEARD.replace('["units"]', '["clarity"]'))
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert f"narration.heard records the take {TAKE} twice" in str(refusal.value)


def test_a_record_may_settle_both_lines(declared):
    with_records(declared, HEARD.replace('["units"]', '["units", "clarity"]'))
    (heard,) = film.load(declared).narration.heard
    assert heard.lines == ("units", "clarity")
