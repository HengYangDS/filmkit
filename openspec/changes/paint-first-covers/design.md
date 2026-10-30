# Design

## Context

`filmkit.film.load` runs when the engine is imported and refuses a declaration that names a missing file. The cover check (`player-check cover`) paints `window.renderCover()` from a staged UHD document and compares the painting with the tracked cover; staging needs the narrated timeline. Packaging is the first step that reads a cover: it copies it into the viewing package and derives the JPEG.

## Goals / Non-Goals

**Goals:**

- A new film can declare its covers, narrate, stage its picture and paint its first covers.
- Packaging, verification and delivery keep requiring both covers.

**Non-Goals:**

- Changing how a cover is painted or compared, or letting any other named file be absent.

## Decisions

- The load-time check covers every named file except the covers, and packaging checks each cover before it reads it, naming `editions.<code>.cover`. An optional `cover` field was rejected: the declaration must still say where the painted cover is tracked, and a film without a cover must still not package.
- The cover check writes the painting before it reads the tracked cover. Without a tracked cover it reports `cover_sha256: null` and `identical: false` and exits 1, so a first painting is never taken for a match. A separate paint command was rejected as a second entry point for the same painting.

## Risks / Trade-offs

- [A film does not paint its covers] → Packaging refuses with the field's name before any film is encoded, and verification and delivery run only after packaging.

## Migration Plan

Release 0.1.1; a film moves to it by changing its uv source tag and locking. A film that already tracks its covers needs no other change.
