"""Where a delivery goes: the folder named, the host's delivery root, or the user's videos folder,
and what the delivery records of it. No test touches a real home folder."""

import json

import pytest

import filmkit.delivery.folder as delivery_folder
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.graph import cli

NAME = FILM.delivery_folder

# The build verifies: the delivery is asked of the folder alone (`delivered`).
pytestmark = pytest.mark.usefixtures("verified_build")


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A home folder below the test's own, on a host that names no delivery root."""
    folder = tmp_path / "home"
    folder.mkdir()
    monkeypatch.setattr(delivery_folder.Path, "home", classmethod(lambda cls: folder))
    for variable in (delivery_folder.ROOT_VARIABLE, delivery_folder.XDG_VIDEOS, "XDG_CONFIG_HOME"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(delivery_folder.sys, "platform", "darwin")
    return folder


def test_a_named_folder_is_the_destination_itself(home, tmp_path, monkeypatch):
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, str(tmp_path / "films"))
    named = tmp_path / "anywhere" / "at all"
    assert delivery_folder.delivery_destination(named) == (named.resolve(), "--to")


def test_the_hosts_delivery_root_holds_the_films_declared_folder(home, tmp_path, monkeypatch):
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, str(tmp_path / "films"))
    assert delivery_folder.delivery_destination() == (
        (tmp_path / "films" / NAME).resolve(),
        "FILMKIT_DELIVERY_ROOT",
    )


def test_on_macos_the_destination_lies_in_the_users_movies_folder(home):
    folder, rule = delivery_folder.delivery_destination()
    assert folder == (home / "Movies" / NAME).resolve()
    assert rule == "the macOS videos folder ~/Movies"
    assert "Documents" not in folder.parts


def test_elsewhere_the_xdg_videos_directory_is_read_in_its_order(home, tmp_path, monkeypatch):
    monkeypatch.setattr(delivery_folder.sys, "platform", "linux")
    # Nothing names it: the XDG default.
    assert delivery_folder.delivery_destination() == (
        (home / "Videos" / NAME).resolve(),
        "the XDG default videos folder ~/Videos",
    )
    # The user's directories file names it, the home folder written as $HOME.
    listed = home / ".config/user-dirs.dirs"
    listed.parent.mkdir()
    listed.write_text('XDG_MUSIC_DIR="$HOME/Musik"\n# a comment\nXDG_VIDEOS_DIR="$HOME/Filme"\n')
    folder, rule = delivery_folder.delivery_destination()
    assert folder == (home / "Filme" / NAME).resolve()
    assert rule == f"XDG_VIDEOS_DIR in {listed}"
    # XDG_CONFIG_HOME names where that file lies.
    other = tmp_path / "xdg"
    other.mkdir()
    (other / "user-dirs.dirs").write_text(f'XDG_VIDEOS_DIR="{tmp_path}/shared videos"\n')
    monkeypatch.setenv("XDG_CONFIG_HOME", str(other))
    shared = (tmp_path / "shared videos" / NAME).resolve()
    assert delivery_folder.delivery_destination()[0] == shared
    # The environment's own XDG_VIDEOS_DIR comes before the file.
    monkeypatch.setenv(delivery_folder.XDG_VIDEOS, str(tmp_path / "from the environment"))
    assert delivery_folder.delivery_destination() == (
        (tmp_path / "from the environment" / NAME).resolve(),
        "XDG_VIDEOS_DIR in the environment",
    )


@pytest.fixture
def listed(home, monkeypatch):
    """The user's directories file on a host that is not macOS, to be written by the test."""
    monkeypatch.setattr(delivery_folder.sys, "platform", "linux")
    file = home / ".config/user-dirs.dirs"
    file.parent.mkdir()
    return file


@pytest.mark.parametrize(
    ("line", "folder"),
    [
        ('XDG_VIDEOS_DIR="$HOME/Filme"', "{home}/Filme"),
        ('XDG_VIDEOS_DIR="${{HOME}}/Filme"', "{home}/Filme"),
        ('XDG_VIDEOS_DIR="$HOME"', "{home}"),
        ("XDG_VIDEOS_DIR='$HOME/Filme'", "{home}/Filme"),
        ('XDG_VIDEOS_DIR="/srv/films"', "/srv/films"),
        ("XDG_VIDEOS_DIR='/srv/our films'", "/srv/our films"),
        ('XDG_VIDEOS_DIR="$HOME/Filme"  # where the films go', "{home}/Filme"),
        ('  XDG_VIDEOS_DIR = "$HOME/Filme"\t#x', "{home}/Filme"),
        (r'''XDG_VIDEOS_DIR="$HOME/My \"Films\" \$1"''', '{home}/My "Films" $1'),
        ('XDG_VIDEOS_DIR="$HOME/Alt"\nXDG_VIDEOS_DIR="$HOME/Neu"', "{home}/Neu"),
        ('# XDG_VIDEOS_DIR="/commented"\nXDG_VIDEOS_DIR="$HOME/Filme"', "{home}/Filme"),
    ],
)
def test_the_videos_line_is_read_as_xdg_user_dirs_writes_it(home, listed, line, folder):
    listed.write_text(f'XDG_MUSIC_DIR="$HOME/Musik"\n{line.format(home=home)}\n')
    found, rule = delivery_folder.delivery_destination()
    assert found == (delivery_folder.Path(folder.format(home=home)) / NAME).resolve()
    assert rule == f"XDG_VIDEOS_DIR in {listed}"


@pytest.mark.parametrize(
    "line",
    [
        'XDG_VIDEOS_DIR="Filme"',
        'XDG_VIDEOS_DIR="./Filme"',
        'XDG_VIDEOS_DIR="~/Filme"',
        'XDG_VIDEOS_DIR="$HOMER/Filme"',
        'XDG_VIDEOS_DIR="$XDG_DATA_HOME/Filme"',
        "XDG_VIDEOS_DIR=$HOME/Filme",
        'XDG_VIDEOS_DIR="$HOME/Filme',
        'XDG_VIDEOS_DIR="$HOME/Filme" and more',
        'export XDG_VIDEOS_DIR="$HOME/Filme"',
        'XDG_VIDEOS_DIR=""',
        "XDG_VIDEOS_DIR=",
    ],
)
def test_a_videos_line_that_names_no_absolute_folder_is_not_used_and_the_rule_says_so(
    home, listed, line
):
    # An earlier line that is usable does not count: the last one is what a shell would hold.
    listed.write_text(f'XDG_VIDEOS_DIR="$HOME/Filme"\n{line}\n')
    found, rule = delivery_folder.delivery_destination()
    assert found == (home / "Videos" / NAME).resolve()
    assert rule == (
        "the XDG default videos folder ~/Videos, since the XDG_VIDEOS_DIR line of "
        f"{listed} is not usable ({line})"
    )


def test_a_relative_folder_in_the_environment_is_not_used_either(home, listed, monkeypatch):
    monkeypatch.setenv(delivery_folder.XDG_VIDEOS, "films")
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/config")
    listed.write_text('XDG_VIDEOS_DIR="$HOME/Filme"\n')
    # The file below ~/.config is read, since the configuration folder named is relative too.
    assert delivery_folder.delivery_destination() == (
        (home / "Filme" / NAME).resolve(),
        f"XDG_VIDEOS_DIR in {listed}",
    )
    listed.write_text('XDG_VIDEOS_DIR="Filme"\n')
    found, rule = delivery_folder.delivery_destination()
    assert found == (home / "Videos" / NAME).resolve()
    assert rule == (
        "the XDG default videos folder ~/Videos, since XDG_VIDEOS_DIR in the environment is no "
        f"absolute path (films) and the XDG_VIDEOS_DIR line of {listed} is not usable "
        '(XDG_VIDEOS_DIR="Filme")'
    )


@pytest.mark.rsync
def test_a_delivery_records_its_destination_and_the_rule_that_gave_it(
    film, home, monkeypatch, capsys
):
    monkeypatch.setattr(repository, "ROOT", film.root)
    # Without a named folder and with no root of the host's: the user's videos folder.
    cli.main(["deliver"])
    videos = (home / "Movies" / NAME).resolve()
    summary = json.loads(capsys.readouterr().out)
    assert (summary["destination"], summary["destination_rule"]) == (
        str(videos),
        "the macOS videos folder ~/Movies",
    )
    assert (videos / "index.html").is_file()
    record = repository.read(film.root / delivery_folder.READBACK)
    assert (record["destination"], record["destination_rule"]) == (
        str(videos),
        "the macOS videos folder ~/Movies",
    )
    # A host's root, in a dry run, which writes nothing there.
    monkeypatch.setenv(delivery_folder.ROOT_VARIABLE, str(film.root.parent / "films"))
    cli.main(["deliver", "--dry-run"])
    planned = json.loads(capsys.readouterr().out)
    assert planned["destination"] == str((film.root.parent / "films" / NAME).resolve())
    assert (planned["destination_rule"], planned["dry_run"]) == ("FILMKIT_DELIVERY_ROOT", True)
    assert not (film.root.parent / "films").exists()
    # A folder named by the caller.
    cli.main(["deliver", "--to", str(film.destination)])
    assert json.loads(capsys.readouterr().out)["destination_rule"] == "--to"
    assert repository.read(film.root / delivery_folder.READBACK)["destination"] == str(
        film.destination.resolve()
    )
