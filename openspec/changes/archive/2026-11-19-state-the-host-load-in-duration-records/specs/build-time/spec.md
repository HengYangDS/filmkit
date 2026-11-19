## ADDED Requirements

### Requirement: A duration record states the host's load

Each duration record SHALL state the host's 1-minute load average at its command's start and at its end, each null on a host that states none. `python -m filmkit.durations` SHALL print a record's load beside its seconds, as one figure where both ends print alike, and after the build's time the lowest and highest load its counted commands state. A record that states no load SHALL print as it did. No check SHALL read the load and no record SHALL bind it.

#### Scenario: A command on a host that turns busy

- **WHEN** `package-film` starts at a 1-minute load of 6.52 and ends at 33.80
- **THEN** its duration record states `load_1m` with `start` 6.52 and `end` 33.8, and its line prints `load 6.5 to 33.8` after its seconds and before its phases

#### Scenario: A command that is refused

- **WHEN** a command that started at a load of 7.0 is refused at a load of 7.3
- **THEN** its record states both readings beside `completed` false, and its line prints the load after `not completed`

#### Scenario: Both ends alike

- **WHEN** a record states 10.18 at its start and 10.21 at its end
- **THEN** its line prints `load 10.2`

#### Scenario: A host that states no load average

- **WHEN** a command runs on a host without load averages, or one whose load average cannot be read
- **THEN** it writes its duration record with both readings null, completes as it would, and its line prints no load

#### Scenario: A record of an earlier engine

- **WHEN** an edition holds a duration record without `load_1m`
- **THEN** its line and the sum print as they did

#### Scenario: The range of a build

- **WHEN** a build's three counted commands state loads from 6.52 to 33.84, and a refused command and an earlier record state higher ones
- **THEN** the last line ends with the host's 1-minute load between 6.5 and 33.8 at their starts and ends

#### Scenario: Counted commands that state none

- **WHEN** two of a build's five counted commands state no load
- **THEN** the last line gives the range of the three that do and says that 2 of them state none

#### Scenario: A build without a stated load

- **WHEN** none of a build's counted commands states a load
- **THEN** the last line is as it was
