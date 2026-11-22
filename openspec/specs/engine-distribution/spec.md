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

Each release SHALL state, in the repository's README, the folder layout the engine reads, the declaration's fields, the npm packages a film declares, and the host tools a build needs. The npm packages a film declares SHALL be the ones the engine's own npm manifest names as the packages it runs, each at that manifest's version; the README SHALL name the manifest as the versions' one source and restate none.

#### Scenario: A new film follows the README

- **WHEN** a film is laid out and declared as the README states, with the stated npm packages and host tools installed
- **THEN** the engine loads it without refusal

#### Scenario: A package the engine runs takes another version

- **WHEN** the engine's manifest names another version of a package it runs in a film
- **THEN** the engine's record and its renderer state that version once the record is written again, and no sentence of the README changes

### Requirement: The engine carries a record of what it was released on

The installed engine SHALL carry a record of the version and integrity of each npm package it runs in a film and of the version of every Python package its own dependencies resolved to at the release. The renderer SHALL take the canvas's version and integrity from that record. The repository's fix task SHALL write the record from the manifest and the locks, and its checks SHALL refuse a record that differs from them.

#### Scenario: The record differs from the locks

- **WHEN** the repository's lock holds another version or integrity of a package than the record the engine carries
- **THEN** the repository's checks refuse it

#### Scenario: The engine's own tools stay out of the record

- **WHEN** the record is written
- **THEN** it holds no package that only the repository's tests or formatter use, and not the engine itself

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

### Requirement: One command lists what a release asks of a film

The engine SHALL provide one command that reads a film's tracked files only and reports every finding in one run, before the film has installed its npm packages, supplied, narrated or staged anything. The command SHALL exit with a failure while a finding stands, SHALL run on a film whose declaration does not load, and SHALL report a file it cannot read as a finding.

#### Scenario: A film adopts a release

- **WHEN** a film that still holds a renamed declaration key, an npm package the engine no longer runs in place of one it does, an older indirect Python package, a task that names a renamed module and a template that loads another script runs the command
- **THEN** one run reports a finding of each, and the command exits with a failure

#### Scenario: A film that holds what the release asks

- **WHEN** the command runs on the sample film
- **THEN** it reports no finding and exits successfully

#### Scenario: A file that cannot be read

- **WHEN** the film's npm manifest, a lock, its Mise configuration or its declaration is not text the command can parse, or holds a list or a word where the command reads a table
- **THEN** the question that reads it reports the file, and the other questions are answered

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

### Requirement: The command reads a film's tasks

The command SHALL report each engine module that a Mise task's text names and this engine lacks, each `filmkit.produce` command that names no action of this engine, and tasks that render a picture while none asks readiness. It SHALL judge neither the order of commands nor their editions. A `filmkit.produce` command that holds a variable outside its options and names no action by a word SHALL be named as not compared and be no finding, and readiness SHALL then not be judged.

#### Scenario: A renamed module

- **WHEN** a task of the film runs an engine module that this engine does not have
- **THEN** the command reports the task and the module

#### Scenario: An action the engine does not have

- **WHEN** a task asks `filmkit.produce` for an action this engine does not have
- **THEN** the command reports the task and the words the command names

#### Scenario: Renders without readiness

- **WHEN** the film's tasks render a picture and no task asks readiness
- **THEN** the command reports that the tasks render and none asks readiness

#### Scenario: Readiness asked anywhere

- **WHEN** one task asks readiness for one edition and another task renders both editions' pictures
- **THEN** the command reports no finding for the tasks

#### Scenario: An action named by a variable

- **WHEN** a task names the action of a `filmkit.produce` command by a shell variable or a task argument
- **THEN** the command reports no finding for it, says under what it did not read that the task was not compared, and reports no tasks that render without readiness

#### Scenario: An edition named by a variable

- **WHEN** every task that renders names its edition by a variable beside the action's word, and no task asks readiness
- **THEN** the command reports that the tasks render and none asks readiness

#### Scenario: A command written over two lines

- **WHEN** a task's command ends a line with a backslash and names its module or its action on the next
- **THEN** the command reads it as one command

#### Scenario: Tasks that no Mise configuration holds

- **WHEN** a film has no Mise configuration at or above its root
- **THEN** the command says its tasks were not read and reports no finding for them

### Requirement: The command reads a film's picture template

The command SHALL report each text of the picture template that staging would refuse, all in one run, and every script or stylesheet the template names beside the two that staging inlines.

#### Scenario: Two template faults

- **WHEN** the template holds one of staging's texts twice and lacks another
- **THEN** one run reports both

#### Scenario: A second naming of the inlined stylesheet

- **WHEN** the template names the stylesheet staging inlines once more, in a tag that is not the one staging replaces
- **THEN** the command reports it as a source staging does not inline

### Requirement: The engine's Node tests are found by their name

The engine's Node test script SHALL run every file under `tests/` whose name ends in `.test.mjs`, found by a pattern,
and SHALL name no test file by hand.

#### Scenario: A new test file

- **WHEN** a file `tests/picture/new.test.mjs` is added
- **THEN** the Node test script runs it with no other change
