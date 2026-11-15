## Context

What the engine holds today, read in 0.22.3 on 15 November 2026:

- `check-picture` and `check-sound` write a gate record that binds the composition, timeline, stylesheet, fonts and engine by SHA-256, and `render-picture` reads the picture's record before it starts the renderer.
- Two classes of finding already have the form this Change generalizes: a wrapped label that breaks a rule and a motion finding are gated unless one of the film's declared exceptions names them with a reason, and an exception that matches nothing is gated as stale.
- `preflight` names every stale input of a render at once: both stages, the cover, an earlier package record, the draft scan, the concept check and the picture gate.
- `narration.script_edits` rebuilds a changed segment and releases the retakes bound to its old text; `narration.audition` refuses a thought whose text changed after the last narration.

What happened on that day, from the three films' own records (each film's Change design and its `build/evidence/retrospectives/2026-11-15.md`, local evidence written that day):

| When           | Film            | What was spent                                                 | What a light check would have said                                                                                                   |
| -------------- | --------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 09:33          | ETHOS film      | one Chinese picture, 56 minutes                                | the geometry record listed four row pairs under 1.5 em, ungated without the flag                                                     |
| 10:03 to 11:20 | ETHOS film      | one English and two Chinese pictures, and a fourth interrupted | the motion audit recorded 35 and 37 stretches over 450 px/s with no limit declared, and a probe at 1.7 em listed five more row pairs |
| morning        | essentials film | one Chinese picture, about 70 minutes                          | the level tolerance changed after the render, and the timeline embeds it                                                             |
| 11:00 to 13:00 | DDWG film       | two narrations of one thought, three of another                | the first recheck found four points a first hearing misreads                                                                         |
| 11:25          | DDWG film       | three bound retakes                                            | on the soundtrack they read 0.40 to 0.68 dB under the takes they replaced                                                            |
| 13:11          | DDWG film       | one audition ticket                                            | its targets held a thought edited after the last narration                                                                           |
| 14:00          | ETHOS film      | a 44-minute queue wait, refused as the ticket started          | the stage bound an assembly record that a later sound stage rewrote                                                                  |
| 15:57 to 16:43 | DDWG film       | five rounds of staged audits of both editions                  | picture cues named words the text no longer said; a longer name unseated a mark; two moves stood one frame over the pace             |

Review round 20 of the ETHOS film, the same evening, added two things the motion audit does not see. In 03.2 a 55 px stretch of a line left within one frame at each of three stations: the audit counts a drawn piece that a mark gains or loses whole, and a line split in two loses none. A reviewer read it as material by the letter of a pattern the owner rejected, and the build was not released. A headless scan that matches each draw call's solid stroke pieces by length from frame to frame at 60 fps finds the three places on that build and none on the repaired one (the film's local evidence of that day). And each chapter title travels to the running head at about 1,200 to 1,300 px/s in two films, while the declared pace limit of 450 px/s covers the marks of scenes only; the films' notes said every glide keeps the limit.

The same day the films carried, undeclared in any tracked file, fifteen English thoughts under the clarity floor in one film, one and two in the others, and one to two captions above the reading rate in each; a count of each lived in a script outside the repositories.

## Goals / Non-Goals

**Goals:**

- A finding that a reviewer would hold against a film is refused or declared before the first heavy step, by the engine, from tracked declarations.
- One owner answers "ready to render", and its answer can be checked again later without repeating its work.
- A film that declares nothing new and holds no such finding builds the same bytes.

**Non-Goals:**

- New thresholds. Each value stays where it is; the study says where it came from.
- Deciding for a film what to accept. The engine asks for a reason and an identity; the judgment is the film's and its reviewers'.
- Scheduling. Whether a ticket waits or runs is the host's.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, and where it applies.

1. **Recorded findings take the form the wrapping and motion exceptions already have.**
   - **Rests on:** the films' records of 15 November 2026, which held recorded findings as counts in task lists and scripts; one English thought of the ETHOS film that stood 0.66 dB under its clarity floor after thirty-two takes, which its reviewers accepted as declared.
   - **Considered:** (a) counts in a film's task list or script; (b) gating every recorded class outright; (c) declaration by identity with a reason, stale ones refused.
   - **Chosen because:** (c). A count passes when one finding leaves and another arrives, and it lives outside the gate; an outright gate would refuse films that reviewers accepted with those findings declared. A declaration by identity is what a reviewer reads, and a stale one cannot linger.
   - **Applies to:** captions above the reading rate (by the cue's text), thoughts under the clarity floor (by thought), row gaps (by scene and the two names) and whatever class a later gate records. Not to the classes a spec defines as informational: thoughts that hold the previous picture within the limit, and cues mostly but not wholly drawn as labels.
2. **The row gap's floor is a declaration, not a flag.**
   - **Rests on:** all three films pass `--gate-row-gaps` today; one review asks 48 px at 1080p, about 1.63 em of the films' label face; the films probed 1.7 em with a copied check; the ETHOS film's geometry record held four pairs under 1.5 em while its task list did not pass the flag.
   - **Considered:** keeping `--gate-row-gaps` in each film's task list; a declared floor with a default.
   - **Chosen because:** a flag is forgotten once per film; a floor in `content/film.toml` is read by the same check everywhere.
   - **Applies to:** every film, default 1.5 em. Breaking only for a film that holds pairs under 1.5 em undeclared.
3. **`preflight` grows; no second readiness tool.**
   - **Rests on:** this repository's rule of one owner per question of behavior; the films' readiness script, which repeated part of `preflight`, missed a binding it knew (the stage binds the assembly record) and, on 15 November, refused a packaged edition by asking the render's question after the packaging.
   - **Considered:** (a) a new `ready` command beside `preflight`; (b) each film keeping a script; (c) extending `preflight`.
   - **Chosen because:** (c). The questions already have their owner in `preflight`; a second tool repeats them and drifts from them.
   - **Applies to:** the readiness of every heavy step, each question asked for the step it admits: before a render, a film package record that binds the current picture is one the render replaces; after the packaging, the same record is the next step's input. The draft scan becomes a declaration because the films replaced drafts by the every-frame audits of `check-picture`; a film that declares drafts keeps today's behavior.
4. **The receipt binds inputs by digest and is checked without repeating the work.**
   - **Rests on:** the host's admission queue, which admits a ticket when the slot frees and has no room there for minutes of audits; the films' receipts of 15 November, checked by their digests before each ticket.
   - **Considered:** re-running `preflight` before each ticket; a receipt with the SHA-256 of each judged input and a cheap check that they still hold.
   - **Chosen because:** the receipt is what a queue can ask for at admission and what a later reader can verify.
   - **Applies to:** the engine, which writes and checks the receipt; admitting a ticket on it is the host's. Both editions are judged for a render of either, since they share the composition.
5. **A text review is a record, and requiring it is the film's declaration.**
   - **Rests on:** the DDWG film's edition 1.3.1, whose changed thoughts were narrated before an independent recheck passed the text, so that two of them were narrated two and three times.
   - **Considered:** leaving the order to the film's process; a record that `narrate` can require.
   - **Chosen because:** the engine cannot judge a recheck's independence, but it can refuse narration of scripts that no recorded verdict covers.
   - **Applies to:** films that declare it. Opt-in because the sample film and a film in its first draft narrate before any review exists.
6. **The script editor reports the picture's words it leaves behind; the film's own tests remain the proof.**
   - **Rests on:** the DDWG film's staged audits of 15 November, which refused both editions at once ("Missing spoken cue") after narration and a runtime fit, because scene modules still named words the narration no longer said.
   - **Considered:** (a) only the film's picture tests, which paint every scene from the script and fail on a missing cue; (b) a report from the editor listing quoted phrases of the changed segments' scene modules that the old text said and the new one does not.
   - **Chosen because:** both. The tests catch a cue; they do not catch a label that still shows the old wording.
   - **Applies to:** every script edit, as a list for the author and not a gate, because a label may deliberately keep a condensed wording.
7. **A retake is compared on the soundtrack with the previous edition's take.**
   - **Rests on:** two films in which the order of two takes changed between the take and the assembled soundtrack (an English retake read 0.18 dB above the bound take and 0.11 dB below it once assembled); three DDWG English retakes that read 0.4 to 0.7 dB under the takes release 1.3.0 delivered.
   - **Considered:** the picking measure on the take alone; the assembled soundtrack against the previous edition's, judged by the engine's own clarity measure.
   - **Chosen because:** differences under about 0.3 dB between takes lie within the measure, and only the soundtrack is what the viewer hears.
   - **Applies to:** a film that names a previous edition; the margin is the film's to declare, default 0.3 dB. A first edition has none.
8. **Caption breaks choose among allowed breaks by reading rate.**
   - **Rests on:** two films that wrote authored breaks by hand for four cues to bring them under 25 characters per second; one authored break that made a cue equal to a picture label.
   - **Considered:** authored breaks per cue in the script; the breaker weighing the rate itself.
   - **Chosen because:** both, the breaker first; authored breaks stay for the cases a rule cannot see, such as a cue that would equal a label.
   - **Applies to:** every edition's captions.
9. **A line split or cut short within one frame is a pop, and marks outside scenes are named.**
   - **Rests on:** the ETHOS film's review round 20 (zh-R20-02), where a reviewer found within one frame a 55 px gap in 03.2's path, three times, on the rendered master after two renders; the motion audit had passed it because no drawn piece left whole. A headless scan in the films' kit that matches each draw call's solid stroke pieces by length frame to frame found those three places on that build and none on the repair, and over both editions of the ETHOS and DDWG films finds no other outside a stage cut the scene declares.
   - **Considered:** leaving both to reviewers' scans of the rendered masters; a rule on each draw call's summed solid stroke length (it read a stroke drawn off gradually as a loss and listed 24 to 54 places per edition); a rule on the pieces themselves: a piece replaced by shorter ones losing 30 px or more in one frame, with no loss in the frames on either side, outside a declared stage cut.
   - **Chosen because:** the piece rule finds what the viewer sees, a line that opens or shortens at once, and passes what the viewer reads as drawing; it costs one headless pass per edition.
   - **Applies to:** solid strokes of scenes, as an audit finding of `check-picture`. Whether a chapter title should keep the pace limit is the film's decision; the engine's part is to say in the gate record that it is not judged.
10. **The thresholds' sources are written once, here.**
    - **Rests on:** the pace line, the row floor, the level steps between thoughts and the reading rate, each used by three films and each taken from a review record of one of them.
    - **Considered:** each film's design stating them; one study in this Change.
    - **Chosen because:** one place for a source keeps three films from citing three readings of it.
    - **Applies to:** the study, which names each value, the record it came from and its date, and what it does not cover. Its form follows what ETHOS provides for research documents when that is released; until then the facts stand in this design.
11. **A flow on a way that moves is judged at every phase of its clock.**
    - **Rests on:** the ETHOS film on 16 November 2026. Its first build of edition 2.0.1 passed the picture gate with a declared pace limit of 450 px/s. The owner then raised a pause floor of the Chinese voice, which moved every later word, and the staged audit of the same scenes refused one point of 05.2's flow at 456 px/s. A scan of that draw call at 60 fps over 22 phases of the flow's 2.2 s clock finds 464 px/s in both editions at the worst phase and 417 px/s at the phases the earlier timelines gave (the film's local evidence of that day): a point that rounds the bend of a link while the link's upward run shrinks under a rising stage. A flow's points stand where voice time puts them, and the audit judges the one phase the timeline gives.
    - **Considered:** (a) leaving it, since the next staged audit after a change of timing finds it within minutes, as it did; (b) a margin under the limit, reported as a warning; (c) the audit judging such a flow at every phase of its clock.
    - **Chosen because:** (c). With (a) a film that passes can be refused by a change that touches no picture, and the repair then comes after the sound is settled; (b) would not have caught this stretch, which stood 33 px/s under the limit at the phase the timeline gave. A flow on a fixed way moves at one pace at every phase, so only a flow whose way changes while it runs needs the sweep.
    - **Applies to:** flows drawn on a way that a glide carries or reshapes, in the motion audit of `check-picture`. What the sweep costs is not measured yet; it is measured before the Change's specs are written.
12. **A reading recorded for a place in the text moves with the text.**
    - **Rests on:** the DDWG film on 16 November 2026. `content/review/readings.json` records the part of speech of each English heteronym by segment and character offset. A text edit made 14.2 longer by 43 characters and left four keys of segment 14 behind. `filmkit.review.listening_plan` refuses such a key, rightly, but it first runs at review preparation: the refusal came after four renders, two comparisons, packaging and verification, and the repair was a commit of four keys. The readings check that runs with a text edit does not derive the plan. The same class, picture cues that named words an edit had removed, was among the causes of five refused staged audits the day before (decision 6).
    - **Considered:** (a) deriving the plan with every text edit and in the readiness check, as the films' kit does since that morning (four seconds); (b) the script editor carrying each key to the same occurrence of its term in the segment it rewrites, and naming the keys whose occurrence the edit removed or added; (c) keying a reading by thought and occurrence instead of by offset.
    - **Chosen because:** (b) with (a) in `preflight`. The editor holds the old and the new text of every segment it rewrites, so it can move what a person would otherwise move by hand, and `preflight` catches an edit made another way. (c) changes every film's file and still breaks when an edit adds an occurrence before the recorded one.
    - **Applies to:** the English heteronym readings, and any later record that names a place in the text by position.

Left out, with the reason: typesetting the timeline's narration fields (they are never shown, and changing them would release every take whose thought holds an apostrophe); a syllable rate by sound between thoughts (one review asked for it in one film; no second case yet).

## Risks / Trade-offs

- A film can declare its way past every finding. → Each declaration carries a reason, is listed in the gate record, and is read by the reviewers with the round's changes note; a stale one is refused.
- `preflight` becomes slower as it reads more records. → It reads records, not media; the audits stay in `check-picture` and `check-sound`.
- The breaking parts reach three films at once. → Each already declares these findings in its design; the adoption is moving them into `content/film.toml`, with the lists the films' own records hold.

## Open Questions

- Whether the receipt's schema should be the one ETHOS settles for host admission, so that one file serves both.
- Whether the review round's facts (changes note, dispositions) join this Change's receipt or keep their own records.
