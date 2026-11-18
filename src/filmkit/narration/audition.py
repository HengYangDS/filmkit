"""Audition alternative takes of chosen thoughts and bind the selected seeds.

audition synthesizes each target thought's spoken text from the narration receipt at
seed + k * 7919, through the narration's own native ICL path and sampling
(`filmkit.narration.candidates`), and measures and judges each take as every take is
(`filmkit.narration.judgment`). A take qualifies when no line of that judgment refuses it:
its length, its ending, its phrase ends, its opening where it opens its recording, its
unmarked pauses, its declared terms, its units by reading and, where the film declares a line
for a single thought, its clarity. That is the one definition of an acceptable take, which
`filmkit.narration.judge` and `filmkit.narration.converge` hold too. Among qualified takes
one whose transcript contains the target's required phrase is proposed before one that does
not, and then the quietest ending or, with --prefer slower or brisker, the longest or the
shortest take; these order the qualified takes and qualify none. A take records its
differing units by unit beside those by reading. The
receipt, by default the one the cast declares, must hold each thought's current text, so
narrate edited segments first; its recordings, thoughts and narrator are checked before
any model loads. Takes and proposals are written under
build/runtime/work/auditions/<language>/; each take records its waveform's SHA-256,
because a rerun rewrites the take's file, and existing proposals are preserved.

A run-on target is narrated on into the thought that follows it in the film. The pinned
aligner locates the thought in each whole take, which is retained beside the take, and the
take is cut in the quiet before the next words (see run_on); a take without that quiet
does not qualify. Its proposal records the run-on that a retake binds with its seed.

apply binds each proposed seed into the cast's group retakes while the thought's
current text is still the auditioned text. The retake records that text's SHA-256, so
a later script edit releases it. Rows without a proposal are reported and left alone.

Usage: python -m filmkit.narration.audition audition
    --language zh|en --targets FILE [--takes 8] [--first 11]
    [--prefer accurate|slower|brisker] [--name audition] [--receipt FILE]
       python -m filmkit.narration.audition apply
    --language zh|en --proposals FILE [--dry-run]
The targets file maps "segment.index" to the phrase the transcript must contain, such
as {"12.3": "intended use"}, or to {"required": phrase, "run_on": true} for a run-on target.
Paths are relative to the repository root.
"""

import argparse
import json

import filmkit.narration.candidates as candidates
import filmkit.narration.group_generation as group_generation
import filmkit.narration.judgment as judgment
import filmkit.narration.terms as terms
import filmkit.repository as repository
from filmkit.film import FILM
from filmkit.narration.candidates import FIRST, bind
from filmkit.narration.judgment import load_aligner
from filmkit.narration.receipts import bound_records
from filmkit.narration.recognition import heard_phrase
from filmkit.narration.run_on import following_spoken_text
from filmkit.narration.transcription import load_asr
from filmkit.production import CODES, Edition

AUDITIONS = "build/runtime/work/auditions"
SUMMARY = (
    "seed",
    "failed",
    "opens_quiet",
    "clip_opens_quiet",
    "natural",
    "required_heard",
    "differing_units",
    "differing_units_by_reading",
    "seconds",
    "fluent",
    "terms_pass",
)


def propose(takes: list[dict], prefer: str = "accurate") -> int | None:
    """The seed of the best qualified take, or None when no take qualifies.

    A take qualifies when no line of the judgment refuses it (`judgment.judge`). Among the
    qualified, a take whose transcript holds the required phrase comes first, and then the
    preference decides.
    """
    qualified = [take for take in takes if not take["failed"]]
    if not qualified:
        return None
    tiebreak = {
        "accurate": lambda take: take["end_ratio"],
        "slower": lambda take: -take["seconds"],
        "brisker": lambda take: take["seconds"],
    }[prefer]
    return min(qualified, key=lambda take: (not take["required_heard"], tiebreak(take)))["seed"]


def audition(
    code: str,
    targets_file: str,
    receipt_file: str | None = None,
    *,
    takes: int = 8,
    first: int = FIRST,
    prefer: str = "accurate",
    name: str = "audition",
) -> None:
    """Synthesize, measure and transcribe takes of each target, then write proposals."""
    edition, folder = Edition(code), repository.ROOT / AUDITIONS / code
    proposals = folder / f"{name}.json"
    if proposals.exists():
        msg = f"Preserve the existing proposals: {proposals}"
        raise FileExistsError(msg)
    targets = _targets(targets_file)
    script, cast = repository.read(edition.script), repository.read(edition.cast)
    records = bound_records(
        receipt_file or cast["performance_recording"]["receipt"], edition.language
    )
    chosen = judgment.checked(script, cast, records, targets)
    run_ons = {
        (record["id"], child["index"]): following_spoken_text(records, record["id"], child["index"])
        for record, child, (_, run_on) in chosen
        if run_on
    }
    references = terms.receipt_references(code, FILM.narration.terms, records)
    model = group_generation.load_voice_model()
    asr = load_asr()
    aligner = load_aligner()
    bench = judgment.bench(code, references, asr=asr, aligner=aligner, film=FILM)
    held = judgment.held(code, script)
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for record, child, (phrase, _) in chosen:
        run_on = run_ons.get((record["id"], child["index"]))
        row = {
            "segment": record["id"],
            "index": child["index"],
            "text": child["text"],
            "spoken_text": child["spoken_text"],
            "required": phrase,
            "current_seed": child["seed"],
            "aligner": aligner["identity"],
            **({} if run_on is None else {"run_on": run_on}),
            "takes": [],
            "proposed_seed": None,
        }
        for k in range(first, first + takes):
            seed = candidates.seed_at(record, k)
            path = folder / f"{candidates.file_stem(record, child, seed)}.wav"
            thought = f"{record['id']}.{child['index']}"
            measured = candidates.taken(model, path, child, thought, seed, run_on, bench)
            take = {
                "seed": seed,
                **judgment.judge(measured, record["id"], child["index"], held),
                "required_heard": heard_phrase(measured["heard"], phrase),
            }
            row["takes"].append(take)
            stops = take["phrase_stops"]
            summary = {
                **{field: take[field] for field in SUMMARY},
                "phrase_stops": None if stops is None else len(stops),
            }
            print(
                json.dumps({"segment": row["segment"], "index": row["index"], **summary}),
                flush=True,
            )
        row["proposed_seed"] = propose(row["takes"], prefer)
        if run_on is not None:
            row["proposed_run_on"] = next(
                (take["run_on"] for take in row["takes"] if take["seed"] == row["proposed_seed"]),
                None,
            )
        rows.append(row)
    proposals.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    proposed = {f"{row['segment']}.{row['index']}": row["proposed_seed"] for row in rows}
    print(
        json.dumps(
            {"proposals": str(proposals.relative_to(repository.ROOT)), "proposed": proposed}
        ),
        flush=True,
    )


def _targets(targets_file: str) -> dict[tuple[str, int], tuple[str, bool]]:
    """The required phrase of each target thought and whether it is read on into the next.

    Targets are keyed by segment and 1-based index.
    """
    targets = {}
    for key, target in repository.read(targets_file).items():
        segment, index = key.split(".")
        if isinstance(target, str):
            targets[segment, int(index)] = (target, False)
        elif (
            isinstance(target, dict)
            and set(target) == {"required", "run_on"}
            and isinstance(target["required"], str)
            and target["run_on"] is True
        ):
            targets[segment, int(index)] = (target["required"], True)
        else:
            msg = f'{key}: a target is a phrase or {{"required": phrase, "run_on": true}}'
            raise ValueError(msg)
    return targets


def apply(code: str, proposals_file: str, *, dry_run: bool = False) -> dict:
    """Bind a proposals file into the edition's cast, writing it unless a dry run."""
    rows = json.loads((repository.ROOT / proposals_file).read_text())
    bound, skipped = bind(code, rows, dry_run=dry_run)
    return {"language": code, "applied": bound, "skipped": skipped, "dry_run": dry_run}


def main(argv: list[str] | None = None) -> None:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--language", choices=CODES, required=True)
    parser = argparse.ArgumentParser(
        description="Audition alternative takes and bind the selected seeds."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    trial = commands.add_parser(
        "audition", parents=[common], help="Synthesize, measure and rank takes"
    )
    trial.add_argument(
        "--targets",
        required=True,
        help='JSON file mapping "segment.index" to a required phrase',
    )
    trial.add_argument("--takes", type=int, default=8, help="Takes per thought")
    trial.add_argument("--first", type=int, default=FIRST, help="First seed multiple k")
    trial.add_argument(
        "--prefer",
        choices=("accurate", "slower", "brisker"),
        default="accurate",
        help="Break ties by the quietest ending, or by the longest or the shortest take",
    )
    trial.add_argument("--name", default="audition", help="Proposals file stem")
    trial.add_argument(
        "--receipt", help="Narration receipt holding the thoughts (default: the cast's)"
    )
    binding = commands.add_parser(
        "apply", parents=[common], help="Bind proposed seeds into the cast"
    )
    binding.add_argument("--proposals", required=True, help="Proposals JSON written by audition")
    binding.add_argument("--dry-run", action="store_true", help="Report without writing the cast")
    options = parser.parse_args(argv)
    if options.command == "audition":
        audition(
            options.language,
            options.targets,
            options.receipt,
            takes=options.takes,
            first=options.first,
            prefer=options.prefer,
            name=options.name,
        )
    else:
        print(json.dumps(apply(options.language, options.proposals, dry_run=options.dry_run)))


if __name__ == "__main__":
    main()
