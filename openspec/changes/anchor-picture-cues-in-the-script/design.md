## Context

See [proposal.md](proposal.md) and the capability's delta ([specs/narration-anchors/spec.md](specs/narration-anchors/spec.md)).
The research behind this design, with the exact count, the comparison of six ways and what was not read, is in
the draft's `research.md`; the list of stranded cues is its `stranded-cues.tsv`; the first independent reading is its
`reading-1.md`, whose findings this version takes as the films session ruled on them [S7]. These files, and the
count's scripts under `count/`, stay with the draft in the films session's work folder, outside the repository.

How the picture meets the narration today, as read on 23 November 2026 at filmkit `6d59ad6` (0.27.0) [S2], each file and line
below read again at `be4f243`, filmkit 0.29.0 on `dev`, which this Change is built on:

- `produce assemble` writes the timeline: the script's fields, and for each segment its picture and voice times and
  `words`, one record per aligned item with its text and times (`soundtrack/assembly.py`, `_timed_segment`, line 414).
  The aligner aligns the segment's written `text` (`narration/alignment.py:114`), and the engine refuses items whose
  units are not exactly the text's (`narration/spoken_units.py`, `_require_cover`, line 66). Units, here and below, are
  the Han characters, Latin letters and digits of the text, the units the aligner covers; a `spoken_text` can hold
  others.
- The picture's data is that timeline with a render offset and the edition (`picture/rendering.py`, `film_data`,
  line 126), inlined as `window.FILM`. Staging refuses a timeline whose segments do not hold every field of their
  script segments (`follows_script`, line 67, through `candidate_picture_inputs`). The headless audits of
  `check-picture` read the timeline file itself (`picture/gates.py:423`, `:451`; `frame-audit.mjs:50`).
- The engine offers no anchor, mark or word index a picture could name. The nearest things are the thought key
  `"segment.index"` of `script_edits` and `[narration.terms]`, and the retakes, which follow their thought by the
  SHA-256 of its text (`narration/retakes.py`, `rebind`, line 140).
- `produce refresh-captions` separates a script's narration from its presentation: it adopts a script that differs
  from the timeline only in caption phrases (and two vestigial event fields) without assembling again, copying the
  caption phrases into the timeline (`_adopt_caption_authoring`, line 131), and records the revision as "Only
  authored visual and caption presentation changed; source copy, words and PCM preserved" (`captions/refresh.py`,
  `PRESENTATION_SCOPE` line 39, `narration_source` line 64).
- The engine has no script loader of its own: scripts are read in about 40 places [S7].

The three films each carry their own copy of `picture/film/timing/cues.js` [S3]. The copies already differ: the full
film counts clause ends over `spoken_text ?? text`, the essentials and ETHOS films over `text`, and the ETHOS film
also records each cue's word end. Each scene calls `cue(s, zh, english)` with both editions' phrases, so one call holds
two copies of narration. Two checks of these copies exist or are planned: each film's composition test paints every
scene against both scripts with words of 0.2 s and fails on the first missing cue of a scene, before narration
(`tests/picture/page.mjs`, `authoredTimeline`) [S3]; and the umbrella draft `decide-before-heavy-work`, Decision 6,
plans a report from the script editor of the quoted phrases an edit leaves without their words [S2]. Both find a
stranded copy; neither removes it. This Change replaces that report of Decision 6 for cues only; that draft is not
edited here, and its report stands for labels [S6].

"Anchor" in this Change means a named span of a script's words. The engine already uses the word for the template's
substitution points (`picture/template.py`, `ANCHORS`) and for a text's anchor point in the typography audits; the code
of this Change lives under `narration/anchors.py` and the timeline's `anchors`, and the README says which is meant
where they meet.

## Goals / Non-Goals

**Goals:**

- The words a picture change is keyed to stand once, in the edition's script, and the picture names them by an id.
- A rewrite of the narration either carries each anchor to its words or names it at the moment of writing, before
  any narration; the picture code is not touched for words it merely quoted.
- An anchor that an edition's picture reads and its script does not mark is refused before any model loads, and
  again before any render.
- A film that marks no anchor keeps every byte it has today. A film that adopts anchors does so without narrating or
  assembling again, and proves that its frames did not change against the same engine: two renders on one engine,
  before and after its migration. Nothing is proved against the released films, which a browser rendered under
  filmkit 0.22.3 and whose receipts hold no drawn-frame digest [S7].

**Non-Goals:**

- Migrating the three films (their `cue` functions, 1,240 calls and the December texts' anchors). That is each film's
  lane; this design gives the order and the proof it needs (Migration Plan).
- Labels whose text repeats narration words: a follow-on Change lets such a label take its text from its anchor (in
  the full film 45.0 % of Chinese and 38.0 % of English cue sites time a label by its whole words [S4]) [S6]. The
  sample film's labels stay as they are.
- English `caption_phrases`, which repeat the whole text with breaks: a follow-on Change puts a break mark in the same
  marked form and removes that copy [S6].
- `decide-before-heavy-work`, Decision 12, which carries the readings' keys (segment and character offset) through
  `script_edits` to the same occurrence of their term, by a rule unlike this Change's: a second carrier of a place in
  the text, to be reconciled with anchors in a follow-on Change, not here [S6][S7].
- A picture API in the engine. The template holds no timeline engine, and the films' clause logic differs.

## Decisions

1. **The narration owns where the picture changes: anchors marked in the script's own words, named by id in the
   picture.**
   - **Rests on:** the count [S1]: 432 stranded cues over the six December editions, and 64 that still resolve but
     in a thought of another number, re-derived by the reader's own parse [S7]; the owner's rule C-2 and the shared
     rule that a check refusing a disagreement afterwards is not a source; the precedents of marking positions inside
     a text by name and taking their times from the speech or the alignment (SSML's `mark`, EPUB 3 Media Overlays'
     fragment ids) [S5].
   - **Considered:** (a) anchors in the script; (b) cues by thought and unit index; (c) the phrases kept, checked and
     suggested by an engine command before the build; (d) a table of quoted words beside the script, keyed by id;
     (e) labels timed by their own text, as the sync audit times them; (f) cues keyed to the concept contract's
     renderings. The full comparison is the table in `research.md`, section "Comparison".
   - **Chosen because:** (a) is the only way in which the words stand once: an anchor is a position inside the words
     and moves with them. (b) removes the copy but goes wrong in silence when a word before the index changes. (c)
     keeps 3,980 copies and makes their failure earlier and complete, not impossible. (d) keeps a copy beside its
     source and refuses afterwards. (e) covers the 36.8 to 49.9 % of cue sites that time a label by the label's
     whole words [S4], and the label text is itself a copy. (f) covers 2 to 5 % [S4].
   - **Applies to:** `src/filmkit/narration/anchors.py` (new).
   - **Reopened when:** a film needs a picture change keyed to something other than spoken words, such as a pause.
2. **The marked form is a new optional field, `anchored_groups`; `utterance_groups`, `text`, `spoken_text` and the
   narration mirror are filled from it. Its rules have one home, `narration/anchors.py`.**
   - **Rests on:** 21 engine files read `utterance_groups`, two of them headless audits, and several count its units
     (`thought_ends`, `authored_groups`); `text` binds every recording by its SHA-256 [S2]. The engine already stores
     filled fields (`text` from the groups, `spoken_text` through the pronunciation contract, both rebuilt by
     `script_edits`) and an authored presentation copy of the text, `caption_phrases` (`captions/phrasing.py:35`).
     The films session ruled that the check has one home [S6].
   - **Considered:** marks inside `utterance_groups`, with every reader taking a plain view; the new field, with the
     plain fields filled; a quoted table (Decision 1 (d)); offsets beside the text; the rules checked where each
     command reads its script.
   - **Chosen because:** marks inside the authored groups would reach every reader that counts units, and a reader
     missed would count an id's letters as speech; the new field leaves every reader and every recording binding as
     it is. A filled field is derived, which C-2 allows while nobody keeps it by hand: the refusal and the README say
     that an anchored segment's plain thoughts are filled and name `script_edits` as the way to change its words.
     `anchors.require(script, edition)` holds every rule and is the one check; each command that reads marks or
     anchors calls it before it writes anything: narration's gate, `assemble`, `refresh-captions`, `stage-picture`,
     `check-picture`, `preflight`, `script_edits` and the report. The resolver refuses a mark whose units are not the
     words', so whatever computes anchors fails closed.
   - **Applies to:** `narration/anchors.py`, the commands named, `narration/script_edits.py`.
   - **Reopened when:** the engine reads scripts through one loader that gives every reader the plain view; then the
     filled fields need not be stored. That is the end state.
3. **An anchor is written `{id}words{/id}`, and anchors may nest and cross.**
   - **Rests on:** no thought of the twelve scripts read holds a brace, a bracket or an angle bracket [S4]; on the
     released timelines, today's cue spans cross one another in 20 Chinese and 41 English pairs in the full film, 3 in
     the essentials film and 12 in the ETHOS film, and none crosses a thought boundary [S4].
   - **Considered:** Pandoc's bracketed span `[words]{#id}`, which nests but cannot cross; SSML's point `mark`, which
     needs two points and two names for a span; offsets.
   - **Chosen because:** a paired mark is two named points with one name, so crossing spans are written as they
     stand, and the text between the marks is the text the owner approved.
   - **Applies to:** `narration/anchors.py`.
   - **Reopened when:** a narration needs a literal brace.
4. **The assembly resolves each anchor from the timeline's own words, once, and the timeline carries the result.**
   - **Rests on:** the films' `cue()` takes its times from `s.words` [S3]; the audits read the timeline file [S2].
   - **Considered:** resolving at staging, in `film_data`, which the audits would not see; resolving in each film's
     picture, which repeats a resolver three times, as `cues.js` is repeated today.
   - **Chosen because:** one resolver, called by `assemble`, by `refresh-captions` and by the derived timeline of
     Decision 8, gives the stage, the audits and the renderer one value. `start` and `end` are the times that `cue()`
     returns for the same words (the first word's start, the last word's end); `units` lets a film keep its own clause
     logic; `thought` serves the report. In an edition that marks any anchor every segment carries `anchors`, empty
     where it marks none, so the audits and the render see one shape; ids stand in the order of their open marks, so
     the bytes are fixed. `anchors` joins `GENERATED_SEGMENT_FIELDS`. A timeline whose script marks none gets no
     field and keeps its bytes.
   - **Applies to:** `soundtrack/assembly.py`, `captions/refresh.py`.
   - **Reopened when:** a picture needs an anchor's time inside a word.
5. **Anchors are presentation: `refresh-captions` adopts a change of anchors alone and writes it into the timeline.**
   - **Rests on:** the refresh's existing split between narration and presentation and its revision record [S2];
     `follows_script`, which refuses at staging a timeline whose segments lack a field of their script segments [S7].
   - **Considered:** requiring `assemble` again, which decodes every recording for a change that alters no sound;
     letting `follows_script` leave `anchored_groups` out of its comparison.
   - **Chosen because:** marks change no word, no spoken text and no sample, and the refresh already proves that the
     words and the soundtrack are those the receipt binds. The refresh copies the script's `anchored_groups` into each
     timeline segment, or removes them where the script holds none, as it copies caption phrases, and writes the
     `anchors` they take from the timeline's words; the timeline then follows its script, and `follows_script` keeps
     comparing every authored field. `anchored_groups` joins the fields that `narration_source` leaves out.
   - **Applies to:** `captions/refresh.py`.
   - **Reopened when:** anchors come to change what is spoken.
6. **Script edits keep an anchor on its words or refuse by name; the writer decides at the moment of writing.**
   - **Rests on:** `script_edits` applies exact replacements and splits and is the films' way of changing a script;
     the retakes show the engine's habit of following content and naming what it releases [S2]. On the December
     texts, a rewrite that moves anchors whose words occur once, or as often as before by rank, carries 4,345 of
     4,798 cue sites and names 453: 431 whose words are gone and 22 whose count of occurrences changed [S1]. Of the
     literal phrases that resolve today, 232 are not substrings of their segment's text, and one English carry of
     1,738 would land inside a longer word [S7].
   - **Considered:** carrying by a character diff of old and new text, which can place an anchor on a repeated word
     in silence; releasing an anchor silently, as a retake is released, which would leave the picture to fail at
     `check-picture`, after narration; refusing every anchor of a rewritten segment, which would name 4,564, since
     the December texts rewrite every segment but two of the full film's English and one each of the other films';
     an `anchor` edit that finds its words by searching the text.
   - **Chosen because:** every anchor either keeps its words, follows them to the one place they stand, or is named;
     none moves in silence, and the decisions are about as many as the strands that must be fixed under any design.
     A replacement whose phrase is exactly an anchor's words keeps the anchor, since that is the commonest rewording of
     a keyed term. In English a carried occurrence begins and ends at word boundaries. An `anchor` edit places its
     marks at a span of units that the edit names, guarded by the words it expects there, and never searches the
     text; once placed, an anchor is found by its marks. Retakes follow the plain thoughts, and an edit of marks alone
     is written. The report names moves by rank and moves into another thought apart from plain moves, for review.
   - **Applies to:** `narration/script_edits.py`.
   - **Reopened when:** the named decisions of a real rewrite prove mostly mechanical; then a rule may decide them.
7. **The engine gives the picture data, not a function.** The composition reads `s.anchors[id]` with its own helper,
   which throws on an unknown id; with Decision 8 that throw guards only the real render.
   - **Rests on:** the README's contract that the template holds no timeline engine; the films' differing clause
     logic [S3].
   - **Considered:** an engine helper injected into every stage.
   - **Chosen because:** it would bind the films to one clause rule they do not share, and the data alone is enough.
   - **Applies to:** the README; the sample film's composition.
   - **Reopened when:** a fourth film copies the same helper.
8. **What the picture reads is checked twice: before narration, on a timeline derived from the script, and by the
   picture gate, on the timeline.** In both, the engine's headless runtime presents each segment's `anchors` through a
   recorder of the ids read from it, and gives a stand-in for an id the edition does not mark, so that the scene goes
   on and every unmarked id of a scene is found; an empty recorder stands where an edition marks none, and any read
   there is refused, so the difference in shape never reaches a render.
   - **Rests on:** the films session's answers 2 and 4 and its rulings on the reading's findings 5 to 7 [S6]: an anchor
     an edition's picture reads must exist in that edition's script, refused at the cheapest point, before any model
     loads; every unknown id of a scene is reported, and the refusal by id is kept when the frame audit exits 1; the
     timeline drawn before narration is derived from the script by the engine, not a second copy of the films'
     `authoredTimeline`; a check whose tool or packages are missing refuses with its reason, and a composition that
     does not load is named, edition-wide, as not judged, whether or not the film marks anchors, and narration goes
     on (the films session's ruling of 23 November, about 12:33, which revises its ruling on finding 7, on the
     build's evidence that the full and ETHOS films' December pictures throw while they load). This research drew a
     whole edition in 3 to
     10 s at a step of 0.25 s, and the calls reached did not change from 2 s down to 0.05 s [S1]. Today a throw inside
     the frame audit makes it exit 1 before any gate record is written (`picture/gates.py`, `run_audits`) [S7].
   - **Considered:** the picture declaring the ids it reads, a second list of the same ids; a static parse of the
     films' code, which misses the 39 calls with computed phrases [S1]; the picture gate alone, which speaks after
     narration; letting the film's helper throw, which ends the scene at its first unknown id and, at the gate, loses
     the refusal behind the audit's exit; refusing, before narration, a scene that throws for another reason.
   - **Chosen because:** the recorder sees exactly what the composition reads, computed ids included, and needs no
     declaration; the stand-in lets one draw name every unmarked id, and the gate refuses from its record whatever
     else an audit reports. The derived timeline is one builder in the engine (the script's fields; one word per Han
     character and per run of Latin letters and digits, 0.2 s each; 0.5 s between thoughts and 1.0 s before each
     segment; the anchors by the resolver of Decision 4; no captions), and the report writes it for the films' own
     tests, so no film keeps a derivation or a resolver of its own. A scene that throws for another reason before
     narration is named as not judged, with the ids it read before it threw, so that a text can be narrated ahead of
     its picture, as the December trials are; a late find then costs a marks edit and a refresh, not a narration,
     unless the fix needs other words [S7]. A composition that does not load is named the same way, for the whole
     edition, with its error's one line: the picture gate after narration still refuses before any render, so
     nothing wrong reaches a film, and the check's answer says not judged, not pass. A tool or package that is
     missing refuses with the reason, and so does an unmarked id read by a scene that loads.
   - **Applies to:** `picture/headless-composition.mjs`, `narration/narrate.py` and the narration's prechecks,
     `picture/gates.py`, `narration/anchors.py` (the derived timeline).
   - **Reopened when:** a film reads anchors in a way the recorder cannot see, such as by copying the object first.
9. **Ids name what the anchor marks.** The engine requires kebab-case and one id per segment and edition, and lets two
   ids mark the same words. A film keeps one vocabulary of ids. At migration, ids start from the picture's variable
   names where those say what the span is, normalized to kebab-case names of what the anchor marks, and are reviewed
   once; no id is derived from a line position. Anchors on the same words share one id when the picture uses them as
   one change, and take two ids otherwise.
   - **Rests on:** the films session's answers 1 and 3 [S6]; 1,368 Chinese cue sites but 1,333 distinct spans in the
     full film [S4].
   - **Considered:** ids from file and line; one id per distinct span.
   - **Chosen because:** an id outlives its line and its words; it must name the picture change, and two changes on
     the same words are still two changes.
   - **Applies to:** `narration/anchors.py` (the pattern), the films' migration (the names).
   - **Reopened when:** a film needs ids shared across its films.

## Risks / Trade-offs

- **Dense marks.** A full-film edition would hold about 1,300 anchors in 30 segments (1,333 spans in Chinese, 1,304 in
  English [S4]). → Every reader and reviewer reads the filled plain fields; the report lists anchors by segment; two
  calls that the picture uses as one change on the same words share one id (Decision 9).
- **Decisions are moved, not removed.** The December texts still need about 453 placements, where copies need 432
  fixes. → They are made once, in the script, beside the words; afterwards a rewrite that keeps the words keeps the
  picture.
- **Units.** The engine counts Han characters of the basic block, ASCII letters and digits; the films' `units()` counts
  every letter and number. They agree on all twelve scripts read [S1][S7]. → A film's helper takes `start` and `end`
  from the anchor and uses `units` only for its clause logic; the README names the difference.
- **Carried over edited words.** An anchor kept over words edited inside it (`轻量档` to `低风险档`) keeps the picture
  change on words whose meaning may have shifted. → The report names every such anchor with its words before and
  after.
- **Reads the recorder cannot see.** A composition that copies `s.anchors` before reading it hides its reads. → The
  README states that a composition reads each anchor from the segment's `anchors` object.
- **A longer narration start.** The check before narration draws both editions once, 3 to 10 s an edition at this
  research's step [S1].
- **Two forms of the words in one file.** A hand edit of one leaves them apart. → Every command that reads marks
  refuses it before writing, naming the segment and `script_edits`.

## Migration Plan

The engine change is additive: it is released, and no film changes until it adopts it. Each film then works in its
own lane on that engine, in this order, because the first steps prove that its picture did not change.

**Which picture and which words.** The full film and the ETHOS film start from their released pictures and released
timelines. The essentials film starts from its December picture, the trial clone's edited one, on its narrated
December timelines; it first fixes the 6 Chinese and 7 English lookups that still strand there [S1], so that the
picture to migrate draws whole.

1. **Spans.** Run the film's own cue functions over those timelines and record, for each call, the exact span of units
   it resolved in each edition. `count/cue-calls.mjs` does this today in 3 to 10 s an edition [S1]; it covers every
   call that the static parse finds and every phrase computed at run time.
2. **Anchors.** A generator writes one `anchor` edit for each span (the thought, the span of units, the id, the words
   it expects), from the cue's resolution and never from a search of the text; the 232 phrases that are not substrings
   of their segment's text are migrated the same way and listed for review [S7]. Ids are named as Decision 9 says and
   reviewed once: between 4,614 anchors (one per distinct span) and 4,798 (one per lookup), as the picture's changes
   share words. `script_edits` applies the edits and `refresh-captions` adopts them. No narration, no assembly.
3. **Picture.** Replace each call by its id and the search in `cues.js` by a read of `s.anchors`. That is 1,240 call
   expressions in 106 files, and by hand the phrases of the 39 computed calls: at least 91 helper calls that feed
   them and 169 entries of the ETHOS film's keyed tables, besides the full film's arrays in segments 06, 12, 13, 14,
   17 and 23 [S7].
4. **Proof.** Draw every frame of both editions headlessly before and after the migration and compare the paints;
   then render the picture before and after its migration on the same engine, on the native canvas (0.24.0 or later),
   in one render ticket, and require the two renders' `drawn_sha256`, the digest of every drawn frame's pixels, to be
   equal. The proof compares two renders of one engine and says nothing against the released renders.
5. **December.** Apply the approved texts as `rewrite` edits on the anchored scripts; place the anchors they name
   (about 177 and 87 in the full film and 85 and 29 in the ETHOS film [S1]; the essentials film's December words are
   already its starting point); then narrate only what the December texts have not narrated: the full film's two
   editions and the ETHOS film's English one. A rewrite that keeps a thought's plain text keeps its recordings bound.

Rollback: before step 5, a film that reverts its scripts and picture to its starting point is that picture; the
engine release changes nothing for it.

## Open Questions

1. **A scene that throws, or a composition that does not load, before narration.** Decision 8 names either as not
   judged and does not refuse, so that a text can be narrated ahead of its picture. Should a film be able to declare
   that narration requires every scene judged?
2. **The pending rewrites.** The drafted D-27 rows would strand about 27 more cues as copies (the films session's
   figure, not counted here); under anchors they become named placements in the same rewrite.

The seven questions of the first draft were answered by the films session on 23 November [S6]; Decisions 8 and 9,
the requirements on what the picture reads and the Non-Goals carry the answers.

## Sources

Read or measured on 23 November 2026 between 03:00 and 05:20 CST, read only.

- **[S1] The count:** `count/cue-calls.mjs`, `count/wrapper.js` and `count/report.py` in the draft's folder, their checks and
  counts in `count/summary.json`, the list in `stranded-cues.tsv`; the rewrite estimate of Decision 6 and the
  Migration Plan, `count/rewrite.py` and `count/rewrite.json`; method and limits in `research.md`, section "Method".
- **[S2] The engine:** filmkit `dev` at `6d59ad6`, version 0.27.0: the files and lines cited above, the README's
  sections "A film's layout" and "The picture gate", `openspec/specs/`, and the active draft
  `openspec/changes/decide-before-heavy-work/design.md`, Decision 6.
- **[S3] The films:** `ddwg-film` (`v1.3.1`), `ddwg-essentials-film` (`v1.0.2`) and `ethos-film` (`v2.0.1`), each at its
  `dev` head, whose `picture/` and `content/` equal the tag; `picture/film/timing/cues.js`, `timing/pauses.js`,
  `playback.js` and the scene modules.
- **[S4] The shape of today's cues:** `count/shape.py` over the released timelines, and its scan of the twelve scripts'
  thoughts for the characters a mark would use; its output in `count/shape.json`.
- **[S5] Precedents, not read for this design:** SSML 1.1's `mark` element, EPUB 3 Media Overlays and the W3C Web
  Annotation model's text-quote selector, cited from the drafter's knowledge; a reader should check them before
  relying on them.
- **[S6] The films session's answers and rulings,** as the decision's owner under the owner's delegation (D-28 in
  `owner-words.md`), relayed on 23 November 2026 to the drafting agent: the seven answers (ids, edition-only anchors,
  shared ids, the check before narration, the two follow-on Changes, the relation to `decide-before-heavy-work`) and
  the rulings on [S7]'s findings.
- **[S7] The first independent reading,** `reading-1.md`, 23 November 2026: the count re-derived by its
  own parse; the released receipts written by `hyperframes render` without `drawn_sha256`; `follows_script` at
  staging; the frame audit's exit; the hand work (91 helper calls, 169 table entries); the 232 phrases that are not
  substrings of their text; `decide-before-heavy-work`, Decision 12.
