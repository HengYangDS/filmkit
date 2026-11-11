"""The runtime fit: the assembly's own steps up to the gap allocation, under the script's pause
policy and its declared variants, writing nothing but the assembly's decode work files."""

import json
from pathlib import Path

import pytest

import filmkit.repository as repository
import filmkit.soundtrack.assembly as soundtrack_assembly
import filmkit.soundtrack.fit as soundtrack_fit
from filmkit.soundtrack.level import LevelError
from filmkit.soundtrack.pauses import PauseError
from filmkit.soundtrack.policy import PausePolicyError

RATE = 48000


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
