## 1. The stage's file names

- [ ] 1.1 State the stage's page and record names once in `src/filmkit/production.py`, give `Rendered` its page's
      place, and let `record_render` in `src/filmkit/picture/renderer.py` take the staged page from its callers; the
      statements that design decision 1 lists read them. Done when no Python module but `production.py` holds the
      literal `"stage.json"`, the literal `"index.html"` stands in Python only there and in the page's lines that task
      6.2 takes, `tests/test_production.py` holds the page's place as a literal expected value beside the stage's
      (`:24-26`), and the tests in that file, `tests/picture/test_rendering.py`, `tests/picture/test_native_render.py`,
      `tests/picture/test_draft.py`, `tests/picture/test_qualification.py`, `tests/picture/test_stage_contract.py`,
      `tests/delivery/test_release_staging.py`, `tests/delivery/test_reproduction.py`,
      `tests/delivery/test_verification_picture.py` and `tests/review/test_measurement.py` pass.
- [ ] 1.2 Take the page's and the record's names from `src/filmkit/picture/stage-contract.mjs` in
      `src/filmkit/picture/geometry-check.mjs`, `src/filmkit/delivery/player-check.mjs` and
      `src/filmkit/picture/native-canvas.mjs` (design decision 2). Done when, of the engine's Node modules, only
      `stage-contract.mjs` spells a stage's page or record in a statement that reads it (usage texts and comments
      keep their words), and the tests in `tests/picture/geometry-check.test.mjs`,
      `tests/picture/native-canvas.test.mjs`, `tests/picture/tool-invocations.test.mjs`,
      `tests/delivery/player.test.mjs` and `tests/picture/test_stage_contract.py` pass.
- [ ] 1.3 Make the input lines that design.md lists under "Test lines by role" for decision 1 read the owners. Done
      when those lines spell neither name, no expectation line listed there has changed, and the tests of their files
      pass.

## 2. The versions of the player page

- [x] 2.1 Make `VERSIONS` in `src/filmkit/delivery/player.py` the one statement of how the films pair into versions,
      taking each version's captioned and uncaptioned kinds from `production.RENDITIONS` by size, and let
      `listed_files`, the film the page opens on and the status line read it (design decision 3). Done when
      `player.py` holds none of `"1080p-captioned"`, `"1080p-uncaptioned"` and `"uhd-uncaptioned"`, holds `"uhd"` and
      `"viewing"` only as keys of `WORDS` and as the word keys `VERSIONS` gives its versions, and the tests in
      `tests/delivery/test_player.py` pass unchanged.

## 3. The Node tools' usage

- [ ] 3.1 Replace the usage lines of the module comment by a pointer to `USAGE` in the eight modules that design
      decision 4 lists, and give the constant of `src/filmkit/picture/native-canvas.mjs` the comment's form,
      `node native-canvas.mjs render …`. Done when `git grep -n 'Usage:' -- 'src/*.mjs'` lists nine lines, one in each
      module that prints a usage, and the tests in `tests/test_tools.py`, `tests/delivery/player.test.mjs`,
      `tests/picture/band-audit.test.mjs`, `tests/picture/caption-equivalence.test.mjs`,
      `tests/picture/detail-audit.test.mjs`, `tests/picture/native-canvas.test.mjs`,
      `tests/picture/whole-turns.test.mjs` and `tests/picture/tool-invocations.test.mjs` pass.

## 4. The published review's names

- [ ] 4.1 Derive in `src/filmkit/delivery/reproduction.py` the release names of an edition's review record and
      report from `Edition.production_review` and `production.review_report`, in one function that `members` and
      `review` call (design decision 5). Done when `production-review` stands in `src/` only in `production.py`, and
      the tests in `tests/delivery/test_reproduction.py` and `tests/delivery/test_release_staging.py` pass.
- [ ] 4.2 Make the input lines that design.md lists for decision 5 read that function or `production.review_report`.
      Done when no listed input line spells a review's name, no listed expectation has changed, and the tests in
      `tests/delivery/test_reproduction.py` and `tests/delivery/test_verification_review.py` pass.

## 5. The engine's name and its manifests' names

- [ ] 5.1 Read the engine's version, and name its tool cache's folder, through `released.ENGINE` in the twelve
      statements of design decision 6, and in the input lines design.md lists for it. Done when
      `git grep -n -E "[\"']filmkit[\"']" -- src` lists nothing, no listed expectation has changed, and the tests in
      `tests/picture/test_derivation.py`, `tests/picture/test_equivalence.py`, `tests/picture/test_gates.py`,
      `tests/picture/test_rendering.py`, `tests/picture/test_still_scan.py`, `tests/picture/test_still_record.py`,
      `tests/picture/test_uncaptioned.py`, `tests/test_preflight.py`, `tests/soundtrack/test_sound_gates.py`,
      `tests/test_tools.py` and `tests/test_adoption.py` pass.
- [x] 5.2 Locate a film's npm manifest, npm lock and Python lock in `src/filmkit/adoption.py` by
      `released.MANIFEST`, `released.NPM_LOCK` and `released.PYTHON_LOCK` (design decision 7). Done when no path
      statement of `adoption.py` spells one of the three names and the tests in `tests/test_adoption.py` pass.

## 6. An edition's documents and page

- [ ] 6.1 Name an edition's SRT and WebVTT captions, transcript, chapters and chapter metadata once, as places of
      `Edition` in `src/filmkit/production.py`, and read them where design decision 8 lists them. Done when none of
      those statements spells a document's name and the tests in `tests/captions/test_documents.py`,
      `tests/delivery/test_packaging.py`, `tests/delivery/test_player.py` and `tests/delivery/test_reproduction.py`
      pass unchanged.
- [ ] 6.2 State the delivered page's name once in `src/filmkit/delivery/player.py` and read it where design decision
      8 lists it. Done when none of those statements spells the name and the tests in
      `tests/delivery/test_delivery_index.py`, `tests/delivery/test_player.py`, `tests/delivery/test_packaging.py` and
      `tests/delivery/test_folder.py` pass unchanged.

## 7. The edition's folders and the pictures' frames

- [ ] 7.1 State the editions' artifacts and evidence folders and the stage folder's name once in
      `src/filmkit/production.py`, leaving the work root `build/runtime/work` to decision D10, and build from them
      the places of `Edition`, the language index's path, the media server's default folder, the superseded folder
      and the pattern that finds an edition in a tool's arguments (design decision 9). Done when no statement in
      `src/` outside `production.py` spells `build/artifacts/film`, `build/evidence/editions` or `final-delivery`,
      and the tests in `tests/test_production.py`, `tests/test_build_durations.py`, `tests/test_tools.py`,
      `tests/delivery/test_delivery_index.py`, `tests/delivery/test_media_server.py`, `tests/delivery/test_folder.py`
      and `tests/review/test_set_aside.py` pass unchanged.
- [ ] 7.2 Read the UHD frame from `picture.rendering.PICTURE_SIZE` in `src/filmkit/delivery/verification.py` and
      `src/filmkit/produce.py`; build the viewing film's scale filter in `src/filmkit/production.py` from its width
      and height; state the draft's frame in `src/filmkit/picture/draft.py` as the viewing film's; and let the cover
      painting of `src/filmkit/delivery/player-check.mjs` take its viewport from `frameContract` (design decision 9).
      Done when no statement of `verification.py`, `produce.py`, `draft.py` or the cover painting spells a frame's
      width or height, `production.py` spells the viewing film's once, and the tests in
      `tests/delivery/test_verification_picture.py`, `tests/test_produce.py`, `tests/test_production.py`,
      `tests/picture/test_draft.py`, `tests/delivery/test_packaging.py`, `tests/delivery/test_viewing_encode.py` and
      `tests/delivery/player.test.mjs` pass unchanged.

## 8. The Changelog

- [x] 8.1 Record the Change under `Unreleased` in `CHANGELOG.md`, as `CONTRIBUTING.md` asks. Done when the entry
      says that the engine reads each of these names from one owner, that no film's output, record or command
      changes, that the renderer's usage text gains `node`, that the cover check refuses a stage whose record and
      page disagree, and that the media server loads the film's declaration when it starts.

## 9. Acceptance

- [ ] 9.1 Make the acceptance checkout, a worktree of the base head apart from the Lane. In these tasks `<work>` and
      `<evidence>` are the Lane's `build/runtime/work/state-each-fact-once/` and `build/evidence/state-each-fact-once/`,
      `<base>` is the commit the Lane started from and `<head>` its commit after groups 1 to 8; each `mise run` names
      one task and runs in the checkout's root, and a step not marked with a host ticket runs as the host's admission
      rules class it. Run `git worktree add --detach <work>/checkout <base>`, then in the checkout `mise trust`,
      `mise run bootstrap` and `mise run sample:supply`, which installs the browser build and the speech models below
      the sample film's `build/runtime/tool-cache/` and is the one step that reaches the network; the host's FFmpeg
      with libx264 and ExifTool serve every later step. Done when `sample:supply` exits 0 and the checkout's `HEAD` is
      `<base>`.
- [ ] 9.2 Narrate the sample film once, on the base head: `mise run sample:narrate` in the checkout (one host
      ticket: it loads the speech models), then clone the checkout's `examples/sample-film/build/` to
      `<work>/narrated/` with `/bin/cp -c -R`. Done when the clone holds both editions'
      `build/evidence/editions/<code>/ear-first/`.
- [ ] 9.3 Build the base head's outputs on that narration, below the checkout's `examples/sample-film/build/`:
      `mise run sample:sound` (on the narration; it loads no speech model), `mise run sample:picture` (one host
      ticket: it renders), `mise run sample:package` (one host ticket: it packages) and
      `mise run sample:verify > <evidence>/verify-base.json`; then move the checkout's `examples/sample-film/build/` to
      `<work>/before/`. Done when each step exits 0 and `<work>/before/` holds each edition's four films.
- [ ] 9.4 Build the same on the Change's head: `git -C <work>/checkout checkout --detach <head>`, clone
      `<work>/narrated/` back to the checkout's `examples/sample-film/build/` with `/bin/cp -c -R`, and run
      `sample:sound`, `sample:picture` (one host ticket), `sample:package` (one host ticket) and `sample:verify`,
      its report to `<evidence>/verify-change.json`, as in task 9.3. Done when each step exits 0.
- [ ] 9.5 Compare `<work>/before/` with the checkout's `examples/sample-film/build/`, and `verify-base.json` with
      `verify-change.json`, file by file by the rule of design decision 11, with a script kept beside its record
      `<evidence>/compared.json`. Done when the record lists every file of both builds, no file stands in one build
      only, and each file is equal by its bytes, by its streams' hashes for a packaged film, or after the values that
      the decision sets aside, which the record names by file and field.
- [ ] 9.6 Run the geometry check and the cover check of both heads on the released films' stages, which their trial
      clones hold: `$HOME/projects/ddwg-film-worktrees/20261122-trial-edition-on-0-26-1`,
      `$HOME/projects/ddwg-essentials-film-worktrees/20261120-trial-edition-on-0-26-0` and
      `$HOME/projects/ethos-film-worktrees/20261122-trial-edition-on-0-26-1`. On 22 November only the essentials clone
      held captioned stages, of both editions; the ddwg-film clone held narration only, and the ETHOS clone narration
      and the Chinese edition's sound. List each clone's `build/` with `/bin/ls -R` into `<evidence>/released.json`, and
      clone each captioned stage `build/runtime/work/final-delivery-<code>-uhd/` that it holds, with the cover its
      `content/film.toml` names for the edition, to `<work>/released/<film>/<code>/`. With the checkout at `<head>`
      and then at `<base>`, run in its `examples/sample-film/`, for each stage,
      `mise exec -- uv run --python 3.12 --frozen --offline python -m filmkit.tools geometry-check <stage> <receipt> 2`
      and `… player-check cover <stage> <cover> <painting>`, receipts to `<evidence>/released/head/` and
      `<evidence>/released/base/` and paintings likewise below `<work>/released/`; each head's runs are one host ticket, since the geometry check drives a browser over a whole
      film. Nothing is written in a trial clone. Done when each stage gives the same exit status, geometry receipt and
      painting on both heads, and `released.json` states each painting's SHA-256, what each clone's `build/` held and
      which changed checks did not run there, with the reasons of design decision 11.
- [ ] 9.7 Remove the acceptance's work: untrust the checkout's Mise configuration (`mise trust --untrust`), remove the
      checkout with `git worktree remove`, then remove `<work>`. Done when `git worktree list` no longer names the
      checkout, `<work>` is gone, and `<evidence>` holds `compared.json` with its script, both verification reports,
      and `released.json` with the receipts of task 9.6.
