"""The film declaration, its refusals, and the engine boundary it draws."""

import re
import shutil
from pathlib import Path

import pytest

import filmkit.film as film
import filmkit.repository as repository
from filmkit.film import FilmError
from filmkit.production import CODES, Edition

# Han characters and CJK or full-width punctuation.
CHINESE = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")


@pytest.fixture
def declared(tmp_path):
    """A copy of this film's declaration and every file it names, below a new root."""
    for _field, path in film.named_files(film.FILM):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository.ROOT / path, target)
    shutil.copy2(repository.ROOT / film.DECLARATION, tmp_path / film.DECLARATION)
    return tmp_path


def rewrite(root: Path, old: str, new: str) -> None:
    """Replace one text of the declaration at a root."""
    path = root / film.DECLARATION
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))


def test_a_complete_declaration_loads(declared):
    assert film.load(declared) == film.FILM
    assert tuple(film.FILM.editions) == CODES


def test_a_missing_script_refuses_naming_its_edition(declared):
    (declared / Edition("en").script).unlink()
    with pytest.raises(FilmError, match=r"editions\.en\.sources: content/en/film-script\.json"):
        film.load(declared)


def test_a_missing_font_or_readings_file_refuses_naming_its_field(declared):
    (declared / film.FILM.picture.fonts[-1]).unlink()
    (declared / film.FILM.review.readings).unlink()
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert f"picture.fonts: {film.FILM.picture.fonts[-1]}" in str(refusal.value)
    assert f"review.readings: {film.FILM.review.readings}" in str(refusal.value)


def test_a_missing_concept_contract_refuses_naming_its_field(declared):
    (declared / film.FILM.concepts).unlink()
    with pytest.raises(FilmError, match=r"concepts: content/concepts\.toml"):
        film.load(declared)


def test_a_declaration_names_covers_before_they_are_painted(declared):
    for code in CODES:
        cover = declared / film.FILM.editions[code].cover
        cover.unlink(missing_ok=True)
        assert not cover.exists()
    assert film.load(declared) == film.FILM


def test_fonts_that_share_a_file_name_refuse(declared):
    font = Path(film.FILM.picture.fonts[-1])
    shutil.copy2(declared / font, declared / font.name)
    rewrite(declared, f'"{font}",', f'"{font}",\n  "{font.name}",')
    with pytest.raises(FilmError, match=r"(?s)picture\.fonts.*stage two fonts as one file"):
        film.load(declared)


def test_invalid_fields_refuse_naming_each_field(declared):
    rewrite(declared, f'slug = "{film.FILM.slug}"', 'slug = "Two Words"')
    rewrite(declared, "overall_minimum = 95", "overall_minimum = 195")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert "slug" in str(refusal.value)
    assert "review.overall_minimum" in str(refusal.value)


def test_an_unknown_field_refuses(declared):
    rewrite(declared, "[review]", 'title = "Another"\n\n[review]')
    with pytest.raises(FilmError, match="title"):
        film.load(declared)


def test_clarity_floors_name_both_editions_in_decibels(declared):
    assert film.FILM.review.clarity_minimum_db == {"zh": 18.0, "en": 17.0}
    floors = "clarity_minimum_db = { zh = 18.0, en = 17.0 }"
    for wrong in ("{ zh = 18.0 }", "{ zh = 18.0, fr = 17.0 }", "{ zh = 0, en = 17.0 }"):
        rewrite(declared, floors, f"clarity_minimum_db = {wrong}")
        with pytest.raises(FilmError, match=r"review\.clarity_minimum_db"):
            film.load(declared)
        floors = f"clarity_minimum_db = {wrong}"
    rewrite(declared, floors + "\n", "")
    assert film.load(declared).review.clarity_minimum_db is None


def test_both_editions_are_declared(declared):
    rewrite(declared, "[editions.en]", "[editions.fr]")
    with pytest.raises(FilmError, match="editions"):
        film.load(declared)


# A wrapping declaration with its own shares, a lead word and one exception.
WRAPPING = """[picture.wrapping]
line_share = 0.75
last_share = 0.5
lead_words = ["versus"]
exceptions = [
  { edition = "en", lines = ["Stated", "assumptions"], reason = "a term set as one name" },
]

"""


def test_wrapping_rules_default_and_are_declared_with_their_exceptions(declared):
    assert film.FILM.picture.wrapping == film.Wrapping(line_share=0.8, last_share=0.6)
    rewrite(declared, "[review]\n", WRAPPING + "[review]\n")
    wrapping = film.load(declared).picture.wrapping
    assert (wrapping.line_share, wrapping.last_share) == (0.75, 0.5)
    assert wrapping.lead_words == ("versus",)
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
        ('["versus"]', '["two words"]', "picture.wrapping.lead_words.0"),
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


def test_a_film_without_a_capture_captures_fast(declared):
    assert film.FILM.picture.capture == "fast"
    assert film.load(declared).picture.capture == "fast"


def test_a_film_may_declare_screenshot_capture(declared):
    rewrite(declared, "[picture]\n", '[picture]\ncapture = "screenshot"\n')
    assert film.load(declared).picture.capture == "screenshot"


def test_another_capture_is_refused_naming_its_field(declared):
    rewrite(declared, "[picture]\n", '[picture]\ncapture = "drawelement"\n')
    named = r"picture\.capture\s+Input should be 'fast' or 'screenshot'"
    with pytest.raises(FilmError, match=named):
        film.load(declared)


# Review levels that hold the sample film's five dimensions.
LEVELS = """[review.levels."信"]
asks = "true to the source, to the other edition and to the words"
dimensions = ["subject_and_faithfulness", "concept_fidelity"]

[review.levels."达"]
asks = "understood on first hearing and first sight"
dimensions = ["narration_and_language", "picture_and_sync"]

[review.levels."雅"]
asks = "natural, restrained and finished"
dimensions = ["deliverable_craft"]

"""


def leveled(root: Path, levels: str = LEVELS) -> None:
    """Declare review levels below the review's dimensions, replacing any the film declares."""
    path = root / film.DECLARATION
    text = path.read_text()
    text = text.split("[review.levels.", 1)[0].rstrip() + "\n"
    path.write_text(text + "\n" + levels)


def test_review_levels_hold_each_declared_dimension_once(declared):
    leveled(declared)
    levels = film.load(declared).review.levels
    assert list(levels) == ["信", "达", "雅"]
    assert levels["达"] == film.Level(
        asks="understood on first hearing and first sight",
        dimensions=("narration_and_language", "picture_and_sync"),
    )


@pytest.mark.parametrize(
    ("old", "new", "named"),
    [
        (', "concept_fidelity"]', "]", "concept_fidelity stands in no level"),
        ('["deliverable_craft"]', '["deliverable_craft", "concept_fidelity"]', "in two levels"),
        ('["deliverable_craft"]', '["deliverable_craft", "taste"]', "taste is no declared"),
    ],
)
def test_review_levels_refuse_a_dimension_missed_repeated_or_unknown(declared, old, new, named):
    leveled(declared, LEVELS.replace(old, new))
    with pytest.raises(FilmError, match=named):
        film.load(declared)


def test_review_levels_are_the_three_and_ask_something(declared):
    leveled(declared, LEVELS.replace('[review.levels."雅"]', '[review.levels."美"]'))
    with pytest.raises(FilmError, match="review.levels"):
        film.load(declared)
    leveled(declared, LEVELS.replace('asks = "natural, restrained and finished"', 'asks = " "'))
    with pytest.raises(FilmError, match="asks"):
        film.load(declared)


def identities() -> set[str]:
    """What names this film.

    Its file prefix, delivery folder and source, and each edition's title, title parts,
    author and chapter titles.
    """
    names = {film.FILM.slug, film.FILM.documents_folder}
    source = repository.read(film.FILM.source_manifest)["repository"]
    names |= {source, source.rstrip("/").rsplit("/", 1)[-1]}
    for code in CODES:
        script = repository.read(Edition(code).script)
        names |= {script["title"], *script["title"].split(" · "), script["author"]}
        names |= {chapter["title"] for chapter in script["chapters"]}
    return names


def test_the_engine_names_no_film():
    found = []
    for path in sorted((repository.ROOT / "src/filmkit").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").casefold()
        found += [
            f"{path.relative_to(repository.ROOT)}: {name}"
            for name in sorted(identities())
            if name.casefold() in text
        ]
    assert found == []


def test_each_edition_declares_the_words_and_colours_of_its_player():
    assert film.FILM.player == film.Player(
        background="#0F1519", text="#ECE8DF", muted="#9BA8B1", line="#34424E", accent="#7DB7D8"
    )
    for code in CODES:
        summary = film.FILM.editions[code].summary
        assert summary and summary == summary.strip()
        assert not (repository.ROOT / film.FILM.editions[code].sources / "player.html").exists()
    assert CHINESE.search(film.FILM.editions["en"].summary) is None


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ('accent = "#7DB7D8"', 'accent = "blue"', "player.accent"),
        ('background = "#0F1519"\n', "", "player.background"),
        ('summary = "这部', 'summary = " "\n# "这部', "editions.zh.summary"),
        ('summary = "A one-minute', '# summary = "A one-minute', "editions.en.summary"),
    ],
)
def test_a_player_declaration_refuses_naming_its_field(declared, old, new, field):
    rewrite(declared, old, new)
    with pytest.raises(FilmError, match=re.escape(field)):
        film.load(declared)


def test_a_film_not_yet_migrated_from_its_player_refuses_naming_the_declarations(declared):
    # As a film stands before it adopts the engine's player: a page of its own, neither word
    # nor colour declared.
    path = declared / film.DECLARATION
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    palette = lines.index("[player]\n")
    del lines[palette : palette + 7]
    path.write_text(
        "".join(line for line in lines if not line.startswith("summary = ")), encoding="utf-8"
    )
    (declared / film.FILM.editions["zh"].sources / "player.html").write_text("<html></html>")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    for field in ("editions.zh.summary", "editions.en.summary", "player\n"):
        assert field in str(refusal.value)


def test_a_player_template_left_in_the_sources_refuses_naming_the_declarations(declared):
    (declared / film.FILM.editions["en"].sources / "player.html").write_text("<html></html>")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert "content/en/player.html" in str(refusal.value)
    assert "editions.<code>.summary" in str(refusal.value)
    assert "[player]" in str(refusal.value)


FLOW = """
[narration.flow]
switch_limit_s = 0.15
unmarked_limit_s = 0.35
exceptions = [
  { edition = "en", thought = "02.3", left = "seed", right = "so", reason = "A kept pause." },
]
"""


def declare_flow(root: Path, table: str) -> None:
    """Append a [narration.flow] table to the declaration at a root."""
    path = root / film.DECLARATION
    path.write_text(path.read_text() + table)


def test_narration_flow_limits_default_and_are_declared_with_their_exceptions(declared):
    assert film.FILM.narration.flow == film.Flow()
    assert (film.Flow().switch_limit_s, film.Flow().unmarked_limit_s) == (0.2, 0.4)
    declare_flow(declared, FLOW)
    flow = film.load(declared).narration.flow
    assert (flow.switch_limit_s, flow.unmarked_limit_s) == (0.15, 0.35)
    assert [(e.edition, e.thought, e.left, e.right, e.reason) for e in flow.exceptions] == [
        ("en", "02.3", "seed", "so", "A kept pause.")
    ]


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("switch_limit_s = 0.15", "switch_limit_s = 0", r"narration\.flow\.switch_limit_s"),
        ("unmarked_limit_s = 0.35", "unmarked_limit_s = 3", r"narration\.flow\.unmarked_limit_s"),
        (', reason = "A kept pause."', "", r"exceptions\.0\.reason"),
        ('reason = "A kept pause."', 'reason = "  "', r"exceptions\.0\.reason"),
        ('thought = "02.3"', 'thought = "02"', r"exceptions\.0\.thought"),
        ('edition = "en"', 'edition = "fr"', r"exceptions\.0\.edition"),
        ("exceptions = [", "pause = 1\nexceptions = [", r"narration\.flow\.pause"),
    ],
)
def test_a_narration_flow_declaration_refuses_naming_its_field(declared, old, new, field):
    assert old in FLOW
    declare_flow(declared, FLOW.replace(old, new))
    with pytest.raises(FilmError, match=field):
        film.load(declared)


def test_two_exceptions_of_one_boundary_refuse(declared):
    again = '  { edition = "en", thought = "02.3", left = "Seed", right = "so", reason = "Too." },'
    declare_flow(declared, FLOW.replace("},\n]", "},\n" + again + "\n]"))
    with pytest.raises(FilmError, match="two exceptions name one boundary"):
        film.load(declared)


TERMS = """
[[narration.terms]]
term = "ETHER"
spoken = "Eether"
ipa = "ˈiːθər"
reference = { zh = { thought = "01.6", index = 0 }, en = { thought = "03.7", index = 0 } }
"""


def test_narration_terms_are_declared_with_their_spoken_form_and_references(declared):
    assert film.FILM.narration.terms == ()
    declare_flow(declared, TERMS)
    (term,) = film.load(declared).narration.terms
    assert (term.term, term.spoken, term.ipa) == ("ETHER", "Eether", "ˈiːθər")
    places = {code: (ref.segment, ref.thought, ref.index) for code, ref in term.reference.items()}
    assert places == {"zh": ("01", "01.6", 0), "en": ("03", "03.7", 0)}


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ('spoken = "Eether"\n', "", r"narration\.terms\.0\.spoken"),
        ('term = "ETHER"', 'term = "two words"', r"narration\.terms\.0\.term"),
        ('ipa = "ˈiːθər"', 'ipa = " "', r"narration\.terms\.0\.ipa"),
        ('thought = "03.7"', 'thought = "03"', r"narration\.terms\.0\.reference\.en\.thought"),
        ("index = 0 } }", "index = -1 } }", r"narration\.terms\.0\.reference\.en\.index"),
        ("zh = {", "fr = {", r"narration\.terms\.0\.reference\.fr"),
        ("[[narration.terms]]\n", '[[narration.terms]]\nsay = "x"\n', r"narration\.terms\.0\.say"),
        (TERMS, TERMS + TERMS.replace('"ETHER"', '"Ether"'), "a term is declared more than once"),
    ],
)
def test_a_narration_term_declaration_refuses_naming_its_field(declared, old, new, field):
    assert old in TERMS
    declare_flow(declared, TERMS.replace(old, new))
    with pytest.raises(FilmError, match=field):
        film.load(declared)
