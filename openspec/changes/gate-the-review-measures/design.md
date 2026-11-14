## Context

Review rounds 16 (essentials), 19 (ETHOS film) and 40 (DDWG film) passed without a finding. Their notes were inventoried against the engine's gates on 14 November: of 159 findings of nine recent rounds, 63 were recorded by the engine and never refused, and 34 were measurable and unmeasured. The reviewers' measuring scripts and their figures for the delivered films exist beside those rounds' reviews and are the reference for every measure this Change adds.

## Goals / Non-Goals

**Goals:**

- Each new or changed measure agrees with the reviewers' own on the delivered films: it flags what their notes name and nothing they accepted.
- A film learns of a broken line before it renders, from a record bound to what was judged.
- The next editions of the three films can close their notes against the engine's records.

**Non-Goals:**

- No general table of film-declared limits yet: two measures gain a switch, because their calibration requires it.
- No measure that the reviewers' own figures do not settle: the rate step between thoughts stays recorded, since its measures disagree in direction.
- No release publication or host scheduling, which the common base owns.

## Decisions

1. **A sound gate beside the picture gate.** `check-sound` is a production action of its own, run after `refresh-captions`, and not a refusal inside `assemble`: the assembly must write the soundtrack and timeline that the measures read, and a command that both produces and refuses its product leaves a half-accepted state. Its record is bound to the two files it judged, as the picture gate's is bound to the composition and timeline.
2. **The sound gate takes the review's measures as they are.** It calls the functions the review's measurement calls, so the producer and the reviewer read one computation. Recomputing them in the gate would create a second measure that could drift.
3. **Only calibrated lines are gated.** On the measurements of seven delivered rounds the gate's lines flag two soundtracks, each for the one phrase its reviewers noted, and pass the rest. Level and rate steps between thoughts stay recorded.
4. **The thought-level tolerance floor is 0.25 dB.** Two adjacent thoughts at opposite edges of a 0.5 dB tolerance stand 1.0 dB apart, which is the step reviewers note; a quarter keeps them within half a decibel. The gain limits and the peak ceiling are unchanged.
5. **Segment clarity follows the whole soundtrack's grid and threshold.** The reviewers keep frames by one energy threshold over the whole soundtrack and assign a frame to the segment that holds its centre; the engine cut each segment out and thresholded it alone, which reads a quiet segment higher. The whole-soundtrack figure is unchanged.
6. **A thought's clarity is its median over the grid's phases.** A short thought holds few frames, and its figure moves by more than half a decibel with the grid's phase; sixteen phases and the spread say how far it can be trusted, and fewer than 150 kept frames marks it short.
7. **A cue holds its typeset text; the script's copy stays the script's.** A timeline carries two kinds of text: the caption cues, which are shown, and the segments' narration, thoughts and words, which are the script's copy and the aligner's items and which the picture, the refresh and the verification hold byte-equal to the script. Typesetting the copy would make a derived file disagree with its source, so only the cues change, and a reviewer who counts straight marks counts them in the cues.
8. **A line that reviewers hold one film to is that film's to declare.** On the delivered films the row-gap measure finds every pair the DDWG and essentials notes name, and eleven more pairs in pictures whose reviewers accepted them, such as the words of the ETHOS film's spelled-out name; the pace measure finds the DDWG glides its notes name, and forty stretches in the ETHOS film whose reviewers noted none. A gate that refused those would disagree with the acceptance authority. So both measures are always recorded, and a film switches the gate on: `--gate-row-gaps` on its geometry check and `picture.motion.pace_limit` in its declaration. The bound for edge slivers stays an engine constant, since no delivered master comes near it.
9. **An identical file is not decoded and calibrates nothing.** Equal bytes decode to equal frames, so the comparison reports the film as identical with its PSNR not measured; a film without a recorded floor still does not pass.

## Risks / Trade-offs

- A film that adopts the release is refused where the previous release passed. → That is the purpose; each gate lists the place and figure, and the three films' next editions already carry the repairs as tasks.
- A measure tuned to the delivered films could miss the next fault. → Constants come from the reviewers' stated lines, not from fitting; each gate has a synthetic refusing case in the tests.
- Changed segment clarity figures break the comparison with earlier rounds. → The method text in the measurement and in the prompts states the rule, and the release note names the change.
