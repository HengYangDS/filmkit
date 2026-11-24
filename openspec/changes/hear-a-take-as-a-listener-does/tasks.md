Every task leaves the engine's whole suite passing on its commit, run as the child of a host ticket where the host's
rules count it heavy. Each group names the tests that show it; a case goes to the file named, or, where that file
stands at the repository's 500-line ceiling, to the file that task 1.1 names. Groups 2 and 3 depend only on group 1,
so either can be cut alone if the owner withholds the other part (design decision 8); task 4.1 then keeps the new
input that remains.

## 1. The base

- [x] 1.1 Read every site again on the base, `v0.31.0`: `recognition.Names`, `Read`, `read_units`, `alike`, `_ways`
      and `compared`, and every caller of `compared` and `reading_distance`; the judgment's `studio`, `bench`, `Held`,
      `held`, `judge` and `choose`, and `judge.py`'s record and exit; `converge`'s rounds, record and exit;
      `audition.propose` and its record; `selection.select`; `preflight.clarity`; `check-sound`'s clarity; the
      English pronunciation's targets that declare a reading (`letter-name`, and `arpabet` under `lexical_stress`);
      `supply.py`; `tests/conftest.py`'s host tools; `film.Narration` and `author`; `languages.Language` and the test
      helper that derives `xa` and `xb`; the golden request test; whether the sample's local acceptance judges any
      take; and the effective lines of each test file named below. Done when
      `build/evidence/hear-a-take-as-a-listener-does/research.md` names the base commit and each site, caller and
      answer with its file and line, and the file each case goes to.
- [x] 1.2 Record the SHA-256 of `tests/narration/golden/sample-requests.json` and
      `tests/narration/golden/receipts.json` at the base. Done when `research.md` holds both.

## 2. English words heard by their pronunciation

Shown by `tests/test_languages.py`, `tests/narration/test_cmudict.py`, `tests/test_supply.py`,
`tests/narration/test_recognition.py` and `tests/narration/test_units_line.py`.

- [x] 2.1 Add `latin_heard` to the language declaration, with the kinds `letters` and `cmudict-pronunciations`;
      declare `cmudict-pronunciations` in `en.toml` and `letters` in `zh.toml`, each with its comment. Done when
      `tests/test_languages.py` holds both values, `xb`'s equal to English's and `xa`'s to Chinese's, and a
      declaration that names another kind, or none, refused when it loads with the language and the field named; and
      passes.
- [x] 2.2 Write `src/filmkit/narration/cmudict.py`: the pin (the file's URL at commit
      `74790861f652b15e4ac49015a90074ad62a27690`, its SHA-256
      `81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22`, its 3,618,488 bytes and its place
      `build/runtime/tool-cache/cmudict/cmudict.dict`), and the reader of each headword's pronunciations in the file's
      order: comments dropped, numbered variants after their headword's first, and secondary stress read as none
      (design decision 2); a missing file or one of other bytes refused in one line that names
      `python -m filmkit.supply`. Done when a new `tests/narration/test_cmudict.py` reads a fixture of CMUdict lines
      with a comment, a numbered variant, `tears`, `catalogue` and `catalog`, and holds the first pronunciation kept
      first, `catalogue`'s equal to `catalog`'s, and both refusals; and passes.
- [x] 2.3 Let `filmkit.supply` download the pinned file into its place before the models, check its size and SHA-256,
      move it into its place only once checked, and keep a file in place whose SHA-256 is the pin's; its report names
      the file. Done when `tests/test_supply.py` holds, with the download stubbed, a checked file in its place, a
      download of other bytes refused with nothing left in the place, and a file in place kept without a download; and
      passes.
- [x] 2.4 Give `recognition.Names` the pronunciations by which its language hears Latin units and the edition's
      declared readings, none in `NO_NAMES`; give each Latin unit that says no declared term its pronunciations in
      `read_units`, looked up as written and then by its letters, a text unit read by the readings its edition's
      pronunciation declares or else by CMUdict's first, and one declared by letter names by its letters only; and let
      `alike` count two Latin units alike when the transcript unit's first pronunciation is one of the text unit's
      readings. Done
      when `tests/narration/test_recognition.py` holds every scenario of the requirements "English words are also
      compared by their pronunciation", "Pronunciations are compared with primary stress, secondary stress read as none" and "A
      word the dictionary does not hold, and a declared term, are compared as before", over a fixture dictionary, and
      the `film-engine` scenario "How a language hears a transcript's Latin-script words"; every test of the file at
      the base passes unchanged, as does `tests/narration/test_terms.py`, whose `respelling_failures` reads no
      pronunciations.
- [x] 2.5 Let `judgment.studio` read the dictionary before any model loads for an edition whose language declares
      `cmudict-pronunciations`, and the readings its pronunciation declares (letter names, and every `arpabet` of a
      target), refusing nothing it would not refuse today; let `bench` pass both in the edition's names, and the
      judgment's record name the dictionary's URL and SHA-256 and bind the pronunciation by its SHA-256. Done when a
      new `tests/narration/test_units_line.py` holds an English bench that hears "labelled" for "labeled" over the
      fixture dictionary, refuses "I" for a declared "AI", a Chinese bench that reads no dictionary, the record's
      fields, and every scenario of the requirement "A judgment reads only the pinned dictionary", with a stub of the
      model loader that a refusal never calls; and passes.
- [x] 2.6 Add the host tool `cmudict` to `tests/conftest.py`, present where the supplied file holds the pinned SHA-256,
      and in `tests/narration/test_cmudict.py` the function that lists, for given text words and a dictionary, the
      other spellings the rule takes for each, with two tests: one over a fixture of CMUdict lines (for "labelled",
      "tiers", "their", "catalogue", "AI" declared by letter names, and "to"), and one marked `cmudict` over the pinned
      file that holds, for each English word of the sample film and each word of the requirements' scenarios, the list
      the test states (the sample's 24 entries of the appendix's list, among them to: thuy, too, tu, tue, two).
      Done when the fixture test passes, and where no file is supplied the run reports the marked test skipped among
      the host tools.

## 3. The owner's hearing, and the thoughts for the ear

Shown by `tests/test_film_hearings.py`, `tests/narration/test_units_line.py`, `tests/narration/test_selection.py`,
`tests/narration/test_converge.py`, `tests/narration/test_audition.py`, `tests/test_preflight.py` and
`tests/soundtrack/test_sound_gates.py`. Tasks 3.4 to 3.7 carry design decision 6.

- [x] 3.1 Add `Narration.heard` to `film.py`: records of `edition`, `thought`, `take`, `lines` (one or both of
      `units` and `clarity`), `listener`, `date` and `note`, refusing an edition the film does not declare, a take that
      is not 64 lowercase hexadecimal digits, lines that are empty, repeated or name another line, a listener other
      than the film's `author`, a missing or empty field and a second record of one take. Done when a new
      `tests/test_film_hearings.py` holds a record loaded and the scenarios "A listener who is not the owner" and "A
      record that names no audio or no line", and passes.
- [x] 3.2 Let `judgment.held` carry the edition's records, and `judge` pass each line a record names for the take
      whose thought and audio SHA-256 it names, the line's record naming the listener and the date, or saying that the
      hearing was not needed where the take passes the line without it. Done when `tests/narration/test_units_line.py`
      holds every scenario of the requirement "The owner's hearing settles the lines it names for one take" but "A
      hearing of the words alone", and passes.
- [x] 3.3 Let `selection.select` refuse, before it writes anything, each record of the edition whose take is not its
      thought's selected take. Done when `tests/narration/test_selection.py` holds the scenarios "A record of another
      take at selection" and "A record of no thought", each with no file written, and passes.
- [x] 3.4 Let `judge`'s clarity line name for the ear a take under its thought's line whose clarity no record
      settles, outside the take's failing lines, and let `filmkit.narration.judge` record and name each thought for
      the ear and exit 1. Done when `tests/narration/test_units_line.py` holds the scenario "A hearing of the words
      alone", the scenarios "A film with a floor and no thought line", "A kept thought above its line", "A thought
      under the line, heard on this take" and "A thought under the line, heard on another take", and every scenario of
      "An edition's narration is judged as a whole" and "A thought for the ear waits for the owner's hearing"; and
      passes.
- [x] 3.5 Let `converge` generate no candidate for a thought that is only for the ear, choose among a thought's takes
      by their margins as before, and record and name each thought for the ear, exiting 1 while one waits. Done when
      `tests/narration/test_converge.py` holds the scenarios "A thought under the line, heard by no one" and "A
      thought under the line that another line refuses", with a stub generator that the first never calls; and passes.
- [x] 3.6 Let `audition.propose` put a take above its clarity line before one for the ear, and its proposals name a
      take for the ear as such. Done when `tests/narration/test_audition.py` holds every scenario of "An audition
      qualifies a take by the judgment's lines" over stub takes, loading no model; and passes.
- [x] 3.7 Let `preflight.clarity` refuse nothing for a thought whose selected take the owner's hearing settles for its
      clarity, and name each thought it refuses for its clarity for the ear with its selected take's audio SHA-256;
      leave `check-sound` reading no record. Done when `tests/test_preflight.py` holds every scenario of the
      requirements "Preflight takes the owner's hearing of the selected take" and "A film declares the line a single
      thought's clarity is judged against", and `tests/soundtrack/test_sound_gates.py` holds every scenario of "The
      sound gate refuses the lines reviewers hold"; and both pass.

## 4. No request changes

Shown by `tests/narration/test_synthesis.py`.

- [ ] 4.1 Add the test of the requirement "What judges a take binds no take's request": in a copy of the sample with
      a record of hearing declared for one English thought and the fixture dictionary in the pin's place, each
      edition's planned requests equal `SAMPLE_REQUESTS`, and `candidates.request_sha256` of one golden receipt child
      at one seed equals its value without them. Done when the test passes, and
      `git diff --exit-code v0.31.0 -- tests/narration/golden/` reports no change, with both digests equal to task
      1.2's.

## 5. The documents

- [ ] 5.1 Document in the README the supply step's download (file, source, size and licence); the units line's
      comparison by pronunciation, with what it lets through (design decision 1, in short), and `latin_heard`;
      `[[narration.heard]]`, with its fields, its listener, what it passes and what refuses it; and the thoughts for
      the ear in `judge`, `converge`, `audition` and preflight. Add to `NOTICE` CMUdict as the supply step downloads
      it and the judgment reads it, with its copyright line and licence, and to the Changelog, under its category,
      what a film does: run the supply step again, record the owner's hearings, and have him hear each thought for the
      ear. Done when the README's sections name each, and the repository's Markdown check passes on the three files.

## 6. Acceptance

Records under `build/evidence/hear-a-take-as-a-listener-does/`. Tasks 6.1 to 6.4 are light and load no model; 6.5
and 6.6 run models and each waits for its own GPU ticket under the host's rules.

- [ ] 6.1 Run `uv run --frozen --offline python -m filmkit.supply` in the engine's repository with the built engine,
      its models already in place (the supply step reaches the network for the dictionary alone). Done when `trial.md`
      records the dictionary's place, size and SHA-256, equal to the pin, and the models kept.
- [ ] 6.2 Run `uv run --frozen --offline pytest -m cmudict tests/narration/test_cmudict.py` with the supplied file in
      place. Done when the marked test of task 2.6 passes on the pinned file and `trial.md` records the run.
- [ ] 6.3 Write `build/runtime/work/hear-a-take-as-a-listener-does/recompare.py`, which compares a recorded
      transcript with its spoken text by the built engine's `recognition.compared` over the supplied dictionary and
      loads no model, and with it compare again each English thought's recorded transcript in the fused trial's judgments
      (`build/runtime/work/trial-fused/<copy>/build/evidence/editions/en/ear-first/judgment.json`, for `ch1-5`,
      `ch6-11` and `ch9-10`, and `build/runtime/work/trial-december/<film>/…` for `full` and `essentials`) with its
      spoken text in the receipt beside it, by
      `uv run --frozen --offline python -I -B build/runtime/work/hear-a-take-as-a-listener-does/recompare.py --judgments`.
      Done when `trial.md` shows 13.2 differing by no unit by reading, 28.3 (`ch6-11`), 29.3 (`ch9-10`), 09.1,
      28.4, 24.9, 28.2 and 28.8 differing as recorded, the December full film's eight mismatches differing as recorded
      but 19.3 by one unit fewer, and no thought that passed the units line differing.
- [ ] 6.4 Compare again in the same way each English recording of the released films, `ddwg-film`,
      `ddwg-essentials-film` and `ethos-film`, read without changing them: each segment's transcript in
      `build/evidence/editions/en/ear-first/asr.json` against its spoken text in the receipt beside it, by
      `uv run --frozen --offline python -I -B build/runtime/work/hear-a-take-as-a-listener-does/recompare.py --film <root>`
      for each film's root. Done when `trial.md` names each recording whose count moves, with its pairs, shows none
      that moves from fewer differing units to more, and states the films' let-through list again from the supplied
      file, equal to the appendix's list.
- [ ] 6.5 In scratch copies of `ch1-5` and `ch6-11`, declare the owner's records for 02.10, 14.4, 21.3 and 09.1
      (D-44), each with `lines = ["units"]` and its take's audio SHA-256 from its copy's judgment, and run
      `python -m filmkit.narration.judge --language <code>` for both editions of each copy, as the child of one GPU
      ticket. Done when `trial.md` shows the four takes passing their units line with the owner named, 28.4 refused by
      its phrase and units lines, 13.2 passing by reading, 28.3 refused by its units line alone, the seven thoughts under their clarity line
      (Chinese 03.5, 04.1, 04.4, 07.7, 12.4 and 15.4; English 14.1) named for the ear with their takes' paths and
      SHA-256 and refused by nothing else, every other verdict as recorded, each judgment bound to the receipt SHA-256
      recorded before, and no recording written.
- [ ] 6.6 In the scratch copy of `ch1-5`, run
      `python -m filmkit.narration.audition audition --language zh --targets <file naming 03.5> --takes 3` as the child
      of one GPU ticket, then `python -m filmkit.narration.audition apply --language zh --proposals <its file> --dry-run`.
      Done when `trial.md` shows the proposal ordered with takes above the line first, a take under it named for the
      ear if it is proposed, and the dry run writing no cast.
