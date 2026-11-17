"""The destinations a delivery refuses before it reads a player or runs rsync: an empty name, the
film's root, a folder that holds it or lies inside it, and a populated folder that no delivery
filled. Every film and every folder lies below the test's own folder."""

from pathlib import Path

import pytest

import filmkit.delivery.folder as delivery_folder
import filmkit.repository as repository
from filmkit.delivery.folder import DeliveryRefusedError
from filmkit.film import FILM

NAME = FILM.delivery_folder


def tree(folder: Path) -> dict[str, str]:
    """Every file and link below a folder, with a file's text."""
    return {
        path.relative_to(folder).as_posix(): "a link" if path.is_symlink() else path.read_text()
        for path in sorted(folder.rglob("*"))
        if path.is_file() or path.is_symlink()
    }


@pytest.fixture
def placed(tmp_path, monkeypatch):
    """Place a film whose members are small texts at a root of the test's choosing, with the
    files a checkout holds beside them; reading a player or running any command fails the test."""

    def refuse(*arguments, **options):
        pytest.fail(f"the delivery went on to {arguments[:1]}")

    for name in ("read_players", "run", "rsync_version"):
        monkeypatch.setattr(delivery_folder, name, refuse)

    def place(root: Path) -> Path:
        for source, path in delivery_folder.plan(root):
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(f"current {path}\n")
        for name in (".git/HEAD", "content/film.toml", "src/film.js"):
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(f"the checkout's {name}\n")
        monkeypatch.setattr(repository, "ROOT", root)
        return root

    return place


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A home folder below the test's own, on macOS, on a host that names no delivery root."""
    folder = tmp_path / "home"
    folder.mkdir()
    monkeypatch.setattr(delivery_folder.Path, "home", classmethod(lambda cls: folder))
    monkeypatch.delenv(delivery_folder.ROOT_VARIABLE, raising=False)
    monkeypatch.setattr(delivery_folder.sys, "platform", "darwin")
    return folder


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    ("destination", "found"),
    [
        ("films/film", "it is the film's root"),
        ("films/link to the film", "it is the film's root"),
        ("films/film/build/..", "it is the film's root"),
        ("films", "it holds the film's root, "),
        ("films/film/build/delivered", "it lies inside the film's root, "),
        ("films/film/build/artifacts/film", "it lies inside the film's root, "),
    ],
)
def test_the_films_root_what_holds_it_and_what_lies_inside_it_are_refused(
    placed, tmp_path, destination, found, dry_run
):
    root = placed(tmp_path / "films/film")
    (tmp_path / "films/link to the film").symlink_to(root)
    before = tree(tmp_path)
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(root, tmp_path / destination, dry_run=dry_run, rule="a test")
    said = str(refused.value)
    assert said.startswith(f"The destination {tmp_path / destination}, which a test gave, is")
    assert f"is refused: {found}" in said
    # Nothing was read back, run or written, the delivery's own filter and sums included.
    assert tree(tmp_path) == before


@pytest.mark.parametrize("arguments", [[], ["--dry-run"]])
@pytest.mark.parametrize("empty", ["", "   "])
def test_an_empty_destination_is_refused_and_is_not_the_working_directory(
    placed, tmp_path, monkeypatch, empty, arguments
):
    root = placed(tmp_path / "films/film")
    monkeypatch.chdir(root)
    before = tree(tmp_path)
    with pytest.raises(SystemExit, match="--destination names no folder: its value is empty"):
        delivery_folder.main(["--destination", empty, *arguments])
    assert tree(tmp_path) == before


@pytest.mark.parametrize("arguments", [[], ["--dry-run"]])
def test_each_rule_that_gives_the_films_root_is_refused_by_its_name(
    placed, home, tmp_path, monkeypatch, arguments
):
    # The caller names the working directory, which is the film's root.
    root = placed(tmp_path / "checkouts" / NAME)
    monkeypatch.chdir(root)
    before = tree(tmp_path)
    with pytest.raises(SystemExit, match="which --destination gave, is refused: it is the film"):
        delivery_folder.main(["--destination", ".", *arguments])
    # The host's delivery root is the folder of checkouts, and the film's checkout has the name
    # of its delivery folder.
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, str(tmp_path / "checkouts"))
    with pytest.raises(SystemExit, match="which FILMKIT_DELIVERY_ROOT gave, is refused: it is"):
        delivery_folder.main(arguments)
    assert tree(tmp_path) == before
    # The film is built inside its own delivery folder below the videos folder.
    monkeypatch.delenv(delivery_folder.ROOT_VARIABLE)
    inside = placed(home / "Movies" / NAME / "checkout")
    before = tree(tmp_path)
    videos = r"which the macOS videos folder ~/Movies gave, is refused: it holds the film's root"
    with pytest.raises(SystemExit, match=videos):
        delivery_folder.main(arguments)
    assert tree(tmp_path) == before
    assert inside.is_dir()


@pytest.mark.parametrize("dry_run", [False, True])
def test_a_populated_folder_that_no_delivery_filled_is_not_emptied(placed, tmp_path, dry_run):
    root, destination = placed(tmp_path / "films/film"), tmp_path / "Movies/holiday"
    for name in ("2019/a.mov", "notes.txt", ".DS_Store", ".claude/state.json", "zh/index.html"):
        (destination / name).parent.mkdir(parents=True, exist_ok=True)
        (destination / name).write_text(f"the user's {name}\n")
    before = tree(tmp_path)
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(root, destination, dry_run=dry_run, rule="--destination")
    assert str(refused.value) == (
        f"The destination {destination}, which --destination gave, is refused: it holds 3 "
        "entries (2019, notes.txt, zh) and no index.html of an earlier delivery. A delivery "
        "moves every entry of its destination that is no member into the predecessors, so "
        "nothing is delivered"
    )
    assert tree(tmp_path) == before
    # Many entries are counted, and the first five are named.
    for number in range(6):
        (destination / f"clip-{number}.mov").write_text("a clip\n")
    many = r"holds 9 entries \(2019, clip-0.mov, clip-1.mov, clip-2.mov, clip-3.mov, \.\.\.\)"
    with pytest.raises(DeliveryRefusedError, match=many):
        delivery_folder.deliver(root, destination, dry_run=dry_run)


def test_a_destination_that_is_a_file_is_refused(placed, tmp_path):
    root, destination = placed(tmp_path / "films/film"), tmp_path / "Movies/film"
    destination.parent.mkdir()
    destination.write_text("a file\n")
    with pytest.raises(DeliveryRefusedError, match="is refused: it is no folder"):
        delivery_folder.deliver(root, destination)
    assert destination.read_text() == "a file\n"


@pytest.mark.rsync
def test_an_absent_folder_one_with_the_preserved_entries_alone_and_a_delivered_one_are_filled(
    film,
):
    root, destination = film
    for name in (".DS_Store", ".claude/state.json"):
        film.write(destination / name, "kept\n")
    report = delivery_folder.deliver(root, destination)
    assert report["all_match"]
    # The folder now holds an entry page: what a user put beside the members goes to the
    # predecessors, as before.
    film.write(destination / "notes.txt", "a note\n")
    report = delivery_folder.deliver(root, destination)
    assert film.tree(root / report["predecessors"]) == {"notes.txt": "a note\n"}
    assert film.tree(destination)[".claude/state.json"] == "kept\n"
