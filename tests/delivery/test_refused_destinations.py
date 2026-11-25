"""The destinations a delivery refuses before it reads a player or runs rsync: an empty name, the
film's root, a folder that holds it or lies inside it, however the path is spelled, a root of
the host's that is no absolute path, and a populated folder that no delivery filled. Every film
and every folder lies below the test's own folder."""

from pathlib import Path

import pytest

import filmkit.delivery.folder as delivery_folder
import filmkit.repository as repository
from filmkit.delivery.folder import DeliveryRefusedError
from filmkit.film import FILM
from filmkit.graph import cli

NAME = FILM.delivery_folder

# The build verifies: the delivery is asked of the folder alone (`delivered`).
pytestmark = pytest.mark.usefixtures("verified_build")


def tree(folder: Path) -> dict[str, str]:
    """Every file and link below a folder, with a file's text."""
    return {
        path.relative_to(folder).as_posix(): "a link" if path.is_symlink() else path.read_text()
        for path in sorted(folder.rglob("*"))
        if path.is_file() or path.is_symlink()
    }


@pytest.fixture
def placed(tmp_path, monkeypatch, passing_scans):
    """Place a film whose members are small texts at a root of the test's choosing, with the
    files a checkout holds beside them; reading a player or running any command fails the test.
    Each edition's film passes its still scan, so a destination's refusal is what is read."""

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


@pytest.fixture
def folds_case(tmp_path):
    """Skip where the test's volume keeps letter case apart, so no folder has two spellings."""
    (tmp_path / "probe").write_text("a probe\n")
    if not (tmp_path / "PROBE").exists():
        pytest.skip("the volume does not fold case")
    (tmp_path / "probe").unlink()


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    ("destination", "found"),
    [
        ("films/FILM", "it is the film's root"),
        ("FILMS/Film/build/..", "it is the film's root"),
        ("FILMS", "it holds the film's root, "),
        ("films/FILM/build/delivered", "it lies inside the film's root, "),
        ("films/Film/Build/Artifacts/Film", "it lies inside the film's root, "),
        ("films/FILM/not yet/there", "it lies inside the film's root, "),
    ],
)
def test_the_films_own_tree_in_another_letter_case_is_refused(
    placed, folds_case, tmp_path, destination, found, dry_run
):
    # The members' own source folder holds an index.html, so in another case only the rule of
    # the root keeps a delivery from emptying it.
    root = placed(tmp_path / "films/film")
    assert (root / "build/artifacts/film/index.html").is_file()
    before = tree(tmp_path)
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(root, tmp_path / destination, dry_run=dry_run, rule="a test")
    assert f"is refused: {found}" in str(refused.value)
    assert tree(tmp_path) == before


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    ("destination", "found"),
    [
        ("link to the films", "it holds the film's root, "),
        ("link to the films/film", "it is the film's root"),
        ("link to the films/film/build/delivered", "it lies inside the film's root, "),
        ("link to the build/delivered", "it lies inside the film's root, "),
    ],
)
def test_the_films_own_tree_through_a_link_above_it_is_refused(
    placed, tmp_path, destination, found, dry_run
):
    root = placed(tmp_path / "films/film")
    (tmp_path / "link to the films").symlink_to(tmp_path / "films")
    (tmp_path / "link to the build").symlink_to(root / "build")
    before = tree(tmp_path)
    with pytest.raises(DeliveryRefusedError) as refused:
        delivery_folder.deliver(root, tmp_path / destination, dry_run=dry_run, rule="a test")
    assert f"is refused: {found}" in str(refused.value)
    assert tree(tmp_path) == before


def test_one_folder_is_one_folder_however_its_path_is_spelled(tmp_path, monkeypatch):
    folder = tmp_path / "films/film"
    folder.mkdir(parents=True)
    (tmp_path / "link").symlink_to(folder)
    assert delivery_folder.same_folder(folder, tmp_path / "link")
    assert delivery_folder.same_folder(tmp_path / "absent", tmp_path / "absent")
    assert not delivery_folder.same_folder(tmp_path / "absent", tmp_path / "other")
    assert not delivery_folder.same_folder(folder, tmp_path / "films")
    # A second path to one volume, as macOS's data volume gives every folder: the operating
    # system's answer is taken, whatever the two spellings are.
    asked = []
    monkeypatch.setattr(
        delivery_folder.os.path, "samefile", lambda one, other: asked.append((one, other)) or True
    )
    data = Path("/System/Volumes/Data") / folder.relative_to("/")
    assert delivery_folder.same_folder(data, folder)
    assert asked == [(data, folder)]


@pytest.mark.parametrize("arguments", [[], ["--dry-run"]])
@pytest.mark.parametrize("named", ["deliveries", "./deliveries", "  ", "\t"])
def test_a_hosts_root_that_is_no_absolute_path_is_refused_by_its_name(
    placed, home, tmp_path, monkeypatch, named, arguments
):
    placed(tmp_path / "films/film")
    (tmp_path / "elsewhere").mkdir()
    monkeypatch.chdir(tmp_path / "elsewhere")
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, named)
    before = tree(tmp_path)
    with pytest.raises(SystemExit) as refused:
        cli.main(["deliver", *arguments])
    assert str(refused.value).startswith(
        f"FILMKIT_DELIVERY_ROOT names no absolute path ({named!r}): "
    )
    assert tree(tmp_path) == before


def test_a_hosts_root_below_the_home_folder_and_an_empty_one_are_read_as_before(home, monkeypatch):
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, "~/films")
    folder, rule = delivery_folder.delivery_destination()
    assert (folder, rule) == ((home / "films" / NAME).resolve(), "FILMKIT_DELIVERY_ROOT")
    # An empty value is an unset variable: the platform's videos folder.
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, "")
    folder, rule = delivery_folder.delivery_destination()
    assert folder == (home / "Movies" / NAME).resolve()
    assert rule == "the macOS videos folder ~/Movies"


@pytest.mark.parametrize("arguments", [[], ["--dry-run"]])
@pytest.mark.parametrize("empty", ["", "   "])
def test_an_empty_destination_is_refused_and_is_not_the_working_directory(
    placed, tmp_path, monkeypatch, empty, arguments
):
    root = placed(tmp_path / "films/film")
    monkeypatch.chdir(root)
    before = tree(tmp_path)
    with pytest.raises(SystemExit, match="--to names no folder: its value is empty"):
        cli.main(["deliver", "--to", empty, *arguments])
    assert tree(tmp_path) == before


@pytest.mark.parametrize("arguments", [[], ["--dry-run"]])
def test_each_rule_that_gives_the_films_root_is_refused_by_its_name(
    placed, home, tmp_path, monkeypatch, arguments
):
    # The caller names the working directory, which is the film's root.
    root = placed(tmp_path / "checkouts" / NAME)
    monkeypatch.chdir(root)
    before = tree(tmp_path)
    with pytest.raises(SystemExit, match="which --to gave, is refused: it is the film"):
        cli.main(["deliver", "--to", ".", *arguments])
    # The host's delivery root is the folder of checkouts, and the film's checkout has the name
    # of its delivery folder.
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, str(tmp_path / "checkouts"))
    with pytest.raises(SystemExit, match="which FILMKIT_DELIVERY_ROOT gave, is refused: it is"):
        cli.main(["deliver", *arguments])
    assert tree(tmp_path) == before
    # The film is built inside its own delivery folder below the videos folder.
    monkeypatch.delenv(delivery_folder.ROOT_VARIABLE)
    inside = placed(home / "Movies" / NAME / "checkout")
    before = tree(tmp_path)
    videos = r"which the macOS videos folder ~/Movies gave, is refused: it holds the film's root"
    with pytest.raises(SystemExit, match=videos):
        cli.main(["deliver", *arguments])
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
        delivery_folder.deliver(root, destination, dry_run=dry_run, rule="--to")
    assert str(refused.value) == (
        f"The destination {destination}, which --to gave, is refused: it holds 3 "
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
