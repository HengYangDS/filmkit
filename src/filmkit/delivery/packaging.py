"""Package each edition's metadata, player and delivered films.

`package_metadata` derives the viewing package: the cover as PNG and JPEG, the subtitles,
transcript and chapters, the edition's player, which the engine renders from the declared
words and colours (`filmkit.delivery.player`), and the language entry page, each recorded with
its SHA-256 in the edition's viewing package beside what the player shows. It refuses an
edition whose declared cover has not been painted yet. `package_film` requires both of the
edition's pictures valid and a passing equivalence record that binds them
(`filmkit.picture.equivalence`). It muxes each rendition's picture, the captioned one or the
uncaptioned one, with the soundtrack and chapters into every rendition in
`production.RENDITIONS`, attaches the cover and the QuickTime keys in the packaging work folder,
checks the finished film and only then links it into place, recording its SHA-256, its picture
and its commands in the edition's film package; it then derives the viewing package again, so
the player names the films' sizes. All four films carry the same soundtrack, chapters, release
metadata and cover.

A film's release metadata comes from its script's "release": FFmpeg writes it as the iTunes
item list (title, artist, collection, genre, year, comments, synopsis, copyright and media
kind) and names each track, and ExifTool adds the same facts as QuickTime keys with the
keywords and creation date, so both kinds of player read them. The title and the prose tags
set quotation marks as the captions do. FFmpeg's MP4 muxer tags its chapter text track English
whatever the film's language, so the finished film's chapter track takes the edition's
language in place (`filmkit.delivery.track_language`), and every track must carry it.

A film names its version, the Semantic Versioning 2.0.0 version without build metadata that the
film repository's `VERSION` holds (`film_version`), in the QuickTime key Information, which
Spotlight imports as the file's information, labelled in the edition's language: 版本号 1.3.0 or
Version 1.3.0. Packaging refuses a film without a valid `VERSION` before it writes anything. Both
pages name the version, and the film package binds `VERSION` among the production inputs, so a
film packaged under another version is stale.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

import filmkit.media as media
import filmkit.repository as repository
from filmkit.captions.timing import typeset
from filmkit.delivery.player import (
    COVER_JPEG,
    COVER_PNG,
    entry_version,
    player_binding,
    player_page,
    runtime_label,
    version_label,
)
from filmkit.delivery.track_language import set_chapter_language
from filmkit.film import FILM, copied_players
from filmkit.picture.equivalence import require_equivalence
from filmkit.picture.rendering import COMPOSITION_SCRIPT, validate_picture
from filmkit.production import CODES, RENDITIONS
from filmkit.repository import read, run, sha, write
from filmkit.specification import (
    AUTHOR,
    CHAPTERS,
    DURATION,
    FPS,
    H264_LEVELS,
    ISO_LANGUAGES,
    RATE,
)

if TYPE_CHECKING:
    from filmkit.production import Edition, Rendition


class PackagingError(ValueError):
    """A package input or a finished film differs from what packaging requires."""


# The delivery folder's entry page, below the repository root.
INDEX = Path(FILM.entry)
# The language entry page derived from INDEX, below the root.
LANGUAGE_INDEX = Path("build/artifacts/film/index.html")
# The folder below the root where each edition's films are encoded and finished.
WORK = Path("build/runtime/work/final-film-packaging")
# What a failed or timed-out encode was bound to, in the edition's evidence folder.
FAILURE_RECEIPT = "packaging-failure.json"
CAPTION_OWNER = (
    "The captioned films' picture draws the captions and the uncaptioned films' picture none;"
    " packaging burns in no captions"
)
# No encode's deadline is shorter, in seconds.
DEADLINE_FLOOR = 600
# The prefix FFprobe reports ExifTool's QuickTime keys under, and the creation date's key, which
# packaging writes beside the release's keys.
QUICKTIME_PREFIX = "com.apple.quicktime."
CREATION_KEY = QUICKTIME_PREFIX + "creationdate"
# The film that a delivery binding names for the real-browser player check.
BOUND_FILM = {"slug": FILM.slug, "duration": DURATION}
# The film repository's version, below its root, and the form it must take: a Semantic Versioning
# 2.0.0 version without build metadata, such as 1.3.0 or 2.0.0-rc.1.
VERSION = Path("VERSION")
SEMANTIC_VERSION = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?", re.ASCII
)


def film_version() -> str:
    """The film's version: what its repository's `VERSION` holds without surrounding whitespace.

    A missing `VERSION`, or one that holds anything but a Semantic Versioning 2.0.0 version
    without build metadata, refuses, naming the file.
    """
    path = repository.ROOT / VERSION
    held = path.read_text(encoding="utf-8", errors="replace").strip() if path.is_file() else None
    if held is None or not SEMANTIC_VERSION.fullmatch(held):
        found = "is missing" if held is None else f"holds {held!r}"
        msg = (
            f"The film's {VERSION} {found}; it must hold a Semantic Versioning 2.0.0 version "
            "without build metadata, such as 1.3.0"
        )
        raise PackagingError(msg)
    return held


def viewing_members(edition: Edition) -> tuple[str, ...]:
    """The viewing package's members in record order, by name in the edition's folder."""
    return (
        COVER_PNG,
        COVER_JPEG,
        f"{edition.prefix}.srt",
        f"{edition.prefix}.vtt",
        f"{edition.prefix}-transcript.md",
        "chapters.json",
        "chapters.ffmeta",
        "index.html",
    )


def package_language_index(version: str) -> dict:
    """Derive one neutral entry point for the sibling language deliveries.

    It names the film's version under the film's title, in a line of its own just before the
    `<nav>` that holds the language links.
    """
    source = repository.ROOT / INDEX
    destination = repository.ROOT / LANGUAGE_INDEX
    template = source.read_text()
    start = template.find("<nav")
    nav = template[start : template.find("</nav>", start)] if start >= 0 else ""
    if not all(f'href="{code}/index.html"' in nav for code in CODES):
        msg = "Delivery entry needs both sibling language links in a <nav>"
        raise PackagingError(msg)
    if "<base " in template:
        msg = "Delivery entry must not select a language through base"
        raise PackagingError(msg)
    page = template.replace("/*RUNTIME*/", runtime_label())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page.replace("<nav", f"{entry_version(version)}\n<nav", 1))
    return {
        "source": str(INDEX),
        "source_sha256": sha(source),
        "path": str(LANGUAGE_INDEX),
        "sha256": sha(destination),
        "languages": list(CODES),
    }


def refresh_shot_plan(edition: Edition, timeline: dict) -> None:
    """Derive scene bindings without assigning capture or artistic acceptance."""
    source = read(edition.script)
    scenes = source["segments"]
    segments = timeline["segments"]
    if len(scenes) != len(segments) or len({s["id"] for s in scenes}) != len(scenes):
        msg = "Shot plan requires the complete unique scene sequence"
        raise PackagingError(msg)
    shots = []
    identity = ("id", "title", "text", "source_sections")
    for scene, segment in zip(scenes, segments, strict=True):
        if any(scene[key] != segment[key] for key in identity):
            msg = "Shot plan timeline differs from the current script"
            raise PackagingError(msg)
        shots.append(
            {
                **{key: scene[key] for key in identity if key != "text"},
                **{
                    key: segment[key]
                    for key in ("start", "end", "voice_start", "voice_end", "gap_kind")
                },
                "script_text_sha256": repository.content_sha(scene["text"]),
                "caption_count": sum(cue["segment"] == scene["id"] for cue in timeline["captions"]),
            }
        )
    write(
        edition.shot_plan,
        {
            "schema_version": 1,
            "language": edition.code,
            "duration": DURATION,
            "fps": FPS,
            "script_sha256": sha(edition.script),
            "composition_sha256": sha(COMPOSITION_SCRIPT),
            "timeline_sha256": sha(edition.timeline),
            "composition_owner": str(COMPOSITION_SCRIPT),
            "motion_grammar": (
                "One dark 2D field; each scene shows its subject as objects, "
                "processes and relations that change on spoken words, with "
                "minimal attached labels."
            ),
            "binding_scope": (
                "Current source and timing projection; capture, audiovisual "
                "quality and artistic acceptance are checked separately."
            ),
            "shots": shots,
        },
    )


def package_metadata(edition: Edition) -> None:
    """Derive the viewing package from the current source-bound timeline and the film's version,
    which must be valid before anything is written."""
    copied = copied_players(repository.ROOT, FILM)
    if copied:
        raise PackagingError(copied)
    output = edition.artifacts
    source_cover = repository.ROOT / edition.cover
    if not source_cover.is_file():
        msg = (
            f"The declaration names an unpainted cover, editions.{edition.code}.cover: "
            f"{edition.cover}; paint it from the staged picture with the cover check"
        )
        raise PackagingError(msg)
    version = film_version()
    target_cover = output / COVER_PNG
    if not target_cover.exists() or sha(target_cover) != sha(source_cover):
        shutil.copy2(source_cover, target_cover)
    timeline = read(edition.timeline)
    if (timeline["duration"], timeline["fps"]) != (DURATION, FPS):
        msg = f"The timeline must last {DURATION} s at {FPS} fps"
        raise PackagingError(msg)
    refresh_shot_plan(edition, timeline)
    chapters = read(output / "chapters.json")["chapters"]
    if len(chapters) != CHAPTERS:
        msg = f"The films have {CHAPTERS} chapters, not {len(chapters)}"
        raise PackagingError(msg)
    language_index = package_language_index(version)
    with Image.open(output / COVER_PNG) as cover:
        if cover.width * 9 != cover.height * 16:
            msg = f"The cover must be 16:9, not {cover.width}x{cover.height}"
            raise PackagingError(msg)
        cover.convert("RGB").save(output / COVER_JPEG, quality=95)
    (output / "index.html").write_text(player_page(edition, version), encoding="utf-8")
    members = viewing_members(edition)
    write(
        edition.viewing_package,
        {
            "script_sha256": sha(edition.script),
            "timeline_sha256": sha(edition.timeline),
            "player": player_binding(edition),
            "language_index": language_index,
            "author": AUTHOR,
            "version": version,
            "chapters": CHAPTERS,
            "members": [{"path": name, "sha256": sha(output / name)} for name in members],
            "scope": "Metadata and player derivation; actual playback checked separately",
        },
    )
    print(json.dumps({"package": str(output), "members": members}), flush=True)


def film_inputs(edition: Edition) -> dict[str, Path]:
    """The production inputs of the delivered films, by the record field of each SHA-256: both
    pictures and the record of their equivalence among them, and the film's `VERSION`."""
    return {
        "picture_sha256": edition.picture,
        "uncaptioned_picture_sha256": edition.rendered(captions=False).file,
        "caption_equivalence_sha256": edition.caption_equivalence,
        "soundtrack_sha256": edition.soundtrack,
        "cover_sha256": edition.artifacts / COVER_JPEG,
        "script_sha256": repository.ROOT / edition.script,
        "chapters_sha256": edition.artifacts / "chapters.ffmeta",
        "version_sha256": repository.ROOT / VERSION,
    }


def film_bindings(edition: Edition) -> dict:
    """The production inputs of the delivered films, by SHA-256, in record order."""
    return {key: sha(path) for key, path in film_inputs(edition).items()}


def stale_bindings(edition: Edition, package: dict) -> list[str]:
    """The fields of a film package record that the current inputs no longer match.

    An input that is missing now matches no record.
    """
    stale = [
        key
        for key, path in film_inputs(edition).items()
        if not path.is_file() or package.get(key) != sha(path)
    ]
    return stale + (["caption_owner"] if package.get("caption_owner") != CAPTION_OWNER else [])


def resume_package(edition: Edition) -> dict:
    """The edition's film package: the recorded one when it binds the current inputs, else new."""
    package = {**film_bindings(edition), "editions": [], "caption_owner": CAPTION_OWNER}
    if edition.film_package.exists():
        previous = read(edition.film_package)
        if stale_bindings(edition, previous):
            msg = "Existing package is bound to different production inputs"
            raise PackagingError(msg)
        package["editions"] = previous["editions"]
    return package


def video_tags(rendition: Rendition) -> str:
    """The H.264 bitstream tags: BT.709 colour and limited range, and the level for 60 fps.

    The tags spare players a guess; at the rendition's height, every other limit of that level
    is at least that of the encoder's lower default.
    """
    return (
        "h264_metadata=colour_primaries=1:transfer_characteristics=1"
        ":matrix_coefficients=1:video_full_range_flag=0"
        f":level={H264_LEVELS[rendition.height] / 10}"
    )


def release_tags(edition: Edition, rendition: Rendition) -> list[tuple[str, str]]:
    """The film's global tags in command order, as FFmpeg names them for the iTunes item list.

    A media type of 9 marks a movie; the 1080p film is also marked as HD video of 1080 lines.
    """
    script = read(edition.script)
    release = script["release"]
    tags = [
        ("title", typeset(script["title"])),
        ("artist", AUTHOR),
        ("album_artist", AUTHOR),
        ("album", release["collection"]),
        ("genre", release["genre"]),
        ("date", str(release["year"])),
        ("comment", typeset(release["comment"])),
        ("description", typeset(release["description"])),
        ("synopsis", typeset(release["synopsis"])),
        ("copyright", f"© {release['year']} {AUTHOR}"),
        ("media_type", "9"),
    ]
    return [*tags, ("hd_video", "2")] if rendition.height == 1080 else tags


def track_names(edition: Edition) -> dict[str, str]:
    """The names of the film's picture and narration tracks."""
    return dict(read(edition.script)["release"]["tracks"])


def quicktime_keys(edition: Edition) -> dict[str, str]:
    """The QuickTime keys ExifTool writes, by ExifTool tag name, without the creation date.

    The author stands only under Author: Spotlight lists every author-bearing QuickTime key
    among a film's authors, so an Artist key would list the author twice, and the item-list
    artist tags, which the release tags carry, do not count. Information names the film's
    version with the edition's label.
    """
    script = read(edition.script)
    release = script["release"]
    return {
        "Author": AUTHOR,
        "Title": typeset(script["title"]),
        "Album": release["collection"],
        "Genre": release["genre"],
        "Description": typeset(release["description"]),
        "Comment": typeset(release["comment"]),
        "Copyright": f"© {release['year']} {AUTHOR}",
        "Keywords": ", ".join(release["keywords"]),
        "Year": str(release["year"]),
        "Information": version_label(edition.code, film_version()),
    }


def delivered_tags(edition: Edition, rendition: Rendition) -> dict[str, str]:
    """The global tags FFprobe reads from a finished film: its item list and QuickTime keys."""
    keys = {
        f"{QUICKTIME_PREFIX}{key.lower()}": value for key, value in quicktime_keys(edition).items()
    }
    return {**dict(release_tags(edition, rendition)), **keys}


def only_release_keys(tags: dict, expected: dict) -> bool:
    """Whether every QuickTime key of a film's tags is one of its release's or its creation date."""
    keys = {key for key in tags if key.startswith(QUICKTIME_PREFIX)}
    return keys <= {*expected, CREATION_KEY}


def keyed_as_declared(rendition: Rendition, keyframes: list[int]) -> bool:
    """Whether a film's keyframes stand at every interval its rendition declares, from the first
    frame, and nowhere else; a rendition that declares none keeps the keyframes it copies."""
    if rendition.keyframe_seconds is None:
        return True
    return keyframes == list(range(0, DURATION * FPS, rendition.keyframe_seconds * FPS))


def keyframe_options(rendition: Rendition) -> tuple[str, ...]:
    """The encoder option that sets a rendition's declared keyframe interval, if it declares one."""
    if rendition.keyframe_seconds is None:
        return ()
    return ("-g:v:0", str(rendition.keyframe_seconds * FPS))


def encode_command(
    edition: Edition, rendition: Rendition, intermediate: Path, created_at: str
) -> list[str]:
    """The FFmpeg command that muxes the rendition's picture, the soundtrack and the chapters
    into one film."""
    language, names = ISO_LANGUAGES[edition.code], track_names(edition)
    tags = [
        *(f"{key}={value}" for key, value in release_tags(edition, rendition)),
        f"creation_time={created_at}",
    ]
    return [
        "ffmpeg",
        "-v",
        "warning",
        "-nostdin",
        *rendition.decoding,
        "-i",
        str(edition.rendered(rendition.captions).file),
        "-i",
        str(edition.soundtrack),
        "-f",
        "ffmetadata",
        "-i",
        str(edition.artifacts / "chapters.ffmeta"),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map_metadata",
        "2",
        "-map_chapters",
        "2",
        *rendition.video,
        *keyframe_options(rendition),
        "-bsf:v:0",
        video_tags(rendition),
        "-c:a",
        "aac",
        "-b:a",
        "256k",
        "-ar",
        str(RATE),
        "-ac",
        "2",
        "-t",
        str(DURATION),
        *(argument for tag in tags for argument in ("-metadata", tag)),
        "-metadata:s:v:0",
        "language=" + language,
        "-metadata:s:v:0",
        "handler_name=" + names["picture"],
        "-metadata:s:a:0",
        "language=" + language,
        "-metadata:s:a:0",
        "handler_name=" + names["narration"],
        "-movflags",
        "+faststart",
        str(intermediate),
    ]


def encode(
    edition: Edition, package: dict, command: list[str], deadline: int, intermediate: Path
) -> None:
    """Run an encode; when it fails or times out, record what it was bound to and re-raise."""
    try:
        run(command, timeout=deadline)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        write(
            edition.evidence / FAILURE_RECEIPT,
            {
                "input_bindings": {
                    key: value for key, value in package.items() if key != "editions"
                },
                "command": command,
                "deadline_seconds": deadline,
                "error_type": type(error).__name__,
                "intermediate": str(intermediate.relative_to(repository.ROOT)),
                "intermediate_sha256": sha(intermediate) if intermediate.exists() else None,
                "completed_members": [member["path"] for member in package["editions"]],
            },
        )
        raise


def attach_cover_and_keys(
    edition: Edition, intermediate: Path, finished: Path, created_at: str
) -> list[list[str]]:
    """Attach the JPEG cover and the QuickTime keys; return both commands."""
    cover_command = [
        "ffmpeg",
        "-v",
        "warning",
        "-nostdin",
        "-i",
        str(intermediate),
        "-i",
        str(edition.artifacts / COVER_JPEG),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-map",
        "1:v:0",
        "-map_metadata",
        "0",
        "-map_chapters",
        "0",
        "-c",
        "copy",
        "-disposition:v:1",
        "attached_pic",
        "-movflags",
        "+faststart",
        str(finished),
    ]
    run(cover_command, timeout=120)
    keys = {**quicktime_keys(edition), "CreationDate": created_at}
    keys_command = [
        "exiftool",
        "-overwrite_original",
        *(f"-Keys:{key}={value}" for key, value in keys.items()),
        str(finished),
    ]
    run(keys_command, timeout=120)
    return [cover_command, keys_command]


def check_delivered_film(path: Path, edition: Edition, rendition: Rendition) -> None:
    """Refuse a finished film without every frame, its duration, cover, release tags or tracks.

    Its release tags must be exactly the rendition's, so only the 1080p film is marked HD, it
    may carry no other QuickTime key than its release's and its creation date, its picture and
    narration tracks must carry their names, and every track but the attached cover, the
    chapter track included, the edition's language. A rendition that declares a keyframe
    interval must hold its keyframes exactly there.
    """
    info = media.probe(path)
    streams = info["streams"]
    movie = media.video_stream(info)
    sounds = [stream for stream in streams if stream["codec_type"] == "audio"]
    tags, expected = info["format"].get("tags", {}), delivered_tags(edition, rendition)
    names, language = track_names(edition), ISO_LANGUAGES[edition.code]
    if not (
        sounds
        and int(movie["nb_frames"]) == DURATION * FPS
        and movie["avg_frame_rate"] == f"{FPS}/1"
        and float(info["format"]["duration"]) == float(sounds[0]["duration"]) == DURATION
        and any(stream.get("disposition", {}).get("attached_pic") for stream in streams)
        and all(tags.get(key) == expected.get(key) for key in {*expected, "hd_video"})
        and only_release_keys(tags, expected)
        and movie.get("tags", {}) | {"handler_name": names["picture"], "language": language}
        == movie.get("tags", {})
        and sounds[0].get("tags", {}) | {"handler_name": names["narration"], "language": language}
        == sounds[0].get("tags", {})
        and all(
            stream.get("tags", {}).get("language") == language
            for stream in streams
            if not stream.get("disposition", {}).get("attached_pic")
        )
    ):
        msg = f"The finished film differs from the delivery contract: {path}"
        raise PackagingError(msg)
    if rendition.keyframe_seconds is not None:
        try:
            keyframes = media.video_cadence(path, DURATION * FPS, FPS)["keyframes"]
        except media.MediaError as error:
            msg = f"The finished film differs from the delivery contract: {path}: {error}"
            raise PackagingError(msg) from error
        if not keyed_as_declared(rendition, keyframes):
            msg = f"The finished film differs from the delivery contract: {path}: keyframes"
            raise PackagingError(msg)


def package_rendition(
    edition: Edition, package: dict, rendition: Rendition, target: Path, created_at: str
) -> dict:
    """Encode, finish and check one film in the work folder, then link it into place.

    Returns the film's package member, which names the picture it carries. A film or work file
    already in place is preserved for inspection, as is the work of a failed step.
    """
    if target.exists():
        msg = f"Preserve existing film output: {target}"
        raise PackagingError(msg)
    work = repository.ROOT / WORK / edition.code
    intermediate, finished = work / target.name, work / "finished" / target.name
    if intermediate.exists() or finished.exists():
        msg = f"Preserve existing packaging input: {target.name}"
        raise PackagingError(msg)
    finished.parent.mkdir(parents=True, exist_ok=True)
    command = encode_command(edition, rendition, intermediate, created_at)
    write(edition.film_package, package)
    deadline = max(DEADLINE_FLOOR, DURATION * rendition.deadline_ratio)
    encode(edition, package, command, deadline, intermediate)
    commands = [command, *attach_cover_and_keys(edition, intermediate, finished, created_at)]
    set_chapter_language(finished, ISO_LANGUAGES[edition.code])
    check_delivered_film(finished, edition, rendition)
    target.hardlink_to(finished)
    picture = edition.rendered(rendition.captions).name
    member = {"path": target.name, "sha256": sha(target), "picture": picture, "commands": commands}
    finished.unlink()
    intermediate.unlink()
    return member


def package_film(edition: Edition) -> None:
    """Write every delivered film with the exact soundtrack and media metadata.

    Both pictures must be valid and their equivalence record must pass and bind them. A film
    recorded by a package bound to the current inputs is reused when its bytes are the recorded
    ones; the edition's folder never receives a film before its checks pass. The finished
    package supersedes the failure receipt of an earlier attempt, which is retired.
    """
    for captions in (True, False):
        picture = edition.rendered(captions).file
        if not picture.is_file():
            msg = f"No rendered picture at {picture}"
            raise PackagingError(msg)
        validate_picture(edition, captions=captions)
    require_equivalence(edition)
    package_metadata(edition)
    package = resume_package(edition)
    created_at = datetime.now(UTC).isoformat()
    for kind, rendition in RENDITIONS.items():
        target = edition.film(kind)
        completed = next((m for m in package["editions"] if m["path"] == target.name), None)
        if completed:
            if not target.is_file() or sha(target) != completed["sha256"]:
                msg = "Completed package member differs; preserve and inspect it"
                raise PackagingError(msg)
            print(json.dumps({"film": target.name, "reused_verified_member": True}), flush=True)
            continue
        package["editions"].append(
            package_rendition(edition, package, rendition, target, created_at)
        )
        write(edition.film_package, package)
        print(json.dumps({"film": target.name, "bytes": target.stat().st_size}), flush=True)
    write(edition.film_package, package)
    (edition.evidence / FAILURE_RECEIPT).unlink(missing_ok=True)
    # The player names the films' sizes, known only now.
    package_metadata(edition)
