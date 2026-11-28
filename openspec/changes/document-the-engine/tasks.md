Every command named here is light and runs at nice 15; a gate whose run alone uses more than two cores takes a host ticket instead. No task changes a file below `src/`, `tests/` or `examples/`.

## 1. The base

- [x] 1.1 Read in ETHOS's source at the bound release how its four documentation gates (`docs-registry`, `markdown-links`, `markdown-lint`, `prose`) join filmkit's proof, and run each alone once before and once after the move (`ethos prove --host --execute --gate <id> --json`). Done when the design records how they join and both runs with result, wall and CPU time, and the docs-registry run after the move reads the pages. Record: `build/evidence/document-the-engine/gates.txt`.
- [x] 1.2 Keep ETHOS's documentation root and vocabulary: the pages under `docs/`, the root ETHOS reads where the profile declares none, with ETHOS's roles and states and no taxonomy file. Done when the docs-registry gate reads every page under `docs/` and reports no invalid role or state.

## 2. The move

- [x] 2.1 Map every sentence of the README at the Change's base to the page that takes it, in the design's table. Done when no sentence is unmapped and each page's role is ETHOS's.
- [x] 2.2 Write `docs/README.md` (role index) and the five pages, each with ETHOS's front matter, moving the mapped sentences without changing their meaning. Done when the four gates pass on `docs/`.
- [x] 2.3 Cut the root README to the entry: what filmkit is and that it carries no film's content, where each kind of document lives, how to start (routes to `docs/install.md`, `docs/film-layout.md` and `docs/build-a-film.md`), and the license. Done when every sentence it lost is on a page by 2.1's map and it holds no section of content.
- [x] 2.4 Search the three films' tracked files and filmkit's own for links into the README's sections at the Change's base, and repoint filmkit's. Done when the search is recorded in the design and no link in filmkit points to a section the README no longer has; a film's link is listed for its own lane. Record: `build/evidence/document-the-engine/links.txt`.

## 3. The requirement and the record

- [ ] 3.1 Apply this Change's delta to `engine-distribution` at archive, and edit its Purpose sentence by hand in the same commit (the delta does not carry the Purpose). Done when `openspec validate --strict` passes and the Purpose names the documentation.
- [x] 3.2 Record the change under `Changed` in the Changelog's `Unreleased` section, with what a film changes to adopt the same form. Done when the Markdown gates pass.

## 4. Acceptance

- [ ] 4.1 The repository's full check on the landed head, through its host ticket. Done when it passes.
- [ ] 4.2 One independent review of the whole change by a reader that has not seen it; its findings answered in the text or the design. Done when the review's verdict is recorded.
