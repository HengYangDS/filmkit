"""The verifier's films are verified at the same time, reported in order and refused as in
sequence, and the reproduction's film pairs likewise."""

import threading
from pathlib import Path

import pytest

import filmkit.delivery.reproduction as reproduction
import filmkit.delivery.verification as delivery_verification
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.verification import VerificationError


@pytest.fixture
def edition(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path.resolve())
    return production.Edition("zh")


def renditions(edition):
    return {edition.film(kind).name: value for kind, value in production.RENDITIONS.items()}


def test_four_films_are_verified_at_the_same_time_and_reported_in_the_order_given(
    edition, monkeypatch
):
    barrier = threading.Barrier(4, timeout=20)

    def verify(_edition, path, rendition):
        # Each film waits here until all four have started: in sequence this would time out.
        barrier.wait()
        return {"path": path.name, "height": rendition.height}

    monkeypatch.setattr(delivery_verification, "verify_media", verify)
    files = sorted(edition.films)
    report = delivery_verification.verify_films(edition, files, renditions(edition))
    assert [film["path"] for film in report["media"]] == [path.name for path in files]
    assert [*report["media_seconds"]] == [path.name for path in files]
    assert all(seconds >= 0 for seconds in report["media_seconds"].values())


def test_the_first_refused_film_in_the_order_given_refuses(edition, monkeypatch):
    files = sorted(edition.films)

    def verify(_edition, path, _rendition):
        if path in files[1:3]:
            message = f"Movie differs from the delivery contract: {path.name}"
            raise VerificationError(message)
        return {"path": path.name}

    monkeypatch.setattr(delivery_verification, "verify_media", verify)
    with pytest.raises(VerificationError, match=files[1].name):
        delivery_verification.verify_films(edition, files, renditions(edition))


def test_film_pairs_are_compared_two_at_a_time_and_reported_in_the_order_given(monkeypatch):
    barrier = threading.Barrier(reproduction.PAIR_POOL, timeout=20)

    def film(asset, rebuilt, published, floor):
        barrier.wait()
        return {"asset": asset.name, "floor": floor}

    monkeypatch.setattr(reproduction, "film", film)
    assets = [reproduction.Asset(name=f"film-{n}.mp4", bytes=1, sha256="0" * 64) for n in range(4)]
    places = (Path("rebuilt"), Path("published"))
    pairs = [(asset, *places, 30.0 + n) for n, asset in enumerate(assets)]
    report = reproduction.compare_films(pairs)
    assert report["films"] == [{"asset": f"film-{n}.mp4", "floor": 30.0 + n} for n in range(4)]
    assert [*report["film_seconds"]] == [asset.name for asset in assets]
    assert reproduction.compare_films([]) == {"films": [], "film_seconds": {}}
