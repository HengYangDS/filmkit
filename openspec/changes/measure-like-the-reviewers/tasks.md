# Tasks

## 1. Text metrics from the film's fonts

- [x] 1.1 Add `filmkit.picture.metrics`, which builds the advance widths of every face `picture/film.css` declares from the film's declared fonts, with the stylesheet's and the fonts' SHA-256; done when its tests build the sample film's table, list a face's non-default advances, skip a family whose source is not a declared font, and the table's widths of sample strings equal the fonts' advance sums.
- [x] 1.2 Measure text in the stand-in canvas with the table that `FILMKIT_TEXT_METRICS` names, in the frame and motion audits, keeping the estimate for an undeclared family and an unmapped character; done when the headless-composition tests show a declared face's width, the estimate for an undeclared family and for an unmapped character, and letter spacing, and every JavaScript test passes with the repository's coverage gate.
- [x] 1.3 Name the table to both audits in `check-picture` and in `python -m filmkit.tools` when the caller names none, and bind the stylesheet's and the fonts' SHA-256 in the gate record and the render gate; done when the gate tests show the record's digests and a render refused after a font changes, and the tools test shows the variable passed.

## 2. Balance as the reviewers measure it

- [x] 2.1 Report `off_centre_builds` and `off_centre_settled` per scene from the full-size lit box of every frame; done when rule tests show a 1.6 s build-up at 120 px reported, a 1.4 s state at 200 px not, a still 2.5 s state at 60 px reported, a growing 3 s state at 70 px not, and a lone centred mark not, and the frame-audit test reads both keys from a real audit of the sample.
- [x] 2.2 Refuse `off_centre_builds` and record `off_centre_settled` in `check-picture`; done when a gate test refuses an off-centre build-up and names it, and another lists a still state off centre in a passing record.
- [x] 2.3 Measure the ETHOS v2 base and its balance repair, and the DDWG `0f91419` composition, from source against the reviewers' tables and findings; done when the new runs on the ETHOS base match the reviewers' balance runs, the repaired composition reports none, and the results are recorded in `build/evidence/balance/` (`calibration-1-30s.json`).
- [x] 2.4 Run `uneven_pitch` and `touching_marks` with exact widths on both films against the reviews that judged them, and refuse them only if they report no rejected finding and nothing on the repaired compositions; done when the decision and its counts are recorded in design §3 and the gate follows it.

## 3. Sample film

- [ ] 3.1 Run the new measures on the sample film and lay out any stage that stands off centre; done when `check-picture` passes for both editions and `mise run sample:build` and `sample:verify` pass.

## 4. Documentation and release notes

- [x] 4.1 Document the text metrics and the balance measures and their gate in `README.md`; done when the README names both measures, their limits and the table.
- [ ] 4.2 Record the changes under `Unreleased`, then date the notes as `[0.8.0]` with the `v0.7.0...v0.8.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.8.0; done when no tracked file outside the Changelog history names 0.7.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.8.0`, the tag's publication and the source-only Release pages.
