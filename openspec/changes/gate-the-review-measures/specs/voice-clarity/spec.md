## ADDED Requirements

### Requirement: A segment's clarity takes the soundtrack's threshold and grid

The measurement SHALL record each segment's clarity as the median over the soundtrack's kept frames, by its one energy threshold and on its one frame grid from the first sample, whose centres, each frame's start plus 512 samples, lie from the segment's start to before its end in the timeline.

#### Scenario: A quiet opening

- **WHEN** a segment opens 20 dB below the soundtrack's loud voice and then rises
- **THEN** its quiet frames are not measured, though the segment measured alone would keep them

#### Scenario: The reviewers' assignment

- **WHEN** the segments are also measured from the whole soundtrack's kept frames by their centres from each segment's start to before its end
- **THEN** each value and frame count agrees, and every kept frame belongs to one segment

#### Scenario: A segment without a kept frame

- **WHEN** no kept frame's centre lies inside a segment
- **THEN** the segment records no value, 0 frames and no verdict

### Requirement: A thought's clarity is its median over sixteen grid phases

The measurement SHALL record each thought's clarity as the median of its medians on the 16 frame grids that start 0, 16 and so on to 240 samples into the soundtrack, each over the frames at or above the soundtrack's threshold whose centres lie from the thought's first word to before its last word's end. It SHALL record beside it the first grid's value and kept frames and the lowest and highest grid, and SHALL mark a thought with fewer than 150 kept frames short.

#### Scenario: The phase median

- **WHEN** a thought is measured step by step on each of the 16 grids
- **THEN** the record holds the median, lowest and highest of those values and the first grid's value and frame count

#### Scenario: A short thought

- **WHEN** a thought of 2 s keeps 125 frames and one of 3 s keeps 188
- **THEN** only the first is marked short and listed among the short thoughts

#### Scenario: Below the floor by its median

- **WHEN** a thought's grids read from 17.88 to 18.72 dB with a median of 18.3 dB against a floor of 18 dB
- **THEN** the thought records 18.3 dB and does not stand below its floor

## MODIFIED Requirements

### Requirement: The review measures voice clarity by one stated method

The review's measurement SHALL record each edition's cepstral peak prominence over its soundtrack: the median, over the 1024-sample frames every 256 samples of the 16 kHz mono decode whose energy lies within 18 dB of their 95th percentile, of the peak of each Hann-windowed frame's cepstral level over quefrency bins 40 to 266 minus that level's least-squares line at the peak's bin.

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

A film MAY declare `review.clarity_minimum_db`, a floor in dB for each edition; the engine SHALL refuse a table that omits an edition, names another or holds a value outside 0 to 60. The measurement SHALL record each value to 0.01 dB beside its edition's floor and whether that value stands below it, list the segments and the thoughts below it, and the prompts SHALL state the floors in `{clarity}`.

#### Scenario: A segment below its floor

- **WHEN** the Chinese floor is 18 dB and one Chinese segment measures below it
- **THEN** the measurement marks that segment below its floor and lists it among the segments below the floor

#### Scenario: A malformed floor table

- **WHEN** the declaration gives a floor for the Chinese edition only, for an edition the film does not have, or of 0 dB
- **THEN** the engine refuses the declaration, naming `review.clarity_minimum_db`

#### Scenario: A film without floors

- **WHEN** the declaration names no floors
- **THEN** the measurement records each value with no floor and no verdict, and the prompts state none declared
