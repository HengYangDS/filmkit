## MODIFIED Requirements

### Requirement: The sound gate refuses the lines reviewers hold

`check-sound` SHALL refuse when the soundtrack or a segment reads below the clarity floor the film declares, when a thought ends abruptly as delivered or is cut while voiced, and when a phrase stops without a heard fall, naming each place with its figure. A record of the owner's hearing SHALL settle no soundtrack and no segment. A film that declares no clarity floor SHALL NOT be judged on clarity.

#### Scenario: A stopped phrase refuses

- **WHEN** one phrase inside a thought stops without a heard fall
- **THEN** the action exits naming the thought, the word and the time

#### Scenario: A segment under the floor refuses

- **WHEN** the film declares an English floor of 17 dB and one English segment reads 16.72 dB
- **THEN** the action refuses and names the segment, its figure and the floor

#### Scenario: A segment under the floor whose thoughts were heard

- **WHEN** the film declares a floor of 18.0 dB, records hearings that settle the clarity of every take in one segment, and that segment reads 17.6 dB
- **THEN** the action refuses and names the segment, its figure and the floor, as it would without the records

#### Scenario: A film without a floor

- **WHEN** the film declares no clarity floor
- **THEN** no clarity figure is gated, and the endings are judged as before
