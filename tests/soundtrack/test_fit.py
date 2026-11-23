"""The runtime fit: the assembly's own steps up to the gap allocation, which give the runtime
under the script's pause policy and its declared variants, writing nothing but the assembly's
decode work files."""

import json
from pathlib import Path

import pytest
from fit_bench import Count

import filmkit.narration.fitting as fitting
import filmkit.narration.selection as narration_selection
import filmkit.repository as repository
import filmkit.soundtrack.assembly as soundtrack_assembly
import filmkit.soundtrack.fit as soundtrack_fit
from filmkit.soundtrack.level import LevelError
from filmkit.soundtrack.pauses import PauseError
from filmkit.soundtrack.policy import PausePolicyError
from filmkit.specification import RATE


def reported(capsys) -> dict[str, dict]:
    """The lines that fit printed, by the policy each reports."""
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    return {line["policy"]: line for line in lines}


def declare(edition, **fields) -> dict:
    """Replace whole fields of the edition's voice performance; the performance."""
    path = repository.ROOT / edition.script
    script = json.loads(path.read_text())
    script["voice_performance"] |= fields
    path.write_text(json.dumps(script, ensure_ascii=False))
    return script["voice_performance"]


def count_of(line: dict) -> int:
    """A report's own count in samples: its speech, designed gaps and closing quiet, and the four
    seconds of credits the bench declares."""
    parts = ("speech_seconds", "gap_seconds", "closing_seconds")
    return sum(round(line[key] * RATE) for key in parts) + 4 * RATE


def counted(line: dict) -> int:
    """The runtime a report's own count gives: the count rounded up to the next whole second."""
    return -(-count_of(line) // RATE)


# A coda pause of 1 s floors the closing join beyond what the 0.45 s mean of two joins funds.
LONG_CODA = {"coda_thought_pause_seconds": 1.0}
UNDESIGNED = "Thought boundaries need a larger declared statement pause"


def tree(root) -> dict[str, str | None]:
    """Every path below a root, with each file's SHA-256."""
    return {
        str(path.relative_to(root)): repository.sha(path) if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


@pytest.mark.ffmpeg
def test_the_dry_run_gives_the_runtime_and_gaps_the_assembly_records(two_chapters, capsys):
    soundtrack_fit.fit(two_chapters)
    declared = reported(capsys)["declared"]
    soundtrack_assembly.assemble(two_chapters)
    receipt = repository.read(two_chapters.audio_assembly)
    timeline = repository.read(two_chapters.timeline)
    assert declared["verdict"] == "fits"
    assert declared["runtime_seconds"] == receipt["duration"] == timeline["duration"]
    assert declared["runtime_seconds"] == counted(declared)
    assert declared["gaps"] == receipt["gaps"]
    assert declared["closing_seconds"] == receipt["closing_seconds"]
    speech = sum(record["frames"] for record in receipt["records"])
    assert declared["speech_seconds"] == speech / RATE
    # The gaps' share of the fraction is what the allocation adds to the designed gaps, and the
    # credits', none here, what it adds to the declared credits.
    allocated = sum(round(gap["seconds"] * RATE) for gap in receipt["gaps"])
    free = round((declared["gap_seconds"] + declared["free_seconds"]) * RATE)
    assert free == allocated
    assert 4 + declared["credits_free_seconds"] == timeline["credits_duration"] == 4
    assert declared["gap_seconds"] == pytest.approx(3.0 + 3.4)


@pytest.mark.ffmpeg
def test_a_fraction_the_gaps_cannot_take_goes_to_the_credits_and_refuses_nothing(
    two_chapters, capsys
):
    # The opening and the chapter gap stand at their declared limits: they have no room.
    declare(two_chapters, designed_pause_limits={"opening": 3.0, "paragraph": 5.5, "chapter": 3.4})
    (line,) = soundtrack_fit.fit(two_chapters)
    runtime = line["runtime_seconds"]
    assert (line["verdict"], type(runtime), runtime) == ("fits", int, counted(line))
    fraction = runtime * RATE - count_of(line)
    # The count leaves a fraction, so the credits have something to take.
    assert fraction > 0
    assert (line["free_seconds"], line["credits_free_seconds"]) == (0.0, fraction / RATE)
    soundtrack_assembly.assemble(two_chapters)
    timeline = repository.read(two_chapters.timeline)
    assert timeline["credits_duration"] == 4 + line["credits_free_seconds"]


@pytest.mark.ffmpeg
def test_each_variant_gives_its_own_runtime_and_the_script_decides_the_exit(two_chapters, capsys):
    performance = repository.read(two_chapters.script)["voice_performance"]
    # Each thought join's designed quiet falls from 0.45 s to 0.3 s.
    shorter = {**performance["designed_pauses"], "thought": 0.3}
    reports = soundtrack_fit.fit(two_chapters, {"shorter-thoughts": {"designed_pauses": shorter}})
    lines = reported(capsys)
    assert list(lines) == ["declared", "shorter-thoughts"]
    declared, variant = lines["declared"], lines["shorter-thoughts"]
    assert [line["verdict"] for line in reports] == ["fits", "fits"]
    # Each runtime is its own count's: two joins 0.15 s shorter.
    assert variant["speech_seconds"] == pytest.approx(declared["speech_seconds"] - 0.3, abs=1e-3)
    assert (declared["runtime_seconds"], variant["runtime_seconds"]) == (
        counted(declared),
        counted(variant),
    )
    assert [gap["kind"] for gap in variant["gaps"]] == ["opening", "chapter"]


@pytest.mark.ffmpeg
def test_a_policy_that_cannot_be_designed_is_refused_as_the_assembly_refuses(two_chapters, capsys):
    declare(two_chapters, **LONG_CODA)
    # A variant without the coda can be designed; the script's policy alone decides the exit.
    with pytest.raises(PauseError) as refused:
        soundtrack_fit.fit(two_chapters, {"no-coda": {"coda_thought_pause_seconds": None}})
    lines = reported(capsys)
    assert str(refused.value) == lines["declared"]["verdict"] == UNDESIGNED
    assert lines["declared"]["runtime_seconds"] is None
    assert lines["no-coda"]["verdict"] == "fits"
    assert lines["no-coda"]["runtime_seconds"] == counted(lines["no-coda"])
    with pytest.raises(PauseError) as assembled:
        soundtrack_assembly.assemble(two_chapters)
    assert str(assembled.value) == str(refused.value)


@pytest.mark.ffmpeg
def test_a_variant_whose_pauses_cannot_be_designed_is_reported_without_deciding_the_exit(
    two_chapters, capsys
):
    reports = soundtrack_fit.fit(two_chapters, {"long-coda": LONG_CODA})
    lines = reported(capsys)
    assert [line["verdict"] for line in reports] == ["fits", lines["long-coda"]["verdict"]]
    assert lines["long-coda"] == {
        "policy": "long-coda",
        "speech_seconds": None,
        "gap_seconds": None,
        "closing_seconds": None,
        "runtime_seconds": None,
        "free_seconds": None,
        "credits_free_seconds": None,
        "gaps": None,
        "verdict": UNDESIGNED,
    }


@pytest.mark.ffmpeg
@pytest.mark.parametrize(
    ("step", "refusal"),
    [
        ("level_thoughts", LevelError("A thought's level gain would clip")),
        ("gap_pause_targets", PauseError("Designed pauses cannot keep their mean")),
    ],
)
def test_a_variant_refused_by_its_levels_or_its_gaps_does_not_decide_the_exit(
    two_chapters, monkeypatch, capsys, step, refusal
):
    # The stand-in refuses only the variant's thought level tolerance of 0.6 dB: while its clips
    # are leveled, or while its gaps are designed.
    original = getattr(soundtrack_assembly, step)

    def refusing(*arguments):
        tolerance = arguments[5] if step == "level_thoughts" else arguments[1]["level_tolerance"]
        if tolerance == 0.6:
            raise refusal
        return original(*arguments)

    monkeypatch.setattr(soundtrack_assembly, step, refusing)
    reports = soundtrack_fit.fit(two_chapters, {"refused": {"thought_level_tolerance_db": 0.6}})
    assert [line["verdict"] for line in reports] == ["fits", str(refusal)]
    expected = {"policy": "refused", **dict.fromkeys(soundtrack_fit.MEASURES)}
    expected["verdict"] = str(refusal)
    assert reported(capsys)["refused"] == expected


def test_a_variant_field_the_pause_policy_does_not_read_is_refused_before_decoding(
    two_chapters,
):
    unread = "^Variant typo: the pause policy reads no thought_pause$"
    with pytest.raises(PausePolicyError, match=unread):
        soundtrack_fit.fit(two_chapters, {"typo": {"thought_pause": 0.3}})
    assert not (repository.ROOT / "build/runtime/work/audio-assembly").exists()


def test_a_malformed_variant_is_refused_before_decoding(two_chapters, performance):
    pauses = {key: value for key, value in performance["designed_pauses"].items()}
    del pauses["closing"]
    variants = {"no-closing": {"designed_pauses": pauses}}
    with pytest.raises(PausePolicyError, match="^Variant no-closing: designed_pauses requires"):
        soundtrack_fit.fit(two_chapters, variants)
    assert not (repository.ROOT / "build/runtime/work/audio-assembly").exists()


@pytest.mark.ffmpeg
def test_the_dry_run_writes_only_the_decode_work_files(two_chapters, capsys):
    before = tree(repository.ROOT)
    soundtrack_fit.fit(two_chapters, {"same": {}})
    after = tree(repository.ROOT)
    work = "build/runtime/work/audio-assembly/zh"
    kept = before.keys() & after.keys()
    assert before.keys() <= after.keys()
    assert [path for path in kept if before[path] != after[path]] == []
    assert after.keys() - before.keys() == {
        "build/runtime",
        "build/runtime/work",
        "build/runtime/work/audio-assembly",
        work,
        f"{work}/01-source.wav",
        f"{work}/02-source.wav",
    }
    lines = reported(capsys)
    assert lines["same"] == {**lines["declared"], "policy": "same"}


MAP = "must map each variant's name to the voice-performance fields it replaces"


@pytest.mark.parametrize(
    ("text", "named"),
    [
        (None, "cannot be read"),
        ("{", "is not JSON"),
        ("[1, 2]", MAP),
        ('{"a": 1}', MAP),
        ('{"declared": {}}', "names a variant declared, which names the script's own policy"),
    ],
)
def test_a_variants_file_that_is_no_map_of_variants_is_refused(tmp_path, text, named):
    path = tmp_path / "variants.json"
    if text is not None:
        path.write_text(text)
    with pytest.raises(soundtrack_fit.VariantsError, match=named):
        soundtrack_fit.read_variants(path)


def test_a_variants_file_is_named_below_the_film_s_root(two_chapters, tmp_path, monkeypatch):
    (repository.ROOT / "variants.json").write_text('{"calmer": {"tail_guard_seconds": 0.4}}')
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    found = soundtrack_fit.read_variants(Path("variants.json"))
    assert found == {"calmer": {"tail_guard_seconds": 0.4}}


def test_a_variants_file_maps_each_variant_to_the_fields_it_replaces(tmp_path):
    path = tmp_path / "variants.json"
    path.write_text('{"as-declared": {}, "calmer": {"tail_guard_seconds": 0.4}}')
    assert soundtrack_fit.read_variants(path) == {
        "as-declared": {},
        "calmer": {"tail_guard_seconds": 0.4},
    }


@pytest.mark.ffmpeg
def test_the_reports_are_given_with_their_refusals_to_a_caller_that_decides(two_chapters, capsys):
    declare(two_chapters, **LONG_CODA)
    ((line, refusal),) = soundtrack_fit.asked(two_chapters)
    assert (line["policy"], line["runtime_seconds"]) == ("declared", None)
    assert (type(refusal), str(refusal)) == (PauseError, line["verdict"])
    # Nothing is printed and nothing is refused: the caller decides by what it is given.
    assert capsys.readouterr().out == ""


@pytest.fixture
def settled(two_chapters, monkeypatch):
    """The two chapters as the convergence asks of them (`filmkit.narration.fitting.read`): the
    cast declares a performance recording, and the selection alone stands in, since the bench
    stages the two records it writes. The binding, the decoding and the measure are the
    assembly's own."""
    cast = {"performance_recording": {"receipt": "receipt.json", "alignment": "alignment.json"}}
    (repository.ROOT / two_chapters.cast).write_text(json.dumps(cast))
    monkeypatch.setattr(fitting, "select", lambda _edition: None)
    return two_chapters


@pytest.mark.ffmpeg
def test_the_convergence_s_question_is_answered_by_the_real_binding_and_measure(settled):
    """What `filmkit.narration.fitting.read` answers when the recordings are bound to the script,
    decoded and measured by the assembly itself."""
    found = fitting.read("zh")
    ((line, _),) = soundtrack_fit.asked(settled)
    assert found == {
        "asked": True,
        "runtime_seconds": line["runtime_seconds"],
        "free_seconds": line["free_seconds"],
        "credits_free_seconds": line["credits_free_seconds"],
        "verdict": "fits",
    }
    assert found["runtime_seconds"] == counted(line)
    assert fitting.said("zh", found) is None
    # A recording that no longer holds the bytes its record names is the edition's refusal.
    (repository.ROOT / "take-01.wav").write_bytes(b"not the recording")
    refused = fitting.read("zh")
    assert refused["verdict"] == "refused" and refused["refusal"].startswith("the assembly: ")
    assert "\n" not in fitting.said("zh", refused)


def test_a_decoder_not_installed_is_the_host_s_fault_and_a_missing_recording_the_edition_s(
    settled, monkeypatch
):
    # No FFmpeg on the PATH: running the decoder raises for its name, which is no file of the
    # film, and the fault is raised to the caller.
    monkeypatch.setenv("PATH", str(repository.ROOT / "no-tools"))
    with pytest.raises(FileNotFoundError) as fault:
        fitting.read("zh")
    assert fault.value.filename == "ffmpeg"
    # A selected recording that is gone from below the film's root is the edition's refusal.
    recording = repository.ROOT / "take-01.wav"
    recording.unlink()
    assert fitting.read("zh") == {
        "asked": True,
        "verdict": "refused",
        "refusal": f"the assembly: [Errno 2] No such file or directory: '{recording}'",
    }


def test_a_missing_file_the_edition_names_outside_the_root_is_refused_in_one_line(
    settled, monkeypatch, tmp_path_factory
):
    outside = tmp_path_factory.mktemp("outside")
    # The receipt, which the cast names by an absolute path and the selection itself reads.
    receipt = outside / "receipt.json"
    cast = {"performance_recording": {"receipt": str(receipt), "alignment": "alignment.json"}}
    (repository.ROOT / settled.cast).write_text(json.dumps(cast))
    monkeypatch.setattr(fitting, "select", narration_selection.select)
    assert fitting.read("zh") == {
        "asked": True,
        "verdict": "refused",
        "refusal": f"the selection: [Errno 2] No such file or directory: '{receipt}'",
    }
    # A recording, which its record names by an absolute path and the binding reads.
    monkeypatch.setattr(fitting, "select", lambda _edition: None)
    recording = outside / "take-01.wav"
    records = json.loads(settled.narration_selected.read_text())
    records["records"][0]["path"] = str(recording)
    settled.narration_selected.write_text(json.dumps(records, ensure_ascii=False))
    refused = fitting.read("zh")
    assert refused["verdict"] == "refused"
    assert fitting.said("zh", refused) == (
        "zh: the settled narration is refused by the assembly: [Errno 2] No such file or "
        f"directory: '{recording}'"
    )


@pytest.mark.ffmpeg
def test_a_recording_that_ffmpeg_cannot_decode_is_refused_with_ffmpeg_s_own_error(settled):
    # The second recording holds no audio and its records name its bytes: the binding accepts
    # it, and FFmpeg ends with an error.
    recording = repository.ROOT / "take-02.wav"
    recording.write_bytes(b"not a recording")
    for path in (settled.narration_selected, settled.alignment_selected):
        records = json.loads(path.read_text())
        records["records"][1]["wav_sha256"] = repository.sha(recording)
        path.write_text(json.dumps(records, ensure_ascii=False))
    refused = fitting.read("zh")
    assert refused["verdict"] == "refused"
    line = fitting.said("zh", refused)
    assert line.startswith("zh: the settled narration is refused by the assembly: Command ")
    assert "\n" not in line and line.endswith("Invalid data found when processing input")


def test_each_policy_is_printed_as_it_is_measured(two_chapters, capsys, monkeypatch):
    performance = repository.read(two_chapters.script)["voice_performance"]
    shorter = {**performance["designed_pauses"], "thought": 0.4}
    count, printed = Count(), []
    monkeypatch.setattr(soundtrack_fit, "_bound", lambda _script, _edition: None)
    monkeypatch.setattr(soundtrack_fit, "measured", count.measured)
    measured = soundtrack_fit.measured

    def watching(name, *rest):
        printed.append((name, len(capsys.readouterr().out.splitlines())))
        return measured(name, *rest)

    monkeypatch.setattr(soundtrack_fit, "measured", watching)
    soundtrack_fit.fit(two_chapters, {"shorter": {"designed_pauses": shorter}})
    # The script's own line is out before the variant is measured.
    assert (printed, count.tried) == ([("declared", 0), ("shorter", 1)], [0.45, 0.4])
