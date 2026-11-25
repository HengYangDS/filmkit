"""The films' formal register: the forms of its standard that a word can show, checked wherever a
viewer meets a film's words.

The standard (`standard.md` beside this module) is the one source of the rules. The engine's
base style (`styles/register/`) holds the forms that a word can show, one Vale rule a standard
item, each with its own cases (`vale test`): the forms R1 and R3 list, English contractions and
R5's marks as errors; R2, R4 and the forms the engine adds within a rule's class as warnings. The
rest of the standard is the reviewers' to judge.

The check first asks the Vale on the path for its version and refuses one other than the
version the engine's release states (`filmkit.released.vale`), and refuses an engine without its
Vale configuration and a style folder that lacks a rule file the engine was installed with,
before it reads any word. It then gathers the words a viewer meets outside the picture
(`filmkit.concepts.places`), renders them as one text, one place a paragraph, its lines joined
by nothing between Chinese characters and by a space elsewhere, characters a viewer does not see
and an empty place left out, and runs Vale once on it, mapping each alert back to its place by a
table. A listed form is an error wherever it stands, but inside a fixed idiom that its rule states
at the form's token, whose characters are not the listed word (其实 in 名副其实, `colloquial.yml`);
the engine holds no other list of words that excuses one.

A film keeps a form at one place in `[[register.exceptions]]` (`filmkit.film.Register`) by naming
the text the form stands within there: the check excuses exactly the form's error-level
occurrences inside that text, refuses every other one, and refuses an exception whose place does
not hold its text, or that excuses no refusal. Each error left refuses, every one named at once
by its place and form, and the refusal says once how a film keeps a standard word or a
quotation. A passing check returns the warnings and the exceptions it applied; no exception
removes a warning. A Vale run that cannot run, outlives its deadline or answers in any form but
the one it documents is a refusal too, so the check never passes on a run it cannot read.

`rules` gives the standard's rules R1 to R6 as its document states them, for the reviewers'
prompt (`filmkit.review.prompts`), which restates none of them; `WARNINGS` and `EXCUSED` are the
names of the report's two parts that the prompt tells its reader of.

Usage: python -m filmkit.register
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import unicodedata
from collections import Counter
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import NamedTuple

import filmkit.concepts as concepts
import filmkit.languages as languages
import filmkit.released as released
from filmkit.film import FILM, form_key
from filmkit.production import CODES

# The engine's Vale configuration, which the check names to Vale by `--config`, and the folder of
# its base style. The file is the check's own data and bears the check's name: `vale.ini` is the
# name of a repository's own prose policy, which this file is not.
_CONFIG = Path(__file__).with_name("register.ini")
_STYLE = Path(__file__).with_name("styles") / "register"
# The standard's document, how it opens each rule of its list, and the rules it states.
_STANDARD = Path(__file__).with_name("standard.md")
_RULE = re.compile(r"^- \*\*(R\d+)\. ", re.M)
_RULES = tuple(f"R{number}" for number in range(1, 7))
# The longest a Vale run may take, in seconds: a film's words take hundredths of one.
_DEADLINE = 60
# Han characters and CJK or full-width marks: a line break between two of them joins by nothing.
_WIDE = languages.compiled("wide")
# Code points a viewer does not see, beside the format characters (category Cf): Unicode's
# Variation_Selector and Other_Default_Ignorable_Code_Point, as PropList.txt of Unicode 16.0.0
# lists them (https://www.unicode.org/Public/16.0.0/ucd/PropList.txt), each range first to last.
_UNSEEN = (
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180D),
    (0x180F, 0x180F),
    (0x2065, 0x2065),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0xE0000, 0xE0000),
    (0xE0002, 0xE001F),
    (0xE0080, 0xE00FF),
    (0xE0100, 0xE01EF),
    (0xE01F0, 0xE0FFF),
)
_UNSEEN_CODES = re.compile("[" + "".join(f"\\U{a:08x}-\\U{b:08x}" for a, b in _UNSEEN) + "]")
# The levels Vale gives an alert.
_SEVERITIES = ("error", "warning", "suggestion")
# What a refusal says once, after its lines, when a listed form of R1 or R3 is among them, and
# the rules that hold those forms.
_KEEP = (
    "A film keeps a standard word or a quotation at its place by declaring it in "
    "[[register.exceptions]]: its place, its form, the text the form stands within there "
    "(within) and a reason"
)
_LISTED = ("register.address", "register.colloquial", "register.contractions")
# How a refusal of the engine's own files ends.
_AGAIN = "install the engine again"
# The two parts of the report that a reader is told of by name: the forms the check records and
# does not refuse, and the exceptions it applied. The names are stated here once: `check` builds
# its report under them, and the reviewers' prompt names them from here.
WARNINGS, EXCUSED = "warnings", "excused"


class RegisterError(ValueError):
    """The film's words hold a form the register refuses, or the check's Vale or style is not
    the pinned one or did not run as documented.

    `lines` holds the refusals, one a line: what a caller counts or records. The error's text
    adds once, after them, how a film keeps a standard word or a quotation, where a listed form
    of R1 or R3 is among the refusals.
    """

    def __init__(self, *lines: str, advise: bool = False) -> None:
        super().__init__("\n".join([*lines, *([_KEEP] if advise else [])]))
        self.lines = lines


class _Alert(NamedTuple):
    """One form Vale found, at the place that holds it, in the paragraph of that place."""

    place: str
    form: str
    error: bool
    rule: str
    message: str
    text: str
    start: int

    @property
    def key(self) -> tuple[str, str]:
        return form_key(self.place, self.form)


def _run(command: list[str], text: str | None = None) -> subprocess.CompletedProcess:
    """One Vale run within the deadline: a run that cannot start or does not end in time is a
    refusal."""
    try:
        return subprocess.run(
            command,
            input=text,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=_DEADLINE,
        )
    except subprocess.TimeoutExpired:
        message = f"{command[0]} did not end within {_DEADLINE} s"
        raise RegisterError(message) from None
    except OSError as error:
        message = f"{command[0]} cannot run: {error.strerror or error}"
        raise RegisterError(message) from None


def _pinned(pinned: str) -> str:
    """The Vale on the path, refused unless it reports the pinned version."""
    runs = f"the register check runs Vale {pinned}, as this engine's release states"
    found = shutil.which("vale")
    if found is None:
        message = f"No vale on the path; {runs}"
        raise RegisterError(message)
    answered = _run([found, "--version"])
    if answered.returncode != 0:
        message = f"{found} --version ended with status {answered.returncode}; {runs}"
        raise RegisterError(message)
    answer = answered.stdout.split()
    reported = answer[2] if answer[:2] == ["vale", "version"] and len(answer) == 3 else None
    if reported != pinned:
        message = (
            f"{found} reports Vale {reported or ' '.join(answer) or 'nothing'}; {runs}: "
            f"mise use {released.VALE}@{pinned}"
        )
        raise RegisterError(message)
    return found


def _shipped() -> set[str]:
    """The rule files that the installation record of the running engine lists for its style.

    An engine installed from its wheel records, in its own lines, every file the wheel laid out,
    so a rule file the record lists and the folder lacks was lost after installation. An engine
    run from its source tree, or installed editable, has no record of the style's files: its
    folder is then the source itself, and the engine's own tests hold it to the rules they name.
    """
    folder = _STYLE.relative_to(_STYLE.parents[3]).as_posix()
    try:
        installed = metadata.distribution(released.ENGINE)
    except metadata.PackageNotFoundError:
        return set()
    # A record of another copy of the engine says nothing of this one's folder.
    if Path(installed.locate_file(folder)).resolve() != _STYLE.resolve():
        return set()
    rows = csv.reader((installed.read_text("RECORD") or "").splitlines())
    paths = [PurePosixPath(row[0]) for row in rows if row]
    return {
        path.name for path in paths if path.parent.as_posix() == folder and path.suffix == ".yml"
    }


def _styled() -> None:
    """Refuse an engine without its Vale configuration, and a style folder without rule files or
    without one the engine was installed with."""
    if not _CONFIG.is_file():
        message = f"The engine's register configuration at {_CONFIG} is not there; {_AGAIN}"
        raise RegisterError(message)
    held = {path.name for path in _STYLE.glob("*.yml")}
    if not held:
        message = f"The engine's register style at {_STYLE} holds no rule file; {_AGAIN}"
        raise RegisterError(message)
    lacking = sorted(_shipped() - held)
    if lacking:
        message = (
            f"The engine's register style at {_STYLE} lacks {', '.join(lacking)}, which the engine"
            f" was installed with; {_AGAIN}"
        )
        raise RegisterError(message)


def rules() -> str:
    """The rules R1 to R6 as the standard states them: the document's own lines from R1 to the
    end of its list of rules, which ends the document or stands before its next heading.

    A document that cannot be read, or that states other rules than R1 to R6, once each and in
    their order, is the engine's own file gone wrong and is refused by name: the reviewers are
    never given a part of the rules as the whole.
    """
    try:
        document = _STANDARD.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        message = f"The engine's standard at {_STANDARD} cannot be read: {error}; {_AGAIN}"
        raise RegisterError(message) from None
    opened = list(_RULE.finditer(document))
    stated = tuple(rule[1] for rule in opened)
    if stated != _RULES:
        message = (
            f"The engine's standard at {_STANDARD} states the rules {', '.join(stated) or 'none'},"
            f" not {_RULES[0]} to {_RULES[-1]}; {_AGAIN}"
        )
        raise RegisterError(message)
    heading = re.compile(r"^#", re.M).search(document, opened[-1].end())
    return document[opened[0].start() : heading.start() if heading else None].rstrip() + "\n"


def _paragraph(text: str) -> str:
    """A place's words on one line as a viewer reads them: no character the viewer does not see,
    its lines joined by nothing between Chinese characters and by a space elsewhere."""
    seen = _UNSEEN_CODES.sub("", "".join(c for c in text if unicodedata.category(c) != "Cf"))
    joined = ""
    for line in filter(None, (line.strip() for line in seen.splitlines())):
        wide = joined and _WIDE.match(joined[-1]) and _WIDE.match(line[0])
        joined += line if not joined or wide else f" {line}"
    return joined


def _found(linted: subprocess.CompletedProcess) -> list[dict]:
    """The alerts of a lint run as Vale documents them: status 0 or 1 and a JSON object whose
    one entry, whatever its key, lists the alerts, an error among them exactly when the status
    is 1."""
    status, printed = linted.returncode, linted.stdout.strip()
    if status not in (0, 1) or not printed:
        said = " ".join(linted.stderr.split())
        message = f"Vale ended with status {status}" + (
            f": {said}" if said else " and printed nothing"
        )
        raise RegisterError(message)
    try:
        found = json.loads(printed)
        alerts = [alert for held in found.values() for alert in held]
        severities = [alert["Severity"] for alert in alerts]
    except (ValueError, AttributeError, TypeError, KeyError):
        message = f"Vale printed no JSON object of alerts: {' '.join(printed.split())[:120]}"
        raise RegisterError(message) from None
    if status == 1 and "error" not in severities:
        message = "Vale ended with status 1 and reported no error-level alert"
        raise RegisterError(message)
    if status == 0 and "error" in severities:
        message = "Vale ended with status 0 though it reported an error-level alert"
        raise RegisterError(message)
    return alerts


def _alert(found: dict, table: dict[int, tuple[str, str]]) -> _Alert:
    """One alert of Vale's at its place, whose span must hold its form."""
    try:
        where, text = table[found["Line"]]
    except (KeyError, TypeError):
        message = f"Vale reported an alert that names no place: {json.dumps(found)[:120]}"
        raise RegisterError(message) from None
    form, severity, rule, said = (found.get(k) for k in ("Match", "Severity", "Check", "Message"))
    span = found.get("Span")
    start = span[0] - 1 if isinstance(span, list) and span and isinstance(span[0], int) else -1
    if (
        not all(isinstance(value, str) for value in (form, rule, said))
        or severity not in _SEVERITIES
    ):
        message = f"Vale reported an alert this check cannot read: {json.dumps(found)[:120]}"
        raise RegisterError(message)
    if start < 0 or text[start : start + len(form)] != form:
        message = f"Vale reported {form!r} at a span its place does not hold it: {span}"
        raise RegisterError(message)
    return _Alert(where, form, severity == "error", rule, said, text, start)


def _alerts(
    vale: str, places: list[concepts.Place], rules: tuple[str, ...]
) -> list[tuple[int, _Alert]]:
    """Each alert of one Vale run over the places, one place a paragraph, at its place, by the
    named rules alone (Vale's `--filter`), with the index of its place among `places`."""
    table, paragraphs, indices = {}, [], {}
    for index, place in enumerate(places):
        paragraph = _paragraph(place.text)
        if paragraph:
            line = 2 * len(paragraphs) + 1
            table[line], indices[line] = (place.where, paragraph), index
            paragraphs.append(paragraph)
    if not paragraphs:
        return []
    named = ", ".join(f'"{_STYLE.name}.{rule}"' for rule in rules)
    command = [vale, "--no-global", f"--config={_CONFIG}", "--ext=.txt", "--output=JSON"]
    command.append(f"--filter=.Name in [{named}]")
    linted = _found(_run(command, "\n\n".join(paragraphs) + "\n"))
    return [(indices.get(found.get("Line"), -1), _alert(found, table)) for found in linted]


def _languages_alerts(vale: str, gathered: dict[str, list[concepts.Place]]) -> list[_Alert]:
    """Each place's alerts by the rules of every language whose words it holds, one Vale run a
    language: an edition's place meets its language's rules and those of the language it reads
    each other script of the place in (`languages.read_in`); a place every edition shares, as the
    entry page, every declared language's. No rule meets a place by its script alone. An alert
    two languages' rules give alike is kept once."""
    every = [place for held in gathered.values() for place in held]
    order = {id(place): rank for rank, place in enumerate(every)}
    by_language: dict[str, list[concepts.Place]] = {}
    for name, held in gathered.items():
        for place in held:
            codes = (
                [language.code for language in languages.read_in(place.text, name)]
                if name in CODES
                else list(CODES)
            )
            for code in codes:
                by_language.setdefault(code, []).append(place)
    found = {}
    for code, places in by_language.items():
        for index, alert in _alerts(vale, places, languages.language(code).rules):
            key = (order[id(places[index])], alert.start, alert.rule, alert.form)
            found.setdefault(key, alert)
    # In the places' order, and each place's alerts in the order of their text.
    return [found[key] for key in sorted(found)]


def _within(alert: _Alert, within: str) -> bool:
    """Whether the alert's occurrence lies inside an occurrence of the text, in any letter case;
    occurrences that overlap one another are each found."""
    end = alert.start + len(alert.form)
    pattern = f"(?=({re.escape(within)}))"
    found = re.finditer(pattern, alert.text, re.I)
    return any(m.start(1) <= alert.start and end <= m.end(1) for m in found)


def _unheld(exception, held: dict[str, list[str]], excused: int, warned: set) -> str | None:
    """Why an exception that excused no refusal is refused: its place does not hold its text,
    the form stands there as a warning, or no error-level occurrence stands within the text."""
    if excused:
        return None
    named = f"The register exception of {exception.form!r} at {exception.place}"
    if not any(
        exception.within.casefold() in text.casefold() for text in held.get(exception.place, ())
    ):
        return f"{named} is stale: the place does not hold {exception.within!r}"
    if exception.key in warned:
        return (
            f"{named} excuses no refusal: the form stands there as a warning, which no exception"
            " removes"
        )
    return (
        f"{named} excuses no refusal: no error-level occurrence stands within {exception.within!r}"
    )


def check() -> dict:
    """Check the film's words against the register, refusing every unexcused error at once.

    Returns:
        The report: the Vale version, the places read, the warnings and the exceptions applied.
    """
    try:
        pinned = released.vale()
    except released.ReleasedError as error:
        raise RegisterError(str(error)) from None
    vale = _pinned(pinned)
    _styled()
    try:
        gathered = concepts.places()
    except concepts.ConceptError as error:
        raise RegisterError(str(error)) from None
    places = [place for held in gathered.values() for place in held]
    alerts = _languages_alerts(vale, gathered)
    held: dict[str, list[str]] = {}
    for place in places:
        held.setdefault(place.where, []).append(_paragraph(place.text))
    exceptions = FILM.formal_register.exceptions
    excusing = [
        (alert, [e for e in exceptions if e.key == alert.key and _within(alert, e.within)])
        for alert in alerts
        if alert.error
    ]
    applied = Counter(id(e) for _, found in excusing for e in found)
    warned = {alert.key for alert in alerts if not alert.error}
    failures = [why for e in exceptions if (why := _unheld(e, held, applied[id(e)], warned))]
    errors = [f"{alert.place}: {alert.message}" for alert, found in excusing if not found]
    if errors or failures:
        advise = any(alert.rule in _LISTED for alert, found in excusing if not found)
        raise RegisterError(*errors, *failures, advise=advise)
    return {
        "vale": pinned,
        "places": len(places),
        WARNINGS: [
            {"place": a.place, "form": a.form, "rule": a.rule, "message": a.message}
            for a in alerts
            if not a.error
        ],
        EXCUSED: [e.model_dump() for e in exceptions if applied[id(e)]],
    }


def main() -> None:
    try:
        report = check()
    except RegisterError as error:
        message = f"register: {error}"
        raise SystemExit(message) from None
    print(json.dumps(report, ensure_ascii=False))
