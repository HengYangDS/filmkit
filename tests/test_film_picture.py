"""The declaration's `[picture]` table: the wrapping, motion and detail exceptions, the capture,
the drafts, the geometry's row gaps and the editions whose uncaptioned picture is rendered
natively, each with its refusals."""

import re

import pytest
from declaring import rewrite

import filmkit.film as film
from filmkit.film import FilmError

# A wrapping declaration with its own shares, a lead word and one exception.
WRAPPING = """[picture.wrapping]
line_share = 0.75
last_share = 0.5
lead_words = { en = ["versus"] }
exceptions = [
  { edition = "en", lines = ["Stated", "assumptions"], reason = "a term set as one name" },
]

"""


def test_wrapping_rules_default_and_are_declared_with_their_exceptions(declared):
    assert film.FILM.picture.wrapping == film.Wrapping(line_share=0.8, last_share=0.6)
    rewrite(declared, "[review]\n", WRAPPING + "[review]\n")
    wrapping = film.load(declared).picture.wrapping
    assert (wrapping.line_share, wrapping.last_share) == (0.75, 0.5)
    assert wrapping.lead_words == {"en": ("versus",)}
    lines, reason = ("Stated", "assumptions"), "a term set as one name"
    kept = film.WrappingException(edition="en", lines=lines, reason=reason)
    assert wrapping.exceptions == (kept,)


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("line_share = 0.75", "line_share = 0", "picture.wrapping.line_share"),
        ("last_share = 0.5", "last_share = 1.2", "picture.wrapping.last_share"),
        (', reason = "a term set as one name"', "", "picture.wrapping.exceptions.0.reason"),
        ('"a term set as one name"', '" "', "picture.wrapping.exceptions.0.reason"),
        ('edition = "en", ', "", "picture.wrapping.exceptions.0.edition"),
        ('["Stated", "assumptions"]', '["Stated assumptions"]', "wrapping.exceptions.0.lines"),
        ('["versus"]', '["two words"]', "picture.wrapping.lead_words.en.0"),
    ],
)
def test_a_wrapping_declaration_refuses_naming_its_field(declared, old, new, field):
    # A share outside (0, 1], an exception without a reason, its edition or two lines, and a
    # lead word of two words.
    rewrite(declared, "[review]\n", WRAPPING + "[review]\n")
    rewrite(declared, old, new)
    with pytest.raises(FilmError, match=re.escape(field)):
        film.load(declared)


def test_two_exceptions_of_one_label_refuse(declared):
    rewrite(declared, "[review]\n", WRAPPING + "[review]\n")
    exception = '  { edition = "en", lines = ["Stated", "assumptions"], reason = "a term" },\n'
    rewrite(declared, "]\n\n[review]", f"{exception}]\n\n[review]")
    with pytest.raises(FilmError, match="two exceptions name the same lines of one edition"):
        film.load(declared)


# A motion declaration that keeps one pop of one edition by its module.
MOTION = """[[picture.motion.exceptions]]
edition = "zh"
scene = "06"
source = "picture/film/scenes/p06/beats.js"
kind = "pop"
reason = "the beat ring marks each condition on its word"

"""


def test_motion_exceptions_default_and_are_declared(declared):
    assert film.FILM.picture.motion == film.Motion()
    rewrite(declared, "[review]\n", MOTION + "[review]\n")
    kept = film.load(declared).picture.motion.exceptions
    assert kept == (
        film.MotionException(
            edition="zh",
            scene="06",
            source="picture/film/scenes/p06/beats.js",
            kind="pop",
            reason="the beat ring marks each condition on its word",
        ),
    )


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ('kind = "pop"', 'kind = "drift"', "picture.motion.exceptions.0.kind"),
        ('source = "picture/film/scenes/p06/beats.js"', 'source = "line 5"', "0.source"),
        ('source = "picture/film/scenes/p06/beats.js"', 'source = "film.js:0"', "0.source"),
        ('reason = "the beat ring marks each condition on its word"', 'reason = " "', "0.reason"),
        ('edition = "zh"\n', "", "picture.motion.exceptions.0.edition"),
    ],
)
def test_a_motion_declaration_refuses_naming_its_field(declared, old, new, field):
    # An unknown kind, a source that is neither a line of film.js nor a module, and an exception
    # without a reason or its edition.
    rewrite(declared, "[review]\n", MOTION + "[review]\n")
    rewrite(declared, old, new)
    with pytest.raises(FilmError, match=re.escape(field)):
        film.load(declared)


def test_two_exceptions_of_one_motion_finding_refuse(declared):
    rewrite(declared, "[review]\n", MOTION + MOTION + "[review]\n")
    with pytest.raises(FilmError, match="two exceptions name the same motion of one edition"):
        film.load(declared)


# The sample film's own capture, as its declaration writes it.
SAMPLE_CAPTURE = 'capture = "software"\n'


def test_a_film_without_a_capture_captures_fast(declared):
    rewrite(declared, SAMPLE_CAPTURE, "")
    assert film.load(declared).picture.capture == "fast"


def test_the_sample_film_declares_the_capture_under_which_pictures_are_derived(declared):
    assert film.FILM.picture.capture == "software"
    assert film.load(declared).picture.capture == "software"


@pytest.mark.parametrize("capture", ["fast", "screenshot", "software"])
def test_a_film_may_declare_its_capture(declared, capture):
    rewrite(declared, SAMPLE_CAPTURE, f'capture = "{capture}"\n')
    assert film.load(declared).picture.capture == capture


def test_another_capture_is_refused_naming_its_field(declared):
    rewrite(declared, SAMPLE_CAPTURE, 'capture = "drawelement"\n')
    named = r"picture\.capture\s+Input should be 'fast', 'screenshot' or 'software'"
    with pytest.raises(FilmError, match=named):
        film.load(declared)


# A detail declaration that keeps one rail of one edition at its narrow row.
DETAIL = """[[picture.detail.exceptions]]
edition = "zh"
kind = "rail"
scene = "13"
source = "duties"
reason = "a lower second row would unseat the names from their marks"

"""


def test_detail_exceptions_default_and_are_declared(declared):
    assert film.FILM.picture.detail == film.Detail()
    rewrite(declared, "[review]\n", DETAIL + "[review]\n")
    kept = film.load(declared).picture.detail.exceptions
    assert kept == (
        film.DetailException(
            edition="zh",
            kind="rail",
            scene="13",
            source="duties",
            reason="a lower second row would unseat the names from their marks",
        ),
    )


@pytest.mark.parametrize(
    ("old", "new", "refusal"),
    [
        ('kind = "rail"', 'kind = "gap"', "picture.detail.exceptions.0.kind"),
        ('kind = "rail"', 'kind = "racing_tip"', "a racing_tip exception cannot name the source"),
        ('kind = "rail"', 'kind = "off_centre_far"', "cannot name the source 'duties'"),
        ('reason = "a lower second row would unseat the names from their marks"', "", "0.reason"),
        ("[review]\n", DETAIL + "[review]\n", "two exceptions name the same detail finding"),
    ],
)
def test_a_detail_declaration_refuses_naming_its_fault(declared, old, new, refusal):
    rewrite(declared, "[review]\n", DETAIL + "[review]\n")
    rewrite(declared, old, new)
    with pytest.raises(FilmError, match=re.escape(refusal)):
        film.load(declared)


def test_a_film_makes_drafts_only_when_it_declares_them(declared):
    # The sample film declares its drafts.
    assert film.load(declared).picture.drafts is True
    rewrite(declared, "drafts = true\n", "")
    assert film.load(declared).picture.drafts is False


def test_the_geometry_s_row_gaps_and_the_native_uncaptioned_editions_are_declared(declared):
    loaded = film.load(declared).picture
    assert (loaded.gate_row_gaps, loaded.native_uncaptioned) == (False, ())
    rewrite(
        declared,
        "drafts = true\n",
        'drafts = true\ngate_row_gaps = true\nnative_uncaptioned = ["zh"]\n',
    )
    loaded = film.load(declared).picture
    assert (loaded.gate_row_gaps, loaded.native_uncaptioned) == (True, ("zh",))


def test_a_native_uncaptioned_edition_the_film_does_not_declare_is_refused(declared):
    rewrite(declared, "drafts = true\n", 'drafts = true\nnative_uncaptioned = ["fr"]\n')
    with pytest.raises(film.FilmError, match="picture.native_uncaptioned"):
        film.load(declared)
