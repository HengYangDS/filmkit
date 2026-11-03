# Design

## Context

See [proposal.md](proposal.md). The frame audit (`picture/frame-audit.mjs`) exercises every frame of an edition's composition headlessly and reports layout, legibility and balance findings, but exits 0 with them. Balance and cover are sampled at the reviewers' two instants of each thought, two seconds in and 70% through. The sync audit (`picture/sync_audit.py`) judges each label against its words from the frame audit's trace and marks, and the motion audit (`picture/motion-audit.mjs`) reports stills, pops, double exposures and colour snaps. `render-picture` checks only that the stage is current. A film owner ran all three audits before each render and refused gated findings with a script outside the engine.

A thought retake (`narration/retakes.py`) is a seed, and possibly a run-on, keyed by the thought's 1-based index and bound to the SHA-256 of the thought's display text. Synthesis narrates the thought's spoken text, which the pronunciation contract derives from the display text.

A review round (`review/round.py`) fills each edition's prompt from the film's template and lists the film's scored dimensions in it. Its context names the concept contract, or "none declared", and the reading occurrence plans, but a template is free to leave either field out.

## Goals / Non-Goals

**Goals:**

- The engine owns the pre-render gate: one command runs the headless audits, one list names what they may not find, and a render refuses a picture that was not checked as it stands.
- The audit measures balance and cover through all speech, as the reviewers do.
- A retake names the speech it was auditioned on, and is refused when that speech changes.
- A film that declares a concept contract has it cited and scored in every review round.

**Non-Goals:**

- Rendering a draft or scanning its pixels: the 10 fps draft and its still scan remain a separate review step.
- Changing what an existing film narrates or renders: a film on 0.5.0 builds as before, and its bound retakes keep binding.
- Gating the reviewers' pixel measures; they stay in the review.

## Decisions

- **Continuous runs on the audit's own lit points.** For each voiced frame the frame audit already gathers the lit marks and legible names it uses at the two instants (`litPoints`, kept to the band from 120 to 900 px). The new measure takes their box in every voiced frame, at the audit's step, and joins frames in which it stands more than 12% off the content centre (960, 510) on either axis, or covers less than a tenth of the band, into runs per scene. Runs of 2 s or more are reported as `off_centre_runs` and `thin_runs`, with start, end and the largest offset or the least cover. These are the reviewers' limits; the measure is headless, so the gate needs no render. A frame without speech ends a run.
- **One gated list in `picture/gates.py`.** The gated findings are:
  - the frame audit's `errors`, `overlaps`, `outside_safe_area`, `graphic_collisions`, `empty_during_speech`, `blank_between_scenes`, `bare_frames`, `dim_frames`, `faint_first_words`, `thin_during_speech`, `shapes_outside_action_safe`, `name_load`, `unplaced_labels`, `type_sizes`, `dot_joins`, `lists_leaving_early`, `lists_leaving_dimmed`, `off_balance`, `off_centre`, `off_centre_runs`, `sparse_runs`, `thin_lit`, `thin_runs`, `underfilled_containers` and `faint_clutter`;
  - every label the sync audit reports out of sync;
  - every still run of the motion audit longer than 3.5 s, the reviewers' limit for a held picture.

  The DDWG reviews turned each of these findings into a rule that a delivered film must keep. The motion audit's pops, jumps, dips, hitches, double exposures and colour snaps are reported in the record but not gated. Its rules count in-scene changes that a composition uses on purpose, so a review judges them.

- **`check-picture` binds what it checked.** The command runs the three audits from the film's root, the frame audit at one thirtieth of a second over the whole timeline with its trace and marks, and the motion audit at 30 frames per second. Their reports go to `build/runtime/work/picture-gates/<code>/`. It then writes `build/evidence/editions/<code>/picture-gates.json`. The record holds the SHA-256 of `picture/film.js` and of the edition's timeline, the engine version, the frame count the frame audit checked, each report's SHA-256, the gated findings and the verdict. A refusal names every gated finding.
- **`render-picture` reads the record.** Before it starts the renderer, it requires a passing record whose composition, timeline and engine version are the current ones, and otherwise refuses and names `check-picture`. The stage's own currency check is unchanged.
- **Retakes bind the spoken text too.** A retake entry may hold `spoken_sha256`, the SHA-256 of the spoken text its audition narrated. `apply_retakes` refuses an entry whose `spoken_sha256` differs from the thought's spoken text, with a message naming the segment and thought. An entry without it binds as before, so a cast bound on 0.5.0 still narrates the takes it recorded. The audition writes each row's spoken text. `bind_proposals` refuses a row without one, and a row whose spoken text is not the thought's current spoken text under the edition's pronunciation contract.
- **A declared contract is cited and scored.** `review.round.contract_gaps` reads the format fields of the prompt template. For a film that declares a concept contract, it reports a template without `{concepts}` or `{readings}` and dimensions without `concept_fidelity`, and `prompts` refuses before writing anything, naming each omission. A film without a contract owes neither. The sample film scores `concept_fidelity` in the words the DDWG and essentials films use, so the engine's own example meets the rule.
- **HyperFrames 0.9.6.** `RENDERER_VERSION` moves to 0.9.6. The browser pin moves only if 0.9.6 declares another Chrome build, and the `undici` override stays while HyperFrames pins 7.25.0.

## Risks / Trade-offs

- [The continuous runs refuse a picture a review would accept] → The limits are the reviewers' own; a composition that holds a sparse or off-centre picture for 2 s of speech is changed before it renders.
- [The headless lit box differs from the reviewers' pixel box] → Both use the same band and limits. The headless measure takes marks by their drawn extent and text by the headless canvas's estimated metrics, so the two boxes can differ by a few pixels. The draft's pixel measures still run in the review.
- [A film on 0.6.0 cannot render without the audits' time] → On 2026-11-03 the three audits of both 25-minute DDWG editions took 79 seconds together, while rendering the Chinese edition took 26 minutes.
- [Legacy retakes keep their text-only binding] → They bind takes already recorded and reviewed; the next audition of such a thought binds its spoken text.
- [A film's review configuration predates the contract] → The refusal names each field and dimension to add, before a round writes anything. The DDWG 1.2.0, ETHOS v2 and essentials configurations already have them.

## Migration Plan

Implement and test the runs, the gate, the retake binding and the review's contract check; move the supply to HyperFrames 0.9.6; build and verify the sample film through its picture task, which now checks the picture first; record and date the release notes. A film adopting 0.6.0 adds `check-picture` before each `render-picture` in its picture task and raises its `hyperframes` pin; a film with a concept contract also cites it and scores it in its review configuration. To roll back, a film pins 0.5.0 again.
