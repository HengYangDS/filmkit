"""Fixtures of the delivery tests.

`film` is a root whose delivery sources are small texts, beside an absent Documents
destination; `inputs` is one edition's inputs bound as the film verifier reads them.
"""

import json
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

import pytest

import filmkit.delivery.documents_folder as delivery_documents_folder
import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.player as delivery_player
import filmkit.delivery.verification as delivery_verification
import filmkit.narration.selection as narration_selection
import filmkit.narration.thought_groups as narration_thought_groups
import filmkit.picture.equivalence as picture_equivalence
import filmkit.picture.rendering as picture_rendering
import filmkit.production as production
import filmkit.repository as repository
import filmkit.specification as specification
from filmkit.film import FILM

# The verified films last two seconds, the last of them credits.
DURATION, CREDITS = 2, 1


def write_input(path: Path, body: str | bytes | dict) -> Path:
    """Write text, bytes or a JSON object to a file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(body, dict):
        path.write_text(json.dumps(body), encoding="utf-8")
    elif isinstance(body, bytes):
        path.write_bytes(body)
    else:
        path.write_text(body, encoding="utf-8")
    return path


class Folder(NamedTuple):
    """A root whose delivery sources are small texts, and an absent destination."""

    root: Path
    destination: Path

    @staticmethod
    def write(path: Path, body: str | bytes) -> Path:
        return write_input(path, body)

    @staticmethod
    def tree(folder: Path) -> dict[str, str]:
        """Every file under a folder with its text."""
        return {
            path.relative_to(folder).as_posix(): path.read_text()
            for path in sorted(folder.rglob("*"))
            if path.is_file()
        }

    def better(self) -> None:
        """Replace every member source with a successor edition."""
        for source, path in delivery_documents_folder.plan(self.root):
            source.write_text(f"better {path}\n")


@pytest.fixture
def film(tmp_path, monkeypatch) -> Folder:
    """A root whose current members are small texts, and an absent destination.

    The players' real-browser readback passes every page, as its own tests read real pages.
    """
    folder = Folder(tmp_path / "root", tmp_path / "Documents" / FILM.documents_folder)
    for source, path in delivery_documents_folder.plan(folder.root):
        write_input(source, f"current {path}\n")
    monkeypatch.setattr(delivery_documents_folder, "check_players", passing_players)
    return folder


def passing_players(binding: Path, receipt: Path) -> int:
    """Stand in for the player check: every page of the bound delivery passes."""
    pages = [
        {"page": page, "verdict": "pass", "problems": []}
        for page in ("index.html", "zh/index.html", "en/index.html")
    ]
    write_input(receipt, {"pass": True, "pages": pages, "binding": str(binding)})
    return 0


def write_soundtrack(
    path: Path, frames: int, rate: int = specification.RATE, channels: int = 2
) -> None:
    """Write a silent 16-bit WAV soundtrack."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(b"\0\0" * channels * frames)


@dataclass
class Inputs:
    """One edition's current inputs, receipts and films below a test root, bound as recorded."""

    root: Path
    edition: production.Edition
    checked: list = field(default_factory=list)
    duration: int = DURATION
    credits: int = CREDITS

    @staticmethod
    def put(path: Path, body: str | bytes | dict) -> Path:
        return write_input(path, body)

    @staticmethod
    def change(path: Path, *keys: str, value: object) -> None:
        """Set one value in a JSON record, by its keys and list indices from the top."""
        record = json.loads(path.read_text(encoding="utf-8"))
        place = record
        for key in keys[:-1]:
            place = place[int(key) if isinstance(place, list) else key]
        last = keys[-1]
        place[int(last) if isinstance(place, list) else last] = value
        path.write_text(json.dumps(record), encoding="utf-8")

    def soundtrack(self, frames: int, rate: int = specification.RATE, channels: int = 2) -> None:
        """Replace the soundtrack and rebind its assembly to it."""
        write_soundtrack(self.edition.soundtrack, frames, rate, channels)
        sha = repository.sha(self.edition.soundtrack)
        self.change(self.edition.audio_assembly, "soundtrack_sha256", value=sha)


def shorten(monkeypatch) -> None:
    """Verify films of DURATION seconds whose last CREDITS seconds are credits."""
    monkeypatch.setattr(delivery_verification, "DURATION", DURATION)
    monkeypatch.setattr(delivery_verification, "CREDITS_DURATION", CREDITS)


@pytest.fixture
def short_films(monkeypatch) -> tuple[int, int]:
    """Verify films of DURATION seconds whose last CREDITS seconds are credits."""
    shorten(monkeypatch)
    return DURATION, CREDITS


def narration(inputs: Inputs, texts: dict[str, str]) -> None:
    """The script, cast, mirror, selected recordings, soundtrack, assembly and timeline."""
    root, edition, sha = inputs.root, inputs.edition, repository.sha
    script = write_input(
        root / edition.script,
        {"segments": [{"id": key, "text": text} for key, text in texts.items()]},
    )
    write_input(root / "assets/reference.wav", b"reference")
    reference = {
        "reference_audio": "assets/reference.wav",
        "reference_sha256": sha("assets/reference.wav"),
    }
    cast = write_input(root / edition.cast, reference)
    write_input(root / edition.mirror, "\n\n".join(texts.values()) + "\n")
    records = []
    for key, text in texts.items():
        recording = write_input(edition.ear_first / f"recordings/{key}.wav", f"take {key}")
        path = recording.relative_to(root).as_posix()
        records.append({"id": key, "text": text, "path": path, "wav_sha256": sha(recording)})
    write_input(
        edition.narration_selected,
        {"script_sha256": sha(script), "cast_sha256": sha(cast), "records": records},
    )
    write_soundtrack(edition.soundtrack, DURATION * specification.RATE)
    level = {
        "policy": specification.PROGRAM_LEVEL,
        "after": {"integrated_lufs": -16.6, "true_peak_dbtp": -1.2},
    }
    write_input(
        edition.audio_assembly,
        {
            "script_sha256": sha(script),
            "soundtrack_sha256": sha(edition.soundtrack),
            "program_level": level,
        },
    )
    segments = [{"id": key, "text": text} for key, text in texts.items()]
    captions = [
        {"start": 0.1, "end": 0.5, "text": "数据先行。"},
        {"start": 0.6, "end": 0.9, "text": "交付在后。"},
    ]
    write_input(edition.timeline, {"segments": segments, "captions": captions})


def picture(inputs: Inputs) -> None:
    """Both staged and rendered pictures, their render receipts and equivalence record, and the
    captioned picture's geometry and shot plan."""
    root, edition, sha = inputs.root, inputs.edition, repository.sha
    write_input(root / picture_rendering.COMPOSITION_SCRIPT, "/* film */")
    for captions in (True, False):
        rendered = edition.rendered(captions)
        write_input(rendered.stage / "index.html", f"<html>{rendered.name}</html>")
        write_input(rendered.file, f"{rendered.name} picture")
        receipt = {"picture": rendered.name, "output_sha256": sha(rendered.file)}
        write_input(rendered.receipt, receipt)
    equivalence = {
        **picture_equivalence.current_bindings(edition),
        "composition": {"instants": 5, "differing_instants": 0},
        "encoded": {"frames": 4, "failing_frames": 0},
        "findings": [],
        "verdict": "pass",
    }
    write_input(edition.caption_equivalence, equivalence)
    write_input(
        edition.picture_geometry,
        {
            "format": "picture-geometry",
            "passed": True,
            "findings": [],
            "errors": [],
            "index_sha256": sha(edition.picture_stage / "index.html"),
            "width": 3840,
            "height": 2160,
            "duration": DURATION,
            "fps": specification.FPS,
            "step_frames": 2,
            "checked": DURATION * specification.FPS // 2,
            "browser": "Chromium",
        },
    )
    write_input(
        root / edition.shot_plan,
        {
            "script_sha256": sha(root / edition.script),
            "composition_sha256": sha(root / picture_rendering.COMPOSITION_SCRIPT),
            "timeline_sha256": sha(edition.timeline),
        },
    )


def packages(inputs: Inputs) -> None:
    """The four films, the viewing members, the entry page and both package records."""
    root, edition, sha = inputs.root, inputs.edition, repository.sha
    output = edition.artifacts
    write_input(root / edition.cover, b"cover png")
    for name in delivery_packaging.viewing_members(edition):
        write_input(
            output / name, b"cover png" if name == delivery_packaging.COVER_PNG else f"{name}\n"
        )
    for film in edition.films:
        write_input(film, f"{film.name}\n")
    members = [
        {"path": edition.film(kind).name, "picture": edition.rendered(rendition.captions).name}
        for kind, rendition in production.RENDITIONS.items()
    ]
    write_input(
        edition.film_package,
        {
            **delivery_packaging.film_bindings(edition),
            "editions": [{**m, "sha256": sha(output / m["path"])} for m in members],
            "caption_owner": delivery_packaging.CAPTION_OWNER,
        },
    )
    for path, body in (
        (delivery_packaging.INDEX, "<entry template>"),
        (delivery_packaging.LANGUAGE_INDEX, "<entry page>"),
    ):
        write_input(root / path, body)
    write_input(
        edition.viewing_package,
        {
            "script_sha256": sha(root / edition.script),
            "timeline_sha256": sha(edition.timeline),
            "player": delivery_player.player_binding(edition),
            "language_index": {
                "source": str(delivery_packaging.INDEX),
                "source_sha256": sha(root / delivery_packaging.INDEX),
                "path": "build/artifacts/film/index.html",
                "sha256": sha(root / delivery_packaging.LANGUAGE_INDEX),
                "languages": ["zh", "en"],
            },
            "author": specification.AUTHOR,
            "chapters": delivery_packaging.CHAPTERS,
            "members": [
                {"path": name, "sha256": sha(output / name)}
                for name in delivery_packaging.viewing_members(edition)
            ],
        },
    )


@pytest.fixture
def inputs(tmp_path, monkeypatch) -> Inputs:
    """The Chinese edition's current bound inputs, for short films.

    The narration and render validators record their calls instead of reading recordings
    and renders, which their own tests cover.
    """
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    shorten(monkeypatch)
    current = Inputs(tmp_path, production.Edition("zh"))
    monkeypatch.setattr(
        narration_thought_groups,
        "validate_group_inputs",
        lambda record, *, root, **_: current.checked.append(("groups", record["id"], root)),
    )
    monkeypatch.setattr(
        narration_selection,
        "validate_voice_record",
        lambda record, cast: current.checked.append(("voice", record["id"], cast)),
    )
    monkeypatch.setattr(picture_rendering, "validate_picture_binding", lambda *_, **__: None)
    narration(current, {"01": "数据先行。", "02": "交付在后。"})
    picture(current)
    packages(current)
    return current
