# engine-distribution Specification

## Purpose

Let a film depend on one pinned engine release: a package built from a release tag that carries every tool the engine runs, and a README that states what the film must provide.

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

Each release SHALL state, in the repository's README, the folder layout the engine reads, the declaration's fields, the npm packages and renderer version a film declares, and the host tools a build needs.

#### Scenario: A new film follows the README

- **WHEN** a film is laid out and declared as the README states, with the stated npm packages and host tools installed
- **THEN** the engine loads it without refusal
