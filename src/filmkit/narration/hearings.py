"""The owner's hearings of takes, which a film records in its declaration as `[[narration.heard]]`
(`filmkit.film.Heard`).

A record says that the film's owner, the author it declares, heard one take of a thought, named by
the SHA-256 of the take's audio, and that the take says its words (`units`) or is clear (`clarity`)
to his ear. It settles those lines of that take alone (`filmkit.narration.judgment`): any other take
of the thought, and every other line, is judged as if no record stood, and no hearing settles a
soundtrack or a segment (`filmkit.soundtrack.gates` reads no record). The declaration binds no
take's request, so a record narrates nothing again.

A record is refused when the declaration loads where it names an edition the film does not
declare, a take that is no SHA-256, no line or another, a line twice, a listener other than the
film's author, or a take that another record names; the selection refuses one whose take is not
its thought's selected take (`stale`). The sound gate counts a thought's selected take as heard
only where the soundtrack was assembled from that selection
(`filmkit.soundtrack.gates.thought_findings`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from filmkit.film import Heard


def refusals(heard: Sequence[Heard], author: str) -> list[str]:
    """What the declaration's records of hearing are refused with when it loads: a line named
    twice, a listener who is not the film's author, and a second record of one take."""
    takes = [record.take for record in heard]
    found = [
        f"narration.heard {record.edition} {record.thought} names a line twice"
        for record in heard
        if len(set(record.lines)) < len(record.lines)
    ]
    found += [
        f"narration.heard {record.edition} {record.thought} names the listener "
        f"{record.listener}; a record of hearing is the film's author, {author}"
        for record in heard
        if record.listener != author
    ]
    found += [
        f"narration.heard records the take {take} twice"
        for take in dict.fromkeys(takes)
        if takes.count(take) > 1
    ]
    return found


# What a line's record says of a hearing that its take passes without.
NOT_NEEDED = "not needed"


def settling(heard: Sequence[Heard], thought: str, take: str) -> dict[str, Heard]:
    """The records that settle a line of one take of a thought, by line: those that name the
    thought and the take's audio SHA-256."""
    return {
        line: record
        for record in heard
        if record.thought == thought and record.take == take
        for line in record.lines
    }


def settled(line: dict, record: Heard | None) -> dict:
    """A line's verdict with the owner's hearing: passed, naming the listener and the date, where
    it failed and a record settles it; said not needed where it passed and a record names it."""
    if record is None or line["passes"] is None:
        return line
    if line["passes"]:
        return {**line, "heard": NOT_NEEDED}
    return {**line, "passes": True, "heard": {"listener": record.listener, "date": record.date}}


def selected_takes(records: Sequence[dict]) -> dict[str, str]:
    """Each thought's selected take by its audio SHA-256, among the selected segments'
    `records` (`narration-selected.json`)."""
    return {
        f"{record['id']}.{child['index']}": child["wav_sha256"]
        for record in records
        for child in record.get("utterance_groups", {}).get("records", [])
    }


def stale(heard: Sequence[Heard], records: Sequence[dict]) -> list[str]:
    """Each record of an edition whose take is not its thought's selected take, among the
    selected segments' `records`, in one line each: a record of another take, and one of a
    thought the script does not hold."""
    selected = selected_takes(records)
    found = []
    for record in heard:
        take = selected.get(record.thought)
        if take == record.take:
            continue
        said = (
            f"the script holds no thought {record.thought}"
            if take is None
            else "the take it names is not the thought's selected take"
        )
        found.append(
            f"narration.heard {record.edition} {record.thought} {record.take}: {said}; remove the "
            "record or record the hearing of the selected take"
        )
    return found
