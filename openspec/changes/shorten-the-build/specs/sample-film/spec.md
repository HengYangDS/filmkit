## ADDED Requirements

### Requirement: The sample build qualifies the renderer

The sample film SHALL declare `software` capture, the capture under which pictures are derived. Its picture task SHALL render the Chinese captioned stage a second time with `qualify-renderer` and refuse unless the two renders pass the comparison of a rendered pair with no row left out, and SHALL render the Chinese uncaptioned picture with `--native` and compare that pair at every frame. A release of the engine requires this qualification to pass under `software` capture.

#### Scenario: Two renders of one stage

- **WHEN** `qualify-renderer` runs after the Chinese captioned picture is rendered and validated
- **THEN** its record names both renders' SHA-256 and frames and `software` capture, holds the comparison's report without a finding, and states how many frames decode identically, the first that does not, and the lowest PSNR of any frame with that frame

#### Scenario: A picture another browser drew

- **WHEN** `qualify-renderer` runs and the captioned picture's receipt names another browser than the one that runs now, or none
- **THEN** it refuses before it renders, naming both, and writes no record

#### Scenario: A pass over every frame that fails

- **WHEN** the pass that counts the frames that decode identically fails after the comparison has passed
- **THEN** the record holds the comparison's report and its verdict, and says why those facts were not measured

#### Scenario: The supply that ran

- **WHEN** `qualify-renderer` runs with a browser other than the build the engine pins
- **THEN** its record states the renderer's version as the film's packages install it, that browser's executable and SHA-256, and that it is not the pinned build

#### Scenario: Renders that differ by the encoder alone

- **WHEN** the second render differs from the first in every decoded frame, within the encoders' noise
- **THEN** `qualify-renderer` passes, and its record states that no frame decodes identically and the lowest PSNR of any frame, which one pass over both renders measured

#### Scenario: A one-frame fault in one render

- **WHEN** the second render holds a fragment for one frame that the first does not
- **THEN** `qualify-renderer` refuses, naming the frame, its time, its box and the render that holds it, and keeps the second render

#### Scenario: A difference that lasts, or another length

- **WHEN** the renders differ beyond the encoders' noise for two frames or more, or hold different counts of frames
- **THEN** `qualify-renderer` refuses, naming the frames or both counts

### Requirement: The sample film prints its build's durations

The repository SHALL carry a task that prints the duration records of the sample film's build with each edition's sum and the time of the build.

#### Scenario: After a sample build

- **WHEN** the durations task runs after the sample film was built
- **THEN** it lists each edition's commands from narration to verification with their seconds, the geometry check and the cover check among them, and prints the time of the build

## MODIFIED Requirements

### Requirement: The sample film offers its captions on and off

The sample film's build SHALL make and validate each edition's picture with and without captions, the Chinese uncaptioned picture rendered and the English one derived, compare each pair, package the four films and read the players back with the captions turned off and on.

#### Scenario: The sample film's four films

- **WHEN** the sample film is built and its players are read back
- **THEN** each edition's comparison passes, its four films verify, and each player's captions control switches between its films
