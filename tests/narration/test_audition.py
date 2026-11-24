"""Auditioning alternative takes of chosen thoughts and binding the selected seeds."""

import dataclasses
import hashlib
import json
import wave
from types import SimpleNamespace

import numpy as np
import pronounced
import pytest

import filmkit.film as film
import filmkit.narration.audition as narration_audition
import filmkit.narration.cmudict as narration_cmudict
import filmkit.narration.group_generation as narration_group_generation
import filmkit.narration.terms as narration_terms
import filmkit.repository as repository
from filmkit.narration.narrate import evidence_paths
from filmkit.production import Edition

# Where the English edition's narration writes its receipt, which the audition reads: no cast
# names it.
RECEIPT = evidence_paths("en")["receipt"]


def sha256(data: bytes | str) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def take(seed, *, failed=(), heard=True, end_ratio=0.1, seconds=3.0):
    return {
        "seed": seed,
        "failed": list(failed),
        "required_heard": heard,
        "end_ratio": end_ratio,
        "seconds": seconds,
    }


def test_propose_ranks_only_the_takes_no_line_of_the_judgment_refuses():
    takes = [
        take(1, failed=["ending"], end_ratio=0.01),
        take(2, failed=["units"], end_ratio=0.02),
        take(3, end_ratio=0.05),
        take(4, end_ratio=0.08, seconds=3.4),
        take(5, failed=["pause"], seconds=4.0),
        take(6, end_ratio=0.09, seconds=2.8),
        take(7, failed=["terms", "clarity"], seconds=2.0),
    ]
    assert narration_audition.propose(takes) == 3
    assert narration_audition.propose(takes, "slower") == 4
    assert narration_audition.propose(takes, "brisker") == 6
    # A take that a line refuses is never proposed, whatever the others fail.
    assert narration_audition.propose([takes[0], takes[1], takes[4], takes[6]]) is None


def test_propose_puts_a_take_that_holds_the_required_phrase_before_one_that_does_not():
    # The phrase orders the qualified takes and qualifies none.
    takes = [take(1, heard=False, end_ratio=0.01), take(2, end_ratio=0.2)]
    assert narration_audition.propose(takes) == 2
    assert narration_audition.propose(takes[:1]) == 1
    assert narration_audition.propose([take(3, failed=["phrase"]), takes[0]]) == 1


THOUGHTS = ["按及时性的标准，这次交付不合格。", "把调度窗口提前，是有权的人做的决定。"]


def proposal(segment: str, index: int, text: str, seed: int | None) -> dict:
    return {
        "segment": segment,
        "index": index,
        "text": text,
        "spoken_text": text,
        "required": "有权的人",
        "current_seed": 4683,
        "takes": [],
        "proposed_seed": seed,
    }


@pytest.fixture
def cast(write_edition):
    return write_edition("zh", {"06": THOUGHTS}, {})["cast"]


def test_apply_binds_current_thoughts_and_skips_rows_without_a_proposal(tmp_path, cast, capsys):
    rows = [proposal("06", 2, THOUGHTS[1], 99711), proposal("06", 1, THOUGHTS[0], None)]
    repository.write(tmp_path / "proposals.json", rows)
    narration_audition.main(["apply", "--language", "zh", "--proposals", "proposals.json"])
    assert json.loads(capsys.readouterr().out) == {
        "language": "zh",
        "applied": ["06.2=99711"],
        "skipped": ["06.1"],
        "dry_run": False,
    }
    assert repository.read(cast)["retakes"] == {
        "06": {
            "groups": {
                "2": {
                    "seed": 99711,
                    "text_sha256": sha256(THOUGHTS[1]),
                    "spoken_sha256": sha256(THOUGHTS[1]),
                }
            }
        }
    }


@pytest.mark.parametrize(
    "row",
    [
        proposal("06", 2, "把调度窗口提前，是负责人的决定。", 99711),
        proposal("06", 3, THOUGHTS[1], 99711),
        proposal("07", 1, THOUGHTS[0], 99711),
    ],
)
def test_apply_refuses_a_thought_whose_text_changed(tmp_path, cast, row):
    repository.write(tmp_path / "proposals.json", [proposal("06", 1, THOUGHTS[0], 7), row])
    before = cast.read_bytes()
    with pytest.raises(ValueError, match="not the current thought"):
        narration_audition.main(["apply", "--language", "zh", "--proposals", "proposals.json"])
    assert cast.read_bytes() == before


def test_apply_dry_run_leaves_the_cast_unchanged(tmp_path, cast, capsys):
    repository.write(tmp_path / "proposals.json", [proposal("06", 2, THOUGHTS[1], 99711)])
    before = cast.read_bytes()
    narration_audition.main(
        ["apply", "--language", "zh", "--proposals", "proposals.json", "--dry-run"]
    )
    report = json.loads(capsys.readouterr().out)
    assert report["applied"] == ["06.2=99711"]
    assert report["dry_run"] is True
    assert cast.read_bytes() == before


@pytest.fixture
def auditioned(retained_group_record, declared, monkeypatch):
    """An English edition whose declared receipt holds one grouped, bound recording.

    The film declares no clarity floor, so no take is decoded for its clarity, and the fixture
    lines of CMUdict stand in for the supplied dictionary (`pronounced`).
    """
    root, record, plans, settings = retained_group_record
    monkeypatch.setattr(repository, "ROOT", root)
    pronounced.supplied(monkeypatch)
    declared(clarity_minimum_db=None)
    record = {**record, "text_sha256": sha256(record["text"])}
    edition = Edition("en")
    section = {
        "id": "26",
        "text": record["text"],
        "spoken_text": record["spoken_text"],
        "utterance_groups": [plan["text"] for plan in plans],
    }
    repository.write(edition.script, {"segments": [section]})
    repository.write(edition.places.pronunciation, {"normalization": []})
    cast = {
        "reference_sha256": settings["reference_sha256"],
        "reference_text": settings["reference_text"],
    }
    repository.write(edition.cast, cast)
    repository.write(RECEIPT, {"records": [record]})
    repository.write("targets.json", {"26.2": "second thought"})

    def unloaded():
        pytest.fail("A refused audition loads no model")

    monkeypatch.setattr(narration_group_generation, "load_voice_model", unloaded)
    monkeypatch.setattr(narration_audition, "load_asr", unloaded)
    monkeypatch.setattr(narration_audition, "load_aligner", unloaded)
    return {"root": root, "record": record, "cast": cast}


def other_narrator(cast: dict) -> None:
    """Put another narrator's reference recording in the edition's place, and its SHA-256 in
    the cast."""
    (repository.ROOT / Edition("en").places.reference).write_bytes(b"another narrator")
    cast.update(reference_sha256=sha256(b"another narrator"))


def rewrite(path, change) -> None:
    value = repository.read(path)
    change(value)
    repository.write(path, value)


@pytest.mark.parametrize(
    ("tamper", "error", "message"),
    [
        (
            lambda: rewrite(
                Edition("en").script,
                lambda script: script["segments"][0].update(
                    utterance_groups=["First thought.", " A new second thought."]
                ),
            ),
            ValueError,
            "26.2: the receipt does not hold the current thought",
        ),
        (lambda: repository.write("targets.json", {"26.3": "third"}), ValueError, "Every target"),
        (
            lambda: rewrite(
                RECEIPT,
                lambda receipt: receipt["records"][0]["utterance_groups"]["records"][1].update(
                    receipt_sha256="0" * 64
                ),
            ),
            RuntimeError,
            "Retained utterance input changed",
        ),
        (
            lambda: rewrite(Edition("en").cast, other_narrator),
            ValueError,
            "26: the recording's narrator reference differs from the cast",
        ),
        (
            lambda: (repository.ROOT / repository.read(RECEIPT)["records"][0]["path"]).write_bytes(
                b"changed"
            ),
            ValueError,
            "26: the recording differs from its receipt",
        ),
    ],
    ids=[
        "stale-thought",
        "unknown-target",
        "tampered-thought",
        "other-reference",
        "changed-recording",
    ],
)
def test_audition_refuses_before_loading_any_model(auditioned, tamper, error, message):
    tamper()
    # The audition reads the receipt where the narration writes it, named by no cast.
    with pytest.raises(error, match=message):
        narration_audition.audition("en", "targets.json")
    assert not (auditioned["root"] / narration_audition.AUDITIONS).exists()


def test_an_audition_without_the_dictionary_stops_before_any_model_loads(auditioned):
    (auditioned["root"] / narration_cmudict.PLACE).unlink()
    with pytest.raises(SystemExit, match="^en: The pinned CMUdict is missing .* filmkit.supply$"):
        narration_audition.audition("en", "targets.json")


def test_audition_preserves_existing_proposals(auditioned):
    repository.write(auditioned["root"] / narration_audition.AUDITIONS / "en/audition.json", [])
    with pytest.raises(FileExistsError, match="Preserve the existing proposals"):
        narration_audition.audition("en", "targets.json")


@pytest.mark.parametrize("retained_group_record", ["kept", "moved"], indirect=True)
def test_audition_records_each_take_with_its_waveform_hash(auditioned, monkeypatch, capsys):
    calls, seeds, heard = [], [], []

    class Voice:
        sample_rate = 24000

        def generate(self, **request):
            calls.append(request)
            yield SimpleNamespace(audio=np.full(30000, 0.2, dtype=np.float32))

    class Recognizer:
        def generate(self, path, *, language):
            heard.append((path, language))
            return SimpleNamespace(text=" Second thought.")

    class Aligner:
        def generate(self, _path, *, text, language):
            assert (text, language) == (" Second thought.", "English")
            words = [Aligned("Second", 0.1, 0.5), Aligned("thought", 0.5, 1.0)]
            return SimpleNamespace(items=words)

    identity = {"repo": "aligner", "revision": "r", "weights_sha256": "0" * 64}
    monkeypatch.setattr(narration_group_generation, "load_voice_model", Voice)
    monkeypatch.setattr(narration_group_generation.mx.random, "seed", seeds.append)
    monkeypatch.setattr(narration_audition, "load_asr", Recognizer)
    monkeypatch.setattr(
        narration_audition, "load_aligner", lambda: {"identity": identity, "model": Aligner()}
    )
    narration_audition.audition("en", "targets.json", takes=2, first=11)
    seed = auditioned["record"]["seed"]
    assert seeds == [seed + 11 * 7919, seed + 12 * 7919]
    assert [call["text"] for call in calls] == [" Second thought."] * 2
    # Each candidate is narrated from the edition's reference at its place, wherever the kept
    # take recorded it.
    place = str(auditioned["root"] / Edition("en").places.reference)
    assert [call["ref_audio"] for call in calls] == [place] * 2
    folder = auditioned["root"] / narration_audition.AUDITIONS / "en"
    (row,) = json.loads((folder / "audition.json").read_text())
    assert [take["seed"] for take in row["takes"]] == seeds
    assert heard == [(str(auditioned["root"] / take["path"]), "English") for take in row["takes"]]
    for take_row in row["takes"]:
        recording = auditioned["root"] / take_row["path"]
        assert take_row["wav_sha256"] == sha256(recording.read_bytes())
        assert (take_row["required_heard"], take_row["differing_units"]) == (True, 0)
        assert take_row["natural"] is False
        # Heard from its first sample up to its first aligned word, it has no onset to release.
        assert (take_row["onset_releasable"], take_row["clip_opens_quiet"]) == (False, False)
        # The thought holds no phrase end before its own.
        assert take_row["phrase_stops"] == []
        # Spoken without a pause, it is fluent, and it says no declared term.
        assert take_row["longest_unmarked_pause"] == {
            "thought": "26.2",
            "left": "Second",
            "right": "thought",
            "at": 0.5,
            "pause_s": 0.0,
            "marks": "",
            "switch": False,
            "limit_s": 0.4,
        }
        assert (take_row["fluent"], take_row["terms_pass"], take_row["term_occurrences"]) == (
            True,
            True,
            [],
        )
    assert row["proposed_seed"] is None
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["proposed"] == {"26.2": None}


@dataclasses.dataclass
class Aligned:
    """One aligned item, as the forced aligner returns it."""

    text: str
    start_time: float
    end_time: float


def dying(seconds: float, rate: int = 24000) -> np.ndarray:
    """A float voice that holds and then dies away over its last 0.3 s."""
    n, tail = round(seconds * rate), round(0.3 * rate)
    envelope = np.concatenate([np.ones(n - tail), np.exp(-np.arange(tail) / (0.03 * rate))])
    return (np.sin(2 * np.pi * 180 * np.arange(n) / rate) * 0.3 * envelope).astype(np.float32)


def test_a_run_on_target_is_read_on_into_the_next_thought_and_cut_before_it(
    auditioned, monkeypatch
):
    repository.write("targets.json", {"26.1": {"required": "first thought", "run_on": True}})
    quiet = np.zeros(2400, dtype=np.float32)
    whole = np.concatenate([quiet, dying(1.0), quiet, np.full(19200, 0.1, dtype=np.float32)])
    texts, aligned = [], []

    class Voice:
        sample_rate = 24000

        def generate(self, **request):
            texts.append(request["text"])
            yield SimpleNamespace(audio=whole)

    class Recognizer:
        def generate(self, *_, **__):
            return SimpleNamespace(text="First thought.")

    class Aligner:
        def generate(self, _path, *, text, language):
            aligned.append((text, language))
            words = [
                ("First", 0.1, 0.5),
                ("thought", 0.5, 1.0),
                ("Second", 1.2, 1.6),
                ("thought", 1.6, 1.9),
            ]
            # The cut take holds only its own thought.
            words = words if "Second" in text else words[:2]
            return SimpleNamespace(items=[Aligned(word, start, end) for word, start, end in words])

    identity = {"repo": "aligner", "revision": "r", "weights_sha256": "0" * 64}
    monkeypatch.setattr(narration_group_generation, "load_voice_model", Voice)
    monkeypatch.setattr(narration_group_generation.mx.random, "seed", lambda _: None)
    monkeypatch.setattr(narration_audition, "load_asr", Recognizer)
    monkeypatch.setattr(
        narration_audition, "load_aligner", lambda: {"identity": identity, "model": Aligner()}
    )
    narration_audition.audition("en", "targets.json", takes=1, first=11)
    assert texts == ["First thought. Second thought."]
    # The whole take locates the cut; the cut take is aligned again for its phrase ends.
    assert aligned == [
        ("First thought. Second thought.", "English"),
        ("First thought.", "English"),
    ]
    folder = auditioned["root"] / narration_audition.AUDITIONS / "en"
    (row,) = json.loads((folder / "audition.json").read_text())
    (taken,) = row["takes"]
    # Three quiet frames of 10 ms after the thought's aligned end at 1.0 s end the cut.
    cut = {"spoken_text": " Second thought.", "cut_sample": 24000 + 720}
    assert (row["run_on"], row["aligner"], taken["run_on"]) == (" Second thought.", identity, cut)
    assert taken["natural"] is True
    assert row["proposed_run_on"] == cut
    with wave.open(str(auditioned["root"] / taken["path"])) as source:
        assert source.getnframes() == cut["cut_sample"]
    assert (auditioned["root"] / taken["run_on_take"]["path"]).exists()


def declare_term(monkeypatch, thought: str) -> None:
    """Declare "Second" a Latin-script term whose English reference is said in a thought."""
    reference = {"en": {"thought": thought, "index": 0}}
    term = film.NarrationTerm(term="Second", spoken="Second", ipa="ˈsɛkənd", reference=reference)
    narration = film.Narration(terms=(term,))
    monkeypatch.setattr(
        narration_audition, "FILM", film.FILM.model_copy(update={"narration": narration})
    )


def test_an_audition_asks_for_the_term_before_it_loads_a_model(auditioned):
    # The pronunciation respells the name the second thought says; the film declares no term.
    rule = {"display": "Sekond", "spoken": "Second", "kind": "english-name"}
    repository.write(Edition("en").places.pronunciation, {"normalization": [rule]})
    with pytest.raises(SystemExit) as refused:
        narration_audition.audition("en", "targets.json")
    assert str(refused.value) == (
        "en: the normalization respells Sekond as Second, said in 26.2; declare Sekond in "
        "[[narration.terms]]"
    )
    assert not (auditioned["root"] / narration_audition.AUDITIONS).exists()


def test_a_reference_the_receipt_does_not_hold_refuses_before_any_model_loads(
    auditioned, monkeypatch
):
    declare_term(monkeypatch, "26.1")
    with pytest.raises(narration_terms.TermError, match="Second reference 26.1 #0 is not in"):
        narration_audition.audition("en", "targets.json")
    assert not (auditioned["root"] / narration_audition.AUDITIONS).exists()


def test_a_take_of_the_thought_that_holds_a_terms_reference_is_not_held_to_the_take_it_replaces(
    auditioned, monkeypatch
):
    declare_term(monkeypatch, "26.2")
    levels = iter((0.2, 0.3))

    class Voice:
        sample_rate = 24000

        def generate(self, **_request):
            yield SimpleNamespace(audio=np.full(30000, next(levels), dtype=np.float32))

    class Aligner:
        def generate(self, _path, *, text, language):
            assert (text, language) == (" Second thought.", "English")
            return SimpleNamespace(
                items=[Aligned("Second", 0.1, 0.5), Aligned("thought", 0.5, 1.0)]
            )

    # The receipt's thought take and the quieter take say one vowel and the louder take
    # another. Each take would itself be the reference once bound: neither is refused for it.
    def vowel(recording, _start, _end, _after=None):
        close = recording.mono.max() < 0.25
        return narration_terms.Vowel(250.0 if close else 650.0, 2750.0 if close else 2000.0, 6)

    identity = {"repo": "aligner", "revision": "r", "weights_sha256": "0" * 64}
    monkeypatch.setattr(narration_group_generation, "load_voice_model", Voice)
    monkeypatch.setattr(narration_group_generation.mx.random, "seed", lambda _: None)
    monkeypatch.setattr(
        narration_audition,
        "load_asr",
        lambda: SimpleNamespace(generate=lambda *_, **__: SimpleNamespace(text="Second thought.")),
    )
    monkeypatch.setattr(
        narration_audition, "load_aligner", lambda: {"identity": identity, "model": Aligner()}
    )
    monkeypatch.setattr(narration_terms, "first_vowel", vowel)
    narration_audition.audition("en", "targets.json", takes=2, first=11)
    folder = auditioned["root"] / narration_audition.AUDITIONS / "en"
    (row,) = json.loads((folder / "audition.json").read_text())
    said = [(take["terms_pass"], take["term_occurrences"]) for take in row["takes"]]
    occurrence = {"term": "Second", "index": 0, "at": 0.1, "reference": True, "frames": 6}
    assert said == [
        (True, [{**occurrence, "f1_hz": 250, "f2_hz": 2750, "passes": True}]),
        (True, [{**occurrence, "f1_hz": 650, "f2_hz": 2000, "passes": True}]),
    ]


def test_a_take_says_its_terms_against_the_reference_of_another_thought(monkeypatch):
    reference = film.TermReference(thought="26.2", index=1)
    term = film.NarrationTerm(
        term="Second", spoken="Second", ipa="ˈsɛkənd", reference={"en": reference}
    )
    forms = narration_terms.spoken_forms(term)
    standard = narration_terms.Standard(
        term, forms, reference, narration_terms.Vowel(250.0, 2750.0, 6)
    )
    words = [
        {"text": "Second", "start": 0.1, "end": 0.5},
        {"text": "thought", "start": 0.5, "end": 0.9},
        {"text": "Second", "start": 1.0, "end": 1.4},
        {"text": "time", "start": 1.4, "end": 1.8},
    ]
    opened = narration_terms.Vowel(650.0, 2000.0, 6)
    monkeypatch.setattr(narration_terms, "first_vowel", lambda *_: opened)
    # In another thought both occurrences are held to the reference's vowel and fail it.
    other = narration_terms.take_terms([standard], words, None, "26.1")
    assert [row["passes"] for row in other["term_occurrences"]] == [False, False]
    assert other["terms_pass"] is False
    # In the reference's own thought its occurrence is the standard to be, and the other is held.
    own = narration_terms.take_terms([standard], words, None, "26.2")
    assert [row["passes"] for row in own["term_occurrences"]] == [False, True]
    assert [row.get("reference", False) for row in own["term_occurrences"]] == [False, True]
    # A reference that shows no two formants is no reference: the gate asks two of it.
    monkeypatch.setattr(narration_terms, "first_vowel", lambda *_: None)
    assert narration_terms.take_terms([standard], words, None, "26.2")["terms_pass"] is False
