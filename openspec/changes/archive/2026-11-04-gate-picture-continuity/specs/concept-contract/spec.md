## MODIFIED Requirements

### Requirement: Counterexamples are refused wherever a viewer meets words

No counterexample of any concept SHALL appear in an edition's narration, segment titles, chapter titles, caption terms, player prose or release synopsis, comment and description, or in a text file of the film's picture sources. Every occurrence SHALL be named with its location, and all occurrences SHALL be reported together.

#### Scenario: A rejected rendering in the narration

- **WHEN** a Chinese segment's narration contains a counterexample of a concept
- **THEN** the check refuses and names the segment, the counterexample and its position

#### Scenario: A rejected rendering in a picture label

- **WHEN** a picture source file contains a counterexample
- **THEN** the check refuses and names the file and the line

#### Scenario: A rejected rendering in the player's description

- **WHEN** the visible prose of an edition's player names a counterexample
- **THEN** the check refuses and names the edition's player and the counterexample

#### Scenario: A rejected rendering in the release synopsis

- **WHEN** an edition's release synopsis names a counterexample
- **THEN** the check refuses and names the edition's synopsis and the counterexample

#### Scenario: Markup the player does not show

- **WHEN** a counterexample stands only in the player's script or style element
- **THEN** the check does not refuse it as player prose
