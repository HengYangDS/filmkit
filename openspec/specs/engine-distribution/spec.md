# engine-distribution Specification

## Purpose

Let a film depend on one pinned engine release: a package built from a release tag that carries every tool the engine runs, and documentation, routed from the README, that states what the film must provide.

## Requirements

### Requirement: A film installs a pinned engine release

The engine SHALL be installable as a Python package from a release tag of its repository. The package's version SHALL come from the repository's `VERSION` alone, and the package SHALL contain every Node tool the engine runs.

#### Scenario: A film pins a release

- **WHEN** a film's Python project declares the engine at a release tag and locks it
- **THEN** the lock records the tag's commit, and the installed package reports the tag's version and contains each Node tool

#### Scenario: A version declared outside VERSION refuses

- **WHEN** the package metadata declares a version literal instead of reading `VERSION`
- **THEN** the repository's checks refuse it

### Requirement: The release states what a film must provide

Each release SHALL state in the repository's documentation the folder layout the engine reads, the declaration's fields, the npm packages a film declares and the host tools a build needs; the README SHALL route to those pages and state none of them. Those packages SHALL be the ones the engine's npm manifest names as those it runs, each at the manifest's version; the documentation SHALL name the manifest as their versions' one source and restate none.

#### Scenario: A new film follows the README

- **WHEN** a film follows the README's "How to start" routes to the pages on installing the engine in a film and on a film's layout, and is laid out and declared as they state, with the npm packages and host tools they state installed
- **THEN** the engine loads it without refusal

#### Scenario: A package the engine runs takes another version

- **WHEN** the engine's manifest names another version of a package it runs in a film
- **THEN** the engine's record and its renderer state that version once the record is written again, and no sentence of the documentation changes

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

### Requirement: An engine without its record is refused by the file and its command

When the engine holds no record it can read, or its record does not state both the version and the integrity of the canvas, it SHALL end in an error whose one line names the record's file and the command that writes it, `python -m filmkit.released`. A traceback MAY precede that line. That command SHALL run where no record stands.

#### Scenario: An engine without its record

- **WHEN** the engine holds no record and the renderer is loaded
- **THEN** the error's one line, the last a caller sees, names the record's file and `python -m filmkit.released`

#### Scenario: A record without the canvas

- **WHEN** the record holds no entry for the canvas and the renderer is loaded
- **THEN** the error's one line names the canvas, the record's file and the command

#### Scenario: A record that states half of the canvas

- **WHEN** the record states the canvas's version and not its integrity, or its integrity and not its version
- **THEN** the engine ends in the same error, whose one line names the canvas

#### Scenario: The command where no record stands

- **WHEN** `python -m filmkit.released` runs in the engine's repository and no record stands
- **THEN** it writes the record that the manifest and the locks state

### Requirement: The engine's Node tests are found by their name

The engine's Node test script SHALL run every file under `tests/` whose name ends in `.test.mjs`, found by a pattern,
and SHALL name no test file by hand.

#### Scenario: A new test file

- **WHEN** a file `tests/picture/new.test.mjs` is added
- **THEN** the Node test script runs it with no other change
