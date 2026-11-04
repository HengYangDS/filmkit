# Proposal

## Why

The ETHOS v2 film's round-4 review (2026-11-04) scored its English edition below the owner's floor of 95 in five dimensions, although `check-picture` passed every frame of both editions. The engine measured some of the defects without gating them: the sync audit lists marks that stand before their names (8 in Chinese, 7 in English, up to 11.4 s) and 1.6 s of English speech without a legible name, and the gate ignores both. Others it did not measure at all: a dashed stand-in that waits 8 s for its content in 09.1, two tool outlines that wait about 4 s for their names in the Chinese 03.6, caption cues drawn in full as labels, names of one row set in mixed case, and straight quotes in the transcript, the player and the MP4 tags while the captions and the picture set typographic ones. The Chinese review also found the player's stale description naming a rendering the concept contract rejects, which no check reads, and a Chinese film whose chapter track is tagged English. Each of these reached a reviewer; this release turns each into a check calibrated against what the reviewers found, so that none does again.

## What Changes

- `check-picture` refuses every seat and every run of unnamed speech that the sync audit lists, naming each, and records each thought that keeps the previous picture without refusing it. **BREAKING** for a film whose sync report lists either: it is refused before its next render.
- The seat check judges a dashed outline that a link joins to another mark on its own, and no longer counts a frame as named by an unnamed pictogram inside it.
- The sync audit lists caption cues whose words are drawn as labels during the cue: a cue drawn whole in one label refuses, and a cue at least 80% drawn in labels is recorded. The frame audit's per-frame `caption_echoes`, which this measure supersedes, is retired.
- The frame audit reports `mixed_case`: names of one set, or of one row, whose initial letters mix upper and lower case; `check-picture` refuses it. CJK names are exempt.
- The transcript (its title and headings included), the player's transcript, the chapter titles and the films' title, comment, description and synopsis tags set quotation marks as the captions do; Chinese output does not change.
- Every track of a delivered film, the chapter track included, carries the edition's language.
- The concept check reads the player's visible prose and the release's synopsis, comment and description, and refuses a counterexample there as in the narration.
- The supply moves to ETHOS 0.2.0-alpha.29 and uv 0.13.7, and the CI projection to `jdx/mise-action` 5.2.6; the code passes alpha.29's Ruff policy, which adds `DOC102`.
- `VERSION` 0.9.0, an `UNRELEASED` 0.9.0 entry in the Changelog and the README pin.

Out of scope: faint stand-ins (marks below the seat check's firm opacity), the order of a film's labels against its words beyond the sync audit's verdicts, any repair of a film's composition or text, and the release's tagging and publication.

## Capabilities

### New Capabilities

- `film-package`: the delivered films' tracks and tags describe their edition.

### Modified Capabilities

- `picture-gates`: the gate refuses seats, unnamed speech, whole caption echoes and mixed case, and records held pictures and partial echoes; the seat check judges stand-ins and pictograms.
- `caption-text`: the display copy's typographic quotes extend to titles, chapter titles and release tags.
- `concept-contract`: the player's prose and the release's prose are carriers of the concept check.

## Impact

- `src/filmkit/picture/`: `gates.py`, `sync_audit.py`, `seat-marks.mjs`, `headless-composition.mjs`, `frame-audit.mjs`, `frame-audit/composition.mjs`, `frame-audit/report.mjs`, `frame-audit/typography/` and their tests.
- `src/filmkit/captions/documents.py`, `src/filmkit/delivery/packaging.py`, `src/filmkit/concepts.py` and their tests.
- `.config/mise/config.toml`, `.config/mise/mise.lock`, `.github/workflows/ci.yml`; `README.md`, `CHANGELOG.md`, `VERSION`.

A film adopts 0.9.0 with its next edition: its picture must pass the new gates before `render-picture` starts, and its packaged transcript, chapters and tags change where its English text holds straight quotes or apostrophes, and in a Chinese film the chapter track's language. In the 0.x series this is a minor release.
