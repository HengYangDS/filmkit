"""A film's editions are the languages its declaration names, in its order, one or more: each
needs a language declaration, and everything the declaration states of an edition names one of
them."""

import shutil
from pathlib import Path

import pytest

import filmkit.film as film
import filmkit.production as production
import filmkit.repository as repository
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
