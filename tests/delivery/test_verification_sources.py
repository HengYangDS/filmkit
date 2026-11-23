"""The verifier's set of every declared edition's films."""

import pytest

import filmkit.delivery.verification as delivery_verification
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.verification import VerificationError


def test_acceptance_needs_exactly_every_editions_current_films(tmp_path, monkeypatch):
    monkeypatch.setattr(repository, "ROOT", tmp_path)
    films = [film for code in production.CODES for film in production.Edition(code).films]
    groups = delivery_verification.edition_inputs(list(reversed(films)))
    assert groups == {code: production.Edition(code).films for code in production.CODES}
    for files in (
        films[1:],
        [*films, tmp_path / "build/artifacts/film/zh/extra.mp4"],
        [*films[1:], films[1]],
        [tmp_path / "elsewhere" / film.name for film in films],
    ):
        with pytest.raises(VerificationError, match="requires each one's current films"):
            delivery_verification.edition_inputs(files)
