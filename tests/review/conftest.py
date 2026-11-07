"""Fixtures of the review tool tests: a repository root, a writer of its fixture files and a
writer of a round's reviews."""

import json

import pytest

import filmkit.repository as repository
import filmkit.review.record as review_record
from filmkit.production import CODES, Edition

SCORES = dict.fromkeys(review_record.DIMENSIONS, 96)


def write_fixture(path, data):
    """Write bytes, text or JSON to a fixture file, creating its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    return path


@pytest.fixture
def put():
    """Write bytes, text or JSON to a fixture file, creating its folders: `put(path, data)`."""
    return write_fixture


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A repository root holding both packaged editions as tiny stand-in files: each edition's
    four films, its package record and both pictures."""
    root = tmp_path.resolve()
    monkeypatch.setattr(repository, "ROOT", root)
    for code in CODES:
        edition = Edition(code)
        pictures = (edition.picture, edition.rendered(captions=False).file)
        for path in (*edition.films, edition.film_package, *pictures):
            write_fixture(path, f"{code} {path.name}")
    return root


@pytest.fixture
def review(put):
    """Write one edition's review and report into a round directory."""

    def write(folder, code, *, media=None, findings=(), **edition):
        media = media or [
            {"path": str(film), "sha256": repository.sha(film)} for film in Edition(code).films
        ]
        edition = {
            "media": media,
            "scores": SCORES,
            "overall": 96.0,
            "findings": list(findings),
            "human_listening_checklist": ["Listen to 24.3 in its clause."],
        } | edition
        put(folder / f"review-{code}.json", {"reviewer": "Reviewer", "editions": {code: edition}})
        put(folder / f"{code}-review.md", f"# {code} review\n")

    return write
