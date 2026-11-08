# Tasks

## 1. Declared terms

- [x] 1.1 Compare caption layouts in `captions/english.py` first by how many breaks fall inside a declared term and then by their cost, without the 90 a split added to its break. Done when `tests/captions/test_phrasing.py`, red before the change, keeps the ETHOS film's expanded name whole after "Its name stands for", splits a term longer than a line once, and the earlier term and phrasing tests still pass. The two new term tests and the quotation tests failed on 0.14.0's phrasing, which split the name after "Trust"; all 41 caption phrasing tests pass.

## 2. Quotations

- [x] 2.1 Move the opening and closing quotation marks from `review/sentences.py` to `narration/spoken_units.py`. Done when `tests/review/` passes unchanged. `narration.spoken_units` also answers whether a quotation is still open; the review and caption tests pass (129).
- [x] 2.2 Join a caption sentence that ends inside an open quotation to the next one while they fit the limit, in `english_caption_sentences`. Done when `tests/captions/test_phrasing.py`, red before the change, sets An Agent hands back one sentence: "Done. All tests pass." on one caption, still divides a quotation longer than the limit at its sentences, and the Chinese quotation test is unchanged.

## 3. Films

- [x] 3.1 Set each film's current English script with this phrasing and with 0.14.0's. Done when `build/evidence/keep-caption-units-whole/films.json` lists, per film, the segments whose captions change and their lines before and after: the ETHOS film's 01, 03 and 09, the DDWG film's 28 and none of the essentials film's. Measured on the film lanes' scripts on 2026-11-08: ETHOS 01, 03, 09; DDWG 28; essentials none.

## 4. Integration

- [x] 4.1 Describe both rules in `README.md` and the Changelog. Done when `npm run format:markdown:check` passes.
- [x] 4.2 Run the repository's checks on the change. Done when `npm test`, `npm run format:markdown:check`, the Python suite, the gate-exact Ruff and ESLint checks and `openspec validate keep-caption-units-whole --strict` pass. `mise run check`: 154 Node tests, the Markdown check and 957 Python tests pass; the gate's isolated Ruff (E, F, B, I, UP) passes on the four changed Python files; no JavaScript changed.

## Workflow follow-up

- The chair sets the version, proves the archived head, lands and releases the change.
- Each film adopts the release by refreshing its captions and, where they change, checking and rendering its captioned picture again in its own lane.
