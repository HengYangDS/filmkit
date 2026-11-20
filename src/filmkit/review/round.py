"""Prepare and record one independent review round of both editions.

A round sets the packages of the previous build aside before the next render
(`filmkit.review.set_aside`), prepares its directory, build/evidence/reviews/round-<n>/, with
one command, and records the finished reviews as the production reviews that
`filmkit.delivery.verification` accepts.

`prepare` writes what the round's reviewers read: the binding of the members a delivery would
hold and the real-browser readback of their players (`filmkit.delivery.folder`), the listening
plan (`filmkit.review.listening_plan`), the measurements (`filmkit.review.measurement`), the
changes note and the dispositions it was given, and each edition's sentences and reviewer prompt
with the exact media hashes and the previous round's findings with the disposition of each, or
the statement that the round is the first (`filmkit.review.prompts`). It checks what it reads
before it derives anything, writes the note and the dispositions first and the prompts last,
and prepares a round again only while the round holds nothing but a preparation.

Setting aside and recording are planned and checked in full before anything moves or is written,
and --dry-run stops after the plan. A refused input raises `ReviewError`, which each command
reports as its refusal in one line. `prepare` reports the same way the refusals of the owners
it asks (`OWNER_REFUSALS`); a fault, such as a tool's failed process or a missing record of the
engine's own, is not caught and shows in full.

A reviewed round's packages are set aside by the round's reviews; an unreviewed build's, such as
a preview the owner watched, with --unreviewed by the consumer folder that holds its films, under
the round's label or one given with --label. --language limits a set-aside to one edition, and
--without-picture leaves the rendered pictures in place, for the editions it names or for both.

Usage: python -m filmkit.review.round set-aside --round <n> --purpose <text>
           [--review-dir <dir>] [--language zh|en] [--without-picture [zh|en ...]] [--dry-run]
       python -m filmkit.review.round set-aside --unreviewed --consumer <dir>
           (--round <n> | --label <label>) --purpose <text>
           [--language zh|en] [--without-picture [zh|en ...]] [--dry-run]
       python -m filmkit.review.round prepare --round <n>
           [--previous <dir> --dispositions <file>] [--changes <file>]
       python -m filmkit.review.round record --round-dir <dir> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

import filmkit.delivery.folder as delivery_folder
import filmkit.media as media
import filmkit.repository as repository
import filmkit.review.listening_plan as review_listening_plan
import filmkit.review.measurement as review_measurement
import filmkit.review.prompts as round_prompts
import filmkit.review.record as review_record
import filmkit.review.set_aside as set_aside
import filmkit.soundtrack.level as soundtrack_level
import filmkit.sources as sources
import filmkit.tools as tools
from filmkit.film import MATERIAL
from filmkit.narration.spoken_units import AlignmentError
from filmkit.picture.errors import PictureError
from filmkit.picture.rendering import COMPOSITION_SCRIPT
from filmkit.production import CODES, Edition, review_report
from filmkit.review import ReviewError
from filmkit.review.files import edition_review, present, review_files, round_directory
from filmkit.review.record import DIMENSIONS, SCHEMA_VERSION, overall

# The round's files that a preparation names besides those the prompts name and write
# (`filmkit.review.prompts`): the players' readback and the copies of the changes note and the
# dispositions. The screenshots that the player check writes beside the readback are named by
# the check alone, and the round reads their names from the readback (`listed_screenshots`).
READBACK = "player-check.json"
CHANGES, DISPOSITIONS = "changes.md", "dispositions.json"
# The classes by which the owners a preparation asks refuse. `prepare` reports an exception of
# one of them as the round's refusal in one line, and catches no other: any other exception is
# a fault and shows in full. So this tuple is where a new owner's refusal is admitted.
OWNER_REFUSALS = (
    delivery_folder.DeliveryRefusedError,
    tools.ToolError,
    PictureError,
    media.MediaError,
    soundtrack_level.LevelError,
    AlignmentError,
    sources.SourceError,
)

HUMAN_LISTENING = (
    "Audio is scored from automated evidence: recognition, word timings, rate, the "
    "pause hierarchy, quiet edges, thought levels, endings and waveforms. Human "
    "listening is a separate acceptance after delivery and does not affect the scores."
)


class ProductionReview(NamedTuple):
    """One edition's production review record, its place and the report it copies."""

    target: Path
    report: Path
    record: dict


def listed_screenshots(round_dir: Path) -> list[str]:
    """The names of the files that the round's readback lists as its screenshots, that lie in
    the round's directory and that hold the bytes the readback lists.

    The readback is the one statement of what the player check wrote beside it, so the round
    states no screenshot's name of its own. A round without a readback, a readback that is no
    JSON and one that lists no screenshot name none. A listed file that lies elsewhere is not
    the round's, and one whose SHA-256 is not the listed one is not the file the check wrote:
    neither is a preparation's, so a readback that lists another file of the round, by hand or
    by fault, has nothing removed. A readback of another shape, whose `screenshots` is no list
    of entries that each hold a `path` and a `sha256`, is a fault of the engine's own record
    and shows with its traceback.
    """
    readback = repository.read_entry(round_dir / READBACK, ("screenshots",))
    listed = [
        (Path(shot["path"]), shot["sha256"]) for shot in (readback or {}).get("screenshots") or ()
    ]
    return [
        path.name
        for path, sha256 in listed
        if delivery_folder.same_folder(path.parent, round_dir)
        and path.is_file()
        and repository.sha(path) == sha256
    ]


def prepared_names(round_dir: Path) -> list[str]:
    """The name of every file of a preparation in a round's directory: the names the round
    itself gives, whether a given run writes them or not, and the screenshots its readback
    lists (`listed_screenshots`)."""
    each = (round_prompts.SENTENCES, round_prompts.PROMPT)
    return [
        *round_prompts.ROUND_INPUTS,
        READBACK,
        CHANGES,
        DISPOSITIONS,
        *(name.format(code=code) for code in CODES for name in each),
        *listed_screenshots(round_dir),
    ]


def given(path: Path | None) -> bytes | None:
    """The bytes of a file the caller names, refused when it is missing; None when none is
    named."""
    return None if path is None else present([path])[0].read_bytes()


def refuse_more_than_a_preparation(number: int, round_dir: Path) -> None:
    """Refuse a round that holds an entry a preparation does not write, and one whose label
    holds set-aside films.

    A review, a reviewer's working folder or any other entry says that the round is under way:
    preparing it again would change what its reviewers read. An entry that bears a prepared
    file's name and is no file, a folder for one, is such an entry too, and so is an image that
    the round's readback does not list (`prepared_names`). A set-aside under the round's label
    moved the films its prompts named, so the films in place are another build's and the label
    is taken: they are the next round's. Finder's `.DS_Store` is no entry, as in a delivery.
    """
    written = {*prepared_names(round_dir), delivery_folder.FINDER_METADATA}
    held = sorted(round_dir.iterdir()) if round_dir.is_dir() else []
    others = [entry.name for entry in held if entry.name not in written or not entry.is_file()]
    if others:
        msg = (
            f"{repository.relative(round_dir)} holds {', '.join(others)}, which a preparation "
            "does not write; a round is prepared again only while it holds nothing else"
        )
        raise ReviewError(msg)
    aside = repository.ROOT / set_aside.SUPERSEDED / set_aside.round_label(number)
    if aside.exists():
        msg = (
            f"the films of round {number} were set aside under its label, "
            f"{repository.relative(aside)}; prepare round {number + 1}"
        )
        raise ReviewError(msg)


def prepare(
    number: int,
    previous: Path | None = None,
    changes: Path | None = None,
    dispositions: Path | None = None,
) -> dict:
    """Prepare a round: write everything its reviewers read into its directory.

    What only reads comes first, so that a refusal there changes no file and leaves a round
    without a directory as it was. A round's number is 0 or more (`round_directory`). The
    changes note and the dispositions are read, since either may be the round's own copy of an
    earlier preparation. Then everything the prompts read is read and checked
    (`filmkit.review.prompts.read_round`): the template's fields, each edition's passing still
    scan, the previous round's reviews, reports and dispositions, a dispositions file that is no
    JSON being refused by name, the note's text, the program levels and each edition's
    timeline. Then the films and the other members a delivery would hold, and the round itself
    (`refuse_more_than_a_preparation`).

    Every file of an earlier preparation is then removed (`prepared_names`), and the round is
    written in this order: the copies of the note and the dispositions from what was read, the
    binding of the delivery's members, the listening plan, the measurements, the real-browser
    readback of the members' players with its screenshots, and each edition's sentences and
    prompt. The copies come first: they may be the only ones, so they are back before anything
    that can refuse. The measurements come before the browser starts, so what they refuse is
    known first. The prompts come last: a round without prompts binds no film and starts no
    reviewer, so a preparation that stops leaves nothing that can be taken for a round.
    """
    round_dir = round_directory(number)
    copies = {CHANGES: given(changes), DISPOSITIONS: given(dispositions)}
    round_prompts.read_round(previous, round_dir, changes, dispositions)
    members = delivery_folder.plan(repository.ROOT)
    present([source for source, _ in members])
    refuse_more_than_a_preparation(number, round_dir)
    for name in prepared_names(round_dir):
        (round_dir / name).unlink(missing_ok=True)
    kept = {name: round_dir / name for name, body in copies.items() if body is not None}
    for name, copy in kept.items():
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(copies[name])
    binding = delivery_folder.bind_players(
        repository.ROOT, members, round_dir / round_prompts.BINDING
    )
    review_listening_plan.listening_plan(round_dir / round_prompts.LISTENING_PLAN)
    review_measurement.write(round_dir / round_prompts.MEASUREMENTS)
    delivery_folder.read_bound_players(repository.ROOT, binding, round_dir / READBACK, outcome="")
    written = round_prompts.prompts(previous, round_dir, kept.get(CHANGES), kept.get(DISPOSITIONS))
    return {"round": repository.relative(round_dir), "members": len(members), **written}


def reviewed_scores(code: str, review: dict) -> dict:
    """A review's scores in record order, which must be exactly the declared dimensions.

    The record derives its overall from them (`filmkit.review.record.overall`); an overall
    that the review states is neither required nor compared.
    """
    if set(review.get("scores", {})) != set(DIMENSIONS):
        msg = f"{code}: a review scores exactly the declared dimensions"
        raise ReviewError(msg)
    return {name: review["scores"][name] for name in DIMENSIONS}


def review_records(round_dir: Path) -> list[ProductionReview]:
    """Each edition's production review record from a finished round, checked, not written.

    Reads each edition's review and report from the round directory (`review_files`) and derives
    the schema 2 record that the film verifier accepts beside a copy of the report: the
    exact reviewed media, script and composition hashes, the declared scores and the
    overall derived from them, every finding and the human-listening state. Both reviews must
    cover the current delivered films and score exactly the declared dimensions.
    For a film that declares review levels, the record carries each level's verdict and each
    sentence's, and a review whose levels do not pass or that leaves a sentence unjudged is
    refused (`filmkit.review.record`). For a film that declares the severities a review may
    hold, a review with a finding of any other severity or of none is refused, by the finding's
    id and severity; a film that does not declare them records its review whatever its findings,
    and the verifier judges them.
    """
    records = []
    for code in CODES:
        edition = Edition(code)
        source, report = present(list(review_files(round_dir, code)))
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
        if review_record.ACCEPTED_SEVERITIES is not None and (
            refused := review_record.refused_findings(entry["findings"])
        ):
            msg = f"{code}: the review holds what the film does not accept: " + "; ".join(refused)
            raise ReviewError(msg)
        problems = review_record.level_problems(entry, scores, entry["findings"])
        if problems:
            msg = f"{code}: the review's levels do not pass: " + "; ".join(problems)
            raise ReviewError(msg)
        problems = review_record.sentence_problems(entry, entry["findings"], edition)
        if problems:
            msg = f"{code}: the review does not judge every sentence: " + "; ".join(problems)
            raise ReviewError(msg)
        judged = (
            {}
            if review_record.LEVELS is None
            else {"levels": entry["levels"], "sentences": entry["sentences"]}
        )
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
            **judged,
            "human_listening": {
                "state": "not_performed",
                "basis": HUMAN_LISTENING,
                "checklist": entry.get("human_listening_checklist", []),
            },
            "report": {
                "path": repository.relative(review_report(target)),
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
        shutil.copyfile(review.report, review_report(review.target))
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
                "material": sum(f.get("severity") == MATERIAL for f in review.record["findings"]),
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


def run_prepare(options: argparse.Namespace) -> dict:
    try:
        return prepare(
            options.round,
            options.previous.resolve() if options.previous else None,
            options.changes.resolve() if options.changes else None,
            options.dispositions.resolve() if options.dispositions else None,
        )
    except OWNER_REFUSALS as error:
        # An owner's refusal is the round's, in one line whatever lines its own words hold.
        raise ReviewError(" ".join(str(error).split())) from error


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
        help="the folder whose <edition>/ holds each edition's films byte-identical",
    )
    aside.add_argument("--language", choices=CODES, help="set aside this edition only")
    aside.add_argument(
        "--without-picture",
        nargs="*",
        choices=CODES,
        metavar="CODE",
        help="leave the rendered pictures in place, for the editions named or for every edition",
    )
    aside.add_argument("--dry-run", action="store_true", help="plan without moving anything")
    aside.set_defaults(run=run_set_aside)


def command_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    set_aside_options(
        commands.add_parser("set-aside", help="move the previous build's packages aside")
    )
    prompt = commands.add_parser(
        "prepare", help="write the round's directory: its inputs, its readback and its prompts"
    )
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
        help="Markdown context bullets: the repairs since the previous review; kept in the round",
    )
    prompt.add_argument(
        "--dispositions",
        type=Path,
        metavar="FILE",
        help="the disposition of each finding of the previous round, as JSON; with --previous",
    )
    prompt.set_defaults(run=run_prepare)
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
