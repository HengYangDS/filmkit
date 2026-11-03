"""The advance widths of the faces a film's stylesheet declares, by which the headless audits
measure text."""

import shutil
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

import filmkit.picture.metrics as metrics
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.rendering import STYLE

# The sample film, whose stylesheet and fonts the test film copies.
SAMPLE = Path(__file__).resolve().parents[2] / "examples/sample-film"


@pytest.fixture
def film(tmp_path, monkeypatch):
    """A film root with the sample film's stylesheet and declared fonts."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    for path in (STYLE, *FILM.picture.fonts):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE / path, root / path)
    return root


def advance_sum(font: Path, text: str) -> float:
    """The sum of the text's advances in a font, in em, read directly from its tables."""
    with TTFont(font, lazy=True) as face:
        cmap, hmtx, em = face.getBestCmap(), face["hmtx"], face["head"].unitsPerEm
        return sum(hmtx[cmap[ord(char)]][0] for char in text) / em


def width(face: dict, text: str) -> float:
    """A text's width in em by the table's face, as the stand-in canvas measures it."""
    return sum(face["advances"].get(char, face["default"]) for char in text)


def test_the_table_holds_each_declared_face_by_its_font(film):
    table = metrics.text_metrics()
    fonts = dict(
        zip(
            ["Sample", "SampleBold", "SampleLatin", "SampleLatinBold"],
            FILM.picture.fonts,
            strict=True,
        )
    )
    assert {family: face["font"] for family, face in table["faces"].items()} == fonts
    assert table["stylesheet_sha256"] == repository.sha(film / STYLE)
    assert table["fonts_sha256"] == {
        font: repository.sha(film / font) for font in FILM.picture.fonts
    }
    # A face lists only the advances other than its default, every one a mapped character.
    for face in table["faces"].values():
        assert face["units_per_em"] > 0
        assert face["default"] not in face["advances"].values()
        assert set(face["advances"]) <= set(face["mapped"])
    # Widths by the table equal the fonts' own advance sums, for a Latin phrase and for Chinese
    # text of the subset's own characters.
    chinese = table["faces"]["Sample"]["mapped"][-8:]
    for family, text in (("SampleLatin", "Data and its owner"), ("Sample", chinese)):
        face = table["faces"][family]
        assert width(face, text) == pytest.approx(advance_sum(film / face["font"], text))


def test_a_face_whose_source_is_not_a_declared_font_keeps_the_estimate(film):
    style = film / STYLE
    style.write_text(
        style.read_text(encoding="utf-8")
        + '\n@font-face { font-family: "Other"; src: url("fonts/other.ttf"); }\n',
        encoding="utf-8",
    )
    assert "Other" not in metrics.declared_faces()
    assert len(metrics.declared_faces()) == 4


def test_the_table_is_written_once_and_again_when_a_font_changes(film):
    path = metrics.current_table()
    assert path == film / metrics.TABLE
    written = path.stat().st_mtime_ns
    assert metrics.current_table().stat().st_mtime_ns == written
    # Another font under a declared name makes the table stale, and it is read again.
    latin = film / FILM.picture.fonts[2]
    shutil.copyfile(SAMPLE / FILM.picture.fonts[3], latin)
    table = repository.read(metrics.current_table())
    assert table["fonts_sha256"][FILM.picture.fonts[2]] == repository.sha(latin)
    bold = repository.read(path)["faces"]["SampleLatinBold"]
    assert table["faces"]["SampleLatin"]["advances"] == bold["advances"]
