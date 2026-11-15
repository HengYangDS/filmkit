## Why

The assembly levels each thought within a declared tolerance of its segment's median and each chapter within a declared tolerance of the film's median. Nothing levels a segment within its chapter. Two neighbouring segments of one chapter can therefore stand apart by the difference of their medians plus twice the thought tolerance, and reviewers hold a line on the step between adjacent thoughts across a segment boundary.

One film's next edition shows it. Its reviewers ask for at most 1.0 LU between adjacent thoughts inside a segment and 1.2 LU across one. With a thought tolerance of 0.4 dB the steps inside its segments stand at 0.81 LU or less, but one segment's median lies 0.74 LU under its chapter's after three of its thoughts took new takes, and the step into it measures 1.34 LU. Narrowing the chapter tolerance changes nothing there, since both segments belong to one chapter; the only lever left to the film was to pick takes by their loudness.

## What Changes

- A script's voice performance may declare `segment_level_tolerance_db`. The assembly then brings each segment whose leveled thoughts stand farther than that from its chapter's median to the edge of the tolerance by one static gain, before the chapters are leveled to the film.
- The assembly receipt records each segment's gain and the declared tolerance.
- A film that declares no segment tolerance is assembled to the same soundtrack and timeline as before.

Out of scope: a line the sound gate would refuse on level steps, which stay with the review's measurement until they are calibrated against reviewers; any change to the thought or chapter leveling.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sound-gates`: a film may declare how closely each segment keeps its chapter's level.

## Impact

- `src/filmkit/soundtrack/level.py`, `policy.py`, `assembly.py` and their tests, and the new module `clip_levels.py`, which takes the clips' segment and chapter gains out of the assembly module so that it keeps within the repository's 500 code lines; the README's list of what a script declares.
- The assembly receipt's pause policy gains the key `segment_level_tolerance` and each record `segment_gain_db`; soundtracks and timelines of films that do not declare the tolerance keep their bytes.
