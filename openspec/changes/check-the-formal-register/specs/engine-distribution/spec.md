## MODIFIED Requirements

### Requirement: The engine carries a record of what it was released on

The installed engine SHALL carry a record of the version and integrity of each npm package it runs in a film and of the version of every Python package its own dependencies resolved to at the release, and the version of the register checker (Vale) its tool configuration pins. The renderer SHALL take the canvas's version and integrity from that record. The repository's fix task SHALL write the record from the manifest and the locks, and its checks SHALL refuse a record that differs from them.

#### Scenario: The record differs from the locks

- **WHEN** the repository's lock holds another version or integrity of a package than the record the engine carries
- **THEN** the repository's checks refuse it

#### Scenario: The engine's own tools stay out of the record

- **WHEN** the record is written
- **THEN** it holds no package that only the repository's tests or formatter use, and not the engine itself

#### Scenario: The register checker in the record

- **WHEN** the record is written
- **THEN** it states the Vale version the engine's tool configuration pins

### Requirement: The command compares a film's packages with the release

The command SHALL report each npm package the engine runs that the film's manifest does not declare at the release's version or that its lock does not hold at the release's version and integrity, a pin of another engine release, and each Python package of the engine's runtime that the film's lock holds at another version, with the constraints that close the difference. A package the film alone holds SHALL be no finding.

#### Scenario: An older indirect package

- **WHEN** a film's Python lock holds a package of the engine's runtime at an older version than the release's
- **THEN** the finding names the package with both versions and prints the constraint that holds it to the release's

#### Scenario: The film's own packages

- **WHEN** a film declares an npm package the engine does not run, or locks a Python package outside the engine's runtime at any version
- **THEN** the command reports no finding for it

#### Scenario: A lock that is missing

- **WHEN** a film holds no npm lock or no Python lock at or above its root
- **THEN** the command reports the missing lock as a finding

#### Scenario: A lock of another release

- **WHEN** a film pins this release and its Python lock still holds the engine at another version
- **THEN** the command reports the lock's version and says to lock again

#### Scenario: A film that pins another Vale or none

- **WHEN** a film's tool configuration pins a Vale version other than the release record's, or pins none
- **THEN** the command names the film's pin, or its absence, and the record's version
