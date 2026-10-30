# Proposal

## Why

A film's declaration names each edition's cover, and filmkit 0.1.0 refuses, when it loads, a declaration that names a missing file. The engine paints each cover from the staged picture, and the stage needs the narration, so a new film cannot narrate before it has covers and cannot paint covers before it narrates. The ETHOS film, the first film started on the engine rather than moved onto it, meets this before its first narration; the DDWG films and the sample film already had their covers.

## What Changes

- A declaration may name covers that do not exist yet: the engine loads it, narrates and stages the picture, and packaging refuses an edition whose cover is missing, naming its field.
- The cover check paints a cover that has no tracked file yet: it writes the painted cover, reports that no tracked cover was compared, and fails until the painted cover is tracked.
- Release 0.1.1.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `film-engine`: a declaration may name covers before the engine paints them, packaging requires them, and the cover check paints a first cover.

## Impact

- The declaration check, packaging and the cover check, with their tests; the README's guide to a new film; `CHANGELOG.md` and `VERSION`.
- A film whose covers exist loads, packages and checks its covers as before.
