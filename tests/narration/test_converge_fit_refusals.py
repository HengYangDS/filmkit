"""A settled narration that the count refuses, or whose count ends in a fault: what the
convergence says in one line as the edition's refusal, what it raises as a fault with the record
ended first, and what it refuses before anything runs."""

import subprocess
import wave

import pytest
from converging import converge, counts, record_of, refused

import filmkit.narration.converge as narration_converge
import filmkit.narration.fitting as fitting
import filmkit.repository as repository
import filmkit.soundtrack.fit as soundtrack_fit
from filmkit.narration.selection import SelectionError
from filmkit.production import Edition
from filmkit.soundtrack.level import LevelError


def begun(*_taken: object) -> None:
    """Stand in for the beginning of a run (`converge.begin`), whatever it is given: a refusal
    that comes before the first effect never reaches it."""
    pytest.fail("the run began before it was refused")


@pytest.mark.parametrize(
    "fields",
    [
        {"reserve_seconds": -0.1},
        {"reserve_seconds": "0.1"},
        {"reserve_seconds": True},
        {"reserve_seconds": float("inf")},
        {"reserve_seconds": 0.1, "shorter_by_at_most": 0.03},
        0.1,
    ],
)
def test_a_reserve_that_is_no_number_of_seconds_is_refused_before_anything_runs(
    count, fields, monkeypatch
):
    cast = repository.read(Edition("en").cast)
    repository.write(Edition("en").cast, {**cast, "runtime_fit": fields})
    monkeypatch.setattr(narration_converge, "begin", begun)
    assert refused() == (
        "en: the cast's runtime_fit declares reserve_seconds, a number of seconds from 0, and "
        "nothing else"
    )
    assert count.selected == 0


def test_a_script_that_declares_no_thought_range_is_refused_before_anything_runs(
    count, monkeypatch
):
    script = repository.read(Edition("en").script)
    del script["voice_performance"]["thought_pause_range"]
    repository.write(Edition("en").script, script)
    monkeypatch.setattr(narration_converge, "begin", begun)
    # The judgment reads the pause policy too: it is refused in one line before the first effect.
    assert refused() == (
        "en: the script's pause policy is refused: thought_pause_range requires a low and a "
        "high value"
    )
    assert not (Edition("en").ear_first / narration_converge.RECORD).exists()
    assert (count.selected, count.bound) == (0, 0)


@pytest.mark.parametrize("kind", soundtrack_fit.REFUSALS)
def test_what_the_count_refuses_is_the_editions_refusal_with_the_record_ended(count, kind, capsys):
    count.binding = kind("Selected recording waveform differs: 26")
    assert refused() == (
        "en: the settled narration is refused by the assembly: Selected recording waveform "
        "differs: 26"
    )
    record = record_of()
    assert (record["state"], record["unsettled"]) == ("ended", {})
    assert record["fit"] == {
        "asked": True,
        "reserve_seconds": 0.0,
        "verdict": "refused",
        "refusal": "the assembly: Selected recording waveform differs: 26",
    }
    assert counts(capsys)["fit"] == "refused"


def test_a_recording_that_does_not_decode_is_the_editions_refusal(count):
    count.binding = subprocess.CalledProcessError(1, ["ffmpeg", "-i", "take.wav"])
    line = refused()
    assert line.startswith("en: the settled narration is refused by the assembly: Command ")
    assert record_of()["state"] == "ended"


def test_a_recording_that_does_not_decode_is_said_with_ffmpeg_s_own_last_error_line(count):
    written = b"[wav @ 0x14f] no data chunk\n\ntake.wav: Invalid data found when processing input\n"
    count.binding = subprocess.CalledProcessError(1, ["ffmpeg", "-i", "take.wav"], stderr=written)
    assert refused() == (
        "en: the settled narration is refused by the assembly: Command '['ffmpeg', '-i', "
        "'take.wav']' returned non-zero exit status 1: take.wav: Invalid data found when "
        "processing input"
    )
    assert record_of()["fit"]["verdict"] == "refused"


def test_the_one_line_holds_no_control_character(count):
    written = b"one\ntwo \x1b[31mred\x1b[0m\x07\tthree\n"
    count.binding = subprocess.CalledProcessError(1, ["ffmpeg"], stderr=written)
    line = refused()
    # The escapes, the bell and the tab of FFmpeg's last line are each a blank.
    assert line.endswith("returned non-zero exit status 1: two  [31mred [0m  three")
    assert all(character.isprintable() for character in line)
    assert record_of()["fit"]["refusal"] == line.removeprefix(
        "en: the settled narration is refused by "
    )


@pytest.mark.parametrize(
    ("where", "refuser", "folder"),
    [
        ("binding", "the assembly", "below"),
        # A recording and a receipt that the edition names by an absolute path outside the root.
        ("binding", "the assembly", "outside"),
        ("selecting", "the selection", "outside"),
    ],
)
def test_a_missing_file_named_by_an_absolute_path_is_the_editions_refusal(
    count, tmp_path_factory, where, refuser, folder
):
    home = repository.ROOT / "build" if folder == "below" else tmp_path_factory.mktemp("outside")
    missing = home / "takes/26.wav"
    setattr(count, where, FileNotFoundError(2, "No such file or directory", str(missing)))
    assert refused() == (
        f"en: the settled narration is refused by {refuser}: [Errno 2] No such file or "
        f"directory: '{missing}'"
    )
    record = record_of()
    assert (record["state"], record["fit"]["verdict"]) == ("ended", "refused")


@pytest.mark.parametrize(
    ("fault", "words"),
    [
        (wave.Error("file does not start with RIFF id"), "file does not start with RIFF id"),
        # A recording that ends inside its header: the reader raises without a word.
        (EOFError(), "EOFError"),
    ],
)
def test_a_recording_that_is_no_wav_is_the_editions_refusal(count, fault, words):
    count.selecting = fault
    assert refused() == f"en: the settled narration is refused by the selection: {words}"
    record = record_of()
    assert (record["state"], record["fit"]["verdict"]) == ("ended", "refused")


@pytest.mark.parametrize(
    ("where", "kind", "named", "words"),
    [
        # A decoder that is not on the PATH, or that may not be executed: what running it
        # raises, for the decoder's bare name.
        (
            "binding",
            FileNotFoundError,
            (2, "No such file or directory", "ffmpeg"),
            "FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'",
        ),
        (
            "binding",
            PermissionError,
            (13, "Permission denied", "ffmpeg"),
            "PermissionError: [Errno 13] Permission denied: 'ffmpeg'",
        ),
        # An error that names no file at all, and one that names a descriptor.
        (
            "selecting",
            OSError,
            (5, "Input/output error"),
            "OSError: [Errno 5] Input/output error",
        ),
        (
            "binding",
            OSError,
            (9, "Bad file descriptor", 7),
            "OSError: [Errno 9] Bad file descriptor: 7",
        ),
    ],
)
def test_an_error_of_the_host_is_a_fault_and_no_refusal_of_the_edition(
    count, where, kind, named, words
):
    setattr(count, where, kind(*named))
    with pytest.raises(kind):
        converge()
    record = record_of()
    assert (record["state"], record["unsettled"]) == ("ended", {})
    assert record["fit"] == {
        "asked": True,
        "reserve_seconds": 0.0,
        "verdict": "failed",
        "fault": words,
    }


def test_what_the_selection_refuses_is_said_in_one_line(count):
    count.selecting = SelectionError("26.1: a pause is unmarked\n26.2: a term is said otherwise")
    assert refused() == (
        "en: the settled narration is refused by the selection: 26.1: a pause is unmarked; "
        "26.2: a term is said otherwise"
    )
    record = record_of()
    assert (record["state"], record["fit"]["verdict"], count.bound) == ("ended", "refused", 0)


def test_an_edition_with_room_that_the_allocation_refuses_is_refused_not_missed(count):
    count.refusal = "The gaps cannot hold the runtime that is left"
    assert refused() == (
        "en: the settled narration is refused by the assembly: The gaps cannot hold the "
        "runtime that is left"
    )
    fit = record_of()["fit"]
    assert (fit["verdict"], fit["free_seconds"]) == ("refused", 0.8)


def test_an_edition_whose_clips_cannot_be_designed_is_refused_with_that_reason(count, monkeypatch):
    refusal = LevelError("Thought levels differ by more than the tolerance: 26")
    line = {"policy": "declared", "free_seconds": None, "verdict": str(refusal)}
    monkeypatch.setattr(soundtrack_fit, "measured", lambda *_: (line, refusal))
    assert refused() == (
        "en: the settled narration is refused by the assembly: Thought levels differ by more "
        "than the tolerance: 26"
    )
    assert record_of()["fit"]["verdict"] == "refused"


def test_a_fault_of_the_count_keeps_its_traceback_and_the_record_is_ended_first(count):
    # A selection that lacks a segment is no refusal of the count's owners.
    count.binding = KeyError("27")
    with pytest.raises(KeyError):
        converge()
    record = record_of()
    assert (record["state"], record["unsettled"]) == ("ended", {})
    assert record["fit"] == {
        "asked": True,
        "reserve_seconds": 0.0,
        "verdict": "failed",
        "fault": "KeyError: '27'",
    }
    assert fitting.said("en", record["fit"]) == (
        "en: the count of the settled narration ended in a fault: KeyError: '27'"
    )


def test_an_error_of_the_host_while_the_pause_is_read_is_a_fault_too(count, monkeypatch):
    count.free = -0.1

    def absent(_edition: Edition, _reserve: float) -> dict:
        raise FileNotFoundError(2, "No such file or directory", "ffmpeg")

    monkeypatch.setattr(soundtrack_fit, "thought_pause_to_fit", absent)
    with pytest.raises(FileNotFoundError):
        converge()
    record = record_of()
    assert (record["state"], record["fit"]["verdict"]) == ("ended", "failed")
