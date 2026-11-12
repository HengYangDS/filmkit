## 1. Spotlight keywords

- [x] 1.1 Add tests for the keywords value and its readback. A release's keywords pack as one value joined by "," with no space. A fixture of `mdimport -t -d2` output parses into keywords and authors, `\Uxxxx` escapes decoded. The verifier refuses a keyword imported with a leading space and a Chinese phrase not imported whole, records an English phrase split into words, and records "unavailable" when `mdimport` is absent. Done when each test fails on 0.20.0 and the failures are recorded under `build/evidence/answer-the-engine-notes/tests/`.
- [x] 1.2 Join the keywords with "," in `packaging.quicktime_keys`. Add `filmkit.delivery.spotlight` for the import and the parse, and call it from the film verification. Done when the tests of 1.1 pass.
- [x] 1.3 Add tests, failing on 0.20.0, that the verifier refuses a film whose imported authors are the declared author twice and passes one whose authors are exactly the declared author; then check the authors in `filmkit.delivery.spotlight`. Done when the tests pass.
- [x] 1.4 Refuse a film whose keywords import none while its release declares some, as design § Keywords decides, so an English edition's empty readback is not recorded as every phrase split. Done when its test fails on the code of 1.2 and passes after.

## 2. Player links

- [x] 2.1 Add tests: every film and cover link of a built player carries `target="_blank"` and `rel="noopener"`, and the readback fails a page whose cover link lacks them, naming the page and the link. Done when each test fails on 0.20.0.
- [ ] 2.2 Write the attributes in `player.file_link`. In `player-read.mjs`, click each film and cover link, require a new page whose address names the file, close it, and require the player's address unchanged. Done when the tests of 2.1 pass and `mise run sample:build` reads both players back.

## 3. English caption pace

- [x] 3.1 Add tests to `tests/captions/test_timing.py`, each failing on 0.20.0:
  - a cue above 25 characters per second joins its neighbour in the same sentence within the limit;
  - a fast cue at a sentence end holds to the rate and no further than the next cue's start;
  - a cue within the rate is unchanged;
  - Chinese cues are unchanged;
  - every cue keeps its words and its start.
- [x] 3.2 Extend `steady_short_cues` with the English reading rate of 25 characters per second. Done when the tests of 3.1 and the existing caption tests pass, and the three films' current English timelines give no cue above the rate that a join or a hold could bring within it.
- [x] 3.3 Record each English cue still above the rate, with its rate, in the edition's caption record. Done when a test shows a cue that can neither join nor hold listed at its rate, and the three films' current timelines list their fast cues: ETHOS 4, DDWG 4, essentials 3.

## 4. Inflected labels

- [x] 4.1 Add `snowballstemmer` to the project's dependencies through `uv add`, at its latest stable release. Done when `uv sync --frozen` installs it and its licence is recorded in `NOTICE`.
- [x] 4.2 Add tests to `tests/picture/test_sync_audit.py`, each failing on 0.20.0:
  - "Availability" is judged against "available" in its own thought when "availability" comes 8.4 s later;
  - an exact occurrence within 8 s still wins;
  - "Publish" does not match "public";
  - a stem match outside the label's thought is not taken;
  - Chinese labels match as before.
- [x] 4.3 Look up inflected occurrences in `sync_audit.audit` and record the match as inflected. Done when the tests of 4.2 pass.
- [x] 4.4 Add tests to `tests/picture/test_sync_audit.py`, each failing on 0.20.0:
  - a label legible again after 1 s or more illegible, with its words said again within 8 s, is judged twice;
  - a label legible again without its words within 8 s is recorded as a recall and not judged;
  - a label that fades out for less than 1 s at a stage cut is judged once.
- [x] 4.5 Judge each appearance of a label in `sync_audit.audit`, from runs in `legible_labels`, and list recalls in the report. Done when the tests of 4.4 and 4.2 pass, and the essentials film's current trace judges its 06.6 "Acceptance" on its own words.
- [x] 4.6 Add a test, failing on 0.20.0, that a cue of one quotation followed by its list's punctuation, such as `“Agreed in principle”, `, counts as a quotation; then let `sync_audit.quotation` ignore punctuation and spaces after the closing mark. Done when the test and the existing sync audit tests pass.

## 5. Balance as the reviewers count it

- [x] 5.1 Add tests for `reviewedRuns`, each failing on 0.20.0:
  - a still run that the next frame grows from is reported as held with its span and offset;
  - a build-up within its limit is not;
  - settled and finished runs are reported as before.

  Add tests for `check-picture`: it refuses a record that lists a held run or a settled run.

- [ ] 5.2 Report held runs in `rules/balance.mjs`, `frame-audit/composition.mjs` and `frame-audit/report.mjs`, and gate `off_centre_held` and `off_centre_settled` in `gates.py`. Done when the tests of 5.1 pass and the sample film passes `check-picture`.
- [x] 5.3 Add a test, failing on the current rule, that a glide passing 50 px 0.25 s before it settles, then standing still 87 px off for 1.9 s until a stage cut, is reported as a finished run of 2.15 s; then time each still run in `reviewedRuns` from the glide that settles into it. Done when the test and the existing balance tests pass, and the four film records of 7.1 are measured again.

## 6. A stroke's pieces

- [x] 6.1 Add tests to `tests/picture/motion-follow.test.mjs`, each failing on 0.20.0:
  - a stroke of three links whose second link joins whole at full ink while the first stands pops by that link, naming the stroke's line;
  - a link of the same stroke drawn on from its first point does not;
  - a link that turns from a vertical stub into a horizontal line does not;
  - the existing follow, cut and dash tests pass unchanged.
- [ ] 6.2 Pair the drawn pieces of each followed pair in `motion-audit/follow.mjs`, and pop by each piece left unpaired at ink 60 or more and 12 px or more across. Done when the tests of 6.1 pass and the sample film passes `check-picture`.

## 7. Release and acceptance

- [x] 7.1 Run each film's current English timeline through the new cue rule, and each film's current composition through the new balance and piece rules on its current timelines; record the cues that join or hold and the runs and pops refused, film by film, under `build/evidence/answer-the-engine-notes/films/`. Done when the records name the essentials and ETHOS films' current pictures and DDWG's repaired n8 as passing, DDWG's round-37 English 06 settled runs, its held runs in both editions and its 29.2 end as refused, and its round-37 25.2 lines as pops.
- [ ] 7.2 Write the CHANGELOG entry, the README's adoption notes and `VERSION` 0.21.0. Done when `mise run check` passes, and the sample film builds and verifies with its keywords read back where `mdimport` exists.
