"""Fixtures of the review tool tests: a repository root, a writer of its fixture files, a writer
of a round's reviews, and for the tests of a round's preparation a build that is ready and the
round before it."""

import json

import pytest

import filmkit.delivery.folder as delivery_folder
import filmkit.repository as repository
import filmkit.review.files as review_files
import filmkit.review.listening_plan as review_listening_plan
import filmkit.review.measurement as review_measurement
import filmkit.review.prompts as review_prompts
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


@pytest.fixture
def ready(root, put, monkeypatch):
    """A build that is ready for round 19: every delivery member and the records the prompts
    and the sentences read, with stand-ins for the listening plan, the measurement and the
    player check. Returns each step that ran with the names the round held when it began."""
    from preparing import ROUND, names, passing_players
    from test_levels import timeline_of
    from test_prompts import round_inputs

    round_inputs(root, put, monkeypatch)
    for source, path in delivery_folder.plan(root):
        if not source.is_file():
            put(source, f"{path}\n")
    for code in CODES:
        put(Edition(code).timeline, timeline_of(code))
    folder, began = review_files.round_directory(ROUND), []

    def step(name, run):
        def recorded(*arguments):
            began.append((name, names(folder)))
            return run(*arguments)

        return recorded

    plan = step("listening plan", lambda out: put(out, {"status": "planned-not-listened"}))
    measure = step("measurements", lambda: {"scope": "stand-in", "editions": {}})
    monkeypatch.setattr(review_listening_plan, "listening_plan", plan)
    monkeypatch.setattr(review_measurement, "measure", measure)
    monkeypatch.setattr(delivery_folder, "check_players", step("readback", passing_players))
    monkeypatch.setattr(review_prompts, "prompts", step("prompts", review_prompts.prompts))
    return began


@pytest.fixture
def previous(review, put, root):
    """Round 18 with one finding, and the options that name it with its dispositions."""
    folder = review_files.round_directory(18)
    review(folder, "zh", findings=[{"id": "R18-1", "severity": "note"}])
    review(folder, "en")
    fixed = {"disposition": "fixed", "evidence": "The card names all seven checks."}
    disposed = put(root / "notes/dispositions.json", {"round": 18, "findings": {"R18-1": fixed}})
    return ("--previous", folder, "--dispositions", disposed)
