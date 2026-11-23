## Why

Each film's picture places a change on the narration by quoting the narration: `cue(s, zh, english)`,
`cues(s, [...])` and `cueFrom(s, zh, english, from)` in the film's own `picture/film/timing/cues.js` search the
segment's aligned words for the quoted phrase and throw `Missing spoken cue …` when it is not there, which stops the
picture. The three released films hold 1,240 such calls with 2,139 phrase pairs: 3,980 literal phrases of narration
text in their picture code. A copy cannot follow its source: run with each film's own cue functions, the December
scripts of the trial clones (not compared here with the approval sheets) strand 172 Chinese and 83 English cues of
the full DDWG film, 44 and 23 of the essentials film and 82 and 28 of the ETHOS film, and 64 more still resolve but in
a thought of another number (`research.md`; re-derived by an independent reader, `reading-1.md`). Under the owner's
rule that each fact has one source and that a check refusing a disagreement afterwards is not a source (C-2), the
words a picture change is keyed to must stand once, in the narration, and the picture must name them rather than
repeat them. That is also what G-1 needs: an edition whose narration changes is produced again by engine commands,
without the picture code being rewritten for words it merely quoted.

## What Changes

- **A script marks anchors in its own words.** A segment may hold `anchored_groups`, its thoughts with named spans
  marked in them (`{order}有先后{/order}`, kebab-case ids, two ids allowed on the same words); its `utterance_groups`,
  text, spoken text and the narration mirror are filled from them, so every reader of the narration reads the plain
  words as before. The rules have one home, `narration/anchors.py`, which every command that reads marks calls.
- **The timeline gives each anchor its words' times.** `produce assemble` writes `anchors` (start, end, units,
  thought) on every segment of an edition that marks any, from the segment's own aligned words; the picture's data
  carries them, and a composition reads `s.anchors[id]` instead of searching for a quoted phrase.
- **Anchors are presentation.** `produce refresh-captions` adopts a change of anchors alone, writing the script's
  `anchored_groups` and their anchors into the timeline from the existing words, so staging accepts it and the
  soundtrack is kept.
- **Script edits carry anchors.** `filmkit.narration.script_edits` keeps an anchor on its words, keeps it over its
  words reworded, and refuses, naming it, an edit that reaches beyond its words unless the edit restates it. A new
  `rewrite` edit replaces a segment's thoughts whole, as approved texts arrive, and moves each anchor whose words the
  new thoughts say exactly once, or as often as before; `anchor` and `unanchor` edits mark a span of units and unmark
  an id. The writer decides where a picture change goes when the words it was keyed to are rewritten, at the moment
  of writing.
- **What the picture reads is checked twice.** Before any speech model loads, narration draws the composition over a
  timeline the engine derives from each edition's script and refuses every id that the edition's picture reads and
  its script does not mark, by name, segment and edition; `check-picture` refuses the same on the timeline, so no
  render follows.
- **A report** (`python -m filmkit.narration.anchors`) lists each edition's anchors, as JSON too, the ids one edition
  alone marks, and writes the derived timeline for the films' own tests.
- **The sample film** keys its cues to anchors; its labels stay as they are.

## Capabilities

### New Capabilities

- `narration-anchors`: named spans of a script's own words, validated with the script, resolved to times in the
  timeline, carried by script edits, adopted by the caption refresh, checked against what each edition's picture
  reads before narration and before rendering, and reported for both editions.

### Modified Capabilities

None. The picture's data remains the timeline (`native-picture`, "A stage holds the picture's data beside its
document"); the anchors reach the stage because they are in it.

## Impact

- **Engine:** a new module `src/filmkit/narration/anchors.py` (the rules, the resolver, the derived timeline and the
  report); `narration/script_edits.py`, `narration/narrate.py` and the narration's prechecks,
  `soundtrack/assembly.py`, `captions/refresh.py`, `picture/headless-composition.mjs`, `picture/gates.py` and the
  commands that call the rules; their tests; the sample film; the README and the Changelog.
- **For a film that marks no anchor:** its scripts, timelines, pictures and films keep their bytes. Narration is the
  one step that changes, and it changes for every film that has a composition (breaking): it draws both editions
  first, which needs the film's npm packages at the engine's canvas version, and its printed gate line gains
  `picture_reads`.
- **Narration starts later and refuses more:** it draws both editions once before any model loads (3 to 10 s an
  edition, measured with this research's harness), refuses a script that lacks an anchor its picture reads, and
  refuses when a tool or package it needs is missing; a scene that throws for another reason, and a composition that
  does not load, edition-wide, are named as not judged and do not stop narration.
- **For a film that adopts anchors:** its scripts gain `anchored_groups` and its timelines `anchors`, so the digests
  that records bind for them change; its narration, soundtrack and captions need not change, and it proves its frames
  unchanged by two renders on one engine, before and after its migration, not against its released renders.
- **Relation to `decide-before-heavy-work`:** this Change replaces its Decision 6's report of quoted phrases for cues
  only; the report stands for labels, and that draft is not edited here. Its Decision 12, which carries readings by
  character offset, is a second carrier of a place in the text, to be reconciled in a follow-on Change.
- **Out of scope:** the films' own migration (their `cue` functions, the 1,240 calls and the December texts' anchors,
  each in the film's lane); labels that take their text from anchors and a caption break mark in place of English
  `caption_phrases`, each a follow-on Change.
