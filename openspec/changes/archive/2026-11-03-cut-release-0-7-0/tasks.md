# Tasks

## 1. Text-layout audit

- [x] 1.1 Add the text-layout module `picture/frame-audit/typography/` with the measures of design and report them per scene as runs of 1 s or more with start, end, texts and offsets; done when rule tests show each measure on synthetic frames, no finding for a half-second misalignment, a heading in a tall card or a name inside an empty ring, and the frame-audit test reads the new reports from a real audit. On 2026-11-03 `tests/picture/typography.test.mjs` shows each measure on synthetic frames and the exemptions, every calibrated exemption breaks a test when disabled, and `tests/picture/frame-audit.test.mjs` reads the six keys from a real audit of the sample; `npm test` passes 80 tests, with 100% of the module's lines covered. The archived head's proof then found the module over the repository's limit of 500 effective lines, so it was compensated and split by ownership into `layout.mjs`, `measures.mjs` and `index.mjs`, moving the code unchanged.
- [x] 1.2 Gate `ragged_rows`, `ragged_columns`, `crammed_lines` and `off_card_centre` in `picture/gates.py`, and record `uneven_pitch` and `touching_marks` in the gate record; done when gate tests refuse a ragged row, pass a picture with only an uneven pitch and list it in the record, and every `mise run check` command passes. On 2026-11-03 the gate tests refuse a ragged row and name it, and pass a picture with only an uneven pitch while listing it under `recorded_findings`.
- [x] 1.3 Run the audit from source over the DDWG 1.2.0 and ETHOS v2 compositions before and after their typography repairs, against the reviewers' findings; done when the gated measures report none of the automated findings the reviewers rejected and nothing gated on the repaired compositions, recorded in `build/evidence/typography/`. On 2026-11-03 the gated measures found every confirmed row of their kinds within the design's scope (DDWG 23/23 and 9/9, ETHOS 8/8 and 13/13) and none of the automated findings the reviewers rejected (`build/evidence/typography/calibration.json`). Over the repairs they report nothing gated in either edition of the DDWG second repair or of ETHOS v2 once its English outcomes' conditions stand in one column (`calibration-repairs.json`).

## 2. Sample film

- [x] 2.1 Give the sample film's `text()` an `align` option, set the closing checklist's items left-aligned at one gap after their checks, and raise its review floors to 95; done when the sample's composition tests pass and `check-picture` reports no text-layout finding in either edition. On 2026-11-03 the checklist's items start 26 px after their checks, both floors are 95, and the sample's whole closing scene reports no text-layout finding in either edition.

## 3. Supply

- [x] 3.1 Declare `tool.uv.cache-keys` for `pyproject.toml` and `VERSION`; done when changing `VERSION` rebuilds the editable install and the sample's gate record names the new engine version. On 2026-11-03, with `VERSION` at 0.7.0, the installed engine reported 0.6.0 before the first `uv run` and 0.7.0 after `mise run sample:build`, and both editions' `picture-gates.json` name `engine_version` 0.7.0.
- [x] 3.2 Raise `hyperframes` to 0.9.8 in `package.json`, refresh `package-lock.json`, and set `RENDERER_VERSION` and the browser pin to what 0.9.8 declares; done when the supply installs that build at its pinned digest, OSV reports no advisory in either lock, and `mise run sample:build` and `sample:verify` pass for both editions. On 2026-11-03 0.9.8 declared the same Chrome Headless Shell, 152.0.7977.30, so the browser pin stays and `RENDERER_VERSION` is 0.9.8; `mise run sample:supply` verified the pinned builds and models offline, `sample:build` and its `sample:verify` passed for both editions with no gated or recorded finding in either gate record, and OSV reported no advisory in either lock.

## 4. Documentation and release notes

- [x] 4.1 Document the text-layout measures and their gate in `README.md`, and bring the README and `NOTICE` to HyperFrames 0.9.8; done when both name the new version and the README lists the gated and the recorded measures. The README names the four gated and the two recorded measures, and both files name HyperFrames 0.9.8.
- [x] 4.2 Record the changes under `Unreleased`, then date the notes as `[0.7.0]` with the `v0.6.0...v0.7.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.7.0; done when no tracked file outside the Changelog history names 0.6.0 as the current version and every `mise run check` command passes. The notes are dated 2026-11-04 with the history link; outside the Changelog, 0.6.0 is named only as a past release, and `mise run check` passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.7.0`, the tag's publication and the source-only Release pages.
