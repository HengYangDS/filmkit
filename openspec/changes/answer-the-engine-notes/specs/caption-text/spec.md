## ADDED Requirements

### Requirement: An English caption read too fast is joined, held or recorded

An English cue read faster than 25 characters per second SHALL join an adjacent cue of its segment when no sentence ends between them, they stand under 0.25 s apart and the joined line fits 66 characters; otherwise it SHALL hold into the quiet after it until it reads at 25 characters per second, never past the next cue's start. A cue still above the rate SHALL be recorded with its rate. Cue words and starts SHALL stay their own; Chinese cues SHALL be unchanged.

#### Scenario: A fast cue joins its neighbour

- **WHEN** the cue "The inference is that the vendor" of 32 characters is shown for 1.12 s, and its sentence continues in the next cue 0.05 s later with 30 characters
- **THEN** the two become one cue of 62 characters from the first cue's start to the second's end

#### Scenario: A fast cue at a sentence end

- **WHEN** a cue of 26 characters ends its sentence after 0.9 s and the next cue starts 0.6 s later
- **THEN** it keeps its text and start and ends 1.04 s after it starts

#### Scenario: A cue within the rate

- **WHEN** a cue of 40 characters is shown for 2 s
- **THEN** it is unchanged

#### Scenario: A fast cue that can neither join nor hold

- **WHEN** a cue of 32 characters is shown for 1.12 s, joining it with the next cue of its sentence would make a line of 69 characters, and the next cue starts as it ends
- **THEN** it keeps its text and times, and the edition's caption record lists it at 28.6 characters per second
