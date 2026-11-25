"""Write each edition's independent reviewer prompt for one review round.

The film declares the prompt as a `str.format` template (`review.prompt`), which each round fills
for each edition with the exact packaged films and their SHA-256, the round's own inputs, the
canonical source, the concept contract and the reading occurrence plans, the delivery format, the
pause, level and clarity policies the film declares, and the previous round's review. A film that
declares a concept contract gets prompts only when its template cites the contract and the
reading occurrence plans and its dimensions score concept fidelity.

Every film's template cites `{register}`, and one that does not is refused, naming the field.
The field names the round's register report (`REGISTER`, which the round's preparation writes
from `filmkit.register.check`), says what the report holds and what the check does not read,
and states the rules R1 to R6 of the formal register as the engine's standard states them
(`filmkit.register.rules`), so a film's review declaration need not restate them.

No round is prepared for films the engine's own measure refuses: the checks that only read
(`read_round`) ask each edition's passing still scan of its 1080p captioned film
(`filmkit.picture.still_scan.require_film_scan`, whose record the node `scan-film` writes), so a
round is not spent on a film that the delivery's verification would refuse afterwards.

`{previous_review}` states the previous round's review, its findings and that each repair is to
be verified, or, for a film's first production review, that no earlier production review exists;
it cites no previous review then. A template may instead cite `{previous}` and `{findings}`
itself, and is then filled only from a previous round.

A film that declares review levels gets prompts only when its template cites `{levels}`, which
states each level with what it asks and, under it, each of its dimensions with what that asks,
and `{sentences}`, which names the file of the edition's sentences (`filmkit.review.sentences`)
that the prompts write into the round's directory as sentences-<code>.json, each with its id,
text and timeline times, for a verdict on every one. A film without levels fills neither. A
template that cites a field the engine does not fill is refused, naming the field.

A round after the first gives each finding of the previous round's reviews one disposition in a
dispositions file: fixed, with the evidence that its reverification holds; declared, with the
design that keeps it; or deferred, with its owner and reason (`DISPOSITIONS`). `{dispositions}`
states those of the edition's previous findings in these three groups, and a first round states
none. A round after the first is refused without the file or with a template that does not cite
the field.
"""

from __future__ import annotations

import re
import string
from pathlib import Path

import filmkit.picture.still_scan as still_scan
import filmkit.register as register
import filmkit.repository as repository
import filmkit.sources as sources
import filmkit.specification as specification
from filmkit.film import FILM
from filmkit.narration.readings import plan_path
from filmkit.production import CODES, Edition
from filmkit.review import RUNTIME_FIELD, ReviewError
from filmkit.review.files import (
    cited,
    edition_review,
    present,
    review_files,
    round_findings,
    round_number,
)
from filmkit.review.record import DIMENSIONS
from filmkit.review.sentences import sentences

# The round's own inputs that each reviewer prompt names: the listening plan, the measurements,
# the binding of the delivery members whose players were read back and the register report.
LISTENING_PLAN = "pronunciation-listening-plan.json"
MEASUREMENTS = "measurements.json"
BINDING = "player-check-artifacts.json"
REGISTER = "register.json"
ROUND_INPUTS = (LISTENING_PLAN, MEASUREMENTS, BINDING, REGISTER)
# Each edition's files that the prompts write into the round's directory: its sentences, for a
# film with levels, and its prompt.
SENTENCES, PROMPT = "sentences-{code}.json", "prompt-{code}.md"
# The fields that each edition's films and its sentences file fill.
EDITION_FIELDS = ("media", "sentences")
# The reviewer prompt, filled per edition: the str.format template the film declares.
TEMPLATE = (repository.ROOT / FILM.review.prompt).read_text(encoding="utf-8")
# How the prompt names an optional field that the film or a script does not declare.
NOT_DECLARED = "none declared"
# The dimension that scores a declared concept contract, and the prompt fields that cite it
# and the reading occurrence plans.
CONCEPT_DIMENSION = "concept_fidelity"
CONTRACT_FIELDS = ("concepts", "readings")
# The prompt fields that a film with review levels cites: the levels and the sentences file.
LEVEL_FIELDS = ("levels", "sentences")
# The prompt field that every film cites, and what it states before the standard's rules: the
# round's register report, what it holds and what the register check does not read. The names of
# the report's two parts are the check's own (`register.WARNINGS`, `register.EXCUSED`).
REGISTER_FIELD = "register"
REGISTERED = (
    "{report} is the register check's report on the words a viewer meets outside the picture, "
    "in every edition and on the entry page. Its `{warnings}` are the forms the check records "
    "and does not refuse, each with its place and its rule's message; its `{excused}` are the "
    "exceptions the film declares that the check applied, each with the text its form stands "
    "within and the film's reason. The check judges single forms, and it does not read the "
    "words the picture paints: those words, the warnings, the exceptions and everything a "
    "single form cannot show are the reviewer's to judge against the rules of the formal "
    "register, as the engine's standard states them:"
)
# The fields that cite the previous round's review itself, which a first round cannot fill.
PREVIOUS_FIELDS = ("previous", "findings")
FIRST_ROUND = (
    "This is the first production review of these films; no earlier production review "
    "exists. Judge everything independently."
)
# Each disposition of a previous finding and how the prompts state a finding's entry, which
# holds exactly the fields its form names, each as text.
DISPOSITIONS = {
    "fixed": "{id}: {evidence}",
    "declared": "{id}: {design}",
    "deferred": "{id} (owner: {owner}): {reason}",
}
# The sentence that opens an edition's dispositions, before their three groups.
DISPOSED = (
    "Dispositions of round {number}'s findings. Re-verify each fixed finding on these media by "
    "its own reverification line; judge a declared finding against the design that keeps it, and "
    "a deferred one as it stands."
)


def cited_fields(template: str) -> list[str]:
    """Each field a template cites, by its name as written, `{}` as the empty name.

    The one reading of a template's fields. The engine fills a field with the text a reviewer is
    to read whole, so a field written with a conversion or a format specification is refused by
    name: `{register:.0}` would cut the rules to nothing, and the prompt would still be written.
    """
    cited = [field for field in string.Formatter().parse(template) if field[1] is not None]
    reshaped = sorted(
        "{" + name + (f"!{conversion}" if conversion else "") + (f":{form}" if form else "") + "}"
        for _, name, form, conversion in cited
        if form or conversion
    )
    if reshaped:
        msg = (
            f"{FILM.review.prompt} cites {' and '.join(reshaped)}, each with a conversion or a "
            "format specification; the engine fills a field that is cited with neither"
        )
        raise ReviewError(msg)
    return [name for _, name, _, _ in cited]


def template_fields(template: str) -> set[str]:
    """The names of the fields a template cites (`cited_fields`), `{}` left out."""
    return {name for name in cited_fields(template) if name}


def contract_gaps(template: str, dimensions: dict[str, str]) -> list[str]:
    """What a film's review configuration leaves out of the concept contract it declares.

    A film that declares a contract cites it and the reading occurrence plans in its prompt
    template and scores concept fidelity; a film without one owes neither.
    """
    if not FILM.concepts:
        return []
    fields = template_fields(template)
    gaps = [
        f"{FILM.review.prompt} never cites {{{name}}}"
        for name in CONTRACT_FIELDS
        if name not in fields
    ]
    if CONCEPT_DIMENSION not in dimensions:
        gaps.append(f"review.dimensions has no {CONCEPT_DIMENSION}")
    return gaps


def level_gaps(template: str) -> list[str]:
    """The level fields a film with review levels leaves out of its template; none without."""
    if FILM.review.levels is None:
        return []
    fields = template_fields(template)
    return [
        f"{FILM.review.prompt} never cites {{{name}}}"
        for name in LEVEL_FIELDS
        if name not in fields
    ]


def register_text(out_dir: Path) -> str:
    """`{register}`: the round's register report, what it holds and what the check does not
    read, then the rules R1 to R6 as the standard's document states them, the list's own lines.
    The standard's refusal of a document it cannot give the rules from is its own."""
    stated = REGISTERED.format(
        report=cited(out_dir / REGISTER), warnings=register.WARNINGS, excused=register.EXCUSED
    )
    return f"{stated}\n{register.rules().rstrip()}"


def levels_text() -> str:
    """`{levels}`: each level with what it asks, and under it each of its dimensions with what
    that dimension asks, or "none declared"."""
    if FILM.review.levels is None:
        return NOT_DECLARED
    lines = []
    for name, level in FILM.review.levels.items():
        lines.append(f"- {name}: {level.asks}")
        lines += [f"  - {dimension}: {DIMENSIONS[dimension]}" for dimension in level.dimensions]
    return "\n".join(lines)


def edition_sentences() -> dict[str, list[dict]]:
    """Each edition's sentences from its current timeline, for a film with levels; none for a
    film without. An edition without a timeline is refused."""
    if FILM.review.levels is None:
        return {}
    timelines = present([Edition(code).timeline for code in CODES])
    return {
        code: sentences(repository.read(timeline), code)
        for code, timeline in zip(CODES, timelines, strict=True)
    }


def declared_seconds(policy: dict, key: str) -> str:
    """A script's declared duration, or "none declared" for an optional one it omits."""
    value = policy.get(key)
    return NOT_DECLARED if value is None else f"{value:.2f} s"


def inner_caps(policy: dict) -> str:
    marks = policy.get("inner_pause_caps_seconds") or {}
    names = {",": "commas", "，": "commas", "、": "enumeration commas"}
    extra = ", ".join(f"{value:.2f} s at {names.get(mark, mark)}" for mark, value in marks.items())
    cap = declared_seconds(policy, "inner_pause_cap_seconds")
    return f"{cap} ({extra})" if extra else cap


def inner_floors(policy: dict) -> str:
    floors = policy.get("inner_pause_floors_seconds")
    if not floors:
        return NOT_DECLARED
    return ", ".join(f"{marks} {value:.3g} s" for marks, value in floors.items())


def inner_breath(policy: dict) -> str:
    breath = policy.get("inner_breath")
    if not breath:
        return NOT_DECLARED
    seconds, pause = breath["longest_group_seconds"], breath["pause_seconds"]
    return f"{seconds:g} s with a {pause:g} s pause"


def boundary(policy: dict) -> str:
    """A script's declared thought boundary ratio and the margin each floored boundary adds."""
    if policy.get("thought_boundary_ratio") is None:
        return NOT_DECLARED
    margin = policy.get("thought_boundary_margin_seconds", 0)
    return f"{policy['thought_boundary_ratio']} and {margin:.2f} s"


def clarity_floors() -> str:
    """The voice-clarity floors the film declares, in dB for each edition in the declared order,
    each by its language's name."""
    floors = FILM.review.clarity_minimum_db
    if not floors:
        return NOT_DECLARED
    return ", ".join(f"{floors[code]:g} dB {Edition(code).language}" for code in CODES)


def finding_index(findings: list[dict]) -> str:
    """Finding identifiers grouped by severity, in order of first appearance."""
    groups: dict[str, list[str]] = {}
    for finding in findings:
        groups.setdefault(finding["severity"], []).append(finding["id"])
    return "; ".join(f"{severity} {', '.join(ids)}" for severity, ids in groups.items())


def previous_review(previous: Path | None, code: str, findings: str) -> str:
    """The sentence that cites the previous round's review, or states that a round is the first."""
    if previous is None:
        return FIRST_ROUND
    review, report = review_files(previous, code)
    return (
        f"The previous review is in {cited(report)} and {cited(review)} ({findings}). Verify on "
        "these media whether each repair landed, and judge everything independently."
    )


def changes_text(changes: Path | None) -> str:
    """`{changes}`: the round's changes note, or nothing without one. A note that is missing or
    is no UTF-8 text is refused by name."""
    if changes is None:
        return ""
    try:
        return present([changes])[0].read_text(encoding="utf-8").strip() + "\n"
    except UnicodeDecodeError as error:
        msg = f"{repository.relative(changes)} is not UTF-8 text: {error}"
        raise ReviewError(msg) from None


def prompt_context(out_dir: Path, previous: Path | None, changes: Path | None) -> dict:
    """The template fields every edition's prompt shares.

    They name the canonical source, the film's concept contract and the readings' occurrence
    plans, the round's places, the delivery format but the runtime, which each edition's own
    fields state, and the pause, level and clarity policies the
    current scripts, assemblies and declaration hold; the previous round's directory only when
    there is one.
    """
    policies = {code: repository.read(Edition(code).script)["voice_performance"] for code in CODES}

    def each(value) -> str:
        """A policy's value for every edition in the declared order, by its language's name."""
        return "; ".join(f"{value(policies[code])} {Edition(code).language}" for code in CODES)

    manifest = sources.manifest()
    assemblies = [repository.read(Edition(code).audio_assembly) for code in CODES]
    levels = {item["program_level"]["policy"]["integrated_lufs"] for item in assemblies}
    if len(levels) != 1:
        msg = f"the soundtracks declare different program levels: {sorted(levels)}"
        raise ReviewError(msg)
    return {
        "root": repository.ROOT,
        "source": sources.location(),
        "documents": ", ".join(Path(member["path"]).stem for member in manifest["members"]),
        "concepts": cited(repository.ROOT / FILM.concepts) if FILM.concepts else NOT_DECLARED,
        "readings": " and ".join(cited(repository.ROOT / plan_path(code)) for code in CODES),
        "out": cited(out_dir),
        **({} if previous is None else {"previous": cited(previous)}),
        "changes": changes_text(changes),
        "fps": specification.FPS,
        "rate": f"{specification.RATE / 1000:g}",
        "program": f"{levels.pop():g}",
        "caps": each(inner_caps),
        "floors": each(inner_floors),
        "breath": each(inner_breath),
        "tolerances": each(lambda policy: f"{policy['thought_level_tolerance_db']} dB"),
        "ratios": each(boundary),
        "codas": each(lambda policy: declared_seconds(policy, "coda_thought_pause_seconds")),
        "clarity": clarity_floors(),
        "dimensions": "\n".join(
            f"{index}. {name}: {text}" for index, (name, text) in enumerate(DIMENSIONS.items(), 1)
        ),
        "levels": levels_text(),
        REGISTER_FIELD: register_text(out_dir),
    }


def previous_context(previous: Path | None, code: str) -> dict:
    """An edition's fields from the previous round: its review, findings and working files.

    A first round has no previous review, so its prompt states that none exists.
    """
    if previous is None:
        return {"previous_review": FIRST_ROUND, "findings": "", "scripts": ""}
    review = present(list(review_files(previous, code)))[0]
    found = edition_review(review, code)[1]["findings"]
    findings = f"findings: {finding_index(found)}" if found else "no findings"
    working = previous / code
    scripts = (
        f" The previous reviewer's working files are in {cited(working)}/; you may "
        "copy and adapt its scripts under your own output directory."
        if working.is_dir()
        else ""
    )
    return {
        "previous_review": previous_review(previous, code, findings),
        "findings": findings,
        "scripts": scripts,
    }


def disposition_fields(kind: str) -> list[str]:
    """The fields a disposition's entry holds, in the order the prompts state them."""
    form = DISPOSITIONS[kind]
    return [name for _, name, _, _ in string.Formatter().parse(form) if name and name != "id"]


def entry_problem(name: str, entry: object) -> str | None:
    """What keeps one finding's entry from being a disposition with its fields, if anything."""
    kind = entry.get("disposition") if isinstance(entry, dict) else None
    if kind not in tuple(DISPOSITIONS):
        return f"{name}: a disposition is fixed, declared or deferred"
    fields = disposition_fields(kind)
    if not all(isinstance(entry.get(field), str) and entry[field].strip() for field in fields):
        return f"{name}: a {kind} disposition states its {' and '.join(fields)}"
    extra = [key for key in entry if key not in ("disposition", *fields)]
    if extra:
        return f"{name}: a {kind} disposition holds no {', '.join(extra)}"
    return None


def checked_dispositions(path: Path, previous: Path) -> tuple[int, dict[str, list[str]], dict]:
    """The previous round's number, each edition's findings in it, and the file's dispositions.

    Refused unless the previous round's directory is named by its number, round-<n>, and the
    file is {"round": <n>, "findings": {<finding id>: <disposition>}} for that round, giving
    each finding of the round's reviews one disposition that holds its fields and no others; the
    refusal names each finding without one, each identifier the round does not hold and each
    entry that is not a disposition. A file that the engine's reader cannot decode as JSON, one
    in another encoding or with a byte order mark among them, is refused by name: an author
    writes it, so it is no fault of the engine's own records.
    """
    number = round_number(previous)
    if number is None:
        where = repository.relative(previous)
        msg = f"the previous round's directory {where} is not named round-<n>"
        raise ReviewError(msg)
    where = repository.relative(path)
    present([path])
    try:
        record = repository.read(path)
    except ValueError as error:
        msg = f"{where} is not JSON: {error}"
        raise ReviewError(msg) from None
    if (
        not isinstance(record, dict)
        or set(record) != {"round", "findings"}
        or not isinstance(record["findings"], dict)
    ):
        msg = f'{where} is not {{"round": <n>, "findings": {{<finding id>: <disposition>}}}}'
        raise ReviewError(msg)
    if isinstance(record["round"], bool) or record["round"] != number:
        msg = f"{where} names round {record['round']}, but the previous round is round {number}"
        raise ReviewError(msg)
    findings = round_findings(previous)
    held = [name for names in findings.values() for name in names]
    entries = record["findings"]
    problems = []
    if missing := [name for name in held if name not in entries]:
        problems.append(f"no disposition of {', '.join(missing)}")
    if unknown := [name for name in entries if name not in held]:
        problems.append(f"round {number} holds no finding {', '.join(unknown)}")
    problems += [
        problem
        for name, entry in entries.items()
        if name in held and (problem := entry_problem(name, entry))
    ]
    if problems:
        msg = f"{where} does not dispose of round {number}'s findings: " + "; ".join(problems)
        raise ReviewError(msg)
    return number, findings, entries


def disposition_text(number: int, names: list[str], entries: dict) -> str:
    """An edition's `{dispositions}`: those of its previous findings, in three groups.

    Each group lists its findings in the order of the previous review and an empty group says
    none; an edition whose previous review holds no findings states nothing. Each field's text
    is stated on one line.
    """
    if not names:
        return ""
    lines = [f"- {DISPOSED.format(number=number)}"]
    for kind, form in DISPOSITIONS.items():
        group = [name for name in names if entries[name]["disposition"] == kind]
        lines.append(f"  - {kind.capitalize()}:" if group else f"  - {kind.capitalize()}: none.")
        fields = disposition_fields(kind)
        for name in group:
            text = {field: " ".join(entries[name][field].split()) for field in fields}
            lines.append(f"    - {form.format(id=name, **text)}")
    return "\n".join(lines) + "\n"


def stated_dispositions(previous: Path | None, path: Path | None) -> dict[str, str]:
    """Each edition's `{dispositions}`: none in a first round, else from the dispositions file.

    Refused when a round after the first has no dispositions file or a template that does not
    cite the field, and when a first round, which has no findings to dispose of, has one. The
    file is checked by `checked_dispositions`.
    """
    if previous is None:
        if path is not None:
            msg = "--dispositions needs --previous; a first round has no findings to dispose of"
            raise ReviewError(msg)
        return dict.fromkeys(CODES, "")
    if path is None:
        msg = (
            f"--previous {repository.relative(previous)} needs --dispositions <file>, a "
            "disposition of each of its findings"
        )
        raise ReviewError(msg)
    if "dispositions" not in template_fields(TEMPLATE):
        msg = (
            f"{FILM.review.prompt} never cites {{dispositions}}, which states the dispositions of "
            "the previous round's findings"
        )
        raise ReviewError(msg)
    number, findings, entries = checked_dispositions(path, previous)
    return {code: disposition_text(number, findings[code], entries) for code in CODES}


def read_round(
    previous: Path | None,
    out_dir: Path,
    changes: Path | None = None,
    dispositions: Path | None = None,
) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """Each edition's template fields other than its films and its sentences file, and each
    edition's sentences: everything of a round's prompts that only reading gives.

    A round's preparation asks this before it derives anything, and `prompts` before it writes
    anything. Refused unless the review configuration keeps the concept contract the film declares
    (`contract_gaps`) and the levels it declares (`level_gaps`), the template cites no field with a
    conversion or a format specification (`cited_fields`, asked first) and cites the register field,
    a first round's template cites no previous review, each edition's 1080p captioned film holds its
    passing still scan (`still_scan.require_film_scan`, whose refusal is raised as that owner's
    own), a later round disposes of every previous finding (`stated_dispositions`), the previous
    round holds each edition's review and report, the changes note is text, the soundtracks declare
    one program level, the standard gives its rules (`filmkit.register.rules`, whose refusal is its
    own too), the template cites no field the engine does not fill, and each edition of a film with
    levels has its timeline.
    """
    named = set(cited_fields(TEMPLATE))
    gaps = contract_gaps(TEMPLATE, DIMENSIONS)
    if gaps:
        msg = "the review omits the concept contract the film declares: " + "; ".join(gaps)
        raise ReviewError(msg)
    gaps = level_gaps(TEMPLATE)
    if gaps:
        msg = "the review omits the levels the film declares: " + "; ".join(gaps)
        raise ReviewError(msg)
    if REGISTER_FIELD not in template_fields(TEMPLATE):
        msg = (
            f"{FILM.review.prompt} never cites {{{REGISTER_FIELD}}}, which names the round's "
            "register report and states the rules of the formal register"
        )
        raise ReviewError(msg)
    unfilled = sorted(template_fields(TEMPLATE).intersection(PREVIOUS_FIELDS))
    if previous is None and unfilled:
        cites = " and ".join(f"{{{name}}}" for name in unfilled)
        msg = (
            f"{FILM.review.prompt} cites {cites}, which only a previous round fills; a first "
            "round's template cites {previous_review}"
        )
        raise ReviewError(msg)
    for code in CODES:
        still_scan.require_film_scan(Edition(code))
    stated = stated_dispositions(previous, dispositions)
    context = prompt_context(out_dir, previous, changes)
    fields = {}
    for code in CODES:
        fields[code] = {
            **context,
            **previous_context(previous, code),
            "dispositions": stated[code],
            "language": Edition(code).language,
            "code": code,
            # Each edition's own runtime: the editions need not last alike.
            RUNTIME_FIELD: Edition(code).runtime,
            "others": others_text(code),
            "editions": editions_text(code),
        }
    # A field is filled by its first name: `{root.name}` asks for `root`, and `{}` for none.
    filled = {*fields[CODES[0]], *EDITION_FIELDS}
    unknown = sorted(
        name for name in named if re.split(r"[.\[]", name, maxsplit=1)[0] not in filled
    )
    if unknown:
        cites = " and ".join(f"{{{name}}}" for name in unknown)
        msg = f"{FILM.review.prompt} cites {cites}, which the engine does not fill"
        raise ReviewError(msg)
    return fields, edition_sentences()


def others_text(code: str) -> str:
    """`{others}`: every other edition by its language's name and its code, in the declared order,
    or the statement that the film has none."""
    named = [f"{Edition(other).language} ({other})" for other in CODES if other != code]
    if not named:
        return "no other edition"
    listed = named[0] if len(named) == 1 else f"{', '.join(named[:-1])} and {named[-1]}"
    return f"the {listed} edition{'s' if len(named) > 1 else ''}"


def editions_text(code: str) -> str:
    """`{editions}`: every edition's script, timeline and folder of delivered files, the prompt's
    own edition first and the others in the declared order."""
    ordered = [code, *(other for other in CODES if other != code)]
    return "; ".join(
        f"{Edition(each).language} ({each}): script {cited(repository.ROOT / Edition(each).script)}"
        f", timeline {cited(Edition(each).timeline)}, delivered files "
        f"{cited(Edition(each).artifacts)}/"
        for each in ordered
    )


def prompts(
    previous: Path | None,
    out_dir: Path,
    changes: Path | None = None,
    dispositions: Path | None = None,
) -> dict:
    """Write each edition's independent reviewer prompt for one round.

    Each prompt names the exact packaged films with their SHA-256, the previous round's
    review and its findings, or that the round is the first, the round's own inputs and the
    policies the film declares. changes holds Markdown context bullets for this round, such
    as the repairs since the previous review, and dispositions the disposition of each finding
    of the previous round (`stated_dispositions`). The previous review is context to verify,
    never a score to inherit. Nothing is written unless everything that only reads passes
    (`read_round`), the round's inputs exist and every edition's films are in place. For a film
    with levels, each edition's sentences are then written into the round's directory as
    sentences-<code>.json, and the prompts after them.
    """
    fields, rows = read_round(previous, out_dir, changes, dispositions)
    present([out_dir / name for name in ROUND_INPUTS])
    listed = {code: out_dir / SENTENCES.format(code=code) for code in rows}
    texts = {}
    for code in CODES:
        media = "\n".join(
            f"- {film} (SHA-256 {repository.sha(film)})" for film in present(Edition(code).films)
        )
        texts[code] = TEMPLATE.format(
            **fields[code],
            sentences=cited(listed[code]) if code in listed else NOT_DECLARED,
            media=media,
        )
    for code, path in listed.items():
        repository.write(path, {"edition": code, "sentences": rows[code]})
    written = []
    for code, text in texts.items():
        path = out_dir / PROMPT.format(code=code)
        path.write_text(text)
        written.append(repository.relative(path))
    return {"prompts": written}
