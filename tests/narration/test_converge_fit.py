"""A settled narration is counted for its edition's runtime: what the convergence asks of the
assembly's count, what it records of the runtime, and what it leaves.

The count here is the bench's stand-in (`fit_bench.Count`), which rounds a given count up and
lets the gaps take the fraction up to a given room: these tests check what the convergence asks
and records of a count, not the count. The count itself is tested where the assembly counts
(`tests/soundtrack/test_assembly.py`, `tests/soundtrack/test_fit.py`)."""

import json
from pathlib import Path

import pytest
from converging import (
    REFUSED,
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
from filmkit.graph import records
from filmkit.production import Edition


def kept() -> dict[str, bytes]:
    """Every file below the film's root with its bytes, but the duration records and the run
    records: each states when its run started and how long it took, which differs from run to
    run (`filmkit.graph.records`)."""
    return {
        path.relative_to(repository.ROOT).as_posix(): path.read_bytes()
        for path in sorted(repository.ROOT.rglob("*"))
        if path.is_file()
        and path.parent != duration_path().parent
        and not path.relative_to(repository.ROOT).is_relative_to(records.FOLDER)
    }


def test_the_convergence_s_duration_record_says_whether_the_edition_ended_fit(count):
    converge()
    record = duration_of()
    assert (record["command"], record["completed"]) == ("converge", True)
    # Nothing was due and nothing refused: the run judged and counted.
    assert [*record["phases"]] == ["judgment", "count"]
    # It is the one duration record that the command writes.
    assert [*duration_path().parent.iterdir()] == [duration_path()]
    # An edition whose pauses the assembly cannot design did not complete.
    count.undesigned = lambda _pause: True
    assert refused().startswith(REFUSED)
    assert (duration_of()["completed"], [*duration_of()["phases"]]) == (
        False,
        ["judgment", "count"],
    )


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
    script = repository.read(edition.script)
    if refusal == "a refused pause policy":
        del script["voice_performance"]["thought_pause_range"]
        repository.write(edition.script, script)
        return "en: the script's pause policy is refused: thought_pause_range requires"
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
        "a refused pause policy",
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
    ended = narration_converge.converge("en", checked)
    assert (ended["state"], ended["fit"]["verdict"]) == ("ended", "fits")


def test_a_settled_edition_is_counted_for_its_runtime(count, studio, capsys):
    # The speech with its thought pauses, its designed gaps and its closing quiet come to
    # 1472.14 s, with 3 s of credits: a runtime of 1476 s, whose 0.86 s fraction the gaps take.
    before = kept()
    converge()
    record = record_of()
    assert record["fit"] == {
        "asked": True,
        "runtime_seconds": 1476,
        "free_seconds": 0.86,
        "credits_free_seconds": 0.0,
        "verdict": "fits",
    }
    assert (record["state"], record["unsettled"]) == ("ended", {})
    printed = capsys.readouterr().out
    said = json.loads(printed.splitlines()[-1])
    assert (said["fit"], said["runtime_seconds"], said["free_seconds"]) == ("fits", 1476, 0.86)
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


def test_a_long_narration_is_counted_and_never_missed(count, capsys):
    # The speech alone comes to 1590.79 s: the runtime is what its count gives, and no second
    # is missing and no thought pause is named.
    count.counted = 1590.79 + 6.4 + 2.6 + 3
    cast = (repository.ROOT / Edition("en").cast).read_bytes()
    script = (repository.ROOT / Edition("en").script).read_bytes()
    converge()
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["runtime_seconds"]) == ("fits", 1603)
    assert not {"missing_seconds", "pause", "reserve_seconds"} & set(fit)
    assert counts(capsys)["fit"] == "fits"
    # Nothing is applied: the script and the cast are as they were, and one pause was counted.
    assert (repository.ROOT / Edition("en").cast).read_bytes() == cast
    assert (repository.ROOT / Edition("en").script).read_bytes() == script
    assert count.tried == [0.45]


@pytest.mark.parametrize(
    ("room", "gaps", "credits"),
    [(2.4, 0.86, 0.0), (0.3, 0.3, 0.56), (0.0, 0.0, 0.86)],
)
def test_the_rounding_s_fraction_is_recorded_as_the_gaps_and_the_credits_take_it(
    count, capsys, room, gaps, credits
):
    # The gaps take the fraction up to their room, and the credits the rest: never a refusal.
    count.room = room
    converge()
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["runtime_seconds"]) == ("fits", 1476)
    assert (fit["free_seconds"], fit["credits_free_seconds"]) == (gaps, pytest.approx(credits))
    assert counts(capsys)["credits_free_seconds"] == pytest.approx(credits)


def test_a_count_of_whole_seconds_holds_no_fraction(count):
    count.counted = 600.0
    converge()
    fit = record_of()["fit"]
    assert (fit["runtime_seconds"], fit["free_seconds"], fit["credits_free_seconds"]) == (
        600,
        0.0,
        0.0,
    )


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
    # The narration writes its receipt and alignment where the count reads them; without the
    # alignment there is nothing to count.
    assert (repository.ROOT / paths["receipt"]).is_file()
    (repository.ROOT / paths["alignment"]).unlink()
    converge()
    assert record_of()["fit"]["why"] == (
        "not asked: the edition has no narration receipt with its alignment"
    )
    assert (count.selected, count.bound) == (0, 0)


def test_a_run_ended_while_it_counts_leaves_its_record_running_and_the_next_run_counts_again(
    count,
):
    converge()
    assert record_of()["fit"]["verdict"] == "fits"
    count.binding = child_processes.Terminated(15)
    with pytest.raises(child_processes.Terminated):
        narration_converge.converge("en", narration_converge.admitted("en"))
    # The record says that a run is under way and holds no fit, the former run's neither. The
    # selection's records are whole, as the selection writes them.
    record = record_of()
    assert (record["state"], record["unsettled"], "fit" in record) == ("running", {}, False)
    count.binding = None
    converge()
    assert (record_of()["state"], record_of()["fit"]["verdict"], count.selected) == (
        "ended",
        "fits",
        3,
    )


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
