# Tasks

## 1. Picture gates

- [x] 1.1 Measure the lit box in every voiced frame of the frame audit and report `off_centre_runs` and `thin_runs`, each a run of 2 s or more of speech beyond 12% off the content centre or below a tenth of the content band, per scene with start, end and worst value; done when a frame-audit test reports a 2.5 s off-centre run and a thin run, reports neither for a 1.5 s excursion or for quiet, and every `mise run check` command passes. `tests/picture/rules.test.mjs` reports a 2.5 s off-centre run with its worst offset and a 3 s thin run, and no run for a 1.5 s excursion, a change of scene or quiet, and `tests/picture/frame-audit.test.mjs` reads both reports from a real audit; on 2026-11-03 every check command passed, with 65 Node tests and 705 Python tests.
- [x] 1.2 Add `check-picture` to `python -m filmkit.produce`: run the frame, sync and motion audits of the edition's current composition and timeline, write `build/evidence/editions/<code>/picture-gates.json` with their bindings and the gated findings of design's list, and refuse any gated finding; done when tests show a passing record for a clean picture and a refusal that names a gated finding. `tests/picture/test_gates.py` writes a passing record that binds the composition, the timeline, the engine version and each report for a clean picture, and a refused record and refusal for an overlap, an off-centre run, a label shown after its words and a 3.6 s still; it also refuses a picture changed while it is checked and an audit that fails.
- [x] 1.3 Make `render-picture` refuse an edition without a passing gate record for its current composition, timeline and engine version; done when tests show a refusal for a missing record, for a composition changed after its check and for another engine version, and a render that proceeds from a current passing record. `tests/picture/test_rendering.py` refuses a missing record, a refused one, one for another engine version and one whose composition changed after its check, each naming `check-picture`, and its renders proceed from a current passing record.

## 2. Narration retakes

- [x] 2.1 Bind each thought retake to the SHA-256 of its spoken text: the audition records each row's spoken text, binding refuses a row without one or with stale speech, and synthesis refuses a retake whose recorded spoken text differs from the thought's, naming it; done when tests cover a reading changed after the audition, unchanged speech, a retake bound before 0.6.0 and a stale proposal. `tests/narration/test_retakes.py` binds a proposal auditioned on its thought's current speech with that speech's `spoken_sha256`, refuses one without spoken text or with speech that a changed reading no longer gives the thought, refuses a retake auditioned on other spoken text and names its thought, and still binds a retake recorded before 0.6.0; `tests/narration/test_audition.py` records each row's spoken text.

## 3. Review contract

- [x] 3.1 Refuse a review round's prompts for a film that declares a concept contract unless its prompt template cites `{concepts}` and `{readings}` and its dimensions include `concept_fidelity`, naming each omission, and score `concept_fidelity` in the sample film; done when tests show the refusal before any prompt is written, nothing required of a film without a contract, and the sample film's prompts listing concept fidelity among their dimensions. `tests/review/test_round.py` refuses a template without `{concepts}` and `{readings}` and dimensions without `concept_fidelity` for the sample film, naming all three before any prompt is written, requires neither of a film without a contract, and finds concept fidelity second among the sample film's dimensions in its prompts.

## 4. Supply

- [x] 4.1 Raise `hyperframes` to 0.9.6 in `package.json`, refresh `package-lock.json` with `npm update --package-lock-only`, and set `RENDERER_VERSION` and the browser pin to what 0.9.6 declares; done when the supply installs that build at its pinned digest and OSV reports no advisory for any package the lock pins. The lock moves only HyperFrames, to 0.9.6. It still declares Chrome Headless Shell 152.0.7977.30 and pins undici 7.25.0, so the browser pin and the undici 7.30.1 override stay, and 7.30.1 is the newest 7.x release; `sample:supply` installed that build at its pinned digest, `uv lock --upgrade` moves nothing, and OSV finds no issue in either lock.
- [ ] 4.2 Run `check-picture` before each `render-picture` in the sample film's picture task, and build the sample film with `mise run sample:build`; done when `sample:verify` passes for both editions.

## 5. Documentation and release notes

- [x] 5.1 Document the picture gates, the retakes' spoken binding and the review's contract check in `README.md`, and bring the README and `NOTICE` to HyperFrames 0.9.6; done when both name the new version and the README names `check-picture` before `render-picture`. The README's new section "The picture gate" names `check-picture` before `render-picture` and the gate record, "Concepts and readings" names the review's contract check, "Whole endings" names the retakes' spoken binding, and the README and `NOTICE` name HyperFrames 0.9.6.
- [ ] 5.2 Record the changes under `Unreleased`, then date the notes as `[0.6.0]` with the `v0.5.0...v0.6.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.6.0; done when no tracked file outside the Changelog history names 0.5.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.6.0`, the tag's publication and the source-only Release pages.
