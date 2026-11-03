# Tasks

## 1. Picture gates

- [ ] 1.1 Measure the lit box in every voiced frame of the frame audit and report `off_centre_runs` and `thin_runs`, each a run of 2 s or more of speech beyond 12% off the content centre or below a tenth of the content band, per scene with start, end and worst value; done when a frame-audit test reports a 2.5 s off-centre run and a thin run, reports neither for a 1.5 s excursion or for quiet, and every `mise run check` command passes.
- [ ] 1.2 Add `check-picture` to `python -m filmkit.produce`: run the frame, sync and motion audits of the edition's current composition and timeline, write `build/evidence/editions/<code>/picture-gates.json` with their bindings and the gated findings of design's list, and refuse any gated finding; done when tests show a passing record for a clean picture and a refusal that names a gated finding.
- [ ] 1.3 Make `render-picture` refuse an edition without a passing gate record for its current composition, timeline and engine version; done when tests show a refusal for a missing record, for a composition changed after its check and for another engine version, and a render that proceeds from a current passing record.

## 2. Narration retakes

- [ ] 2.1 Bind each thought retake to the SHA-256 of its spoken text: the audition records each row's spoken text, binding refuses a row without one or with stale speech, and synthesis refuses a retake whose recorded spoken text differs from the thought's, naming it; done when tests cover a reading changed after the audition, unchanged speech, a retake bound before 0.6.0 and a stale proposal.

## 3. Review contract

- [ ] 3.1 Refuse a review round's prompts for a film that declares a concept contract unless its prompt template cites `{concepts}` and `{readings}` and its dimensions include `concept_fidelity`, naming each omission, and score `concept_fidelity` in the sample film; done when tests show the refusal before any prompt is written, nothing required of a film without a contract, and the sample film's prompts listing concept fidelity among their dimensions.

## 4. Supply

- [ ] 4.1 Raise `hyperframes` to 0.9.6 in `package.json`, refresh `package-lock.json` with `npm update --package-lock-only`, and set `RENDERER_VERSION` and the browser pin to what 0.9.6 declares; done when the supply installs that build at its pinned digest and OSV reports no advisory for any package the lock pins.
- [ ] 4.2 Run `check-picture` before each `render-picture` in the sample film's picture task, and build the sample film with `mise run sample:build`; done when `sample:verify` passes for both editions.

## 5. Documentation and release notes

- [ ] 5.1 Document the picture gates, the retakes' spoken binding and the review's contract check in `README.md`, and bring the README and `NOTICE` to HyperFrames 0.9.6; done when both name the new version and the README names `check-picture` before `render-picture`.
- [ ] 5.2 Record the changes under `Unreleased`, then date the notes as `[0.6.0]` with the `v0.5.0...v0.6.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.6.0; done when no tracked file outside the Changelog history names 0.5.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.6.0`, the tag's publication and the source-only Release pages.
