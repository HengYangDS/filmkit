# Agent Entry

Use the installed ETHOS product: run `ethos status --root . --json` and follow
its current result. Read the reported `agent_guidance.path` for version-matched
operation guidance. OpenSpec owns accepted Change intent; this file grants no
mutation authority.

## Engine Contract

This repository holds `filmkit`, the engine that rebuilds narrated bilingual
explainer films from a film's tracked sources. The engine carries no film's
content: each film's title, identity, scripts, voices, sources, pages, review
policy and picture composition stay in that film's repository, and the engine
reads them from the film it builds. An engine change keeps every existing film's
output bytes unless its release says otherwise; a film adopts such a release
only after it rebuilds and compares under its own reproduction standard.

The tests load only the sample film in `examples/sample-film/`. Its text is
written for the tests and is no film's source.

Generated output belongs under the ignored `build/` of this repository and of
the sample film. The tracked tree holds sources only.

## Host Tools

A film's build needs Apple silicon, FFmpeg with VideoToolbox and ExifTool, and
its delivery needs rsync 3; Homebrew owns all three
(`brew install ffmpeg exiftool rsync`). The supply step is the only one that
reaches the network. The proof sets hold the portable gates that hosted CI also
runs; the sample film's build is a local acceptance.
