# Tasks

## 1. Declared terms

- [ ] 1.1 Compare caption layouts in `captions/english.py` first by how many breaks fall inside a declared term and then by their cost, without the 90 a split added to its break. Done when `tests/captions/test_phrasing.py`, red before the change, keeps the ETHOS film's expanded name whole after "Its name stands for", splits a term longer than a line once, and the earlier term and phrasing tests still pass.

## 2. Quotations

- [ ] 2.1 Move the opening and closing quotation marks from `review/sentences.py` to `narration/spoken_units.py`. Done when `tests/review/` passes unchanged.
- [ ] 2.2 Join a caption sentence that ends inside an open quotation to the next one while they fit the limit, in `english_caption_sentences`. Done when `tests/captions/test_phrasing.py`, red before the change, sets An Agent hands back one sentence: "Done. All tests pass." on one caption, still divides a quotation longer than the limit at its sentences, and the Chinese quotation test is unchanged.

## 3. Films

- [ ] 3.1 Set each film's current English script with this phrasing and with 0.14.0's. Done when `build/evidence/keep-caption-units-whole/films.json` lists, per film, the segments whose captions change and their lines before and after: the ETHOS film's 01, 03 and 09, the DDWG film's 28 and none of the essentials film's.

## 4. Integration

- [ ] 4.1 Describe both rules in `README.md` and the Changelog. Done when `npm run format:markdown:check` passes.
- [ ] 4.2 Run the repository's checks on the change. Done when `npm test`, `npm run format:markdown:check`, the Python suite, the gate-exact Ruff and ESLint checks and `openspec validate keep-caption-units-whole --strict` pass.

## Workflow follow-up

- The chair sets the version, proves the archived head, lands and releases the change.
- Each film adopts the release by refreshing its captions and, where they change, checking and rendering its captioned picture again in its own lane.
