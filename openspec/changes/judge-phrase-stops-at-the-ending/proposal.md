## Why

The sound gate of 0.22.0 refused the English soundtrack of a film's next edition for a phrase whose take is byte for byte the take its delivered edition holds: thought 01.2 stops at "overnight," after a fall of 5 ms. The delivered soundtrack passes the same gate. Nothing in the sound differs; the new soundtrack begins 16 ms later, so its samples lie on another phase of the measure's frame grid.

Two defects in the measure of a stopped ending explain it.

- The fall is the median over every phase of the 1 ms grid, but the voicing before it is read on one phase only. On this ending 37 of the 48 phases read voiced and 11 do not, so the verdict follows where the soundtrack happens to start.
- The fall is judged at the take's own level and again with its bounds lowered by the gain the soundtrack applies, and the shortest fall is the verdict, while the voicing is always read where the fall at the take's own level begins. At "overnight," the vowel closes into the stop consonant in 5 ms at the take's own level, and the consonant's release follows 60 ms later and dies away over 19 ms. The release lies under the take-level bound and is heard at the delivered level. The measure judged the closure as the ending. A reviewer of the delivered round had examined this place and found the release natural. At "person," in another film the fast fall is the one at the delivered level, and the voicing was read 3 ms before it, at another place.

The calibration of 0.22.0 counted both phrases as lines the reviewers hold. Only one is: the reviewer who noted "overnight," noted that the measure was wrong there.

## What Changes

- The voicing before a fall is read where that fall begins, at the gain that gives it, and is the median over every phase of the frame grid, as the fall is. An ending's verdict no longer depends on where its recording or soundtrack starts.
- A fall is not the ending when the sound rises again after it: when the last sound heard as loud at the greatest gain judged lies after the fall's stop and itself dies away. Such a fall is a closure before its release, and the release is judged as the ending.
- A sound after a fall that itself stops at once, such as a click, excuses nothing: the fall before it stays the ending.

The rule is one function, so it holds alike for a take's ending, a phrase's ending inside a take, and both as delivered in a soundtrack.

Out of scope: a release that follows its closure after 80 ms or more of heard quiet, which the phrase measure still takes for the next phrase's quiet; a declared exception for a single ending.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `narration-endings`: a fall is judged at the ending a listener hears, independent of the frame grid's phase.

## Impact

- `src/filmkit/narration/take_edges.py` (`final_fall`), its tests.
- Recorded `final_voicing` and `final_fall_gain_db` values of takes may change; the verdicts of the takes the three films hold are compared before release.
- A film's sound gate no longer refuses a closure before a heard release, and holds its verdict when a soundtrack shifts.
