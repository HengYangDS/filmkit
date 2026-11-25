"""Fixtures shared by the narration tests and the declaration's, and the speech runtime and host
tool gates.

The engine's tests build the sample film: FILMKIT_ROOT names it here, before any engine module
loads the declaration of the film it builds, so no test reads another film's sources. They narrate
in one process (FILMKIT_NARRATION_PROCESSES).
"""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import wave
from pathlib import Path
from typing import NamedTuple

import derived_languages
import numpy as np
import pytest
import real_processes

os.environ["FILMKIT_ROOT"] = str(Path(__file__).resolve().parents[1] / "examples/sample-film")
# The tests narrate with a model double in this process. A narration that divided its segments
# among processes would start the real speech model in each, so the count is 1 unless a test of
# the processes names another.
os.environ["FILMKIT_NARRATION_PROCESSES"] = "1"

import filmkit.child_processes as child_processes
import filmkit.delivery.folder as delivery_folder
import filmkit.languages as languages
import filmkit.narration.cmudict as narration_cmudict
from filmkit.narration.thought_groups import join_quiet
from filmkit.narration.voice_model import MODEL, NATIVE_DECODER, REVISION

# Test modules whose code under test imports the MLX speech runtime at module load.
SPEECH_RUNTIME_MODULES = [
    "narration/test_alignment.py",
    "narration/test_audition.py",
    "narration/test_converge.py",
    "narration/test_converge_edges.py",
    "narration/test_converge_fit.py",
    "narration/test_converge_fit_refusals.py",
    "narration/test_group_generation.py",
    "narration/test_judgment.py",
    "narration/test_synthesis.py",
    "narration/test_synthesis_processes.py",
    "narration/test_transcription.py",
]


def speech_runtime() -> bool:
    """Whether the MLX speech runtime loads, which needs a Metal device.

    A failed import of mlx.core aborts a later attempt in the same process, so a child
    process probes.
    """
    probe = subprocess.run(
        [sys.executable, "-c", "import mlx.core"], capture_output=True, check=False, timeout=120
    )
    return probe.returncode == 0


# Modules that run the speech model are collected only where its runtime loads. The header
# and the summary of every run name the modules a run without it leaves out.
collect_ignore = [] if speech_runtime() else SPEECH_RUNTIME_MODULES


def metal_evaluates() -> bool:
    """Whether the speech runtime evaluates an array on the host's Metal device.

    The runtime loads on a device that builds no compute pipeline: on 18 November 2026 the
    paravirtual GPU of a virtual machine failed every evaluation, and the one test that evaluates
    on the device failed there in two hosted proofs of a sound commit. A child process probes,
    as for the load; a probe that does not end is a device that does not evaluate.
    """
    if collect_ignore:
        return False
    try:
        probe = subprocess.run(
            [sys.executable, "-c", "import mlx.core as mx; mx.eval(mx.zeros((1024,)) + 1)"],
            capture_output=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False
    return probe.returncode == 0


class HostTool(NamedTuple):
    """What a host must have for the tests marked with its marker to run."""

    name: str
    runs: str
    present: bool
    missing: str = "is not on PATH"


def rsync_3() -> bool:
    """Whether the rsync on PATH is the rsync 3 that delivery requires."""
    return bool(shutil.which("rsync")) and delivery_folder.rsync_version().startswith(
        delivery_folder.RSYNC_3
    )


def cmudict_supplied() -> bool:
    """Whether the supply step placed the pinned CMUdict below the sample film's root, where
    `mise run sample:supply` places it, its SHA-256 the pin's (`filmkit.narration.cmudict`)."""
    place = Path(os.environ["FILMKIT_ROOT"]) / narration_cmudict.PLACE
    return place.is_file() and (
        hashlib.sha256(place.read_bytes()).hexdigest() == narration_cmudict.SHA256
    )


# Production runs host tools that Homebrew installs and the locked toolchain does not supply:
# FFmpeg with libx264, ExifTool for the films' QuickTime keys, and rsync 3 for delivery, since
# macOS's own rsync is openrsync. Tests
# marked with a tool's marker run it and are skipped where it is not on PATH; the header and the
# summary of every run name the tests it skips. A test that evaluates on the host's Metal device
# is marked and skipped the same way where the device evaluates nothing, and one that reads the
# pinned CMUdict where the supply step has not placed it below the sample film's root.
HOST_TOOLS = {
    "ffmpeg": HostTool(
        "host FFmpeg",
        "the host FFmpeg and FFprobe",
        all(shutil.which(tool) for tool in ("ffmpeg", "ffprobe")),
    ),
    "exiftool": HostTool("host ExifTool", "the host ExifTool", bool(shutil.which("exiftool"))),
    "rsync": HostTool("host rsync 3", "the host rsync 3", rsync_3()),
    "metal": HostTool(
        "host Metal evaluation",
        "an evaluation on the host's Metal device",
        metal_evaluates(),
        "fails",
    ),
    "cmudict": HostTool(
        "supplied CMUdict",
        "a read of the pinned CMUdict that the supply step places below the sample film's root",
        cmudict_supplied(),
        f"is not at {narration_cmudict.PLACE} with its pinned SHA-256; run "
        f"{narration_cmudict.SUPPLY}",
    ),
}
host_skipped: dict[str, list[str]] = {marker: [] for marker in HOST_TOOLS}


# The only step of the engine that reaches the network is a film's supply (`filmkit supply`),
# which every test stubs; any other test that connects beyond this host is refused, in this
# process, rather than reaching it. A test's child processes are the engine's own commands, none
# of which connects.
LOCAL = ("127.0.0.1", "::1", "localhost")


def local(address) -> bool:
    """Whether a socket's address is a path or a name of this host."""
    return not isinstance(address, tuple) or address[0] in LOCAL


def refused_beyond_this_host(connect):
    def guarded(self, address, *rest):
        if not local(address):
            message = f"the engine's tests reach no network: a connection to {address}"
            raise ConnectionRefusedError(message)
        return connect(self, address, *rest)

    return guarded


def pytest_configure(config) -> None:
    """Register the markers of the tests that run a host tool, and refuse every connection
    beyond this host (`refused_beyond_this_host`)."""
    socket.socket.connect = refused_beyond_this_host(socket.socket.connect)
    socket.socket.connect_ex = refused_beyond_this_host(socket.socket.connect_ex)
    for marker, tool in HOST_TOOLS.items():
        config.addinivalue_line("markers", f"{marker}: runs {tool.runs}")
    config.addinivalue_line(
        "markers", "deadline(seconds): the seconds a test that starts real processes may take"
    )


def pytest_collection_modifyitems(items) -> None:
    """Skip the tests that run a host tool where the host does not have it."""
    for marker, tool in HOST_TOOLS.items():
        if tool.present:
            continue
        skip = pytest.mark.skip(reason=f"the {tool.name} {tool.missing}")
        for item in items:
            if item.get_closest_marker(marker):
                item.add_marker(skip)
                host_skipped[marker].append(item.nodeid)


@pytest.fixture(autouse=True)
def requests_restored():
    """After each test, forget a request to end that the test handed this process as the
    interpreter does, and put back the handlers that stood before (`child_processes.restore`):
    a command that was asked to end keeps them taken to its exit, and the test run goes on."""
    yield
    child_processes.restore()


# Seconds a test that starts real processes may take before it fails.
PROCESS_TEST_DEADLINE = 60


@pytest.fixture
def processes(tmp_path, request):
    """The real processes of one test (`real_processes.Processes`), killed when the test is over
    whatever it did. A test that has not ended within `PROCESS_TEST_DEADLINE` seconds, or those
    its `deadline` marker names, as a test of many trials does, fails there, so that a hang
    fails the test and does not stall the run."""
    started = real_processes.Processes(tmp_path.resolve())
    named = request.node.get_closest_marker("deadline")
    try:
        with real_processes.deadline(named.args[0] if named else PROCESS_TEST_DEADLINE):
            yield started
    finally:
        started.end()


@pytest.fixture
def speech():
    """Skip a test whose command loads the speech runtime where that runtime does not load, by
    the probe that leaves the speech modules out of such a run."""
    if collect_ignore:
        pytest.skip("the speech runtime does not load on this host")


def pytest_report_header() -> list[str]:
    speech = (
        f"speech runtime: absent; not collected: {', '.join(collect_ignore)}"
        if collect_ignore
        else "speech runtime: present; every speech runtime module collected"
    )
    tools = [
        f"{tool.name}: present; every test marked {marker} runs"
        if tool.present
        else f"{tool.name}: absent; the tests marked {marker} are skipped"
        for marker, tool in HOST_TOOLS.items()
    ]
    return [speech, *tools]


def pytest_terminal_summary(terminalreporter) -> None:
    if collect_ignore:
        terminalreporter.write_sep(
            "!",
            f"speech runtime absent: {len(collect_ignore)} test modules not collected",
            yellow=True,
        )
        for module in collect_ignore:
            terminalreporter.write_line(f"not collected: tests/{module}")
    for marker, skipped in host_skipped.items():
        if not skipped:
            continue
        terminalreporter.write_sep(
            "!", f"{HOST_TOOLS[marker].name} absent: {len(skipped)} tests skipped", yellow=True
        )
        for test in skipped:
            terminalreporter.write_line(f"skipped: {test}")


@pytest.fixture
def declared(tmp_path):
    """A copy of the sample film's declaration and every file it names, below a new root."""
    import declaring

    return declaring.copied(tmp_path)


@pytest.fixture
def unleveled(monkeypatch) -> None:
    """The sample film without its review levels, as a film that declares none reads: its
    prompts, records and verification keep the overall and dimension floors alone."""
    import filmkit.review.prompts as review_prompts
    import filmkit.review.record as review_record

    review = review_prompts.FILM.review.model_copy(update={"levels": None})
    monkeypatch.setattr(review_record, "LEVELS", None)
    monkeypatch.setattr(
        review_prompts, "FILM", review_prompts.FILM.model_copy(update={"review": review})
    )


def write_pcm(path, pcm, rate) -> None:
    """Write mono 16-bit PCM as a WAV file, as the narration receipts record it."""
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(np.asarray(pcm, dtype="<i2").tobytes())


GROUP_SETTINGS = {
    # The English edition's reference recording, at the place its code derives.
    "reference_audio": "assets/audio/en/narration-reference.wav",
    "reference_text": "Reference.",
    "reference_treatment": None,
    "seed": 1,
    "temperature": 0.46,
    "max_tokens": 1900,
    "language": "English",
    "model": MODEL,
    "revision": REVISION,
    "decoder": NATIVE_DECODER,
    "stream": False,
    "pronunciation_contract_sha256": "c" * 64,
}


def retained_record(
    root, plans: list[dict], pcms: list[np.ndarray], reference: str | None = None
) -> tuple[dict, dict]:
    """Retain thought recordings of the given PCM, joined with only added quiet, and their receipts.

    The takes record their reference recording at `reference`, the English edition's place
    unless one is named, where the recording is written.

    A thought whose plan reads on into its run-on records the frames of its native take, which
    are its own frames plus those cut after them, as many again here.

    Returns:
        The joined recording's record and the speech settings its thoughts share.
    """
    recorded = {**GROUP_SETTINGS, **({"reference_audio": reference} if reference else {})}
    reference = root / recorded["reference_audio"]
    reference.parent.mkdir(parents=True, exist_ok=True)
    write_pcm(reference, np.full(24000, 300, dtype=np.int16), 24000)
    settings = {
        **recorded,
        "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
    }
    text = "".join(plan["text"] for plan in plans)
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "text": text,
                "spoken": text,
                "reference": settings["reference_sha256"],
                "reference_text": settings["reference_text"],
                **{
                    key: settings[key]
                    for key in (
                        "seed",
                        "temperature",
                        "max_tokens",
                        "language",
                        "model",
                        "revision",
                        "decoder",
                        "stream",
                    )
                },
                "utterance_plan": plans,
                "join_quiet_minimum": 0.30,
                "pronunciation_contract": settings["pronunciation_contract_sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    parent = root / "build/audio" / f"26-{fingerprint[:12]}.wav"
    parent.with_suffix("").mkdir(parents=True)
    records, pieces, joins, cursor = [], [], [], 0
    for index, (plan, pcm) in enumerate(zip(plans, pcms, strict=True), 1):
        inputs = {"parent_fingerprint": fingerprint, **settings, **plan, "index": index}
        child_hash = hashlib.sha256(
            json.dumps(inputs, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        path = parent.with_suffix("") / f"{index:02d}-{child_hash[:12]}.wav"
        write_pcm(path, pcm, 24000)
        child = {
            **inputs,
            "fingerprint": child_hash,
            "path": path.relative_to(root).as_posix(),
            "wav_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "frames": len(pcm),
            "sample_rate": 24000,
            "native_chunks": 1,
            **({"native_frames": 2 * len(pcm)} if "run_on" in plan else {}),
            "post_pitch_transform": False,
            "post_tempo_transform": False,
        }
        receipt = path.with_suffix(".json")
        receipt.write_text(json.dumps(child))
        path.with_suffix(".request.json").write_text(
            json.dumps({"state": "received", "fingerprint": child_hash})
        )
        if pieces:
            native, added = join_quiet(pcms[index - 2], pcm, 24000)
            joins.append(
                {
                    "after_group": index - 1,
                    "source_sample": cursor,
                    "native_quiet_frames": native,
                    "added_quiet_frames": added,
                    "removed_samples": 0,
                    "listening_accepted": False,
                }
            )
            pieces.append(np.zeros(added, dtype=np.int16))
            cursor += added
        records.append(
            {
                **child,
                "receipt": receipt.relative_to(root).as_posix(),
                "receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
                "start_sample": cursor,
            }
        )
        pieces.append(pcm)
        cursor += len(pcm)
    write_pcm(parent, np.concatenate(pieces), 24000)
    record = {
        "id": "26",
        "text": text,
        "spoken_text": text,
        "fingerprint": fingerprint,
        "path": parent.relative_to(root).as_posix(),
        "wav_sha256": hashlib.sha256(parent.read_bytes()).hexdigest(),
        **{
            key: value
            for key, value in settings.items()
            if key not in ("reference_text", "max_tokens")
        },
        "reference_text_sha256": hashlib.sha256(settings["reference_text"].encode()).hexdigest(),
        "sample_rate": 24000,
        "duration": cursor / 24000,
        "utterance_groups": {"records": records, "joins": joins, "listening_accepted": False},
    }
    return record, settings


# Where an English reference recording stood before its edition's reference came to stand at the
# place its code derives: the path a take recorded then.
MOVED_FROM = "assets/audio/narration-reference.wav"


@pytest.fixture
def retained_group_record(tmp_path, request):
    """Construct native PCM and exact receipts without loading a speech model.

    With the indirect parameter "moved", the takes record their reference where it stood
    before the move, `MOVED_FROM`, and the recording is then moved, its bytes unchanged, to the
    English edition's place.
    """
    plans = [{"text": text, "spoken_text": text} for text in ("First thought.", " Second thought.")]
    pcms = [np.full(48000, 1000 * index, dtype=np.int16) for index in (1, 2)]
    moved = getattr(request, "param", None) == "moved"
    record, settings = retained_record(tmp_path, plans, pcms, MOVED_FROM if moved else None)
    if moved:
        place = tmp_path / GROUP_SETTINGS["reference_audio"]
        place.parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / MOVED_FROM).rename(place)
    return tmp_path, record, plans, settings


def dying(frames: int, rate: int = 24000) -> np.ndarray:
    """A 16-bit voice that holds and then dies away over its last 0.3 s, ending naturally."""
    tail = round(0.3 * rate)
    envelope = np.concatenate([np.ones(frames - tail), np.exp(-np.arange(tail) / (0.03 * rate))])
    tone = np.sin(2 * np.pi * 180 * np.arange(frames) / rate) * 0.3 * envelope
    return (tone * 32767).astype(np.int16)


@pytest.fixture
def retained_records(tmp_path):
    """Retain a recording from thought plans and their PCM, as often as a test narrates."""

    def build(plans: list[dict], pcms: list[np.ndarray]) -> tuple[dict, dict]:
        return retained_record(tmp_path, plans, pcms)

    return build


@pytest.fixture
def run_on_record(tmp_path):
    """Build a retained recording whose second thought was read on into the words after it.

    The second thought's take ends as its PCM ends: dying away, or cut while voiced.
    """

    def build(*, natural: bool = True):
        plans = [
            {"text": "First thought.", "spoken_text": "First thought."},
            {
                "text": " Second thought.",
                "spoken_text": " Second thought.",
                "seed": 7,
                "run_on": {"spoken_text": " Next words.", "cut_sample": 48000},
            },
        ]
        second = dying(48000) if natural else np.full(48000, 2000, dtype=np.int16)
        record, settings = retained_record(
            tmp_path, plans, [np.full(48000, 1000, dtype=np.int16), second]
        )
        return tmp_path, record, plans, settings

    return build


@pytest.fixture
def test_languages(monkeypatch):
    """The engine with the test languages `xa` and `xb` declared beside its own
    (`derived_languages`)."""
    for code in derived_languages.DERIVED:
        monkeypatch.setitem(languages.LANGUAGES, code, derived_languages.derived(code))
    return {code: languages.LANGUAGES[code] for code in derived_languages.DERIVED}


@pytest.fixture
def test_editions(test_languages, monkeypatch):
    """The sample film with the editions `xa` and `xb` beside its own, in the test languages of
    those codes: `xa` declared as the Chinese edition is and `xb` as the English one."""
    import filmkit.production as production
    from filmkit.film import FILM

    for code, source in (("xa", "zh"), ("xb", "en")):
        monkeypatch.setitem(FILM.editions, code, FILM.editions[source])
    monkeypatch.setattr(production, "CODES", (*production.CODES, "xa", "xb"))
    return test_languages


@pytest.fixture
def table_of(monkeypatch):
    """Hold the engine's node table to the nodes named, each declaring only the inputs that stand
    when it is asked, so that `filmkit verify` judges a fixture's build of those nodes alone as
    whole: a fixture stages no picture and writes no declaration's every file. Give the names,
    and get the table."""
    from dataclasses import replace

    from filmkit.graph import chain, nodes, records, runs

    def standing(way):
        def inputs(edition):
            found = way(edition)
            return nodes.Places({k: v for k, v in found.items() if records.file_of(v).exists()})

        return inputs

    def only(*names: str):
        held = [
            replace(node, ways={name: standing(way) for name, way in node.ways.items()})
            for node in chain.TABLE
            if node.name in names
        ]
        shared = {
            output: kept
            for output, writers in chain.SHARED.items()
            if (kept := tuple(w for w in writers if w.node in names))
        }
        table = nodes.load(held, shared, chain.CODES)
        monkeypatch.setattr(chain, "table", lambda: table)
        monkeypatch.setattr(runs, "table", lambda: {node.name: node for node in held})
        return table

    return only
