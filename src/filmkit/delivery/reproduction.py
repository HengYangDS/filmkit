"""Compare a rebuild with the published release under the reproduction standard.

The published assets lie in build/artifacts/release under the names that the release manifest
release.json, at the film's root, records with each asset's size and SHA-256; an asset that
differs from the manifest, or a film-bound source that differs from the bytes the manifest
records, refuses the comparison before any layer is compared. Each edition's soundtrack and
staged picture documents must hold the bytes the manifest records, its captions, transcript and
cover the published bytes, and its published review must bind the published films and the
current script and composition. Each rebuilt film that the release publishes must have its published
film's frame count, decoded audio, streams, chapters and tags, and every decoded frame's PSNR
against it at or above the floor that the manifest records. Without a floor the comparison
reports the lowest frames, so that they can be inspected and the floor recorded, and does not
pass. A rebuilt film that holds its published film's size and SHA-256 decodes as it does: the
comparison decodes neither, reports an identical file whose every layer holds and whose PSNR
is not measured, and, without a floor, still does not pass, for such a film calibrates none.

The manifest states the FFmpeg that encoded each film and the drawn-frame digest of each UHD
picture the renderer drew (design decision 13 of build-a-film-by-its-verbs). A film rebuilt by
another FFmpeg, or whose record states none, is compared before encoding where FFmpeg encodes:
its audio through the soundtrack's recorded bytes, and its picture through the drawn-frame
digest of the UHD picture it carries or is encoded from, where the renderer drew that picture
for the release and for the rebuild; a derived picture, and any picture of a record without an
encoder, by decoded frames against the floor. The report names both encoders for each film.

A release publishes either all four films of each edition, with the uncaptioned picture's stage
document recorded beside the captioned one's, or, published before the films without captions
existed, only each edition's two films with captions; the comparison then lists the rebuilt
uncaptioned films as unpublished and compares the rest.

`filmkit.delivery.release` writes the manifest and stages the published assets. The rules `load`
holds a manifest to are also asked of a record that is not yet written (`check`), so that the
writer asks them before it changes a file.

`filmkit verify --release` compares after the records and writes nothing (`compared`, `judge`);
each edition's comparison is measured as a run (`filmkit.graph.runs`), which writes nothing of
its own. A comparison that does not pass refuses with "<edition>: <asset>: <layer>" for each
failing layer.
"""

from __future__ import annotations

import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, NonNegativeInt, PositiveFloat, StringConstraints, ValidationError

import filmkit.child_processes as child_processes
import filmkit.delivery.packaging as packaging
import filmkit.delivery.verification as verification
import filmkit.graph.runs as seam
import filmkit.media as media
import filmkit.production as production
import filmkit.repository as repository
from filmkit.delivery.player import COVER
from filmkit.film import Declared

MANIFEST = Path(repository.RELEASE_RECORD)
RELEASE = Path("build/artifacts/release")
CHECKSUMS = "SHA256SUMS"
# Seconds one decode of a film pair may take.
DECODE_DEADLINE = 7200
# How many of the lowest frames a film's comparison reports.
LOWEST = 10
# How many film pairs are compared at the same time: each pair is two complete decodes.
PAIR_POOL = 2
# The container tags that name the encoder or the time a film was packaged, not the film.
PACKAGING_TAGS = ("encoder", "creation_time", "com.apple.quicktime.creationdate")

Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
AssetName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]
# A release's version as the manifest states it: three numbers, with no pre-release.
Version = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]
# A tracked file's path below the root, each of its names an asset name.
SourcePath = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*$")
]


class ReproductionError(ValueError):
    """The release manifest or a published asset differs from what the comparison requires."""


class Asset(Declared):
    """A published asset: its name in the release and its exact bytes."""

    name: AssetName
    bytes: NonNegativeInt
    sha256: Digest


# The first line `ffmpeg -version` prints, which names the encoder's version.
EncoderVersion = Annotated[str, StringConstraints(min_length=1, pattern=r"^\S")]


class EditionRecord(Declared):
    """What an edition's published films were made from, and each film's PSNR floor.

    `ffmpeg` states, for each published film, the FFmpeg that encoded it, and `drawn_sha256`
    each of the edition's UHD pictures that the renderer drew by its drawn-frame digest; a
    picture derived from another is drawn by none and has none. A record written before the
    release that added them states neither, and its films are of an unknown encoder.
    """

    soundtrack_sha256: Digest
    stage_sha256: Digest
    uncaptioned_stage_sha256: Digest | None = None
    picture_floor_db: dict[AssetName, PositiveFloat] = Field(default_factory=dict)
    ffmpeg: dict[AssetName, EncoderVersion] = Field(default_factory=dict)
    drawn_sha256: dict[Literal["captioned", "uncaptioned"], Digest] = Field(default_factory=dict)


class Release(Declared):
    """The release manifest: its version, editions' records, film-bound sources and assets."""

    version: Version
    editions: dict[str, EditionRecord]
    # Each tracked file that no formatter rewrites and whose exact bytes the build of the
    # published films reads, with its SHA-256.
    sources: dict[SourcePath, Digest] = Field(min_length=1)
    assets: tuple[Asset, ...] = Field(min_length=1)


def release_name(edition: production.Edition, path: Path) -> str:
    """The name a release publishes an edition's file under where the file's own name does not
    tell the editions apart, as its review record and report and its cover: the edition's prefix,
    then that name."""
    return f"{edition.prefix}-{path.name}"


def members(
    edition: production.Edition, *, uncaptioned: bool = True
) -> dict[str, tuple[str, Path]]:
    """Each asset an edition publishes, by its release name: its layer and the build file.

    With `uncaptioned` False they are those of a release published before the films without
    captions existed, which holds only the films with captions.
    """
    review = edition.production_review
    report = production.review_report(review)
    films = [
        edition.film(kind)
        for kind, rendition in production.RENDITIONS.items()
        if uncaptioned or rendition.captions
    ]
    return {
        **{film.name: ("film", film) for film in films},
        **{
            document.name: ("document", document)
            for document in (edition.srt, edition.vtt, edition.transcript)
        },
        release_name(edition, Path(COVER)): ("document", edition.artifacts / packaging.COVER_PNG),
        release_name(edition, review): ("review", review),
        release_name(edition, report): ("review", report),
    }


def checksums(release: Release) -> str:
    """The release's SHA256SUMS: every other asset's SHA-256 and name, as shasum writes them."""
    listed = sorted((a.name, a.sha256) for a in release.assets if a.name != CHECKSUMS)
    return "".join(f"{digest}  {name}\n" for name, digest in listed)


def check(release: Release) -> Release:
    """A release record, refused unless it records exactly what the editions publish.

    These are the rules `load` holds the manifest to, asked of a record that need not be written
    yet, so that the release's writer (`filmkit.delivery.release`) asks them before it changes a
    file. The record is returned as it was given.
    """
    if set(release.editions) != set(production.CODES):
        missing = [code for code in production.CODES if code not in release.editions]
        others = sorted(set(release.editions) - set(production.CODES))
        named = [f"no record of the {code} edition" for code in missing]
        named += [f"a record of {code}, which the film does not declare" for code in others]
        msg = f"{MANIFEST} records the editions {sorted(release.editions)}: " + "; ".join(named)
        raise ReproductionError(msg)
    names = [asset.name for asset in release.assets]
    choices = {
        uncaptioned: [
            name
            for code in production.CODES
            for name in members(production.Edition(code), uncaptioned=uncaptioned)
        ]
        for uncaptioned in (True, False)
    }
    held = [
        u for u, published in choices.items() if sorted(names) == sorted([*published, CHECKSUMS])
    ]
    if len(set(names)) != len(names) or not held:
        msg = f"{MANIFEST} does not name every published asset of the editions, each once"
        raise ReproductionError(msg)
    if any(
        (record.uncaptioned_stage_sha256 is None) == held[0] for record in release.editions.values()
    ):
        msg = (
            f"{MANIFEST} records the uncaptioned picture's stage exactly when it publishes the "
            "films without captions"
        )
        raise ReproductionError(msg)
    for code, record in release.editions.items():
        films = {film.name for film in production.Edition(code).films} & set(names)
        for said, named in (("a floor", record.picture_floor_db), ("an FFmpeg", record.ffmpeg)):
            if not set(named) <= films:
                msg = f"{MANIFEST} records {said} for an asset that is not a film of {code}"
                raise ReproductionError(msg)
    listed = next(asset for asset in release.assets if asset.name == CHECKSUMS)
    if listed.sha256 != repository.content_sha(checksums(release)):
        msg = f"{MANIFEST}: {CHECKSUMS} differs from the assets it lists"
        raise ReproductionError(msg)
    return release


def load() -> Release:
    """The release manifest, refused unless it records exactly what the editions publish."""
    try:
        release = Release.model_validate_json((repository.ROOT / MANIFEST).read_bytes())
    except ValidationError as error:
        msg = f"{MANIFEST} is not a release manifest: {error}"
        raise ReproductionError(msg) from None
    return check(release)


def drawn(edition: production.Edition) -> dict[str, str]:
    """The drawn-frame digest of each of the edition's UHD pictures that the renderer drew, by
    the picture's name, as its render receipt states it. A derived picture's receipt states
    none, nor does a picture without a receipt."""
    found = {}
    for captions in (True, False):
        picture = edition.rendered(captions)
        if picture.receipt.is_file():
            digest = json.loads(picture.receipt.read_text()).get("drawn_sha256")
            if isinstance(digest, str):
                found[picture.name] = digest
    return found


def running_ffmpeg() -> str:
    """The first line of the running FFmpeg's `ffmpeg -version`; a missing tool where none runs."""
    version = seam.encoder("FFmpeg")
    if version == seam.ABSENT:
        raise child_processes.absent("ffmpeg")
    return version


def changed_sources(release: Release) -> list[str]:
    """Each film-bound source whose tracked bytes differ from those the manifest records."""
    return [
        path
        for path, digest in release.sources.items()
        if not (repository.ROOT / path).is_file() or repository.sha(path) != digest
    ]


def published(release: Release) -> dict[str, Path]:
    """Each published asset, refused unless it holds the bytes the manifest records.

    A comparison may then take an asset's recorded size and SHA-256 for its file's.
    """
    folder, found = repository.ROOT / RELEASE, {}
    for asset in release.assets:
        path = folder / asset.name
        if (
            not path.is_file()
            or path.stat().st_size != asset.bytes
            or repository.sha(path) != asset.sha256
        ):
            msg = f"The published asset differs from the release manifest: {asset.name}"
            raise ReproductionError(msg)
        found[asset.name] = path
    return found


def recorded(path: Path, digest: str) -> dict:
    """A rebuilt file that must hold recorded bytes."""
    current = repository.sha(path) if path.is_file() else None
    return {
        "path": repository.relative(path),
        "sha256": current,
        "verdict": "pass" if current == digest else "fail",
    }


def identical(name: str, rebuilt: Path, published: Path) -> dict:
    """A rebuilt document that must hold its published asset's bytes."""
    same = rebuilt.is_file() and repository.sha(rebuilt) == repository.sha(published)
    return {"asset": name, "verdict": "pass" if same else "fail"}


def review(edition: production.Edition, assets: dict[str, Path]) -> dict:
    """The edition's published review, which must bind its published films and sources."""
    films = [assets[film.name] for film in edition.films if film.name in assets]
    record = assets[release_name(edition, edition.production_review)]
    try:
        accepted = verification.verify_review(edition, films, record=record)
    except verification.VerificationError as error:
        return {"verdict": "fail", "reason": str(error)}
    return {"verdict": "pass", **accepted}


def decoded_audio(path: Path) -> str:
    """The SHA-256 of a film's first audio stream, decoded."""
    hashed = repository.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-f",
            "hash",
            "-hash",
            "sha256",
            "-",
        ],
        timeout=DECODE_DEADLINE,
    ).stdout.decode()
    return hashed.strip().removeprefix("SHA256=")


def container(path: Path) -> dict:
    """A film's streams, duration, chapters and tags, apart from its packaging labels."""
    data = media.probe(path)
    keys = ("codec_type", "codec_name", "width", "height", "sample_rate", "channels", "nb_frames")
    return {
        "streams": [
            {key: stream.get(key) for key in keys}
            | {
                "cover": bool(stream.get("disposition", {}).get("attached_pic")),
                "tags": {
                    key: value
                    for key, value in stream.get("tags", {}).items()
                    if key in ("language", "handler_name")
                },
            }
            for stream in data["streams"]
        ],
        "duration": data["format"].get("duration"),
        "chapters": [
            (chapter["start_time"], chapter["end_time"], chapter.get("tags", {}).get("title"))
            for chapter in data.get("chapters", [])
        ],
        "tags": {
            key: value
            for key, value in data["format"].get("tags", {}).items()
            if key not in PACKAGING_TAGS
        },
    }


@dataclass(frozen=True)
class Encoded:
    """What a film's encoded layers are compared through: the FFmpeg the record states for the
    film (None where it states none) and the one that runs; the edition's soundtrack against its
    recorded bytes; and the drawn-frame digest of the UHD picture the film carries or is encoded
    from, as the record states it and as the rebuilt picture's receipt does."""

    recorded: str | None
    running: str
    soundtrack: bool
    picture: str
    drawn: tuple[str | None, str | None]

    @property
    def same(self) -> bool:
        """Whether the film is rebuilt by the FFmpeg that encoded it, so that its encoded
        layers are compared decoded, as before the encoder was recorded."""
        return self.recorded == self.running

    @property
    def digests(self) -> bool:
        """Whether the picture is compared before encoding: another FFmpeg than the recorded one
        rebuilds it, and the renderer drew it both times, so that each draw states its digest."""
        return self.recorded is not None and not self.same and None not in self.drawn

    def stated(self) -> dict:
        """The encoders and what each encoded layer was compared through, as the report
        states them."""
        audio = "decoded" if self.same else "before encoding: the soundtrack's bytes"
        picture = (
            f"before encoding: the {self.picture} picture's drawn-frame digest"
            if self.digests
            else "decoded frames against the floor"
        )
        return {
            "encoders": {"recorded": self.recorded, "running": self.running},
            "compared": {"audio": audio, "picture": picture},
        }


def unmeasured(floor: float | None) -> dict:
    """A film's PSNR where no frame was decoded."""
    return {
        "floor_db": floor,
        "measured": False,
        "identical_frames": None,
        "minimum_db": None,
        "mean_db": None,
        "lowest": [],
        "below_floor": [],
    }


def measured(psnr: list[float], floor: float | None) -> dict:
    """A film's PSNR from every decoded frame's, against its floor."""
    finite = sorted((value, index) for index, value in enumerate(psnr) if math.isfinite(value))
    return {
        "floor_db": floor,
        "measured": True,
        "identical_frames": len(psnr) - len(finite),
        "minimum_db": finite[0][0] if finite else None,
        "mean_db": sum(value for value, _ in finite) / len(finite) if finite else None,
        "lowest": [{"frame": index, "psnr_db": value} for value, index in finite[:LOWEST]],
        "below_floor": [
            index for index, value in enumerate(psnr) if floor is not None and value < floor
        ][:LOWEST],
    }


def identical_film(asset: Asset, floor: float | None) -> dict:
    """A rebuilt film that holds its published film's bytes: every layer holds, none decoded.

    Equal bytes decode to equal frames and audio, so no frame is counted and no PSNR measured.
    Such a film exercises no floor: without a recorded one it does not pass, and calibrates none.
    """
    note = "The rebuilt file holds the published film's bytes: no frame or audio was decoded"
    if floor is None:
        note += ", so that it measures no minimum and calibrates no floor"
    return {
        "asset": asset.name,
        "identical_file": True,
        "sha256": asset.sha256,
        "note": f"{note}.",
        "frames": None,
        "audio": "identical",
        "container": "identical",
        "psnr": unmeasured(floor),
        "failing": [],
        "verdict": "calibrating" if floor is None else "pass",
    }


def film(
    asset: Asset, rebuilt: Path, published: Path, floor: float | None, encoded: Encoded
) -> dict:
    """A rebuilt film against its published film: frames, audio, container and picture.

    `published` holds the bytes that `asset` records; a rebuilt film of that size and SHA-256
    is reported as an identical file, and any other is compared. Rebuilt by the FFmpeg that
    encoded it, its audio and every frame are decoded and compared, each frame against the
    floor. Rebuilt by another, or of an unknown encoder, its audio is compared before encoding,
    through the soundtrack's recorded bytes; its picture through the drawn-frame digest where
    the renderer drew it both times, and otherwise by decoded frames against the floor. Its
    frame count, streams, chapters and tags, which FFmpeg does not encode, are compared in
    every case.
    """
    stated = encoded.stated()
    if not rebuilt.is_file():
        return {"asset": asset.name, "verdict": "fail", "failing": ["missing"]}
    if rebuilt.stat().st_size == asset.bytes and repository.sha(rebuilt) == asset.sha256:
        return {**identical_film(asset, floor), "encoders": stated["encoders"]}
    head = {"asset": asset.name, **stated}
    frames = media.video_stream(media.probe(published)).get("nb_frames")
    if encoded.digests:
        probed = media.video_stream(media.probe(rebuilt)).get("nb_frames")
        counted = int(probed) if str(probed).isdigit() else probed
        psnr, picture = unmeasured(floor), encoded.drawn[0] == encoded.drawn[1]
        head["drawn_sha256"] = dict(zip(("recorded", "rebuilt"), encoded.drawn, strict=True))
    else:
        decoded = media.frame_psnr(rebuilt, published, DECODE_DEADLINE)
        counted, psnr = len(decoded), measured(decoded, floor)
        picture = not psnr["below_floor"]
    audio = (
        decoded_audio(rebuilt) == decoded_audio(published) if encoded.same else encoded.soundtrack
    )
    result = {
        **head,
        "identical_file": False,
        "frames": counted,
        "audio": "identical" if audio else "differs",
        "container": "identical" if container(rebuilt) == container(published) else "differs",
        "psnr": psnr,
    }
    failing = [
        layer
        for layer, held in (
            ("frames", str(counted) == str(frames)),
            ("audio", audio),
            ("container", result["container"] == "identical"),
            ("picture", picture),
        )
        if not held
    ]
    if encoded.recorded is None:
        result["note"] = (
            "The record states no FFmpeg for this film, so its encoder is unknown: its audio is "
            "compared through the soundtrack's bytes and its picture by decoded frames."
        )
    calibrating = floor is None and psnr["measured"]
    result["failing"] = failing
    result["verdict"] = "fail" if failing else "calibrating" if calibrating else "pass"
    return result


Pair = tuple[Asset, Path, Path, float | None, Encoded]


def compare_films(pairs: list[Pair]) -> dict:
    """Compare each rebuilt film with its published film, up to `PAIR_POOL` pairs at the same
    time: the results in the order given, and the seconds each pair took."""

    def timed(pair: Pair) -> tuple[dict, float]:
        started = time.monotonic()
        result = film(*pair)
        return result, round(time.monotonic() - started, 1)

    with ThreadPoolExecutor(max_workers=PAIR_POOL) as pool:
        compared = list(pool.map(timed, pairs))
    names = [asset.name for asset, *_ in pairs]
    return {
        "films": [result for result, _ in compared],
        "film_seconds": {name: seconds for name, (_, seconds) in zip(names, compared, strict=True)},
    }


def compare_edition(
    edition: production.Edition,
    record: EditionRecord,
    assets: dict,
    listed: dict[str, Asset],
    running: str,
) -> dict:
    """One edition's every layer against its published assets and its manifest record.

    `assets` holds each published asset's file, `listed` its record in the manifest, and
    `running` the running FFmpeg's version.
    """
    layers = members(edition)
    uncaptioned = edition.rendered(captions=False).page
    soundtrack = recorded(edition.soundtrack, record.soundtrack_sha256)
    rebuilt = drawn(edition)
    pictures = {
        edition.film(kind): edition.rendered(rendition.captions).name
        for kind, rendition in production.RENDITIONS.items()
    }

    def encoded(name: str, source: Path) -> Encoded:
        picture = pictures[source]
        return Encoded(
            record.ffmpeg.get(name),
            running,
            soundtrack["verdict"] == "pass",
            picture,
            (record.drawn_sha256.get(picture), rebuilt.get(picture)),
        )

    return {
        "soundtrack": soundtrack,
        "stage": recorded(edition.rendered().page, record.stage_sha256),
        **(
            {}
            if record.uncaptioned_stage_sha256 is None
            else {"uncaptioned_stage": recorded(uncaptioned, record.uncaptioned_stage_sha256)}
        ),
        "review": review(edition, assets),
        "documents": [
            identical(name, source, assets[name])
            for name, (layer, source) in layers.items()
            if layer == "document"
        ],
        **compare_films(
            [
                (
                    listed[name],
                    source,
                    assets[name],
                    record.picture_floor_db.get(name),
                    encoded(name, source),
                )
                for name, (layer, source) in layers.items()
                if layer == "film" and name in assets
            ]
        ),
        "unpublished": [
            name for name, (layer, _) in layers.items() if layer == "film" and name not in assets
        ],
    }


def failures(report: dict) -> list[str]:
    """Each failing layer as "<edition>: <layer>" or "<edition>: <asset>: <layer>"."""
    found = []
    for code, edition in report["editions"].items():
        found += [
            f"{code}: {layer}"
            for layer in ("soundtrack", "stage", "uncaptioned_stage", "review")
            if layer in edition and edition[layer]["verdict"] == "fail"
        ]
        found += [
            f"{code}: {document['asset']}: documents"
            for document in edition["documents"]
            if document["verdict"] == "fail"
        ]
        for result in edition["films"]:
            found += [f"{code}: {result['asset']}: {layer}" for layer in result["failing"]]
    return found


def passed(code: str, compared: dict) -> bool:
    """Whether an edition's comparison passed: no layer fails and no film is still calibrating."""
    calibrating = any(result["verdict"] == "calibrating" for result in compared["films"])
    return not calibrating and not failures({"editions": {code: compared}})


def compare_editions(records: dict, assets: dict, listed: dict, running: str) -> dict:
    """Each edition's comparison in the editions' order, as a run of its own. The comparison
    reports every layer before the command refuses, so an edition that did not pass says so to
    its run, which then did not complete."""
    compared = {}
    for code in production.CODES:
        with seam.run(code, "reproduce") as run:
            edition = production.Edition(code)
            compared[code] = compare_edition(edition, records[code], assets, listed, running)
            if not passed(code, compared[code]):
                run.fail()
    return compared


def compare() -> dict:
    """The comparison of the rebuild with the published release, every layer reported."""
    release = load()
    changed = changed_sources(release)
    if changed:
        msg = f"The film-bound sources differ from the release manifest: {', '.join(changed)}"
        raise ReproductionError(msg)
    assets = published(release)
    listed = {asset.name: asset for asset in release.assets}
    running = running_ffmpeg()
    report = {
        "release": release.version,
        "ffmpeg": running,
        "editions": compare_editions(release.editions, assets, listed, running),
    }
    verdicts = [
        result["verdict"] for edition in report["editions"].values() for result in edition["films"]
    ]
    report["verdict"] = (
        "fail" if failures(report) else "calibrating" if "calibrating" in verdicts else "pass"
    )
    return report


def compared() -> dict:
    """The comparison, a refusal of the release or its sources as the command's one line."""
    try:
        return compare()
    except ReproductionError as error:
        raise SystemExit(str(error)) from None


def judge(report: dict) -> None:
    """Print the comparison's verdict and release, and refuse one that did not pass: a
    comparison still calibrating in one line, one that failed with each failing layer."""
    print(json.dumps({"verdict": report["verdict"], "release": report["release"]}))
    if report["verdict"] == "calibrating":
        msg = "The comparison is calibrating: inspect each film's lowest frames, record its floor"
        raise SystemExit(msg)
    if report["verdict"] != "pass":
        raise SystemExit("\n".join(failures(report)))


if __name__ == "__main__":
    from filmkit.retired import refuse

    refuse(__spec__.name)
