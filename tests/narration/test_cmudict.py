"""The pinned CMUdict: read in its file's order, secondary stress as none, and refused where the
supply step has not placed its bytes."""

import pronounced
import pytest

import filmkit.narration.cmudict as cmudict
import filmkit.repository as repository

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
