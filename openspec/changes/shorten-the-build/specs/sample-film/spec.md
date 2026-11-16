## ADDED Requirements

### Requirement: The sample build qualifies the renderer

The sample film SHALL declare `software` capture, the capture under which pictures are derived. Its picture task SHALL render the Chinese captioned stage a second time with `qualify-renderer` and refuse unless every decoded frame equals the first render's, and SHALL render the Chinese uncaptioned picture with `--native` and compare that pair at every frame. A release of the engine requires this qualification to pass under `software` capture.

#### Scenario: Two renders of one stage

- **WHEN** `qualify-renderer` runs after the Chinese captioned picture is rendered and validated
- **THEN** its record names both renders' SHA-256, the frames compared and `software` capture, and says that every decoded frame is identical

#### Scenario: A render that differs

- **WHEN** the second render differs from the first at one decoded frame
- **THEN** `qualify-renderer` refuses, naming the first frame that differs

### Requirement: The sample film prints its build's durations

The repository SHALL carry a task that prints the duration records of the sample film's build with each edition's sum and the time of the build.

#### Scenario: After a sample build

- **WHEN** the durations task runs after the sample film was built
- **THEN** it lists each edition's commands from narration to verification with their seconds, the geometry check and the cover check among them, and prints the time of the build

## MODIFIED Requirements

### Requirement: The sample film offers its captions on and off

The sample film's build SHALL make and validate each edition's picture with and without captions, both captioned pictures rendered at the same time by one command, the Chinese uncaptioned picture rendered and the English one derived, compare each pair, package the four films and read the players back with the captions turned off and on.

#### Scenario: The sample film's four films

- **WHEN** the sample film is built and its players are read back
- **THEN** each edition's comparison passes, its four films verify, and each player's captions control switches between its films
