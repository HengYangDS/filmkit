"""Fixtures of the delivery tests.

`film` is a root whose delivery sources are small texts, beside an absent destination;
`inputs` is one edition's inputs bound as the film verifier reads them, the still scan of its
1080p captioned film among them (`Inputs.scan_film`), and `editions` both
editions' with the manifest of the pinned sources; `built` is that build reviewed and held by
the film's own folder, for the tests of the release's writer (`release_build.Built`).
"""

import contextlib
import io
import json
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

import pytest
from release_build import Built

import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.packaging as delivery_packaging
import filmkit.delivery.player as delivery_player
import filmkit.narration.selection as narration_selection
import filmkit.narration.thought_groups as narration_thought_groups
import filmkit.picture.derivation as picture_derivation
import filmkit.picture.equivalence as picture_equivalence
import filmkit.picture.rendering as picture_rendering
import filmkit.picture.still_scan as picture_still_scan
import filmkit.production as production
import filmkit.repository as repository
import filmkit.review.record as review_record
import filmkit.sources as sources
import filmkit.specification as specification
from filmkit.film import FILM

# The runtime each edition's timeline states, which every check reads a film's length from, the
# last second of it credits: long enough to hold a still run of more than the scan's limit, and
# short enough for a soundtrack written whole.
RUNTIME, CREDITS = 8, 1
# The runtimes of a delivered film whose editions differ in length: 27:16 and 24:36.
EDITION_RUNTIMES = {"zh": 1636, "en": 1476}
# The film's version, which the bound root's VERSION holds.
VERSION = "1.3.0"


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
        for source, path in delivery_folder.plan(self.root):
            source.write_text(f"better {path}\n")


@pytest.fixture
def passing_scans(monkeypatch) -> None:
    """Stand in for the requirement of the still scan that delivery asks of each edition's
    1080p captioned film: every film passes, as the scan's own tests cover."""
    monkeypatch.setattr(picture_still_scan, "require_film_scan", lambda _edition: {})


@pytest.fixture
def film(tmp_path, monkeypatch, passing_scans) -> Folder:
    """A root whose current members are small texts, beside each edition's timeline, and an
    absent destination.

    The players' real-browser readback passes every page, as its own tests read real pages, and
    each edition's film passes its still scan (`passing_scans`).
    """
    folder = Folder(tmp_path / "root", tmp_path / "Movies" / FILM.delivery_folder)
    # The delivery asks the still scans of the film the command runs in, which is this root.
    monkeypatch.setattr(repository, "ROOT", folder.root)
    for source, path in delivery_folder.plan(folder.root):
        write_input(source, f"current {path}\n")
    for code, runtime in EDITION_RUNTIMES.items():
        write_input(production.Edition(code).timeline, {"duration": runtime})
    monkeypatch.setattr(delivery_folder, "check_players", passing_players)
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

    def review(self, report: str | None = None) -> Path:
        """Record a passing production review of the edition's current films, beside its report;
        the record."""
        edition, sha = self.edition, repository.sha
        text = report or f"# Review of {edition.code}\n"
        beside = write_input(edition.production_review.with_suffix(".md"), text)
        record = {
            "schema_version": review_record.SCHEMA_VERSION,
            "language": edition.code,
            "reviewer": "independent reviewer",
            "media": [
                {"path": repository.relative(film), "sha256": sha(film)} for film in edition.films
            ],
            "script_sha256": sha(self.root / edition.script),
            "composition_sha256": sha(self.root / picture_rendering.COMPOSITION_SCRIPT),
            "scores": dict.fromkeys(review_record.DIMENSIONS, 96),
            "overall": 96.0,
            "findings": [],
            "human_listening": {"state": "performed"},
            "report": {"path": repository.relative(beside), "sha256": sha(beside)},
        }
        return write_input(edition.production_review, record)

    def scan_film(self, *runs: dict) -> None:
        """Write the still scan record of the edition's 1080p captioned film as `scan-film`
        writes it, bound to the film, the timeline, the composition and the engine as they
        stand. The film's frames are not decoded: the scan reads a report that lists the given
        still runs, and a refusal of a run at the limit is left to the record's readers."""
        self.edition.film_stills.unlink(missing_ok=True)
        longest = max((run["speech"] for run in runs), default=0)
        report = {
            "fps": picture_still_scan.FPS,
            "frames": RUNTIME * picture_still_scan.FPS,
            "fine": {"rule": picture_still_scan.FINE_RULE, "runs": list(runs)},
            "coarse": {"rule": picture_still_scan.COARSE_RULE, "runs": []},
            "longest_fine_speech": longest,
        }
        phases = [report] * len(picture_still_scan.PHASES)
        with pytest.MonkeyPatch.context() as patch, contextlib.redirect_stdout(io.StringIO()):
            patch.setattr(picture_still_scan, "phase_reports", lambda *_: phases)
            with contextlib.suppress(picture_rendering.PictureError):
                picture_still_scan.scan_film(self.edition)


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
    write_soundtrack(edition.soundtrack, RUNTIME * specification.RATE)
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
    segments = [{"id": key, "text": text, "words": []} for key, text in texts.items()]
    captions = [
        {"start": 0.1, "end": 0.5, "text": "数据先行。"},
        {"start": 0.6, "end": 0.9, "text": "交付在后。"},
    ]
    timeline = {
        "segments": segments,
        "captions": captions,
        "duration": RUNTIME,
        "credits_duration": CREDITS,
    }
    write_input(edition.timeline, timeline)


def picture(inputs: Inputs, *, derived: bool = False) -> None:
    """Both staged and rendered pictures, their render receipts and equivalence record, and the
    captioned picture's geometry and shot plan. With `derived` the uncaptioned picture's receipt
    is a derivation's, which names no stage."""
    root, edition, sha = inputs.root, inputs.edition, repository.sha
    write_input(root / picture_rendering.COMPOSITION_SCRIPT, "/* film */")
    for captions in (True, False):
        rendered = edition.rendered(captions)
        write_input(rendered.page, f"<html>{rendered.name}</html>")
        write_input(rendered.file, f"{rendered.name} picture")
        receipt = {"picture": rendered.name, "output_sha256": sha(rendered.file)}
        if derived and not captions:
            receipt["derived"] = {"rows": [1872, 2048], "ground": {"y": 21, "u": 129, "v": 125}}
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
            "index_sha256": sha(edition.rendered().page),
            "width": 3840,
            "height": 2160,
            "duration": RUNTIME,
            "fps": specification.FPS,
            "step_frames": 2,
            "checked": RUNTIME * specification.FPS // 2,
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
    """The film's version, the four films, the viewing members, the entry page and both package
    records."""
    root, edition, sha = inputs.root, inputs.edition, repository.sha
    output = edition.artifacts
    write_input(root / "VERSION", f"{VERSION}\n")
    write_input(root / edition.cover, b"cover png")
    for name in delivery_packaging.viewing_members(edition):
        write_input(
            output / name, b"cover png" if name == delivery_packaging.COVER_PNG else f"{name}\n"
        )
    for film in edition.films:
        write_input(film, f"{film.name}\n")
    members = [
        {
            "path": edition.film(kind).name,
            "picture": edition.rendered(rendition.captions).name,
            # The picture file the film read: its own, or of a derived pair's 1080p uncaptioned
            # film the captioned one.
            "source": picture_derivation.film_source(edition, rendition)[0].name,
        }
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
            "version": VERSION,
            "chapters": delivery_packaging.CHAPTERS,
            "members": [
                {"path": name, "sha256": sha(output / name)}
                for name in delivery_packaging.viewing_members(edition)
            ],
        },
    )


@pytest.fixture
def inputs(tmp_path, monkeypatch) -> Inputs:
    """The Chinese edition's current bound inputs, for films of RUNTIME seconds whose last CREDITS
    seconds are credits, the passing still scan of its 1080p captioned film among them.

    The narration and render validators record their calls instead of reading recordings
    and renders, which their own tests cover.
    """
    monkeypatch.setattr(repository, "ROOT", tmp_path)
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
    current.scan_film()
    return current


@pytest.fixture
def editions(inputs, monkeypatch) -> dict[str, Inputs]:
    """Both editions' current bound inputs, each with its uncaptioned picture derived as the
    films make theirs: `inputs` and the English edition's beside it, bound the same way, each
    with the passing still scan of its film as it then stands, and the manifest of the pinned
    sources, which no local clone checks."""
    english = Inputs(inputs.root, production.Edition("en"), inputs.checked)
    narration(english, {"01": "Data first.", "02": "Delivery after."})
    for current in (inputs, english):
        picture(current, derived=True)
        packages(current)
        current.scan_film()
    monkeypatch.delenv(sources.CHECKOUT, raising=False)
    pinned = {"path": "README.md", "sha256": repository.content_sha("# The source\n")}
    write_input(
        inputs.root / sources.MANIFEST,
        {"repository": "https://example.test/source", "commit": "0" * 40, "members": [pinned]},
    )
    return {"zh": inputs, "en": english}


@pytest.fixture
def built(editions, tmp_path_factory, monkeypatch) -> Built:
    """A reviewed, delivered build. The staging's check of a stage is a stand-in that records
    what it was asked and refuses, in the staging's words, a document other than the one the
    fixture's sources stage; the real check has its own tests."""
    folder = tmp_path_factory.mktemp("host").resolve() / FILM.delivery_folder
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, str(folder.parent))
    current = Built(repository.ROOT, folder, editions, VERSION)

    def staged_now(edition, stage, *, captions=True):
        current.asked.append((edition.code, stage, captions))
        page = stage / production.STAGE_PAGE
        if page.read_text() != f"<html>{edition.rendered(captions).name}</html>":
            msg = "The staged document differs from the one the current sources derive"
            raise picture_rendering.PictureError(msg)
        return {}

    monkeypatch.setattr(picture_rendering, "require_current_stage", staged_now)
    for inputs in editions.values():
        inputs.review()
    current.deliver()
    return current
