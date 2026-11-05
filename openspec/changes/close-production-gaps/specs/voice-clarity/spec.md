## Purpose

Measure how clear each edition's narrator sounds by one stated computation that reviewers can reproduce, and record it against the floors the film declares.

## ADDED Requirements

### Requirement: The review measures voice clarity by one stated method

The review's measurement SHALL record each edition's cepstral peak prominence over its soundtrack and over each segment's voice: the median, over the 1024-sample frames every 256 samples of the 16 kHz mono decode whose energy lies within 18 dB of their 95th percentile, of the peak of each Hann-windowed frame's cepstral level over quefrency bins 40 to 266 minus that level's least-squares line at the peak's bin.

#### Scenario: A clear voice and a breathy one

- **WHEN** one segment holds a harmonic voice and the next the same voice under noise
- **THEN** the first measures above 25 dB and the second below 18 dB

#### Scenario: Pauses do not count

- **WHEN** a voice is followed by a silence as long
- **THEN** only the frames of the voice and those that overlap its end are measured

#### Scenario: The stated steps

- **WHEN** a signal is measured both by the engine and step by step as the method states, with a least-squares solver for each frame
- **THEN** the two medians agree within 1e-9 dB over the same frames

### Requirement: A film declares its voice-clarity floors

A film MAY declare `review.clarity_minimum_db`, a floor in dB for each edition; the engine SHALL refuse a table that omits an edition, names another or holds a value outside 0 to 60. The measurement SHALL record each value to 0.01 dB beside its edition's floor and whether that value stands below it, and the prompts SHALL state the floors in `{clarity}`.

#### Scenario: A segment below its floor

- **WHEN** the Chinese floor is 18 dB and one Chinese segment measures below it
- **THEN** the measurement marks that segment below its floor and lists it among the segments below the floor

#### Scenario: A malformed floor table

- **WHEN** the declaration gives a floor for the Chinese edition only, for an edition the film does not have, or of 0 dB
- **THEN** the engine refuses the declaration, naming `review.clarity_minimum_db`

#### Scenario: A film without floors

- **WHEN** the declaration names no floors
- **THEN** the measurement records each value with no floor and no verdict, and the prompts state none declared
