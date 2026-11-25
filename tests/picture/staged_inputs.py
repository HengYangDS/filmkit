"""Both editions' current inputs below a film root, with the real composition, for the tests of
staging (`test_staging.py`) and rendering (`test_rendering.py`), which register `root` and
`staged` as their fixtures."""

import json
import shutil

import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.released as released
import filmkit.repository as repository
from filmkit.production import Edition

# The real composition, found before a test rebinds the repository root.
COMPOSITION = repository.ROOT / picture_rendering.COMPOSITION


# The runtime the fixture's timelines state: an odd number of seconds, unlike the sample's 60.
RUNTIME = 1477


def put(path, data):
    """Write text or JSON to a fixture file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


def root(tmp_path, monkeypatch):
    """A repository root with both editions' current inputs and the real composition."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    supported = {
        "name": picture_renderer.RENDERER_NAME,
        "version": picture_renderer.RENDERER_VERSION,
    }
    put(root / "node_modules" / picture_renderer.RENDERER_PACKAGE, supported)
    shutil.copytree(COMPOSITION, root / picture_rendering.COMPOSITION)
    put(root / repository.DECLARATION, 'slug = "sample-reel"\n')
    for path, source in picture_rendering.staged_members():
        if not (root / source).exists():
            put(root / source, f"fixture {path}")
    put(root / "content/source-manifest.json", {"members": []})
    for code, text in (("zh", "先看数据。"), ("en", "Read the data.")):
        edition = Edition(code)
        script = {"segments": [{"id": "01", "text": text}]}
        put(root / edition.script, script)
        segment = {"id": "01", "text": text, "words": []}
        timeline = {**script, "edition": code, "duration": RUNTIME, "segments": [segment]}
        timeline["captions"] = []
        put(edition.timeline, timeline)
        put(edition.soundtrack, f"{code} narration")
        assembly = {
            "script_sha256": repository.sha(edition.script),
            "soundtrack_sha256": repository.sha(edition.soundtrack),
        }
        put(edition.audio_assembly, assembly)
    return root


def passing_gates(edition, **changes):
    """A gate record that check-picture passed for the edition's current picture."""
    composition = repository.ROOT / picture_rendering.COMPOSITION_SCRIPT
    record = {
        "composition_sha256": repository.sha(composition),
        "timeline_sha256": repository.sha(edition.timeline),
        "declaration_sha256": repository.sha(repository.ROOT / repository.DECLARATION),
        "engine_version": released.version(),
        **picture_rendering.face_bindings(),
        "verdict": "pass",
        **changes,
    }
    put(edition.picture_gates, record)


def staged():
    """The Chinese edition, staged complete at the UHD frame, its picture checked."""
    edition = Edition("zh")
    picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
    passing_gates(edition)
    return edition
