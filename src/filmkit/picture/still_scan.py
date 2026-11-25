"""Still pictures in a rendered film, measured as the independent reviewers measure them.

The film is decoded at 10 fps to 480x270 grey. A frame is still when at most 12 pixels of
the content band, rows 30-225, change by more than 24 levels from the frame before; the
coarser measure compares frames 0.2 s apart and calls a pair still when under 0.05 % of
the band changes that much. Each run of still frames is reported with the speech it
carries, from the timeline's aligned words. A 10 fps sample can land either side of a mark
that moves for one frame, so the film is read at two phases, 0.05 s apart, and the worse reading
decides; one decode gives both phases their frames (`decode`, `phase_reports`). The
specification allows no still picture with 3.5 s of speech or more; a run's speech is recorded
cut to whole hundredths, so the recorded figure stands at the limit exactly when the measured
one does.

A record names the film, the timeline and the composition script it judged, the composition as
it stands when the scan runs, each with its SHA-256, the rules it was written under (`rules`)
and the frames each phase read. A film or a timeline that changes while it is scanned is
refused, and so is a film, a timeline or an answer of ffprobe that cannot be read, by its name.

Both records of an edition are read by one reader (`filmkit.picture.still_record.answer`),
which answers only from a record that has the scan's shape, binds what stands, states the
engine's own rules, read the whole film and agrees with itself.

The final film's scan decides. `scan_film`, the action `scan-film` of `filmkit.produce`, scans
the edition's 1080p captioned film against its timeline into the edition's film record
(`Edition.film_stills`), which also names the engine that scanned. `film_record` reads it for
the film, the timeline, the composition and the engine as they stand; `scan-film` scans again
whenever it does not answer, so the command a refusal names repairs any record.
`require_film_scan` is the one owner of whether an edition passes: the delivery's verification,
the delivery and a review round's preparation call it, and it refuses an edition whose record
does not answer, saying why and naming `scan-film`, or whose film holds a still run at the
limit. A record that answers is not decoded again.

A draft's scan is an early warning and settles nothing about the film. A draft is drawn at half
the size the film's picture is drawn at, and text is set on whole pixels of the size it is drawn
at, so a label can step by one pixel in a draft where the film holds it still, and the draft
then ends a still run that the film holds whole. With --language the timeline is the edition's
and the record is its draft's (`Edition.draft_stills`), which `filmkit.preflight` requires, of a
film that declares drafts, before a render (`draft_record`: the same reader, for the timeline
and the composition as they stand); `record_draft` writes it, for this command and for
`filmkit.picture.draft`, of a draft that decodes to its timeline's seconds.

What the scan cannot read is its command's refusal, in one line, and no error of its own.

Usage: python -m filmkit.picture.still_scan <movie> --language <code> [--limit <seconds>]
       python -m filmkit.picture.still_scan <movie> <timeline> --out <record> [--limit <seconds>]
       python -m filmkit.produce scan-film --language <code>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from errno import ENOENT
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

import filmkit.graph.runs as seam
import filmkit.picture.still_record as still_record
import filmkit.released as released
import filmkit.repository as repository
from filmkit.picture.errors import PictureError
from filmkit.picture.rendering import COMPOSITION_SCRIPT
from filmkit.picture.still_record import NoAnswerError
from filmkit.production import CODES, Edition, UnassembledError

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

FPS, WIDTH, HEIGHT = 10, 480, 270
# Sixty-fps frames into each 0.1 s sample at which the two phases are read.
PHASES = (0, 3)
BAND = slice(30, 226)
LEVEL = 24
FINE_PIXELS = 12
COARSE_SHARE = 0.0005
# Runs that carry less speech than this are left out of the report.
REPORTED_SPEECH_SECONDS = 1.0
LIMIT_SECONDS = 3.5
# The delivered film whose scan decides for its edition (`production.RENDITIONS`): the viewing
# film with its captions, the one a review watches. The action that scans it.
SCANNED_FILM = "1080p-captioned"
SCAN_ACTION = "scan-film"
FINE_RULE = f"at most {FINE_PIXELS} band pixels change by more than {LEVEL} levels in 0.1 s"
COARSE_RULE = f"under {COARSE_SHARE:.2%} of the band changes by more than {LEVEL} levels in 0.2 s"
# What the decode does to each frame it keeps, as FFmpeg is given it, and how a run's speech is
# recorded: a reading depends on both, so a record states them.
DECODE = f"scale={WIDTH}:{HEIGHT}:flags=area,format=gray"
SPEECH = "cut to whole hundredths of a second"
# The files a record binds, by the names it binds them under.
SUBJECTS = ("movie", "timeline", "composition")


def rules(limit: float = LIMIT_SECONDS) -> dict:
    """The rules a scan is made under, as its record states them: the scan's constants, the
    filters of its decode and the cut of a run's speech. A reader compares them with the
    engine's own, so a record of other rules never answers. What the scan's code does beyond
    them (which frames the coarse measure keys on, where a run begins and ends) no rule states:
    the engine's version, which a film record binds, stands for it."""
    return {
        "fps": FPS,
        "size": [WIDTH, HEIGHT],
        "band": [BAND.start, BAND.stop],
        "phases": list(PHASES),
        "decode": DECODE,
        "fine": FINE_RULE,
        "coarse": COARSE_RULE,
        "coarse_share": COARSE_SHARE,
        "reported_speech_seconds": REPORTED_SPEECH_SECONDS,
        "speech": SPEECH,
        "limit_seconds": limit,
    }


class StillScanError(RuntimeError):
    """The film could not be read, so the scan has not judged it."""


def cut(seconds: float) -> float:
    """Seconds cut to whole hundredths, the float's noise under a microsecond rounded off first:
    a limit is stated in hundredths, so the cut figure stands at it exactly when `seconds` does."""
    return round(seconds * 1_000_000) // 10_000 / 100


def runs(still: list[bool], step: float) -> list[tuple[float, float]]:
    """Each run of still frames, from the frame before its first to its last, in seconds."""
    found, start = [], None
    for i, flag in enumerate(still):
        if flag and start is None and i:
            start = (i - 1) * step
        if not flag and start is not None:
            found.append((start, (i - 1) * step))
            start = None
    if start is not None:
        found.append((start, (len(still) - 1) * step))
    return found


def aligned(timeline: object) -> np.ndarray:
    """A timeline's aligned words as rows of their start and end in seconds."""
    try:
        spans = [(w["start"], w["end"]) for s in timeline["segments"] for w in s["words"]]
    except (KeyError, TypeError) as error:
        msg = "The timeline's aligned words stand in no form the scan reads"
        raise StillScanError(msg) from error
    if not all(still_record.number(second) for span in spans for second in span):
        msg = "The timeline states a word whose start or end is no time"
        raise StillScanError(msg)
    return np.array(spans, dtype=float).reshape(-1, 2)


def speech(words: np.ndarray, start: float, end: float) -> float:
    """Seconds of aligned speech between `start` and `end`, at most the seconds between them:
    words that overlap in a timeline do not make a run carry more speech than it lasts, which a
    record's reader would refuse (`still_record.runs`)."""
    if not len(words):
        return 0.0
    within = np.clip(np.minimum(words[:, 1], end) - np.maximum(words[:, 0], start), 0, None)
    return min(float(within.sum()), end - start)


class Stills:
    """Both measures' still flags over grey frames at FPS, taken a frame at a time, so that the
    frames of several phases can come from one decode."""

    def __init__(self) -> None:
        self.fine, self.coarse, self.count = [False], [False], 0
        self.previous = self.key = None

    def add(self, frame: np.ndarray) -> None:
        band = frame[BAND].astype(np.int16)
        if self.previous is not None:
            self.fine.append(int((np.abs(band - self.previous) > LEVEL).sum()) <= FINE_PIXELS)
        if self.count % 2 == 0:
            if self.key is not None:
                self.coarse.append(float((np.abs(band - self.key) > LEVEL).mean()) < COARSE_SHARE)
            self.key = band
        self.previous, self.count = band, self.count + 1


def scan(frames: Iterable[np.ndarray], timeline: dict) -> dict:
    """Both measures over grey frames at FPS: each still run with the speech it carries."""
    stills = Stills()
    for frame in frames:
        stills.add(frame)
    return reported(stills, timeline)


def reported(stills: Stills, timeline: dict) -> dict:
    """What a scan reports of the frames it took: each still run with the speech it carries."""
    fine, coarse = stills.fine, stills.coarse
    if not stills.count:
        msg = "The scan read no frames, so it cannot judge the film"
        raise StillScanError(msg)
    words = aligned(timeline)

    def report(still: list[bool], step: float) -> list[dict]:
        found = [(a, b, speech(words, a, b)) for a, b in runs(still, step)]
        return [
            {"start": round(a, 2), "end": round(b, 2), "speech": cut(s)}
            for a, b, s in found
            if s >= REPORTED_SPEECH_SECONDS
        ]

    fine_runs = report(fine, 1 / FPS)
    return {
        "fps": FPS,
        "frames": len(fine),
        "fine": {
            "rule": FINE_RULE,
            "runs": fine_runs,
        },
        "coarse": {
            "rule": COARSE_RULE,
            "runs": report(coarse, 2 / FPS),
        },
        "longest_fine_speech": max((run["speech"] for run in fine_runs), default=0),
    }


def worst(reports: list[dict]) -> dict:
    """The phase whose fine measure finds the most speech over a still picture, with the frames
    each phase read."""
    chosen = max(reports, key=lambda report: report["longest_fine_speech"])
    return {**chosen, "phases": len(reports), "phase_frames": [r["frames"] for r in reports]}


def over_limit(report: dict, limit: float = LIMIT_SECONDS) -> list[dict]:
    """The fine measure's still runs that carry at least `limit` seconds of speech."""
    return still_record.at_limit(report["fine"]["runs"], limit)


def still_pictures(found: list[dict]) -> str:
    """Still runs as a refusal names them, each with its time and its speech."""
    return "; ".join(
        f"{run['start']:.2f}-{run['end']:.2f} s with {run['speech']:.2f} s of speech"
        for run in found
    )


def limit_words(limit: float = LIMIT_SECONDS) -> str:
    """The limit in its one wording, which the scan's refusal, a draft's and the pre-render
    check's answer name it by: the speech that no still picture may carry."""
    return f"{limit} s of speech or more"


def frame_rate(movie: Path) -> int:
    """The movie's video frame rate, which must be a whole multiple of FPS."""
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=r_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(movie),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    numerator, _, denominator = probe.stdout.strip().partition("/")
    named = repository.relative(repository.ROOT / movie)
    if probe.returncode or not (numerator.isdigit() and (denominator or "1").isdigit()):
        msg = f"FFmpeg read no frames from {named} (ffprobe exit {probe.returncode})"
        raise StillScanError(msg)
    rate = int(numerator) / int(denominator or 1) if int(denominator or 1) else 0
    if rate <= 0 or rate != round(rate) or round(rate) % FPS:
        msg = f"{named} runs at {rate:g} fps, not a whole multiple of {FPS} above none"
        raise StillScanError(msg)
    return round(rate)


def sampling(every: int, phases: tuple[int, ...]) -> str:
    """The frames a decode keeps, as FFmpeg's select expression: of every `every` frames, the
    frame of each phase asked for."""
    return "+".join(
        f"eq(mod(n\\,{every})\\,{phase})" for phase in sorted({p % every for p in phases})
    )


def decode(movie: Path, phases: tuple[int, ...] = PHASES[:1]) -> Iterator[np.ndarray]:
    """The movie's frames at FPS as 480x270 grey arrays, for each of `phases` from its frame of
    that number on, in the film's order: one process decodes the film once and keeps the frames
    of every phase asked for, so two phases' frames alternate.

    A 60 fps film is read at every sixth frame and a 10 fps draft at every frame, so its two
    phases differ only on a film fast enough to have a frame between its samples.
    """
    every = frame_rate(movie) // FPS
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(movie),
        "-an",
        "-vf",
        f"select='{sampling(every, phases)}',{DECODE}",
        "-fps_mode",
        "passthrough",
        "-f",
        "rawvideo",
        "-",
    ]
    size, read = WIDTH * HEIGHT, 0
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        while len(buffer := process.stdout.read(size)) == size:
            read += 1
            yield np.frombuffer(buffer, np.uint8).reshape(HEIGHT, WIDTH)
    if process.returncode or not read:
        named = repository.relative(repository.ROOT / movie)
        ended = f"ended with exit {process.returncode} after {read} frames of {named}"
        msg = f"FFmpeg {ended}" if read else f"FFmpeg read no frames from {named}"
        raise StillScanError(msg)


def phase_reports(film: Path, words: dict) -> list[dict]:
    """Each phase's scan of a film, from one decode: the frames come in the film's order, one
    of each distinct phase in turn, and are dealt to their phases. Phases that select the same
    frames read one report: a movie at the scan's own rate holds no frame between its samples."""
    every = frame_rate(film) // FPS
    offsets = [phase % every for phase in PHASES]
    kept = sorted(set(offsets))
    dealt = [Stills() for _ in kept]
    for k, frame in enumerate(decode(film, PHASES)):
        dealt[k % len(kept)].add(frame)
    reports = dict(zip(kept, [reported(stills, words) for stills in dealt], strict=True))
    return [reports[offset] for offset in offsets]


def judged(movie: Path, timeline: Path, limit: float = LIMIT_SECONDS) -> dict:
    """A film's scan against a timeline at both phases, as its record states it.

    Paths are below the film's root, or absolute. The record names the film, the timeline and the
    composition script it judged, with each one's SHA-256, so its result stays bound to them, the
    rules it was made under, and the still runs of the worse phase that carry at least `limit`
    seconds of speech. The film and the timeline are hashed before the film is decoded and after
    it: where either changed meanwhile, the scan judged bytes that no longer stand and is refused.
    A timeline whose words cannot be read is refused by its name before the film is decoded.
    """
    film, against = repository.ROOT / movie, repository.ROOT / timeline
    bound = [repository.sha(film), repository.sha(against)]
    words = repository.read_entry(against, ("segments",))
    try:
        aligned(words)
    except StillScanError as error:
        msg = f"{error} ({repository.relative(against)})"
        raise StillScanError(msg) from error
    report = worst(phase_reports(film, words))
    if [repository.sha(film), repository.sha(against)] != bound:
        msg = (
            f"{repository.relative(film)} or {repository.relative(against)} changed while the "
            "film was scanned"
        )
        raise StillScanError(msg)
    script = repository.ROOT / COMPOSITION_SCRIPT
    paths = (repository.relative(film), repository.relative(against), str(COMPOSITION_SCRIPT))
    digests = (*bound, repository.sha(script))
    subjects = {
        name: {"path": path, "sha256": digest}
        for name, path, digest in zip(SUBJECTS, paths, digests, strict=True)
    }
    stated = {
        "rules": rules(limit),
        "limit_seconds": limit,
        "over_limit": over_limit(report, limit),
    }
    return {**subjects, **report, **stated}


def record_scan(movie: Path, timeline: Path, out: Path, limit: float = LIMIT_SECONDS) -> dict:
    """Scan a film against a timeline at both phases and write the record at `out` (`judged`)."""
    record = judged(movie, timeline, limit)
    repository.write(out, record)
    return record


def record_draft(edition: Edition, movie: Path, limit: float = LIMIT_SECONDS) -> dict:
    """Scan an edition's draft against the edition's timeline into its draft record, which
    names what drew the draft as the draft's receipt does (`drawn_by`: the canvas package, its
    version and its text renderer; none where the draft has no receipt). The scan's limits were
    set on drafts a browser drew, and a renderer's frames fall otherwise at them, so a record
    admits a render only by the renderer that drew its draft (`filmkit.preflight`). A draft
    that does not decode to its timeline's seconds is refused and leaves no record."""
    record = judged(movie, edition.timeline, limit)
    whole(repository.ROOT / movie, record, film_frames(edition), edition.draft_stills)
    receipt = edition.draft_receipt
    drew = repository.read(receipt).get("renderer") if receipt.is_file() else None
    named = ("package", "version", "text_renderer")
    record["drawn_by"] = {key: drew.get(key) for key in named} if isinstance(drew, dict) else None
    repository.write(edition.draft_stills, record)
    return record


def whole(film: Path, record: dict, frames: list[int], place: Path) -> None:
    """Refuse a scan whose phases did not read the frames of the timeline's seconds: a decode
    that ends early would otherwise be reported as a shorter film. An earlier record at the
    scan's place is removed, so that none stands for a film that was not read whole."""
    if record["phase_frames"] != frames:
        place.unlink(missing_ok=True)
        read = " and ".join(map(str, record["phase_frames"]))
        msg = (
            f"{repository.relative(film)} decodes to {read} frames at {FPS} fps in its phases, "
            f"not the {frames[0]} of its timeline's seconds"
        )
        raise StillScanError(msg)


def subject_places(edition: Edition) -> dict[str, Path]:
    """The files an edition's film record binds, by the names it binds them under: its 1080p
    captioned film, its timeline and the composition."""
    paths = (edition.film(SCANNED_FILM), edition.timeline, repository.ROOT / COMPOSITION_SCRIPT)
    return dict(zip(SUBJECTS, paths, strict=True))


def film_subjects(edition: Edition) -> dict[str, Path]:
    """The files of `subject_places`, refused while one of them is missing."""
    subjects = subject_places(edition)
    missing = [repository.relative(path) for path in subjects.values() if not path.is_file()]
    if missing:
        msg = f"The {edition.code} film's still scan needs {', '.join(missing)}"
        raise PictureError(msg)
    return subjects


def film_frames(edition: Edition) -> list[int]:
    """The frames each phase of a scan reads of the edition's whole film: its runtime as its
    timeline states it (`Edition.runtime`), at the scan's rate. A missing timeline is the
    caller's to name, as every missing input is."""
    if not edition.timeline.is_file():
        raise FileNotFoundError(ENOENT, "No timeline", str(edition.timeline))
    try:
        seconds = edition.runtime
    except UnassembledError as error:
        raise PictureError(str(error)) from error
    return [seconds * FPS] * len(PHASES)


def film_record(edition: Edition) -> dict:
    """The edition's film record, where it answers for the film, the timeline, the composition
    and the engine as they stand (`still_record.answer`). `NoAnswerError` says why it does not,
    in the words that follow "The <code> film" in a refusal."""
    if not edition.film_stills.is_file():
        raise NoAnswerError(" has no still scan record")
    subjects, engine = film_subjects(edition), released.version()
    try:
        return still_record.answer(
            edition.film_stills, subjects, rules(), film_frames(edition), engine
        )
    except NoAnswerError as error:
        raise NoAnswerError(f"'s still scan record {error}") from error


def draft_record(edition: Edition) -> dict:
    """The edition's draft record, where it answers for the timeline and the composition as they
    stand, by the reader of the film's record (`still_record.answer`): a draft binds no engine
    and its own file is not kept as an input. `NoAnswerError` says why it does not."""
    paths = (edition.timeline, repository.ROOT / COMPOSITION_SCRIPT)
    subjects = dict(zip(SUBJECTS[1:], paths, strict=True))
    return still_record.answer(edition.draft_stills, subjects, rules(), film_frames(edition))


def refuse_still_pictures(edition: Edition, record: dict) -> None:
    """Refuse a film whose record lists a still run at the limit, naming each run."""
    held = over_limit(record)
    if held:
        msg = (
            f"The {edition.code} film holds a still picture with {limit_words()}: "
            f"{still_pictures(held)}; see {repository.relative(edition.film_stills)}"
        )
        raise PictureError(msg)


def scan_film(edition: Edition) -> dict:
    """Scan the edition's 1080p captioned film against its timeline into its film record, and
    refuse a film that holds a still run at the limit, after the record is written.

    A record that answers for the film as it stands (`film_record`) already holds the verdict:
    the film is then not decoded again, and the line printed and the run's settings say so
    (`scanned`). Any other record, a damaged one included, is replaced by a new scan. A
    film that cannot be read, that changes while it is read or that does not decode to the
    frames of its timeline's seconds is refused and leaves no record, an earlier one included.
    """
    path = edition.film_stills
    try:
        record, scanned = film_record(edition), False
    except NoAnswerError:
        record, scanned = {}, True
    run = seam.current()
    if run is not None:
        run.settings["scanned"] = scanned
    if scanned:
        film, frames = film_subjects(edition)["movie"], film_frames(edition)
        try:
            with seam.phase("scan"):
                record = judged(film, edition.timeline)
            whole(film, record, frames, path)
        except StillScanError as error:
            path.unlink(missing_ok=True)
            raise PictureError(str(error)) from error
        record["engine_version"] = released.version()
        repository.write(path, record)
    longest, held = record["longest_fine_speech"], len(over_limit(record))
    print(json.dumps({"longest_fine_speech": longest, "over_limit": held, "scanned": scanned}))
    refuse_still_pictures(edition, record)
    return record


def require_film_scan(edition: Edition) -> dict:
    """What the edition's film record found, refused unless the record answers for the film as
    it stands (`film_record`; the refusal says why not and names the action that scans) and
    lists no still run at the limit."""
    try:
        record = film_record(edition)
    except NoAnswerError as error:
        msg = f"The {edition.code} film{error}; run {SCAN_ACTION}"
        raise PictureError(msg) from error
    refuse_still_pictures(edition, record)
    return {
        "film": edition.film(SCANNED_FILM).name,
        "longest_fine_speech": record["longest_fine_speech"],
        "limit_seconds": LIMIT_SECONDS,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Report still pictures with speech in a rendered film."
    )
    parser.add_argument("movie")
    parser.add_argument("timeline", nargs="?", help="the timeline, unless --language names it")
    parser.add_argument("--out", help="the record, unless --language names it")
    parser.add_argument(
        "--language", choices=CODES, help="scan the edition's draft against its timeline"
    )
    parser.add_argument(
        "--limit", type=float, default=LIMIT_SECONDS, help="Fail a still run with this much speech"
    )
    options = parser.parse_args(argv)
    if cut(options.limit) != options.limit:
        parser.error("--limit is stated in whole hundredths of a second")
    movie = Path(options.movie)
    if (options.timeline is None) != (options.out is None) or (
        (options.language is None) == (options.timeline is None)
    ):
        parser.error("give the timeline and --out, or --language, which names both")
    try:
        if options.language is not None:
            record = record_draft(Edition(options.language), movie, options.limit)
        else:
            record = record_scan(movie, Path(options.timeline), Path(options.out), options.limit)
    except (StillScanError, PictureError) as error:
        sys.exit(f"still_scan: {error}")
    failing = record["over_limit"]
    print(
        json.dumps(
            {"longest_fine_speech": record["longest_fine_speech"], "over_limit": len(failing)}
        )
    )
    if failing:
        sys.exit(1)


if __name__ == "__main__":
    main()
