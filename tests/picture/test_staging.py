"""Stage an edition's picture with fixture inputs and the real composition: the document, its
fonts, its bound inputs and the refusals of a stage."""

import json
import re
from pathlib import Path

import pytest
import staged_inputs
from assembled import stage
from staged_inputs import COMPOSITION, RUNTIME, put

import filmkit.captions.refresh as refresh
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import PictureError
from filmkit.production import STAGE_RECORD, Edition, UnassembledError

# The film root of both editions' inputs, for every test here, and the staged Chinese edition.
root = pytest.fixture(autouse=True)(staged_inputs.root)
staged = pytest.fixture(staged_inputs.staged)


# The template patterns that the renderer document replaces.
PLACEHOLDERS = (
    "/* FILM_DATA */",
    '<link rel="stylesheet" href="film.css">',
    '<script src="film.js"></script>',
    'data-duration="1200"',
    'data-width="1920"',
    'data-height="1080"',
    'content="width=1920, height=1080"',
    'width="1920" height="1080"',
)


@pytest.mark.parametrize("code", ["zh", "en"])
def test_staging_twice_writes_the_same_complete_document(code):
    edition = Edition(code)
    stage = edition.picture_stage
    written = []
    for _ in range(2):
        picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
        written.append(((stage / "index.html").read_bytes(), (stage / "stage.json").read_bytes()))
    assert written[0] == written[1]
    document = written[0][0].decode()
    template = (COMPOSITION / "index.html").read_text()
    for placeholder in PLACEHOLDERS:
        assert placeholder in template
        assert placeholder not in document
    assert f'<html lang="{"en" if code == "en" else "zh-CN"}">' in document
    assert 'data-duration="1477"' in document
    assert '<div style="width:3840px;height:2160px" id="film"' in document
    assert "<script>" + (COMPOSITION / "film.js").read_text() + "</script>" in document
    assert "<style>" + (COMPOSITION / "film.css").read_text() + "</style>" in document
    film = json.loads(document.split("window.FILM=", 1)[1].split(";</script>", 1)[0])
    assert (film["edition"], film["render_offset"]) == (code, 0)
    binding = json.loads(written[0][1])
    inputs, timeline = picture_rendering.candidate_picture_inputs(edition)
    assert binding["inputs"] == inputs
    # The edition is the one the assembly wrote into the timeline, which staging copies.
    assert timeline["edition"] == code
    assert film == {**timeline, "render_offset": 0}
    assert [(member["path"], member["source"]) for member in binding["members"]] == [
        (path, str(source)) for path, source in picture_rendering.staged_members()
    ]
    for member in binding["members"]:
        assert repository.sha(stage / member["path"]) == member["sha256"]


def test_a_stage_holds_exactly_the_declared_fonts_in_order(staged):
    stage = staged.picture_stage
    declared = [Path(font) for font in FILM.picture.fonts]
    binding = json.loads((stage / "stage.json").read_text())
    fonts = [(member["path"], member["source"]) for member in binding["members"][2:]]
    assert fonts == [(f"fonts/{font.name}", str(font)) for font in declared]
    assert sorted(path.name for path in (stage / "fonts").iterdir()) == sorted(
        font.name for font in declared
    )


def test_staging_reads_each_bound_input_once(root, monkeypatch):
    # The stage inlines the very timeline whose bytes it binds.
    edition = Edition("zh")
    opened = []
    path_open = Path.open

    def counted(self, *args, **kwargs):
        opened.append(self)
        return path_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counted)
    picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
    for path in (root / edition.script, edition.timeline, edition.audio_assembly):
        assert opened.count(path) == 1


def test_candidate_inputs_refuse_a_timeline_or_soundtrack_of_other_sources():
    edition = Edition("zh")
    timeline = json.loads(edition.timeline.read_text())
    segment = {**timeline["segments"][0], "text": "另一句。"}
    put(edition.timeline, {**timeline, "segments": [segment]})
    with pytest.raises(PictureError, match="timeline differs from its authored script"):
        picture_rendering.candidate_picture_inputs(edition)
    put(edition.timeline, timeline)
    put(edition.soundtrack, "another narration")
    with pytest.raises(PictureError, match="soundtrack differs from its native assembly"):
        picture_rendering.candidate_picture_inputs(edition)


def test_an_edition_refreshed_after_an_anchor_is_added_stages_as_following_its_script(
    tmp_path, monkeypatch
):
    words = (("甲", 2.0, 2.4), ("乙", 2.4, 2.8), ("丙", 3.4, 3.8), ("丁", 3.8, 4.2))
    edition = stage(tmp_path, monkeypatch, "zh", ["甲乙。", "丙丁。"], words)
    script = repository.read(edition.script)
    script["segments"][0]["anchored_groups"] = ["甲乙。", "{last}丙丁{/last}。"]
    put(repository.ROOT / edition.script, script)
    refresh.refresh_captions(edition)
    picture_rendering.stage_picture(edition, None, 9, 3840, 2160)
    staged = repository.read(edition.rendered(True).stage / picture_rendering.DATA)
    # The stage's data holds the anchor with the times of its words, 丙 to 丁.
    assert [staged["segments"][0]["anchors"]["last"][key] for key in ("start", "end")] == [3.4, 4.2]


def test_staging_refuses_other_frames_durations_and_places(root):
    edition = Edition("zh")
    for duration, size, start in ((RUNTIME + 1, (3840, 2160), 0), (RUNTIME, (1280, 720), 0)):
        with pytest.raises(PictureError, match="admitted frame and duration"):
            picture_rendering.stage_picture(edition, None, duration, *size, start)
    with pytest.raises(PictureError, match="build owner"):
        picture_rendering.stage_picture(edition, root / "elsewhere", RUNTIME, 3840, 2160)
    assert not edition.picture_stage.exists()


def test_the_document_refuses_a_template_pattern_it_does_not_find_exactly(root):
    edition = Edition("zh")
    template = root / picture_rendering.COMPOSITION / "index.html"
    text = template.read_text()
    for changed, pattern in (
        (text.replace('data-width="1920"', 'data-width="1600"'), 'data-width="1920"'),
        (text.replace("</body>", '<div id="film"></div></body>'), '<div id="film"'),
        (text.replace(' data-duration="1200"', ""), 'data-duration="1200"'),
    ):
        template.write_text(changed)
        with pytest.raises(PictureError, match=re.escape(repr(pattern))):
            picture_rendering.picture_html(edition, RUNTIME, 3840, 2160, 0)


def test_a_stage_spans_the_runtime_its_edition_s_timeline_states(staged):
    edition = staged
    record = json.loads((edition.picture_stage / STAGE_RECORD).read_text())
    assert (record["duration"], record["start"]) == (1477, 0)
    assert picture_rendering.require_current_stage(edition, edition.picture_stage) == record
    # A stage of the sample's 60 s is no stage of this edition's whole runtime.
    picture_rendering.stage_picture(edition, None, 60, 3840, 2160)
    with pytest.raises(PictureError, match="duration differ"):
        picture_rendering.require_current_stage(edition, edition.picture_stage)


def test_an_edition_without_a_timeline_is_refused_before_a_stage_is_written():
    edition = Edition("en")
    edition.timeline.unlink()
    with pytest.raises(UnassembledError) as refused:
        picture_rendering.stage_picture(edition, None, RUNTIME, 3840, 2160)
    assert str(refused.value) == (
        "The en edition has no timeline at build/artifacts/film/en/timeline.json, so no runtime: "
        "run produce assemble --language en"
    )
    assert not edition.picture_stage.exists()
