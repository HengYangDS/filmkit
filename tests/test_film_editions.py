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
    # Its entry page links its one edition alone.
    page = declared / film.FILM.entry
    lines = page.read_text(encoding="utf-8").splitlines(keepends=True)
    page.write_text("".join(line for line in lines if 'href="zh/' not in line), encoding="utf-8")
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
    assert f"{name}:{end - 1} cites {{other}}, which the engine no longer fills; name every" in said
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
    *moved, sources, script, other = str(refusal.value).split("\n", 4)
    # Each file is named with its destination (task 8.1), and its keys where it stands.
    assert moved == [
        f"content/{name} is the zh edition's file at its old place; move it to content/zh/{name}"
        for name in film.EDITION_FILES
    ]
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
    # The table names no key of a declaration or a segment yet; each later withdrawal adds its
    # row, and the loader reads every kind of place for it.
    rows = [
        withdrawn.Withdrawn(kind, "held", "remove it")
        for kind in ("declaration", "review", "edition", "segment", "part")
    ]
    monkeypatch.setattr(withdrawn, "WITHDRAWN", (*withdrawn.WITHDRAWN, *rows))
    rewrite(declared, "credits_duration = 3", "credits_duration = 3\nheld = 1")
    rewrite(declared, "[review]\n", "[review]\nheld = 1\n")
    rewrite(declared, "[editions.en]\n", "[editions.en]\nheld = 1\n")
    script = json.loads((declared / "content/zh" / film.SCRIPT).read_text())
    script["segments"][0]["held"] = 1
    (declared / "content/zh" / film.SCRIPT).write_text(json.dumps(script, ensure_ascii=False))
    (declared / "content/en/pronunciation.json").write_text('{"held": 1}')
    segment = script["segments"][0]["id"]
    assert film.problems(declared)[:5] == [
        "content/film.toml declares held; remove it",
        "content/film.toml review declares held; remove it",
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


@pytest.mark.parametrize(
    ("kind", "file", "key", "value"),
    [
        ("script", f"content/zh/{film.SCRIPT}", "pronunciation_contract", "content/v.json"),
        ("part", "content/zh/pronunciation.json", "language", "Chinese"),
        ("part", "content/en/pronunciation.json", "occurrence_plan", {"count": 0, "entries": []}),
    ],
)
def test_a_pronunciation_not_split_by_edition_is_refused_at_load(declared, kind, file, key, value):
    # Each edition's pronunciation stands in its folder, which states its language; the readings
    # check derives the occurrence plan, and no script names a contract.
    path = declared / file
    if not path.exists():
        path.write_text("{}")
    declare(path, **{key: value})
    assert film.problems(declared) == [f"{file} declares {key}; {withdrawn.keys(kind)[key]}"]


def test_the_review_tables_readings_are_refused_beside_other_problems(declared):
    rewrite(declared, "[review]\n", '[review]\nreadings = "content/review/readings.json"\n')
    rewrite(declared, 'slug = "sample-reel"', 'slug = "Two Words"')
    first, other = film.problems(declared)
    assert first == (
        f"content/film.toml review declares readings; {withdrawn.keys('review')['readings']}"
    )
    # The key is set aside: pydantic names the file prefix alone, and not the withdrawn key.
    assert "\nslug\n" in other and "review.readings" not in other


# The chapter of each of the sample's segments, by its index and title, which its scripts stated
# until the engine derived them.
SAMPLE_CHAPTERS = {
    "zh": [(0, "从源文件开始"), (1, "一次离线构建"), (1, "一次离线构建"), (2, "逐项核对")],
    "en": [
        (0, "Where a film begins"),
        (1, "One offline build"),
        (1, "One offline build"),
        (2, "Checked against its sources"),
    ],
}


def test_the_timeline_values_of_the_sample_are_those_its_scripts_stated():
    for code in production.CODES:
        derived = film.timeline_values(repository.read(production.Edition(code).script), film.FILM)
        assert (derived["author"], derived["fps"]) == ("Yang HENG", 60)
        chapters = [(s["chapter_index"], s["chapter_title"]) for s in derived["segments"]]
        assert chapters == SAMPLE_CHAPTERS[code]
    # A segment's chapter fields come from the chapter it names, whatever it states.
    script = repository.read(production.Edition("en").script)
    script["segments"][0] |= {"chapter": "check", "chapter_title": "Stated", "chapter_index": 7}
    derived = film.timeline_values(script, film.FILM)["segments"][0]
    assert (derived["chapter_index"], derived["chapter_title"]) == (
        2,
        script["chapters"][2]["title"],
    )
    script["segments"][0]["chapter"] = "nowhere"
    with pytest.raises(ValueError, match="hold no chapter of segment 01$"):
        film.timeline_values(script, film.FILM)


def test_a_declaration_without_its_author_is_refused_naming_it(declared):
    rewrite(declared, 'author = "Yang HENG"\n', "")
    (problem,) = film.problems(declared)
    assert "\nauthor\n  Field required" in problem


def test_staging_and_the_refresh_read_no_chapter_value_a_script_states():
    # Every comparison of a timeline with its script leaves out what the engine derives.
    import filmkit.captions.refresh as refresh
    import filmkit.picture.rendering as rendering

    script = repository.read(production.Edition("en").script)
    timeline = film.timeline_values(script, film.FILM)
    script["segments"][0] |= {"chapter_title": "Stated", "chapter_index": 7}
    assert rendering.follows_script(timeline, script)
    assert refresh.narration_source(script) == refresh.narration_source(timeline)


@pytest.mark.parametrize(
    ("kind", "key"),
    [
        ("script", "author"),
        ("script", "fps"),
        ("segment", "chapter_index"),
        ("segment", "chapter_title"),
    ],
)
def test_a_value_every_timeline_derives_is_refused_where_a_script_states_it(declared, kind, key):
    path = declared / "content/en" / film.SCRIPT
    script = json.loads(path.read_text())
    where = "content/en/film-script.json"
    held = script["segments"][0] if kind == "segment" else script
    held[key] = 1
    if kind == "segment":
        where += f" segment {held['id']}"
    path.write_text(json.dumps(script, ensure_ascii=False))
    assert film.problems(declared) == [f"{where} declares {key}; {withdrawn.keys(kind)[key]}"]


@pytest.mark.parametrize("key", ["model", "revision", "reference_mode", "scope"])
def test_a_cast_that_restates_a_pin_of_the_engine_or_keeps_its_scope_is_refused(declared, key):
    # The pins are removed; the scope, a record of how the reference recording was made, moves.
    declare(declared / "content/zh" / film.CAST, **{key: "a value"})
    (problem,) = film.problems(declared)
    assert problem.startswith(f"content/zh/voice-reference.json declares {key}; ")
    if key == "scope":
        assert problem.endswith(
            "move its text into the cast's derivation, as derivation.scope, "
            "which the engine keeps unread"
        )
    else:
        assert problem.split("; ", 1)[1].startswith("remove it: every request takes the engine's")


def test_each_sample_cast_keeps_its_scope_in_its_derivation():
    for code in production.CODES:
        cast = repository.read(production.Edition(code).cast)
        assert cast["derivation"]["scope"].startswith("The DDWG narrator's reference recording")
        assert not {"model", "revision", "reference_mode", "scope"} & set(cast)


@pytest.mark.parametrize(
    "key", ["performance_intent", "energy_curve", "pacing_profile", "provider_notes"]
)
def test_the_pause_policys_prose_is_refused_with_where_its_records_go(declared, key):
    path = declared / "content/en" / film.SCRIPT
    script = json.loads(path.read_text())
    script["voice_performance"][key] = "Words."
    path.write_text(json.dumps(script, ensure_ascii=False))
    assert film.problems(declared) == [
        f"content/en/film-script.json voice_performance declares {key}; remove it: no step reads "
        "it; move any words that record how the voice, its reference or its takes were made or "
        "approved into the edition's cast derivation, each under its own key"
    ]


# How the loader names an edition's file missing at the place its code derives.
MISSING = "content/film.toml names a missing file: "


def as_at_the_base(root: Path) -> None:
    """Put the sample's sources below a root back as they stood at the base, 0.30.0: the Chinese
    script and cast in content/ under a declared folder, its reference recording and cover
    without its code, a narration copy in each folder, one pronunciation contract named by each
    script and the analyst readings in content/review/."""
    rewrite(root, "[editions.zh]\n", '[editions.zh]\nsources = "content"\n')
    rewrite(root, 'sources = "content"\n', 'sources = "content"\ncover = "c.png"\n')
    rewrite(root, "[editions.en]\n", '[editions.en]\nsources = "content/en"\n')
    without(root, "pronunciation")
    for name in film.EDITION_FILES:
        (root / "content/zh" / name).rename(root / "content" / name)
    (root / "assets/audio/zh/narration-reference.wav").rename(root / "assets/audio/clear.wav")
    declare(root / "content" / film.CAST, reference_audio="assets/audio/clear.wav")
    (root / "c.png").write_bytes(b"cover")
    for folder in ("content", "content/en"):
        (root / folder / "narration.md").write_text("Narration.\n")
        declare(
            root / folder / film.SCRIPT, pronunciation_contract="content/voice-performance.json"
        )
    for part in ("content/zh/pronunciation.json", "content/en/pronunciation.json"):
        (root / part).unlink()
    (root / "content/voice-performance.json").write_text("{}")
    (root / "content/review/readings.json").write_text("{}")


def test_the_sample_as_it_stood_at_the_base_is_named_once_in_one_refusal(declared):
    as_at_the_base(declared)
    with pytest.raises(FilmError) as refusal:
        film.load(declared)
    problems = str(refusal.value).splitlines()
    moved = {
        "content/film-script.json": "content/zh/film-script.json",
        "content/voice-reference.json": "content/zh/voice-reference.json",
        "c.png": "assets/cover/sample-reel-cover-zh.png",
        "assets/audio/clear.wav": "assets/audio/zh/narration-reference.wav",
    }
    named = [
        f"{old} is the zh edition's file at its old place; move it to {new}"
        for old, new in moved.items()
    ]
    named += [
        f"{MISSING}editions.{code}: content/{code}/pronunciation.json" for code in ("zh", "en")
    ]
    named += [
        f"{path}: this release removes it; "
        for path in (
            "content/voice-performance.json",
            "content/review/readings.json",
            "content/narration.md",
            "content/en/narration.md",
        )
    ]
    named += [
        "content/film.toml declares no [pronunciation]; ",
        "content/film.toml editions.zh declares sources; ",
        "content/film.toml editions.zh declares cover; ",
        "content/film.toml editions.en declares sources; ",
        "content/film-script.json declares pronunciation_contract; ",
        "content/en/film-script.json declares pronunciation_contract; ",
        "content/voice-reference.json declares reference_audio; ",
    ]
    for fact in named:
        assert sum(line.startswith(fact) for line in problems) == 1, fact
    assert not any("missing file: editions.zh: content/zh/film-script" in line for line in problems)


def test_a_film_that_removed_its_contract_without_splitting_it_is_named(declared):
    (declared / "content/voice-performance.json").write_text("{}")
    without(declared, "pronunciation")
    for code in ("zh", "en"):
        (declared / f"content/{code}/pronunciation.json").unlink()
    problems = film.problems(declared)
    assert problems[0].startswith(f"{MISSING}editions.zh: content/zh/pronunciation.json")
    assert problems[1].startswith(f"{MISSING}editions.en: content/en/pronunciation.json")
    assert problems[2].startswith(
        "content/voice-performance.json: this release removes it; split it by edition"
    )
    assert problems[3].startswith("content/film.toml declares no [pronunciation]; ")
    assert len(problems) == 4


def test_a_reference_recording_the_cast_no_longer_names_is_named_missing_at_its_place(declared):
    (declared / "assets/audio/zh/narration-reference.wav").unlink()
    assert film.problems(declared) == [
        f"{MISSING}editions.zh: assets/audio/zh/narration-reference.wav"
    ]


def test_a_cast_names_the_identity_recording_at_its_place(declared):
    declare(
        declared / "content/zh" / film.CAST,
        derivation={"from": "assets/audio/narration-reference.wav"},
    )
    assert film.problems(declared) == [
        "content/zh/voice-reference.json derivation cites assets/audio/narration-reference.wav; "
        "move the recording every reference derives from to assets/audio/narrator-identity.wav and "
        "cite it there"
    ]
    # Where the film holds the identity recording, each cast's derivation names it.
    (declared / "assets/audio/narrator-identity.wav").write_bytes(b"identity")
    declare(
        declared / "content/zh" / film.CAST,
        derivation={"from": "assets/audio/narrator-identity.wav"},
    )
    assert film.problems(declared) == [
        "content/en/voice-reference.json has no derivation that names "
        "assets/audio/narrator-identity.wav, the recording every reference derives from; record "
        "there how the reference was made from it"
    ]


def test_a_script_at_its_old_place_is_named_with_its_destination_and_not_as_missing(declared):
    (declared / "content/zh" / film.SCRIPT).rename(declared / "content" / film.SCRIPT)
    assert film.problems(declared) == [
        "content/film-script.json is the zh edition's file at its old place; move it to "
        "content/zh/film-script.json"
    ]


def test_an_unreadable_cast_is_named(declared):
    (declared / "content/en" / film.CAST).write_text("{")
    (problem,) = film.problems(declared)
    assert problem.startswith("content/en/voice-reference.json cannot be read: ")
