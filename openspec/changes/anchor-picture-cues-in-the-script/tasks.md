## 1. The anchored form

- [x] 1.1 Write `src/filmkit/narration/anchors.py` with `require(script, edition)`: read each segment's
      `anchored_groups` into its plain thoughts and its anchors (id, thought, span of units of the text), and refuse
      every broken rule of the requirement "The engine refuses a broken anchor before it writes anything" at once, by
      edition, segment, thought and id, naming `script_edits` for plain thoughts edited by hand. Done when
      `tests/narration/test_anchors.py` passes, with a case for an unclosed mark, a close without an open, an id used
      twice, an id that is not kebab-case (`Order_2`, `order-`), an anchor without a unit and an anchor across
      thoughts, and with nested and crossing anchors and two ids on the same words read correctly.
- [x] 1.2 Call `anchors.require` before anything is written in narration's gate, `assemble`, `refresh-captions`,
      `stage-picture`, `check-picture`, `preflight`, `script_edits` and the report. Done when
      `tests/narration/test_anchors.py` holds that each of them refuses a broken script and writes no file; that a
      script without `anchored_groups` passes each as before is held by each command's own tests and by 2.1's golden
      timeline.

## 2. The timeline

- [x] 2.1 Capture, before any code of this Change, the timeline that `assemble` writes for a fixture script without
      anchors, as a golden file under `tests/soundtrack/`. Done when the file exists and names the engine version and
      commit that wrote it.
- [x] 2.2 `produce assemble` writes `anchors` (start, end, units, thought; ids in the order of their open marks) on
      every segment of an edition that marks any anchor, empty where a segment marks none, and the resolver refuses a
      mark whose units are not the words'. Done when `tests/soundtrack/test_assembly.py` holds an anchor's start and
      end equal to its first and last words' times, its units and thought, an empty object on a segment without
      marks, the resolver's refusal, and the timeline of the fixture without anchors equal, byte for byte, to the
      golden file of 2.1.
- [x] 2.3 `refresh-captions` copies the script's `anchored_groups` into each timeline segment, or removes them where
      the script holds none, with the `anchors` they take from the timeline's words; `anchors` joins
      `GENERATED_SEGMENT_FIELDS` and `anchored_groups` the fields that `narration_source` leaves out. Done when
      `tests/captions/test_refresh.py` holds an anchors-only change adopted with the soundtrack's SHA-256 unchanged and
      the presentation revision recorded, the anchors removed again, and a changed word still refused.
- [x] 2.4 An edition staged after an anchors-only refresh follows its script. Done when `tests/picture/test_rendering.py`
      refreshes a fixture edition after an anchor is added and then stages it: `stage-picture` accepts the timeline and
      the stage's `film.json` holds the anchors; at the engine before 2.3 the same test fails with "Current candidate
      timeline differs from its authored script".

## 3. Script edits

- [x] 3.1 `script_edits` applies replacements and splits to `anchored_groups` and fills `utterance_groups`, text,
      spoken text and the mirror from them; retakes follow the plain thoughts, and an edit of marks alone is written.
      Done when `tests/narration/test_script_edits.py` holds each scenario of the requirements "Script edits work on
      the anchored thoughts" and "A replacement or a split keeps an anchor on its words or refuses", a retake kept
      across an anchor edit, and a refused edit that writes no file.
- [x] 3.2 Add the `rewrite` edit: a segment's thoughts replaced whole, each anchor moved when its units occur once, or
      as often as before by rank, at word boundaries in English, and refused by name otherwise unless restated; the
      report names plain moves, moves by rank and moves into another thought apart. Done when
      `tests/narration/test_script_edits.py` holds each scenario of the requirement "A rewrite moves each anchor to the
      words it still says".
- [x] 3.3 Add the `anchor` and `unanchor` edits: an anchor placed at a span of units of its thought, guarded by its
      expected words, marks immediately around the span's first and last units. Done when
      `tests/narration/test_script_edits.py` holds each scenario of the requirement "Script edits mark and unmark
      words", an id already marked refused and an unknown id refused.

## 4. The report and the derived timeline

- [x] 4.1 Add `python -m filmkit.narration.anchors`: for each edition, each segment's anchors with thought, words,
      units and, where the timeline holds them, times, and with `--json` the same as one document; the ids one edition
      alone marks; exit 0 for them. Done when `tests/narration/test_anchors.py` holds the report and the JSON of a
      two-edition fixture with an id in one edition only, with and without timelines.
- [x] 4.2 Derive the timeline of the checks from a script (words 0.2 s each, 0.5 s between thoughts, 1.0 s before each
      segment, anchors by the resolver of 2.2, no captions) and write it with `--timeline <path>`. Done when
      `tests/narration/test_anchors.py` holds the requirement's scenario and the sample film's derived timeline.
- [x] 4.3 Give a timeline that other code built of its own words its anchors with
      `--place <timeline> --language <code>`, and let the engine's Node tests take the sample's anchors from it. Done when
      `tests/narration/test_anchors.py` holds the requirement "A timeline of other words takes its anchors from the
      engine" and no file below `tests/` reads the marks or resolves an anchor but through that command.

## 5. What the picture reads

- [x] 5.1 The headless runtime presents each segment's `anchors` through a recorder of the ids a composition reads,
      with a stand-in for an id the edition does not mark and an empty recorder where an edition marks none, and returns
      the reads with each draw. Done when `tests/picture/headless-composition.test.mjs` holds every unmarked id of one
      fixture scene found in one draw, the scene drawn to its end, and the timeline's bytes unchanged by the draw.
- [x] 5.2 Narration's prechecks draw the composition for each edition over its derived timeline, after the readings
      check, before any speech model loads and in a dry run too, and refuse each unmarked id read, by id, segment and
      edition; a scene that throws is named as not judged with the ids it read, and a composition that does not load
      as not judged for the whole edition; a missing tool or package refuses with its reason; a film without a
      composition is not asked. Done when `tests/narration/test_anchors.py` holds each
      scenario of the requirements "Narration refuses a script that does not mark what its picture reads" and "The
      check before narration names what it could not judge", with a model loader that a refusal never calls.
- [x] 5.3 `check-picture` records every unmarked id read while its audits draw, and refuses by those ids, also when an
      audit exits with an error. Done when `tests/picture/test_gates.py` holds both scenarios of the requirement "The
      picture gate refuses an anchor that the edition does not mark" and `render-picture` refusing the edition.

## 6. The sample film and the documents

- [ ] 6.1 The sample film keys its cues to anchors in both editions; its labels stay as they are. Done when
      `tests/picture/headless-composition.test.mjs` draws every frame of both sample editions with no unmarked id read,
      and a test in `tests/narration/test_anchors.py` holds that `examples/sample-film/picture/film.js` holds no search
      of the segment's words and passes only ids to its anchor helper.
- [ ] 6.2 Document anchors in the README (the field and its marks; that an anchored segment's plain thoughts are filled
      and changed through `script_edits`; the timeline's `anchors`; the refresh; the edits; the report and the derived
      timeline; the checks of what a picture reads; that a composition reads each anchor from the segment's `anchors`
      object; the units and how they differ from a composition's; which meaning of "anchor" is meant) and in the
      Changelog. Done when the README's sections name each and the repository's Markdown check passes on both files.

## 7. Acceptance on the films

- [ ] 7.1 In a scratch copy of one film whose picture passes `check-picture` on the built engine, migrate one
      segment: `anchor` edits from the spans its own `cue()` resolves (`count/cue-calls.mjs` of the draft), adopted by
      `refresh-captions`, and the segment's calls rewritten to read `s.anchors`. Compare every frame's paints headlessly
      before and after, then render the edition before and after on the built engine in one render ticket. Done when
      the record under `build/evidence/anchor-picture-cues-in-the-script/` shows the same paints frame by frame and the
      two renders' `drawn_sha256` equal.
- [ ] 7.2 In scratch copies of the three films at their release tags, with their timelines first refreshed by filmkit
      0.27.0 on the same inputs and no review round binding them, run the built engine's `refresh-captions` and the
      check before narration as a dry run on their released and December scripts. Done when the record under
      `build/evidence/anchor-picture-cues-in-the-script/` shows each edition's timeline and assembly receipt with the
      SHA-256 that 0.27.0 gave them, no anchor read, and on the December scripts the scenes whose `cue()` throws named
      as not judged and nothing refused.
