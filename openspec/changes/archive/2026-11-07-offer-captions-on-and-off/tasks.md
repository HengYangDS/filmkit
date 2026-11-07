# Tasks

## 1. The uncaptioned picture

- [x] 1.1 Name each picture's stage, file and receipt in `production.Edition.rendered`, and give each rendition the picture it carries in `RENDITIONS`. Done when production tests find the uncaptioned stage, picture and receipt beside the captioned ones and the four films in order.
- [x] 1.2 Stage, render and validate the uncaptioned picture with `--uncaptioned` in `picture/rendering.py` and `produce.py`, each stage record and receipt naming its picture. Done when `tests/picture/test_uncaptioned.py` stages the timeline without its captions, renders it to its own file and receipt, refuses a receipt or stage of the other picture and reads a record without a picture as the captioned one, and `tests/test_produce.py` refuses `--uncaptioned` on any other action.

## 2. The equivalence gate

- [x] 2.1 Compare the compositions with and without captions in `picture/caption-equivalence.mjs`. Done when `tests/picture/caption-equivalence.test.mjs` finds both sample editions equivalent and refuses a mark drawn from the captions, a scene placed by the captions, a cue's text outside the caption role and a paint drawn only without captions.
- [x] 2.2 Compare the encoded pictures outside the caption band and write the edition's record in `picture/equivalence.py`, behind `produce compare-pictures`. Done when `tests/picture/test_equivalence.py` passes pictures that differ only in the band, refuses one that differs outside it, one short of the sampled frames and a composition that differs, and refuses a stale record.
- [x] 2.3 Calibrate the tile limit and the PSNR floor on the sample film. Done when `build/evidence/offer-captions-on-and-off/encoded-calibration.json` records the noise between the two pictures and the two controls for both editions, and the limits refuse the missing label.

## 3. Four films and the player

- [x] 3.1 Package the four films from their pictures after a passing comparison in `delivery/packaging.py`. Done when packaging tests encode four films with their own pictures, record each film's picture and refuse without both valid pictures or a passing record.
- [x] 3.2 Render the captions control and the files list's captions in `delivery/player.py`. Done when player tests find one control pressed with its words in both languages, the version buttons naming both films and the files list naming each film's captions.
- [x] 3.3 Exercise the control in the real-browser readback in `delivery/player-read.mjs`, `player-verdict.mjs` and `player-check.mjs`. Done when `tests/delivery/player-read.test.mjs` fails a switch that does not reach the other film, moves the time, loses playback or leaves the control pressed against the captions, and the readback of the sample film passes (`build/evidence/offer-captions-on-and-off/player-readback.json`) and fails a page whose control does not switch.

## 4. Delivery, verification and earlier builds

- [x] 4.1 Take the four films in `documents_folder.py`, `verification.py`, `review/round.py` and the preflight's stages. Done when the delivery, verification, round and preflight tests pass on 25 members, four films per edition and both stages.
- [x] 4.2 Set aside a build's own films and pictures in `review/set_aside.py`, and compare a release's own films in `delivery/reproduction.py`. Done when set-aside tests move a build packaged before 0.13.0 by its two films and reproduction tests compare a release with two films per edition and refuse a partial one.

## 5. The sample film and the release

- [x] 5.1 Stage, render, validate and compare both pictures in the sample's `sample:picture` task, and describe the four films in its prompt. Done when the sample's steps package and verify four films per edition in the scratch build.
- [x] 5.2 Document captions on and off in `README.md`, add the `[0.13.0] - UNRELEASED` Changelog entry and set `VERSION` and the README pin to 0.13.0. Done when every `mise run check` command and `openspec validate offer-captions-on-and-off --strict` pass.

## Workflow follow-up

- Before the release: `mise run sample:build` and its verification on the narrated sample in the lane.
- Run `compare-pictures` on each film's first 0.13.0 build and keep its measures beside the sample's.
- Archive the Change, prove the archived head once, land it and close out; date the Changelog entry when the release is cut.
