"""Exercise a second preparation of a review round: a round is prepared again only while it
holds nothing but a preparation."""

import json
from functools import partial

from preparing import PREPARED, ROUND, names, passing_players, prepare, refusal, tree

import filmkit.delivery.folder as delivery_folder
import filmkit.repository as repository
import filmkit.review.measurement as review_measurement
import filmkit.review.round as review_round
import filmkit.review.set_aside as review_set_aside
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError

PURPOSE = "superseded by its repairs"


def test_a_round_that_holds_anything_but_a_preparation_is_refused_by_name(put, ready):
    folder = prepare()
    # A review, a reviewer's working folder and a file of unknown origin, each alone.
    for entry in ("review-zh.json", "zh/frames.txt", "facts.json"):
        put(folder / entry, "kept")
        before = tree(folder)
        assert refusal() == (
            f"prepare: {PREPARED} holds {entry.split('/')[0]}, which a preparation does not "
            "write; a round is prepared again only while it holds nothing else"
        )
        assert tree(folder) == before
        (folder / entry).unlink()
        if "/" in entry:
            (folder / entry).parent.rmdir()
    # Finder's file is no entry, as in a delivery: it refuses nothing and stays.
    put(folder / ".DS_Store", "finder")
    prepare()
    assert (folder / ".DS_Store").read_text() == "finder"


def test_a_round_whose_films_were_set_aside_is_refused_naming_the_next(root, put, ready):
    folder = prepare()
    built = {
        path: path.read_bytes()
        for edition in map(Edition, CODES)
        for path in (
            *edition.films,
            edition.film_package,
            *review_set_aside.built_pictures(edition),
        )
    }
    consumer = root / "Movies/preview"
    for code in CODES:
        for film in Edition(code).films:
            put(consumer / code / film.name, built[film])
    aside = ["set-aside", "--unreviewed", "--consumer", str(consumer), "--purpose", PURPOSE]

    def rebuilt(*label):
        """Set the build aside under a label, and build it again."""
        review_round.main([*aside, *label])
        for path, body in built.items():
            put(path, body)

    # Set aside under a label of its own, the round keeps its number and is prepared again.
    rebuilt("--label", "preview-1")
    prepare()
    # Set aside under the round's label, the label is taken: the films are the next round's.
    rebuilt("--round", str(ROUND))
    before = tree(folder)
    assert refusal() == (
        "prepare: the films of round 19 were set aside under its label, "
        "build/artifacts/film/superseded/round-19; prepare round 20"
    )
    assert tree(folder) == before


def test_a_second_preparation_replaces_every_file_of_the_first(root, put, ready, previous):
    changes = put(root / "notes/changes.md", "- Repairs: 07.6 names all seven checks.\n")
    folder = prepare(*previous, "--changes", changes)
    first = names(folder)
    # A corrected note, the films as they stood: no file of the first preparation remains. The
    # readback stays one, marked, and lists its screenshots with the bytes they now hold, since
    # the screenshots it lists by their bytes are the preparation's.
    receipt = folder / "player-check.json"
    read = json.loads(receipt.read_text())
    for path in folder.iterdir():
        path.write_text("first")
    shots = [shot | {"sha256": repository.sha(shot["path"])} for shot in read["screenshots"]]
    put(receipt, read | {"first": True, "screenshots": shots})
    put(changes, "- Repairs: 07.6 names all eight checks.\n")
    prepare(*previous, "--changes", changes)
    assert names(folder) == first
    assert b"first" not in tree(folder).values()
    assert "first" not in json.loads(receipt.read_text())
    prompt = folder / "prompt-zh.md"
    assert "all eight checks" in prompt.read_text()
    assert "seven checks.\n- Pause" not in prompt.read_text()
    # The round's own copies, corrected and named as the sources, are read before they are removed.
    own = put(folder / "changes.md", "- Repairs: 07.6 names all nine checks.\n")
    kept = (folder / "dispositions.json").read_bytes()
    prepare(*previous[:3], folder / "dispositions.json", "--changes", own)
    assert own.read_text() == "- Repairs: 07.6 names all nine checks.\n"
    assert (folder / "dispositions.json").read_bytes() == kept
    assert "all nine checks" in prompt.read_text()
    # Prepared again without its note, the round holds none and the prompts state none; without
    # its previous round it holds no dispositions either: every file a preparation can write
    # went, whether this run writes it or not.
    prepare(*previous)
    assert "changes.md" not in names(folder)
    assert "Repairs" not in prompt.read_text()
    prepare()
    assert "dispositions.json" not in names(folder)
    assert "Dispositions of round" not in prompt.read_text()


def test_a_second_preparation_that_stops_keeps_the_round_s_own_note_and_dispositions(
    put, ready, previous, monkeypatch
):
    folder = prepare(*previous, "--changes", put(previous[3].with_name("changes.md"), "- First.\n"))
    # The author corrects the round's own copies, which then exist nowhere else.
    note = put(folder / "changes.md", "- Corrected in the round.\n").read_bytes()
    disposed = (folder / "dispositions.json").read_bytes()

    def unbound():
        message = "zh: the picture gate record is not bound to the current timeline"
        raise ReviewError(message)

    monkeypatch.setattr(review_measurement, "measure", unbound)
    own = (*previous[:3], folder / "dispositions.json", "--changes", folder / "changes.md")
    assert refusal(*own) == (
        "prepare: zh: the picture gate record is not bound to the current timeline"
    )
    assert (folder / "changes.md").read_bytes() == note
    assert (folder / "dispositions.json").read_bytes() == disposed
    assert not list(folder.glob("prompt-*.md"))


def test_an_entry_that_bears_a_prepared_name_and_is_no_file_is_refused_by_name(ready):
    folder = prepare()
    (folder / "prompt-zh.md").unlink()
    (folder / "prompt-zh.md").mkdir()
    before = names(folder), tree(folder)
    assert refusal() == (
        f"prepare: {PREPARED} holds prompt-zh.md, which a preparation does not write; a round "
        "is prepared again only while it holds nothing else"
    )
    assert (names(folder), tree(folder)) == before


def test_the_screenshots_a_readback_lists_are_the_preparation_s_whatever_their_names(
    ready, monkeypatch
):
    # The receipt is the one statement of what the check wrote beside it; the round states no
    # screenshot's name of its own, so a check that names its screenshots otherwise changes nothing.
    monkeypatch.setattr(
        delivery_folder, "check_players", partial(passing_players, name="shot-{code}.png")
    )
    folder = prepare()
    assert {"shot-en.png", "shot-zh.png"} < set(names(folder))
    monkeypatch.setattr(
        delivery_folder, "check_players", partial(passing_players, name="frame-{code}.png")
    )
    prepare()
    assert [name for name in names(folder) if name.endswith(".png")] == [
        "frame-en.png",
        "frame-zh.png",
    ]


def test_an_image_the_readback_does_not_list_is_refused_by_name(root, put, ready):
    folder = prepare()
    receipt = folder / "player-check.json"
    read = json.loads(receipt.read_text())
    # The readback lists the first player's screenshot in the round, and the second player's in
    # another folder: the second image in the round is no file of the preparation's.
    elsewhere = {"path": str(root / "elsewhere/player-en.png"), "sha256": "0" * 64}
    put(receipt, read | {"screenshots": [read["screenshots"][0], elsewhere]})
    before = tree(folder)
    assert refusal() == (
        f"prepare: {PREPARED} holds player-en.png, which a preparation does not write; a round "
        "is prepared again only while it holds nothing else"
    )
    assert tree(folder) == before


def test_a_round_whose_readback_is_no_json_and_holds_no_image_is_prepared_again(put, ready):
    folder = prepare()
    first = names(folder)
    # A readback that is no JSON lists nothing: an image beside it is no file of a preparation's.
    put(folder / "player-check.json", "{")
    assert refusal() == (
        f"prepare: {PREPARED} holds player-en.png, player-zh.png, which a preparation does not "
        "write; a round is prepared again only while it holds nothing else"
    )
    for code in CODES:
        (folder / f"player-{code}.png").unlink()
    prepare()
    assert names(folder) == first
    assert json.loads((folder / "player-check.json").read_text())["pass"] is True


def test_a_listed_screenshot_that_holds_other_bytes_is_refused_by_name(put, ready):
    folder = prepare()
    # The readback lists the screenshot with the bytes the check wrote; the file now holds others.
    put(folder / "player-zh.png", "painted over")
    before = tree(folder)
    assert refusal() == (
        f"prepare: {PREPARED} holds player-zh.png, which a preparation does not write; a round "
        "is prepared again only while it holds nothing else"
    )
    assert tree(folder) == before


def test_a_readback_that_lists_a_review_deletes_nothing(put, ready):
    folder = prepare()
    receipt = folder / "player-check.json"
    read = json.loads(receipt.read_text())
    # By hand or by fault, the readback lists a review of the round in a screenshot's place,
    # under that screenshot's SHA-256.
    review = put(folder / "review-zh.json", "a review")
    listed = [read["screenshots"][0] | {"path": str(review)}, read["screenshots"][1]]
    put(receipt, read | {"screenshots": listed})
    before = tree(folder)
    assert refusal() == (
        f"prepare: {PREPARED} holds player-zh.png, review-zh.json, which a preparation does not "
        "write; a round is prepared again only while it holds nothing else"
    )
    assert tree(folder) == before


def test_a_readback_that_lists_a_folder_of_the_round_is_refused_by_name(put, ready):
    folder = prepare()
    receipt = folder / "player-check.json"
    read = json.loads(receipt.read_text())
    # The readback lists a folder of the round in a screenshot's place: no file a check wrote.
    (folder / "zh").mkdir()
    listed = [read["screenshots"][0] | {"path": str(folder / "zh")}, read["screenshots"][1]]
    put(receipt, read | {"screenshots": listed})
    before = names(folder), tree(folder)
    assert refusal() == (
        f"prepare: {PREPARED} holds player-zh.png, zh, which a preparation does not write; a round "
        "is prepared again only while it holds nothing else"
    )
    assert (names(folder), tree(folder)) == before
