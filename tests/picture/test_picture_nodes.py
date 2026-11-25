"""The picture's two checks as nodes (design decision 7 of build-a-film-by-its-verbs): the
geometry check refuses a record that does not cover the whole current staged film, and the cover
check a tracked cover other than the one the composition paints, each naming what to do."""

import pytest

import filmkit.repository as repository
import filmkit.tools as tools
from filmkit.graph import chain
from filmkit.picture.rendering import PICTURE_SIZE
from filmkit.production import Edition
from filmkit.specification import FPS

RUNTIME = 9


@pytest.fixture
def edition(tmp_path, monkeypatch):
    """The Chinese edition below a root of its own: a staged page and a runtime of 9 s."""
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    monkeypatch.setattr(Edition, "runtime", property(lambda edition: RUNTIME))
    edition = Edition("zh")
    page = edition.rendered().page
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("<html>the staged picture</html>")
    return edition


def geometry(edition, **changed) -> dict:
    """A geometry record that passed on the whole staged film at step 2, with changes."""
    width, height = PICTURE_SIZE
    return {
        "format": "picture-geometry",
        "passed": True,
        "findings": [],
        "errors": [],
        "index_sha256": repository.sha(edition.rendered().page),
        "width": width,
        "height": height,
        "duration": RUNTIME,
        "fps": FPS,
        "step_frames": 2,
        "checked": -(-RUNTIME * FPS // 2),
        **changed,
    }


def tool_writing(record: dict):
    """A geometry tool that writes this record and passes."""

    def run(tool, arguments, stdout=None):
        repository.write(repository.ROOT / arguments[1], record)
        return 0

    return run


def test_the_geometry_check_passes_on_a_record_of_the_whole_current_stage(edition, monkeypatch):
    monkeypatch.setattr(tools, "run", tool_writing(geometry(edition)))
    chain.geometry_check(edition)


@pytest.mark.parametrize(
    ("changed", "lacks"),
    [
        ({"checked": 100}, "it checked 100 frames of the 270 its step must"),
        ({"duration": 5}, "it checked 5 s at 60 fps, not the runtime of 9 s at 60 fps"),
        ({"index_sha256": "0" * 64}, "it checked another staged page"),
        ({"passed": False, "errors": ["a row"]}, "it did not pass; it holds findings or errors"),
    ],
    ids=["part of the frames", "another runtime", "another stage", "failed"],
)
def test_the_geometry_check_refuses_a_record_short_of_the_whole_stage(
    edition, monkeypatch, changed, lacks
):
    monkeypatch.setattr(tools, "run", tool_writing(geometry(edition, **changed)))
    with pytest.raises(tools.ToolError) as refused:
        chain.geometry_check(edition)
    assert str(refused.value) == (
        "build/evidence/editions/zh/picture-geometry.json does not cover the current staged "
        f"film: {lacks}; stage the whole picture and check it again, filmkit build "
        "stage-picture:zh geometry-check:zh"
    )


def cover_tool(report: dict | None, status: int = 0):
    """A cover check that writes this report to its standard output and exits with `status`."""

    def run(tool, arguments, stdout=None):
        if report is not None:
            repository.write(stdout, report)
        return status

    return run


def test_the_cover_check_passes_on_the_painting_tracked(edition, monkeypatch):
    monkeypatch.setattr(tools, "run", cover_tool({"identical": True, "cover_sha256": "0" * 64}))
    chain.cover_check(edition)


@pytest.mark.parametrize(
    ("report", "status", "said"),
    [
        (
            {"identical": False, "cover_sha256": "0" * 64, "differing_pixels": 12},
            1,
            "{cover} differs in 12 pixels from the cover the composition paints; track the "
            "painting build/runtime/work/cover-zh.png",
        ),
        (
            {"identical": False, "cover_sha256": None},
            1,
            "no tracked cover at {cover}; track the painting build/runtime/work/cover-zh.png",
        ),
        (
            {"identical": False, "cover_sha256": "0" * 64, "differing_pixels": None},
            1,
            "{cover} is not the size of the painting build/runtime/work/cover-zh.png",
        ),
        (None, 2, "the cover check exited with status 2 and no report"),
    ],
    ids=["another cover", "no cover", "another size", "no report"],
)
def test_the_cover_check_refuses_a_tracked_cover_other_than_its_painting(
    edition, monkeypatch, report, status, said
):
    monkeypatch.setattr(tools, "run", cover_tool(report, status))
    with pytest.raises(tools.ToolError) as refused:
        chain.cover_check(edition)
    assert str(refused.value) == said.format(cover=edition.cover)
