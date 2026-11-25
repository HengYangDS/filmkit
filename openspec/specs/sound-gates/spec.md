# sound-gates Specification

## Purpose

Judge an assembled soundtrack by the lines reviewers hold, before the picture is rendered on it, and let a film declare how closely each thought keeps its segment's level.

## Requirements

### Requirement: The assembled soundtrack is judged before the picture follows it

The engine SHALL provide a production action, `check-sound`, that takes from an edition's assembled soundtrack and its timeline the review's own measures of voice clarity and of delivered endings and writes them with their verdict to the edition's sound gate record, bound to the SHA-256 of the soundtrack and of the timeline it judged.

#### Scenario: A soundtrack that holds every line passes

- **WHEN** no segment reads below the declared floor, every thought ends naturally and no phrase stops
- **THEN** the record's verdict is pass, it holds the measures and both digests, and the action succeeds

#### Scenario: A refused soundtrack keeps its record

- **WHEN** the action refuses
- **THEN** the record holds the verdict refuse and every gated finding, so the refusal can be read after the command ends

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

### Requirement: A film declares how closely each thought keeps its segment's level

A script's voice performance MAY declare `thought_level_tolerance_db` from 0.25 to 6.0. The assembly SHALL move a thought whose loudness stands farther than that from its segment's median to the edge of the tolerance by one static gain, and the engine SHALL refuse a value outside the range.

#### Scenario: A quarter of a decibel is accepted

- **WHEN** a script declares a thought-level tolerance of 0.25 dB
- **THEN** the pause policy holds it, and two adjacent thoughts of one segment are assembled at most 0.5 dB apart unless a gain limit or the peak ceiling holds one back

#### Scenario: A tighter value refuses

- **WHEN** a script declares a thought-level tolerance of 0.2 dB
- **THEN** the engine refuses the policy and names the range from 0.25 to 6.0

### Requirement: A film declares how closely each segment keeps its chapter's level

A script's voice performance MAY declare `segment_level_tolerance_db` from 0.1 to 3.0. The assembly SHALL then move a segment whose leveled thoughts' median loudness stands farther than that from the median over its chapter's leveled thoughts to the edge of the tolerance, by one static gain of at most 2 dB that keeps the segment's peak below −1 dBFS, before it levels the chapters, and SHALL record each segment's gain. The engine SHALL refuse a value outside the range.

#### Scenario: A segment that stands under its chapter is raised

- **WHEN** a script declares a segment-level tolerance of 0.2 dB and one of a chapter's three segments stands 0.8 dB under the chapter's median
- **THEN** that segment is assembled 0.6 dB louder, its record holds the gain, and the other two segments keep their level

#### Scenario: A film that declares nothing

- **WHEN** a script declares no segment-level tolerance
- **THEN** the soundtrack and the timeline hold the bytes the previous release assembled, every record's segment gain is 0, and the receipt's policy holds no tolerance

#### Scenario: A value outside the range refuses

- **WHEN** a script declares a segment-level tolerance of 0.05 dB
- **THEN** the engine refuses the policy and names the range from 0.1 to 3.0

### Requirement: The sound gate judges each thought against the film's thought line

A film MAY declare a margin of zero or more under its clarity floor. `check-sound` SHALL then refuse a thought the sound gate reads under the floor less that margin, and one between that line and the floor the film does not declare by name with a reason, unless the owner heard its selected take clear; and it SHALL refuse a declared thought reading at or over the floor. With a margin of zero no thought MAY be declared. Without a margin it SHALL report that single thoughts are not judged.

#### Scenario: A thought under the thought line

- **WHEN** the floor is 18 dB, the margin 1.0 dB and a thought reads 16.9 dB
- **THEN** the gate refuses, naming the thought, its reading and the line of 17.0 dB, whether or not the thought is declared

#### Scenario: A thought between the two lines

- **WHEN** a thought reads 17.62 dB and the film declares it with a reason
- **THEN** the gate refuses nothing for it; undeclared, the gate names it and the declaration that would keep it

#### Scenario: A declared thought that reads at the floor again

- **WHEN** a declared thought reads 18.4 dB after a retake
- **THEN** the gate refuses the declaration as stale

#### Scenario: A margin of zero

- **WHEN** the floor is 18 dB and the margin 0
- **THEN** a thought that reads 18.0 dB passes, a thought that reads 17.99 dB is refused as under the floor to which the film holds every thought, and a declaration that names a thought to keep beside that margin is refused when it loads

#### Scenario: A film without a thought line

- **WHEN** a film declares no margin and its sound gate record lists thoughts under the floor
- **THEN** the gate reports that single thoughts are not judged and refuses nothing for them

### Requirement: The sound gate takes the owner's hearing of the selected take

`check-sound` SHALL refuse nothing for the clarity of a thought whose selected take, the take the selection bound for it, the owner's hearing settles for its clarity. It SHALL name each thought it refuses for its clarity for the ear, with its reading, its line and its selected take's audio SHA-256.

#### Scenario: A thought heard clear on its selected take

- **WHEN** the floor is 18 dB, the margin 0, a thought reads 17.4 dB, and the film records the owner's hearing that settles the clarity of the thought's selected take
- **THEN** the gate refuses nothing for that thought

#### Scenario: A thought heard clear on another take

- **WHEN** the film's record of hearing names another take of that thought than the selected one
- **THEN** the gate refuses, naming the thought for the ear with its reading, the line and its selected take's audio SHA-256

### Requirement: The sound gate holds each cue to the edition's reading rate

`check-sound` SHALL refuse each caption cue of the edition's current timeline that reads above the edition's reading rate unless the film declares the cue's shown text for that edition with a reason, and SHALL refuse a declared cue that no cue above the rate matches.

#### Scenario: An undeclared fast cue

- **WHEN** an English cue of 33 characters is shown for 1.2 s and the film declares no cue
- **THEN** the gate names the cue's text, its 27.5 characters per second and the declaration that would keep it

#### Scenario: A declared fast cue

- **WHEN** the film declares that cue's text for the English edition with a reason
- **THEN** the gate reports the caption rate current

#### Scenario: A cue that no longer reads fast

- **WHEN** a declared cue's text no longer reads above the rate, or is declared for an edition without a reading rate
- **THEN** the gate refuses the declaration as stale
