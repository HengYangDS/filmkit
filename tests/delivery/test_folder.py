"""Delivery of the film's folder through rsync, and its readback through shasum."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from still_records import REQUIRE_FILM_SCAN

import filmkit.delivery.folder as delivery_folder
import filmkit.picture.still_scan as still_scan
import filmkit.repository as repository
from filmkit.delivery.folder import DeliveryRefusedError
from filmkit.picture.errors import PictureError
from filmkit.production import CODES


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def members(root: Path) -> list[str]:
    return [path for _, path in delivery_folder.plan(root)]


def test_the_delivery_members_are_the_entry_page_then_each_editions_films_and_viewing_package():
    root = Path("/root")
    assert members(root) == [
        "index.html",
        *(
            f"{code}/{name}"
            for code in CODES
            for name in (
                f"sample-reel-{code}-uhd.mp4",
                f"sample-reel-{code}-1080p-captioned.mp4",
                f"sample-reel-{code}-uhd-uncaptioned.mp4",
                f"sample-reel-{code}-1080p-uncaptioned.mp4",
                "sample-reel-cover.png",
                "sample-reel-cover.jpg",
                f"sample-reel-{code}.srt",
                f"sample-reel-{code}.vtt",
                f"sample-reel-{code}-transcript.md",
                "chapters.json",
                "chapters.ffmeta",
                "index.html",
            )
        ),
    ]
    sources = [source for source, _ in delivery_folder.plan(root)]
    assert sources[0] == root / "build/artifacts/film/index.html"
    assert sources[1] == root / "build/artifacts/film/zh/sample-reel-zh-uhd.mp4"


@pytest.mark.rsync
def test_a_first_delivery_places_and_reads_back_every_member(film):
    root, destination = film
    report = delivery_folder.deliver(root, destination)
    assert len(report["members"]) == 25
    assert report["members"][1] == {
        "path": "zh/sample-reel-zh-uhd.mp4",
        "sha256": sha("current zh/sample-reel-zh-uhd.mp4\n"),
        "bytes": len("current zh/sample-reel-zh-uhd.mp4\n"),
    }
    assert (report["all_match"], report["unexpected"], report["predecessors"]) == (True, [], None)
    # The players were read back from the sources before any of them was placed.
    receipt = root / delivery_folder.PLAYERS
    assert report["players"] == {
        "receipt": str(delivery_folder.PLAYERS),
        "sha256": repository.sha(receipt),
    }
    binding = json.loads((root / delivery_folder.PLAYERS_BINDING).read_text())
    assert binding["destination"] == str(root / "build/artifacts/film")
    assert [m["path"] for m in binding["members"]] == members(root)
    assert report["film"] == {"slug": "sample-reel", "runtimes": {"zh": 1636, "en": 1476}}
    assert report["destination"] == str(destination)
    assert json.loads((root / delivery_folder.READBACK).read_text()) == report
    assert film.tree(destination) == {path: f"current {path}\n" for path in members(root)}
    sums = (root / delivery_folder.SUMS).read_text().splitlines()
    assert sums[0] == f"{sha('current index.html' + chr(10))}  index.html"


@pytest.mark.rsync
def test_a_delivery_keeps_what_it_replaces_or_removes_and_the_foreign_entries(film):
    root, destination = film
    delivery_folder.deliver(root, destination)
    film.write(destination / "zh/sample-reel-zh (copy).srt", "copy\n")
    film.write(destination / ".DS_Store", "finder\n")
    film.write(destination / "en/.DS_Store", "finder\n")
    film.write(destination / ".claude/state.json", "{}\n")
    film.better()
    report = delivery_folder.deliver(root, destination)
    assert film.tree(destination) == {
        ".DS_Store": "finder\n",
        ".claude/state.json": "{}\n",
        "en/.DS_Store": "finder\n",
        **{path: f"better {path}\n" for path in members(root)},
    }
    kept = root / report["predecessors"]
    assert kept.is_relative_to(root / delivery_folder.PREDECESSORS)
    assert film.tree(kept) == {
        "zh/sample-reel-zh (copy).srt": "copy\n",
        **{path: f"current {path}\n" for path in members(root)},
    }
    assert report["all_match"]


@pytest.mark.rsync
def test_an_unchanged_delivery_replaces_nothing(film):
    root, destination = film
    delivery_folder.deliver(root, destination)
    report = delivery_folder.deliver(root, destination)
    assert (report["predecessors"], report["changes"]) == (None, [])


@pytest.mark.rsync
def test_a_dry_run_reports_the_changes_and_writes_nothing(film):
    root, destination = film
    report = delivery_folder.deliver(root, destination, dry_run=True)
    assert report["dry_run"]
    assert "zh/sample-reel-zh-uhd.mp4" in "\n".join(report["changes"])
    assert not destination.exists()
    assert not (root / delivery_folder.READBACK).exists()


@pytest.mark.parametrize("dry_run", [False, True])
def test_an_edition_whose_film_holds_no_passing_still_scan_is_not_delivered(
    film, monkeypatch, dry_run
):
    # Delivery asks the scan's own requirement of each edition before rsync changes anything, in
    # a dry run too, whether or not a task ran the verifier first: `package-film` and then this
    # command would otherwise deliver a film that was never scanned.
    root, destination = film
    monkeypatch.setattr(repository, "ROOT", root)
    monkeypatch.setattr(still_scan, "require_film_scan", REQUIRE_FILM_SCAN)
    monkeypatch.setattr(delivery_folder, "run", lambda *_: pytest.fail("the delivery ran rsync"))
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(root, destination, dry_run=dry_run)
    assert str(refused.value) == "The zh film has no still scan record; run scan-film"
    assert not destination.exists()


def test_an_edition_without_a_timeline_is_refused_in_one_line_before_rsync(film, monkeypatch):
    # The player check's binding names each edition's runtime, which only its timeline states:
    # the command refuses in the one line of the runtime's reading, before rsync changes anything.
    root, destination = film
    (root / "build/artifacts/film/en/timeline.json").unlink()
    monkeypatch.setattr(delivery_folder, "rsync_version", lambda: delivery_folder.RSYNC_3 + "4.1")
    monkeypatch.setattr(delivery_folder, "run", lambda *_: pytest.fail("the delivery ran rsync"))
    with pytest.raises(SystemExit) as refused:
        delivery_folder.main(["--destination", str(destination)])
    assert str(refused.value) == (
        "The en edition has no timeline at build/artifacts/film/en/timeline.json, so no runtime: "
        "run produce assemble --language en"
    )
    assert not destination.exists()


def test_the_delivery_asks_the_scan_of_every_edition(film, monkeypatch):
    # Asking the first edition alone would deliver the second unscanned.
    root, destination = film
    asked = []

    def require(edition):
        asked.append(edition.code)
        if edition.code == CODES[-1]:
            msg = f"The {edition.code} film has no still scan record; run scan-film"
            raise PictureError(msg)

    monkeypatch.setattr(still_scan, "require_film_scan", require)
    monkeypatch.setattr(delivery_folder, "run", lambda *_: pytest.fail("the delivery ran rsync"))
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(root, destination)
    assert asked == list(CODES)
    assert str(refused.value) == f"The {CODES[-1]} film has no still scan record; run scan-film"
    assert not destination.exists()


def test_a_root_that_is_not_the_film_the_command_runs_in_is_refused(film, tmp_path, monkeypatch):
    # The scan's requirement reads the records of the film the command runs in: the members of
    # another root would be delivered on that film's scans.
    root, destination = film
    elsewhere = tmp_path / "another-film"
    shutil.copytree(root, elsewhere)
    monkeypatch.setattr(delivery_folder, "run", lambda *_: pytest.fail("the delivery ran rsync"))
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(elsewhere, destination, dry_run=True)
    assert str(refused.value) == (
        f"The delivery reads the still scans of the film at {root}, not {elsewhere}"
    )
    assert not destination.exists()


def test_missing_sources_refuse_before_any_change(film):
    root, destination = film
    (root / "build/artifacts/film/en/chapters.json").unlink()
    with pytest.raises(DeliveryRefusedError, match=r"Missing delivery sources: en/chapters\.json"):
        delivery_folder.deliver(root, destination)
    assert not destination.exists()


@pytest.mark.rsync
def test_the_readback_refuses_a_member_that_differs_at_the_destination(film):
    root, destination = film
    delivery_folder.deliver(root, destination)
    (destination / "en/sample-reel-en.vtt").write_text("WEBVTT\n")
    with pytest.raises(
        DeliveryRefusedError, match=r"differs from its sources: en/sample-reel-en\.vtt"
    ):
        delivery_folder.readback(root, destination)


@pytest.mark.rsync
def test_the_readback_refuses_an_entry_beside_the_members(film):
    root, destination = film
    delivery_folder.deliver(root, destination)
    film.write(destination / "notes.txt", "notes\n")
    with pytest.raises(DeliveryRefusedError, match=r"unexpected entries: notes\.txt"):
        delivery_folder.readback(root, destination)


def test_an_rsync_other_than_rsync_3_is_refused(film, monkeypatch):
    monkeypatch.setattr(delivery_folder, "rsync_version", lambda: "openrsync 2.6.9")
    with pytest.raises(DeliveryRefusedError, match="rsync 3 is required"):
        delivery_folder.deliver(*film)
    assert not film.destination.exists()


@pytest.mark.rsync
def test_the_command_reports_the_readback_summary(film, monkeypatch, capsys):
    monkeypatch.setattr(repository, "ROOT", film.root)
    delivery_folder.main(["--destination", str(film.destination)])
    assert json.loads(capsys.readouterr().out) == {
        "members": 25,
        "destination": str(film.destination.resolve()),
        "destination_rule": "--destination",
        "all_match": True,
        "predecessors": None,
    }
    film.write(film.root / "build/artifacts/film/index.html", "edited\n")
    delivery_folder.main(["--destination", str(film.destination)])
    summary = json.loads(capsys.readouterr().out)
    assert summary["predecessors"].startswith(str(delivery_folder.PREDECESSORS))
    (film.root / "build/artifacts/film/en/index.html").unlink()
    with pytest.raises(SystemExit, match="Missing delivery sources"):
        delivery_folder.main(["--destination", str(film.destination)])


def test_a_player_that_fails_its_readback_refuses_delivery_before_any_change(film, monkeypatch):
    root, destination = film
    calls = []

    def failing(binding, receipt):
        calls.append((binding, receipt))
        problem = "sample-reel-zh.ass resolves to zh/sample-reel-zh.ass, which is no member"
        pages = [
            {"page": "index.html", "verdict": "pass", "problems": []},
            {"page": "zh/index.html", "verdict": "fail", "problems": [problem]},
        ]
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({"pass": False, "pages": pages}))
        return 1

    monkeypatch.setattr(delivery_folder, "check_players", failing)
    monkeypatch.setattr(delivery_folder, "rsync_version", lambda: "rsync  version 3.4.1")
    with pytest.raises(
        DeliveryRefusedError,
        match=r"zh/index\.html: sample-reel-zh\.ass resolves to zh/sample-reel-zh\.ass",
    ):
        delivery_folder.deliver(root, destination)
    assert not destination.exists()
    assert calls == [(root / delivery_folder.PLAYERS_BINDING, root / delivery_folder.PLAYERS)]
    # A player check that stops without a receipt refuses too, by its status.
    monkeypatch.setattr(delivery_folder, "check_players", lambda binding, receipt: 2)
    (root / delivery_folder.PLAYERS).unlink()
    with pytest.raises(DeliveryRefusedError, match="The player check exited with status 2"):
        delivery_folder.deliver(root, destination)
    assert not destination.exists()


def test_a_player_check_that_cannot_run_refuses_delivery(film, monkeypatch):
    root, destination = film

    def absent(binding, receipt):
        raise delivery_folder.tools.ToolError("No node on PATH")

    monkeypatch.setattr(delivery_folder, "check_players", absent)
    monkeypatch.setattr(delivery_folder, "rsync_version", lambda: "rsync  version 3.4.1")
    with pytest.raises(DeliveryRefusedError, match="No node on PATH"):
        delivery_folder.deliver(root, destination)
    assert not destination.exists()


def test_a_dry_run_reads_no_player(film, monkeypatch):
    root, destination = film
    monkeypatch.setattr(
        delivery_folder,
        "check_players",
        lambda *_: pytest.fail("a dry run opens no browser"),
    )
    monkeypatch.setattr(delivery_folder, "rsync_version", lambda: "rsync  version 3.4.1")
    completed = delivery_folder.subprocess.CompletedProcess
    monkeypatch.setattr(delivery_folder, "run", lambda command, cwd: completed(command, 0, "", ""))
    report = delivery_folder.deliver(root, destination, dry_run=True)
    place = {"destination": str(destination), "destination_rule": "--destination"}
    assert report == {**place, "changes": [], "dry_run": True}


def test_the_player_check_runs_the_engines_tool_on_the_binding(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        delivery_folder.tools,
        "run",
        lambda tool, arguments, **_: calls.append((tool, arguments)) or 0,
    )
    binding, receipt = tmp_path / "binding.json", tmp_path / "receipt.json"
    assert delivery_folder.check_players(binding, receipt) == 0
    assert calls == [("player-check", ["players", str(binding), str(receipt)])]


def test_the_players_readback_lies_where_a_delivery_keeps_it_or_where_it_is_told(film, monkeypatch):
    root, _ = film

    def pictured(binding, receipt):
        """Stand in for the player check: every page passes, and one screenshot a player lies
        beside the receipt, as the check writes them."""
        shots = [receipt.with_name(f"player-{code}.png") for code in CODES]
        for shot in shots:
            film.write(shot, f"{shot.name} of {binding.name}\n")
        named = [{"path": str(shot), "sha256": repository.sha(shot)} for shot in shots]
        film.write(receipt, json.dumps({"pass": True, "pages": [], "screenshots": named}))
        return 0

    monkeypatch.setattr(delivery_folder, "check_players", pictured)
    plan = delivery_folder.plan(root)
    # A delivery's readback lies where it does today: the binding in the delivery's work folder,
    # the receipt and the screenshots beside it in the delivery's evidence.
    receipt = root / delivery_folder.PLAYERS
    assert delivery_folder.read_players(root, plan) == {
        "receipt": str(delivery_folder.PLAYERS),
        "sha256": repository.sha(receipt),
    }
    evidence = "build/evidence/delivery"
    kept = {
        "build/runtime/work/delivery/players.json",
        *(f"{evidence}/{name}" for name in ("player-check.json", "player-en.png", "player-zh.png")),
    }
    sources = {source.relative_to(root).as_posix() for source, _ in plan}
    # Beside the members' sources stand the editions' timelines, which state their runtimes.
    timelines = {f"build/artifacts/film/{code}/timeline.json" for code in ("zh", "en")}
    assert set(film.tree(root)) == sources | kept | timelines
    delivered = film.tree(root)
    # A readback into another folder, as a review round asks for its own, writes the binding, the
    # receipt and the screenshots there and changes nothing of the delivery's.
    folder = root / "build/evidence/reviews/round-3"
    binding, receipt = folder / "player-check-artifacts.json", folder / "player-check.json"
    bound = delivery_folder.bind_players(root, plan, binding)
    assert delivery_folder.read_bound_players(root, bound, receipt) == {
        "receipt": "build/evidence/reviews/round-3/player-check.json",
        "sha256": repository.sha(receipt),
    }
    assert sorted(path.name for path in folder.iterdir()) == [
        "player-check-artifacts.json",
        "player-check.json",
        "player-en.png",
        "player-zh.png",
    ]
    assert json.loads(binding.read_text()) == json.loads(
        (root / delivery_folder.PLAYERS_BINDING).read_text()
    )
    assert [shot["path"] for shot in json.loads(receipt.read_text())["screenshots"]] == [
        str(folder / f"player-{code}.png") for code in CODES
    ]
    assert {path: text for path, text in film.tree(root).items() if path in delivered} == delivered


def test_a_folder_is_compared_with_the_builds_members_and_each_that_differs_is_named(film):
    root, destination = film
    plan = delivery_folder.plan(root)
    # A folder that does not exist holds no member.
    absent = delivery_folder.differing_members(root, destination)
    assert absent == {path: "is missing" for _, path in plan}
    for source, path in plan:
        film.write(destination / path, source.read_text())
    assert delivery_folder.differing_members(root, destination) == {}
    # An entry beside the members is not the comparison's to name.
    film.write(destination / "notes.txt", "notes\n")
    film.write(destination / ".DS_Store", "finder\n")
    assert delivery_folder.differing_members(root, destination) == {}
    (destination / "zh/sample-reel-zh.srt").unlink()
    film.write(destination / "en/sample-reel-en-uhd.mp4", "an earlier build\n")
    # Other bytes of the same length differ too.
    film.write(destination / "en/chapters.json", "CURRENT en/chapters.json\n")
    assert delivery_folder.differing_members(root, destination) == {
        "zh/sample-reel-zh.srt": "is missing",
        "en/sample-reel-en-uhd.mp4": "holds other bytes",
        "en/chapters.json": "holds other bytes",
    }
    # The comparison reads: the folder and the build hold what they held, the editions'
    # timelines beside the members' sources.
    held = film.tree(root)
    assert {name: held[name] for name in held if not name.endswith("/timeline.json")} == {
        source.relative_to(root).as_posix(): f"current {path}\n" for source, path in plan
    }
    assert (destination / "notes.txt").read_text() == "notes\n"
    # A member's place that holds a folder is named as no file, not as missing.
    (destination / "zh/sample-reel-zh.vtt").unlink()
    (destination / "zh/sample-reel-zh.vtt").mkdir()
    assert delivery_folder.differing_members(root, destination)["zh/sample-reel-zh.vtt"] == (
        "is no file"
    )
    # A member the build itself no longer holds is named as that, whatever the folder holds.
    (root / "build/artifacts/film/index.html").unlink()
    assert delivery_folder.differing_members(root, destination)["index.html"] == (
        "has no file in the build"
    )
