# Design

## Context

`check-picture` runs the frame audit, the sync audit and the motion audit and refuses what `gates.gated_findings` lists. The frame audit reports layout and balance; the sync audit (`filmkit.picture.sync_audit`) judges each label against its spoken words and lists, under `continuity`, unnamed speech, held-over thoughts and seats. The gate reads the sync audit's `findings` and none of its `continuity`, so the seats and the unnamed speech of ETHOS v2 reached the reviewers with a passing record.

The seat check (`src/filmkit/picture/seat-marks.mjs`) joins the graphics of a voiced frame whose paint touches into one mark, within 12 px so that a link belongs to the mark it reaches. A mark is named when it holds another mark or a text, when it is no empty frame and a legible name stands within reach, or when it lies inside a named mark. Two rules of that model hid the two stand-ins the reviews found:

- In 09.1 a dashed box stands at the end of the opening card's link. The link joins it to the card and the Agent, so the three are one mark 1029 px wide. The box of that mark encloses the Agent's inner dot, so the mark holds another mark and counts as named in every frame, before any name is legible; the dashed box is never judged on its own. It is not excluded for being dim: it is painted at full opacity, and the audits do not read its dash at all. At 90 px tall it is also below the 120 by 100 px from which an empty outline counts as a frame, and far below the 60,000 px² from which a container counts as underfilled.
- In 03.6 two tool outlines stand from the cut, each holding a pictogram (Git's branch, a tool's features), about 4 s before their names. Each frame holds another mark, so it counts as named, and each pictogram lies inside a named mark, so it counts as named too. Nothing about their strokes keeps them from the trace.

Text is typeset for the captions, the subtitles and a transcript's body by `filmkit.captions.timing.typeset`, and only there: a transcript's title and headings come from the script as written, and so do the chapters and the MP4 tags.

## Goals / Non-Goals

**Goals:**

- Refuse before a render what the round-4 reviews refused, each by the measure the reviewers used or one calibrated against them.
- Keep the seat check's verdict on every mark it already judged, except for the two rules above.
- Give each deliverable one source for its quotation marks and each carrier of a film's words one check.

**Non-Goals:**

- Judging faint stand-ins: a mark at or below the firm opacity of 0.35 stays outside the seat check.
- Reading a composition's intent, such as whether a count's words may draw a group's outlines: the gate lists the mark and the film repairs or re-times it.
- Repairing any film.

## Decisions

### 1. The gate reads the sync audit's continuity

`gated_findings` adds a finding for each row of `continuity.seats` and `continuity.unnamed_speech`; `recorded_findings` takes the sync report and adds each row of `continuity.held_over`. A held picture stays recorded because a deliberate index can stay while the first new name arrives, which only the stage's intent tells. No new report key is needed.

### 2. A dashed outline joined to a mark is judged on its own

The canvas stand-in already keeps the dash of `setLineDash`; each paint now carries it as `dashed`, the frame audit keeps it on its graphics, and the seat check's shapes carry it. In `seatMarks`, every dashed closed outline of a mark that holds other paint, at least the size of a detail, yields a row of its own, named when a legible name stands within its reach or a mark or text stands inside it. A row whose box equals a mark's or a member's is dropped, because that mark is already judged and two rows on one box would confuse the frame-to-frame tracking.

Alternatives considered, on the ETHOS v2 lane's two editions: judging every hollow closed outline joined to other paint also lists the opening card at 01.1 and the marks of 01.4, 02.4 and 09.1, which the reviewers judged clean; a card waits a moment for words that arrive on their cue, and only the dash says that the outline stands in for something absent. Lowering the frame's size would judge the card too and would still leave the box joined to its mark. Naming the outline only by its content would pass a dashed outline whose label comes late and which is never filled; the dash shows a missing thing that the narration names, so a name at it is enough. The rule lists 09.1 in both editions (Chinese 5.13 s, English 5.87 s, until the seal's name) and nothing else.

### 3. A frame is named by what it holds only through a name

A frame, a filled panel or closed outline of at least 120 by 100 px, no longer counts as named for enclosing another mark. It is named when it holds a text, when it holds a mark and a legible name stands within its reach, or when it holds a mark that is named; a mark inside a named mark still belongs to it. Marks without a frame keep the old rule, because the box of a chain or an icon encloses its own details, and that says nothing of a name. On ETHOS v2 the rule lists the two tool frames of 03.6 in each edition, through their pictograms, until the links join them to the kernel's named mark (3.5 and 3.7 s), and the bar of the English 03.7 with the stretch of unnamed speech already listed there; a stricter variant that kept a frame holding a mark from being named by a name beside it also listed the card of the Chinese 03.5, which a heading in reach names.

The sample film's cards stood whole from each scene's start, empty until their names, as seats under the old rule too (nine in Chinese, seven in English on its staged timelines); each card now carries a small tag of its kind of file or its step until the narration names it.

### 4. Caption echoes live in the sync audit

The sync audit holds both inputs: the label trace and, in the timeline, the cues. It compares each cue with the labels legible at any sample within the cue, as words: a run of letters and digits with its apostrophes in Latin text, and each CJK character alone, since a Chinese cue has no spaces. A label covers the cue's words it repeats as one run. A cue of three or more words is a whole echo when one label covers all of them, and a partial echo when labels cover at least 80%; the report lists each under `continuity`, the gate refuses the first and records the second. The reviewers counted the same shares for the English edition.

The frame audit's `caption_echoes`, names that hold three quarters of the caption standing with them, was never gated and is superseded; it is retired so the rule keeps one owner.

On the ETHOS v2 lane the recorded measure reproduces the English review's count exactly, 6 cues in 01–06 and 17 in 07–09, and the three cues it named are each drawn in two labels at 100%, so they are recorded rather than refused. Refusing every cue drawn whole by several labels would also refuse a fourth English cue and ten Chinese ones whose list items are named on their words, which the reviews accepted; a cue that only a longer label contains, such as a rule's heading or the opening quotation, is not repeated by it.

### 5. Mixed case is a text-layout measure

Sets and rows are read in the frame audit's text layout, whose paints know a name's baseline and size. The frame audit copies each registered text's `whole` and `set` onto its paint, which a settled name's lines keep. `mixedCase` takes one entry per whole name, at the baseline of its first line, groups the names by set and by row (one scene and size, baselines within half the size, anywhere across the frame), and reports a group whose judged names begin in both cases. A name is judged when its first character is a letter that has a case and its first word holds no later capital, which leaves acronyms and brand names out. Runs of 1 s or more count, as for every text-layout measure, and `check-picture` refuses them.

A row here crosses containers and distance, unlike the ragged-row measure: three equal cards and the two sides of a mark are one row to the eye, and a case slip across them is what the reviewers saw. A quotation keeps its source's case and is not judged: the claim card's “Done. All tests pass.” stood on one baseline with an attested row in 09.2. On the English edition the measure lists 11 runs, all in 07–09, the stretch the review found mixed, including the four rows it named; the Chinese edition has none.

### 6. The display copy reaches every title and tag

`_transcript` typesets the film's title and every heading, and `_chapters` typesets each chapter's title where it is derived, so `chapters.json`, the FFmetadata, the MP4 chapter track and the player's chapter list agree with the transcript and the picture; a transcript alone would disagree with them on every apostrophe. The player's transcript derives from the Markdown one. `release_tags` and `quicktime_keys` typeset the title, comment, description and synopsis, the four prose tags; the brief named three, and the description is the fourth of the same kind. Chinese scripts set their quotes already, so their output does not change.

### 7. The chapter track carries the edition's language

FFmpeg's MP4 muxer writes its chapter text track with language code 0, which reads as English, offers no option for it, and creates a new one on every remux; ExifTool cannot write a media language, and neither can a stream copy reach it. GPAC's `MP4Box -lang` could, at the price of a new host tool for every film. So `package_rendition` writes the two language bytes of the chapter track's media header in place once the film is finished: the file's size and offsets do not change. `check_delivered_film` then requires the edition's language on every track, the attached cover, which is no track, aside.

### 8. The concept check reads the player and the release prose

`edition_places` adds the edition's release synopsis, comment and description, and a place for the player's prose: the text of `Edition.player` outside its `script` and `style` elements, read with the standard library's HTML parser, entities decoded. A film without a player page has no such place. `counterexamples` needs no change.

### 9. The supply

ETHOS 0.2.0-alpha.29 and uv 0.13.7 are declared and locked by the family's recipe, and `.github/workflows/ci.yml` is projected for `jdx/mise-action` 5.2.6. alpha.29's Ruff policy adds `DOC102`, a docstring that documents a parameter its signature lacks.

## Risks / Trade-offs

- [A film that passed 0.8.1 is refused by 0.9.0] → That is the intent. ETHOS v2 adopts it with its repair; a film keeps its pin until its next edition.
- [A dash is the signal for a stand-in, so a stand-in drawn hollow but solid passes] → It stays a reviewer's judgement: the solid form cannot be told from a card waiting for its cue, and the calibration shows the cost of trying.
- [The in-place language write depends on the MP4 box layout] → It walks only `moov/trak/mdia`, refuses a film without exactly one text track, and `check_delivered_film` reads the result back through FFprobe.
- [A frame's wait ends when a link joins it to a named mark] → The tool outlines of 03.6 are listed through their pictograms, for the seconds until the links draw, not until their own names; the wait is still far over the limit.
- [A row across the frame can join unrelated names] → A stage shows one structure, and the calibration on ETHOS v2 lists only rows the reviewers read as sets.

## Migration Plan

A film adopts 0.9.0 with a new edition. Its picture must pass the new gates before `render-picture` starts, and its package changes where the Changelog says. Rollback is the previous pin; nothing a film tracks changes.

## Open Questions

None.
