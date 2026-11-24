"""Verify delivered film editions against their current authored inputs.

The checks cover the pinned canonical sources, narration custody, both rendered pictures and
the record that they differ only by their captions, package bindings, the still scan of the
1080p captioned film (`filmkit.picture.still_scan.require_film_scan`), the film's version that
the films and pages name, complete media decoding of all four films, the keywords and authors
Spotlight imports from each film where the host has `mdimport`, and the recorded review
thresholds.
Aesthetic judgment belongs to the review record; human listening stays separate.
The verifier reads and decodes, and prints each edition's report, which states the seconds each
film's media took. Up to four films' media are verified at the same time. The one file it writes
is each edition's duration record of the run (`filmkit.durations`), which says how long the
verification took and nothing about the films: no check reads it, and with --read-only the
verifier writes nothing at all.

Usage: python -m filmkit.delivery.verification [--technical-only] --language zh|en|all
           [<films>]
Without films, each selected edition's current delivered films are verified.
"""

from __future__ import annotations

import argparse
import json
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import filmkit.captions.timing as captions_timing
import filmkit.delivery.packaging as packaging
import filmkit.delivery.player as player
import filmkit.delivery.spotlight as spotlight
import filmkit.durations as durations
import filmkit.languages as languages
import filmkit.media as media
import filmkit.narration.selection as narration_selection
import filmkit.narration.spoken_units as narration_spoken_units
import filmkit.narration.thought_groups as narration_thought_groups
import filmkit.picture.derivation as picture_derivation
import filmkit.picture.equivalence as picture_equivalence
import filmkit.picture.rendering as picture_rendering
import filmkit.picture.still_scan as picture_still_scan
import filmkit.production as production
import filmkit.repository as repository
import filmkit.review.record as review_record
import filmkit.sources as sources
import filmkit.specification as specification
from filmkit.picture.rendering import COMPOSITION_SCRIPT


class VerificationError(ValueError):
    """A delivered edition or one of its bound inputs differs from what acceptance requires."""


# How many films' media are verified at the same time: each is one complete decode, which uses a
# few of the host's cores.
MEDIA_POOL = 4
FPS, RATE = specification.FPS, specification.RATE


def edition_inputs(files: list[Path]) -> dict[str, list[Path]]:
    """Require every declared edition's films, each under its edition's current folder, and no
    other file, naming each edition whose films are missing (a bridge until R2b's `filmkit
    verify`, which replaces this command's loop over the editions)."""
    groups = {code: production.Edition(code).films for code in production.CODES}
    expected = {path for films in groups.values() for path in films}
    if len(files) != len(expected) or set(files) != expected:
        missing = [code for code, films in groups.items() if not set(films) <= set(files)]
        others = sorted(path.name for path in set(files) - expected)
        named = [f"the {code} edition's current films are missing" for code in missing]
        named += [f"{', '.join(others)} belong to no edition's current films"] if others else []
        named += ["a film is named twice"] if len(files) != len(set(files)) else []
        msg = "Acceptance of every edition requires each one's current films: " + "; ".join(named)
        raise VerificationError(msg)
    return groups


def verify_sources() -> dict:
    """The pinned canonical sources, checked against a local clone when one is named."""
    return sources.verify()


def verify_captions(timeline: dict, code: str) -> int:
    """Captions stay single-line, typeset, within their limit and before the credits: the
    timeline's runtime less its credits as laid out, which must lie within it."""
    limit, prior_end = languages.language(code).captions.limit, 0.0
    runtime, laid = production.Edition(code).runtime_in(timeline), timeline.get("credits_duration")
    if type(laid) not in {int, float} or not 0 <= laid < runtime:
        msg = f"The {code} timeline states no credits within its runtime"
        raise VerificationError(msg)
    credits = runtime - laid
    for cue in timeline["captions"]:
        display = cue.get("display_text", cue["text"])
        if not (
            0 <= cue["start"] < cue["end"] <= credits
            and cue["start"] >= prior_end - 0.15
            and all("\n" not in v and len(v) <= limit for v in (cue["text"], display))
            and all(captions_timing.typeset(v) == v for v in (cue["text"], display))
            and narration_spoken_units.units(display) == narration_spoken_units.units(cue["text"])
        ):
            msg = f"Caption differs from the caption contract: {cue}"
            raise VerificationError(msg)
        prior_end = cue["end"]
    return len(timeline["captions"])


def verify_narration(edition: production.Edition) -> dict:
    """Bind script, selected recordings, assembly, soundtrack and timeline."""
    script_path, cast_path = repository.ROOT / edition.script, repository.ROOT / edition.cast
    script, cast = repository.read(script_path), repository.read(cast_path)
    script_sha256 = repository.sha(script_path)
    mirror = (repository.ROOT / edition.mirror).read_text().strip()
    if mirror != "\n\n".join(segment["text"] for segment in script["segments"]):
        msg = "Narration mirror differs from the current script"
        raise VerificationError(msg)
    selected = repository.read(edition.narration_selected)
    assembly = repository.read(edition.audio_assembly)
    soundtrack = edition.soundtrack
    timeline = repository.read(edition.timeline)
    if (
        selected["script_sha256"] != script_sha256
        or selected["cast_sha256"] != repository.sha(cast_path)
        or assembly["script_sha256"] != script_sha256
        or assembly["soundtrack_sha256"] != repository.sha(soundtrack)
    ):
        msg = "Narration custody differs from the current script"
        raise VerificationError(msg)
    with wave.open(str(soundtrack)) as audio:
        shape = (audio.getnframes(), audio.getframerate(), audio.getnchannels())
    if shape != (edition.runtime_in(timeline) * RATE, RATE, 2):
        msg = "Soundtrack must be exact 48 kHz stereo for the runtime"
        raise VerificationError(msg)
    level, policy = assembly.get("program_level", {}), specification.PROGRAM_LEVEL
    after = level.get("after", {})
    if not (
        level.get("policy") == policy
        and abs(after.get("integrated_lufs", -99) - policy["integrated_lufs"]) <= 0.5
        and after.get("true_peak_dbtp", 99) <= policy["true_peak_ceiling_dbtp"]
    ):
        msg = "Soundtrack differs from the declared program level"
        raise VerificationError(msg)
    order = [segment["id"] for segment in script["segments"]]
    if order != [segment["id"] for segment in timeline["segments"]] or order != [
        record["id"] for record in selected["records"]
    ]:
        msg = "Script, timeline and selection differ in segment order"
        raise VerificationError(msg)
    for section, segment, record in zip(
        script["segments"], timeline["segments"], selected["records"], strict=True
    ):
        if (
            not (section["text"] == segment["text"] == record["text"])
            or repository.sha(repository.ROOT / record["path"]) != record["wav_sha256"]
        ):
            msg = f"Selected recording differs: {section['id']}"
            raise VerificationError(msg)
        narration_thought_groups.validate_group_inputs(
            record, root=repository.ROOT, section=section
        )
        narration_selection.validate_voice_record(record, cast, edition.places.reference)
    return {
        "segments": len(order),
        "captions": verify_captions(timeline, edition.code),
        "soundtrack_sha256": assembly["soundtrack_sha256"],
        "program_level": after,
    }


def require_covering_geometry(edition: production.Edition) -> dict:
    """The geometry record, refused unless it passed on the whole current staged film."""
    geometry = repository.read(edition.picture_geometry)
    step, runtime = geometry.get("step_frames"), edition.runtime
    if not (
        geometry.get("format") == "picture-geometry"
        and geometry.get("passed") is True
        and geometry["findings"] == geometry["errors"] == []
        and geometry["index_sha256"] == repository.sha(edition.rendered().page)
        and (geometry["width"], geometry["height"]) == picture_rendering.PICTURE_SIZE
        and (geometry["duration"], geometry["fps"]) == (runtime, FPS)
        and step in (1, 2)
        and geometry["checked"] == -(-runtime * FPS // step)
    ):
        msg = "Picture geometry does not cover the current staged film"
        raise VerificationError(msg)
    return geometry


def verify_picture(edition: production.Edition) -> dict:
    """Bind the captioned picture's render and whole-film geometry to its staged picture and the
    uncaptioned picture to its render or its derivation, and require the passing record that the
    two differ only by their captions."""
    render = repository.read(edition.render_receipt)
    picture_rendering.validate_picture_binding(edition, render)
    uncaptioned = repository.read(edition.rendered(captions=False).receipt)
    picture_rendering.validate_picture_binding(edition, uncaptioned, captions=False)
    geometry = require_covering_geometry(edition)
    plan = repository.read(edition.shot_plan)
    if (
        plan["script_sha256"] != repository.sha(repository.ROOT / edition.script)
        or plan["composition_sha256"] != repository.sha(repository.ROOT / COMPOSITION_SCRIPT)
        or plan["timeline_sha256"] != repository.sha(edition.timeline)
    ):
        msg = "Shot plan differs from the current picture inputs"
        raise VerificationError(msg)
    equivalence = picture_equivalence.require_equivalence(edition)
    encoded = equivalence["encoded"]
    compared = (
        {"derived": True, "ground_frames": encoded["derived"]["ground_check"]["frames"]}
        if "derived" in encoded
        else {"encoded_frames": encoded["frames"]}
    )
    return {
        "picture_sha256": render["output_sha256"],
        "uncaptioned_picture_sha256": uncaptioned["output_sha256"],
        "caption_equivalence": {
            "composition_instants": equivalence["composition"]["instants"],
            **compared,
        },
        "geometry_frames": geometry["checked"],
        "browser": geometry["browser"],
    }


def language_index() -> dict:
    """The record of the language entry page that a current viewing package holds."""
    return {
        "source": str(packaging.INDEX),
        "source_sha256": repository.sha(repository.ROOT / packaging.INDEX),
        "path": str(packaging.LANGUAGE_INDEX),
        "sha256": repository.sha(repository.ROOT / packaging.LANGUAGE_INDEX),
        "languages": list(production.CODES),
    }


def verify_package(edition: production.Edition) -> dict:
    """Bind every delivered film, the picture each carries, the picture file each read and the
    viewing package to their inputs, the film's `VERSION` among them; the viewing package's pages
    must name its version."""
    output = edition.artifacts
    films = repository.read(edition.film_package)
    names = sorted(film.name for film in edition.films)
    pictures, sources = {}, {}
    for kind, rendition in production.RENDITIONS.items():
        own = edition.rendered(rendition.captions)
        pictures[edition.film(kind).name] = own.name
        # A member written before members named their source read its own picture.
        read = picture_derivation.film_source(edition, rendition)[0].name
        sources[edition.film(kind).name] = (own.file.name, read)
    if (
        packaging.stale_bindings(edition, films)
        or sorted(member["path"] for member in films["editions"]) != names
        or any(
            member["sha256"] != repository.sha(output / member["path"])
            or member.get("picture") != pictures[member["path"]]
            or member.get("source", sources[member["path"]][0]) != sources[member["path"]][1]
            for member in films["editions"]
        )
    ):
        msg = "Film package differs from its current inputs"
        raise VerificationError(msg)
    viewing = repository.read(edition.viewing_package)
    if [member["path"] for member in viewing["members"]] != list(
        packaging.viewing_members(edition)
    ):
        msg = "Viewing package members differ from the declared viewing members"
        raise VerificationError(msg)
    if (
        viewing["script_sha256"] != repository.sha(repository.ROOT / edition.script)
        or viewing["timeline_sha256"] != repository.sha(edition.timeline)
        or viewing.get("player") != player.player_binding(edition)
        or viewing["author"] != specification.AUTHOR
        or viewing.get("version") != packaging.film_version()
        or viewing["chapters"] != specification.CHAPTERS
        or any(
            member["sha256"] != repository.sha(output / member["path"])
            for member in viewing["members"]
        )
        or repository.sha(output / packaging.COVER_PNG)
        != repository.sha(repository.ROOT / edition.cover)
    ):
        msg = "Viewing package differs from its current inputs"
        raise VerificationError(msg)
    if viewing.get("language_index") != language_index():
        msg = "Viewing package language index differs from the current entry page"
        raise VerificationError(msg)
    return {"films": names, "viewing_members": len(viewing["members"])}


def verify_media(edition: production.Edition, path: Path, rendition: production.Rendition) -> dict:
    """Decode one complete delivered movie and check its rendition's declared contract, over
    the edition's runtime."""
    size, runtime = rendition.size, edition.runtime
    data = media.probe(path)
    try:
        video = media.require_video(
            data, frames=runtime * FPS, fps=FPS, size=size, duration=runtime
        )
    except media.MediaError as error:
        msg = f"Movie differs from the delivery contract: {path.name}: {error}"
        raise VerificationError(msg) from error
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    tags = data["format"]["tags"]
    language = edition.declaration.iso639_2
    release, names = packaging.delivered_tags(edition, rendition), packaging.track_names(edition)
    tolerance = media.DURATION_TOLERANCE
    if not (
        audio is not None
        and video.get("field_order", "progressive") in ("progressive", "unknown")
        and all(
            video.get(key) == "bt709"
            for key in ("color_primaries", "color_transfer", "color_space")
        )
        and video.get("level") == specification.H264_LEVELS[size[1]]
        and (int(audio["sample_rate"]), audio["channels"]) == (RATE, 2)
        and abs(float(audio["duration"]) - runtime) < tolerance
        and any(s.get("disposition", {}).get("attached_pic") for s in data["streams"])
        and tags.get("artist") == specification.AUTHOR
        and tags.get("author", tags.get("com.apple.quicktime.author")) == specification.AUTHOR
        and all(tags.get(key) == release.get(key) for key in {*release, "hd_video"})
        and packaging.only_release_keys(tags, release)
        and all(
            stream.get("tags", {}).get("language") == language
            for stream in data["streams"]
            if not stream.get("disposition", {}).get("attached_pic")
        )
        and video.get("tags", {}).get("handler_name") == names["picture"]
        and audio.get("tags", {}).get("handler_name") == names["narration"]
        and len(data["chapters"]) == specification.CHAPTERS
    ):
        msg = f"Movie differs from the delivery contract: {path.name}"
        raise VerificationError(msg)
    cadence = media.video_cadence(path, runtime * FPS, FPS)
    if not packaging.keyed_as_declared(rendition, cadence.get("keyframes", []), runtime):
        msg = f"Movie differs from the delivery contract: {path.name}: keyframes"
        raise VerificationError(msg)
    frames = media.decoded_video_frames(path, runtime * FPS, max(300, runtime))
    sample_frames = media.decoded_audio_frames(path)
    # AAC encoder padding is distinct from the declared sample domain.
    if abs(sample_frames - runtime * RATE) > 1024:
        msg = f"Decoded audio length differs: {path.name}"
        raise VerificationError(msg)
    return {
        "path": str(path.relative_to(repository.ROOT)),
        "sha256": repository.sha(path),
        "bytes": path.stat().st_size,
        "dimensions": list(size),
        "video_frames": frames,
        "audio_sample_frames_decoded": sample_frames,
    }


def verify_spotlight(edition: production.Edition, files: list[Path]) -> dict:
    """Read each delivered film's keywords and authors back as Spotlight imports them, where the
    host has `mdimport`.

    A film is refused with an imported keyword that has a space at either end, no imported keyword
    while the release declares some, a declared Chinese keyword that does not import whole, or any
    authors but the declared author, once.
    Each film records the keywords and authors imported and the declared keywords the importer
    split into words (`filmkit.delivery.spotlight`).
    """
    declared = repository.read(repository.ROOT / edition.script)["release"]["keywords"]
    films = []
    for path in files:
        imported = spotlight.imported(path)
        if imported is None:
            return {"readback": "unavailable"}
        problems = [
            *spotlight.keyword_problems(declared, imported["keywords"]),
            *spotlight.author_problems(specification.AUTHOR, imported["authors"]),
        ]
        if problems:
            msg = f"Spotlight imports {path.name} otherwise than declared: {'; '.join(problems)}"
            raise VerificationError(msg)
        films.append(
            {
                "path": str(path.relative_to(repository.ROOT)),
                **imported,
                "split_into_words": spotlight.split_into_words(declared, imported["keywords"]),
            }
        )
    return {"readback": "mdimport", "films": films}


def verify_review(
    edition: production.Edition, files: list[Path], record: Path | None = None
) -> dict:
    """Accept only a current review of every delivered film above threshold.

    The record is the edition's own unless a published one is named. A review covers each
    film by its name and bytes, and its report lies beside it under the same name. It holds no
    finding the film does not accept, and for a film that declares review levels every level
    passes and every sentence of the current timeline is judged (`filmkit.review.record`).
    """
    path = record or edition.production_review
    if not path.is_file():
        msg = f"No review record {repository.relative(path)}"
        raise VerificationError(msg)
    review = repository.read(path)
    covered = {Path(item["path"]).name: item["sha256"] for item in review["media"]}
    current = {film.name: repository.sha(film) for film in files}
    if (
        review.get("schema_version") != review_record.SCHEMA_VERSION
        or review.get("language") != edition.code
        or covered != current
        or review["script_sha256"] != repository.sha(repository.ROOT / edition.script)
        or review["composition_sha256"] != repository.sha(repository.ROOT / COMPOSITION_SCRIPT)
    ):
        msg = "Review does not cover the current delivered edition"
        raise VerificationError(msg)
    scores = review["scores"]
    if set(scores) != set(review_record.DIMENSIONS):
        msg = "Review must score every declared dimension"
        raise VerificationError(msg)
    if review_record.overall(scores) != review["overall"]:
        msg = "Review overall score must be the mean of its dimensions"
        raise VerificationError(msg)
    if (
        review["overall"] < review_record.OVERALL_MINIMUM
        or min(scores.values()) < review_record.DIMENSION_MINIMUM
    ):
        msg = "Review scores are below the acceptance thresholds"
        raise VerificationError(msg)
    if refused := review_record.refused_findings(review["findings"]):
        msg = "Review records an unresolved " + "; ".join(refused)
        raise VerificationError(msg)
    problems = review_record.level_problems(review, scores, review["findings"])
    if problems:
        msg = "Review levels do not pass: " + "; ".join(problems)
        raise VerificationError(msg)
    problems = review_record.sentence_problems(review, review["findings"], edition)
    if problems:
        msg = "Review does not judge every sentence: " + "; ".join(problems)
        raise VerificationError(msg)
    report = production.review_report(path)
    if not report.is_file() or repository.sha(report) != review["report"]["sha256"]:
        msg = "Review report differs from its record"
        raise VerificationError(msg)
    return {
        "path": str(path.relative_to(repository.ROOT)),
        "reviewer": review["reviewer"],
        "overall": review["overall"],
        "minimum_dimension": min(scores.values()),
        **(
            {}
            if review_record.LEVELS is None
            else {"levels": {name: v["verdict"] for name, v in review["levels"].items()}}
        ),
        "human_listening": review["human_listening"],
    }


def verify_films(edition: production.Edition, files: list[Path], renditions: dict) -> dict:
    """Verify the films' media, up to `MEDIA_POOL` at the same time: each film's report in the
    order given, and the seconds each took. The first film in that order that is refused
    refuses, as it does in sequence."""

    def timed(path: Path) -> tuple[dict, float]:
        started = time.monotonic()
        report = verify_media(edition, path, renditions[path.name])
        return report, round(time.monotonic() - started, 1)

    with ThreadPoolExecutor(max_workers=MEDIA_POOL) as pool:
        verified = list(pool.map(timed, files))
    return {
        "media": [report for report, _ in verified],
        "media_seconds": {
            path.name: seconds for path, (_, seconds) in zip(files, verified, strict=True)
        },
    }


def verify_bindings(edition: production.Edition) -> dict:
    """The checks of an edition's bound inputs, which decode no film, as the report states them.

    The still scan of the 1080p captioned film is one of them: its requirement reads the scan's
    record, so every caller of this function asks it.
    """
    return {
        "sources": verify_sources(),
        "narration": verify_narration(edition),
        "picture": verify_picture(edition),
        "package": verify_package(edition),
        "still_scan": picture_still_scan.require_film_scan(edition),
    }


def qualify(
    edition: production.Edition, files: list[Path], *, technical_only: bool = False
) -> dict:
    """Verify one edition's four delivered films and their bound inputs."""
    renditions = {
        edition.film(kind).name: rendition for kind, rendition in production.RENDITIONS.items()
    }
    if sorted(path.name for path in files) != sorted(renditions) or any(
        path.parent != edition.artifacts for path in files
    ):
        msg = "An edition is verified as its four current delivered films"
        raise VerificationError(msg)
    report = {
        "verdict": "pass",
        "scope": "technical" if technical_only else "acceptance",
        "language": edition.code,
    }
    with durations.phase("bindings"):
        report |= verify_bindings(edition)
    with durations.phase("media"):
        report |= verify_films(edition, sorted(files), renditions)
    with durations.phase("spotlight"):
        report["spotlight"] = verify_spotlight(edition, sorted(files))
    report["review"] = (
        {"verdict": "not_reviewed"} if technical_only else verify_review(edition, sorted(files))
    )
    report["limits"] = (
        "Media, source and binding checks do not certify taste; human listening "
        "is recorded by the review, not inferred from these checks."
    )
    return report


# The owners' refusals that the command reports as "<language>: <reason>"; any other exception
# keeps its traceback.
REFUSALS = (
    VerificationError,
    production.UnassembledError,
    sources.SourceError,
    media.MediaError,
    picture_rendering.PictureError,
    narration_selection.SelectionError,
    narration_spoken_units.AlignmentError,
    narration_thought_groups.RetainedUtteranceError,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path)
    # The film-media gate passes this flag. Without it the one file the verifier writes is the
    # duration record of its run.
    parser.add_argument("--read-only", action="store_true", help="write no duration record")
    parser.add_argument("--technical-only", action="store_true")
    parser.add_argument("--language", choices=(*production.CODES, "all"), required=True)
    options = parser.parse_args(argv)
    codes = production.CODES if options.language == "all" else (options.language,)
    files = [path.resolve() for path in options.files] or [
        film for code in codes for film in production.Edition(code).films
    ]
    groups = edition_inputs(files) if options.language == "all" else {options.language: files}
    for language, members in groups.items():
        try:
            with durations.run(language, "verify", record=not options.read_only):
                report = qualify(
                    production.Edition(language), members, technical_only=options.technical_only
                )
        except REFUSALS as error:
            msg = f"{language}: {error}"
            raise SystemExit(msg) from None
        print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
