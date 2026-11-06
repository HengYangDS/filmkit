"""Prepare and record one independent review round of both editions.

A round sets the packages of the previous build aside before the next render
(`filmkit.review.set_aside`), binds the packaged members for the real-browser player check,
writes each edition's reviewer prompt with the exact media hashes and the previous round's
findings with the disposition of each, or states that the round is the first
(`filmkit.review.prompts`), and records the finished reviews as the production reviews that
`filmkit.delivery.verification` accepts. A round's directory defaults to
build/evidence/reviews/round-<n>/. Setting aside and recording are planned and checked in full
before anything moves or is written, and --dry-run stops after the plan. A refused input raises
`ReviewError`, which each command reports as its refusal.

A reviewed round's packages are set aside by the round's reviews; an unreviewed build's, such as
a preview the owner watched, with --unreviewed by the consumer folder that holds its films, under
the round's label or one given with --label. --language limits a set-aside to one edition, and
--without-picture leaves the rendered picture in place, for the editions it names or for both.

Usage: python -m filmkit.review.round set-aside --round <n> --purpose <text>
           [--review-dir <dir>] [--language zh|en] [--without-picture [zh|en ...]] [--dry-run]
       python -m filmkit.review.round set-aside --unreviewed --consumer <dir>
           (--round <n> | --label <label>) --purpose <text>
           [--language zh|en] [--without-picture [zh|en ...]] [--dry-run]
       python -m filmkit.review.round bind --out <file>
       python -m filmkit.review.round prompts --round <n>
           [--previous <dir> --dispositions <file>] [--changes <file>] [--out-dir <dir>]
       python -m filmkit.review.round record --round-dir <dir> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

import filmkit.repository as repository
import filmkit.review.prompts as round_prompts
import filmkit.review.set_aside as set_aside
from filmkit.delivery.packaging import BOUND_FILM
from filmkit.picture.rendering import COMPOSITION_SCRIPT
from filmkit.production import CODES, Edition
from filmkit.review import ReviewError
from filmkit.review.files import edition_review, present, round_directory
from filmkit.review.record import DIMENSIONS, SCHEMA_VERSION, overall

HUMAN_LISTENING = (
    "Audio is scored from automated evidence: recognition, word timings, rate, the "
    "pause hierarchy, quiet edges, thought levels, endings and waveforms. Human "
    "listening is a separate acceptance after delivery and does not affect the scores."
)
# A reported overall score may differ from the mean of its scores by this much rounding.
OVERALL_ROUNDING = 0.05


class ProductionReview(NamedTuple):
    """One edition's production review record, its place and the report it copies."""

    target: Path
    report: Path
    record: dict


def bind(out: Path) -> dict:
    """Bind the packaged delivery members for the real-browser player check.

    The members are the neutral language entry and, for each edition, its two films and
    the viewing package its package record names. Writes the destination, the film's file
    prefix and duration, and each member's path and SHA-256, the shape the player check reads.
    """
    destination = repository.ROOT / "build/artifacts/film"
    paths = ["index.html"]
    for code in CODES:
        edition = Edition(code)
        viewing = repository.read(present([edition.viewing_package])[0])
        paths += [f"{code}/{film.name}" for film in edition.films]
        paths += [f"{code}/{member['path']}" for member in viewing["members"]]
    present([destination / path for path in paths])
    members = [{"path": path, "sha256": repository.sha(destination / path)} for path in paths]
    repository.write(
        out, {"destination": str(destination), "film": dict(BOUND_FILM), "members": members}
    )
    return {"members": len(members), "binding": repository.relative(out)}


def reviewed_scores(code: str, review: dict) -> dict:
    """A review's scores in record order.

    They must be exactly the declared dimensions, and the review must report their mean
    as its overall score.
    """
    if set(review.get("scores", {})) != set(DIMENSIONS):
        msg = f"{code}: a review scores exactly the declared dimensions"
        raise ReviewError(msg)
    scores = {name: review["scores"][name] for name in DIMENSIONS}
    mean, reported = overall(scores), review.get("overall")
    if not isinstance(reported, int | float) or isinstance(reported, bool):
        msg = f"{code}: a review reports its overall score"
        raise ReviewError(msg)
    if abs(reported - mean) > OVERALL_ROUNDING:
        msg = f"{code}: reported overall {reported} is not the mean {mean}"
        raise ReviewError(msg)
    return scores


def review_records(round_dir: Path) -> list[ProductionReview]:
    """Each edition's production review record from a finished round, checked, not written.

    Reads review-<code>.json and <code>-review.md from the round directory and derives
    the schema 2 record that the film verifier accepts beside a copy of the report: the
    exact reviewed media, script and composition hashes, the declared scores and their
    mean, every finding and the human-listening state. Both reviews must cover the
    current delivered films, score exactly the declared dimensions and report their mean.
    """
    records = []
    for code in CODES:
        edition = Edition(code)
        source, report = present(
            [round_dir / f"review-{code}.json", round_dir / f"{code}-review.md"]
        )
        review, entry = edition_review(source, code)
        current = {
            repository.relative(film): repository.sha(film) for film in present(edition.films)
        }
        reviewed = {
            repository.relative(repository.ROOT / item["path"]): item["sha256"]
            for item in entry.get("media", [])
        }
        if reviewed != current:
            msg = f"{code}: reviewed media differ from the current delivered films"
            raise ReviewError(msg)
        scores = reviewed_scores(code, entry)
        target = edition.production_review
        record = {
            "schema_version": SCHEMA_VERSION,
            "language": code,
            "reviewer": review["reviewer"],
            "recorded_at": datetime.now(UTC).isoformat(),
            "media": [{"path": path, "sha256": sha} for path, sha in sorted(current.items())],
            "script_sha256": repository.sha(edition.script),
            "composition_sha256": repository.sha(repository.ROOT / COMPOSITION_SCRIPT),
            "scores": scores,
            "overall": overall(scores),
            "findings": entry["findings"],
            "human_listening": {
                "state": "not_performed",
                "basis": HUMAN_LISTENING,
                "checklist": entry.get("human_listening_checklist", []),
            },
            "report": {
                "path": repository.relative(target.with_name("production-review.md")),
                "sha256": repository.sha(report),
            },
            "source_review": {
                "path": repository.relative(source),
                "sha256": repository.sha(source),
            },
        }
        records.append(ProductionReview(target, report, record))
    return records


def write_review_records(records: list[ProductionReview]) -> None:
    """Write each production review record beside a copy of its report."""
    for review in records:
        review.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(review.report, review.target.with_name("production-review.md"))
        repository.write(review.target, review.record)


def record_report(records: list[ProductionReview], *, dry_run: bool) -> dict:
    """Each edition's recorded overall, lowest score and material findings, as printed."""
    return {
        "dry_run": dry_run,
        "editions": [
            {
                "language": review.record["language"],
                "overall": review.record["overall"],
                "minimum": min(review.record["scores"].values()),
                "material": sum(f.get("severity") == "material" for f in review.record["findings"]),
            }
            for review in records
        ],
    }


def run_set_aside(options: argparse.Namespace) -> dict:
    codes = CODES if options.language is None else (options.language,)
    kept = codes if options.without_picture == [] else tuple(options.without_picture or ())
    pictures = tuple(code for code in codes if code not in kept)
    if options.unreviewed:
        if options.consumer is None or options.review_dir is not None:
            msg = "an unreviewed set-aside names its --consumer and reads no reviews"
            raise ReviewError(msg)
        label = options.label or set_aside.round_label(options.round)
        plans = set_aside.plan_unreviewed(
            label, options.purpose, options.consumer.resolve(), codes=codes, pictures=pictures
        )
    else:
        if options.round is None or options.consumer is not None:
            msg = "a reviewed set-aside names its --round and no consumer; see --unreviewed"
            raise ReviewError(msg)
        review_dir = (options.review_dir or round_directory(options.round)).resolve()
        plans = set_aside.plan_set_aside(
            options.round, options.purpose, review_dir, codes=codes, pictures=pictures
        )
    if not options.dry_run:
        set_aside.move_aside(plans)
    return set_aside.set_aside_report(plans, dry_run=options.dry_run)


def run_bind(options: argparse.Namespace) -> dict:
    return bind(options.out.resolve())


def run_prompts(options: argparse.Namespace) -> dict:
    return round_prompts.prompts(
        options.previous.resolve() if options.previous else None,
        (options.out_dir or round_directory(options.round)).resolve(),
        options.changes.resolve() if options.changes else None,
        options.dispositions.resolve() if options.dispositions else None,
    )


def run_record(options: argparse.Namespace) -> dict:
    records = review_records(options.round_dir.resolve())
    if not options.dry_run:
        write_review_records(records)
    return record_report(records, dry_run=options.dry_run)


def set_aside_options(aside: argparse.ArgumentParser) -> None:
    label = aside.add_mutually_exclusive_group(required=True)
    label.add_argument("--round", type=int, metavar="N", help="the round, labelled round-N")
    label.add_argument(
        "--label", metavar="NAME", help="an unreviewed build's own label, in lowercase words"
    )
    aside.add_argument(
        "--purpose",
        required=True,
        metavar="TEXT",
        help="why the packages are superseded, recorded in each manifest",
    )
    aside.add_argument(
        "--review-dir",
        type=Path,
        metavar="DIR",
        help="the round's reviews (default build/evidence/reviews/round-N)",
    )
    aside.add_argument(
        "--unreviewed",
        action="store_true",
        help="set aside a build nobody reviewed, bound by the copies --consumer holds",
    )
    aside.add_argument(
        "--consumer",
        type=Path,
        metavar="DIR",
        help="the folder whose <edition>/ holds each edition's two films byte-identical",
    )
    aside.add_argument("--language", choices=CODES, help="set aside this edition only")
    aside.add_argument(
        "--without-picture",
        nargs="*",
        choices=CODES,
        metavar="CODE",
        help="leave the rendered picture in place, for the editions named or for every edition",
    )
    aside.add_argument("--dry-run", action="store_true", help="plan without moving anything")
    aside.set_defaults(run=run_set_aside)


def command_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    set_aside_options(
        commands.add_parser("set-aside", help="move the previous build's packages aside")
    )
    binding = commands.add_parser("bind", help="bind the packaged members for the player check")
    binding.add_argument("--out", type=Path, required=True, metavar="FILE")
    binding.set_defaults(run=run_bind)
    prompt = commands.add_parser("prompts", help="write the round's reviewer prompts")
    prompt.add_argument("--round", type=int, required=True, metavar="N")
    prompt.add_argument(
        "--previous",
        type=Path,
        metavar="DIR",
        help="the previous round's review directory; without it the round is the first",
    )
    prompt.add_argument(
        "--changes",
        type=Path,
        metavar="FILE",
        help="Markdown context bullets: the repairs since the previous review",
    )
    prompt.add_argument(
        "--dispositions",
        type=Path,
        metavar="FILE",
        help="the disposition of each finding of the previous round, as JSON; with --previous",
    )
    prompt.add_argument(
        "--out-dir",
        type=Path,
        metavar="DIR",
        help="the round's directory (default build/evidence/reviews/round-N)",
    )
    prompt.set_defaults(run=run_prompts)
    recorder = commands.add_parser(
        "record", help="record the round's reviews as production reviews"
    )
    recorder.add_argument("--round-dir", type=Path, required=True, metavar="DIR")
    recorder.add_argument("--dry-run", action="store_true", help="check without writing")
    recorder.set_defaults(run=run_record)
    return parser


def main(argv: list[str] | None = None) -> None:
    options = command_parser().parse_args(argv)
    try:
        result = options.run(options)
    except ReviewError as error:
        msg = f"{options.command}: {error}"
        raise SystemExit(msg) from None
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
