## ADDED Requirements

### Requirement: The assembled soundtrack is judged before the picture follows it

The engine SHALL provide a production action, `check-sound`, that takes from an edition's assembled soundtrack and its timeline the review's own measures of voice clarity and of delivered endings and writes them with their verdict to the edition's sound gate record, bound to the SHA-256 of the soundtrack and of the timeline it judged.

#### Scenario: A soundtrack that holds every line passes

- **WHEN** no segment reads below the declared floor, every thought ends naturally and no phrase stops
- **THEN** the record's verdict is pass, it holds the measures and both digests, and the action succeeds

#### Scenario: A refused soundtrack keeps its record

- **WHEN** the action refuses
- **THEN** the record holds the verdict refuse and every gated finding, so the refusal can be read after the command ends

### Requirement: The sound gate refuses the lines reviewers hold

`check-sound` SHALL refuse when the soundtrack or a segment reads below the clarity floor the film declares, when a thought ends abruptly as delivered or is cut while voiced, and when a phrase stops without a heard fall, naming each place with its figure. A film that declares no clarity floor SHALL NOT be judged on clarity.

#### Scenario: A stopped phrase refuses

- **WHEN** one phrase inside a thought stops without a heard fall
- **THEN** the action exits naming the thought, the word and the time

#### Scenario: A segment under the floor refuses

- **WHEN** the film declares an English floor of 17 dB and one English segment reads 16.72 dB
- **THEN** the action refuses and names the segment, its figure and the floor

#### Scenario: A film without a floor

- **WHEN** the film declares no clarity floor
- **THEN** no clarity figure is gated, and the endings are judged as before

### Requirement: A film declares how closely each thought keeps its segment's level

A script's voice performance MAY declare `thought_level_tolerance_db` from 0.25 to 6.0. The assembly SHALL move a thought whose loudness stands farther than that from its segment's median to the edge of the tolerance by one static gain, and the engine SHALL refuse a value outside the range.

#### Scenario: A quarter of a decibel is accepted

- **WHEN** a script declares a thought-level tolerance of 0.25 dB
- **THEN** the pause policy holds it, and two adjacent thoughts of one segment are assembled at most 0.5 dB apart unless a gain limit or the peak ceiling holds one back

#### Scenario: A tighter value refuses

- **WHEN** a script declares a thought-level tolerance of 0.2 dB
- **THEN** the engine refuses the policy and names the range from 0.25 to 6.0
