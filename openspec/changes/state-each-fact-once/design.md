## Context

See [proposal.md](proposal.md). Line numbers are of `1e4d459`; a source path without `tests/`, `.config/` or `openspec/` is below `src/filmkit/`. The engine keeps an edition's places in `production.py` (`Edition`, `Rendered`) and its delivered films in `RENDITIONS` (`production.py:94-99`). Its Node modules run as tools from a film's copy of them (`tools.py:98-112`), and `picture/stage-contract.mjs` is their reading of a stage. The review of 20 November listed facts stated twice [S1]; its dispositions sorted them [S2]; the re-reading at `1e4d459` of the places the dispositions call single is [S3].

## Goals / Non-Goals

**Goals:**

- Each fact in scope is stated once in Python and, where the Node modules need it, once among them; every other place derives it.
- No film's tracked file, record, delivered byte or command line changes. The printed changes are the renderer's usage text (decision 4) and the cover check's refusal of a stage whose record and page disagree (decision 9).

**Non-Goals:**

- The items of the decisions note, among them the player check's own lists (D3, D4), the films' prompt template (D2), the source of `released.ENGINE` (D6) and the stage's names across the two languages (D9).
- Module paths and command strings that name the import package (decision 6).
- The roots of the build layout, among them the work folder, which modules other than the edition's places use (D10).
- A test's expected values, which stay literals (decision 10).

## Decisions

1. **The stage's names stand in `production`, and the renderer is given the staged page.**
   - **Rests on:** the page is named in 13 occurrences and 12 statements of 8 modules: `picture/rendering.py:250`, `:302`, `:349`; `picture/renderer.py:316`, `:341`; `delivery/reproduction.py:406`, `:409`; `delivery/release.py:288` and `:290`, one statement (`:286-293`); `delivery/verification.py:169`; `review/measurement.py:467`; `picture/qualification.py:120`; `picture/equivalence.py:116`. The record is named at `picture/rendering.py:254` and `:302`. `rendering` imports the renderer (`picture/rendering.py:32`). `production` loads the film's declaration when it is imported, through `from filmkit.film import FILM` (`production.py:12`, `film.py:666-674`); none of the renderer's imports does (`picture/renderer.py:45-50`). `record_render` uses its stage only to hash the page (`picture/renderer.py:316`, `:341`); its callers are `picture/draft.py:59`, `picture/qualification.py:99-101` and `picture/rendering.py:429`.
   - **Considered:** (a) the names in `rendering`, which the renderer cannot import; (b) the names in `production`, imported by the renderer, which would then load the declaration on import, so that `tools`, importing the renderer (`tools.py:44`) before `production` (`:48`), would report a broken declaration where it now reports a missing `released.json`; (c) the names in `production`, `Rendered` giving its page, and `record_render` taking the page from its callers.
   - **Chosen because:** (c) keeps the names with the places they belong to (`production.py:102-118` names a picture's stage, file and receipt) and leaves the renderer's imports, and so its import-time behaviour, as they are.
   - **Applies to:** the 12 statements and 2 record statements above, `record_render` and its three callers.
   - **Reopened when:** the renderer needs another file of the stage.
2. **The Node modules take the stage's names from the stage contract.**
   - **Rests on:** `picture/stage-contract.mjs:9-10` states `RECORD` and `PAGE`; `picture/geometry-check.mjs:285` and `delivery/player-check.mjs:308` restate the page, `picture/native-canvas.mjs:120` and `:348` the record. `tools.stage_tools` copies every Node module of the package with its relative path (`tools.py:104-105`), so the imports resolve in a film's copy. The data file is named once in each language (`picture/rendering.py:53`, `picture/native-canvas.mjs:139`).
   - **Considered:** each module keeping its literal; importing from the contract.
   - **Chosen because:** the contract is already the tools' reading of a stage and imports no browser.
   - **Applies to:** the three modules named.
   - **Reopened when:** decision D9 of the decisions note changes how a tool is handed a stage.
3. **`VERSIONS` is the one statement of how the delivered films pair into versions.**
   - **Rests on:** `RENDITIONS` states each film's size and whether its picture draws captions; `delivery/player.py:73-76`, `:221-224` and `:425` pair or name the kinds by hand, and the status line names the version the page opens on by its word (`:431`) beside the flag that presses its button (`:74`). The page's words for a version are keys of `WORDS`: the button's (`viewing`, `uhd`; `delivery/player.py:84-85`, `:114-115`) and the film's (`viewing_film`, `uhd_film`; `:94-95`, `:124-125`).
   - **Considered:** deriving the pairing in each of the four places; deriving it once.
   - **Chosen because:** once is the rule. `VERSIONS` holds, for each version in the page's order (the viewing size, then UHD), its captioned and uncaptioned kinds taken from `RENDITIONS` by size, whether its button starts pressed and its two word keys; `listed_files`, the film the page opens on and the status line read it. The keys `viewing` and `uhd` of `WORDS` name words of the page, not kinds.
   - **Applies to:** `delivery/player.py`.
   - **Reopened when:** a version holds other films than one captioned and one uncaptioned of one size.
4. **A Node tool states its usage once, in the text it prints.**
   - **Rests on:** eight modules restate their usage in the module comment beside a `USAGE` constant: `picture/band-audit.mjs:16` and `:22`, `picture/caption-equivalence.mjs:17` and `:22`, `picture/detail-audit.mjs:15` and `:26-27`, `picture/frame-audit.mjs:3` and `:27-28`, `picture/motion-audit.mjs:6` and `:20-21`, `picture/native-canvas.mjs:3-5` and `:55-56`, `picture/whole-turns.mjs:9` and `:15`, `delivery/player-check.mjs:19-20` and `:35-37`. `picture/geometry-check.mjs` states its usage once (`:330-332`). In `native-canvas.mjs` the two copies differ: the comment reads `node native-canvas.mjs render …`, the constant `native-canvas.mjs render …`; the renderer runs the module as Node on it (`picture/renderer.py:219`, `:229-230`). No test asserts that text (`tests/picture/native-canvas.test.mjs:203-216` holds the exit status).
   - **Considered:** the comment as the statement, which nothing can print; the constant.
   - **Chosen because:** the printed text is what a user reads; the comment points at the constant. The renderer's constant takes the comment's form, which states how it is run.
   - **Applies to:** the eight modules.
   - **Reopened when:** not applicable.
5. **The release names of the review derive from its build files.**
   - **Rests on:** `delivery/reproduction.py:129-130` and `:242` spell the release names; `Edition.production_review` (`production.py:316-319`) and `production.review_report` (`:121-125`) name the build files.
   - **Considered:** keeping the spelled names; one function that prefixes a build file's name.
   - **Chosen because:** the release name is the edition's prefix and the build name, by the code's own pattern for its other documents (`delivery/reproduction.py:124-127`).
   - **Applies to:** `members` and `review` in `delivery/reproduction.py`.
   - **Reopened when:** a release names its review otherwise than by its build file.
6. **The engine's version is read under `released.ENGINE`; the import package's name is out of scope.**
   - **Rests on:** `ENGINE` (`released.py:29`) is read as the distribution's name by `adoption.py:247`, `:263`, `:275-276`, `:399` and `register/__init__.py:185`. Eleven reads of the version spell the name (`picture/derivation.py:149`, `picture/equivalence.py:124`, `picture/gates.py:390`, `picture/rendering.py:400`, `picture/still_scan.py:448`, `:504`, `preflight.py:204`, `:355`, `:372`, `soundtrack/gates.py:74`, `tools.py:103`), and so does the tool cache's folder (`tools.py:65`). Module paths and command strings name the import package: `adoption.py:62`, `:66`; `durations.py:372`; `narration/converge.py:155`; `narration/narrate.py:71`, `:92`, `:108`; `narration/processes.py:135`; `picture/faults.py:87`, `:89`; `picture/repair.py:51`; `review/set_aside.py:45`; `tools.py:191`.
   - **Considered:** deriving the module paths too, from `__package__` or a module's `__name__`; leaving them.
   - **Chosen because:** the version reads and the cache folder name the distribution, which `ENGINE` serves. A module path names the import package as every `import filmkit` statement of the engine does; deriving the strings alone would leave the name in every import, and renaming the package is one move of the whole tree. Which source `ENGINE` derives from is D6.
   - **Applies to:** the twelve statements named first.
   - **Reopened when:** D6 is decided for another way than its first.
7. **The adoption command locates a film's manifests by the names the record states.**
   - **Rests on:** `released.py:34`; `adoption.py:203`, `:212`, `:265`. The messages name the files in prose (`adoption.py:215-216`, `:227`, `:233`).
   - **Considered:** keeping the three spelled names; reading the names the record states.
   - **Chosen because:** they are npm's and uv's file names, stated once for the engine's own manifests; the three path statements read them and the messages keep their words.
   - **Applies to:** the three path statements of `adoption.py`.
   - **Reopened when:** not applicable.
8. **An edition's documents and its page are named once.**
   - **Rests on:** the documents are written to `edition.artifacts` (`captions/documents.py:233-242`), listed, bound and read again (`delivery/packaging.py:134-138`, `:246`, `:285`, `:442`; `delivery/player.py:240-244`, `:398`) and published under the same names (`delivery/reproduction.py:125-126`). The page's name stands at `delivery/packaging.py:86`, `:139`, `:154`, `:256` and `delivery/player.py:406`, `:408`; the player module owns the page (`delivery/player.py:3`), and `packaging` already imports from it (`delivery/packaging.py:50-51`).
   - **Considered:** the documents' names in their writer, `captions/documents.py`, which packaging, the player and the release would import; the names as places of `Edition`. The page's name in packaging; in the player.
   - **Chosen because:** an edition's files are `Edition`'s places, beside `film(kind)` (`production.py:212-214`); the page is the player's.
   - **Applies to:** the statements named.
   - **Reopened when:** an edition delivers another document.
9. **The edition's folders and the pictures' frames are read from their owners.**
   - **Rests on:** `production.py:172` (`build/artifacts/film`), `:176` (`build/evidence/editions`) and `:183` (the stage folder `final-delivery-<code>-uhd`, below the work root `build/runtime/work`, which `:290` and 13 statements of other modules spell, among them `delivery/packaging.py:88`, `delivery/folder.py:89` and `preflight.py:75`). The artifacts folder is restated at `delivery/packaging.py:86`, `delivery/media_server.py:88` and `review/set_aside.py:40`; the stage folder and the two folders' last names at `tools.py:76`, in the pattern that finds an edition in a tool's arguments (`tools.py:167-176`). The media server imports only `repository` (`delivery/media_server.py:13`), and importing `production` loads the film's declaration (`production.py:12`, `film.py:666-674`).
   - **Rests on, for the frames:** the UHD frame (`production.py:65`) is derived once as `picture/rendering.py:50` (`PICTURE_SIZE`) and restated at `delivery/verification.py:170` and `produce.py:169-170`; both modules already import `rendering` (`delivery/verification.py:41`, `produce.py:54`). The viewing film's frame (`production.py:67-68`) is restated in its own scale filter (`:72`) and as the draft's frame (`picture/draft.py:41`), which a stage may take only as a delivered film's frame (`picture/rendering.py:51`, `:234`). The cover check paints at 3840 by 2160 (`delivery/player-check.mjs:304`), the frame of the stage it paints, which the stage's record states and `frameContract` reads (`picture/stage-contract.mjs:29-58`), as the geometry check takes it (`picture/geometry-check.mjs:284-289`). Packaging marks a film 1080 lines high as HD video (`delivery/packaging.py:336`, `:353`): the tag's value 2 means 1080 lines, a fact of the tag and not of the viewing film, so it stays.
   - **Considered:** for the pattern, keeping it by hand, a second statement of three names, or building it from `production`'s values; for the two folders, `production`, beside the places that format them, or `repository`, beside the film's root, where no declaration loads; for the cover's viewport, the UHD frame stated in Node or the stage's frame contract.
   - **Chosen because:** `repository` states the two folders once, beside the film's root and its declaration, and `production` the stage's name; the places of `Edition`, the pattern, the default folder and the superseded folder are built from those values. In `production` the folders would make the media server, which imports only `repository`, load the film's declaration when it starts, so that a film whose declaration does not load could no longer have its built media served; in `repository` the server starts as before, as decision 1 keeps the renderer's imports. The work root stays as every module spells it until the build layout's roots get an owner of their own. The cover is painted at the frame of the stage it paints, as the geometry check measures it; a stage whose record and page disagree, which the geometry check already refuses, is then refused by the cover check too, before it paints.
   - **Applies to:** the statements named, but for `delivery/packaging.py:353`.
   - **Reopened when:** the build layout's roots get an owner of their own.
10. **A test reads an owner only to build an input; an expected value stays a literal.**
    - **Rests on:** the owner's rule of 20 November: a test's expected value standing beside its input is not a second source. The dispositions keep such values [S2].
    - **Chosen because:** a test that asserts the code's constant equals itself checks nothing. A line that writes, places or alters an input may read the owner; an assertion is not rewritten. The lines by role are listed under "Test lines by role" below.
    - **Reopened when:** not applicable.
11. **Acceptance builds the sample film on both heads from one narration and compares the builds file by file; the changed browser checks also run on the released films' stages.**
    - **Rests on:** `CONTRIBUTING.md` asks a picture change to rebuild the sample film and compare it with its previous output, and `openspec/config.yaml` asks a Change that changes a check to run the check on its real consumers, the released films. The sample build runs `sample:narrate`, `sample:sound`, `sample:picture`, `sample:package` and `sample:verify` in that order (`.config/mise/config.toml:130-138`), below the ignored `examples/sample-film/build/` (`.gitignore:2`), after `sample:supply` has installed the browser build and the speech models, the one step that reaches the network (`:44-51`). Narration loads the speech models; `sample:sound` loads none, writes each edition's documents in `assemble` and again in `refresh-captions` (`soundtrack/assembly.py:631`, `captions/refresh.py:169`) and writes the sound gate's record (`soundtrack/gates.py:74`); `sample:picture` stages, checks, paints the covers and renders; `sample:package` encodes the films; `sample:verify` prints its report and writes only a duration record (`delivery/verification.py:525-548`). No group edits a module of `narration/`; narration writes the edition's places, which `select` reads. Records state times (`picture/renderer.py:333-334`, `picture/derivation.py:431-432`, `durations.py:135-136`, `delivery/verification.py:450-452`), packaging writes a creation date into every film (`delivery/packaging.py:645`), and a render receipt names the absolute paths of its stage and output (`picture/renderer.py:324`, `:336`).
    - **Considered:** (a) staging alone, which reaches neither the renderer, the cover, the documents nor packaging; (b) the whole build on the base head in a checkout of its own and on the Change's head in the Lane, which narrates twice for no input the Change touches and leaves the two builds' receipts naming different roots; (c) one checkout apart from the Lane, narrated once on the base head, which builds sound, picture, packaging and verification at each head in turn from a clone of that narration.
    - **Chosen because:** (c) runs every step after narration on both heads, so each document, record, page and film that the Change can reach is written by the Change's own code, and with one root the receipts' paths agree. A file is compared by its bytes. A value that differs from run to run by its nature is set aside and named: a time or a duration, the creation date in a film's container, and a SHA-256 of a file that differs only by such values. A packaged film is compared by FFmpeg's hash of each of its streams (`-f streamhash`), which leaves the container's creation date out. Below `build/runtime/tool-cache/`, the supply is not compared, since both builds take it from one clone, and the copy of the engine's Node modules is compared by its folder's name, which task 5.1 derives, since it holds the modules the Change edits.
    - **What the sample build does not reach:** a release (groups 1, 4 and 6), a review round's measurement (group 1), the adoption command (task 5.2), the media server and the setting aside of superseded films (task 7.1) and the Node tools' usage texts (group 3). The tests that those tasks name hold their output as literal expected values (decision 10).
    - **On the released films:** of the changed checks, the geometry check and the cover check judge a stage by its content, so each runs on every captioned stage that the films' trial clones hold, from the acceptance checkout at each head. They run on clones of the stages and covers, with the sample film as the engine's root, so that a run writes nothing in a trial clone: a tool run copies the engine's modules into its root's tool cache and records its duration only for a path below that root (`tools.py:98-112`, `:167-186`). The other changed checks do not run there. In the sound gate, the picture gate, the still scan and the pre-render check the Change alters only the name under which each reads the engine's version, and in the film verifier only how it names the staged page and the UHD frame; none of these values depends on a film's input. The reads that hold a record to the running engine's version (`picture/rendering.py:397-404`, `preflight.py:201-205`, `picture/still_scan.py:448-450`) would find a released build, made by 0.26.0 or 0.26.1, stale on both heads alike; the two gates write their records into the film's own evidence; and the verifier needs a packaged edition. The sample build runs all five on both heads. The player check's other mode, which reads a delivery, changes only in its module comment and in the import that the cover check's run loads.
    - **Reopened when:** a compared file differs, or a released film's stage gives another verdict on one head than on the other.

### Test lines by role

Inputs, which may read the owner; expectations, which stay literal.

- **Decision 1, the page.** Inputs: `tests/delivery/conftest.py:270`, `:291`, `:432`; `tests/delivery/test_release.py:47`, `:124`, `:135`; `tests/delivery/test_reproduction.py:98`, `:101`, `:156`, `:337`, `:341`; `tests/delivery/test_verification_picture.py:72`; `tests/picture/test_derived_verification.py:29`; `tests/picture/test_equivalence.py:72`; `tests/picture/test_faults.py:109`; `tests/picture/test_native_render.py:84`; `tests/picture/test_rendering.py:167`, `:299`; `tests/picture/test_uncaptioned_way.py:206`; `tests/review/test_measurement.py:537`; `tests/test_preflight.py:110`; `tests/picture/geometry-check.test.mjs:351`. Expectations: `tests/delivery/test_release_staging.py:40`, `:42`, `:160`, `:162`; `tests/picture/test_draft.py:91`, `:98`; `tests/picture/test_faces.py:105`; `tests/picture/test_renderer.py:157`; `tests/picture/test_rendering.py:192`, `:397`; `tests/picture/test_stage_contract.py:42`, `:49`; `tests/picture/test_uncaptioned.py:79`, `:92`; `tests/picture/geometry-check.test.mjs:374`; and a new line of `tests/test_production.py` that holds the page's place beside the stage's (`:24`).
- **Decision 1, the record.** Inputs: `tests/picture/test_rendering.py:323`; `tests/picture/test_stage_contract.py:45`, `:46`; `tests/picture/test_uncaptioned.py:108`; `tests/picture/geometry-check.test.mjs:342`; `tests/picture/native-canvas.test.mjs:95`. Expectations: `tests/picture/test_draft.py:86`, `:91`; `tests/picture/test_faces.py:103`; `tests/picture/test_rendering.py:192`, `:220`; `tests/picture/test_uncaptioned.py:93`; `tests/picture/tool-invocations.test.mjs:101`.
- **Decision 5.** Inputs: `tests/delivery/test_reproduction.py:166`, `:184`, `:368`, `:403`; `tests/delivery/test_verification_review.py:22`, `:45`, `:66`, `:67`, `:72`, `:98`, `:148`. Expectations: `tests/delivery/test_release.py:57`; `tests/delivery/test_release_staging.py:290`, `:298-299`, `:459`; `tests/delivery/test_reproduction.py:528`; `tests/delivery/test_verification_review.py:71`, `:143`, `:152`.
- **Decision 6.** Inputs: `tests/picture/conftest.py:93`; `tests/picture/test_rendering.py:102`; `tests/picture/test_still_scan.py:502`; `tests/picture/test_uncaptioned.py:60`; `tests/test_preflight.py:87`, `:98`; `tests/test_adoption.py:51-54`, `:165`, `:428`, `:553-554`, `:558`. Expectations: `tests/picture/test_gates.py:162`; `tests/picture/test_still_record.py:451`; `tests/picture/test_still_scan.py:308`; `tests/test_preflight.py:443`; `tests/test_adoption.py:167`, `:258`; `tests/test_tools.py:45`.
- **Decisions 2 to 4 and 7 to 9.** No test line changes; the tests the tasks name hold the output with their expected values, among them the stage folder and the places of `Rendered` (`tests/test_production.py:24-26`) and the viewing film's scale filter (`tests/delivery/test_packaging.py:271`, `tests/delivery/test_viewing_encode.py:101`).

## Risks / Trade-offs

- [The pattern that finds an edition in a tool's arguments is built wrongly] → A tool run's duration record would name no edition. `tests/test_build_durations.py:275-283` holds the pattern's answers as expected values.
- [A test input that reads an owner no longer notices a rename] → The expectations stay literal (decision 10), and the acceptance compares bytes.
- [The renderer's usage text changes] → The Changelog entry names it; no test or caller reads it.
- [Import order] → Avoided by decision 1 (c): the renderer imports nothing new, so `tools` reports the same error first as before.
- [The cover check refuses a stage that it painted before] → Only a stage whose record and page disagree, which the geometry check, run on the same stage before it in a build, already refuses.
- [The acceptance is host-heavy] → Narration runs once; the pictures and the packages are built on each head, each step under its own host ticket, and the released films' checks under one ticket for each head.
- [The acceptance's checkout is a second worktree of the repository] → Task 9.7 removes it, with the work below it, once the records are kept.

## Migration Plan

Nothing migrates: no film's file, record or command changes. To roll back, revert the Change's commits.

## As built

The owners the decisions name exist as the design reads them at `1e4d459`: `production.py` with `Edition`, `Rendered` and `RENDITIONS`, `picture/stage-contract.mjs` with `RECORD`, `PAGE` and `frameContract`, `delivery/player.py`, `delivery/reproduction.py`, `released.ENGINE`, `MANIFEST`, `NPM_LOCK` and `PYTHON_LOCK`, and `picture.rendering.PICTURE_SIZE`. Their new members:

- Decision 1: `production.STAGE_PAGE` and `STAGE_RECORD`, and `Rendered.page`.
- Decision 3: `player.Version`, a named tuple of the five fields the decision lists; `player.kinds_at`, which takes a size's two kinds from `RENDITIONS`; `VERSIONS`; and `OPENING`, the version whose button starts pressed, which the page's video and status line read.
- Decision 5: `reproduction.release_name(edition, path)`.
- Decision 8: `Edition.srt`, `vtt`, `transcript`, `chapters` and `chapter_metadata`, and `player.PAGE`.
- Decision 9: `repository.ARTIFACTS` and `EVIDENCE`, and `production.STAGE`, the captioned stage's name as a format of the edition's code, which `tools.py` splits at the code to build its pattern; and `production.VIEWING_SIZE`, from which `VIEWING` and its scale filter are built.

Where the code says more than the design:

- The draft's stage is no `Rendered` (`Edition.draft_stage`), so `picture/draft.py` hands `record_render` its stage's page as `stage / STAGE_PAGE`.
- In `tests/test_adoption.py:51-54` and `:553-554` the pin's table key, its tag and the lock entries' name read `released.ENGINE`; the stand-in source URL `https://example.invalid/filmkit` is no read of the engine's name and keeps its words.

Line numbers above remain those of `1e4d459`; the Change moves some of them.

## Sources

- **[S1]** `build/evidence/release-0.25.0/reviews/review-ssot.md` in the canonical checkout, section C.
- **[S2]** `build/evidence/release-0.25.0/work/adoption-study/notes-section-c-dispositions.md` in the canonical checkout.
- **[S3]** The re-reading of the places said to stand once, `records/reread.md`, to be kept as `build/evidence/state-each-fact-once/reread.md`.
