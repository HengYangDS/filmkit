## Context

What the engine holds today, read in 0.22.3 on 15 November 2026:

- `check-picture` and `check-sound` write a gate record that binds the composition, timeline, stylesheet, fonts and engine by SHA-256, and `render-picture` reads the picture's record before it starts the renderer.
- Two classes of finding already have the form this Change generalizes: a wrapped label that breaks a rule and a motion finding are gated unless one of the film's declared exceptions names them with a reason, and an exception that matches nothing is gated as stale.
- `preflight` names every stale input of a render at once: both stages, the cover, an earlier package record, the draft scan, the concept check and the picture gate.
- `narration.script_edits` rebuilds a changed segment and releases the retakes bound to its old text; `narration.audition` refuses a thought whose text changed after the last narration.

What happened on that day, from the three films' own records (each film's Change design and its `build/evidence/retrospectives/2026-11-15.md`, local evidence written that day):

| When | Film | What was spent | What a light check would have said |
| --- | --- | --- | --- |
| 09:33 | ETHOS film | one Chinese picture, 56 minutes | the geometry record listed four row pairs under 1.5 em, ungated without the flag |
| 10:03 to 11:20 | ETHOS film | one English and two Chinese pictures, and a fourth interrupted | the motion audit recorded 35 and 37 stretches over 450 px/s with no limit declared, and a probe at 1.7 em listed five more row pairs |
| morning | essentials film | one Chinese picture, about 70 minutes | the level tolerance changed after the render, and the timeline embeds it |
| 11:00 to 13:00 | DDWG film | two narrations of one thought, three of another | the first recheck found four points a first hearing misreads |
| 11:25 | DDWG film | three bound retakes | on the soundtrack they read 0.40 to 0.68 dB under the takes they replaced |
| 13:11 | DDWG film | one audition ticket | its targets held a thought edited after the last narration |
| 14:00 | ETHOS film | a 44-minute queue wait, refused as the ticket started | the stage bound an assembly record that a later sound stage rewrote |
| 15:57 to 16:43 | DDWG film | five rounds of staged audits of both editions | picture cues named words the text no longer said; a longer name unseated a mark; two moves stood one frame over the pace |

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

Each decision names what was weighed, what is taken and why, and where it applies.

1. **Recorded findings take the form the wrapping and motion exceptions already have.** Weighed: (a) counts in a film's task list or script, as the films did on 15 November; (b) gating every recorded class outright; (c) declaration by identity with a reason, stale ones refused. Taken: (c). A count passes when one finding leaves and another arrives, and it lives outside the gate; an outright gate would refuse films that reviewers accepted with those findings declared (one English thought stood 0.66 dB under its floor after thirty-two takes). A declaration by identity is what a reviewer reads, and a stale one cannot linger. Applies to captions above the reading rate (by the cue's text), thoughts under the clarity floor (by thought), row gaps (by scene and the two names) and whatever class a later gate records. Does not apply to the classes a spec defines as informational: thoughts that hold the previous picture within the limit, and cues mostly but not wholly drawn as labels.
2. **The row gap's floor is a declaration, not a flag.** Weighed: keeping `--gate-row-gaps` in each film's task list; a declared floor with a default. Taken: the declaration, default 1.5 em. All three films pass the flag today, one review asks 48 px at 1080p, about 1.63 em of the films' label face, and the films probed 1.7 em with a copied check. A flag is forgotten once per film; a floor in `content/film.toml` is read by the same check everywhere. Breaking only for a film that holds pairs under 1.5 em undeclared.
3. **`preflight` grows; no second readiness tool.** Weighed: (a) a new `ready` command beside `preflight`; (b) each film keeping a script; (c) extending `preflight`. Taken: (c). The films' script repeated part of `preflight` and missed a binding it knew (the stage binds the assembly record). One owner per question is this repository's rule for behavior. The draft scan becomes a declaration because the films replaced drafts by the every-frame audits of `check-picture`; a film that declares drafts keeps today's behavior.
4. **The receipt binds inputs by digest and is checked without repeating the work.** Weighed: re-running `preflight` before each ticket (minutes of audits read again); a receipt with the SHA-256 of each judged input and a cheap check that they still hold. Taken: the receipt. It is what a queue can ask for at admission and what a later reader can verify. The engine writes and checks it; admitting a ticket on it is the host's. Both editions are judged for a render of either, since they share the composition.
5. **A text review is a record, and requiring it is the film's declaration.** Weighed: leaving the order to the film's process; a record that `narrate` can require. Taken: the record, opt-in. The engine cannot judge a recheck's independence, but it can refuse narration of scripts that no recorded verdict covers. Opt-in because the sample film and a film in its first draft narrate before any review exists.
6. **The script editor reports the picture's words it leaves behind; the film's own tests remain the proof.** Weighed: (a) only the film's picture tests, which paint every scene from the script and fail on a missing cue; (b) a report from the editor listing quoted phrases of the changed segments' scene modules that the old text said and the new one does not. Taken: both. The tests catch a cue; they do not catch a label that still shows the old wording. The report is a list for the author, not a gate, because a label may deliberately keep a condensed wording.
7. **A retake is compared on the soundtrack with the previous edition's take.** Weighed: the picking measure on the take alone; the assembled soundtrack against the previous edition's, judged by the engine's own clarity measure. Taken: the soundtrack. Differences under about 0.3 dB between takes lie within the measure, and the order of two takes changed between the take and the soundtrack in two films. The margin is the film's to declare, default 0.3 dB. Applies when the film names a previous edition; a first edition has none.
8. **Caption breaks choose among allowed breaks by reading rate.** Weighed: authored breaks per cue in the script, as two films wrote by hand for four cues; the breaker weighing the rate itself. Taken: both, the breaker first. Authored breaks stay for the cases a rule cannot see, such as a cue that would equal a label.
9. **The thresholds' sources are written once, here.** The pace line, the row floor, the level steps between thoughts and the reading rate are used by three films and came from review records of those films. The study names each value, the record it came from and its date, and what it does not cover. Its form follows what ETHOS provides for research documents when that is released; until then the facts stand in this design.

Left out, with the reason: typesetting the timeline's narration fields (they are never shown, and changing them would release every take whose thought holds an apostrophe); a syllable rate by sound between thoughts (one review asked for it in one film; no second case yet).

## Risks / Trade-offs

- A film can declare its way past every finding. → Each declaration carries a reason, is listed in the gate record, and is read by the reviewers with the round's changes note; a stale one is refused.
- `preflight` becomes slower as it reads more records. → It reads records, not media; the audits stay in `check-picture` and `check-sound`.
- The breaking parts reach three films at once. → Each already declares these findings in its design; the adoption is moving them into `content/film.toml`, with the lists the films' own records hold.

## Open Questions

- Whether the receipt's schema should be the one ETHOS settles for host admission, so that one file serves both.
- Whether the review round's facts (changes note, dispositions) join this Change's receipt or keep their own records.
