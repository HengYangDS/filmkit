"""The concept contract and the check that keeps a film's words to it."""

import json
import shutil
import subprocess

import pytest

import filmkit.concepts as concepts
import filmkit.repository as repository
import filmkit.sources as sources
from filmkit.concepts import ConceptError, Place

# A contract entry, as TOML, with its id and source path left to fill.
ENTRY = """
[[concept]]
id = "{id}"
term = "rebuild"
essence = "Making the films again from their tracked sources."
source = {{ path = "{path}", quote = "everything needed to rebuild them" }}
zh = {{ rendering = "重建", avoid = ["复刻"] }}
en = {{ rendering = "rebuild", forms = ["rebuilt"], avoid = ["remake"] }}
"""
PINNED = {"commit": "0" * 40, "members": [{"path": "README.md"}]}


@pytest.fixture
def root(tmp_path, monkeypatch):
    """An empty film root."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    monkeypatch.delenv(sources.CHECKOUT, raising=False)
    return tmp_path


def write_contract(root, *entries: str) -> str:
    """Write a contract of the given TOML entries and return its root-relative path."""
    (root / "content").mkdir(exist_ok=True)
    (root / "content/concepts.toml").write_text("".join(entries), encoding="utf-8")
    return "content/concepts.toml"


def segment(segment_id: str, thoughts: list[str], declared: list[str] | None = None) -> dict:
    """A script segment of authored thoughts that declares concepts."""
    item: dict = {"id": segment_id, "title": f"Part {segment_id}", "text": "".join(thoughts)}
    item["utterance_groups"] = thoughts
    if declared is not None:
        item["concepts"] = declared
    return item


def test_the_sample_film_passes_and_reports_its_quotations_unchecked():
    report = concepts.check()
    assert report["contract"] == "content/concepts.toml"
    assert report["concepts"] == 2
    assert report["quotations"] == "not_checked"
    assert report["declarations"] == 6


def test_a_film_without_a_contract_reports_none(monkeypatch):
    monkeypatch.setattr(concepts, "FILM", concepts.FILM.model_copy(update={"concepts": None}))
    assert concepts.check() == {"contract": None, "status": "not_declared"}


def test_a_repeated_id_and_an_unpinned_source_refuse_together(root):
    path = write_contract(
        root,
        ENTRY.format(id="rebuild", path="README.md"),
        ENTRY.format(id="rebuild", path="docs/other.md"),
    )
    with pytest.raises(ConceptError) as refusal:
        concepts.load(path, PINNED)
    assert str(refusal.value).splitlines() == [
        "Concept rebuild is declared more than once",
        "Concept rebuild cites docs/other.md, which the source manifest does not pin",
    ]


def test_a_malformed_contract_refuses_naming_the_field(root):
    path = write_contract(
        root, ENTRY.format(id="rebuild", path="README.md").replace("zh = ", "z = ")
    )
    with pytest.raises(
        ConceptError, match=r"(?s)is not a concept contract: .*concept\.0\.zh\n  Field required"
    ):
        concepts.load(path, PINNED)


def test_quotations_are_found_at_the_pinned_commit_of_a_clone(root, tmp_path, monkeypatch):
    clone = tmp_path / "source"
    clone.mkdir()
    (clone / "README.md").write_text(
        "It holds **everything needed\nto rebuild** them from `source`.\n"
    )

    def git(*arguments):
        return subprocess.run(
            ["git", "-C", str(clone), *arguments], capture_output=True, check=True, text=True
        ).stdout.strip()

    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=t", "-c", "user.email=t@example.test", "commit", "-qm", "docs")
    pinned = {"commit": git("rev-parse", "HEAD"), "members": [{"path": "README.md"}]}
    path = write_contract(root, ENTRY.format(id="rebuild", path="README.md"))
    contract = concepts.load(path, pinned)
    assert concepts.quotations(contract, pinned) == ("not_checked", [])
    monkeypatch.setenv(sources.CHECKOUT, str(clone))
    assert concepts.quotations(contract, pinned) == ("verified", [])
    # A later working-tree edit does not move the pinned commit.
    (clone / "README.md").write_text("changed\n")
    assert concepts.quotations(contract, pinned) == ("verified", [])
    missing = write_contract(
        root, ENTRY.format(id="rebuild", path="README.md").replace("them", "it")
    )
    status, failures = concepts.quotations(concepts.load(missing, pinned), pinned)
    assert status == "refused"
    assert failures == [
        f"Concept rebuild: the quotation is not in README.md at {pinned['commit'][:12]}"
    ]
    unread = {**pinned, "commit": "f" * 40}
    assert concepts.quotations(contract, unread)[1] == [
        "Concept rebuild: README.md cannot be read at ffffffffffff"
    ]


def test_english_matches_whole_words_ignoring_case_and_chinese_any_substring():
    assert concepts.found("The Rebuild is complete.", "rebuild", "en") == [4]
    assert concepts.found("rebuilding it", "rebuild", "en") == []
    assert concepts.found("这次重建才算完成。", "重建", "zh") == [2]


def test_declarations_must_be_known_alike_and_said(root):
    contract = concepts.load(
        write_contract(root, ENTRY.format(id="rebuild", path="README.md")), PINNED
    )
    scripts = {
        "zh": {
            "segments": [
                segment("01", ["从源文件重建出来。", "就这样。"], ["rebuild"]),
                segment("02", ["复原一遍。", "就这样。"], ["rebuild"]),
                segment("03", ["一句话。", "又一句。"], ["unknown"]),
            ]
        },
        "en": {
            "segments": [
                segment("01", ["It is rebuilt. ", "That is all."], ["rebuild"]),
                segment("02", ["It runs again. ", "That is all."], []),
                segment("03", ["One line. ", "Another."], ["unknown"]),
            ]
        },
    }
    assert concepts.declarations(contract, scripts) == [
        "zh 03 declares unknown, which the contract does not hold",
        "en 03 declares unknown, which the contract does not hold",
        "02 declares different concepts in its editions: rebuild",
        "zh 02 declares rebuild but says none of: 重建",
    ]


def test_counterexamples_are_named_wherever_a_viewer_meets_them(root):
    contract = concepts.load(
        write_contract(root, ENTRY.format(id="rebuild", path="README.md")), PINNED
    )
    places = {
        "zh": [Place("zh 01.2", "先复刻，再复刻。"), Place("zh 02 title", "重建")],
        "en": [Place("en caption term", "a Remake"), Place("en 01.1", "remakes")],
        "picture": [Place("picture/film.js:7", 'label("复刻")')],
    }
    assert concepts.counterexamples(contract, places) == [
        "zh 01.2 at 1: '复刻', a counterexample of rebuild",
        "zh 01.2 at 5: '复刻', a counterexample of rebuild",
        "picture/film.js:7 at 7: '复刻', a counterexample of rebuild",
        "en caption term at 2: 'remake', a counterexample of rebuild",
    ]


def test_picture_text_sources_are_read_by_line_outside_packages(root):
    (root / "picture/film/scenes").mkdir(parents=True)
    (root / "picture/node_modules/vendor").mkdir(parents=True)
    (root / "picture/film/scenes/kernel.js").write_text("one\ntwo\n")
    (root / "picture/index.html").write_text("<title>t</title>\n")
    (root / "picture/node_modules/vendor/lib.js").write_text("ignored\n")
    (root / "picture/cover.png").write_bytes(b"\x89PNG")
    assert concepts.picture_places() == [
        Place("picture/film/scenes/kernel.js:1", "one"),
        Place("picture/film/scenes/kernel.js:2", "two"),
        Place("picture/index.html:1", "<title>t</title>"),
    ]


def test_edition_places_name_titles_thoughts_caption_terms_release_and_player():
    script = {
        "title": "Film",
        "chapters": [{"id": "sources", "title": "Where it begins"}],
        "segments": [segment("01", ["First. ", "Second."])],
        "release": {"synopsis": "A film.", "comment": "For tests.", "description": "English"},
    }
    places = concepts.edition_places("en", script)
    assert places[:-1] == [
        Place("en title", "Film"),
        Place("en chapter sources title", "Where it begins"),
        Place("en 01 title", "Part 01"),
        Place("en 01.1", "First. "),
        Place("en 01.2", "Second."),
        Place("en caption term", "reference recording"),
        Place("en caption term", "build folder"),
        Place("en release synopsis", "A film."),
        Place("en release comment", "For tests."),
        Place("en release description", "English"),
    ]
    # The player's prose: what its page shows, outside its scripts and styles.
    assert places[-1].where == "en player"
    assert "A one-minute film that shows how a film is rebuilt from its sources." in places[-1].text
    assert "/*CHAPTERS*/" not in places[-1].text


def test_a_counterexample_in_the_player_or_the_synopsis_refuses(tmp_path, monkeypatch):
    shutil.copytree(repository.ROOT / "content", tmp_path / "content")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    player = tmp_path / "content/player.html"
    page = player.read_text(encoding="utf-8")
    player.write_text(
        page.replace("</body>", "<p>它能复刻影片</p><script>const 复刻 = 1;</script></body>"),
        encoding="utf-8",
    )
    path = tmp_path / "content/en/film-script.json"
    script = json.loads(path.read_text(encoding="utf-8"))
    script["release"]["synopsis"] = "How to remake a film."
    path.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ConceptError) as refused:
        concepts.check()
    failures = str(refused.value).splitlines()
    assert [line.split(" at ")[0] for line in failures] == ["zh player", "en release synopsis"]
    assert failures[1] == "en release synopsis at 7: 'remake', a counterexample of rebuild"


def test_the_cli_prints_the_report_and_refuses_with_every_failure(monkeypatch, capsys):
    concepts.main()
    assert json.loads(capsys.readouterr().out)["concepts"] == 2

    def refuse():
        message = "one\ntwo"
        raise ConceptError(message)

    monkeypatch.setattr(concepts, "check", refuse)
    with pytest.raises(SystemExit, match="concepts: one\ntwo"):
        concepts.main()


def test_the_check_refuses_a_counterexample_in_the_sample_film(tmp_path, monkeypatch):
    shutil.copytree(repository.ROOT / "content", tmp_path / "content")
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    path = tmp_path / "content/film-script.json"
    script = json.loads(path.read_text(encoding="utf-8"))
    script["segments"][0]["title"] = "复刻"
    path.write_text(json.dumps(script, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ConceptError, match="zh 01 title at 0: '复刻', a counterexample of rebuild"):
        concepts.check()
