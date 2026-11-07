"""The uncaptioned picture: staged from the same composition and timeline with no captions, rendered
with the same settings to its own file and receipt, and bound by records that name it."""

import json
import shutil
import sys
import textwrap
from importlib.metadata import version

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition
from filmkit.specification import DURATION

# The real composition, found before a test rebinds the repository root.
COMPOSITION = repository.ROOT / picture_rendering.COMPOSITION
CUES = [{"start": 1.0, "end": 2.0, "text": "先看数据。", "segment": "01"}]


def put(path, data):
    """Write text or JSON to a fixture file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
    return path


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """The Chinese edition's current inputs with one caption, its picture checked, below a root
    with the real composition and a stand-in renderer that writes the picture it is given."""
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
    put(edition.timeline, {**script, "segments": [segment], "captions": CUES})
    put(edition.soundtrack, "zh narration")
    assembly = {
        "script_sha256": repository.sha(edition.script),
        "soundtrack_sha256": repository.sha(edition.soundtrack),
    }
    put(edition.audio_assembly, assembly)
    composition = repository.sha(root / picture_rendering.COMPOSITION_SCRIPT)
    gates = {"composition_sha256": composition, "timeline_sha256": repository.sha(edition.timeline)}
    gates |= {"engine_version": version("filmkit"), **picture_rendering.face_bindings()}
    put(edition.picture_gates, {**gates, "verdict": "pass"})
    fake = tmp_path / "hyperframes"
    body = """
        import sys
        with open(sys.argv[sys.argv.index("--output") + 1], "w") as picture:
            picture.write("rendered " + sys.argv[2])
        """
    fake.write_text(f"#!{sys.executable}\n{textwrap.dedent(body)}")
    fake.chmod(0o755)
    monkeypatch.setattr(picture_rendering, "RENDERER", fake)
    return edition


def staged_film(stage):
    """The timeline a staged document inlines."""
    document = (stage / "index.html").read_text()
    return json.loads(document.split("window.FILM=", 1)[1].split(";</script>", 1)[0])


def test_the_uncaptioned_stage_inlines_the_timeline_without_its_captions(edition):
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160)
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160, captions=False)
    captioned, uncaptioned = edition.rendered(True), edition.rendered(False)
    assert uncaptioned.stage.name == "final-delivery-zh-uhd-uncaptioned"
    assert staged_film(captioned.stage)["captions"] == CUES
    assert staged_film(uncaptioned.stage) == {**staged_film(captioned.stage), "captions": []}
    # Apart from the timeline it inlines, the uncaptioned document is the captioned one.
    for stage in (captioned.stage, uncaptioned.stage):
        assert (stage / "index.html").read_text().count("window.FILM=") == 1
    records = [json.loads((r.stage / "stage.json").read_text()) for r in (captioned, uncaptioned)]
    assert [record["picture"] for record in records] == ["captioned", "uncaptioned"]
    assert {key: v for key, v in records[0].items() if key != "picture"} == {
        key: v for key, v in records[1].items() if key != "picture"
    }
    picture_rendering.require_current_stage(edition, uncaptioned.stage, captions=False)
    # A stage holds one picture: the captioned stage is no uncaptioned one, nor the reverse.
    with pytest.raises(PictureError, match="picture differ"):
        picture_rendering.require_current_stage(edition, captioned.stage, captions=False)
    with pytest.raises(PictureError, match="picture differ"):
        picture_rendering.require_current_stage(edition, uncaptioned.stage)


def test_a_stage_record_that_names_no_picture_is_the_captioned_one(edition):
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160)
    record = edition.picture_stage / "stage.json"
    earlier = {key: value for key, value in json.loads(record.read_text()).items()}
    del earlier["picture"]
    put(record, earlier)
    picture_rendering.require_current_stage(edition, edition.picture_stage)
    shutil.copytree(edition.picture_stage, edition.rendered(False).stage)
    with pytest.raises(PictureError, match="picture differ"):
        picture_rendering.require_current_stage(
            edition, edition.rendered(False).stage, captions=False
        )


def test_the_uncaptioned_picture_renders_to_its_own_file_and_receipt(edition):
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160, captions=False)
    picture_rendering.render_picture(edition, 60, captions=False)
    rendered = edition.rendered(False)
    receipt = repository.read(rendered.receipt)
    assert rendered.receipt.name == "receipt-uncaptioned.json"
    assert rendered.file.name == "sample-reel-final-picture-uncaptioned.mp4"
    assert receipt["picture"] == "uncaptioned"
    assert receipt["command"][2:5] == [str(rendered.stage), "--output", str(rendered.file)]
    assert rendered.file.read_text() == f"rendered {rendered.stage}"
    assert not edition.picture.exists() and not edition.render_receipt.exists()
    picture_rendering.validate_picture_binding(edition, receipt, captions=False)
    # A receipt is read only for the picture it holds.
    with pytest.raises(PictureError, match="holds the uncaptioned picture, not the captioned"):
        picture_rendering.validate_picture_binding(edition, receipt)
    for named in ({"picture": "captioned"}, {"picture": None}):
        earlier = {**receipt, **named}
        if named["picture"] is None:
            del earlier["picture"]
        with pytest.raises(PictureError, match="holds the captioned picture, not the uncaptioned"):
            picture_rendering.validate_picture_binding(edition, earlier, captions=False)


def test_the_uncaptioned_render_waits_for_its_own_current_stage(edition):
    picture_rendering.stage_picture(edition, None, DURATION, 3840, 2160)
    with pytest.raises(PictureError, match="No staged picture document and record in .*-uncap"):
        picture_rendering.render_picture(edition, 60, captions=False)
    assert not edition.rendered(False).receipt.exists()
