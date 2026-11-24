"""The supply task: the browser build and model snapshots it installs and checks."""

import json

import pronounced
import pytest

import filmkit.narration.cmudict as cmudict
import filmkit.picture.browser as picture_browser
import filmkit.repository as repository
import filmkit.supply as supply
from filmkit.narration.snapshots import DOWNLOAD_RECORDS, Snapshot
from filmkit.supply import SupplyError


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A repository root whose browser installer and model downloads are stand-ins."""
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    (tmp_path / "node_modules").mkdir()
    monkeypatch.delenv("FILM_CHROMIUM_PATH", raising=False)
    calls = []
    browser = b"browser build"

    def install(command, **_options):
        calls.append(("install", command))
        path = picture_browser.supplied_browser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(browser)

    def download(repo, *, revision, allow_patterns, local_dir):
        calls.append(("download", repo, revision, allow_patterns, local_dir))
        (local_dir / DOWNLOAD_RECORDS).mkdir(parents=True, exist_ok=True)
        (local_dir / "model.safetensors").write_bytes(repo.encode())
        digest = repository.content_sha(repo.encode())
        (local_dir / DOWNLOAD_RECORDS / "model.safetensors.metadata").write_text(
            f"{revision}\n{digest}\n"
        )

    monkeypatch.setattr(repository, "run", install)
    monkeypatch.setattr(supply, "snapshot_download", download)
    monkeypatch.setattr(picture_browser, "BROWSER_SHA256", repository.content_sha(browser))
    snapshots = tuple(
        Snapshot(
            name,
            f"org/{name}",
            "c" * 40,
            ("*.safetensors",),
            f"build/runtime/tool-cache/narration-{name}",
            {"model.safetensors": repository.content_sha(f"org/{name}".encode())},
        )
        for name in ("voice", "recognizer")
    )
    monkeypatch.setattr(supply, "SNAPSHOTS", snapshots)
    served = {"bytes": pronounced.RAW}

    def fetch(url, place, *, deadline):
        calls.append(("dictionary", url, deadline))
        place.write_bytes(served["bytes"])

    monkeypatch.setattr(supply, "fetch", fetch)
    monkeypatch.setattr(cmudict, "SHA256", repository.content_sha(pronounced.RAW))
    monkeypatch.setattr(cmudict, "BYTES", len(pronounced.RAW))
    return tmp_path, calls, served


def test_the_supply_installs_and_checks_the_browser_and_every_model(root, capsys):
    folder, calls, _ = root
    supply.main([])
    product, version = picture_browser.BROWSER
    install = calls[0][1]
    assert install[0] == str(folder / "node_modules/.bin/browsers")
    assert install[1:] == [
        "install",
        f"{product}@{version}",
        "--path",
        str(folder / "build/runtime/tool-cache/browsers"),
    ]
    # The dictionary is placed before the models.
    assert calls[1] == ("dictionary", cmudict.URL, supply.DEADLINE)
    assert [call[1:4] for call in calls[2:]] == [
        ("org/voice", "c" * 40, ["*.safetensors"]),
        ("org/recognizer", "c" * 40, ["*.safetensors"]),
    ]
    report = json.loads(capsys.readouterr().out)
    assert report["browser"]["build"] == f"{product}@{version}"
    assert report["dictionary"] == {
        "url": cmudict.URL,
        "file": cmudict.PLACE,
        "bytes": len(pronounced.RAW),
        "sha256": cmudict.SHA256,
        "kept": False,
    }
    assert [model["repo"] for model in report["models"]] == ["org/voice", "org/recognizer"]
    assert (folder / cmudict.PLACE).read_bytes() == pronounced.RAW


def test_a_download_of_other_bytes_is_refused_and_leaves_nothing_in_the_place(root):
    folder, calls, served = root
    served["bytes"] = pronounced.RAW + b"zebra Z IY1 B R AH0\n"
    with pytest.raises(SupplyError, match="differs from the pinned SHA-256"):
        supply.main([])
    assert not (folder / cmudict.PLACE).exists()
    assert list((folder / cmudict.PLACE).parent.iterdir()) == []
    # Nothing after the dictionary is supplied.
    assert [call[0] for call in calls] == ["install", "dictionary"]


def test_a_file_in_place_that_holds_the_pin_is_kept_without_a_download(root, capsys):
    folder, calls, _ = root
    place = folder / cmudict.PLACE
    place.parent.mkdir(parents=True)
    place.write_bytes(pronounced.RAW)
    supply.main([])
    assert "dictionary" not in [call[0] for call in calls]
    assert json.loads(capsys.readouterr().out)["dictionary"]["kept"] is True


def test_a_file_in_place_of_other_bytes_is_replaced_by_the_pinned_one(root):
    folder, calls, _ = root
    place = folder / cmudict.PLACE
    place.parent.mkdir(parents=True)
    place.write_bytes(b"an older file\n")
    supply.main([])
    assert "dictionary" in [call[0] for call in calls]
    assert place.read_bytes() == pronounced.RAW


@pytest.mark.usefixtures("root")
def test_a_browser_build_of_other_bytes_is_refused(monkeypatch):
    monkeypatch.setattr(picture_browser, "BROWSER_SHA256", "0" * 64)
    with pytest.raises(SupplyError, match="browser build differs from the pinned SHA-256"):
        supply.main([])


def test_a_download_that_fails_is_refused_in_one_line_that_names_the_file(root, monkeypatch):
    folder, calls, _ = root

    def unreachable(url, place, *, deadline):
        raise OSError("[Errno 8] nodename nor servname provided, or not known")

    monkeypatch.setattr(supply, "fetch", unreachable)
    with pytest.raises(SupplyError) as refusal:
        supply.main([])
    said = str(refusal.value)
    assert "\n" not in said and cmudict.URL in said and cmudict.PLACE in said
    assert said.endswith("nodename nor servname provided, or not known")
    assert not list((folder / cmudict.PLACE).parent.iterdir())
