## Why

A film's chapter metadata is written as FFmetadata, which reads `=`, `;`, `#`, the backslash and a newline in a value
as its own syntax. The engine wrote the title, the author, the comment and each chapter title as they stand, so a
backslash in a title was dropped and a newline ended the value
(`build/evidence/tooling-assessment-2026-11-20/media-audio.md`, the
defect found by the research of 20 November 2026). Of the released films, none holds one of these marks in a title,
its author or a chapter title; each English edition's comment holds one semicolon. FFmpeg reads that semicolon back
as the same character with or without the escape, so the packaged films' tags read as before; the `chapters.ffmeta`
that each English edition delivers gains one backslash, and its player page, which holds that file as a download and
names its size, changes with it.

## What Changes

- The title, the author, the comment and each chapter title written to `chapters.ffmeta` escape `=`, `;`, `#`, the
  backslash and a newline with a backslash.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `caption-text`: the chapter metadata keeps every character of a title, the author and a comment.

## Impact

- `src/filmkit/captions/documents.py` and its test. A film whose title, author, comment or chapter titles hold one of
  the marks gets another `chapters.ffmeta`, which is a member of its viewing package, and another player page, which
  holds that file as a download and names its size: of the released films, each English edition's, by one backslash
  before its comment's semicolon. The tags of the packaged films read the same, except where a value holds a
  backslash or a newline, which were lost before.
