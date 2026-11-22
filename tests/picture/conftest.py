"""Fixtures shared by the picture tests that stage and render.

`film_root` is a film root with both editions' current inputs and the real composition, whose
npm packages record the pinned canvas build and whose renderer is a stand-in: it records each
run beside itself, writes the next file queued for its output, or a text naming the stage it
rendered when none is queued, and reports the frames it drew, its text renderer and the native
library it loaded as the renderer does: the pinned library unless `FilmRoot.loads` names another.
"""

import json
import shutil
import sys
import textwrap
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

import pytest

import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.released as released
import filmkit.repository as repository
from filmkit.production import Edition
from filmkit.specification import DURATION

# The real composition, found before a test rebinds the repository root.
COMPOSITION = repository.ROOT / picture_rendering.COMPOSITION
# Each edition's one segment.
TEXTS = {"zh": "先看数据。", "en": "Read the data."}
# What npm recorded of the binary package in the fixture's film: a stand-in, since the engine
# pins that package's library by its bytes and no integrity of the package.
BINARY_RECORDED = "sha512-as-npm-recorded-the-binary-package"
# The stand-in renderer. Each run appends its arguments after its own path, its scheduling
# priority, its input and whether it leads its own session to runs.jsonl beside it. Its report
# states a digest of the stage it was given, or the one the file `drawn` beside it holds, and the
# native library the file `loaded.json` beside it names.
STAND_IN = """
import hashlib, json, os, pathlib, sys
here = pathlib.Path(sys.argv[0]).parent
output = pathlib.Path(sys.argv[sys.argv.index("--output") + 1])
run = {
    "argv": sys.argv[1:],
    "niceness": os.getpriority(os.PRIO_PROCESS, 0),
    "stdin": sys.stdin.read(),
    "session_leader": os.getsid(0) == os.getpid(),
}
with open(here / "runs.jsonl", "a") as runs:
    runs.write(json.dumps(run) + "\\n")
queue = here / "queue" / output.name
queued = sorted(queue.iterdir()) if queue.is_dir() else []
if queued:
    queued[0].replace(output)
else:
    output.write_text("rendered " + sys.argv[2])
drawn = here / "drawn"
report = {
    "frames": 1,
    "spans": int(sys.argv[sys.argv.index("--spans") + 1]),
    "text_renderer": sys.argv[sys.argv.index("--text-renderer") + 1],
    "binary": json.loads((here / "loaded.json").read_text()),
    "drawn_sha256": drawn.read_text() if drawn.exists()
    else hashlib.sha256(sys.argv[2].encode()).hexdigest(),
}
pathlib.Path(sys.argv[sys.argv.index("--report") + 1]).write_text(json.dumps(report))
"""


def put(path: Path, data: str | dict) -> Path:
    """Write text or JSON to a fixture file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


@dataclass(frozen=True)
class FilmRoot:
    """A film root with both editions' current inputs, and its stand-in renderer."""

    path: Path
    renderer: Path

    def timeline(self, edition: Edition, *, words=(), captions=()) -> None:
        """Give the edition's timeline these words in its segment and these captions."""
        script = repository.read(edition.script)
        segment = {**script["segments"][0], "words": list(words)}
        put(edition.timeline, {**script, "segments": [segment], "captions": list(captions)})

    def checked(self, edition: Edition) -> None:
        """Record that check-picture passed the edition's current picture."""
        record = {
            "composition_sha256": repository.sha(self.path / picture_rendering.COMPOSITION_SCRIPT),
            "timeline_sha256": repository.sha(edition.timeline),
            "engine_version": version(released.ENGINE),
            **picture_rendering.face_bindings(),
            "verdict": "pass",
        }
        put(edition.picture_gates, record)

    def staged(self, edition: Edition) -> None:
        """Stage both of the edition's pictures complete and record their passing check."""
        for captions in (True, False):
            picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160, captions=captions)
        self.checked(edition)

    def queue(self, output: Path, *files: Path) -> None:
        """Have the stand-in write these files, in turn, to `output` on its next runs."""
        folder = self.renderer.parent / "queue" / output.name
        folder.mkdir(parents=True, exist_ok=True)
        last = max((int(pending.stem) for pending in folder.iterdir()), default=0)
        for number, file in enumerate(files, last + 1):
            shutil.copyfile(file, folder / f"{number:03d}{file.suffix}")

    def installs(self, integrity: str | None = None) -> None:
        """Record what npm installed: the pinned canvas build, or the canvas package with the
        integrity given, as another build of that version has."""
        version = picture_renderer.RENDERER_VERSION
        pinned = picture_renderer.INTEGRITY
        name, binary = picture_renderer.RENDERER_NAME, picture_renderer.BINARY_PACKAGE
        packages = {
            f"node_modules/{name}": {"version": version, "integrity": integrity or pinned[name]},
            f"node_modules/{binary}": {"version": version, "integrity": BINARY_RECORDED},
        }
        put(self.path / "node_modules" / picture_renderer.INSTALLED, {"packages": packages})

    def loads(self, sha256: str | None = None, package: str | None = None) -> dict:
        """Have the stand-in report the native library it loaded: the pinned one of the pinned
        binary package, or another by its SHA-256 or its package. The library as it reports it."""
        loaded = {
            "path": str(self.renderer.parent / "skia.node"),
            "sha256": sha256 or picture_renderer.BINARY_SHA256,
            "package": package or picture_renderer.BINARY_PACKAGE,
            "version": picture_renderer.RENDERER_VERSION,
        }
        put(self.renderer.parent / "loaded.json", loaded)
        return loaded

    def canvas(self) -> dict:
        """The canvas a receipt names for a run of the stand-in as things stand: what the film
        installs, the library the stand-in reports with npm's record of its package, and the
        engine's text renderer."""
        return picture_renderer.drawn_by(
            {
                "text_renderer": picture_renderer.TEXT_RENDERER,
                "binary": repository.read(self.renderer.parent / "loaded.json"),
            }
        )

    def runs(self) -> list[dict]:
        """The stand-in's runs, in order."""
        log = self.renderer.parent / "runs.jsonl"
        lines = log.read_text().splitlines() if log.exists() else []
        return [json.loads(line) for line in lines]


@pytest.fixture
def film_root(tmp_path, monkeypatch) -> FilmRoot:
    """A film root with both editions' current inputs and the real composition, whose renderer
    is the stand-in."""
    root = tmp_path.resolve() / "film"
    monkeypatch.setattr(repository, "ROOT", root)
    supported = {
        "name": picture_renderer.RENDERER_NAME,
        "version": picture_renderer.RENDERER_VERSION,
    }
    put(root / "node_modules" / picture_renderer.RENDERER_PACKAGE, supported)
    shutil.copytree(COMPOSITION, root / picture_rendering.COMPOSITION)
    for path, source in picture_rendering.staged_members():
        if not (root / source).exists():
            put(root / source, f"fixture {path}")
    put(root / "content/source-manifest.json", {"members": []})
    for code, text in TEXTS.items():
        edition = Edition(code)
        script = {"duration": DURATION, "segments": [{"id": "01", "text": text}]}
        put(root / edition.script, script)
        put(edition.soundtrack, f"{code} narration")
        assembly = {
            "script_sha256": repository.sha(edition.script),
            "soundtrack_sha256": repository.sha(edition.soundtrack),
        }
        put(edition.audio_assembly, assembly)
    renderer = tmp_path.resolve() / "renderer" / "native-canvas"
    put(renderer, f"#!{sys.executable}\n{textwrap.dedent(STAND_IN)}").chmod(0o755)
    monkeypatch.setattr(picture_renderer, "launcher", lambda: [str(renderer)])
    film = FilmRoot(root, renderer)
    film.installs()
    film.loads()
    for code in TEXTS:
        film.timeline(Edition(code))
    return film
