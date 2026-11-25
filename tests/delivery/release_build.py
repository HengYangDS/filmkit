"""A reviewed, delivered build for the tests of the release's writer.

`Built` is the build the `built` fixture gives (`conftest.py`). The tests of what the writer asks
(`test_release.py`) and of what it builds and stages (`test_release_staging.py`) share it, the
sources they state and the command's one line of refusal.
"""

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import filmkit.delivery.folder as delivery_folder
import filmkit.delivery.release as release
import filmkit.delivery.reproduction as reproduction
import filmkit.film as film
import filmkit.picture.rendering as picture_rendering
import filmkit.repository as repository
from filmkit.production import CODES, Edition

# The film-bound sources a test states: both editions' scripts and the composition's script.
SOURCES = sorted(
    [*(Edition(code).script for code in CODES), str(picture_rendering.COMPOSITION_SCRIPT)]
)
# How the command's refusal of a declared source begins.
DECLARED = "A film-bound source that content/film.toml declares in [release] sources"
# The version of the earlier release whose record a test tracks, unless it names another.
EARLIER_VERSION = "1.2.0"
# The version line each encoder states to a built film's tests, on a host with or without it.
FFMPEG = "ffmpeg version 8.0.1 Copyright (c) 2000-2025 the FFmpeg developers"
ENCODERS = {"FFmpeg": FFMPEG}


@dataclass
class Built:
    """A reviewed build of both editions, each uncaptioned picture derived, which the film's own
    folder below a host's root holds, the version the fixture bound it with, and each stage the
    staging's check was asked for."""

    root: Path
    folder: Path
    editions: dict
    fixture_version: str
    monkeypatch: pytest.MonkeyPatch
    asked: list = field(default_factory=list)

    @property
    def manifest(self) -> Path:
        return self.root / reproduction.MANIFEST

    @property
    def release(self) -> Path:
        return self.root / reproduction.RELEASE

    def deliver(self) -> None:
        """Hold every delivery member in the film's own folder with the build's bytes."""
        for source, path in delivery_folder.plan(self.root):
            (self.folder / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, self.folder / path)

    def tree(self) -> dict[str, bytes | None]:
        """Every file of the film and of the host's root with its bytes, and every folder."""
        return {
            str(path): path.read_bytes() if path.is_file() else None
            for top in (self.root, self.folder.parent)
            for path in sorted(top.rglob("*"))
        }

    def declare(self, sources: list[str]) -> None:
        """Declare the film-bound sources, as the film's `[release] sources` declares them."""
        held = film.FILM.release.model_copy(update={"sources": tuple(sources)})
        self.monkeypatch.setattr(film, "FILM", film.FILM.model_copy(update={"release": held}))

    def version(self, held: str) -> None:
        """Give the film another version, bound as a build of that version binds it."""
        (self.root / "VERSION").write_text(f"{held}\n")
        for inputs in self.editions.values():
            edition = inputs.edition
            inputs.change(edition.viewing_package, "version", value=held)
            bound = repository.sha(self.root / "VERSION")
            inputs.change(edition.film_package, "version_sha256", value=bound)

    def track(
        self,
        *,
        version: str = EARLIER_VERSION,
        floors: dict | None = None,
        sources: list[str] = SOURCES,
        assets: tuple[str, ...] = ("earlier-film.mp4",),
    ) -> None:
        """Track the record of an earlier release as the manifest's model reads one: its floors by
        edition, its sources with digests that have moved since, and its assets by name."""
        floors = floors or {}
        editions = {
            code: {
                "soundtrack_sha256": "1" * 64,
                "stage_sha256": "2" * 64,
                "picture_floor_db": floors.get(code, {}),
            }
            for code in dict.fromkeys([*CODES, *floors])
        }
        record = {
            "version": version,
            "editions": editions,
            "sources": dict.fromkeys(sources, "0" * 64),
            "assets": [{"name": name, "bytes": 1, "sha256": "3" * 64} for name in assets],
        }
        self.manifest.write_text(json.dumps(record))

    def staged(self) -> list[str]:
        """The names of the release folder's entries."""
        return sorted(entry.name for entry in self.release.iterdir())


def refused(arguments: list[str]) -> str:
    """The one line the command refuses with."""
    with pytest.raises(SystemExit) as refusal:
        release.main(arguments)
    line = str(refusal.value)
    assert line
    assert "\n" not in line
    return line


def unchanged_refusal(
    built: Built, arguments: tuple[str, ...] = (), *, sources: list[str] | None = None
) -> str:
    """The command's one line of refusal, no file of the film or of the host's root changed;
    with `sources`, the film declares those as its film-bound sources first."""
    if sources is not None:
        built.declare(sources)
    before = built.tree()
    line = refused(list(arguments))
    assert built.tree() == before
    return line


def uncaptioned_stage(code: str) -> Path:
    return Edition(code).rendered(captions=False).stage
