## Why

A film's chapter metadata is written as FFmetadata, which reads `=`, `;`, `#`, the backslash and a newline in a value
as its own syntax; FFmpeg ends a value at a carriage return too. The engine wrote the title, the author, the comment
and each chapter title into `chapters.ffmeta` as they stand
(`build/evidence/tooling-assessment-2026-11-20/media-audio.md`, the defect found by the research of 20 November 2026).
A packaged film takes its chapter titles from that file, so a chapter title lost a backslash, and ended at a newline
or a carriage return, in the film's chapter track. The film's title, artist and comment tags come from the packaging
command and were whole. The file is also delivered, in the viewing package and as a download of the player page, and
FFmpeg read each of its values with the same loss.

Of the released films, none holds one of these marks in a title, its author or a chapter title; each English edition's
comment holds one semicolon, which FFmpeg reads the same with or without the escape.

## What Changes

- The title, the author, the comment and each chapter title written to `chapters.ffmeta` escape `=`, `;`, `#`, the
  backslash, a newline and a carriage return with a backslash.
- A value among them that ends in a backslash is refused before the edition's documents are written, naming the
  script, the field and the value: FFmpeg reads the line after such a value into it, whatever is written.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `caption-text`: the chapter metadata keeps every character of a title, the author, a comment and a chapter title,
  and a value it cannot keep is refused.

## Impact

- `src/filmkit/captions/documents.py`, and the assembly and the caption refresh, which ask its refusal before they
  write; their tests.
- A film whose title, author, comment or chapter titles hold one of the marks gets another `chapters.ffmeta`, and
  another player page, which holds that file as a download and names its size. An edition's film package binds
  `chapters.ffmeta` by its SHA-256, so the package of such an edition is stale: the engine refuses it until its four
  films are set aside and packaged again, and the records that bind them follow (the viewing package's record, the
  film package's, the still scan, the review round, the delivery's checksums and readback, the release record).
- Of the released films that is each English edition, by one backslash before its comment's semicolon. No member of a
  Chinese edition changes. The packaged films' title, artist and comment tags are the packaging command's and read as
  before, and no chapter title of theirs holds one of the marks.
