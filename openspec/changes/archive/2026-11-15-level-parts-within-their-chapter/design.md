## Context

`level_thoughts` moves each thought of a segment to within the thought tolerance of that segment's median loudness, by one static gain per thought of at most 3 dB. `chapter_level_gains` then moves each chapter whose median leveled thought stands beyond the chapter tolerance of the film's median, by one static gain of at most 2 dB that keeps the peak below −1 dBFS. A segment keeps the level its recording has, apart from a correction a recording may declare with its evidence.

On the English soundtrack of one film's next edition the segments' medians stand from 0.74 LU under to 0.58 LU over their chapters' medians; the review's `level_continuity` measures the largest step between adjacent thoughts at 1.34 LU, into the segment that stands lowest.

## Goals / Non-Goals

**Goals:**

- A film can bound the step between adjacent thoughts across a segment boundary by declaration: with a thought tolerance `t` and a segment tolerance `s`, two neighbouring segments of one chapter stand at most `2 (t + s)` apart at their boundary, unless a gain limit or the peak ceiling holds one back.
- Films that declare nothing keep their soundtracks and timelines byte for byte.

**Non-Goals:**

- Gating level steps in `check-sound`.
- Leveling across a chapter boundary beyond what the chapter tolerance already does.

## Decisions

- **The segment gain follows the chapter gain's shape.** A segment's level is the median loudness of its leveled thoughts and the reference is the median over every leveled thought of its chapter; a segment beyond the tolerance moves to its edge by one static gain of at most 2 dB that keeps its peak below −1 dBFS. One rule at three scales (thought in segment, segment in chapter, chapter in film) is easier to state and to verify than a second mechanism.
- **Segments are leveled before chapters.** The chapter's median is then taken over thoughts that already stand near each other, and the chapter gain acts on the result. The other order would level a chapter by a median that the segment gains then move.
- **One pass.** Moving a segment moves its chapter's median a little; the gains are computed once from the medians before any segment moved, as the chapter gains are computed once from the film's median. Iterating to a fixed point would hide the rule behind a loop for a few hundredths of a decibel.
- **A chapter of one segment has no segment gain.** Its segment's median is the chapter's.
- **The receipt always records the key and the gain,** as it records every other policy key: `segment_level_tolerance` holds null without a declaration, and each record's `segment_gain_db` holds 0.0. The receipt's bytes change for every film; no soundtrack or timeline does.
- **Range 0.1 to 3.0 dB,** the chapter tolerance's range.

## Risks / Trade-offs

- A segment gain changes the level a reviewer hears across a whole part. → It is bounded at 2 dB and by the peak ceiling, recorded per segment, and the film chooses the tolerance.
- A film could declare a segment tolerance tighter than its thought tolerance, which levels segments by medians whose thoughts scatter more than the tolerance. → Allowed: the median is still well defined, and the receipt shows the gains.
- Adopting films change their soundtrack and timeline when they declare the tolerance. → It is a pause-and-level policy like the others: settled before any picture is staged.
