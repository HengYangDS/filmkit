# Tasks

## 1. Text-layout audit

- [ ] 1.1 Add `picture/frame-audit/typography.mjs` with the measures of design and report them per scene as runs of 1 s or more with start, end, texts and offsets; done when rule tests show each measure on synthetic frames, no finding for a half-second misalignment, a heading in a tall card or a name inside an empty ring, and the frame-audit test reads the new reports from a real audit.
- [ ] 1.2 Gate `ragged_rows`, `ragged_columns`, `crammed_lines` and `off_card_centre` in `picture/gates.py`, and record `uneven_pitch` and `touching_marks` in the gate record; done when gate tests refuse a ragged row, pass a picture with only an uneven pitch and list it in the record, and every `mise run check` command passes.
- [ ] 1.3 Run the audit from source over the DDWG 1.2.0 and ETHOS v2 compositions before and after their typography repairs, against the reviewers' findings; done when the gated measures report none of the automated findings the reviewers rejected and nothing gated on the repaired compositions, recorded in `build/evidence/typography/`.

## 2. Sample film

- [ ] 2.1 Give the sample film's `text()` an `align` option, set the closing checklist's items left-aligned at one gap after their checks, and raise its review floors to 95; done when the sample's composition tests pass and `check-picture` reports no text-layout finding in either edition.

## 3. Supply

- [ ] 3.1 Declare `tool.uv.cache-keys` for `pyproject.toml` and `VERSION`; done when changing `VERSION` rebuilds the editable install and the sample's gate record names the new engine version.
- [ ] 3.2 Raise `hyperframes` to 0.9.8 in `package.json`, refresh `package-lock.json`, and set `RENDERER_VERSION` and the browser pin to what 0.9.8 declares; done when the supply installs that build at its pinned digest, OSV reports no advisory in either lock, and `mise run sample:build` and `sample:verify` pass for both editions.

## 4. Documentation and release notes

- [ ] 4.1 Document the text-layout measures and their gate in `README.md`, and bring the README and `NOTICE` to HyperFrames 0.9.8; done when both name the new version and the README lists the gated and the recorded measures.
- [ ] 4.2 Record the changes under `Unreleased`, then date the notes as `[0.7.0]` with the `v0.6.0...v0.7.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.7.0; done when no tracked file outside the Changelog history names 0.6.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.7.0`, the tag's publication and the source-only Release pages.
