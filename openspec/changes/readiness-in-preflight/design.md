## Context

The draft Change `decide-before-heavy-work` studies what the films' builds of 15 and 16 November 2026 showed the engine lacks, in twenty-one decisions with their evidence. This Change admits the slice of it that the films' readiness script stands for: the picture checks that script runs as scans outside any repository, and the answer "ready for the first render" with a receipt. Its proposal states why and what changes; its specs state the behavior. This design records how the slice is built, where it departs from the draft's wording and why, and what stays in the draft.

What the engine holds, read at `22308e5` (0.22.3 and the draft): `check-picture` runs three headless audits and writes a gate record bound by SHA-256; wrapped labels and motion findings are gated unless a declared exception names them, and a stale exception is gated; `preflight` names every stale input of a render at once and writes nothing; no command checks an earlier answer.

What the films' kit holds, read the same day: a readiness script that asks three of `preflight`'s questions one by one, since no film makes the draft scan that `preflight` requires, and adds the sound gate, the geometry record, counts of declared findings from environment files and five scans of the composition (ink drops, chapter titles, part-drawn strokes, runs off centre, rails); a receipt of digests; and a script that admits a ticket on the receipt.

## Goals / Non-Goals

**Goals:**

- A film can replace its readiness script by `check-picture`, `preflight` and `admitted`, with its accepted findings in `content/film.toml`.
- Each scan the kit holds becomes an audit finding of `check-picture` under the engine's one form of finding and declaration.
- A film that holds none of the new findings and declares nothing new keeps its gate verdicts; its films' bytes do not depend on this Change.

**Non-Goals:**

- New thresholds. Each line is a reviewer's or one the engine already holds; decision 7 names each source once.
- Enforcing admission. `render-picture` keeps reading the gate record alone; whether a ticket waits for `admitted` is the host's.
- The rest of the draft. The section "Left in the draft" lists it with the reason.

## Decisions

Each decision states what it rests on, what was considered, why the option taken was chosen, and where it applies. A decision of the draft is cited by its number there.

1. **The kit's scans become one fourth audit, the detail audit, at 60 frames per second.**
   - **Rests on:** the draft's decisions 9, 13 and 15. The motion audit samples at 30 frames per second and follows marks; a line that opens for one frame of a 60 fps film falls between its samples, and it judges a mark by the pieces that leave whole. The frame audit's module stands at 492 of the 500 non-blank lines a module may hold. Measured on 17 November 2026 at niceness 15, the audit takes 39 and 40 s for the DDWG film's two editions (90,001 frames each), 49 and 54 s for the ETHOS film's (54,001) and 22 to 42 s for the essentials film's (36,001).
   - **Considered:** (a) four tools, as the kit has; (b) the rules inside the motion audit; (c) one tool with four rule modules, each a pure accumulator tested on its own inputs, as the motion audit's rules are.
   - **Chosen because:** (c). The four rules share one pass over the frames and one report; (b) would double the motion audit's sampling for every film to serve one rule, and its follower has no notion of a quiet or a list.
   - **Applies to:** `check-picture`, whose record binds the report as `detail`. The tool also runs alone, with a range, as the other audits do.
2. **An ink drop is judged per draw call, by its pieces.** The draft's decision 9 holds the evidence and the rule that was rejected (the summed length of a call, which read 24 to 54 gradual losses per edition as drops).
   - **Rests on:** that decision, and the kit's scan, whose rule this is: on the six current editions the audit and the scan agree on every count (no drop; 7, 7, 5, 5, 1 and 1 losses on declared stage cuts).
   - **Considered:** following strokes as the motion audit's marks; matching pieces by position.
   - **Chosen because:** the call, the line of the composition that draws, is what a film can name in a declaration and repair; matching by length needs no notion of where a piece stands, so a line carried by a glide is no finding.
   - **Applies to:** solid strokes of scenes at opacity 0.5 or more.
3. **A text outside every scene keeps the pace policy of the marks inside them.** This departs from the draft's decision 9, which left such a text unjudged and asked only that the gate record say so.
   - **Rests on:** the DDWG film's review round 41. Finding EN41-11 tracked each of seven chapter titles from its card to the running head at a centre peak of 1,137 to 1,198 px/s, over the film's declared 450 px/s for about 0.9 s and over the race line of 900 px/s for 0.50 to 0.58 s, judged it by the pattern of a mark that races, and asked for `check-picture`'s audit to cover the title with no race and no pace; note Z41-4 asked the same of the Chinese edition. The film then stopped the titles' travel, and its kit holds them to the pace limit.
   - **Considered:** (a) naming them as unjudged; (b) a limit of their own; (c) the policy the motion gate has: at 900 px/s or more a race, refused; over 450 px/s a stretch, refused only over the film's `pace_limit`.
   - **Chosen because:** (c). A viewer does not tell a title from a mark, and one declared limit that holds for every moving thing is what the films' notes already claimed.
   - **Applies to:** every text no scene draws, captions apart, followed by its words: the same words more than 60 px away one frame later are another text, so a card that fades into its running head is no travel.
4. **Drawn strokes are read from what the composition publishes.** The draft's decision 13, unchanged: a `draws` list beside the layout's `texts`, read at the middle of every quiet between two thoughts of a segment; a tip at the pace at which a mark races is listed from the same list.
   - **Rests on:** that decision. The three films' current compositions publish `draws`, read on 17 November 2026; the sample film publishes none.
   - **Considered:** refusing a composition that publishes none.
   - **Chosen because:** a film that draws no stroke by its tip has nothing to publish, and the audit cannot tell it from one that does and stays silent, so the gate records in a line of its record that the strokes were not judged, and refuses nothing.
   - **Applies to:** `check-picture`.
5. **Rails are read headlessly by their list, not in the geometry check.** The draft's decision 15 placed them in `geometry-check`.
   - **Rests on:** what each check can see. The geometry check reads the staged page in the browser and knows text by its box; the composition registers each name's list (`set`) with the layout the headless audits read. The kit's scan is headless and reads the same layout; on the DDWG film's English edition both list ten rails and the same three under 48 px (13.8, 13.9 and 14.6 px), on its Chinese edition six and none.
   - **Considered:** teaching the geometry check the lists; reading rails in the detail audit at the rest of each thought.
   - **Chosen because:** the headless reading needs no stage and no browser, so it runs with the other audits before anything is staged, and a rail is then declared in the one place the other picture findings are.
   - **Applies to:** names of one scene and one list on exactly two alternating lines. Heights are the headless estimate, as for every headless measure.
6. **A run far off centre is a finding, however the picture moves.** New; written into the draft as its decision 22.
   - **Rests on:** the DDWG film's review rounds 41 and 42. Round 41 (note Z41-5) listed 26 runs of the lit box beyond 50 px for 1 s or more, each the first mark of a build standing on its side, the largest 466 px off for 1.58 s, and asked that none beyond 400 px last longer than 1.0 s. Round 42 (note Z42-5) found none of 1.0 s and four of 0.55 to 0.98 s, at up to 688 px, and asked that none last 0.5 s or more. The gate's two balance lines pass such a run: a build-up may stand more than 90 px off for under 1.5 s.
   - **Considered:** (a) the kit's scan, a model of the reviewers' box with an opacity line; (b) a third line on the box the frame audit already measures in every frame for those two lines.
   - **Chosen because:** (b) costs no pass and is the reviewers' own box. On the DDWG film's current Chinese composition it lists the four runs round 42 listed and no other, each end within 0.07 s of the reviewer's reading and the two offsets the reviewer states within 1 px (12.3 from 595.80 to 596.60 s, 12.4 from 608.50 to 609.27 s, 27.5 from 1,314.90 to 1,315.87 s at 624.5 px, 28.2 from 1,342.27 to 1,342.83 s at 687.8 px).
   - **Applies to:** the frame audit, as `off_centre_far`: one scene, one side, 0.5 s or more, more than 400 px.
7. **Each line is a declared constant with its source named once.** The draft's decision 10.
   - **Rests on:** the lines of this Change: 30 px lost and 3 px calm for an ink drop (the reviewer's gap was 55 px; a stroke drawn off at 450 px/s loses 7.5 px a frame); 450 and 900 px/s, the motion audit's pace line and racing pace, imported from it; 48 px for a rail (round 41, note Z41-3); 400 px and 0.5 s for a far run (round 42, note Z42-5).
   - **Considered:** values a film may set.
   - **Chosen because:** a film keeps a finding by declaring it with a reason, which a reviewer reads; a private line would hide it.
   - **Applies to:** the rule modules, which state each value beside its source, and the detail report, which carries the lines the gate words its findings by.
8. **The new findings take the form the wrapping and motion exceptions have.** The draft's decision 1, for the picture's findings and for the two classes `preflight` reads.
   - **Rests on:** that decision; the films' counts of declared findings in environment files, which pass when one finding leaves and another arrives.
   - **Considered:** counts; one exception table per kind.
   - **Chosen because:** identity with a reason is what a reviewer reads. One table, `[[picture.detail.exceptions]]`, holds the picture's kinds, each named by its kind and scene and, where the film wants one finding of several, a source: the drawing line or module, the text, the thought, the list or the side. A racing tip is named by its scene alone, since the cue that keys a stroke moves with every fit of the runtime. A fast cue is declared by its shown text and a thought by its name.
   - **Applies to:** `check-picture` and `preflight`. The row gap keeps its flag (the draft's decision 2).
9. **`preflight` grows, by the questions the kit asked and the engine did not.** The draft's decision 3.
   - **Rests on:** that decision. The delivery's verification refuses a geometry record that did not pass on the whole current staged film; the kit asked for the sound gate's record on the current timeline and engine; `preflight` asked for neither.
   - **Considered:** a second command; repeating the verification's condition in `preflight`.
   - **Chosen because:** `preflight` names what a later owner would refuse, so the geometry question is the verification's own, extracted where it stood, and asked early. The draft scan is asked only of a film that declares `drafts`, since the films replaced drafts by the every-frame audits and none could call `preflight` while it required one.
   - **Applies to:** the render's readiness. A film package record still refuses, as before: this is the question before a render. The steps after a render ask `admitted`, which does not repeat it.
10. **A single thought is judged in `preflight`, and only for a film that declares its line.** Part of the draft's decision 14.
    - **Rests on:** that decision's measurements (a floor set for a soundtrack and held thought by thought fails about one thought in seven) and the owner's line of 16 November 2026 for two films: the floor less 1.0 dB for a thought, the thoughts between the lines listed.
    - **Considered:** gating every thought under the floor unless declared, for every film.
    - **Chosen because:** a film that has not decided a line for single thoughts, as the sample film has not, would be refused for what its sound gate records by design. With a declared margin the film has decided, and the list between the lines is then exact by name.
    - **Applies to:** `preflight`, read from the sound gate's record. The sound gate and the review prompt are not changed here. The margin may be zero: every thought is then held to the floor itself, the refusal says so, and the declaration refuses a thought to keep beside it, since none can stand between the floor and itself. The first form required a margin above zero, so a film could not say what its owner decided on 17 November 2026 for the three films' next editions, one line of 18.0 dB for the soundtrack, each segment and each thought (the draft's decision 14).
11. **One receipt per edition, and admission asks both.** The draft's decision 4, with the films' later refinement.
    - **Rests on:** that decision ("both editions are judged for a render of either, since they share the composition") and the kit's receipts since 16 November, which admit an edition while its own inputs hold whatever the other edition's script or sound does, so that an English retake does not stop a Chinese render.
    - **Considered:** one receipt for the film; one per edition checked alone.
    - **Chosen because:** both hold with one rule: `admitted` asks the edition's receipt on every input it bound and the other edition's on the inputs both share (composition, stylesheet, fonts, declaration). A finding in the other edition's picture gate refuses its receipt and so this edition; a change of its script alone does not.
    - **Applies to:** `preflight`, which writes the receipt whether it passes or refuses, and `produce admitted`, which hashes the bound inputs and asks nothing else.

### Left in the draft

- **Decision 11, a flow judged at every phase of its clock.** The kit's scan edits the scene's source to shift the flow's clock, bundles the composition again and reads one draw call, twenty-two times. An audit needs instead a way to shift a flow's clock from outside and to know which marks ride it, which neither the headless runtime nor any film's composition provides; the cost of the sweep is unmeasured, as that decision says. It needs a composition contract first, and the films are frozen until their December editions.
- **Decision 2**, the row gap's declared floor, and decisions 5 to 8, 12 and 16 to 21: no part of the readiness script, each with its own owner in the engine.
- **Of decision 14**: `check-sound` gating the thought line and the review prompt printing it.
- **From the kit's readiness script**: the level steps between thoughts, which the sound gate's own text calls not yet calibrated; the row probe (decision 2); the comparison of changed takes (decision 7); the listening plan (decision 12); and the checks of a lane, which are not the engine's.

## Risks / Trade-offs

- A film can declare its way past every finding. → Each declaration carries a reason, is listed in the gate record or refused as stale, and is read by reviewers.
- The far-run line refuses compositions that reviewers passed with a note. On the current compositions it lists seven runs in the DDWG film's two editions and three in the ETHOS film's, none in the essentials film's; the kit's scan, run at 1.0 s for those two films, listed none. → Each is repaired or declared when the film adopts this release; the films' pins hold until then.
- The sample film's English cues and the far runs of its real timelines were not read on a build here. → The sample build is the acceptance of this Change; a refusal names the cue or the run, and the sample then declares or repairs it.
- `preflight` now refuses a film that runs it before `check-sound` or the geometry check. → The sample's tasks run both first; the README states the order.

## Migration Plan

A film adopts this with the release that carries it: publish `draws` if it draws strokes by their tip; move its declared rails, fast cues and thoughts from its environment files into `content/film.toml`; repair or declare its far runs; replace its readiness script's engine questions by `preflight` and its ticket check by `admitted`. Rolling back is the film's pin.

## Open Questions

- Whether the receipt's schema should be the one ETHOS settles for host admission (the draft's first open question).
- Whether a film should be able to require `admitted` inside `render-picture`.
