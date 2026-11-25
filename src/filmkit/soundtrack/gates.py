"""The sound gate: the lines a soundtrack must hold before the picture follows it.

The review's measurement records a soundtrack's clarity and its delivered endings, and reviewers
hold lines on them: no segment under the clarity floor its film declares, no thought that ends
abruptly or is cut while voiced, no phrase that stops without a heard fall. A record that nothing
refuses lets a retake cross such a line and a reviewer find it one round later, after the picture
was rendered on it. `check-sound` takes the same measures from the assembled soundtrack and its
timeline, writes them with their verdict beside the edition's other records, bound to the
soundtrack and the timeline it judged, and refuses a gated finding.

It also holds what a render waits for (design decision 7 of build-a-film-by-its-verbs): each
thought under the floor to the film's thought line, where the owner's hearing of its selected
take, which the soundtrack holds, settles it (`thought_findings`), and each caption cue to its
edition's reading rate, unless the film declares the cue by its text (`rate_findings`).

The gate judges only the lines whose measures agree with the reviewers' on delivered films. A
measure that is recorded but not yet calibrated against them, such as the pace or level step
between thoughts, stays with the review's measurement.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import filmkit.narration.hearings as hearings
import filmkit.released as released
import filmkit.repository as repository
import filmkit.review.clarity as clarity
import filmkit.review.endings as endings
from filmkit.captions.timing import captions_above_rate, reading_rate
from filmkit.film import FILM
from filmkit.graph import target
from filmkit.soundtrack.assembly import AssemblyError

if TYPE_CHECKING:
    from pathlib import Path

    from filmkit.production import Edition


def clarity_findings(measured: dict) -> list[str]:
    """The soundtrack and each segment that read below the floor the film declares."""
    floor = measured["floor_db"]
    findings = []
    if measured["soundtrack"]["below_floor"]:
        value = measured["soundtrack"]["cpp_db"]
        findings.append(f"the soundtrack's clarity is {value} dB, below the declared {floor} dB")
    findings += [
        f"segment {row['id']}'s clarity is {row['cpp_db']} dB, below the declared {floor} dB"
        for row in measured["segments"]
        if row["below_floor"]
    ]
    return findings


def ending_findings(measured: dict) -> list[str]:
    """The thoughts that end abruptly or are cut while voiced, and the phrases that stop."""
    delivered = measured["delivered"]
    findings = [f"thought {name} ends abruptly as delivered" for name in delivered["abrupt"]]
    findings += [
        f"thought {name} is cut while voiced where its release begins"
        for name in delivered["cut_while_voiced"]
    ]
    findings += [
        f"thought {stop['thought']} stops at {stop['word']!r} ({stop['end']} s)"
        " without a heard fall"
        for stop in measured["phrase_endings"]["stopped"]
    ]
    return findings


def thought_findings(edition: Edition, measured: dict) -> list[str]:
    """Each thought under the clarity floor that is neither one the film declares above its line
    nor one the owner heard clear on the selected take the soundtrack holds.

    The gate holds the floor for the soundtrack and its segments and records the thoughts. A
    film that declares `review.clarity_thought_margin_db` holds every thought to the floor less
    that margin and names each thought between the two lines; one that declares none is not
    judged here. With a margin of zero the line is the floor: every thought under it is refused
    and none is between the two.
    """
    margin = FILM.review.clarity_thought_margin_db
    if margin is None:
        return []
    lines = clarity.thought_lines(edition.code, floor=measured["floor_db"], film=FILM)
    line, declared = lines.line, lines.kept
    below = {row["id"]: row["cpp_db"] for row in measured["thoughts"] if row["below_floor"]}
    takes, assembled = selected_takes(edition)
    heard = [record for record in FILM.narration.heard if record.edition == edition.code]
    under = {
        name: value for name, value in below.items() if clarity.under_its_line(value, name, lines)
    }
    clear = {
        name
        for name in under
        if name in takes and hearings.settling(heard, name, takes[name]).get("clarity")
    }
    # A take the owner heard counts only where the soundtrack the gate measured holds it.
    unassembled = [
        f"thought {name} reads {under[name]} dB: the owner heard its selected take, but the "
        f"soundtrack was assembled from another selection of segment {name.rsplit('.', 1)[0]};"
        f" run {target('assemble', edition.code)}"
        for name in sorted(clear - assembled)
    ]
    refused = {name: value for name, value in under.items() if name not in clear}
    held = f"the thought line of {line} dB"
    if not margin:
        held = f"the floor of {line} dB, to which the film holds every thought"
    ear = {
        name: f": for the owner's ear, its selected take {takes[name]}" if name in takes else ""
        for name in refused
    }
    found = [
        f"thought {name} reads {value} dB, under {held}{ear[name]}"
        for name, value in refused.items()
        if value < line
    ]
    found += [
        f"thought {name} reads {value} dB, under the floor of {measured['floor_db']} dB, and is"
        f" not declared in review.clarity_exceptions{ear[name]}"
        for name, value in refused.items()
        if value >= line
    ]
    found += [
        f"the declared thought {name} is stale: it does not read under the floor"
        for name in sorted(declared - set(below))
    ]
    return unassembled + found


def selected_takes(edition: Edition) -> tuple[dict[str, str], set[str]]:
    """Each thought's selected take by its audio SHA-256, as the selection bound it, and the
    thoughts whose segment's selected recording is the one the assembly record names as its
    source (`source_sha256`): those the assembled soundtrack holds. None where the edition has
    no selected narration; no thought is assembled where it has no assembly record."""
    path = repository.ROOT / edition.narration_selected
    if not path.is_file():
        return {}, set()
    records = repository.read(path)["records"]
    assembly = edition.audio_assembly
    sources = {}
    if assembly.is_file():
        sources = {r["id"]: r.get("source_sha256") for r in repository.read(assembly)["records"]}
    takes = hearings.selected_takes(records)
    held = {r["id"] for r in records if sources.get(r["id"]) == r.get("wav_sha256")}
    return takes, {name for name in takes if name.rsplit(".", 1)[0] in held}


def rate_findings(edition: Edition, cues: list[dict]) -> list[str]:
    """Each cue above the edition's reading rate that the film does not declare by its text, and
    each declared cue that no cue reads above it."""
    rate = reading_rate(edition.code)
    fast = {cue["text"]: cue["characters_per_second"] for cue in captions_above_rate(cues, rate)}
    declared = {e.text for e in FILM.captions.rate_exceptions if e.edition == edition.code}
    found = [
        f"the cue {text!r} reads at {speed} characters per second, above {rate}, and is not"
        " declared in captions.rate_exceptions"
        for text, speed in fast.items()
        if text not in declared
    ]
    found += [
        f"the declared cue {text!r} is stale: no cue with that text reads above the rate"
        for text in sorted(declared - set(fast))
    ]
    return found


def sound_findings(clarity_measured: dict, endings_measured: dict) -> list[str]:
    """Every gated finding of a soundtrack's measures, clarity first, in the film's order."""
    return clarity_findings(clarity_measured) + ending_findings(endings_measured)


def bound_inputs(edition: Edition) -> dict[str, Path]:
    """The inputs the gate record binds, by the key of each one's SHA-256: the soundtrack and
    the timeline it measures, the assembly record whose levels its endings read, and the film's
    declaration, whose clarity floors it holds them to."""
    return {
        "soundtrack_sha256": edition.soundtrack,
        "timeline_sha256": edition.timeline,
        "assembly_sha256": edition.audio_assembly,
        "declaration_sha256": repository.ROOT / repository.DECLARATION,
    }


def bindings(edition: Edition) -> dict:
    """What the gate record binds: each input's SHA-256 (`bound_inputs`) and the engine's
    version."""
    digests = {key: repository.sha(path) for key, path in bound_inputs(edition).items()}
    return {**digests, "engine_version": released.version()}


def check_sound(edition: Edition) -> dict:
    """Measure the edition's assembled soundtrack, write its gate record and refuse a finding."""
    timeline = repository.read(edition.timeline)
    assembly = repository.read(edition.audio_assembly)
    bound = bindings(edition)
    clarity_measured = clarity.voice_clarity(edition.code, edition.soundtrack, timeline)
    endings_measured = endings.endings(edition, timeline, assembly)
    findings = sound_findings(clarity_measured, endings_measured)
    findings += thought_findings(edition, clarity_measured)
    findings += rate_findings(edition, timeline["captions"])
    record = {
        **bound,
        "clarity": clarity_measured,
        "endings": endings_measured,
        "gated_findings": findings,
        "verdict": "refuse" if findings else "pass",
    }
    repository.write(edition.sound_gates, record)
    print(json.dumps({"verdict": record["verdict"], "gated_findings": len(findings)}))
    if findings:
        noun = "finding" if len(findings) == 1 else "findings"
        msg = f"The {edition.code} soundtrack has {len(findings)} gated {noun}: " + "; ".join(
            findings
        )
        raise AssemblyError(msg)
    return record
