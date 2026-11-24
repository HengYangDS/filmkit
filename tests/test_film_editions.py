"""A film's editions are the languages its declaration names, in its order, one or more: each
needs a language declaration, and everything the declaration states of an edition names one of
them."""

import json
import shutil
from pathlib import Path

import pytest

import filmkit.film as film
import filmkit.production as production
import filmkit.repository as repository
import filmkit.withdrawn as withdrawn
from filmkit.film import FilmError


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
    path = root / film.DECLARATION
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))


def table(root: Path, name: str) -> str:
    """One table of the declaration, from its header to the next blank line before a header."""
    text = (root / film.DECLARATION).read_text()
    start = text.index(f"[{name}]\n")
    end = text.index("\n\n", start) + 2
    return text[start:end]


def without(root: Path, name: str) -> None:
    """Remove one table of the declaration."""
    rewrite(root, table(root, name), "")


def test_the_editions_are_the_declarations_in_its_order():
    assert production.CODES == tuple(film.FILM.editions) == ("zh", "en")
    assert production.codes(film.FILM) == production.CODES


def test_a_declaration_whose_english_table_comes_first_lists_english_first(declared):
    zh = table(declared, "editions.zh")
    rewrite(declared, zh, "")
    rewrite(declared, "[picture]\n", f"{zh}[picture]\n")
    # The entry page links the editions in the declared order (`filmkit.delivery.entry`).
    page = declared / film.FILM.entry
    zh_link, en_link = (
        next(line for line in page.read_text().splitlines() if f'href="{code}/' in line)
        for code in ("zh", "en")
    )
    page.write_text(page.read_text().replace(f"{zh_link}\n{en_link}", f"{en_link}\n{zh_link}"))
    assert production.codes(film.load(declared)) == ("en", "zh")


def test_a_film_of_one_edition_loads(declared):
    without(declared, "editions.zh")
    rewrite(
        declared,
        "clarity_minimum_db = { zh = 18.0, en = 16.0 }",
        "clarity_minimum_db = { en = 16.0 }",
    )
    loaded = film.load(declared)
    assert tuple(loaded.editions) == ("en",)


def test_a_declaration_of_no_edition_is_refused(declared):
    without(declared, "editions.zh")
    without(declared, "editions.en")
    with pytest.raises(FilmError, match="editions"):
        film.load(declared)


def test_an_edition_without_a_language_declaration_is_refused_in_one_line(declared):
    rewrite(declared, "[editions.en]", "[editions.xq]")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    named = "editions.xq: the engine holds no language declaration for 'xq'; it declares en, zh"
    assert [line for line in str(refusal.value).splitlines() if named in line]


def test_an_exception_of_an_undeclared_edition_is_refused(declared):
    exception = '[[captions.rate_exceptions]]\nedition = "ja"\ntext = "A cue"\nreason = "Kept."\n\n'
    rewrite(declared, "[review]\n", f"{exception}[review]\n")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert (
        "captions.rate_exceptions names the edition ja, which the film does not declare; it "
        "declares zh, en"
    ) in str(refusal.value)


def test_floors_for_an_undeclared_edition_or_without_a_declared_one_are_refused(declared):
    rewrite(declared, "{ zh = 18.0, en = 16.0 }", "{ zh = 18.0, en = 16.0, ja = 17.0 }")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert "review.clarity_minimum_db names the edition ja" in str(refusal.value)
    rewrite(declared, "{ zh = 18.0, en = 16.0, ja = 17.0 }", "{ zh = 18.0 }")
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    assert "review.clarity_minimum_db states no floor for en" in str(refusal.value)


def test_a_flat_list_of_lead_words_is_refused_with_what_to_write_instead(declared):
    rewrite(declared, "[review]\n", '[picture.wrapping]\nlead_words = ["versus"]\n\n[review]\n')
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    said = "picture.wrapping.lead_words is a list; key it by the language its words lead in"
    assert said in str(refusal.value)
    assert "lead_words = { en = ['versus'] }" in str(refusal.value)


def test_a_prompt_that_cites_the_former_fields_or_names_an_editions_files_is_refused(declared):
    prompt = declared / film.FILM.review.prompt
    prompt.parent.mkdir(parents=True, exist_ok=True)
    text = (repository.ROOT / film.FILM.review.prompt).read_text(encoding="utf-8")
    text += "- The {other_language} ({other}) edition.\n"
    text += "- Scripts: ROOT/content/en/film-script.json in ROOT/build/{{zh,en}}/.\n"
    prompt.write_text(text, encoding="utf-8")
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    said = str(refusal.value)
    end = len(text.splitlines())
    name = film.FILM.review.prompt
    assert f"{name}:{end - 1} cites {{other}}, which the engine no longer fills; name the" in said
    assert f"{name}:{end - 1} cites {{other_language}}" in said and "by {others}" in said
    assert f"{name}:{end} names an edition's files by their path; name every edition's" in said
    assert f"{name}:{end} groups the editions' codes in braces;" in said
    assert "slug" in said


def test_an_entry_page_that_breaks_its_rule_is_refused_at_load_beside_other_problems(declared):
    page = declared / film.FILM.entry
    page.write_text(page.read_text().replace('<html lang="mul">', '<html lang="zh-CN">'))
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    said = str(refusal.value)
    assert 'content/index.html opens with lang="zh-CN"; its root is <html lang="mul">' in said
    assert "slug" in said
    page.write_text(page.read_text().replace('<html lang="zh-CN">', '<html lang="mul">'))
    rewrite(declared, 'slug = "Two Words"', 'slug = "sample-reel"')
    assert film.load(declared) == film.FILM


def test_every_place_of_an_edition_comes_from_its_code_alone():
    for code in ("zh", "en"):
        assert film.places(code, "sample-reel") == (
            f"content/{code}",
            f"content/{code}/film-script.json",
            f"content/{code}/voice-reference.json",
            f"content/{code}/pronunciation.json",
            f"content/{code}/readings.json",
            f"assets/audio/{code}/narration-reference.wav",
            f"assets/cover/sample-reel-cover-{code}.png",
        )


def declare(path: Path, **fields) -> None:
    """Add fields to a JSON file of the film."""
    path.write_text(json.dumps({**json.loads(path.read_text()), **fields}, ensure_ascii=False))


# What the loader says of a script's withdrawn runtime, at whichever place the script stands.
DURATION = "declares duration; " + withdrawn.keys("script")["duration"]


def test_a_withdrawn_key_is_refused_where_the_declaration_still_names_the_files(declared):
    # A film that has not moved its Chinese files keeps them where its declaration names them.
    for name in film.EDITION_FILES:
        (declared / "content/zh" / name).rename(declared / "content" / name)
    rewrite(declared, "[editions.zh]\n", '[editions.zh]\nsources = "content"\n')
    declare(declared / "content" / film.SCRIPT, duration=1500)
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    sources, script, other = str(refusal.value).split("\n", 2)
    assert sources == f"content/film.toml editions.zh declares sources; {WITHDRAWN['sources']}"
    assert script == f"content/film-script.json {DURATION}"
    assert "\nslug\n" in other


def test_a_withdrawn_key_is_refused_at_the_place_its_code_derives(declared):
    declare(declared / "content/zh" / film.SCRIPT, duration=1500)
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    first, other = film.problems(declared)
    assert first == f"content/zh/film-script.json {DURATION}"
    assert "\nslug\n" in other
    rewrite(declared, 'slug = "Two Words"', 'slug = "sample-reel"')
    assert film.problems(declared) == [first]


# What the loader says of each key an edition's table may no longer declare.
WITHDRAWN = withdrawn.keys("edition")


@pytest.mark.parametrize(("key", "value"), [("sources", '"content/en"'), ("cover", '"c.png"')])
def test_an_edition_s_folder_or_cover_is_refused_in_one_line_beside_other_problems(
    declared, key, value
):
    rewrite(declared, "[editions.en]\n", f"[editions.en]\n{key} = {value}\n")
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    first, other = film.problems(declared)
    assert first == f"content/film.toml editions.en declares {key}; {WITHDRAWN[key]}"
    # The key is set aside: pydantic names the file prefix alone, and not the withdrawn key.
    assert "\nslug\n" in other and f"editions.en.{key}" not in other
    rewrite(declared, 'slug = "Two Words"', 'slug = "sample-reel"')
    assert film.problems(declared) == [first]


@pytest.mark.parametrize(
    "fields", [{"reserve_seconds": 0.5}, {"reserve_seconds": 0.0}, {}, 0.1, None]
)
def test_a_cast_that_declares_runtime_fit_is_refused_whatever_it_holds(declared, fields):
    # Nothing reads it, since an edition lasts as long as its narration: a reserve, an empty
    # table and any other value are refused alike, before any command runs.
    declare(declared / "content/en" / film.CAST, runtime_fit=fields)
    assert film.problems(declared) == [
        "content/en/voice-reference.json declares runtime_fit; remove it: nothing reads it, since "
        "an edition lasts as long as its narration"
    ]


def test_every_kind_of_place_is_read_for_its_withdrawn_keys(declared, monkeypatch):
    # The table names no key of a declaration, an edition's table, a segment or a part yet;
    # each later withdrawal adds its row, and the loader reads every kind of place for it.
    rows = [
        withdrawn.Withdrawn(kind, "held", "remove it")
        for kind in ("declaration", "edition", "segment", "part")
    ]
    monkeypatch.setattr(withdrawn, "WITHDRAWN", (*withdrawn.WITHDRAWN, *rows))
    rewrite(declared, "credits_duration = 3", "credits_duration = 3\nheld = 1")
    rewrite(declared, "[editions.en]\n", "[editions.en]\nheld = 1\n")
    script = json.loads((declared / "content/zh" / film.SCRIPT).read_text())
    script["segments"][0]["held"] = 1
    (declared / "content/zh" / film.SCRIPT).write_text(json.dumps(script, ensure_ascii=False))
    (declared / "content/en/pronunciation.json").write_text('{"held": 1}')
    segment = script["segments"][0]["id"]
    assert film.problems(declared)[:4] == [
        "content/film.toml declares held; remove it",
        f"content/zh/film-script.json segment {segment} declares held; remove it",
        "content/film.toml editions.en declares held; remove it",
        "content/en/pronunciation.json declares held; remove it",
    ]


@pytest.mark.parametrize("place", ["top", "segment"])
def test_a_script_that_declares_its_language_is_refused_at_load(declared, place):
    path = declared / "content/zh" / film.SCRIPT
    script = json.loads(path.read_text())
    where = "content/zh/film-script.json"
    if place == "segment":
        script["segments"][1]["language"] = "Chinese"
        where += f" segment {script['segments'][1]['id']}"
    else:
        script["language"] = "Chinese"
    path.write_text(json.dumps(script, ensure_ascii=False))
    assert film.problems(declared) == [
        f"{where} declares language; remove it: the engine takes the edition's language from "
        "its code"
    ]


@pytest.mark.parametrize("key", withdrawn.keys("cast"))
def test_a_cast_that_declares_a_withdrawn_key_is_refused_at_load(declared, key):
    declare(declared / "content/en" / film.CAST, **{key: "a value"})
    assert film.problems(declared) == [
        f"content/en/voice-reference.json declares {key}; {withdrawn.keys('cast')[key]}"
    ]
