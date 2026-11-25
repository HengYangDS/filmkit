"""The sample film's chain on stand-in takes, for the tests of the run records.

`copy_film` copies the sample's tracked sources below a scratch root. `narrate` writes an
edition's narration there as the engine's synthesis writes it: its receipt, takes, take receipts
and request files built by the engine's own functions (`filmkit.narration.thought_groups`), from
a stand-in voice in place of the speech model, and the two checks' outputs, each word placed
where the voice says it. `run` runs a command of the chain as the film's task runs it, in a
process of its own with the scratch root as the film's root, recording what it opens where a log
is named (`filmkit.graph.opens`); `CHAIN` lists the commands the graph's tests build the sample
with, in the order of its tasks.

The stand-in voice says a Chinese character in 0.17 s and a Latin word in more, with a 180 Hz
voice and its harmonics, keeps quiet after each mark inside a thought, and dies away at the end of
each phrase, as a take that ends naturally does.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.graph import opens
from filmkit.narration import thought_groups
from filmkit.narration.narrate import evidence_paths
from filmkit.narration.pronunciation import (
    native_utterance_plan,
    pronunciation,
    pronunciation_text,
    validate_language_reference,
)
from filmkit.narration.retakes import segment_take
from filmkit.narration.voice_model import request_fingerprint
from filmkit.places import places
from filmkit.production import Edition

SAMPLE = Path(__file__).resolve().parents[2] / "examples/sample-film"
# The sample's tracked sources, which its build reads.
SOURCES = ("VERSION", "assets", "content", "picture")
RATE = 24000
LEAD, F0, TAIL = 0.1, 180.0, 0.12
# The quiet the voice keeps after each mark inside a thought, within the floor and the cap that
# each edition's script declares for it.
QUIET = {"，": 0.15, "、": 0.12, "；": 0.22, "：": 0.22, "。": 0.3, "？": 0.3, "！": 0.3}
QUIET |= {",": 0.08, ";": 0.15, ":": 0.15, ".": 0.18, "?": 0.18, "!": 0.18}
# A phrase and the marks that end it; a word, a Chinese character or a Latin word.
PHRASE = re.compile(rf"([^{re.escape(''.join(QUIET))}]+)([{re.escape(''.join(QUIET))}]*)")
WORD = re.compile(r"[\u3400-\u9fff]|[A-Za-z0-9'’]+")
# The editions narrated, and the commands run after, each with its edition, in the order of the
# sample's tasks: every node the light suite can run.
NARRATED = ("zh", "en")
SOUND = ("select", "assemble", "refresh-captions", "check-sound")
CHAIN = (
    *((command, "zh") for command in SOUND),
    *((command, "en") for command in SOUND),
    ("stage-picture", "zh"),
    ("package-metadata", "zh"),
    ("package-metadata", "en"),
)
# The runs that end refused here, each with its reason.
REFUSED: dict[tuple[str, str], str] = {}


def copy_film(root: Path) -> Path:
    """Copy the sample's tracked sources below `root`, which becomes a film's root, with the
    repository's npm packages, which the sample's build uses, linked beside them."""
    root.mkdir(parents=True, exist_ok=True)
    for name in SOURCES:
        source = SAMPLE / name
        if source.is_dir():
            shutil.copytree(source, root / name)
        else:
            shutil.copy2(source, root / name)
    (root / "node_modules").symlink_to(SAMPLE.parents[1] / "node_modules")
    return root


def voiced(seconds: float) -> np.ndarray:
    """A voice of 180 Hz and its harmonics for `seconds`, dying away over its last `TAIL`."""
    frames = round(seconds * RATE)
    time = np.arange(frames) / RATE
    tone = sum(np.sin(2 * np.pi * F0 * k * time) / k for k in range(1, 9))
    envelope, tail = np.ones(frames), round(TAIL * RATE)
    envelope[-tail:] = np.exp(-np.arange(tail) / (0.025 * RATE))
    return tone / np.max(np.abs(tone)) * 0.3 * envelope


def said(text: str) -> tuple[np.ndarray, list[dict]]:
    """A thought's PCM and its words, each placed in seconds from the thought's start: 0.17 s
    for a Chinese character, more for a longer Latin word, and after each phrase but the last
    the quiet of the mark that ends it."""
    pieces, words, cursor = [np.zeros(round(LEAD * RATE))], [], LEAD
    phrases = [(phrase, marks) for phrase, marks in PHRASE.findall(text) if WORD.search(phrase)]
    for number, (phrase, marks) in enumerate(phrases, 1):
        tokens = WORD.findall(phrase)
        lengths = [0.17 if len(token) == 1 else 0.1 + 0.04 * len(token) for token in tokens]
        pieces.append(voiced(sum(lengths)))
        for token, length in zip(tokens, lengths, strict=True):
            words.append({"text": token, "start_time": cursor, "end_time": cursor + length})
            cursor += length
        quiet = QUIET[marks[0]] if marks and number < len(phrases) else 0.05
        pieces.append(np.zeros(round(quiet * RATE)))
        cursor += quiet
    return np.rint(np.concatenate(pieces) * 32767).astype(np.int16), words


def write_pcm(path: Path, pcm: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(pcm.astype("<i2").tobytes())


def take(segment: dict, speech: dict, plan: list[dict], folder: Path, contract: str) -> tuple:
    """One segment's retained recording, with its thoughts, and its aligned words."""
    fingerprint = request_fingerprint(
        thought_groups.parent_request(segment["text"], segment["spoken_text"], speech, plan)
    )
    path = folder / f"{segment['id']}-{fingerprint[:12]}.wav"
    settings = thought_groups.group_settings(fingerprint, speech)
    pieces, records, joins, words, cursor = [], [], [], [], 0
    takes = [said(thought["text"]) for thought in plan]
    for index, (thought, (pcm, placed)) in enumerate(zip(plan, takes, strict=True), 1):
        request = thought_groups.child_request(settings, thought, index)
        wave_path = path.with_suffix("") / f"{index:02d}-{request_fingerprint(request)[:12]}.wav"
        write_pcm(wave_path, pcm)
        child = thought_groups.child_receipt(
            request,
            path=repository.relative(wave_path),
            wav_sha256=repository.sha(wave_path),
            frames=len(pcm),
            sample_rate=RATE,
            native_chunks=1,
        )
        receipt = wave_path.with_suffix(".json")
        repository.write(receipt, child)
        repository.write(
            wave_path.with_suffix(".request.json"),
            {"state": "received", "fingerprint": child["fingerprint"]},
        )
        records.append(
            {
                **child,
                "receipt": repository.relative(receipt),
                "receipt_sha256": repository.sha(receipt),
                "start_sample": cursor,
            }
        )
        at = cursor / RATE
        words += [
            {"text": w["text"], "start_time": w["start_time"] + at, "end_time": w["end_time"] + at}
            for w in placed
        ]
        pieces.append(pcm)
        cursor += len(pcm)
        if index < len(plan):
            native, added = thought_groups.join_quiet(pcm, takes[index][0], RATE)
            joins.append(
                {
                    "after_group": index,
                    "source_sample": cursor,
                    "native_quiet_frames": native,
                    "added_quiet_frames": added,
                    "removed_samples": 0,
                    "listening_accepted": False,
                }
            )
            pieces.append(np.zeros(added, dtype=np.int16))
            cursor += added
    write_pcm(path, np.concatenate(pieces))
    record = {
        "id": segment["id"],
        "path": repository.relative(path),
        "text": segment["text"],
        "spoken_text": segment["spoken_text"],
        "text_sha256": repository.content_sha(segment["text"]),
        "model": speech["model"],
        "revision": speech["revision"],
        "reference_sha256": speech["reference_sha256"],
        "reference_mode": "icl",
        "duration": cursor / RATE,
        "sample_rate": RATE,
        "elapsed": 0.0,
        "wav_sha256": repository.sha(path),
        "scope": "A stand-in voice for the tests of the run records",
        "fingerprint": fingerprint,
        "decoder": speech["decoder"],
        "stream": speech["stream"],
        "chunks": len(plan),
        "seed": speech["seed"],
        "temperature": speech["temperature"],
        "reference_text_sha256": repository.content_sha(speech["reference_text"]),
        "language": speech["language"],
        "reference_audio": speech["reference_audio"],
        "pronunciation_contract": contract,
        "pronunciation_contract_sha256": speech["pronunciation_contract_sha256"],
        "reference_treatment": speech["reference_treatment"],
        "post_pitch_transform": False,
        "post_tempo_transform": False,
        **(
            {"icl_repetition_penalty": speech["icl_repetition_penalty"]}
            if "icl_repetition_penalty" in speech
            else {}
        ),
        "utterance_groups": {
            "policy": thought_groups.GROUP_POLICY,
            "records": records,
            "joins": joins,
            "listening_accepted": False,
        },
    }
    thought_groups.validate_group_inputs(record, root=repository.ROOT, section=segment)
    return record, words


def narrate(code: str) -> None:
    """Write an edition's narration below the film's root, as `filmkit.narration.narrate` writes
    its receipt and its two checks' outputs, from the stand-in voice."""
    edition, paths = Edition(code), evidence_paths(code)
    script, cast = repository.read(edition.script), repository.read(edition.cast)
    contract, contract_sha256 = pronunciation(code)
    language = validate_language_reference(script, cast, code)
    reference = places(code, FILM.slug).reference
    folder = repository.ROOT / paths["folder"]
    records, aligned = [], []
    for written in script["segments"]:
        segment = {**written, "spoken_text": pronunciation_text(written, contract)}
        thoughts = native_utterance_plan(segment, contract)
        seed, temperature, plan = segment_take(segment, cast, thoughts)
        speech = thought_groups.cast_speech(
            cast,
            reference=reference,
            language=language,
            contract_sha256=contract_sha256,
            seed=seed,
            temperature=temperature,
        )
        contract_path = places(code, FILM.slug).pronunciation
        record, words = take(segment, speech, plan, folder, contract_path)
        records.append(record)
        row = {"id": record["id"], "wav_sha256": record["wav_sha256"], "path": record["path"]}
        aligned.append({**row, "text_sha256": record["text_sha256"], "items": words})
    repository.write(paths["receipt"], {"records": records})
    repository.write(paths["alignment"], {"records": aligned})
    keys = ("id", "wav_sha256", "path")
    heard = [{**{k: r[k] for k in keys}, "heard": r["text"]} for r in records]
    repository.write(paths["asr"], {"records": heard})


# A node's run in a process of its own, as `filmkit build` runs it once its plan holds it stale
# (`build.run_node`): the run's refusal or failure is its one line, and its status the run's.
RUN_NODE = (
    "import sys; from filmkit.graph import build, chain; "
    "status, said = build.run_node(chain.table(), sys.argv[1]); "
    "said and print(said, file=sys.stderr); sys.exit(status)"
)


def run(root: Path, command: str, code: str, log: Path | None = None) -> str:
    """Run a node of the film's chain on an edition, in its own process with `root` as the
    film's root, as `filmkit build` runs it; its output. A failure names its lines, and so does
    a run that `REFUSED` names and that passed."""
    environment = {**os.environ, repository.ROOT_VARIABLE: str(root)}
    environment.pop(opens.NODE, None)
    if log is not None:
        environment[opens.VARIABLE] = str(log)
    done = subprocess.run(
        [sys.executable, "-I", "-B", "-c", RUN_NODE, f"{command}:{code}"],
        env=environment,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if bool(done.returncode) != ((command, code) in REFUSED):
        raise AssertionError(f"{command} {code} exited {done.returncode}:\n{done.stderr[-3000:]}")
    return done.stdout
