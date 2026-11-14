## ADDED Requirements

### Requirement: A fall is judged at the ending a listener hears

The measure of a stopped ending SHALL read the voicing where the judged fall begins, at the gain that gives that fall, as the median over every phase of the frame grid. A fall SHALL NOT count as the ending when the sound rises again after it and dies away: when the last sound loud at the greatest gain judged lies after the fall's stop and falls in 6 ms or more.

#### Scenario: The same sound on another phase of the frame grid

- **WHEN** one recording is measured again with any number of samples of silence before it
- **THEN** its fall, its voicing and its verdict are the same

#### Scenario: A closure before a heard release

- **WHEN** a voiced syllable closes in under 6 ms at the take's own level and a release follows that is loud only at the delivered level and dies away over 6 ms or more
- **THEN** the ending is judged at the release and does not stop

#### Scenario: A cut that only the delivered level shows

- **WHEN** a voice fades under the take-level bound, is then cut in under 6 ms and is voiced where that cut begins, though unvoiced sound precedes the fade
- **THEN** the ending stops

#### Scenario: A click after a cut

- **WHEN** a voiced syllable is cut in under 6 ms at the take's own level and a sound follows that is loud only at the delivered level and itself falls in under 6 ms
- **THEN** the ending stops
