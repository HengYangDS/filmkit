"""The units line as a listener hears a take: English words by their pronunciation in the pinned
CMUdict, read only where the supply step placed it, and named in the judgment's record."""

import pronounced
import pytest

import filmkit.film as film
import filmkit.narration.cmudict as narration_cmudict
import filmkit.narration.converge as narration_converge
import filmkit.narration.judge as narration_judge
import filmkit.narration.judgment as narration_judgment
import filmkit.repository as repository
from filmkit.production import Edition

LETTER_NAMES = {"term": "AI", "kind": "letter-name", "lexical_stress": {}}


def said(narrated, voiced, first: str, heard: str, targets=()) -> None:
    """Narrate the English edition with `first` as its first thought, which the recognizer hears
    as `heard`, under a pronunciation that declares `targets`."""
    plans = [{"text": first, "spoken_text": first}, {"text": " Second thought."}]
    plans[1]["spoken_text"] = plans[1]["text"]
    repository.write(
        Edition("en").places.pronunciation, {"normalization": [], "targets": list(targets)}
    )
    narrated([voiced(), voiced()], plans)
    narrated.recognizer.thoughts[0] = heard


def judged_first() -> dict:
    narration_judge.main(["--language", "en"])
    record = repository.read(Edition("en").ear_first / narration_judge.RECORD)
    return record["thoughts"][0]


def test_an_english_bench_hears_another_spelling_of_the_same_word(narrated, voiced):
    said(narrated, voiced, "It is labelled.", "It is labeled.")
    first = judged_first()
    assert (first["differing_units"], first["differing_units_by_reading"]) == (1, 0)
    assert first["failed"] == []


def test_a_word_declared_by_letter_names_is_not_heard_as_the_word_eye(narrated, voiced):
    said(narrated, voiced, "AI helps.", "I helps.", [LETTER_NAMES])
    with pytest.raises(SystemExit):
        narration_judge.main(["--language", "en"])
    record = repository.read(Edition("en").ear_first / narration_judge.RECORD)
    assert record["refused"] == {"26.1": ["units"]}


def test_the_record_names_the_dictionary_and_binds_the_pronunciation(narrated, voiced):
    said(narrated, voiced, "It is labelled.", "It is labeled.")
    narration_judge.main(["--language", "en"])
    record = repository.read(Edition("en").ear_first / narration_judge.RECORD)
    assert record["pronunciations"] == {
        "dictionary": narration_cmudict.URL,
        "dictionary_sha256": narration_cmudict.SHA256,
        "pronunciation_sha256": repository.sha(Edition("en").places.pronunciation),
    }
    assert narration_cmudict.URL.endswith(f"{narration_cmudict.COMMIT}/cmudict.dict")


@pytest.mark.parametrize("left", [None, b"other bytes\n"])
def test_a_dictionary_not_in_place_stops_the_judgment_before_any_model_loads(
    narrated, voiced, monkeypatch, left
):
    said(narrated, voiced, "It is labelled.", "It is labeled.")
    place = repository.ROOT / narration_cmudict.PLACE
    if left is None:
        place.unlink()
    else:
        place.write_bytes(left)
    monkeypatch.setattr(narration_judgment, "load_asr", pytest.fail)
    monkeypatch.setattr(narration_judgment, "load_aligner", pytest.fail)
    with pytest.raises(SystemExit) as refusal:
        narration_judge.main(["--language", "en"])
    said_once = str(refusal.value)
    assert "\n" not in said_once and said_once.startswith("en: ")
    assert "python -m filmkit.supply" in said_once
    assert not (Edition("en").ear_first / narration_judge.RECORD).exists()


def test_a_convergence_stops_before_its_first_effect_without_the_dictionary(narrated, voiced):
    said(narrated, voiced, "It is labelled.", "It is labeled.")
    (repository.ROOT / narration_cmudict.PLACE).unlink()
    with pytest.raises(SystemExit, match="python -m filmkit.supply"):
        narration_converge.main(["--language", "en"])
    assert not (Edition("en").ear_first / narration_converge.RECORD).exists()


def test_a_language_that_hears_its_latin_words_by_their_letters_reads_no_dictionary(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    repository.write(Edition("zh").places.pronunciation, {"normalization": []})
    groups = ["先看 their 目标。", "再看 there 的。"]
    text = "".join(groups)
    segment = {"id": "01", "text": text, "spoken_text": text, "utterance_groups": groups}
    repository.write(Edition("zh").script, {"segments": [segment]})
    monkeypatch.setattr(narration_cmudict, "supplied", pytest.fail)
    assert narration_judgment.pronunciations("zh") is None
    bench = narration_judgment.bench("zh", [], asr=None, aligner={})
    assert (bench.names.heard, bench.pronounced) == (None, None)


def test_the_pronunciation_declares_the_readings_the_bench_hears_by(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    pronounced.supplied(monkeypatch)
    read = {
        "term": "read",
        "kind": "contextual-homograph",
        "lexical_stress": {
            "verb": {"arpabet": ["R", "IY1", "D"], "syllable_count": 1},
            "past": [{"arpabet": ["R", "EH1", "D"], "syllable_count": 1}],
        },
    }
    catalogue = {
        "term": "Catalogue",
        "kind": "lexical",
        "lexical_stress": {"arpabet": ["K", "AE1", "T", "AH0", "L", "AO2", "G"]},
    }
    part = {"normalization": [], "targets": [LETTER_NAMES, read, catalogue]}
    repository.write(Edition("en").places.pronunciation, part)
    heard = narration_judgment.pronunciations("en").heard
    assert heard.declared == {
        "ai": (),
        "read": (("R", "IY1", "D"), ("R", "EH1", "D")),
        "catalogue": (("K", "AE1", "T", "AH0", "L", "AO0", "G"),),
    }
    assert heard.said == narration_cmudict.parse(pronounced.RAW)


SHA = "b" * 64


def record_of(*lines: str, take: str = SHA, thought: str = "26.1") -> film.Heard:
    """The owner's hearing of one English take, settling `lines`."""
    return film.Heard(
        edition="en",
        thought=thought,
        take=take,
        lines=lines,
        listener=film.FILM.author,
        date="2026-11-24",
        note="Heard on the clip.",
    )


def a_take(*, by_reading=0, stops=(), clarity=None, sha=SHA) -> dict:
    """A measured take of thought 26.1, its clarity read as `clarity` dB."""
    return {
        "path": "take.wav",
        "wav_sha256": sha,
        "natural": True,
        "clip_opens_quiet": True,
        "phrase_stops": list(stops),
        "fluent": True,
        "terms_pass": True,
        "differing_units": by_reading,
        "differing_units_by_reading": by_reading,
        "short": False,
        "_clarity": clarity,
    }


@pytest.fixture
def judged(monkeypatch):
    """Judge a take of 26.1 under an 18.0 dB floor and thought line, with the records given."""
    reading = {}

    def take_clarity(_path, floor):
        value = reading["value"]
        return None if floor is None else {"cpp_db": value, "below_floor": value < floor}

    monkeypatch.setattr(narration_judgment, "take_clarity", take_clarity)

    def judge(take: dict, *records: film.Heard) -> dict:
        reading["value"] = take.pop("_clarity")
        floor = None if reading["value"] is None else 18.0
        held = narration_judgment.Held({}, floor, floor, frozenset(), records)
        return narration_judgment.judge(take, "26", 1, held)

    return judge


def test_a_take_heard_to_say_its_words_passes_its_units_line_naming_the_listener(judged):
    row = judged(a_take(by_reading=1), record_of("units"))
    assert row["failed"] == []
    assert row["lines"]["units"] == {
        "passes": True,
        "limit": 0,
        "heard": {"listener": film.FILM.author, "date": "2026-11-24"},
    }
    assert row["differing_units_by_reading"] == 1


def test_a_take_heard_clear_passes_its_clarity_line_and_keeps_its_reading(judged):
    row = judged(a_take(clarity=17.4), record_of("clarity"))
    assert row["failed"] == []
    assert row["lines"]["clarity"]["passes"] is True
    assert row["lines"]["clarity"]["heard"] == {"listener": film.FILM.author, "date": "2026-11-24"}
    assert row["clarity"]["cpp_db"] == 17.4


def test_a_heard_take_that_cuts_a_phrase_end_is_refused_by_the_phrase_line_alone(judged):
    row = judged(
        a_take(by_reading=1, stops=[{"stops": True}], clarity=17.4), record_of("units", "clarity")
    )
    assert row["failed"] == ["phrase"]


def test_another_take_of_the_heard_thought_is_judged_as_if_no_record_stood(judged):
    row = judged(a_take(by_reading=1, sha="c" * 64), record_of("units", "clarity"))
    assert row["failed"] == ["units"]
    assert "heard" not in row["lines"]["units"]
    # A record of another thought settles nothing of this one.
    row = judged(a_take(by_reading=1), record_of("units", thought="26.2"))
    assert row["failed"] == ["units"]


def test_a_record_the_take_does_not_need_says_so_and_refuses_nothing(judged):
    row = judged(a_take(), record_of("units"))
    assert row["failed"] == []
    assert row["lines"]["units"] == {"passes": True, "limit": 0, "heard": "not needed"}
