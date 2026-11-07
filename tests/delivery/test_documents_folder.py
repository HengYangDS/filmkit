"""Delivery of the Documents folder through rsync, and its readback through shasum."""

import hashlib
import json
from pathlib import Path

import pytest

import filmkit.delivery.documents_folder as delivery_documents_folder
import filmkit.repository as repository
from filmkit.delivery.documents_folder import DeliveryRefusedError
from filmkit.production import CODES


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def members(root: Path) -> list[str]:
    return [path for _, path in delivery_documents_folder.plan(root)]


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
    sources = [source for source, _ in delivery_documents_folder.plan(root)]
    assert sources[0] == root / "build/artifacts/film/index.html"
    assert sources[1] == root / "build/artifacts/film/zh/sample-reel-zh-uhd.mp4"


@pytest.mark.rsync
def test_a_first_delivery_places_and_reads_back_every_member(film):
    root, destination = film
    report = delivery_documents_folder.deliver(root, destination)
    assert len(report["members"]) == 25
    assert report["members"][1] == {
        "path": "zh/sample-reel-zh-uhd.mp4",
        "sha256": sha("current zh/sample-reel-zh-uhd.mp4\n"),
        "bytes": len("current zh/sample-reel-zh-uhd.mp4\n"),
    }
    assert (report["all_match"], report["unexpected"], report["predecessors"]) == (True, [], None)
    # The players were read back from the sources before any of them was placed.
    receipt = root / delivery_documents_folder.PLAYERS
    assert report["players"] == {
        "receipt": str(delivery_documents_folder.PLAYERS),
        "sha256": repository.sha(receipt),
    }
    binding = json.loads((root / delivery_documents_folder.PLAYERS_BINDING).read_text())
    assert binding["destination"] == str(root / "build/artifacts/film")
    assert [m["path"] for m in binding["members"]] == members(root)
    assert report["film"] == {"slug": "sample-reel", "duration": 60}
    assert report["destination"] == str(destination)
    assert json.loads((root / delivery_documents_folder.READBACK).read_text()) == report
    assert film.tree(destination) == {path: f"current {path}\n" for path in members(root)}
    sums = (root / delivery_documents_folder.SUMS).read_text().splitlines()
    assert sums[0] == f"{sha('current index.html' + chr(10))}  index.html"


@pytest.mark.rsync
def test_a_delivery_keeps_what_it_replaces_or_removes_and_the_foreign_entries(film):
    root, destination = film
    delivery_documents_folder.deliver(root, destination)
    film.write(destination / "zh/sample-reel-zh (copy).srt", "copy\n")
    film.write(destination / ".DS_Store", "finder\n")
    film.write(destination / "en/.DS_Store", "finder\n")
    film.write(destination / ".claude/state.json", "{}\n")
    film.better()
    report = delivery_documents_folder.deliver(root, destination)
    assert film.tree(destination) == {
        ".DS_Store": "finder\n",
        ".claude/state.json": "{}\n",
        "en/.DS_Store": "finder\n",
        **{path: f"better {path}\n" for path in members(root)},
    }
    kept = root / report["predecessors"]
    assert kept.is_relative_to(root / delivery_documents_folder.PREDECESSORS)
    assert film.tree(kept) == {
        "zh/sample-reel-zh (copy).srt": "copy\n",
        **{path: f"current {path}\n" for path in members(root)},
    }
    assert report["all_match"]


@pytest.mark.rsync
def test_an_unchanged_delivery_replaces_nothing(film):
    root, destination = film
    delivery_documents_folder.deliver(root, destination)
    report = delivery_documents_folder.deliver(root, destination)
    assert (report["predecessors"], report["changes"]) == (None, [])


@pytest.mark.rsync
def test_a_dry_run_reports_the_changes_and_writes_nothing(film):
    root, destination = film
    report = delivery_documents_folder.deliver(root, destination, dry_run=True)
    assert report["dry_run"]
    assert "zh/sample-reel-zh-uhd.mp4" in "\n".join(report["changes"])
    assert not destination.exists()
    assert not (root / delivery_documents_folder.READBACK).exists()


def test_missing_sources_refuse_before_any_change(film):
    root, destination = film
    (root / "build/artifacts/film/en/chapters.json").unlink()
    with pytest.raises(DeliveryRefusedError, match=r"Missing delivery sources: en/chapters\.json"):
        delivery_documents_folder.deliver(root, destination)
    assert not destination.exists()


@pytest.mark.rsync
def test_the_readback_refuses_a_member_that_differs_at_the_destination(film):
    root, destination = film
    delivery_documents_folder.deliver(root, destination)
    (destination / "en/sample-reel-en.vtt").write_text("WEBVTT\n")
    with pytest.raises(
        DeliveryRefusedError, match=r"differs from its sources: en/sample-reel-en\.vtt"
    ):
        delivery_documents_folder.readback(root, destination)


@pytest.mark.rsync
def test_the_readback_refuses_an_entry_beside_the_members(film):
    root, destination = film
    delivery_documents_folder.deliver(root, destination)
    film.write(destination / "notes.txt", "notes\n")
    with pytest.raises(DeliveryRefusedError, match=r"unexpected entries: notes\.txt"):
        delivery_documents_folder.readback(root, destination)


def test_an_rsync_other_than_rsync_3_is_refused(film, monkeypatch):
    monkeypatch.setattr(delivery_documents_folder, "rsync_version", lambda: "openrsync 2.6.9")
    with pytest.raises(DeliveryRefusedError, match="rsync 3 is required"):
        delivery_documents_folder.deliver(*film)
    assert not film.destination.exists()


@pytest.mark.rsync
def test_the_command_reports_the_readback_summary(film, monkeypatch, capsys):
    monkeypatch.setattr(repository, "ROOT", film.root)
    delivery_documents_folder.main(["--destination", str(film.destination)])
    assert json.loads(capsys.readouterr().out) == {
        "members": 25,
        "all_match": True,
        "predecessors": None,
    }
    film.write(film.root / "build/artifacts/film/index.html", "edited\n")
    delivery_documents_folder.main(["--destination", str(film.destination)])
    summary = json.loads(capsys.readouterr().out)
    assert summary["predecessors"].startswith(str(delivery_documents_folder.PREDECESSORS))
    (film.root / "build/artifacts/film/en/index.html").unlink()
    with pytest.raises(SystemExit, match="Missing delivery sources"):
        delivery_documents_folder.main(["--destination", str(film.destination)])


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

    monkeypatch.setattr(delivery_documents_folder, "check_players", failing)
    monkeypatch.setattr(delivery_documents_folder, "rsync_version", lambda: "rsync  version 3.4.1")
    with pytest.raises(
        DeliveryRefusedError,
        match=r"zh/index\.html: sample-reel-zh\.ass resolves to zh/sample-reel-zh\.ass",
    ):
        delivery_documents_folder.deliver(root, destination)
    assert not destination.exists()
    assert calls == [
        (root / delivery_documents_folder.PLAYERS_BINDING, root / delivery_documents_folder.PLAYERS)
    ]
    # A player check that stops without a receipt refuses too, by its status.
    monkeypatch.setattr(delivery_documents_folder, "check_players", lambda binding, receipt: 2)
    (root / delivery_documents_folder.PLAYERS).unlink()
    with pytest.raises(DeliveryRefusedError, match="The player check exited with status 2"):
        delivery_documents_folder.deliver(root, destination)
    assert not destination.exists()


def test_a_player_check_that_cannot_run_refuses_delivery(film, monkeypatch):
    root, destination = film

    def absent(binding, receipt):
        raise delivery_documents_folder.tools.ToolError("No node on PATH")

    monkeypatch.setattr(delivery_documents_folder, "check_players", absent)
    monkeypatch.setattr(delivery_documents_folder, "rsync_version", lambda: "rsync  version 3.4.1")
    with pytest.raises(DeliveryRefusedError, match="No node on PATH"):
        delivery_documents_folder.deliver(root, destination)
    assert not destination.exists()


def test_a_dry_run_reads_no_player(film, monkeypatch):
    root, destination = film
    monkeypatch.setattr(
        delivery_documents_folder,
        "check_players",
        lambda *_: pytest.fail("a dry run opens no browser"),
    )
    monkeypatch.setattr(delivery_documents_folder, "rsync_version", lambda: "rsync  version 3.4.1")
    completed = delivery_documents_folder.subprocess.CompletedProcess
    monkeypatch.setattr(
        delivery_documents_folder, "run", lambda command, cwd: completed(command, 0, "", "")
    )
    report = delivery_documents_folder.deliver(root, destination, dry_run=True)
    assert report == {"destination": str(destination), "changes": [], "dry_run": True}


def test_the_player_check_runs_the_engines_tool_on_the_binding(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        delivery_documents_folder.tools,
        "run",
        lambda tool, arguments, **_: calls.append((tool, arguments)) or 0,
    )
    binding, receipt = tmp_path / "binding.json", tmp_path / "receipt.json"
    assert delivery_documents_folder.check_players(binding, receipt) == 0
    assert calls == [("player-check", ["players", str(binding), str(receipt)])]
