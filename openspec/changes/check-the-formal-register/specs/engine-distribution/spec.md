## ADDED Requirements

### Requirement: The command reads a film's pin of the register checker

The command SHALL read the entry `github:vale-cli/vale` under `[tools]`, as one version, in the Mise configuration the film's tasks are read from, and no other entry or file for it. It SHALL report a file whose entry states another version than the release record's, and a file that holds no version under that name, each by the file's name with the record's version. A film without a Mise configuration SHALL be reported as having none.

#### Scenario: Another version

- **WHEN** the film's Mise configuration pins `github:vale-cli/vale` at another version than the release record's
- **THEN** the command names the file, the film's version and the record's

#### Scenario: A pin under another name or in another file

- **WHEN** a film pins Vale as `vale` or as another tool's entry, or in `mise.toml` beside the `.config/mise/config.toml` that holds its tasks
- **THEN** the command says that the file it read holds no version under `github:vale-cli/vale`, with the record's version and the entry to add, and does not say that the film pins none

#### Scenario: A film whose one Mise file bears another name

- **WHEN** a film's one Mise configuration is `mise.toml` or `.mise.toml` and pins the record's version there
- **THEN** the command reads the pin in that file and reports no finding

#### Scenario: No Mise configuration

- **WHEN** a film has no Mise configuration at or above its root
- **THEN** the command reports that the film has none, with the record's version and the entry to add

#### Scenario: Tools that are no table

- **WHEN** the file states `tools` as something other than a table
- **THEN** the question reports the file and the place, and the other questions are answered

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
