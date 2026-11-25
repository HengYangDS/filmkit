"""A narration that converges by itself: candidates, the choice, the binding and the record."""

import signal
from types import SimpleNamespace

import numpy as np
import pytest
from converging import (
    SEED,
    THOUGHTS,
    counts,
    measured_of,
    record_of,
    seed_of,
    thought_of,
    unmeasured,
)

import filmkit.child_processes as child_processes
import filmkit.narration.converge as narration_converge
import filmkit.narration.group_generation as narration_group_generation
import filmkit.narration.narrate as narration_narrate
import filmkit.narration.synthesis as narration_synthesis
import filmkit.repository as repository
from filmkit.graph import cli, runs
from filmkit.production import Edition

# The convergence's own narration, which runs a child and which the bench replaces (`studio`).
NARRATE = narration_converge.narrate
# The plan's own question whether a narration is ready, which the narration's fixtures answer.
JUDGED = narration_narrate.judged


def test_a_convergence_of_two_narrations_records_its_seconds_with_its_phases(
    studio, voiced, monkeypatch
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced()
    # A narration is due at first. Each narration runs where the convergence runs its child
    # and takes 20 s by the clock that the seam reads; the first has nothing to write
    # here, since the bench's receipt holds the first takes, and the second is the bench's.
    clock, due, ran, narrated = [100.0], iter([True]), [], narration_converge.narrate

    def child(command: list[str], **_how: object) -> None:
        clock[0] += 20.0
        ran.append(command[3])
        if len(ran) > 1:
            narrated("en")

    monkeypatch.setattr(runs, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(narration_converge, "narration_due", lambda _code: next(due, False))
    monkeypatch.setattr(narration_converge, "narrate", NARRATE)
    monkeypatch.setattr(child_processes, "run", child)
    cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "1"])
    assert (ran, studio.narrations) == (["filmkit.narration.narrate"] * 2, 1)
    record = measured_of()
    assert record["completed"] is True
    # Both narrations are one phase; the judgments, the round of candidates and the count of
    # the runtime are the others, in the order each first ran.
    assert [*record["phases"]] == ["narration", "judgment", "candidates", "count"]
    assert (record["phases"]["narration"], record["seconds"]) == (40.0, 40.0)


def test_filmkit_narrate_is_refused_before_any_model_loads_while_the_plan_holds_it(
    studio, voiced, monkeypatch
):
    # Below the studio's root the source check has no record, so the plan calls the narration,
    # which waits for the check, not ready.
    monkeypatch.setattr(narration_narrate, "judged", JUDGED)
    studio.begin([voiced(), voiced(natural=False)])
    with pytest.raises(SystemExit) as refused:
        cli.main(["narrate", "--edition", "en"])
    line = refused.value.code
    assert line.startswith("narrate:en is not ready, so it is not narrated: check: stale")
    assert line.endswith("(filmkit build check)") and "\n" not in line
    assert (studio.loads, studio.narrations) == (0, 0)
    assert not (repository.ROOT / Edition("en").ear_first / narration_converge.RECORD).exists()


def test_filmkit_narrate_converges_a_settled_narration_once_and_leaves_its_cast(count, studio):
    # The stand-in edition was narrated once from its settled cast (`count`): its receipt holds
    # every take the cast asks for, so the verb narrates nothing again, judges and counts.
    edition = Edition("en")
    sources = [repository.ROOT / edition.cast, repository.ROOT / edition.script]
    held = [path.read_bytes() for path in sources]
    cli.main(["narrate", "--edition", "en"])
    assert (studio.loads, studio.narrations) == (0, 0)
    assert [path.read_bytes() for path in sources] == held
    # The convergence's record states the run's seconds and phases.
    record = measured_of()
    assert record["completed"] is True and record["seconds"] >= 0
    assert [*record["phases"]] == ["judgment", "count"]


def test_filmkit_narrate_narrates_a_node_the_plan_calls_stale_though_no_take_is_due(
    count, studio, monkeypatch
):
    # The plan calls the narration stale, as after the next engine version or an edit of a
    # chapter's title, while the receipt holds every take the cast asks for: the verb narrates
    # once, so that the node's record is fresh after it, and leaves the cast as it is.
    monkeypatch.setattr(narration_narrate, "judged", lambda _code: (None, True))
    narrated = []
    monkeypatch.setattr(narration_converge, "narrate", narrated.append)
    edition = Edition("en")
    sources = [repository.ROOT / edition.cast, repository.ROOT / edition.script]
    held = [path.read_bytes() for path in sources]
    cli.main(["narrate", "--edition", "en"])
    assert (studio.loads, narrated) == (0, ["en"])
    assert [path.read_bytes() for path in sources] == held
    assert measured_of()["completed"] is True


def test_an_edition_left_unsettled_records_that_its_convergence_did_not_complete(studio, voiced):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced(natural=False)
    with pytest.raises(SystemExit, match="en: 1 thoughts are unsettled"):
        cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "1"])
    record = measured_of()
    # Nothing was bound, so nothing was narrated, and an unsettled edition is not counted.
    assert (record["completed"], [*record["phases"]]) == (False, ["judgment", "candidates"])


def test_a_refused_thought_gets_candidates_and_the_chosen_seed_is_bound(studio, voiced, capsys):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda seed, _text: voiced(natural=seed == seed_of(12))
    cli.main(["narrate", "--edition", "en", "--rounds", "2", "--takes", "3"])
    # One round: three candidates of the refused thought at the audition's seeds, one narration.
    assert studio.said == [(seed_of(k), " Second thought.") for k in (11, 12, 13)]
    assert studio.narrations == 1
    cast = repository.read(Edition("en").cast)
    assert cast["retakes"] == {
        "26": {
            "groups": {
                "2": {
                    "seed": seed_of(12),
                    "text_sha256": repository.content_sha(" Second thought."),
                    "spoken_sha256": repository.content_sha(" Second thought."),
                }
            }
        }
    }
    record = record_of()
    (entry,) = record["thoughts"]
    assert (entry["thought"], entry["first"]) == ("26.2", {"seed": SEED, "failed": ["ending"]})
    tried = [(take["round"], take["seed"], take["failed"]) for take in entry["candidates"]]
    assert tried == [
        (1, seed_of(11), ["ending"]),
        (1, seed_of(12), []),
        (1, seed_of(13), ["ending"]),
    ]
    assert entry["chosen"] == [{"round": 1, "seed": seed_of(12), "kind": "plain"}]
    assert (entry["final"], entry["settled"]) == ({"seed": seed_of(12), "failed": []}, True)
    assert (record["state"], record["unsettled"]) == ("ended", {})
    said = counts(capsys)
    assert said["settled_after"] == {"first take": 1, "round 1": 2}
    assert (said["takes_generated"], said["takes_found"], said["unsettled"]) == (3, 0, {})
    # A second run changes nothing: no take, no narration, the same cast and the same record
    # but the measurement of its run.
    kept = [unmeasured(record_of())]
    kept.append((repository.ROOT / Edition("en").cast).read_bytes())
    cli.main(["narrate", "--edition", "en", "--rounds", "2", "--takes", "3"])
    assert (len(studio.said), studio.narrations) == (3, 1)
    assert kept[0] == unmeasured(record_of())
    assert kept[1] == (repository.ROOT / Edition("en").cast).read_bytes()
    assert counts(capsys)["settled_after"] == {"first take": 2}


def test_a_thought_no_candidate_settles_is_named_as_not_narratable_as_written(
    studio, voiced, capsys
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced(natural=False)
    with pytest.raises(SystemExit) as refused:
        cli.main(["narrate", "--edition", "en", "--rounds", "2", "--takes", "2"])
    lines = str(refused.value).splitlines()
    assert lines[:2] == [
        "en: 1 thoughts are unsettled",
        "  26.2: not narratable as written; its take fails ending",
    ]
    assert lines[2:6] == [
        f"    plain candidate {seed_of(k)}: fails ending" for k in (11, 12, 13, 14)
    ]
    # The last thought of the film has nothing to be read on into, and the refusal says so.
    assert lines[6].startswith("    no run-on candidate: ") and len(lines) == 7
    record = record_of()
    assert record["unsettled"] == {
        "26.2": {"failed": ["ending"], "verdict": "not narratable as written"}
    }
    (entry,) = record["thoughts"]
    assert "no_run_on" in entry and entry["chosen"] == [] and entry["settled"] is False
    assert [take["round"] for take in entry["candidates"]] == [1, 1, 2, 2]
    assert "retakes" not in repository.read(Edition("en").cast)
    assert studio.narrations == 0
    assert counts(capsys)["takes_generated"] == 4
    # Asked again, it judges the candidates it left and generates none.
    with pytest.raises(SystemExit):
        cli.main(["narrate", "--edition", "en", "--rounds", "2", "--takes", "2"])
    said = counts(capsys)
    assert (said["takes_generated"], said["takes_found"], len(studio.said)) == (0, 4, 4)
    assert unmeasured(record_of()) == unmeasured(record)


def test_a_run_on_take_settles_a_thought_whose_plain_candidates_end_abruptly(
    studio, voiced, capsys
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
    cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "2"])
    (entry,) = record_of()["thoughts"]
    assert [(take["kind"], take["k"], take["failed"]) for take in entry["candidates"]] == [
        ("plain", 11, ["ending"]),
        ("plain", 12, ["ending"]),
        ("run-on", 13, []),
        ("run-on", 14, []),
    ]
    assert entry["chosen"] == [{"round": "run-on", "seed": seed_of(13), "kind": "run-on"}]
    bound = repository.read(Edition("en").cast)["retakes"]["26"]["groups"]["1"]
    assert bound["seed"] == seed_of(13)
    assert bound["run_on"]["spoken_text"] == " Second thought."
    assert entry["settled"] is True
    assert counts(capsys)["settled_after"] == {"first take": 1, "round 1": 1, "run-on": 2}


def test_a_narration_is_due_only_while_the_receipt_lacks_what_the_cast_asks_for(
    studio, voiced, monkeypatch
):
    monkeypatch.undo()
    paths = narration_converge.evidence_paths("en")
    job = SimpleNamespace(segment={"id": "26"}, fingerprint="f" * 64)
    retained = iter([None, {}, {}, {}, {}, {}])
    patch = pytest.MonkeyPatch()
    patch.setattr(repository, "ROOT", studio.root)
    patch.setattr(narration_synthesis, "load_request", lambda _argv: None)
    patch.setattr(narration_synthesis, "speech_plan", lambda _request: [job])
    patch.setattr(narration_synthesis, "reuse_or_refuse", lambda _job: next(retained))

    def receipt(fingerprint: str) -> None:
        record = {"id": "26", "fingerprint": fingerprint, "wav_sha256": "a" * 64}
        repository.write(paths["receipt"], {"records": [record]})

    def checks(**digests: str) -> None:
        for name in ("alignment", "asr"):
            row = {"id": "26", "wav_sha256": digests.get(name, "a" * 64)}
            repository.write(paths[name], {"records": [row]})

    try:
        # A segment without a retained recording; a receipt without its checks; a receipt of
        # another request; a check's output of the recordings before; and then nothing to do.
        assert narration_converge.narration_due("en") is True
        assert narration_converge.narration_due("en") is True
        checks()
        receipt("0" * 64)
        assert narration_converge.narration_due("en") is True
        receipt("f" * 64)
        checks(alignment="b" * 64)
        assert narration_converge.narration_due("en") is True
        checks(asr="b" * 64)
        assert narration_converge.narration_due("en") is True
        checks()
        assert narration_converge.narration_due("en") is False
    finally:
        patch.undo()


def test_a_run_on_take_without_a_cut_is_refused_and_judged_again_from_its_whole_take(
    studio, voiced, capsys
):
    studio.begin([voiced(natural=False), voiced()])
    # Read on, the voice never falls quiet before the next words: no cut, whatever a release says.
    studio.sound = lambda _seed, _text: voiced(natural=False, seconds=3.0)
    for generated, found in ((2, 0), (0, 2)):
        with pytest.raises(SystemExit, match="26.1: not narratable as written; its take fails"):
            cli.main(["narrate", "--edition", "en", "--rounds", "0", "--takes", "2"])
        said = counts(capsys)
        assert (said["takes_generated"], said["takes_found"]) == (generated, found)
    (entry,) = record_of()["thoughts"]
    assert [(take["kind"], take["run_on"], take["failed"]) for take in entry["candidates"]] == [
        ("run-on", None, ["ending"]),
        ("run-on", None, ["ending"]),
    ]
    assert all(take["path"].endswith("-on-run-on.wav") for take in entry["candidates"])


def test_a_convergence_asked_to_end_while_it_narrates_says_so_and_binds_nothing_more(
    studio, voiced, monkeypatch, capsys
):
    studio.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced()

    def asked(code: str) -> None:
        raise child_processes.Terminated(signal.SIGTERM)

    monkeypatch.setattr(narration_converge, "narrate", asked)
    with pytest.raises(SystemExit) as left:
        cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "1"])
    # One line, and the status a shell gives a command that SIGTERM ended.
    assert left.value.code == 143
    assert capsys.readouterr().err == (
        "The convergence was stopped by a request to end (SIGTERM); what it was running was "
        "ended with it\n"
    )
    # The choice it had bound stands in the cast; the next run narrates it and goes on.
    assert repository.read(Edition("en").cast)["retakes"]["26"]["groups"]["2"]["seed"] == seed_of(
        11
    )
    record = record_of()
    assert (record["state"], record["unsettled"]) == ("running", {})
    assert [take["seed"] for take in record["thoughts"][0]["candidates"]] == [seed_of(11)]


def test_rounds_count_their_seeds_on_and_settle_each_thought_where_a_take_is_accepted(
    studio, voiced, capsys
):
    studio.begin([voiced(natural=False), voiced(natural=False)])
    accepted = {("First thought.", seed_of(11)), (" Second thought.", seed_of(15))}
    studio.sound = lambda seed, text: voiced(natural=(text, seed) in accepted)
    cli.main(["narrate", "--edition", "en", "--rounds", "2", "--takes", "3"])
    # Round 1 tries both thoughts at k = 11 to 13 and settles the first; round 2 tries the
    # second alone at k = 14 to 16.
    assert [(text, seed) for seed, text in studio.said] == [
        *[("First thought.", seed_of(k)) for k in (11, 12, 13)],
        *[(" Second thought.", seed_of(k)) for k in (11, 12, 13, 14, 15, 16)],
    ]
    groups = repository.read(Edition("en").cast)["retakes"]["26"]["groups"]
    assert {index: retake["seed"] for index, retake in groups.items()} == {
        "1": seed_of(11),
        "2": seed_of(15),
    }
    first, second = record_of()["thoughts"]
    assert first["chosen"] == [{"round": 1, "seed": seed_of(11), "kind": "plain"}]
    assert second["chosen"] == [{"round": 2, "seed": seed_of(15), "kind": "plain"}]
    assert [take["round"] for take in second["candidates"]] == [1, 1, 1, 2, 2, 2]
    assert counts(capsys)["settled_after"] == {"first take": 0, "round 1": 1, "round 2": 2}
    # Each narration starts its own processes, so the voice is let go before it and loaded
    # again for the round that follows.
    assert (studio.narrations, studio.loads) == (2, 2)


def test_the_engines_own_narration_says_the_candidate_it_was_bound_to(engine, voiced, capsys):
    # Nothing is narrated yet: the convergence finds a narration due and starts it.
    assert narration_converge.narration_due("en") is True
    refused = voiced(natural=False)
    accepted = voiced(seconds=2.5)
    engine.sound = lambda seed, text: (
        voiced() if text == THOUGHTS[0] else accepted if seed == engine.wanted else refused
    )
    engine.wanted = None
    narration_converge.narrate("en")
    segment_seed = repository.read(engine.paths["receipt"])["records"][0]["seed"]
    engine.wanted = segment_seed + 12 * narration_converge.STRIDE
    engine.said.clear()
    engine.narrations = 0
    cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "2"])
    # Two candidates of the refused thought, then one narration of its segment from the cast:
    # the first thought again at its own seed, the second at the seed that was bound.
    said = [(text, seed) for seed, text in engine.said]
    first_seed = said[2][1]
    assert said == [
        (THOUGHTS[1], segment_seed + 11 * narration_converge.STRIDE),
        (THOUGHTS[1], engine.wanted),
        (THOUGHTS[0], first_seed),
        (THOUGHTS[1], engine.wanted),
    ]
    assert engine.narrations == 1
    (entry,) = record_of()["thoughts"]
    chosen = next(take for take in entry["candidates"] if take["seed"] == engine.wanted)
    # The narrated take is the candidate that was judged, sample for sample.
    assert thought_of(2)["seed"] == engine.wanted
    assert thought_of(2)["wav_sha256"] == chosen["wav_sha256"]
    assert (entry["final"], entry["settled"]) == ({"seed": engine.wanted, "failed": []}, True)
    # The receipt now holds what the cast asks for, with both checks of it: nothing is due,
    # and a second run narrates and generates nothing.
    assert narration_converge.narration_due("en") is False
    cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "2"])
    assert (engine.narrations, len(engine.said)) == (1, 4)
    assert counts(capsys)["settled_after"] == {"first take": 2}


def test_a_narration_ended_inside_a_thought_is_named_by_its_file_and_not_replayed(
    engine, voiced, capsys
):
    engine.sound = lambda _seed, text: voiced(natural=text == THOUGHTS[0])
    narration_converge.narrate("en")
    segment_seed = repository.read(engine.paths["receipt"])["records"][0]["seed"]
    bound = segment_seed + 11 * narration_converge.STRIDE
    engine.sound = lambda seed, text: voiced(natural=text == THOUGHTS[0] or seed == bound)
    # The narration that follows the round is asked to end while it says the retaken thought.
    engine.said.clear()
    original = narration_group_generation.synthesize

    def stopping(model, text, *rest):
        # The candidate was generated; its second synthesis is the narration's.
        if text == THOUGHTS[1] and [said for _, said in engine.said].count(THOUGHTS[1]) >= 1:
            raise child_processes.Terminated(signal.SIGTERM)
        return original(model, text, *rest)

    patch = pytest.MonkeyPatch()
    patch.setattr(narration_group_generation, "synthesize", stopping)
    try:
        with pytest.raises(SystemExit) as left:
            cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "1"])
    finally:
        patch.undo()
    assert left.value.code == 143
    capsys.readouterr()
    record = record_of()
    assert (record["state"], record["unsettled"]) == ("running", {})
    cast = repository.read(Edition("en").cast)
    assert cast["retakes"]["26"]["groups"]["2"]["seed"] == bound
    # The thought's request stands at `started` with no recording. The next run names the
    # file and starts nothing: the engine refuses to replay an unresolved utterance.
    (left_file,) = narration_converge.leftovers("en")
    assert left_file.endswith(".request.json")
    engine.narrations = 0
    with pytest.raises(SystemExit) as refused:
        cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "1"])
    message = str(refused.value)
    assert "Unresolved native utterance; inspect before replay" in message
    assert message.splitlines()[-1] == f"  {left_file}"
    assert engine.narrations == 0
    # Once the leftover is inspected and removed, the run narrates what the cast holds and
    # goes on: the bound seed gives the accepted take.
    (repository.ROOT / left_file).unlink()
    cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "1"])
    final = record_of()
    assert (final["state"], final["unsettled"]) == ("ended", {})
    assert thought_of(2)["seed"] == bound


def clarity_by_take(monkeypatch, values: dict) -> None:
    """Declare an 18.0 dB floor and thought line, and read each take's clarity by its seed or
    its thought's place, `values` mapping either to dB, 18.4 for any other."""
    import filmkit.film as film
    import filmkit.narration.judgment as narration_judgment

    review = film.FILM.review.model_copy(
        update={"clarity_minimum_db": {"zh": 18.0, "en": 18.0}, "clarity_thought_margin_db": 0}
    )
    monkeypatch.setattr(
        narration_judgment, "FILM", narration_judgment.FILM.model_copy(update={"review": review})
    )

    def take_clarity(path, _floor):
        fields = path.stem.split("-")
        key = int(fields[-1]) if fields[0] == "26" else int(fields[0])
        value = values.get(key, 18.4)
        return {"cpp_db": value, "below_floor": value < 18.0}

    monkeypatch.setattr(narration_judgment, "take_clarity", take_clarity)


def test_a_thought_under_its_line_heard_by_no_one_gets_no_candidate_and_waits(
    studio, voiced, monkeypatch, capsys
):
    studio.begin([voiced(), voiced()])
    clarity_by_take(monkeypatch, {2: 17.4})

    def generated(*_args, **_kwargs):
        pytest.fail("A thought for the ear gets no candidate")

    monkeypatch.setattr(narration_group_generation, "load_voice_model", generated)
    with pytest.raises(SystemExit) as waiting:
        cli.main(["narrate", "--edition", "en", "--rounds", "2", "--takes", "3"])
    record = record_of()
    second = thought_of(2)
    assert record["unsettled"] == {}
    assert record["for_the_ear"] == {
        "26.2": {
            "path": second["path"],
            "wav_sha256": second["wav_sha256"],
            "cpp_db": 17.4,
            "line_db": 18.0,
        }
    }
    assert str(waiting.value).splitlines() == [
        "en: 1 of 2 thoughts wait for the owner's ear",
        f"  26.2: {second['path']} ({second['wav_sha256']}) reads 17.4 dB, under its line of "
        "18.0 dB",
    ]
    said = counts(capsys)
    assert (said["takes_generated"], said["for_the_ear"]) == (0, ["26.2"])
    assert said["fit"] == "not asked: a thought waits for the owner's ear"
    assert (measured_of()["completed"], studio.said) == (False, [])


def test_a_thought_under_its_line_that_another_line_refuses_gets_candidates(
    studio, voiced, monkeypatch, capsys
):
    studio.begin([voiced(), voiced(natural=False)])
    # The first take of 26.2 ends abruptly and reads 17.4 dB: its ending refuses it. The three
    # candidates end naturally; the second reads clearest, the third under the line.
    seeds = {seed_of(11): 18.2, seed_of(12): 18.9, seed_of(13): 17.6}
    clarity_by_take(monkeypatch, {2: 17.4, **seeds})
    studio.sound = lambda _seed, _text: voiced()
    with pytest.raises(SystemExit):
        cli.main(["narrate", "--edition", "en", "--rounds", "1", "--takes", "3"])
    (entry,) = record_of()["thoughts"]
    assert entry["first"]["failed"] == ["ending"]
    # The convergence chooses by its margins as before: the clearest candidate is bound. Its
    # narrated take stands at the thought's place, whose clarity the stand-in reads at 17.4 dB,
    # so the thought then waits for the ear.
    assert entry["chosen"] == [{"round": 1, "seed": seed_of(12), "kind": "plain"}]
    assert [take["failed"] for take in entry["candidates"]] == [[], [], []]
    assert list(record_of()["for_the_ear"]) == ["26.2"]
    # A thought that waits for the ear is not settled, in the record or in the counts.
    assert entry["settled"] is False
    assert counts(capsys)["settled_after"] == {"first take": 1, "round 1": 1}
