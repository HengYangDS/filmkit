"""The pre-render check: every stale or missing input of an edition's render, reported at once,
and the readiness receipt it writes."""

import json
import shutil
from importlib.metadata import version

import pytest
import still_records

import filmkit.concepts as concepts
import filmkit.picture.renderer as picture_renderer
import filmkit.picture.rendering as picture_rendering
import filmkit.preflight as preflight
import filmkit.produce as produce
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.production import Edition
from filmkit.specification import DURATION, FPS

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
    pictures, passing gate records of its picture and its sound, a geometry record of its stage,
    a passing draft scan and no earlier package."""
    root = tmp_path.resolve()
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
    put(root / repository.DECLARATION, 'slug = "sample-reel"\n')
    put(root / FILM.entry, "<title>Sample</title>\n")
    put(root / "VERSION", "1.3.0\n")
    edition = Edition("zh")
    script = {"duration": DURATION, "segments": [{"id": "01", "text": "先看数据。"}]}
    put(root / edition.script, script)
    put(root / edition.cast, {"voice": "narrator"})
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
    put(edition.draft_stills, still_records.draft_stills(edition))
    put(
        edition.sound_gates,
        {
            "soundtrack_sha256": repository.sha(edition.soundtrack),
            "timeline_sha256": repository.sha(edition.timeline),
            "engine_version": version("filmkit"),
            "clarity": {"floor_db": 18.0, "thoughts": []},
            "verdict": "pass",
        },
    )
    put(
        edition.picture_geometry,
        {
            "format": "picture-geometry",
            "passed": True,
            "findings": [],
            "errors": [],
            "index_sha256": repository.sha(edition.picture_stage / "index.html"),
            "width": 3840,
            "height": 2160,
            "duration": DURATION,
            "fps": FPS,
            "step_frames": 2,
            "checked": -(-DURATION * FPS // 2),
        },
    )
    monkeypatch.setattr(preflight.concepts, "check", lambda: {"status": "not_declared"})
    monkeypatch.setattr(preflight.register, "check", lambda: {"warnings": []})
    return edition


def declaring(monkeypatch, **fields):
    """The film with `fields` of its picture, review or captions replaced."""
    updates = {}
    for table, values in fields.items():
        updates[table] = getattr(FILM, table).model_copy(update=values)
    monkeypatch.setattr(preflight, "FILM", FILM.model_copy(update=updates))


# Every question of the check, in the order it reports them.
# The questions a test stands in for when it only needs a receipt.
ASKED = ("stage", "gates", "sound", "caption_rate", "geometry", "draft", "package", "cover")
QUESTIONS = [
    "stage",
    "uncaptioned_stage",
    "picture_gate",
    "sound_gate",
    "thought_clarity",
    "caption_rate",
    "geometry",
    "draft_stills",
    "concepts",
    "register",
    "film_package",
    "cover",
]


def test_an_edition_whose_inputs_are_current_passes(edition, monkeypatch, capsys):
    run, calls = painted()
    monkeypatch.setattr(preflight.tools, "run", run)
    report = preflight.preflight(edition)
    # The sample film declares no line for a single thought.
    expected = {**dict.fromkeys(QUESTIONS, "current"), "thought_clarity": preflight.NO_THOUGHT_LINE}
    assert report == expected and list(report) == QUESTIONS
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
        "draft_stills: build/evidence/editions/zh/draft-stills.json binds another composition; "
        "scan a new draft",
        "concepts: 01: 复刻 is a counterexample of rebuild; 02: says no rendering of offline",
        "film_package: build/evidence/editions/zh/film-package.json binds other picture_sha256, "
        "uncaptioned_picture_sha256, caption_equivalence_sha256, soundtrack_sha256, cover_sha256, "
        "script_sha256, chapters_sha256, version_sha256, caption_owner; set its films aside first",
        "cover: not compared: the stage is not current",
    ):
        assert named in message
    # A stale stage paints no cover.
    assert calls == []
    printed = json.loads(capsys.readouterr().out)["inputs"]
    stale = ("sound_gate", "caption_rate", "geometry", "thought_clarity", "register")
    assert all(value != "current" for name, value in printed.items() if name not in stale)
    # The receipt holds the refusal and what it was judged on.
    receipt = repository.read(edition.readiness)
    assert receipt["verdict"] == "refuse" and receipt["inputs"] == printed


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


def test_a_film_that_declares_no_drafts_is_not_asked_for_a_draft_scan(edition, monkeypatch):
    monkeypatch.setattr(preflight.tools, "run", painted()[0])
    edition.draft_stills.unlink()
    declaring(monkeypatch, picture={"drafts": False})
    assert preflight.preflight(edition)["draft_stills"] == preflight.NO_DRAFTS
    declaring(monkeypatch, picture={"drafts": True})
    with pytest.raises(preflight.PreflightError, match="1 stale or missing inputs.*draft_stills"):
        preflight.preflight(edition)


def test_the_draft_scan_must_exist_and_pass(edition):
    named = "build/evidence/editions/zh/draft-stills.json"
    held = [{"start": 1, "end": 5, "speech": 3.9}]
    record = still_records.draft_stills(edition, held)
    put(edition.draft_stills, record)
    assert preflight.draft(edition) == (
        f"{named} finds 1 still pictures with 3.5 s of speech or more"
    )
    # The record is read as the film's is (`tests/picture/test_still_record.py`): a draft
    # scanned with a laxer limit, which calls nothing over its own, states other rules than the
    # engine's, and a record that lists its runs in no form the scan writes cannot be read.
    laxer = {"rules": {**record["rules"], "limit_seconds": 99}, "limit_seconds": 99}
    put(edition.draft_stills, {**record, **laxer, "over_limit": []})
    assert preflight.draft(edition) == (
        f"{named} states other rules than the engine's: a limit of 99 s where the engine's is "
        "3.5 s; scan a new draft"
    )
    put(edition.draft_stills, {**record, "fine": {"runs": [{"speech": "3.9"}]}})
    assert preflight.draft(edition) == f"{named} cannot be read; scan a new draft"
    edition.draft_stills.unlink()
    assert preflight.draft(edition) == f"no still scan of the 10 fps draft at {named}"


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


def test_the_sound_gate_must_have_passed_the_current_soundtrack_and_timeline(edition):
    record, named = repository.read(edition.sound_gates), "build/evidence/editions/zh"
    assert preflight.sound(edition) is None
    put(edition.sound_gates, {**record, "verdict": "refuse"})
    assert preflight.sound(edition) == f"{named}/sound-gates.json did not pass; run check-sound"
    put(edition.sound_gates, {**record, "timeline_sha256": "0" * 64, "engine_version": "0.1.0"})
    assert preflight.sound(edition) == (
        f"{named}/sound-gates.json binds another timeline_sha256, engine_version; run check-sound"
    )
    edition.sound_gates.unlink()
    assert preflight.sound(edition) == (
        f"no sound gate record at {named}/sound-gates.json; run check-sound"
    )


def thoughts(edition, **values):
    """Give the sound gate record these thoughts' clarity, against the floor of 18 dB."""
    rows = [
        {"id": name, "cpp_db": value, "below_floor": value < 18} for name, value in values.items()
    ]
    record = repository.read(edition.sound_gates)
    put(edition.sound_gates, {**record, "clarity": {"floor_db": 18.0, "thoughts": rows}})


def test_a_thought_under_the_floor_is_declared_and_none_stands_under_the_thought_line(
    edition, monkeypatch
):
    thoughts(edition, **{"01.1": 18.4, "01.2": 17.62, "02.1": 16.9})
    # A film that declares no line for a single thought is not judged.
    assert preflight.clarity(edition) == preflight.NO_THOUGHT_LINE
    kept = [
        {"edition": "zh", "thought": "01.2", "reason": "thirty-two takes"},
        {"edition": "zh", "thought": "03.1", "reason": "an earlier build"},
        {"edition": "en", "thought": "02.1", "reason": "the other edition's"},
    ]
    review = type(FILM.review)(
        **{
            **FILM.review.model_dump(),
            "clarity_thought_margin_db": 1.0,
            "clarity_exceptions": kept,
        }
    )
    monkeypatch.setattr(preflight, "FILM", FILM.model_copy(update={"review": review}))
    assert preflight.clarity(edition) == (
        "thought 02.1 reads 16.9 dB, under the thought line of 17.0 dB; "
        "the declared thought 03.1 is stale: it does not read under the floor"
    )
    thoughts(edition, **{"01.1": 18.4, "01.2": 17.62, "02.1": 17.0, "03.1": 17.99})
    assert preflight.clarity(edition) == (
        "thought 02.1 reads 17.0 dB, under the floor of 18.0 dB, and is not declared in"
        " review.clarity_exceptions"
    )
    thoughts(edition, **{"01.2": 17.62, "03.1": 17.99})
    assert preflight.clarity(edition) is None
    # A declaration keeps no thought under the thought line.
    thoughts(edition, **{"01.2": 16.4, "03.1": 17.99})
    assert preflight.clarity(edition) == (
        "thought 01.2 reads 16.4 dB, under the thought line of 17.0 dB"
    )


def test_with_a_margin_of_zero_every_thought_is_held_to_the_floor_itself(edition, monkeypatch):
    review = type(FILM.review)(**{**FILM.review.model_dump(), "clarity_thought_margin_db": 0})
    monkeypatch.setattr(preflight, "FILM", FILM.model_copy(update={"review": review}))
    # A thought at the floor passes.
    thoughts(edition, **{"01.1": 18.0, "01.2": 18.4})
    assert preflight.clarity(edition) is None
    # A thought a hundredth of a decibel under it is refused, and no declaration could keep it.
    thoughts(edition, **{"01.1": 18.0, "01.2": 17.99, "02.1": 16.9})
    assert preflight.clarity(edition) == (
        "thought 01.2 reads 17.99 dB, under the floor of 18.0 dB, to which the film holds every "
        "thought; thought 02.1 reads 16.9 dB, under the floor of 18.0 dB, to which the film "
        "holds every thought"
    )


def test_a_cue_above_the_reading_rate_is_declared_by_its_text(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    edition = Edition("en")
    fast = "The people watching the pipeline."
    cues = [
        {"segment": "01", "text": "Read the data first.", "start": 1.0, "end": 3.0},
        {"segment": "01", "text": fast, "start": 3.0, "end": 4.2},
    ]
    put(edition.timeline, {"captions": cues})
    assert preflight.caption_rate(edition) == (
        f"the cue {fast!r} reads at 27.5 characters per second, above 25, and is not declared in"
        " captions.rate_exceptions"
    )
    kept = [
        {"edition": "en", "text": fast, "reason": "a quoted line kept whole"},
        {"edition": "en", "text": "Read the data first.", "reason": "an earlier build"},
    ]
    captions = type(FILM.captions)(rate_exceptions=kept)
    monkeypatch.setattr(preflight, "FILM", FILM.model_copy(update={"captions": captions}))
    assert preflight.caption_rate(edition) == (
        "the declared cue 'Read the data first.' is stale: no cue with that text reads above the"
        " rate"
    )
    captions = type(FILM.captions)(rate_exceptions=kept[:1])
    monkeypatch.setattr(preflight, "FILM", FILM.model_copy(update={"captions": captions}))
    assert preflight.caption_rate(edition) is None
    # A Chinese cue has no reading rate, so none is above it, and a declared one is stale.
    put(Edition("zh").timeline, {"captions": [{**cues[1], "text": "先看数据，再看流水线。"}]})
    assert preflight.caption_rate(Edition("zh")) is None
    kept = [{"edition": "zh", "text": "先看数据，再看流水线。", "reason": "kept whole"}]
    captions = type(FILM.captions)(rate_exceptions=kept)
    monkeypatch.setattr(preflight, "FILM", FILM.model_copy(update={"captions": captions}))
    assert preflight.caption_rate(Edition("zh")) == (
        "the declared cue '先看数据，再看流水线。' is stale: no cue with that text reads above the"
        " rate"
    )


def test_the_geometry_record_must_cover_the_current_staged_film(edition):
    record, named = repository.read(edition.picture_geometry), "build/evidence/editions/zh"
    assert preflight.geometry(edition) is None
    refusal = (
        f"Picture geometry does not cover the current staged film ({named}/picture-geometry.json);"
        " run filmkit.tools geometry-check on the stage"
    )
    for changed in ({"passed": False}, {"index_sha256": "0" * 64}, {"step_frames": 4}):
        put(edition.picture_geometry, {**record, **changed})
        assert preflight.geometry(edition) == refusal
    edition.picture_geometry.unlink()
    assert preflight.geometry(edition) == f"missing {named}/picture-geometry.json"


def ready(code, monkeypatch):
    """Write the edition's passing receipt on the inputs as they stand, its questions stood in."""
    judged = Edition(code)
    for question in ASKED:
        monkeypatch.setattr(preflight, question, lambda *_, **__: None)
    preflight.preflight(judged)
    return judged


def test_the_receipt_binds_what_the_answer_was_judged_on(edition, monkeypatch):
    monkeypatch.setattr(preflight.tools, "run", painted()[0])
    preflight.preflight(edition)
    receipt = repository.read(edition.readiness)
    assert receipt["edition"] == "zh" and receipt["verdict"] == "pass"
    assert receipt["engine_version"] == version("filmkit")
    assert receipt["inputs"]["stage"] == "current"
    root, faces = repository.ROOT, picture_rendering.face_bindings()
    assert receipt["bound"] == {
        "composition": repository.sha(root / picture_rendering.COMPOSITION_SCRIPT),
        "stylesheet": faces["stylesheet_sha256"],
        "fonts": faces["fonts_sha256"],
        "declaration": repository.sha(root / repository.DECLARATION),
        "entry": repository.sha(root / FILM.entry),
        "script": repository.sha(root / edition.script),
        "cast": repository.sha(root / edition.cast),
        "timeline": repository.sha(edition.timeline),
        "assembly": repository.sha(edition.audio_assembly),
        "soundtrack": repository.sha(edition.soundtrack),
    }
    # A missing input refuses by name and leaves the receipt without digests.
    (root / edition.cast).unlink()
    with pytest.raises(preflight.PreflightError, match="receipt: missing content/voice-"):
        preflight.preflight(edition)
    receipt = repository.read(edition.readiness)
    assert receipt["verdict"] == "refuse" and receipt["bound"] is None


def test_an_edition_is_admitted_on_both_receipts_without_repeating_the_checks(
    edition, monkeypatch, capsys
):
    root = repository.ROOT
    english = Edition("en")
    for path, text in (
        (root / english.script, "{}"),
        (root / english.cast, "{}"),
        (english.timeline, "{}"),
        (english.audio_assembly, "{}"),
        (english.soundtrack, "en narration"),
    ):
        put(path, text)
    with pytest.raises(preflight.PreflightError) as refusal:
        preflight.admitted(edition)
    assert str(refusal.value) == (
        "The zh edition is not admitted: no readiness receipt at"
        " build/evidence/editions/zh/readiness.json; run preflight --language zh | no readiness"
        " receipt at build/evidence/editions/en/readiness.json; run preflight --language en"
    )
    ready("zh", monkeypatch)
    ready("en", monkeypatch)
    capsys.readouterr()
    # The check reads the receipts and the inputs' bytes: no question is asked again.
    for question in ASKED:
        monkeypatch.setattr(preflight, question, None)
    assert preflight.admitted(edition) == {"language": "zh", "admitted": True}
    assert json.loads(capsys.readouterr().out) == {"language": "zh", "admitted": True}
    produce.main(["admitted", "--language", "en"])
    # The other edition's own inputs may move: its English retake refuses no Chinese render.
    put(english.timeline, '{"captions": []}')
    assert preflight.admitted(edition)["admitted"] is True
    with pytest.raises(SystemExit) as refusal:
        produce.main(["admitted", "--language", "en"])
    assert str(refusal.value) == (
        "admitted: The en edition is not admitted: build/evidence/editions/en/readiness.json"
        " binds another timeline; run preflight --language en"
    )
    # A change of the composition, which both editions render, refuses both.
    put(root / picture_rendering.COMPOSITION_SCRIPT, "scenes = {};\n")
    with pytest.raises(preflight.PreflightError) as refusal:
        preflight.admitted(edition)
    assert str(refusal.value) == (
        "The zh edition is not admitted: build/evidence/editions/zh/readiness.json binds another"
        " composition; run preflight --language zh | build/evidence/editions/en/readiness.json"
        " binds another composition; run preflight --language en"
    )


def test_a_receipt_that_refused_or_another_engine_wrote_admits_nothing(edition, monkeypatch):
    ready("zh", monkeypatch)
    receipt = repository.read(edition.readiness)
    put(Edition("en").readiness, {**receipt, "edition": "en"})
    assert preflight.admitted(edition)["admitted"] is True
    put(edition.readiness, {**receipt, "engine_version": "0.1.0"})
    with pytest.raises(preflight.PreflightError, match=r"zh/readiness\.json binds another engine_"):
        preflight.admitted(edition)
    put(edition.readiness, {**receipt, "verdict": "refuse"})
    with pytest.raises(preflight.PreflightError, match=r"zh/readiness\.json did not pass; run"):
        preflight.admitted(edition)
    # The other edition's refused receipt refuses this one too.
    put(edition.readiness, receipt)
    put(Edition("en").readiness, {**receipt, "edition": "en", "verdict": "refuse"})
    with pytest.raises(preflight.PreflightError, match=r"en/readiness\.json did not pass; run"):
        preflight.admitted(edition)
