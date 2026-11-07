"""The pre-render check: every stale or missing input of an edition's render, reported at once."""

import json
import shutil
from importlib.metadata import version

import pytest

import filmkit.concepts as concepts
import filmkit.picture.rendering as picture_rendering
import filmkit.preflight as preflight
import filmkit.produce as produce
import filmkit.repository as repository
from filmkit.production import Edition
from filmkit.specification import DURATION

# The sample film's composition, found before a test rebinds the repository root.
COMPOSITION = repository.ROOT / picture_rendering.COMPOSITION


def put(path, data):
    """Write text or JSON to a fixture file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


def painted(identical=True, cover_sha256="0" * 64, differing=0):
    """Stand in for the cover check: write its report and exit as it does."""
    calls = []

    def run(tool, arguments, *, environment=None, stdout=None):
        calls.append((tool, arguments))
        put(
            stdout,
            {"cover_sha256": cover_sha256, "differing_pixels": differing, "identical": identical},
        )
        return 0 if identical else 1

    return run, calls


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """The Chinese edition with every input of its render current: a stage of each of its current
    pictures, a passing gate record, a passing draft scan and no earlier package."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    supported = {"name": "hyperframes", "version": picture_rendering.RENDERER_VERSION}
    put(root / "node_modules" / picture_rendering.RENDERER_PACKAGE, supported)
    shutil.copytree(COMPOSITION, root / picture_rendering.COMPOSITION)
    for path, source in picture_rendering.staged_members():
        if not (root / source).exists():
            put(root / source, f"fixture {path}")
    put(root / "content/source-manifest.json", {"members": []})
    edition = Edition("zh")
    script = {"duration": DURATION, "segments": [{"id": "01", "text": "先看数据。"}]}
    put(root / edition.script, script)
    segment = {"id": "01", "text": "先看数据。", "words": []}
    put(edition.timeline, {**script, "segments": [segment], "captions": []})
    put(edition.soundtrack, "zh narration")
    assembly = {
        "script_sha256": repository.sha(edition.script),
        "soundtrack_sha256": repository.sha(edition.soundtrack),
    }
    put(edition.audio_assembly, assembly)
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160)
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160, captions=False)
    composition = repository.sha(root / picture_rendering.COMPOSITION_SCRIPT)
    put(
        edition.picture_gates,
        {
            "composition_sha256": composition,
            "timeline_sha256": repository.sha(edition.timeline),
            "engine_version": version("filmkit"),
            **picture_rendering.face_bindings(),
            "verdict": "pass",
        },
    )
    put(
        edition.draft_stills,
        {
            "timeline": {"sha256": repository.sha(edition.timeline)},
            "composition": {"sha256": composition},
            "limit_seconds": 3.5,
            "over_limit": [],
        },
    )
    monkeypatch.setattr(preflight.concepts, "check", lambda: {"status": "not_declared"})
    return edition


def test_an_edition_whose_inputs_are_current_passes(edition, monkeypatch, capsys):
    run, calls = painted()
    monkeypatch.setattr(preflight.tools, "run", run)
    report = preflight.preflight(edition)
    assert report == dict.fromkeys(
        [
            "stage",
            "uncaptioned_stage",
            "picture_gate",
            "draft_stills",
            "concepts",
            "film_package",
            "cover",
        ],
        "current",
    )
    assert json.loads(capsys.readouterr().out) == {"language": "zh", "inputs": report}
    # The cover is painted from the stage with the edition's tracked cover beside it.
    ((tool, arguments),) = calls
    assert tool == "player-check" and arguments[:3] == [
        "cover",
        str(edition.picture_stage),
        edition.cover,
    ]
    assert arguments[3] == str(repository.ROOT / "build/runtime/work/preflight/zh/cover.png")


def test_every_stale_input_is_named_at_once_and_refuses(edition, monkeypatch, capsys):
    run, calls = painted()
    monkeypatch.setattr(preflight.tools, "run", run)
    # The composition changes after its stage, its gate record and its draft scan.
    put(repository.ROOT / picture_rendering.COMPOSITION_SCRIPT, "scenes = {};\n")
    put(edition.film_package, {"picture_sha256": "0" * 64, "editions": []})

    def refuse():
        message = "01: 复刻 is a counterexample of rebuild\n02: says no rendering of offline"
        raise concepts.ConceptError(message)

    monkeypatch.setattr(preflight.concepts, "check", refuse)
    with pytest.raises(SystemExit) as refusal:
        produce.main(["preflight", "--language", "zh"])
    message = str(refusal.value)
    assert message.startswith("preflight: 7 stale or missing inputs before the zh render: stage: ")
    for named in (
        "stage: The staged document differs from the one the current sources derive; run "
        "stage-picture |",
        "uncaptioned_stage: The staged document differs from the one the current sources derive; "
        "run stage-picture --uncaptioned",
        "picture_gate: The zh picture gate record binds another composition_sha256",
        "draft_stills: build/evidence/editions/zh/draft-stills.json does not bind the current "
        "composition; scan a new draft",
        "concepts: 01: 复刻 is a counterexample of rebuild; 02: says no rendering of offline",
        "film_package: build/evidence/editions/zh/film-package.json binds other picture_sha256, "
        "uncaptioned_picture_sha256, caption_equivalence_sha256, soundtrack_sha256, cover_sha256, "
        "script_sha256, chapters_sha256, caption_owner; set its films aside first",
        "cover: not compared: the stage is not current",
    ):
        assert named in message
    # A stale stage paints no cover.
    assert calls == []
    printed = json.loads(capsys.readouterr().out)["inputs"]
    assert all(value != "current" for value in printed.values())


def test_a_package_of_the_current_inputs_is_named_for_the_picture_the_render_replaces(
    edition, monkeypatch
):
    monkeypatch.setattr(preflight.tools, "run", painted()[0])
    uncaptioned = edition.rendered(captions=False).file
    for path in (edition.picture, uncaptioned, edition.caption_equivalence):
        put(path, f"{path.name} bytes")
    put(edition.artifacts / "sample-reel-cover.jpg", "cover bytes")
    put(edition.artifacts / "chapters.ffmeta", ";FFMETADATA1\n")
    record = {**preflight.packaging.film_bindings(edition), "editions": []}
    put(edition.film_package, {**record, "caption_owner": preflight.packaging.CAPTION_OWNER})
    assert preflight.package(edition) == (
        "build/evidence/editions/zh/film-package.json binds the picture the render replaces; "
        "set its films aside first"
    )
    with pytest.raises(preflight.PreflightError, match="1 stale or missing inputs"):
        preflight.preflight(edition)


@pytest.mark.parametrize(
    ("painting", "named"),
    [
        (
            painted(identical=False, differing=1834),
            "assets/cover/sample-reel-cover.png differs in 1834 pixels from the cover the "
            "composition paints; track the painting build/runtime/work/preflight/zh/cover.png",
        ),
        (
            painted(identical=False, cover_sha256=None, differing=None),
            "no tracked cover at assets/cover/sample-reel-cover.png; track the painting "
            "build/runtime/work/preflight/zh/cover.png",
        ),
        (
            painted(identical=False, differing=None),
            "assets/cover/sample-reel-cover.png is not the size of the painting "
            "build/runtime/work/preflight/zh/cover.png",
        ),
    ],
)
def test_a_cover_other_than_the_composition_paints_is_named(edition, monkeypatch, painting, named):
    monkeypatch.setattr(preflight.tools, "run", painting[0])
    assert preflight.cover(edition) == named


def test_the_draft_scan_must_exist_and_pass(edition):
    record = repository.read(edition.draft_stills)
    put(edition.draft_stills, {**record, "over_limit": [{"start": 1, "end": 5, "speech": 3.9}]})
    assert preflight.draft(edition) == (
        "build/evidence/editions/zh/draft-stills.json finds 1 still pictures over 3.5 s of speech"
    )
    edition.draft_stills.unlink()
    assert preflight.draft(edition) == (
        "no still scan of the 10 fps draft at build/evidence/editions/zh/draft-stills.json"
    )


def test_a_missing_input_is_named_rather_than_raised(edition, monkeypatch):
    monkeypatch.setattr(preflight.tools, "run", painted()[0])
    edition.timeline.unlink()
    found = {
        name: check(edition)
        for name, check in (
            ("stage", preflight.stage),
            ("picture_gate", preflight.gates),
            ("draft_stills", preflight.draft),
        )
    }
    assert found == dict.fromkeys(found, "missing build/artifacts/film/zh/timeline.json")
