## ADDED Requirements

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
