## Context

See [proposal.md](proposal.md) and the `caption-text` delta. `filmkit.captions.documents` writes
`chapters.ffmeta`. Packaging gives the file to FFmpeg, which takes the film's chapters from it; the
film's title, artist and comment tags are set on the packaging command, which replaces the file's,
and the file's `author` reaches no tag of the film. The file is also a member of the viewing
package and a download of the player page. FFmetadata reads `=`, `;`, `#`, the backslash and a
newline in a value as its own syntax unless a backslash precedes each, and FFmpeg's reader ends a
value at a carriage return too. Every value in the file is the film's: its title, its author
(written under two keys), its comment and each chapter title.

## Goals / Non-Goals

**Goals:**

- FFmpeg reads each value of `chapters.ffmeta` back as the film declares it, so a chapter title
  reaches the packaged film's chapter track whole and the delivered file says what the film
  declares.
- A value the format cannot keep is refused, and the film's text is not changed to fit.

**Non-Goals:**

- Changing what a film's titles, author or comments say, or any other document that the module
  writes.
- Escaping the keys and the numbers, which the engine writes itself and which hold none of these
  marks.
- Changing how packaging sets the film's tags.

## Decisions

- One function, `_metadata_value`, states the escape, and `_chapter_metadata` writes every value
  that a film declares through it, after `typeset` where a value was typeset before. Alternative
  considered: refusing a value that holds one of the marks. Not taken, because they are ordinary
  punctuation in a title and the format has an escape for them.
- The escape is applied where a value is written into the format and nowhere earlier, so the script
  and the other documents keep the text as authored.
- A carriage return is escaped with the five marks that FFmpeg's documentation of the format lists.
  The documentation does not name it; FFmpeg 9.0.2's reader ends a value at one and reads one back
  whole after a backslash [S1, E2], which the read-back test holds.
- A value that ends in a backslash is refused by `require_metadata_values`, in the module that
  writes the format, with the package's `CaptionError`: the refusal names the file that holds the
  value, the field and the value as JSON writes it. The author and the comment are the script's; the
  title and the chapter titles are read from the script when an edition is assembled and from its
  timeline when its captions are refreshed, since the documents are written from the timeline [S2,
  m2]. FFmpeg's reader takes a newline after a backslash as part of the value, whether or not that
  backslash is itself escaped, so no escape keeps such a value, and FFmpeg's own writer fails the
  same way [S1, E3]. Alternatives considered: stripping the backslash, which changes the film's
  text; and stating the limit while writing the value, which loses the next line's tag in silence.
  The values stand in a film's scripts, which no loader of their own judges, and the limit is the
  format's, so its refusal stands with the format's writer. `assemble` asks it before it decodes a
  recording. `refresh-captions` asks it after it has held the edition to its current script and
  selection and before it writes anything, so an edition whose script was corrected since its
  assembly is told to assemble again and not of a value its script no longer holds [S2, m2]. A
  refused edition keeps its soundtrack, timeline, receipt and documents as they were; the documents
  step asks again before it writes a document.
- The chapters are derived once, by `_chapter_segments`: a chapter runs while the segments' chapter
  stays the same and takes the title of its first segment. The documents are written from that
  derivation and the refusal judges the titles it gives, so a chapter that returns is refused by
  the title it would be written with, named by its segment [S2, m1].

## Risks / Trade-offs

- [A released film's delivered bytes change] → They do. Each released English edition's comment
  holds a semicolon, so its `chapters.ffmeta` gains one backslash, and its player page, which holds
  that file as a download and names its size, changes with it. The edition's film package binds
  `chapters.ffmeta` by its SHA-256, so the package is stale: its four films are set aside and
  packaged again, with other bytes at least in their creation time, and the still scan, the review
  round, the delivery and the release record follow [S1, E1]. No member of a Chinese edition
  changes. The films' title, artist and comment tags are the packaging command's and read as
  before. The release says so, and a film adopts it after it rebuilds and compares, as for every
  release.
- [A film declares a value that ends in a backslash] → It is refused by name before anything is
  written. No released film declares one.
- [A value holds a NUL] → A script can state one, as `\u0000`. It is neither escaped nor refused:
  the file holds it as it stands, and FFmpeg reads the value up to it [S2, n2]. No released film
  holds one.

## Migration Plan

Add the escape and the refusal with their tests. To roll back, write the values as before.

## Sources

- [S1] `build/evidence/check-the-formal-register/small-changes-review-1.md`, the independent review
  of 22 November 2026, with its probes of FFmpeg 9.0.2: E1 (the package binds the file), E2 (the
  carriage return), E3 (a value that ends in a backslash), E5 (which tags a film takes from the
  file).
- [S2] `build/evidence/formal-register/code-review-6.md`, the independent review of the lane of
  22 November 2026: m1 (the refusal derived the chapter titles a second way), m2 (the refresh named
  the script for values of the timeline, before the binding was checked), m6 (the Changelog names
  the records) and n2 (a NUL).
