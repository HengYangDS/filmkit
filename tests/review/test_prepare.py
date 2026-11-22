"""Exercise the review round's preparation: one command writes the round's directory.
`test_prepare_again` holds a second preparation of a round."""

import json
import re
import subprocess
from pathlib import Path

import pytest
from preparing import PREPARED, REGISTER_REPORT, ROUND, names, prepare, refusal, tree
from still_records import REQUIRE_FILM_SCAN

import filmkit.concepts as concepts
import filmkit.delivery.folder as delivery_folder
import filmkit.media as media
import filmkit.picture.still_scan as still_scan
import filmkit.register as register
import filmkit.repository as repository
import filmkit.review.files as review_files
import filmkit.review.measurement as review_measurement
import filmkit.review.prompts as review_prompts
import filmkit.review.round as review_round
import filmkit.soundtrack.level as soundtrack_level
import filmkit.sources as sources
import filmkit.tools as tools
from filmkit.film import FILM, Film
from filmkit.narration.spoken_units import AlignmentError
from filmkit.picture.errors import PictureError
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

# Each edition's files that the prompts write: its sentences and its prompt.
PROMPTED = (("sentences", "json"), ("prompt", "md"))
# The register check itself, kept before the fixture of a ready build stands in for it.
REGISTER_CHECK = register.check


def test_prepare_writes_the_round_of_a_ready_build_and_its_prompts_last(
    root, put, ready, previous, capsys, monkeypatch
):
    asked, words = [], []

    def passing(edition):
        asked.append(edition.code)
        return {}

    def reported():
        words.append(dict(REGISTER_REPORT))
        return words[-1]

    monkeypatch.setattr(still_scan, "require_film_scan", passing)
    monkeypatch.setattr(register, "check", reported)
    changes = put(root / "notes/changes.md", "- Repairs: 07.6 names all seven checks.\n")
    folder = prepare(*previous, "--changes", changes)
    # Each edition's still scan is asked twice, in the editions' order. The requirement is one
    # of the checks that only read, and a preparation asks those before it derives anything
    # and again when the prompts are written, from the round's own copies of the note and the
    # dispositions.
    assert asked == [*CODES, *CODES]
    bound = ["changes.md", "dispositions.json", "player-check-artifacts.json", "register.json"]
    planned = sorted([*bound, "pronunciation-listening-plan.json"])
    measured = sorted([*planned, "measurements.json"])
    kept = sorted([*measured, "player-check.json", "player-en.png", "player-zh.png"])
    # Each step began on the files of the steps before it: the copies of the note and the
    # dispositions and the register report first, the measurements before the browser, and the
    # prompts last.
    assert ready == [
        ("listening plan", bound),
        ("measurements", planned),
        ("readback", measured),
        ("prompts", kept),
    ]
    assert names(folder) == sorted(
        [*kept, *(f"{name}-{code}.{kind}" for code in CODES for name, kind in PROMPTED)]
    )
    assert json.loads(capsys.readouterr().out) == {
        "round": PREPARED,
        "members": 25,
        "prompts": [f"{PREPARED}/prompt-{code}.md" for code in CODES],
    }
    # The readback is the round's own: a verdict for each page, and its screenshots in the round.
    readback = json.loads((folder / "player-check.json").read_text())
    assert [page["verdict"] for page in readback["pages"]] == ["pass"] * 3
    assert [Path(shot["path"]) for shot in readback["screenshots"]] == [
        folder / f"player-{code}.png" for code in CODES
    ]
    # The measurements are written as the measurement's own command writes them.
    stated = json.dumps({"scope": "stand-in", "editions": {}}, ensure_ascii=False, indent=2)
    assert (folder / "measurements.json").read_text() == stated + "\n"
    # The register report is the check's own, written as the engine writes a record, and the
    # check was asked once: the report in the round is the one that admitted it.
    assert json.loads((folder / "register.json").read_text()) == REGISTER_REPORT
    assert len(words) == 1
    assert (folder / "changes.md").read_bytes() == changes.read_bytes()
    assert (folder / "dispositions.json").read_bytes() == previous[3].read_bytes()
    for code in CODES:
        text = (folder / f"prompt-{code}.md").read_text()
        for film in Edition(code).films:
            assert f"- {film} (SHA-256 {repository.sha(film)})" in text
        # Each prompt cites the round's directory for the round's inputs.
        for cited in (
            f"Write only under ROOT/{PREPARED}/.",
            f"ROOT/{PREPARED}/measurements.json records the cepstral peak prominence",
            f"ROOT/{PREPARED}/sentences-{code}.json lists every sentence of this edition",
            f"ROOT/{PREPARED}/register.json is the register check's report",
            "- Repairs: 07.6 names all seven checks.\n",
        ):
            assert cited in text
    assert (
        "    - R18-1: The card names all seven checks.\n" in (folder / "prompt-zh.md").read_text()
    )


def test_a_prepared_round_holds_the_register_report_and_each_prompt_names_it_with_the_rules(
    ready, monkeypatch
):
    kept = {"place": "zh title", "form": "其实", "within": "名副其实", "reason": "an idiom"}
    declared = {**FILM.model_dump(by_alias=True), "register": {"exceptions": [kept]}}
    monkeypatch.setattr(register, "FILM", Film.model_validate(declared))
    held = [
        ("zh title", "这个示例名副其实"),
        ("zh 01.1", "我们先看。"),
        ("en 01.1", "Why? And how?"),
    ]
    places = [concepts.Place(where, text) for where, text in held]
    monkeypatch.setattr(concepts, "places", lambda: {"both": places})
    monkeypatch.setattr(register, "check", REGISTER_CHECK)
    folder = prepare()
    # The report holds each warning with its place and form, and each exception the check
    # applied with the text its form stands within and its reason.
    report = json.loads((folder / "register.json").read_text())
    assert sorted(report) == ["excused", "places", "vale", "warnings"]
    assert [(warning["place"], warning["form"]) for warning in report["warnings"]] == [
        ("zh 01.1", "我们"),
        ("en 01.1", "?"),
    ]
    assert (report["places"], report["excused"]) == (3, [kept])
    # Each prompt names the report and carries the rules as the standard's document states them:
    # its own lines from R1 to its end.
    standard = Path(register.__file__).with_name("standard.md").read_text(encoding="utf-8")
    rules = standard[standard.index("- **R1. The film does not address its audience.**") :]
    assert rules.count("\n- **R") == 5
    assert "- **R6. Terms and collocations of the field.**" in rules
    for code in CODES:
        text = (folder / f"prompt-{code}.md").read_text()
        assert f"ROOT/{PREPARED}/register.json is the register check's report" in text
        assert rules in text
        # The prompt tells its reader of two parts of the report by name, and the round's report
        # holds each under that name.
        (told,) = (line for line in text.splitlines() if "is the register check's report" in line)
        named = re.findall(r"`(\w+)`", told)
        assert len(named) == 2
        assert all(isinstance(report[name], list) for name in named)


def test_the_binding_names_the_language_entry_and_each_delivery_member(root, ready):
    folder = prepare()
    binding = json.loads((folder / "player-check-artifacts.json").read_text())
    assert binding["destination"] == str(root / "build/artifacts/film")
    # The members are the delivery's own plan: the entry page, then each edition's four films
    # and its viewing members.
    paths = [member["path"] for member in binding["members"]]
    assert paths == [path for _, path in delivery_folder.plan(root)]
    assert (len(paths), paths[0], paths[1]) == (25, "index.html", "zh/sample-reel-zh-uhd.mp4")
    for member in binding["members"]:
        assert member["sha256"] == repository.sha(root / "build/artifacts/film" / member["path"])
    (root / "build/artifacts/film/en/index.html").unlink()
    before = tree(folder)
    assert refusal() == "prepare: missing build/artifacts/film/en/index.html"
    assert tree(folder) == before


def test_prepare_refuses_what_it_reads_before_it_derives_anything(root, review, put, ready):
    folder = review_files.round_directory(ROUND)
    film = Edition("en").film("uhd")
    body = film.read_bytes()
    film.unlink()
    assert refusal() == "prepare: missing build/artifacts/film/en/sample-reel-en-uhd.mp4"
    film.write_bytes(body)
    earlier = review_files.round_directory(18)
    review(earlier, "zh")
    review(earlier, "en")
    assert refusal("--previous", earlier) == (
        "prepare: --previous build/evidence/reviews/round-18 needs --dispositions <file>, a "
        "disposition of each of its findings"
    )
    # A dispositions file that is no JSON is refused by name, not shown as a fault.
    disposed = put(root / "notes/dispositions.json", "{round: 18")
    assert refusal("--previous", earlier, "--dispositions", disposed) == (
        "prepare: notes/dispositions.json is not JSON: Expecting property name enclosed in "
        "double quotes: line 1 column 2 (char 1)"
    )
    put(disposed, {"round": 18, "findings": {}})
    given = ("--previous", earlier, "--dispositions", disposed)
    assert refusal(*given, "--changes", root / "notes/changes.md") == (
        "prepare: missing notes/changes.md"
    )
    # Nothing was derived, and the round's directory does not exist.
    assert ready == []
    assert not folder.exists()


def test_a_film_without_its_passing_still_scan_is_refused_and_leaves_no_directory(
    ready, monkeypatch
):
    folder = review_files.round_directory(ROUND)
    # Below this root no edition holds a record, and the scan's own requirement says so.
    monkeypatch.setattr(still_scan, "require_film_scan", REQUIRE_FILM_SCAN)
    assert refusal() == "prepare: The zh film has no still scan record; run scan-film"
    assert (ready, folder.exists()) == ([], False)
    asked = []

    def held(edition):
        asked.append(edition.code)
        if edition.code == "en":
            msg = "The en film holds a still picture with 3.5 s of speech or more: 1.00-5.00 s"
            raise PictureError(msg)
        return {}

    # Both editions are asked before anything is derived: the second's refusal is the round's.
    monkeypatch.setattr(still_scan, "require_film_scan", held)
    assert refusal() == (
        "prepare: The en film holds a still picture with 3.5 s of speech or more: 1.00-5.00 s"
    )
    assert asked == list(CODES)
    assert (ready, folder.exists()) == ([], False)


def test_a_preparation_that_stops_while_it_derives_refuses_in_one_line_and_leaves_no_prompt(
    ready, monkeypatch
):
    folder = review_files.round_directory(ROUND)
    measure = review_measurement.measure

    def unbound():
        message = "zh: the picture gate record is not bound to the current timeline"
        raise ReviewError(message)

    # The measurement refuses after the binding was written, and before the browser starts.
    monkeypatch.setattr(review_measurement, "measure", unbound)
    assert refusal() == (
        "prepare: zh: the picture gate record is not bound to the current timeline"
    )
    assert names(folder) == [
        "player-check-artifacts.json",
        "pronunciation-listening-plan.json",
        "register.json",
    ]
    assert [name for name, _ in ready] == ["listening plan"]
    monkeypatch.setattr(review_measurement, "measure", measure)

    def failing(binding, receipt):
        problem = "sample-reel-zh.ass resolves to zh/sample-reel-zh.ass, which is no member"
        pages = [{"page": "zh/index.html", "verdict": "fail", "problems": [problem]}]
        receipt.write_text(json.dumps({"pass": False, "pages": pages}))
        return 1

    # A player that links a file the members do not hold refuses the round by page and link.
    monkeypatch.setattr(delivery_folder, "check_players", failing)
    assert refusal() == (
        "prepare: The players fail their readback: zh/index.html: "
        "sample-reel-zh.ass resolves to zh/sample-reel-zh.ass, which is no member"
    )
    # The round keeps the failing readback and holds no sentences and no prompt.
    assert names(folder) == [
        "measurements.json",
        "player-check-artifacts.json",
        "player-check.json",
        "pronunciation-listening-plan.json",
        "register.json",
    ]

    def absent(binding, receipt):
        message = "No node on PATH"
        raise delivery_folder.tools.ToolError(message)

    monkeypatch.setattr(delivery_folder, "check_players", absent)
    assert refusal() == "prepare: The player check cannot run: No node on PATH"
    assert names(folder) == [
        "measurements.json",
        "player-check-artifacts.json",
        "pronunciation-listening-plan.json",
        "register.json",
    ]


@pytest.mark.usefixtures("root")
def test_the_commands_prompts_and_bind_are_gone(capsys):
    for removed in (["prompts", "--round", "1"], ["bind", "--out", "binding.json"]):
        with pytest.raises(SystemExit) as stopped:
            review_round.main(removed)
        assert stopped.value.code == 2
        assert f"invalid choice: '{removed[0]}'" in capsys.readouterr().err
    assert not hasattr(review_round, "bind")


@pytest.mark.parametrize(
    "encoded",
    [
        pytest.param(lambda text: b"\xef\xbb\xbf" + text.encode(), id="a byte order mark"),
        pytest.param(lambda text: text.encode("utf-16"), id="UTF-16"),
    ],
)
def test_dispositions_the_engine_s_reader_cannot_decode_are_refused_by_name(
    root, review, ready, encoded
):
    earlier = review_files.round_directory(18)
    review(earlier, "zh")
    review(earlier, "en")
    disposed = root / "notes/dispositions.json"
    disposed.parent.mkdir()
    disposed.write_bytes(encoded(json.dumps({"round": 18, "findings": {}})))
    refused = refusal("--previous", earlier, "--dispositions", disposed)
    assert refused.startswith("prepare: notes/dispositions.json is not JSON: ")
    assert ready == []
    assert not review_files.round_directory(ROUND).exists()


def test_a_dispositions_file_that_is_missing_is_said_as_missing_by_the_reader_itself(root, review):
    # The command refuses a missing file before it reads; the reader, asked by itself, says the
    # same and does not word a missing file as one that is no JSON.
    earlier = review_files.round_directory(18)
    review(earlier, "zh")
    review(earlier, "en")
    with pytest.raises(ReviewError) as refused:
        review_prompts.checked_dispositions(root / "notes/none.json", earlier)
    assert str(refused.value) == "missing notes/none.json"


def lacking_a_report(root, put, previous, monkeypatch):
    (previous[1] / "zh-review.md").unlink()
    return previous, "missing build/evidence/reviews/round-18/zh-review.md"


def note_that_is_no_text(root, put, previous, monkeypatch):
    note = root / "notes/changes.md"
    note.write_bytes("- Repairs: 07.6.\n".encode("utf-16"))
    return (*previous, "--changes", note), "notes/changes.md is not UTF-8 text: "


def unknown_field(root, put, previous, monkeypatch):
    template = review_prompts.TEMPLATE + "{unknown_field} {reviewer.name} {}\n"
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    return previous, (
        "content/review/prompt.md cites {} and {reviewer.name} and {unknown_field}, which the "
        "engine does not fill"
    )


def reshaped_fields(root, put, previous, monkeypatch):
    # A conversion or a format specification would cut or reword what the engine fills a field
    # with: `{register:.0}` leaves no rule and names no report, and `{levels!r}` quotes the levels.
    template = review_prompts.TEMPLATE.replace("{register}", "{register:.0}")
    template = template.replace("{levels}", "{levels!r}").replace("{concepts}", "{concepts!s:>9}")
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    return previous, (
        "content/review/prompt.md cites {concepts!s:>9} and {levels!r} and {register:.0}, each "
        "with a conversion or a format specification; the engine fills a field that is cited "
        "with neither"
    )


def other_program_level(root, put, previous, monkeypatch):
    put(Edition("en").audio_assembly, {"program_level": {"policy": {"integrated_lufs": -14.0}}})
    return previous, "the soundtracks declare different program levels: [-16.5, -14.0]"


def missing_timeline(root, put, previous, monkeypatch):
    Edition("en").timeline.unlink()
    return previous, "missing build/artifacts/film/en/timeline.json"


def no_register_field(root, put, previous, monkeypatch):
    template = review_prompts.TEMPLATE.replace("{register}", "")
    monkeypatch.setattr(review_prompts, "TEMPLATE", template)
    return previous, (
        "content/review/prompt.md never cites {register}, which names the round's register "
        "report and states the rules of the formal register"
    )


def refused_words(root, put, previous, monkeypatch):
    def refuse():
        line = "zh 01.1: '你们' addresses the audience (R1)"
        raise register.RegisterError(line, advise=True)

    monkeypatch.setattr(register, "check", refuse)
    return previous, "zh 01.1: '你们' addresses the audience (R1) A film keeps a standard word "


def no_pinned_vale(root, put, previous, monkeypatch):
    # The round asks the check itself, which refuses where the Vale it runs is not on the path.
    monkeypatch.setattr(register, "check", REGISTER_CHECK)
    monkeypatch.setenv("PATH", str(root / "no-tools"))
    return previous, "No vale on the path; the register check runs Vale "


@pytest.mark.parametrize(
    "case",
    [
        lacking_a_report,
        note_that_is_no_text,
        unknown_field,
        reshaped_fields,
        other_program_level,
        missing_timeline,
        no_register_field,
        refused_words,
        no_pinned_vale,
    ],
)
def test_every_check_that_only_reads_refuses_in_one_line_before_anything_is_derived(
    root, put, ready, previous, monkeypatch, case
):
    options, named = case(root, put, previous, monkeypatch)
    assert refusal(*options).startswith(f"prepare: {named}")
    assert ready == []
    assert not review_files.round_directory(ROUND).exists()


@pytest.mark.parametrize(
    "refused",
    [
        media.MediaError("Loudness measurement returned no input_i"),
        AlignmentError("03: the aligned words do not cover the text"),
        soundtrack_level.LevelError("K-weighting is declared for 48 kHz audio"),
        sources.SourceError("Source manifest pins no canonical document"),
        tools.ToolError("No node on PATH"),
        PictureError("The renderer is not built"),
        delivery_folder.DeliveryRefusedError("The players fail their readback:\n  zh/index.html"),
    ],
    ids=lambda refused: type(refused).__name__,
)
def test_an_owner_s_refusal_is_the_round_s_refusal_in_one_line(ready, monkeypatch, refused):
    def refuse():
        raise refused

    monkeypatch.setattr(review_measurement, "measure", refuse)
    assert refusal() == "prepare: " + " ".join(str(refused).split())
    assert not list(review_files.round_directory(ROUND).glob("prompt-*.md"))


@pytest.mark.parametrize(
    "fault",
    [
        subprocess.CalledProcessError(1, ["ffmpeg"]),
        FileNotFoundError("build/evidence/editions/zh/ear-first/asr.json"),
        KeyError("tolerance"),
    ],
    ids=lambda fault: type(fault).__name__,
)
def test_a_fault_while_a_round_is_derived_keeps_its_traceback(ready, monkeypatch, fault):
    def fail():
        raise fault

    monkeypatch.setattr(review_measurement, "measure", fail)
    with pytest.raises(type(fault)):
        prepare()


def test_a_round_s_number_is_not_negative(root, ready):
    with pytest.raises(SystemExit) as stopped:
        review_round.main(["prepare", "--round", "-1"])
    assert str(stopped.value) == "prepare: a round's number is 0 or more, not -1"
    assert ready == []
    assert not (root / "build/evidence/reviews/round--1").exists()
