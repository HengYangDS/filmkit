## ADDED Requirements

### Requirement: The geometry check refuses a record that does not cover the staged film

The node `geometry-check` SHALL refuse, after it writes its record, a record that did not pass, that holds a finding or an error, or that does not cover the whole current staged film at a step of 1 or 2 frames, naming the record and what it lacks.

#### Scenario: A record of fewer frames

- **WHEN** the geometry check sampled fewer frames than the staged film's runtime gives at its step
- **THEN** the node refuses, naming the record and the frames it checked against the frames it must

#### Scenario: A covering record

- **WHEN** the record passed on the whole current staged film at a step of 2
- **THEN** the node passes, and the plan holds the edition's render behind no geometry refusal
