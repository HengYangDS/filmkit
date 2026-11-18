"""The one reader of a stylesheet's faces: what it reads, and what it refuses by name."""

import pytest

import filmkit.picture.faces as faces
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.picture.errors import PictureError

FONTS = ["assets/fonts/a.otf", "assets/fonts/b.ttf"]


def test_the_sample_films_faces_are_read_in_their_order_with_their_fonts():
    read = picture_rendering.declared_faces()
    assert [face["family"] for face in read] == [
        "Sample",
        "SampleBold",
        "SampleLatin",
        "SampleLatinBold",
    ]
    assert read[0] == {
        "family": "Sample",
        "path": "fonts/noto-sans-cjk-sc-subset-regular.otf",
        "font": FILM.picture.fonts[0],
    }
    assert [face["font"] for face in read] == list(FILM.picture.fonts)


@pytest.mark.parametrize(
    "stylesheet",
    [
        "@font-face{font-family:Film;src:url('fonts/a.otf')}body{font-family:Film}"
        "@font-face{font-family:'Film Bold';src:url(fonts/b.ttf) format('truetype')}",
        '@FONT-FACE { FONT-FAMILY: Film; SRC: URL(fonts/a.otf) FORMAT("opentype"); }\n'
        '@font-face { font-family: "Film Bold"; src: /* the bold */ url("fonts/b.ttf");'
        " font-weight: 700; font-style: normal; font-display: block }",
        "/* @font-face { font-family: Left; src: url(fonts/left.otf) } */"
        "@font-face{src:url(fonts/a.otf);font-family:Film}"
        "@font-face{font-family:Film Bold;src:url( fonts/b.ttf )}",
    ],
    ids=["minified", "upper case, comment and descriptors", "commented out and reordered"],
)
def test_a_rule_is_read_however_it_is_written(stylesheet):
    assert faces.rules(stylesheet) == [("Film", "fonts/a.otf"), ("Film Bold", "fonts/b.ttf")]
    assert faces.held(stylesheet, FONTS) == [
        {"family": "Film", "path": "fonts/a.otf", "font": "assets/fonts/a.otf"},
        {"family": "Film Bold", "path": "fonts/b.ttf", "font": "assets/fonts/b.ttf"},
    ]


@pytest.mark.parametrize(
    ("rule", "why"),
    [
        ('font-family:B;src:local("B"),url(fonts/b.ttf)', "does not declare one family and one"),
        ("font-family:B;src:url(fonts/b.ttf),url(fonts/a.otf)", "does not declare one family"),
        ("font-family:B;src:local(B)", "does not declare one family and one source"),
        ("src:url(fonts/b.ttf)", "does not declare one family and one source"),
        ("font-family:B", "does not declare one family and one source"),
        ("font-family:B;src:url(fonts/b.ttf);unicode-range:U+00-7F", "declares unicode-range"),
        ("font-family:B;src:url(fonts/b.ttf);font-stretch:50%", "declares font-stretch"),
        ("font-family:B;src:url(fonts/b.ttf);src:url(fonts/a.otf)", "declares src twice"),
        ("font-family:B;src url(fonts/b.ttf)", "twice or badly"),
    ],
)
def test_a_rule_the_canvas_cannot_be_held_to_is_refused_and_named(rule, why):
    stylesheet = "@font-face{font-family:A;src:url(fonts/a.otf)}@font-face{" + rule + "}"
    with pytest.raises(PictureError) as refused:
        faces.rules(stylesheet)
    assert why in str(refused.value)
    assert "@font-face{" + rule + "}" in str(refused.value) or "twice" in str(refused.value)


def test_two_rules_of_one_family_and_a_rule_that_is_no_block_are_refused():
    first = "@font-face{font-family:A;src:url(fonts/a.otf)}"
    twice = first + "@font-face{font-family:A;src:url(fonts/b.ttf)}"
    with pytest.raises(PictureError, match="Two face rules declare the family A"):
        faces.rules(twice)
    with pytest.raises(PictureError, match="not one block of declarations"):
        faces.rules("@font-face{font-family:A;src:url(fonts/a.otf)")


def test_the_faces_and_the_declared_fonts_must_cover_each_other():
    only = "@font-face{font-family:A;src:url(fonts/a.otf)}"
    with pytest.raises(PictureError, match="No face rule names the declared font fonts/b.ttf"):
        faces.held(only, FONTS)
    with pytest.raises(PictureError, match="The face A names fonts/a.otf, which is none of"):
        faces.held(only, ["assets/fonts/b.ttf"])
    # A source outside fonts/ is no declared font's place in a stage, whatever its file name.
    with pytest.raises(PictureError, match="The face A names a.otf"):
        faces.held("@font-face{font-family:A;src:url(a.otf)}", ["assets/fonts/a.otf"])


def test_a_stage_records_its_faces_and_its_language_and_a_changed_stylesheet_is_refused(
    film_root,
):
    from filmkit.production import Edition
    from filmkit.specification import DURATION

    for code, language in (("zh", "zh-CN"), ("en", "en")):
        edition = Edition(code)
        film_root.staged(edition)
        record = repository.read(edition.picture_stage / "stage.json")
        assert record["language"] == language
        assert f'<html lang="{language}">' in (edition.picture_stage / "index.html").read_text()
        assert record["faces"] == [
            {"family": face["family"], "path": face["path"]}
            for face in picture_rendering.declared_faces()
        ]
    # A stage staged before a face was renamed no longer names the faces the sources declare.
    style = film_root.path / picture_rendering.STYLE
    style.write_text(style.read_text().replace("font-family: SampleBold;", "font-family: Bolder;"))
    with pytest.raises(PictureError, match="faces differ"):
        picture_rendering.require_current_stage(Edition("zh"), Edition("zh").picture_stage)
    # A stylesheet with a rule the reader refuses stages nothing.
    style.write_text(style.read_text() + "@font-face{font-family:X;src:local(X)}")
    with pytest.raises(PictureError, match="does not declare one family and one source"):
        picture_rendering.stage_picture(Edition("zh"), None, DURATION, 3840, 2160)
