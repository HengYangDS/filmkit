"""The render's worker count: eight, or a count named for a measurement, and recorded."""

import os

import pytest

import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.picture.rendering import PictureError
from filmkit.production import Edition


@pytest.mark.parametrize("cores", [4, 8, 10, 18, 32, None])
def test_the_count_is_eight_on_every_host(monkeypatch, cores):
    monkeypatch.delenv(picture_rendering.WORKERS_VARIABLE, raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: cores)
    assert picture_rendering.render_workers() == picture_rendering.WORKERS == 8
    command = picture_rendering.renderer_command(repository.ROOT, repository.ROOT, 60, "looks")
    assert command[command.index("--workers") + 1] == "8"


def test_a_named_count_is_passed_as_it_is(monkeypatch):
    monkeypatch.setattr(os, "cpu_count", lambda: 18)
    monkeypatch.setenv(picture_rendering.WORKERS_VARIABLE, "12")
    assert picture_rendering.render_workers() == 12
    command = picture_rendering.renderer_command(repository.ROOT, repository.ROOT, 60, "looks")
    assert command[command.index("--workers") + 1] == "12"


@pytest.mark.parametrize("named", ["many", "0", "-4", "3.5", "１２"])
def test_a_value_that_is_no_count_is_refused_by_the_variable(monkeypatch, named):
    monkeypatch.setenv(picture_rendering.WORKERS_VARIABLE, named)
    with pytest.raises(PictureError, match="FILMKIT_RENDER_WORKERS names"):
        picture_rendering.render_workers()


def test_an_empty_variable_is_read_as_unset(monkeypatch):
    monkeypatch.setattr(os, "cpu_count", lambda: 18)
    monkeypatch.setenv(picture_rendering.WORKERS_VARIABLE, "")
    assert picture_rendering.render_workers() == 8


def test_the_receipt_records_the_count_its_command_passes(film_root, monkeypatch):
    monkeypatch.setenv(picture_rendering.WORKERS_VARIABLE, "12")
    edition = Edition("zh")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    receipt = repository.read(edition.render_receipt)
    assert receipt["workers"] == 12
    assert receipt["command"][receipt["command"].index("--workers") + 1] == "12"


def test_a_command_without_a_worker_count_records_none():
    assert picture_rendering.command_workers(["hyperframes", "render", "stage"]) is None


@pytest.mark.parametrize(("named", "recorded"), [(None, "on"), ("off", "off")])
def test_the_receipt_records_the_renderers_lock(film_root, monkeypatch, named, recorded):
    if named is None:
        monkeypatch.delenv(picture_rendering.RENDER_LOCK, raising=False)
    else:
        monkeypatch.setenv(picture_rendering.RENDER_LOCK, named)
    edition = Edition("en")
    film_root.staged(edition)
    picture_rendering.render_picture(edition, 60)
    assert repository.read(edition.render_receipt)["render_lock"] == recorded
