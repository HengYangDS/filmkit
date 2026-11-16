## 1. Audits

- [ ] 1.1 Add the detail audit's four rule modules under `src/filmkit/picture/detail-audit/` (ink drops, texts outside scenes, strokes in quiets, rails), each with its lines as declared constants and their source; verify `tests/picture/detail-rules.test.mjs`, whose cases hold a failing and a passing input for each rule.
- [ ] 1.2 Add the tool `detail-audit` and name it in `filmkit.tools` among the tools that measure text by the film's faces; verify `tests/picture/detail-audit.test.mjs`: a composition that shows each artefact is reported row by row, the same composition repaired reports none, the sample film reports none, and a malformed invocation exits 2.
- [ ] 1.3 Report `off_centre_far` from the frame audit's reviewed balance; verify `tests/picture/rules/balance.test.mjs` (one second at 624 px is a far run; 0.4 s, a stretch at exactly 400 px, 0.3 s on the other side and a run two scenes share are not) and `tests/picture/frame-audit.test.mjs`.

## 2. Gate and declarations

- [ ] 2.1 Declare `[[picture.detail.exceptions]]`, `picture.drafts`, `review.clarity_thought_margin_db` with `[[review.clarity_exceptions]]`, and `[[captions.rate_exceptions]]` in the film's declaration, each refused when malformed; verify `tests/test_film.py`.
- [ ] 2.2 Run the detail audit in `check-picture`, bind its report in the gate record, and gate each of its findings and each far run unless a declared exception of the edition names it, a stale exception refused; verify `tests/picture/test_detail_gates.py` and `tests/picture/test_gates.py`.

## 3. Readiness

- [ ] 3.1 Ask in `preflight` for the sound gate's record, the geometry record as the delivery's verification requires it, the declared cues above the reading rate, the declared thoughts under the floor of a film with a thought line, and the draft scan only of a film that declares drafts; verify `tests/test_preflight.py` and `tests/delivery/test_verification_picture.py`.
- [ ] 3.2 Write the readiness receipt in `preflight` and add `produce admitted`, which checks the edition's receipt on every bound input and the other edition's on the shared ones; verify `tests/test_preflight.py` and `tests/test_produce.py`.
- [ ] 3.3 Declare the sample film's drafts, end its picture task with `admitted` for both editions, and state the audit, the declarations, `preflight` and `admitted` in the README and the Changelog; verify the repository's Markdown check on both files.

## 4. Films and acceptance

- [ ] 4.1 Run the lane's frame audit and detail audit, read-only and headless, on the three films' current compositions and compare each with the kit's scan of the same composition and timeline; verify that `build/evidence/readiness-in-preflight/films.json` holds each edition's digests and findings. The ink drops, texts outside scenes, strokes and rails agree with the kit on all six editions; the far-run line lists seven runs in the DDWG film and three in the ETHOS film that the kit's scan at 1.0 s did not.
- [ ] 4.2 Run `mise run check` and the proof's static lint on the lane's head; verify that the Node suite, the Markdown check, the Python suite and the lint pass.
- [ ] 4.3 Build the sample film with `mise run sample:build`; verify that both editions pass `check-picture`, `preflight` and `admitted`, and declare or repair in the sample film whatever the build names, such as an English cue above the reading rate or a far run.
- [ ] 4.4 Prepare the release that carries this Change: `VERSION` and the Changelog section's version and date; verify `mise run check` again.
