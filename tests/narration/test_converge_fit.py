"""A settled narration is asked whether its edition fits the runtime: what the convergence asks
of the assembly's count, what it says of a miss, and what it leaves."""

import json
from pathlib import Path

import pytest
from converging import (
    MISS,
    PERFORMANCE,
    RANGE,
    converge,
    counts,
    duration_of,
    duration_path,
    record_of,
    refused,
    seed_of,
)

import filmkit.child_processes as child_processes
import filmkit.narration.converge as narration_converge
import filmkit.narration.fitting as fitting
import filmkit.repository as repository
import filmkit.soundtrack.fit as soundtrack_fit
from filmkit.production import Edition
from filmkit.soundtrack.assembly import AssemblyError
from filmkit.specification import RATE


def kept() -> dict[str, bytes]:
    """Every file below the film's root with its bytes, but the duration records: a duration
    differs from run to run, and no record binds it."""
    return {
        path.relative_to(repository.ROOT).as_posix(): path.read_bytes()
        for path in sorted(repository.ROOT.rglob("*"))
        if path.is_file() and path.parent != duration_path().parent
    }


def test_the_convergence_s_duration_record_says_whether_the_edition_ended_fit(count):
    converge()
    record = duration_of()
    assert (record["command"], record["completed"]) == ("converge", True)
    # Nothing was due and nothing refused: the run judged and counted.
    assert [*record["phases"]] == ["judgment", "count"]
    # It is the one duration record that the command writes.
    assert [*duration_path().parent.iterdir()] == [duration_path()]
    # A miss, and an edition with room that the allocation refuses, did not complete.
    count.free = -0.1
    assert refused().startswith(MISS)
    assert (duration_of()["completed"], [*duration_of()["phases"]]) == (
        False,
        ["judgment", "count"],
    )
    count.free, count.refusal = 0.8, "The gaps cannot hold the runtime that is left"
    assert refused().startswith("en: the settled narration is refused by the assembly: ")
    assert duration_of()["completed"] is False


# What may stand in the place of a former run's record that no run can go on from: its text,
# or None for a folder.
DAMAGED = {
    "a former record that is no JSON": "{",
    "a former record whose thoughts are a number": '{"thoughts": 3}',
    "a former record whose thoughts are null": '{"thoughts": null}',
    "a former record whose thoughts are a text": '{"thoughts": "26.2"}',
    "a former thought that is an empty object": '{"thoughts": [{}]}',
    "a former thought without its spoken text": '{"thoughts": [{"thought": "26.2"}]}',
    "a former thought whose name is a list": (
        '{"thoughts": [{"thought": ["26.2"], "spoken_sha256": "0"}]}'
    ),
    "a folder in the former record's place": None,
}


def staged(refusal: str) -> str:
    """Stage what refuses a convergence before its first effect; what its refusal begins with."""
    edition, paths = Edition("en"), narration_converge.evidence_paths("en")
    cast, script = repository.read(edition.cast), repository.read(edition.script)
    if refusal == "a negative reserve":
        repository.write(edition.cast, {**cast, "runtime_fit": {"reserve_seconds": -0.1}})
        return "en: the cast's runtime_fit declares reserve_seconds, a number of seconds from 0"
    if refusal == "a refused pause policy":
        del script["voice_performance"]["thought_pause_range"]
        repository.write(edition.script, script)
        return "en: the script's pause policy is refused: thought_pause_range requires"
    if refusal == "another receipt":
        declared = {**cast["performance_recording"], "receipt": "elsewhere/receipt.json"}
        repository.write(edition.cast, {**cast, "performance_recording": declared})
        return "en: the cast declares the receipt elsewhere/receipt.json, and a convergence"
    if refusal in DAMAGED:
        former = edition.ear_first / narration_converge.RECORD
        former.unlink()
        if DAMAGED[refusal] is None:
            former.mkdir()
        else:
            former.write_text(DAMAGED[refusal])
        return "en: the record that a former run left cannot be read: "
    repository.write(f"{paths['folder']}/26/26-02.request.json", {"state": "started"})
    return "en: a narration was ended inside a thought and left its request started"


@pytest.mark.parametrize(
    "refusal",
    [
        "a negative reserve",
        "a refused pause policy",
        "another receipt",
        *DAMAGED,
        "a leftover request",
    ],
)
def test_a_convergence_refused_before_its_first_effect_writes_no_duration_record(count, refusal):
    record = duration_path()
    # The convergence that narrated the standing build wrote its record.
    converge()
    standing = record.read_bytes()
    begins = staged(refusal)
    with pytest.raises(SystemExit) as refusing:
        converge()
    assert str(refusing.value).startswith(begins)
    # The refusal leaves that record byte for byte, and writes none where none stands.
    assert record.read_bytes() == standing
    record.unlink()
    with pytest.raises(SystemExit, match="^en: "):
        converge()
    assert not record.exists()


def test_the_former_record_is_read_among_the_checks_and_by_nothing_in_the_run(count, monkeypatch):
    converge()
    checked = narration_converge.admitted("en")
    read = {"read": repository.read, "read_entry": repository.read_entry}

    def unread(reader):
        def reading(path, *more):
            if Path(path).name == narration_converge.RECORD:
                pytest.fail("the former record is read inside the run")
            return reader(path, *more)

        return reading

    for name, reader in read.items():
        monkeypatch.setattr(repository, name, unread(reader))
    # The run goes on from the record that the checks read, and reads the file no second time.
    ended = narration_converge.converge("en", *checked)
    assert (ended["state"], ended["fit"]["verdict"]) == ("ended", "fits")


def test_a_settled_edition_that_fits_states_the_seconds_free(count, studio, capsys):
    before = kept()
    converge()
    record = record_of()
    assert record["fit"] == {
        "asked": True,
        "reserve_seconds": 0.0,
        "free_seconds": 0.8,
        "verdict": "fits",
    }
    assert (record["state"], record["unsettled"]) == ("ended", {})
    printed = capsys.readouterr().out
    said = json.loads(printed.splitlines()[-1])
    assert (said["fit"], said["free_seconds"]) == ("fits", 0.8)
    # The count was asked once, of the selection, and the selection's own line is not printed.
    assert (count.selected, count.bound, count.tried) == (1, 1, [0.45])
    assert '"selected"' not in printed
    # It generated and narrated nothing and wrote the two records beside the receipt alone:
    # no take, no cast, no script.
    assert (studio.said, studio.narrations) == ([], 0)
    after = kept()
    assert {name for name in after if after[name] != before.get(name)} == {
        "build/evidence/editions/en/ear-first/convergence.json",
        "build/evidence/editions/en/ear-first/judgment.json",
    }
    # A second run asks again and writes the same record: nothing is kept between runs.
    converge()
    assert (count.selected, count.bound, kept()) == (2, 2, after)
    assert counts(capsys)["fit"] == "fits"


def test_a_miss_names_the_seconds_missing_and_the_pause_that_would_fit(count, capsys):
    count.free = -0.1
    cast = (repository.ROOT / Edition("en").cast).read_bytes()
    script = (repository.ROOT / Edition("en").script).read_bytes()
    line = refused()
    # Each 0.01 s off the two thought joins frees 0.02 s of the 0.10 s that are missing.
    assert line == f"{MISS}0.10 s; a thought pause of 0.4 s, {RANGE}, would fit with 0.00 s free"
    record = record_of()
    assert record["fit"] == {
        "asked": True,
        "reserve_seconds": 0.0,
        "free_seconds": -0.1,
        "verdict": "misses",
        "missing_seconds": 0.1,
        "pause": {
            "declared_seconds": 0.45,
            "range_seconds": [0.3, 0.6],
            "reserve_seconds": 0.0,
            "fits_at_seconds": 0.4,
            "free_seconds": 0.0,
        },
    }
    assert (record["state"], counts(capsys)["fit"]) == ("ended", "misses")
    # The pause is named and not applied: the script and the cast are as they were.
    assert (repository.ROOT / Edition("en").cast).read_bytes() == cast
    assert (repository.ROOT / Edition("en").script).read_bytes() == script
    # The pause it names was counted and fits, and the step above it was counted and does not.
    assert {0.4, 0.41} <= set(count.tried)
    # A second run says the same line and writes the same record.
    files = kept()
    assert (refused(), kept()) == (line, files)


@pytest.mark.parametrize(
    ("frames", "missing"),
    [(-1, "0.000021"), (-48, "0.0010"), (-240, "0.01")],
)
def test_a_miss_is_compared_as_it_is_counted_and_never_said_as_no_seconds(count, frames, missing):
    count.free = frames / RATE
    line = refused()
    assert line.startswith(f"{MISS}{missing} s; a thought pause of 0.44 s, ")
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["free_seconds"], fit["missing_seconds"]) == (
        "misses",
        frames / RATE,
        -frames / RATE,
    )


@pytest.mark.parametrize("reserve", [None, 0, 0.0])
def test_an_exact_fit_fits_with_no_reserve_or_one_of_nothing(count, capsys, reserve):
    count.free = 0.0
    if reserve is not None:
        cast = repository.read(Edition("en").cast)
        repository.write(Edition("en").cast, {**cast, "runtime_fit": {"reserve_seconds": reserve}})
    converge()
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["free_seconds"]) == ("fits", 0.0)
    assert counts(capsys)["fit"] == "fits"


@pytest.mark.parametrize(
    ("least", "missing", "named"), [(0.3, 0.1, "0.4"), (0.30405, 0.1, "0.39405")]
)
def test_the_pause_that_is_printed_fits_when_the_script_declares_it(count, least, missing, named):
    count.declare(thought_pause_range=[least, 0.6])
    count.free = -missing
    line = refused()
    assert f"; a thought pause of {named} s, " in line
    # The film declares the pause as the line prints it, and the edition then fits.
    printed = float(line.split("a thought pause of ")[1].split(" s,")[0])
    pauses = {**PERFORMANCE["designed_pauses"], "thought": printed}
    count.declare(designed_pauses=pauses)
    converge()
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["free_seconds"] >= 0) == ("fits", True)
    # One step more would not have fitted.
    count.declare(designed_pauses={**pauses, "thought": round(printed + 0.01, 6)})
    assert refused().startswith(MISS)


def test_a_miss_that_no_pause_of_the_range_closes_names_the_range(count):
    # The range's least pause, 0.3 s, frees 0.30 s of the 0.40 s that are missing.
    count.free = -0.4
    assert refused() == (
        f"{MISS}0.40 s; no thought pause of the declared range, 0.3 to 0.6 s, fits: "
        "at 0.3 s it still misses by 0.10 s"
    )
    pause = record_of()["fit"]["pause"]
    assert (pause["fits_at_seconds"], pause["tried_seconds"], pause["free_seconds"]) == (
        None,
        0.3,
        -0.1,
    )


def test_a_range_of_one_value_holds_no_shorter_pause(count):
    count.declare(thought_pause_range=[0.45, 0.45])
    count.free = -0.1
    assert refused() == (
        f"{MISS}0.10 s; no thought pause of the declared range, 0.45 to 0.45 s, fits: "
        "at 0.45 s it still misses by 0.10 s"
    )


def test_a_declared_reserve_must_stay_free_and_the_pause_named_leaves_it(count):
    cast = repository.read(Edition("en").cast)
    repository.write(Edition("en").cast, {**cast, "runtime_fit": {"reserve_seconds": 0.05}})
    # The allocation accepts the edition, which leaves 0.02 s free where 0.05 s must be.
    count.free = 0.02
    assert refused() == (
        f"{MISS}0.03 s, the declared reserve of 0.05 s included; a thought pause of 0.43 s, "
        f"{RANGE}, would fit with 0.06 s free"
    )
    fit = record_of()["fit"]
    assert (fit["reserve_seconds"], fit["free_seconds"], fit["verdict"]) == (0.05, 0.02, "misses")
    assert fit["pause"]["free_seconds"] >= 0.05
    # With the reserve free the edition fits.
    count.free = 0.05
    converge()
    assert record_of()["fit"]["verdict"] == "fits"


def test_a_missed_reserve_is_a_miss_though_the_allocation_refuses_the_edition_too(count):
    cast = repository.read(Edition("en").cast)
    repository.write(Edition("en").cast, {**cast, "runtime_fit": {"reserve_seconds": 0.05}})
    # The count leaves 0.02 s free where 0.05 s must be, and the allocation refuses the edition
    # at every pause: the miss is said first, and the refusal with the largest pause with room.
    count.free, count.refusal = 0.02, "The gaps cannot hold the runtime that is left"
    assert refused() == (
        f"{MISS}0.03 s, the declared reserve of 0.05 s included; no thought pause of the "
        "declared range, 0.3 to 0.6 s, fits: at 0.43 s the assembly refuses it: The gaps "
        "cannot hold the runtime that is left"
    )
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["free_seconds"]) == ("misses", 0.02)
    assert fit["missing_seconds"] == pytest.approx(0.03, abs=1e-9)
    assert (fit["pause"]["tried_seconds"], fit["pause"]["free_seconds"]) == (0.43, 0.06)


def test_a_pause_reading_that_is_refused_leaves_the_miss_said(count, monkeypatch):
    count.free = -0.1

    def refuse(_edition: Edition, _reserve: float) -> dict:
        raise AssemblyError("Selected recording waveform differs: 26")

    monkeypatch.setattr(soundtrack_fit, "thought_pause_to_fit", refuse)
    assert refused() == (
        f"{MISS}0.10 s; the thought pause that would fit could not be read: Selected recording "
        "waveform differs: 26"
    )
    assert record_of()["state"] == "ended"


def test_with_a_thought_unsettled_the_count_is_not_asked(bench, studio, voiced):
    count = bench
    count.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced(natural=False)
    with pytest.raises(SystemExit, match="en: 1 thoughts are unsettled"):
        converge("--rounds", "1", "--takes", "1")
    record = record_of()
    assert record["fit"] == {"asked": False, "why": "not asked: thoughts are unsettled"}
    assert (list(record["unsettled"]), count.selected, count.bound) == (["26.2"], 0, 0)


def test_the_count_is_asked_of_the_edition_that_the_rounds_settled(
    bench, studio, voiced, monkeypatch, capsys
):
    count = bench
    count.begin([voiced(), voiced(natural=False)])
    studio.sound = lambda _seed, _text: voiced()
    narrate = narration_converge.narrate

    def narrated(code: str) -> None:
        # The stand-in narration writes the script anew; the film's declarations stand.
        narrate(code)
        count.declare()

    monkeypatch.setattr(narration_converge, "narrate", narrated)
    converge("--rounds", "1", "--takes", "1")
    record = record_of()
    assert record["thoughts"][0]["final"] == {"seed": seed_of(11), "failed": []}
    assert (record["fit"]["verdict"], count.selected, studio.narrations) == ("fits", 1, 1)
    assert counts(capsys)["settled_after"] == {"first take": 1, "round 1": 2}


def test_an_edition_that_declares_nothing_to_count_is_not_asked(count, capsys):
    edition, paths = Edition("en"), narration_converge.evidence_paths("en")
    script = repository.read(edition.script)
    repository.write(edition.script, {**script, "voice_performance": {}})
    converge()
    why = "not asked: the script declares no pause policy (voice_performance)"
    assert (record_of()["fit"], counts(capsys)["fit"]) == ({"asked": False, "why": why}, why)
    cast = repository.read(edition.cast)
    repository.write(edition.cast, {**cast, "performance_recording": {"receipt": paths["receipt"]}})
    converge()
    assert record_of()["fit"]["why"] == (
        "not asked: the cast declares no performance recording with its alignment"
    )
    assert (count.selected, count.bound) == (0, 0)


def test_a_run_ended_while_it_counts_leaves_its_record_running_and_the_next_run_counts_again(
    count,
):
    converge()
    assert record_of()["fit"]["verdict"] == "fits"
    count.binding = child_processes.Terminated(15)
    with pytest.raises(child_processes.Terminated):
        narration_converge.converge("en", *narration_converge.admitted("en"))
    # The record says that a run is under way and holds no fit, the former run's neither. The
    # selection's records are whole, as the selection writes them.
    record = record_of()
    assert (record["state"], record["unsettled"], "fit" in record) == ("running", {}, False)
    count.binding, count.free = None, -0.1
    assert refused().startswith(f"{MISS}0.10 s; a thought pause of 0.4 s")
    assert (record_of()["state"], count.selected) == ("ended", 3)


def test_a_run_without_a_former_record_and_one_with_it_write_the_same_record(count):
    path = Edition("en").ear_first / narration_converge.RECORD
    assert not path.exists()
    converge()
    first = path.read_bytes()
    path.unlink()
    converge()
    assert path.read_bytes() == first


def test_the_count_writes_what_the_selection_writes_and_nothing_else(
    bench, studio, voiced, monkeypatch
):
    import converging

    import filmkit.narration.selection as narration_selection

    # The real selection on the edition's own alignment; the binding and the measure stand in.
    studio.words = converging.placed
    bench.begin([voiced(), voiced()])
    monkeypatch.setattr(fitting, "select", narration_selection.select)
    before = kept()
    converge()
    after = kept()
    edition = Edition("en")
    selection = {
        path.relative_to(repository.ROOT).as_posix()
        for path in (
            repository.ROOT / edition.narration_selected,
            repository.ROOT / edition.alignment_selected,
        )
    }
    assert {name for name in after if after[name] != before.get(name)} == selection | {
        "build/evidence/editions/en/ear-first/convergence.json",
        "build/evidence/editions/en/ear-first/judgment.json",
    }
    assert set(before) - set(after) == set()
    # The two records are the ones that the selection writes when it is asked by itself.
    for name in selection:
        (repository.ROOT / name).unlink()
    narration_selection.select(edition)
    assert {name: kept()[name] for name in selection} == {name: after[name] for name in selection}
    assert record_of()["fit"]["verdict"] == "fits"
