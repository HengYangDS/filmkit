# Design

## Context

See proposal.md for why. The picture's motion audit (`picture/motion-audit.mjs`) renders every frame of an edition headlessly at 30 fps and records each mark a scene paints. That record holds the mark's kind, words, line width, ink level, screen box and box in its own drawing coordinates. It keys a mark by that drawing box, so it loses a mark the moment the composition draws it at new coordinates. A flow's dot, a glide and a row that re-centres are drawn that way, so the audit never follows them. Only its still runs are gated.

The ETHOS film's lane carries a prototype probe (`build/runtime/work/production/motion/probe.mjs`). It follows marks of one class (scene, kind, words, line width) by the nearest centre among marks of nearly the same size whose box moved whole, with the thresholds the brief names. On the three films it reports many events that are not what a viewer sees, and most of its events carry no origin.

The reviews score each film's declared dimensions and average them. The verifier and `review.round record` accept a review whose overall score and every dimension meet the floors and that holds no material finding.

## Goals / Non-Goals

**Goals**

- Follow every mark as a viewer sees it move, and refuse halts, starts, races and pops outside stage cuts, naming the line that drew each. Calibrate on the three films' committed compositions.
- Keep each film's exceptions visible and refuse stale ones, as `[narration.flow]` and `[picture.wrapping]` do.
- Accept a review level by level, and give every sentence a verdict, for a film that declares its levels; keep every other film's reviews as they are.
- Give the reviewers motion as measurement, from the gate's own report.

**Non-Goals**

- Gating the quiet between thoughts, a change in the picture between one thought's last word and the next one's first. The reviewers measure it, and the voice clock now holds it.
- Judging a mark's colour or ink changes as motion. The audit's colour snaps and faint rests keep their own measures.

## Decisions

### Marks are followed by their own motion, in one assignment per group of like marks

A mark is any paint a scene draws at ink level 25 or more, captions apart, with its scene, kind, words, line width to 0.5 px and screen box. In each frame:

1. **Still marks.** A mark whose box and line width are unchanged continues the mark that stood there.
2. **Like marks.** The other marks of each group of like marks (scene, kind and words) are matched by the assignment of least total miss. A mark's miss is the distance, summed over the four edges, between its box and where the previous mark's own edge velocities put it. Leaving a mark unfollowed costs four times the turn limit.
3. **A pair qualifies** when it is one of these:
   - **a whole move:** the same line width and nearly the same size (2 px or 5%), each axis's two edges shifting together within 2 px or a fifth of the axis's shift; its motion is its centre's shift;
   - **a growth:** a mark that grows, shrinks or redraws in place or while it moves. Once the shift both edges of each axis share is taken out, the boxes overlap by half the smaller box. Its motion is that shared shift, which, like every motion, stays within 4,500 px/s; its edges may grow faster, as a stroke drawn on does.
4. **Limits.** A followed mark changes its velocity within one frame by no more than 1,200 px/s or its own speed, whichever is larger. A mark under 6 px across grows into, or shrinks from, only a mark that is under 12 px across its narrower side.
5. **Words that change.** A text whose words change continues a text of its scene by a whole move, as a counter does.
6. **A fixed end.** A pair that holds one end of one of its drawn subpaths exactly (to 0.01 px) where it stood grows or turns from that end and does not travel, however its box changes: a bracket's moving end sliding through its fixed end flips the box, which is no motion of the mark.

The probe's nearest-centre rule produced four kinds of event that the films do not show, found by checking each kind at its frame on the three films:

- **Pop pairs.** A mark that grows while it moves, such as a link drawing on from a gliding mark or a vertical rule lengthening as it slides, was reported as a pop-in and a pop-out in every frame. The growth rule follows it.
- **Flow-dot wraps.** A dot shrinking to nothing at the end of its link was paired with the next dot growing from nothing at the start, as a race. Both are under 6 px across, and the audit judges no move of a mark that small.
- **Jumps between like marks.** A dot that vanished was paired with a like dot appearing 73 px away, as a start and a race. A mark at rest that is predicted to stay cannot reach a mark that far within the turn limit.
- **Swapped identities.** A list of rules halting in step was rotated, the top rule paired with the middle one, so a halt was reported where none happened. Matching by the least total miss keeps each mark with itself.

The repaired essentials composition, whose motion follows these rules by design, showed three more patterns that the gate reported and a viewer does not see, each checked at its frame:

- **Pieces that join or leave a like mark.** A slab that eases down and joins its stack, a bracket's second end entering by size and a line drawn on from a point change a mark's box or make a new mark of its pieces, which read as pops. A pop is judged by the pieces it brings or takes, its drawn subpaths that no like mark of the other frame holds in place within 2 px, together 12 px or more across.
- **A turn through a fixed end.** A bracket shrinking through its fixed end, as the late start's bracket does when it moves earlier, flips its box from one side of the end to the other, which read as a halt and a start. The fixed end rule above keeps it still.
- **Declared stage cuts.** Marks that give way to others on a word, where the composition declares a stage cut, were pops when the change kept most of the scene's ink. The gate reads the composition's own `stageCuts` map (below).

The alternatives were:

- **Greedy matching by the predicted position.** A halting list, or two series drawn on one above the other, then traded identities, which the optimal assignment does not do.
- **The brief's continuation alone.** A mark that grows in place may continue any like mark whose box it overlaps by half the smaller box. The shared shift is needed so that a mark growing while it moves is followed rather than reported as pops.

### A stage cut counts marks as well as ink, arriving as well as leaving

A frame is a stage cut for a scene when at least 35% of the scene's firm marks, at ink level 60 or more, vanish or appear in it, counted or weighed by their ink (box area times ink level), or when the composition declares a cut of the scene in it. The 35% is the brief's. The three films keep a global `stageCuts` map of each scene to the times of the cuts it declares on its words as it renders, which the headless composition reads; a composition without one is judged by the shares alone. Counting only the ink that vanished, as the probe does, misses most of the films' designed cuts on a word:

- **Handoffs.** A stage hands over to the next while a large frame stays. In ETHOS 06, 36 of 41 firm marks leave at once, which is 19% of the ink. In DDWG 01, 13 of 32 leave, which is 14%.
- **Arrivals.** A stage arrives whole, as at ETHOS 02 with 51% of the ink after the cut.

Weighing by box area also lets one large outline outweigh many names. Across the six editions the frames where many marks change at once lie between 0.29 and 0.97 of their scene's firm marks, while a card or a name that pops alone changes under 0.2 of them. No mark is followed across a cut, and a scene's first and last frames are cuts.

### The thresholds are the brief's, and the following limits are measured

Each limit below was measured by running the gate's follower without it on the six editions of the three films' committed compositions.

- **Kept from the brief.** The halt and start bounds (60 px/s and 1.5 px/s), the race (900 px/s), the pop's ink level (60) and size (12 px across) and the cut (35%) are the brief's.
- **The eased end.** A halt whose last step is under half the step before it, or a start whose next step is more than twice its own, is the end of an eased move sampled at 30 fps: the mark slows or gathers speed over frames, and the frame step alone crosses the bounds. Without this rule the gate also refuses 2–11 halts and 1–133 starts per edition (46 starts on ETHOS Chinese, 65 and 133 on DDWG), all of them eased.
- **The turn limit.** A followed mark changes its velocity within one frame by at most 1,200 px/s, or its own speed when that is larger. The followed marks change their velocity by at most 69–306 px/s at the 99th percentile and 297–745 px/s at the 99.9th. The few larger changes, up to 3,202 px/s, belong to a ticker that sweeps its values and to marks at speed, which the larger own speed admits. Without the limit a mark jumps to a like mark that appears elsewhere: 2–13 more halts and 2–13 more starts per edition. The limit also leaves 9–12 pops per edition, where a mark is redrawn elsewhere at once, as a highlight bar that jumps to its next row, which a viewer sees as a pop.
- **The 6 px size.** A move is judged only on marks 6 px or more across. The dots entering and leaving by size are under 3 px across when they wrap, and the films' flow dots that a viewer follows are 8–10 px. Without the size the gate reports the wrapping: 18–19 more races on the essentials film, 4 and 3 more halts on ETHOS, and 27 more halts and 25–26 more starts on DDWG.
- **The stage cut.** Without the cut, every designed stage change is a pop: 1,240–4,839 pops per edition in place of 18–228.
- **The reach.** 4,500 px/s, the probe's, bounds a mark's shift; its edges may grow faster, as a stroke drawn on does.
- **What the films show.** The 58 halts and 59 starts on the committed compositions fall from or rise to 64–1,088 px/s, 20 of each under 300 px/s, the pace of a flow. The ETHOS round-9 composition, which the owner watched, holds 27 halts and 29 starts of flow dots in English, every halt within 0.25 s of a word's end. After the voice clock eases to rest, 6 and 5 remain. The races peak at 903–3,951 px/s, 582 of the 606 under 2,000 px/s. The essentials film's repaired composition, whose flows move at 160 px/s and whose glides ease in voice time, holds no finding.
- **Calibration evidence.** The per-film counts are in tasks.md 1.4's evidence and in the Changelog.

### A finding names the scene line that drew it

`openComposition` gives each paint's origin as the innermost line of scene code on its call stack. Scene code is a scene's body (`scenes["NN"] = function`) or a module that the bundle's path comments (`// picture/film/scenes/p02/hard.js`) place in a folder below `scenes/`. Where no such line drew the paint, the origin is the innermost line of the composition. Each origin also names its module where the bundle carries path comments.

The alternatives were:

- **Rebuilding the film's bundle with a source map.** The probe's successor does this, but it needs the film's bundler and its configuration in the engine.
- **The scene body alone, as before.** In a bundled film this names only the dispatcher line that calls a scene module.

### Findings are grouped and exceptions match a line or a module

The report lists every frame's event. The gate groups them into one finding per edition, scene, kind of finding, origin and episode, consecutive frames of one followed mark, so a glide racing for six frames is one race with its peak.

An exception names its edition, scene, kind and `source`. A source is `film.js:<line>`, which is exact but moves with every edit, or the module, which is stable across edits of other modules. A finding that an exception matches is recorded with the reason. An exception that matches no finding of its edition is refused, as `[narration.flow]` refuses one.

### Speeds are recorded per scene, as glide and flow

For each scene the audit records the largest speed of a glide, a mark more than 16 px across or a text, and of a flow, a smaller mark, with its time. The films draw their flow dots with radius 4 to 5 px, so the size separates them from the structures that glide.

### Review levels and sentences live with the review record

- **Declaration.** `film.py` declares `[review.levels]`: a table per level, `信`, `达` and `雅`, with `asks` and `dimensions`, checked against `[review.dimensions]` when the declaration loads.
- **Acceptance.** `filmkit.review.record` owns it, as it owns the floors: `level_problems` and `sentence_problems`, which `review.round record` and `filmkit.delivery.verification` both call.
- **The record.** It carries `levels` and `sentences` beside the scores. Its schema version stays 2, so a record written before 0.12.0 for a film without levels still verifies.
- **Sentences.** `filmkit.review.sentences` derives each edition's sentences from its timeline: the thoughts by their aligned words, each thought split at its sentence marks with its closing marks and quotations kept whole, and each sentence's start and end from its first and last aligned units.
- **Prompts.** `review.round prompts` writes `sentences-<code>.json` into the round directory and names it in `{sentences}`. The record and the verifier take the ids from the current timeline.

### The measurement reads the gate's motion report

`review.measurement` reads the edition's gate record and its motion report. It refuses either when it is not bound to the current composition and timeline, or when the report's SHA-256 differs from the record's. It does not run the audit again: the gate owns the measure, and the reviewers read exactly what the gate judged.

## Risks / Trade-offs

- **[The gate refuses a film's deliberate pulses and flashes]** → They are pops by the owner's standard unless declared. A film declares each with its reason, by module so that edits elsewhere do not stale it.
- **[A rare configuration still swaps identities]** → Like marks spaced exactly one frame's travel apart can be matched either way. The calibration found none after the assignment, and a film may declare such a finding.
- **[The audit takes longer]** → On the three films it adds a few seconds per edition: about 7 s on a 25-minute DDWG edition, from 56 s to 64 s.
- **[Attribution follows a folder convention]** → A bundle without a `scenes/` folder falls back to the scene bodies and then to the innermost line, so every finding still names a line.
- **[Films without levels keep averaged reviews]** → Levels are the film's declaration. The three films adopt them in their own lanes, with their review prompts.
