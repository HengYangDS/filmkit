"""A convergence at its edges: what it refuses, what it finds again, and what it asks its gates."""

import json
import signal
import wave

import numpy as np
import pytest
from converging import RATE, SEED, counts, placed, record_of, seed_of

import filmkit.child_processes as child_processes
import filmkit.narration.candidates as narration_candidates
import filmkit.narration.converge as narration_converge
import filmkit.narration.judgment as narration_judgment
import filmkit.repository as repository
from filmkit.production import Edition


def test_a_candidate_that_is_not_heard_to_say_its_text_is_refused_and_never_bound(
    studio, voiced, capsys
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced()
    # Every candidate ends naturally. The first is heard to say nothing and the second another
    # word; the third is heard to say its text in the recognizer's own spelling.
    studio.recognizer.heard = {
        f"26-02-{seed_of(11)}.wav": "",
        f"26-02-{seed_of(12)}.wav": "Second fought.",
        f"26-02-{seed_of(13)}.wav": "second, Thought",
    }
    narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "3"])
    (entry,) = record_of()["thoughts"]
    tried = [(take["differing_units_by_reading"], take["failed"]) for take in entry["candidates"]]
    assert tried == [(2, ["units"]), (1, ["units"]), (0, [])]
    bound = repository.read(Edition("en").cast)["retakes"]["26"]["groups"]["2"]
    assert bound["seed"] == seed_of(13)


def test_a_thought_whose_candidates_all_say_other_words_is_named_and_nothing_is_bound(
    studio, voiced
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced()
    studio.recognizer.heard = {f"26-02-{seed_of(k)}.wav": "Second fought." for k in (11, 12)}
    with pytest.raises(SystemExit, match="26.2: not narratable as written"):
        narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "2"])
    assert "retakes" not in repository.read(Edition("en").cast)
    (entry,) = record_of()["thoughts"]
    assert [take["failed"] for take in entry["candidates"]] == [["units"], ["units"]]


def test_a_run_asked_to_end_in_its_first_narration_says_so_and_names_no_thought(
    studio, voiced, monkeypatch
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced(natural=False)
    with pytest.raises(SystemExit):
        narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "1"])
    former = record_of()
    assert former["state"] == "ended" and "26.2" in former["unsettled"]

    def asked(_code: str) -> None:
        raise child_processes.Terminated(signal.SIGTERM)

    monkeypatch.setattr(narration_converge, "narration_due", lambda _code: True)
    monkeypatch.setattr(narration_converge, "narrate", asked)
    with pytest.raises(SystemExit) as left:
        narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "1"])
    assert left.value.code == 143
    # The record says that a run is under way and names no thought; what was found stays.
    record = record_of()
    assert (record["state"], record["unsettled"]) == ("running", {})
    assert record["thoughts"] == former["thoughts"]


def test_a_former_candidate_is_found_again_only_under_the_same_request(
    studio, voiced, monkeypatch, capsys
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced(natural=False)
    arguments = ["--language", "en", "--rounds", "1", "--takes", "2"]
    for generated, found in ((2, 0), (0, 2)):
        with pytest.raises(SystemExit):
            narration_converge.main(arguments)
        said = counts(capsys)
        assert (said["takes_generated"], said["takes_found"]) == (generated, found)
    (entry,) = record_of()["thoughts"]
    former = [take["request_sha256"] for take in entry["candidates"]]
    assert all(len(request) == 64 for request in former)
    # Another library decodes another take from the same seed: the recordings a former run left
    # are not judged for it, and each candidate is generated again under its new request.
    libraries = {**narration_candidates.LIBRARIES, "mlx-audio": "0.0.0"}
    monkeypatch.setattr(narration_candidates, "LIBRARIES", libraries)
    with pytest.raises(SystemExit):
        narration_converge.main(arguments)
    said = counts(capsys)
    assert (said["takes_generated"], said["takes_found"]) == (2, 0)
    (entry,) = record_of()["thoughts"]
    assert [take["request_sha256"] for take in entry["candidates"]] != former
    # A run-on is part of a candidate's request too.
    child = {"spoken_text": " Second thought.", "temperature": 0.9}
    plain = narration_candidates.request_sha256(child, seed_of(11), None)
    assert plain != narration_candidates.request_sha256(child, seed_of(11), " Next words.")


def test_a_run_on_take_whose_alignment_misses_its_text_is_a_refused_candidate(
    studio, voiced, capsys
):
    studio.begin([voiced(natural=False), voiced()])
    whole = "First thought. Second thought."
    studio.sound = lambda _seed, _text: voiced(seconds=3.0)
    # The aligner returns items for the first thought only: the thought cannot be found.
    studio.aligner.placed[whole] = [("First", 0.1, 0.5), ("thought", 0.5, 1.0)]
    with pytest.raises(SystemExit, match="26.1: not narratable as written"):
        narration_converge.main(["--language", "en", "--rounds", "0", "--takes", "1"])
    (entry,) = record_of()["thoughts"]
    (candidate,) = entry["candidates"]
    assert (candidate["kind"], candidate["run_on"]) == ("run-on", None)
    assert candidate["failed"] == ["ending", "phrase"]
    assert record_of()["state"] == "ended"


def test_a_candidate_of_one_second_or_less_is_refused_and_not_bound(studio, voiced):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced(seconds=0.8)
    studio.aligner.placed[" Second thought."] = [("Second", 0.15, 0.45), ("thought", 0.45, 0.8)]
    with pytest.raises(SystemExit, match="26.2: not narratable as written"):
        narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "1"])
    (candidate,) = record_of()["thoughts"][0]["candidates"]
    assert candidate["seconds"] <= 1.0 and candidate["failed"] == ["length"]
    assert "retakes" not in repository.read(Edition("en").cast)


def test_a_thought_first_refused_by_the_last_narration_is_named_with_no_candidate_tried(
    studio, voiced, monkeypatch
):
    studio.begin([voiced(natural=False), voiced()])
    whole = "First thought. Second thought."
    quiet = np.zeros(2400, dtype=np.int16)
    read_on = np.concatenate([voiced(seconds=1.0), quiet, np.full(19200, 3000, dtype=np.int16)])
    studio.sound = lambda _seed, text: read_on if text == whole else voiced(natural=False)
    studio.aligner.placed[whole] = [
        ("First", 0.1, 0.5),
        ("thought", 0.5, 1.0),
        ("Second", 1.2, 1.6),
        ("thought", 1.6, 1.9),
    ]
    narrate = narration_converge.narrate

    def narrate_and_move_a_sibling(code: str) -> None:
        # Stands in for any cause that makes another thought fail only now, as a declared
        # term's standard does when its reference thought was the one retaken.
        studio.first[1] = voiced(natural=False)
        narrate(code)

    monkeypatch.setattr(narration_converge, "narrate", narrate_and_move_a_sibling)
    with pytest.raises(SystemExit) as refused:
        narration_converge.main(["--language", "en", "--rounds", "0", "--takes", "1"])
    assert str(refused.value).splitlines() == [
        "en: 1 thoughts are unsettled",
        f"  26.2: {narration_converge.UNTRIED}; its take fails ending",
    ]
    record = record_of()
    assert record["unsettled"]["26.2"]["verdict"] == narration_converge.UNTRIED
    first, second = record["thoughts"]
    assert (first["thought"], first["settled"]) == ("26.1", True)
    assert (second["thought"], second["candidates"], second["settled"]) == ("26.2", [], False)
    assert first["chosen"] == [{"round": "run-on", "seed": seed_of(11), "kind": "run-on"}]


def test_a_thought_the_selections_gates_refuse_goes_to_the_next_round(studio, voiced, capsys):
    # The first take of the second thought holds 0.9 s of quiet after its first word. Aligned
    # alone, its words are placed before that quiet and it is fluent; the segment's own
    # alignment places its second word after the quiet, and the selection's gate refuses the
    # pause. The candidate speaks without a pause and passes both.
    halting = np.concatenate(
        [
            voiced(seconds=1.2),
            np.zeros(round(0.9 * RATE), dtype=np.int16),
            voiced(seconds=0.9, quiet_first=False),
        ]
    )
    studio.words = lambda record: placed(record, gap=1.9)
    studio.begin([voiced(), halting])
    studio.sound = lambda _seed, _text: voiced(seconds=3.0)
    narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "1"])
    (entry,) = record_of()["thoughts"]
    assert entry["first"] == {"seed": SEED, "failed": ["gate-pause"]}
    assert [take["failed"] for take in entry["candidates"]] == [[]]
    assert (entry["final"]["failed"], entry["settled"]) == ([], True)
    assert counts(capsys)["settled_after"] == {"first take": 1, "round 1": 2}
    judged = repository.read(Edition("en").ear_first / "judgment.json")
    assert judged["gates"] == "asked"
    assert [row["gate"] for row in judged["thoughts"]] == [[], []]


def test_the_choice_of_a_round_is_the_widest_margin_and_not_the_first_accepted(
    studio, voiced, monkeypatch
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced()
    wide = {seed_of(11): 0.1, seed_of(12): 0.3, seed_of(13): 0.2}
    monkeypatch.setattr(narration_judgment, "margin", lambda take: wide.get(take["seed"], 1.0))
    narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "3"])
    (entry,) = record_of()["thoughts"]
    assert [take["margin"] for take in entry["candidates"]] == [0.1, 0.3, 0.2]
    assert entry["chosen"] == [{"round": 1, "seed": seed_of(12), "kind": "plain"}]


def test_a_round_does_not_try_the_seed_the_thought_already_holds(studio, voiced):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda seed, _text: voiced(natural=seed == seed_of(12))
    cast = repository.read(Edition("en").cast)
    retake = {
        "seed": seed_of(11),
        "text_sha256": repository.content_sha(" Second thought."),
        "spoken_sha256": repository.content_sha(" Second thought."),
    }
    repository.write(Edition("en").cast, {**cast, "retakes": {"26": {"groups": {"2": retake}}}})
    # The receipt's take of the second thought is the one bound at k = 11, and it is refused.
    held = seed_of(11)
    studio.sound = lambda seed, _text: voiced(natural=seed == seed_of(12))
    (repository.ROOT / narration_converge.WORK / "en").mkdir(parents=True)
    with wave.open(
        str(repository.ROOT / narration_converge.WORK / "en" / f"26-02-{held}.wav"), "wb"
    ) as take:
        take.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        take.writeframes(voiced(natural=False).tobytes())
    narration_converge.narrate("en")
    studio.said.clear()
    narration_converge.main(["--language", "en", "--rounds", "1", "--takes", "2"])
    assert [seed for seed, _ in studio.said] == [seed_of(12)]


def test_the_narration_is_given_twice_the_time_it_may_itself_wait_for_its_children(
    monkeypatch, tmp_path, capsys
):
    waits = []
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.setattr(
        child_processes, "run", lambda command, **options: waits.append((command, options))
    )
    narration_converge.narrate("en")
    ((command, options),) = waits
    assert command[-4:] == ["-m", "filmkit.narration.narrate", "--language", "en"]
    assert options["seconds"] == 4 * child_processes.STOP_SECONDS
    assert json.loads(capsys.readouterr().out)["step"] == "narration"
