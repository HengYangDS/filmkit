## Context

See [proposal.md](proposal.md) and the `caption-text` delta. `filmkit.captions.documents` writes
`chapters.ffmeta`, which FFmpeg reads when a film is packaged. FFmetadata reads `=`, `;`, `#`, the
backslash and a newline in a value as its own syntax unless a backslash precedes each. Every value
in the file is the film's: its title, its author (written under two keys), its comment and each
chapter title.

## Goals / Non-Goals

**Goals:**

- Every character of a film's title, its author, its comment and each chapter title reaches the
  packaged film's metadata.

**Non-Goals:**

- Changing what a film's titles, author or comments say, or any other document that the module
  writes.
- Escaping the keys and the numbers, which the engine writes itself and which hold none of these
  marks.

## Decisions

- One function, `_metadata_value`, states the escape, and `_chapter_metadata` writes every value
  that a film declares through it, after `typeset` where a value was typeset before. Alternative
  considered: refusing a value that holds one of the marks. Not taken, because they are ordinary
  punctuation in a title and the format has an escape for them.
- The escape is applied where a value is written into the format and nowhere earlier, so the script
  and the other documents keep the text as authored.

## Risks / Trade-offs

- [A released film's packaged bytes change] → No released film holds a backslash or a newline in
  these values, and FFmpeg reads an escaped semicolon back as the same character, which is the
  proposal's evidence that the packaged tags stay the same bytes. A film adopts the release after it
  rebuilds and compares, as for every release.

## Migration Plan

Add the escape with its test. To roll back, write the values as before.
