"""A rebuild of both editions and the release it is compared with, for the tests of the
reproduction comparison (`test_reproduction.py`) and of the release manifest's rules
(`test_reproduction_manifest.py`); their fixtures stand in `conftest.py`.
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import filmkit.delivery.reproduction as reproduction
import filmkit.picture.rendering as picture_rendering
import filmkit.production as production
import filmkit.repository as repository

# The FFmpeg that encoded the published films, as the record states it, and another.
RECORDED = "ffmpeg version 8.0.1 Copyright (c) 2000-2025 the FFmpeg developers"
ANOTHER = "ffmpeg version 8.1 Copyright (c) 2000-2026 the FFmpeg developers"


def encode(target: Path, picture: str, tone: int, created: str = "2026-10-28T11:29:43Z") -> Path:
    """A six-frame 60 fps film of a test picture and a sine tone, titled and dated like a film."""
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            f"{picture}=s=64x36:r=60",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={tone}:sample_rate=48000",
            "-frames:v",
            "6",
            "-t",
            "0.1",
            "-ac",
            "2",
            "-c:v",
            "libx264",
            "-bf",
            "0",
            "-c:a",
            "aac",
            "-metadata",
            "title=A film",
            "-metadata",
            f"creation_time={created}",
            str(target),
        ],
        check=True,
        capture_output=True,
        timeout=60,
    )
    return target


@dataclass
class Release:
    """A rebuild of both editions below the root and the release it is compared with."""

    root: Path
    films: dict[str, Path]
    # The FFmpeg that runs, as the comparison reads its version.
    running: str = RECORDED

    @property
    def folder(self) -> Path:
        return self.root / reproduction.RELEASE

    def publish(self, name: str, source: Path) -> None:
        """Place a published asset as a copy of a file."""
        self.folder.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, self.folder / name)

    def record(self, floors: float | None = 30.0, *, encoders: bool = True) -> None:
        """Write the release manifest of the published folder, with each published film's floor;
        a release that publishes the films without captions records their stage too. With
        `encoders` it states each film's FFmpeg, `RECORDED`, and each drawn picture's digest as
        its receipt states it; without, it is a record written before they were recorded."""
        editions = {}
        for code in production.CODES:
            edition = production.Edition(code)
            films = [film.name for film in edition.films if (self.folder / film.name).is_file()]
            uncaptioned = edition.rendered(captions=False).page
            editions[code] = {
                "soundtrack_sha256": repository.sha(edition.soundtrack),
                "stage_sha256": repository.sha(edition.rendered().page),
                **(
                    {"uncaptioned_stage_sha256": repository.sha(uncaptioned)}
                    if len(films) == len(edition.films)
                    else {}
                ),
                "picture_floor_db": {} if floors is None else dict.fromkeys(films, floors),
            }
            if encoders:
                editions[code]["ffmpeg"] = dict.fromkeys(films, RECORDED)
                editions[code]["drawn_sha256"] = reproduction.drawn(edition)
        sources = [
            *(production.Edition(code).script for code in production.CODES),
            picture_rendering.COMPOSITION_SCRIPT,
        ]
        assets = [
            {"name": path.name, "bytes": path.stat().st_size, "sha256": repository.sha(path)}
            for path in sorted(self.folder.iterdir())
            if path.name != reproduction.CHECKSUMS
        ]
        manifest = {
            "version": "1.0.0",
            "editions": editions,
            "sources": {str(path): repository.sha(path) for path in sources},
            "assets": assets,
        }
        checksums = reproduction.checksums(reproduction.Release.model_validate(manifest))
        (self.folder / reproduction.CHECKSUMS).write_text(checksums)
        assets.append(
            {
                "name": reproduction.CHECKSUMS,
                "bytes": len(checksums.encode()),
                "sha256": repository.content_sha(checksums),
            }
        )
        (self.root / reproduction.MANIFEST).write_text(json.dumps(manifest))

    def compare(self) -> dict:
        return reproduction.compare()


def drawn_digest(code: str, picture: str) -> str:
    """The drawn-frame digest a stand-in render of an edition's picture states."""
    return repository.content_sha(f"{code} {picture} drawn")


def listing(root: Path) -> list[tuple[Path, int, int]]:
    return [(path, path.stat().st_size, path.stat().st_mtime_ns) for path in root.rglob("*")]


def packaged_anew(release: Release, *codes: str) -> None:
    """Package each film of the editions anew: it holds other bytes than its published film."""
    for code in codes:
        for film in production.Edition(code).films:
            shutil.copyfile(release.films["later"], film)
