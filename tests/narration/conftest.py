"""Fixtures of the narration tests that edit, audition, judge or rebind an edition's thoughts.

The judgment loads the speech runtime, so the fixtures that need it import it when they are
asked for: the tests that need no runtime are collected on a host that has none.
"""

import dataclasses
import json
import signal
import wave
from pathlib import Path
from types import SimpleNamespace

import fit_bench
import numpy as np
import pytest

import filmkit.film as film
import filmkit.narration.anchors as anchors
import filmkit.repository as repository
from filmkit.production import Edition

CONTRACT = "content/voice-performance.json"


@pytest.fixture
def write_edition(tmp_path, monkeypatch):
    """Write tiny editions under a temporary root.

    Each edition gets a script of authored thoughts bound to a shared pronunciation
    contract, a cast holding only its retakes, and its narration mirror. A segment whose
    thoughts are written with anchors holds them as its anchored thoughts.
    """
    monkeypatch.setattr(repository, "ROOT", tmp_path)

    def write(code: str, thoughts: dict, retakes: dict, normalization: tuple = ()) -> dict:
        edition = Edition(code)
        contract = (
            repository.read(CONTRACT)
            if (tmp_path / CONTRACT).exists()
            else {"pronunciation": {"languages": {}}}
        )
        contract["pronunciation"]["languages"][edition.language] = {
            "normalization": list(normalization)
        }
        repository.write(CONTRACT, contract)
        segments = []
        for sid, groups in thoughts.items():
            # Thoughts written with marks are a segment's anchored ones, its plain ones filled.
            plain = anchors.plain(groups)
            segment = {"id": sid, "text": "".join(plain), "spoken_text": "".join(plain)}
            segments.append({**segment, "utterance_groups": plain})
            if plain != groups:
                segments[-1]["anchored_groups"] = list(groups)
        repository.write(edition.script, {"pronunciation_contract": CONTRACT, "segments": segments})
        repository.write(edition.cast, {"retakes": retakes})
        mirror = tmp_path / edition.mirror
        mirror.write_text("\n\n".join(segment["text"] for segment in segments) + "\n")
        return {
            "script": tmp_path / edition.script,
            "cast": tmp_path / edition.cast,
            "mirror": mirror,
        }

    return write


RATE = 24000
THOUGHTS = ("First thought.", " Second thought.")
IDENTITY = {"repo": "aligner", "revision": "r", "weights_sha256": "0" * 64}


@dataclasses.dataclass
class Aligned:
    """One aligned item, as the forced aligner returns it."""

    text: str
    start_time: float
    end_time: float


def voice(*, natural: bool = True, quiet_first: bool = True, seconds: float = 2.0) -> np.ndarray:
    """A 16-bit voice of 180 Hz that dies away, or is cut while it sounds, after 0.1 s of quiet."""
    frames, tail = round(seconds * RATE), round(0.3 * RATE)
    envelope = np.ones(frames)
    if natural:
        envelope[-tail:] = np.exp(-np.arange(tail) / (0.03 * RATE))
    tone = np.sin(2 * np.pi * 180 * np.arange(frames) / RATE) * 0.3 * envelope
    lead = np.zeros(round(0.1 * RATE) if quiet_first else 0)
    return (np.concatenate([lead, tone]) * 32767).astype(np.int16)


class Recognizer:
    """A recognizer that hears each take say its own thought, or what a test has it hear.

    A receipt's take is named for its thought's place and a candidate for its segment, its
    thought's place and its seed; `heard` maps a take's file name to other words.
    """

    def __init__(self) -> None:
        self.heard: dict[str, str] = {}
        self.thoughts = [*THOUGHTS, " Third thought."]

    def generate(self, path, *, language):
        name = Path(path).name
        if name in self.heard:
            return SimpleNamespace(text=self.heard[name])
        fields = Path(path).stem.split("-")
        place = int(fields[1] if fields[0] == "26" else fields[0])
        return SimpleNamespace(text=self.thoughts[place - 1])


class Aligner:
    """An aligner that places each word of a text 0.4 s long from 0.15 s, or as a test places it."""

    def __init__(self) -> None:
        self.placed: dict[str, list[tuple[str, float, float]]] = {}

    def generate(self, _path, *, text, language):
        words = self.placed.get(text) or [
            (word, 0.15 + 0.4 * number, 0.55 + 0.4 * number)
            for number, word in enumerate(text.replace(".", "").split())
        ]
        return SimpleNamespace(items=[Aligned(*word) for word in words])


@pytest.fixture
def voiced():
    """The synthetic voice of a thought take: `voiced(natural=False)` is cut while it sounds."""
    return voice


@pytest.fixture
def declared(monkeypatch):
    """Declare review settings, such as clarity lines, in the film the judgment reads."""

    import filmkit.narration.judgment as narration_judgment

    def declare(**review) -> None:
        update = {"review": film.FILM.review.model_copy(update=review)}
        monkeypatch.setattr(narration_judgment, "FILM", film.FILM.model_copy(update=update))

    return declare


@pytest.fixture
def stand_ins(monkeypatch):
    """The recognizer and the aligner every judgment of a test loads: `.recognizer`, `.aligner`."""
    import filmkit.narration.judgment as narration_judgment

    models = SimpleNamespace(recognizer=Recognizer(), aligner=Aligner())
    monkeypatch.setattr(narration_judgment, "load_asr", lambda: models.recognizer)
    monkeypatch.setattr(
        narration_judgment, "load_aligner", lambda: {"identity": IDENTITY, "model": models.aligner}
    )
    return models


@pytest.fixture
def narrated(retained_records, declared, stand_ins, tmp_path, monkeypatch):
    """An English edition whose receipt a test narrates from the PCM of its two thoughts.

    The film declares no clarity floor, and the recognizer and the aligner are stand-ins:
    `narrated.recognizer` and `narrated.aligner`.
    """
    from filmkit.narration.narrate import evidence_paths

    monkeypatch.setattr(repository, "ROOT", tmp_path)
    declared(clarity_minimum_db=None)
    edition = Edition("en")
    contract = "content/voice-performance.json"
    repository.write(contract, {"pronunciation": {"languages": {"English": {"normalization": []}}}})

    def narrate(pcms, plans=None) -> dict:
        plans = plans or [{"text": text, "spoken_text": text} for text in THOUGHTS]
        record, settings = retained_records(plans, pcms)
        record = {**record, "text_sha256": repository.content_sha(record["text"])}
        section = {
            "id": "26",
            "text": record["text"],
            "spoken_text": record["spoken_text"],
            "utterance_groups": [plan["text"] for plan in plans],
        }
        repository.write(
            edition.script, {"pronunciation_contract": contract, "segments": [section]}
        )
        if not (tmp_path / edition.cast).exists():
            cast = {
                "reference_audio": settings["reference_audio"],
                "reference_sha256": settings["reference_sha256"],
                "reference_text": settings["reference_text"],
                "narration_language": "English",
            }
            repository.write(edition.cast, cast)
        repository.write(evidence_paths("en")["receipt"], {"records": [record]})
        return record

    narrate.aligner, narrate.recognizer = stand_ins.aligner, stand_ins.recognizer
    return narrate


@pytest.fixture
def studio(narrated, voiced, monkeypatch, tmp_path):
    """An edition with a stand-in voice and a narration that follows the cast.

    `studio.sound(seed, text)` gives the PCM the voice says; a narration reads each retaken
    thought's candidate, as the engine narrates the same take again from the bound seed.
    """
    import converging

    import filmkit.narration.converge as narration_converge
    import filmkit.narration.group_generation as narration_group_generation

    state = SimpleNamespace(
        seed=None, said=[], narrations=0, loads=0, first=None, sound=None, root=tmp_path, words=None
    )

    class Voice:
        sample_rate = converging.RATE

        def __init__(self) -> None:
            state.loads += 1

        def generate(self, **request):
            state.said.append((state.seed, request["text"]))
            pcm = state.sound(state.seed, request["text"])
            yield SimpleNamespace(audio=(pcm / 32767).astype(np.float32))

    def narrate(code: str) -> None:
        state.narrations += 1
        retakes = repository.read(Edition(code).cast).get("retakes", {})
        groups = retakes.get("26", {}).get("groups", {})
        plans, pcms = [], []
        for index, text in enumerate(converging.THOUGHTS, 1):
            plan, pcm = {"text": text, "spoken_text": text}, state.first[index - 1]
            retake = groups.get(str(index))
            if retake:
                plan["seed"] = retake["seed"]
                if "run_on" in retake:
                    plan["run_on"] = retake["run_on"]
                name = f"26-{index:02d}-{retake['seed']}" + ("-on" if "run_on" in retake else "")
                with wave.open(
                    str(tmp_path / narration_converge.WORK / code / f"{name}.wav")
                ) as take:
                    pcm = np.frombuffer(take.readframes(take.getnframes()), dtype="<i2")
            plans.append(plan)
            pcms.append(pcm)
        record = narrated(pcms, plans)
        if state.words:
            converging.write_checks(code, [record], state.words)

    def begin(first: list) -> None:
        state.first = first
        record = narrated(first)
        if state.words:
            converging.write_checks("en", [record], state.words)

    state.begin, state.aligner, state.recognizer = begin, narrated.aligner, narrated.recognizer
    monkeypatch.setattr(narration_group_generation, "load_voice_model", Voice)
    monkeypatch.setattr(
        narration_group_generation.mx.random, "seed", lambda seed: setattr(state, "seed", seed)
    )
    monkeypatch.setattr(narration_converge, "narration_due", lambda _code: False)
    monkeypatch.setattr(narration_converge, "narrate", narrate)
    return state


@pytest.fixture
def engine(stand_ins, declared, voiced, monkeypatch, tmp_path):
    """An edition that the engine's own synthesis narrates, with a voice double.

    A narration runs `filmkit.narration.synthesis` in this process on the edition's script and
    cast, so its plan, its requests, its retained recordings and its receipt are the engine's;
    the two checks' outputs are written as of that receipt. `engine.sound(seed, text)` gives
    the PCM the voice says, and `engine.stop_at`, a seed and a text, has the voice take a
    request to end when it is asked for that take.
    """
    import converging

    import filmkit.child_processes as child_processes
    import filmkit.narration.converge as narration_converge
    import filmkit.narration.group_generation as narration_group_generation
    import filmkit.narration.synthesis as narration_synthesis

    monkeypatch.setattr(repository, "ROOT", tmp_path)
    declared(clarity_minimum_db=None)
    state = SimpleNamespace(seed=None, said=[], narrations=0, stop_at=None)
    state.sound = lambda _seed, _text: voiced()

    class Voice:
        sample_rate = converging.RATE

        def generate(self, **request):
            state.said.append((state.seed, request["text"]))
            if state.stop_at == (state.seed, request["text"]):
                raise child_processes.Terminated(signal.SIGTERM)
            pcm = state.sound(state.seed, request["text"])
            yield SimpleNamespace(audio=(pcm / 32767).astype(np.float32))

    snapshot = SimpleNamespace(folder="voice-snapshot", verify=lambda: None)
    monkeypatch.setattr(narration_group_generation, "VOICE", snapshot)
    monkeypatch.setattr(narration_group_generation, "load_model", lambda _path: Voice())
    monkeypatch.setattr(
        narration_group_generation.mx.random, "seed", lambda seed: setattr(state, "seed", seed)
    )
    edition, paths = Edition("en"), narration_converge.evidence_paths("en")
    reference = tmp_path / "reference.wav"
    reference.write_bytes(b"approved synthetic reference")
    contract = "content/voice-performance.json"
    repository.write(contract, {"pronunciation": {"languages": {"English": {"normalization": []}}}})
    section = {
        "id": "26",
        "text": "".join(converging.THOUGHTS),
        "utterance_groups": list(converging.THOUGHTS),
    }
    repository.write(edition.script, {"pronunciation_contract": contract, "segments": [section]})
    cast = {
        "reference_audio": "reference.wav",
        "reference_sha256": repository.sha(reference),
        "reference_text": "A reference.",
        "narration_language": "English",
        "reference_language": "English",
        "full_narration_seed": 4677,
    }
    repository.write(edition.cast, cast)
    sources = ["--script", edition.script, "--cast", edition.cast, "--folder", paths["folder"]]

    def narrate(code: str) -> None:
        state.narrations += 1
        narration_synthesis.narrate([*sources, "--receipt", paths["receipt"]])
        converging.write_checks(
            code, repository.read(paths["receipt"])["records"], converging.placed
        )

    monkeypatch.setattr(narration_converge, "narrate", narrate)
    state.paths = paths
    mx = narration_group_generation.mx
    previous = mx.set_cache_limit(0)
    mx.set_cache_limit(previous)
    yield state
    mx.set_cache_limit(previous)
    mx.clear_cache()


@pytest.fixture
def bench(studio, voiced, monkeypatch):
    """A count that stands in for the assembly's binding, decoding and measuring, for an
    edition that a test narrates with `bench.begin(first takes)`, which declares what the
    count reads.

    The measure is `fit_bench.Count`, with its `counted`, `room`, `joins`, `undesigned` and
    `tried`. Beside them `count.binding`, an exception, is what the binding of the recordings
    raises, and `count.selecting` what the selection raises; `count.selected` and `count.bound`
    count the questions.
    """
    import filmkit.narration.converge as narration_converge
    import filmkit.narration.fitting as fitting
    import filmkit.soundtrack.fit as soundtrack_fit

    state = fit_bench.Count()
    state.binding = state.selecting = None
    state.selected = state.bound = 0
    edition, paths = Edition("en"), narration_converge.evidence_paths("en")

    def declare(**fields) -> None:
        cast = repository.read(edition.cast)
        cast["performance_recording"] = {
            "receipt": paths["receipt"],
            "alignment": paths["alignment"],
        }
        repository.write(edition.cast, cast)
        script = repository.read(edition.script)
        policy = {**script.get("voice_performance", fit_bench.PERFORMANCE), **fields}
        repository.write(edition.script, {**script, "voice_performance": policy})

    def select(asked: Edition) -> None:
        state.selected += 1
        if state.selecting:
            raise state.selecting
        print(json.dumps({"selected": 1, "seconds": 4.2}))

    def bound(_script: dict, _edition: Edition) -> None:
        state.bound += 1
        if state.binding:
            raise state.binding

    def begin(first: list) -> None:
        studio.begin(first)
        declare()

    monkeypatch.setattr(fitting, "select", select)
    monkeypatch.setattr(soundtrack_fit, "_bound", bound)
    monkeypatch.setattr(soundtrack_fit, "measured", state.measured)
    state.declare, state.begin = declare, begin
    return state


@pytest.fixture
def count(bench, voiced):
    """A settled edition of two accepted takes, with the stand-in count."""
    bench.begin([voiced(), voiced()])
    return bench
