"""The runtime fit: the assembly's own steps up to the gap allocation, under the script's pause
policy and its declared variants, writing nothing but the assembly's decode work files."""

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


def overrun(edition, seconds: float) -> dict:
    """Lengthen the declared closing quiet until the narration exceeds the runtime by `seconds`,
    measured by the assembly; the performance."""
    soundtrack_assembly.assemble(edition)
    receipt = repository.read(edition.audio_assembly)
    pauses = receipt["designed_pause_policy"]["pauses"]
    allocated = sum(round(gap["seconds"] * RATE) for gap in receipt["gaps"])
    designed = sum(round(pauses[gap["kind"]] * RATE) for gap in receipt["gaps"])
    closing = pauses["closing"] + (allocated - designed) / RATE + seconds
    return declare(edition, designed_pauses={**pauses, "closing": closing})


def tree(root) -> dict[str, str | None]:
    """Every path below a root, with each file's SHA-256."""
    return {
        str(path.relative_to(root)): repository.sha(path) if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


@pytest.mark.ffmpeg
def test_the_dry_run_allocates_the_gaps_the_assembly_records(two_chapters, capsys):
    soundtrack_fit.fit(two_chapters)
    declared = reported(capsys)["declared"]
    soundtrack_assembly.assemble(two_chapters)
    receipt = repository.read(two_chapters.audio_assembly)
    assert declared["verdict"] == "fits"
    assert declared["gaps"] == receipt["gaps"]
    assert declared["closing_seconds"] == receipt["closing_seconds"]
    speech = sum(record["frames"] for record in receipt["records"])
    assert declared["speech_seconds"] == speech / RATE
    # The free runtime is what the allocation adds to the designed gaps.
    allocated = sum(round(gap["seconds"] * RATE) for gap in receipt["gaps"])
    free = round((declared["gap_seconds"] + declared["free_seconds"]) * RATE)
    assert free == allocated
    assert declared["gap_seconds"] == pytest.approx(3.0 + 3.4)


@pytest.mark.ffmpeg
def test_an_overrun_is_reported_and_refused_as_the_assembly_refuses(two_chapters, capsys):
    overrun(two_chapters, 0.10)
    capsys.readouterr()
    with pytest.raises(PauseError) as refused:
        soundtrack_fit.fit(two_chapters)
    declared = reported(capsys)["declared"]
    assert str(refused.value) == "Narration exceeds the runtime by 0.10 s"
    assert (declared["free_seconds"], declared["gaps"]) == (-0.1, None)
    assert declared["verdict"] == "Narration exceeds the runtime by 0.10 s"
    with pytest.raises(PauseError) as assembled:
        soundtrack_assembly.assemble(two_chapters)
    assert str(assembled.value) == str(refused.value)


@pytest.mark.ffmpeg
def test_a_variant_is_reported_and_the_script_decides_the_exit(two_chapters, capsys):
    performance = overrun(two_chapters, 0.10)
    # Each thought join's designed quiet falls from 0.45 s to 0.3 s.
    shorter = {**performance["designed_pauses"], "thought": 0.3}
    variants = {"shorter-thoughts": {"designed_pauses": shorter}}
    capsys.readouterr()
    with pytest.raises(PauseError, match="exceeds the runtime by 0.10 s"):
        soundtrack_fit.fit(two_chapters, variants)
    lines = reported(capsys)
    assert list(lines) == ["declared", "shorter-thoughts"]
    variant = lines["shorter-thoughts"]
    # Two joins 0.15 s shorter leave 0.2 s free where the script misses 0.1 s.
    assert variant["verdict"] == "fits"
    speech = lines["declared"]["speech_seconds"] - 0.3
    assert variant["speech_seconds"] == pytest.approx(speech, abs=1e-3)
    assert variant["free_seconds"] == pytest.approx(0.2, abs=1e-3)
    assert [gap["kind"] for gap in variant["gaps"]] == ["opening", "chapter"]


@pytest.mark.ffmpeg
def test_a_variant_whose_pauses_cannot_be_designed_is_reported_without_deciding_the_exit(
    two_chapters, capsys
):
    # A coda pause of 1 s floors the closing join beyond what the 0.45 s mean of two joins funds.
    reports = soundtrack_fit.fit(two_chapters, {"long-coda": {"coda_thought_pause_seconds": 1.0}})
    lines = reported(capsys)
    assert [line["verdict"] for line in reports] == ["fits", lines["long-coda"]["verdict"]]
    assert lines["long-coda"] == {
        "policy": "long-coda",
        "speech_seconds": None,
        "gap_seconds": None,
        "closing_seconds": None,
        "free_seconds": None,
        "gaps": None,
        "verdict": "Thought boundaries need a larger declared statement pause",
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
    measures = ("speech_seconds", "gap_seconds", "closing_seconds", "free_seconds", "gaps")
    expected = {"policy": "refused", **dict.fromkeys(measures), "verdict": str(refusal)}
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
    overrun(two_chapters, 0.10)
    capsys.readouterr()
    ((line, refusal),) = soundtrack_fit.asked(two_chapters)
    assert (line["policy"], line["free_seconds"]) == ("declared", -0.1)
    assert (type(refusal), str(refusal)) == (PauseError, line["verdict"])
    # Nothing is printed and nothing is refused: the caller decides by what it is given.
    assert capsys.readouterr().out == ""


@pytest.mark.ffmpeg
@pytest.mark.parametrize(("reserve", "fits_at", "free"), [(0.0, 0.4, 0.0), (0.05, 0.37, 0.06)])
def test_the_largest_thought_pause_that_fits_is_read_and_not_applied(
    two_chapters, capsys, reserve, fits_at, free
):
    performance = overrun(two_chapters, 0.10)
    soundtrack_fit.asked(two_chapters)
    before = tree(repository.ROOT)
    # Each 0.01 s off the two thought joins frees 0.02 s of the 0.10 s that are missing.
    found = soundtrack_fit.thought_pause_to_fit(two_chapters, reserve)
    assert found == {
        "declared_seconds": 0.45,
        "range_seconds": [0.3, 0.6],
        "reserve_seconds": reserve,
        "fits_at_seconds": fits_at,
        "free_seconds": pytest.approx(free, abs=1e-9),
    }
    assert tree(repository.ROOT) == before
    capsys.readouterr()
    # The pause it names fits where the script declares it, and 0.01 s more does not.
    declare(two_chapters, designed_pauses={**performance["designed_pauses"], "thought": fits_at})
    assert soundtrack_fit.fit(two_chapters)[0]["verdict"] == "fits"
    longer = round(fits_at + 0.01, 2)
    declare(two_chapters, designed_pauses={**performance["designed_pauses"], "thought": longer})
    ((line, _),) = soundtrack_fit.asked(two_chapters)
    assert line["free_seconds"] < reserve


@pytest.mark.ffmpeg
def test_a_miss_that_no_thought_pause_of_the_range_closes_is_said_with_what_is_left(two_chapters):
    overrun(two_chapters, 0.40)
    # The range's least pause, 0.3 s, frees 0.30 s of the 0.40 s that are missing.
    assert soundtrack_fit.thought_pause_to_fit(two_chapters) == {
        "declared_seconds": 0.45,
        "range_seconds": [0.3, 0.6],
        "reserve_seconds": 0.0,
        "fits_at_seconds": None,
        "tried_seconds": 0.3,
        "free_seconds": pytest.approx(-0.1, abs=1e-9),
        "refusal": "Narration exceeds the runtime by 0.10 s",
    }


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
    found = fitting.read("zh", 0.0)
    assert (found["verdict"], found["free_seconds"] >= 0) == ("fits", True)
    assert fitting.said("zh", found) is None
    overrun(settled, 0.10)
    found = fitting.read("zh", 0.0)
    assert found == {
        "asked": True,
        "reserve_seconds": 0.0,
        "free_seconds": pytest.approx(-0.1, abs=1e-9),
        "verdict": "misses",
        "missing_seconds": pytest.approx(0.1, abs=1e-9),
        "pause": {
            "declared_seconds": 0.45,
            "range_seconds": [0.3, 0.6],
            "reserve_seconds": 0.0,
            "fits_at_seconds": 0.4,
            "free_seconds": pytest.approx(0.0, abs=1e-9),
        },
    }
    assert fitting.said("zh", found) == (
        "zh: the settled narration misses its runtime by 0.10 s; a thought pause of 0.4 s, "
        "declared at 0.45 s in a range from 0.3 to 0.6 s, would fit with 0.00 s free"
    )
    # A recording that no longer holds the bytes its record names is the edition's refusal.
    (repository.ROOT / "take-01.wav").write_bytes(b"not the recording")
    refused = fitting.read("zh", 0.0)
    assert refused["verdict"] == "refused" and refused["refusal"].startswith("the assembly: ")
    assert "\n" not in fitting.said("zh", refused)


def test_a_decoder_not_installed_is_the_host_s_fault_and_a_missing_recording_the_edition_s(
    settled, monkeypatch
):
    # No FFmpeg on the PATH: running the decoder raises for its name, which is no file of the
    # film, and the fault is raised to the caller.
    monkeypatch.setenv("PATH", str(repository.ROOT / "no-tools"))
    with pytest.raises(FileNotFoundError) as fault:
        fitting.read("zh", 0.0)
    assert fault.value.filename == "ffmpeg"
    # A selected recording that is gone from below the film's root is the edition's refusal.
    recording = repository.ROOT / "take-01.wav"
    recording.unlink()
    assert fitting.read("zh", 0.0) == {
        "asked": True,
        "reserve_seconds": 0.0,
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
    assert fitting.read("zh", 0.0) == {
        "asked": True,
        "reserve_seconds": 0.0,
        "verdict": "refused",
        "refusal": f"the selection: [Errno 2] No such file or directory: '{receipt}'",
    }
    # A recording, which its record names by an absolute path and the binding reads.
    monkeypatch.setattr(fitting, "select", lambda _edition: None)
    recording = outside / "take-01.wav"
    records = json.loads(settled.narration_selected.read_text())
    records["records"][0]["path"] = str(recording)
    settled.narration_selected.write_text(json.dumps(records, ensure_ascii=False))
    refused = fitting.read("zh", 0.0)
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
    refused = fitting.read("zh", 0.0)
    assert refused["verdict"] == "refused"
    line = fitting.said("zh", refused)
    assert line.startswith("zh: the settled narration is refused by the assembly: Command ")
    assert "\n" not in line and line.endswith("Invalid data found when processing input")


def counted(
    monkeypatch,
    missing: float,
    refused_under: float = 0.0,
    refused_between: tuple[float, float] | None = None,
) -> list[float]:
    """Stand in for the assembly's count (`fit_bench.Count`): two thought joins, `missing`
    seconds over the runtime at the contract's thought pause, and no design for a pause under
    `refused_under` or from the first to the second of `refused_between`. The thought pauses
    that were measured, in order."""

    def undesigned(pause: float) -> bool:
        banned = refused_between is not None and refused_between[0] <= pause <= refused_between[1]
        return pause < refused_under or banned

    count = Count(free=-missing, undesigned=undesigned)
    monkeypatch.setattr(soundtrack_fit, "_bound", lambda _script, _edition: None)
    monkeypatch.setattr(soundtrack_fit, "measured", count.measured)
    return count.tried


def test_the_pauses_tried_begin_at_the_range_s_own_least_value(two_chapters, monkeypatch):
    declare(two_chapters, thought_pause_range=[0.30405, 0.6])
    tried = counted(monkeypatch, 0.10)
    # The steps run from 0.30405 s, which is on no grid of hundredths or of ten-thousandths:
    # 0.39405 s is the largest of them that fits, and it is named as it was counted.
    found = soundtrack_fit.thought_pause_to_fit(two_chapters)
    assert (found["range_seconds"], found["fits_at_seconds"]) == ([0.30405, 0.6], 0.39405)
    # The count is in whole samples: 572 of them are free, 0.0119 s to four places.
    assert (found["free_seconds"], min(tried)) == (572 / RATE, 0.30405)
    assert {0.39405, 0.40405} <= set(tried)
    # The pause as it is printed is the pause that was counted.
    assert float(str(found["fits_at_seconds"])) in tried


def test_a_least_pause_under_the_reserve_is_not_said_to_fit(two_chapters, monkeypatch):
    counted(monkeypatch, 0.10)
    # The range's least pause, 0.3 s, frees 0.30 s: 0.20 s free, where 0.25 s must be, though
    # the allocation accepts it.
    assert soundtrack_fit.thought_pause_to_fit(two_chapters, 0.25) == {
        "declared_seconds": 0.45,
        "range_seconds": [0.3, 0.6],
        "reserve_seconds": 0.25,
        "fits_at_seconds": None,
        "tried_seconds": 0.3,
        "free_seconds": 0.2,
        "refusal": None,
    }


def test_a_range_of_one_value_is_tried_at_that_value_alone(two_chapters, monkeypatch):
    declare(two_chapters, thought_pause_range=[0.45, 0.45])
    tried = counted(monkeypatch, 0.10)
    found = soundtrack_fit.thought_pause_to_fit(two_chapters)
    assert (found["fits_at_seconds"], found["tried_seconds"], tried) == (None, 0.45, [0.45])


def test_pauses_that_cannot_be_designed_lie_under_the_pause_that_fits(two_chapters, monkeypatch):
    # No pause under 0.35 s can be designed; 0.4 s is still the largest that fits.
    counted(monkeypatch, 0.10, refused_under=0.35)
    assert soundtrack_fit.thought_pause_to_fit(two_chapters)["fits_at_seconds"] == 0.4
    # Where every pause that would close the miss lies under them, the design's refusal is said.
    counted(monkeypatch, 0.30, refused_under=0.35)
    found = soundtrack_fit.thought_pause_to_fit(two_chapters)
    assert (found["fits_at_seconds"], found["tried_seconds"], found["free_seconds"]) == (
        None,
        0.34,
        None,
    )
    assert found["refusal"] == "Thought boundaries need a larger declared statement pause"


def test_a_refusal_between_two_pauses_hides_no_pause_that_fits(two_chapters, monkeypatch):
    # 0.24 s are missing: the pauses to 0.33 s fit. No pause from 0.36 to 0.40 s can be
    # designed, and the halving ends on one of them; the pauses under it are then tried.
    tried = counted(monkeypatch, 0.24, refused_between=(0.36, 0.40))
    found = soundtrack_fit.thought_pause_to_fit(two_chapters)
    assert (found["fits_at_seconds"], found["free_seconds"]) == (0.33, 0.0)
    # The halving ended on 0.4 s, and every pause from there down to the answer was counted.
    assert {0.4, 0.36, 0.35, 0.34, 0.33} <= set(tried)


def test_each_policy_is_printed_as_it_is_measured(two_chapters, capsys, monkeypatch):
    performance = repository.read(two_chapters.script)["voice_performance"]
    shorter = {**performance["designed_pauses"], "thought": 0.4}
    tried, printed = counted(monkeypatch, 0.0), []
    measured = soundtrack_fit.measured

    def watching(name, *rest):
        printed.append((name, len(capsys.readouterr().out.splitlines())))
        return measured(name, *rest)

    monkeypatch.setattr(soundtrack_fit, "measured", watching)
    soundtrack_fit.fit(two_chapters, {"shorter": {"designed_pauses": shorter}})
    # The script's own line is out before the variant is measured.
    assert (printed, tried) == ([("declared", 0), ("shorter", 1)], [0.45, 0.4])
