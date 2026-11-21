## Why

A film's chapter metadata is written as FFmetadata, which reads `=`, `;`, `#`, the backslash and a newline in a value
as its own syntax. The engine wrote the title, the comment and each chapter title as they stand, so a backslash in a
title was dropped and a newline ended the value (`build/evidence/tooling-assessment-2026-11-20/media-audio.md`, the
defect found by the research of 20 November 2026). No released film is affected: no chapter title holds one of these
marks, and the English comments' semicolons are read back the same with or without the escape, to the same bytes.

## What Changes

- Each value written to `chapters.ffmeta` escapes `=`, `;`, `#`, the backslash and a newline with a backslash.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `caption-text`: the chapter metadata keeps every character of a title and a comment.

## Impact

- `src/filmkit/captions/documents.py` and its test. A film's packaged bytes do not change unless one of its titles or
  comments holds a backslash, a newline, or a mark FFmpeg would otherwise misread.
