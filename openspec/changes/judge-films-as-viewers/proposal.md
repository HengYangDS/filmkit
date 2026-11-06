# Proposal

## Why

The owner judges every film as a first-time viewer, by 信、达、雅. Since 2026-11-01 the owner has repeatedly been the first to notice a fault that the engine's gates and two reviews scoring 95–97 did not report. 0.11.0 gated pauses, term readings, number and the players. Three classes of fault still have no owner:

- **Motion.** No gate measures motion. The picture's motion audit follows a mark only while its box in its own coordinates stays put. It never follows a flow's dot or a glide, and nothing it records refuses a render. The owner saw the ETHOS flow dots halt dead at the end of every thought and set off again at full speed.
- **Averaged reviews.** The reviews score twelve technical dimensions and average them, so a strong score in one dimension makes up for a fault in another. The owner accepts a film only when each of 信, 达 and 雅 holds as a whole.
- **Sentences.** The reviews' language check scans for patterns. Nothing reads each sentence as speech, as a newcomer hears it, which is how 「也可能是当初想要得到的好处」 went through.

## What Changes

- **Motion continuity in `check-picture`.**
  - The motion audit follows every mark across frames as a viewer sees it move: by its scene, kind, words and line width, by its own motion, and through growth, shrinking, redrawing and words that change in place. Speeds are in 1080p pixels per second.
  - `check-picture` refuses, outside stage cuts:
    - `motion_halts`, a mark that falls from at least 60 px/s to rest within one frame;
    - `motion_starts`, the reverse;
    - `motion_races`, a mark at 900 px/s or more;
    - `motion_pops`, a firm mark that appears or vanishes within one frame.
  - Each finding names its time, scene, kind, words and the composition line that drew it. This is the calling scene line rather than a shared helper, and also the module where the composition is bundled from modules.
  - A film may keep a finding by declaring `[[picture.motion.exceptions]]`. An exception that matches no finding is refused.
  - The audit records, per scene, the largest glide and flow speeds a viewer meets.
  - **BREAKING**: the gate applies to every film from 0.12.0, whatever it declares.
- **信、达、雅 as the review's acceptance structure.**
  - `content/film.toml` may declare `[review.levels]`: the levels 信, 达 and 雅, each with what it asks of the whole film and the dimensions it holds.
  - `review.round prompts` states the levels in `{levels}`.
  - A review records a verdict for each level, and each finding names its level. `review.round record` and the verifier refuse any of these:
    - a level that fails;
    - a level verdict that contradicts its findings or its dimensions' floors;
    - a missing level.
- **Every sentence judged.** `review.round prompts` writes each edition's sentences, with stable ids and timeline times, and names the file in `{sentences}`. A film that declares levels gets a verdict for every sentence. A review that misses a sentence or names an unknown one is refused.
- **Motion in the review's measurements.** `review.measurement` records each edition's motion from its current picture gate: the counts, the largest speeds and the events with their times.
- **The sample film** declares `[review.levels]`, and its prompt cites `{levels}` and `{sentences}`.
- **Out of scope.** Gating the quiet between thoughts, which the reviews measure, and moving a film to 0.12.0, which each film does in its own lane.

## Capabilities

### New Capabilities

- `picture-motion`: following every mark of an edition's picture as a viewer sees it move, refusing halts, starts, races and pops before a render, the film's declared exceptions, the speeds a viewer meets, and the motion the review's measurements record.

### Modified Capabilities

- `review-rounds`: a film's review levels, stated in the prompts and accepted level by level; the sentences file and a verdict for every sentence.
- `sample-film`: the sample film declares the three review levels.

## Impact

- **Code.**
  - `src/filmkit/picture/motion-audit.mjs` with new modules below `motion-audit/` for following marks and for the findings, and `headless-composition.mjs` for attribution;
  - `picture/gates.py`, and `film.py` for `[picture.motion]` and `[review.levels]`;
  - `review/prompts.py`, `review/record.py`, `review/round.py` and a new `review/sentences.py`;
  - `delivery/verification.py`;
  - `review/measurement.py` with a new `review/motion.py`.
- **Film declarations.** `content/film.toml` gains `[[picture.motion.exceptions]]` and `[review.levels]`. A film that declares levels cites `{levels}` and `{sentences}` in its prompt.
- **Adoption.**
  - No film's output bytes change.
  - Every film's `check-picture` verdict can change. On their current compositions the three films are refused until they repair their motion findings or declare them.
  - A film without `[review.levels]` keeps today's prompts, records and verification.
