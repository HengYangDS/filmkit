## 1. Spotlight keywords

- [ ] 1.1 Add tests for the keywords value and its readback. A release's keywords pack as one value joined by "," with no space. A fixture of `mdimport -t -d2` output parses into keywords and authors, `\Uxxxx` escapes decoded. The verifier refuses a keyword imported with a leading space and a Chinese phrase not imported whole, records an English phrase split into words, and records "unavailable" when `mdimport` is absent. Done when each test fails on 0.20.0 and the failures are noted here.
- [ ] 1.2 Join the keywords with "," in `packaging.quicktime_keys`. Add `filmkit.delivery.spotlight` for the import and the parse, and call it from the film verification. Done when the tests of 1.1 pass.

## 2. Player links

- [ ] 2.1 Add tests: every film and cover link of a built player carries `target="_blank"` and `rel="noopener"`, and the readback fails a page whose cover link lacks them, naming the page and the link. Done when each test fails on 0.20.0.
- [ ] 2.2 Write the attributes in `player.file_link`. In `player-read.mjs`, click each film and cover link, require a new page whose address names the file, close it, and require the player's address unchanged. Done when the tests of 2.1 pass and `mise run sample:build` reads both players back.

## 3. English caption pace

- [ ] 3.1 Add tests to `tests/captions/test_timing.py`, each failing on 0.20.0:
  - a cue above 25 characters per second joins its neighbour in the same sentence within the limit;
  - a fast cue at a sentence end holds to the rate and no further than the next cue's start;
  - a cue within the rate is unchanged;
  - Chinese cues are unchanged;
  - every cue keeps its words and its start.
- [ ] 3.2 Extend `steady_short_cues` with the English reading rate of 25 characters per second. Done when the tests of 3.1 and the existing caption tests pass, and the three films' current English timelines give no cue above the rate that a join or a hold could bring within it.

## 4. Inflected labels

- [ ] 4.1 Add `snowballstemmer` to the project's dependencies through `uv add`, at its latest stable release. Done when `uv sync --frozen` installs it and its licence is recorded in `NOTICE`.
- [ ] 4.2 Add tests to `tests/picture/test_sync_audit.py`, each failing on 0.20.0:
  - "Availability" is judged against "available" in its own thought when "availability" comes 8.4 s later;
  - an exact occurrence within 8 s still wins;
  - "Publish" does not match "public";
  - a stem match outside the label's thought is not taken;
  - Chinese labels match as before.
- [ ] 4.3 Look up inflected occurrences in `sync_audit.audit` and record the match as inflected. Done when the tests of 4.2 pass.
- [ ] 4.4 Add tests to `tests/picture/test_sync_audit.py`, each failing on 0.20.0:
  - a label legible again after 1 s or more illegible, with its words said again within 8 s, is judged twice;
  - a label legible again without its words within 8 s is recorded as a recall and not judged;
  - a label that fades out for less than 1 s at a stage cut is judged once.
- [ ] 4.5 Judge each appearance of a label in `sync_audit.audit`, from runs in `legible_labels`, and list recalls in the report. Done when the tests of 4.4 and 4.2 pass, and the essentials film's current trace judges its 06.6 "Acceptance" on its own words.

## 5. Balance as the reviewers count it

- [ ] 5.1 Add tests for `reviewedRuns`, each failing on 0.20.0:
  - a still run that the next frame grows from is reported as held with its span and offset;
  - a build-up within its limit is not;
  - settled and finished runs are reported as before.

  Add tests for `check-picture`: it refuses a record that lists a held run or a settled run.

- [ ] 5.2 Report held runs in `rules/balance.mjs`, `frame-audit/composition.mjs` and `frame-audit/report.mjs`, and gate `off_centre_held` and `off_centre_settled` in `gates.py`. Done when the tests of 5.1 pass and the sample film passes `check-picture`.

## 6. Release and acceptance

- [ ] 6.1 Run each film's current English timeline through the new cue rule. Run its current composition through the new balance rules on its current timelines. Record the cues that join or hold and the runs refused, film by film, under `build/evidence/answer-the-engine-notes/films/`. Done when the records name the essentials film's repaired pictures as passing and DDWG's English 06 runs as refused.
- [ ] 6.2 Write the CHANGELOG entry, the README's adoption notes and `VERSION` 0.21.0. Done when `mise run check` passes, and the sample film builds and verifies with its keywords read back where `mdimport` exists.
