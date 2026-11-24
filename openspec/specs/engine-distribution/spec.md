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

The command SHALL report each text of the picture template that staging would refuse, all in one run, a language anchor other than `<html lang="und">` among them, and every script or stylesheet the template names beside the two that staging inlines.

#### Scenario: Two template faults

- **WHEN** the template holds one of staging's texts twice and lacks another
- **THEN** one run reports both

#### Scenario: A second naming of the inlined stylesheet

- **WHEN** the template names the stylesheet staging inlines once more, in a tag that is not the one staging replaces
- **THEN** the command reports it as a source staging does not inline

#### Scenario: A template whose anchor is a language's tag

- **WHEN** the template opens with `<html lang="zh-CN">`
- **THEN** the command names it with the anchor `<html lang="und">` that staging replaces

### Requirement: The engine's Node tests are found by their name

The engine's Node test script SHALL run every file under `tests/` whose name ends in `.test.mjs`, found by a pattern,
and SHALL name no test file by hand.

#### Scenario: A new test file

- **WHEN** a file `tests/picture/new.test.mjs` is added
- **THEN** the Node test script runs it with no other change

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

### Requirement: The command reads what a film states of its runtime and credits

The command SHALL report each line of the review prompt that cites the runtime's field without saying "This edition", with what to do instead, by the question `runtime`. Each script that declares `duration` or `credits_duration`, each cast that declares `runtime_fit` and a declaration without `credits_duration` SHALL be reported once, by the declaration's question, as the loader refuses them, each in one line that says what to do instead.

#### Scenario: A film that has not adopted the release

- **WHEN** both scripts declare `duration` and `credits_duration`, a cast declares `runtime_fit` and the review prompt says "Each edition: exactly {duration} s"
- **THEN** one run names each key with its file and what to do instead, by `declaration`, and the prompt's line with its number and the wording to use, by `runtime`, and the command exits with a failure

#### Scenario: A declaration without the credits

- **WHEN** the declaration states no `credits_duration`
- **THEN** the command names it once, in one line that says to declare the credits' length there

#### Scenario: A prompt line that cites the runtime in other words

- **WHEN** a line of the review prompt cites the runtime's field, with a format or without one, and does not say "This edition"
- **THEN** the command names the line, whatever else it says, and a line that only escapes the field's braces is not named

#### Scenario: A film that holds what the release asks

- **WHEN** no script or cast declares a withdrawn key, the declaration states its credits and every line of the review prompt that cites the runtime says "This edition"
- **THEN** the question reports no finding

#### Scenario: A script that has not moved

- **WHEN** the declaration still states `sources = "content"` for its Chinese edition and `content/film-script.json` declares `duration`
- **THEN** the question `declaration` names `content/film-script.json` and `duration` beside `editions.zh.sources`, and the question `runtime` names neither

### Requirement: The command reports the loader's refusals once

The question `declaration` SHALL report every refusal of the loader, each withdrawn key and each misplaced, missing or retired source among them, each once and with what to write instead; no other question SHALL name a fact that the loader refuses.

#### Scenario: Restated keys

- **WHEN** both scripts declare `language` at their tops and in a segment, and the English cast declares `language`, `provider` and `reference_text_sha256`
- **THEN** the question `declaration` names each key with its file, and its segment where it stands in one, and what to do instead, and no other question names them

#### Scenario: A declaration key

- **WHEN** the declaration still names `editions.zh.sources`
- **THEN** the question `declaration` names it, and no other question does

### Requirement: The command names every text the loader does not read that names an old place

Until the release that retires the command, the question `editions` SHALL name each line of a tracked text file whose facts no refusal of the loader owns, a film's Mise tasks, NOTICE and test loaders among them, that names a file this release moves or removes by its old path, with its file, its number and the new path. It SHALL name each file it cannot read, SHALL fail while a finding stands, and SHALL need no declaration that loads.

#### Scenario: Old paths in other files

- **WHEN** the film's NOTICE names `content/film-script.json`, a task's tool line names `assets/cover/ddwg-cover.png` and `tests/picture/page.mjs` names `content/film-script.json`
- **THEN** the question names each line with its file, its number and the new path, and the command exits with a failure

#### Scenario: The old paths it knows

- **WHEN** the declaration's `sources` and a cast's `reference_audio` are still stated, the Chinese cast's derivation cites `assets/audio/narration-reference.wav`, a line names `content/narration.md` and the NOTICE names the cited recording
- **THEN** the question takes as old paths those the withdrawn keys still state, the fixed names this release retires and each recording a cast's derivation cites, whose new path is `assets/audio/narrator-identity.wav`, and names both lines

#### Scenario: A copy that Git does not hold

- **WHEN** a copy of the film's tracked files stands in a folder that another repository ignores, or below which it tracks nothing
- **THEN** the question reads every file of the copy but its built output, packages and Git's records, and names each line it would name were the files tracked

#### Scenario: An old path that another finding owns

- **WHEN** the declaration still names `cover = "assets/cover/ddwg-cover.png"` and the Chinese cast names its reference by its old path
- **THEN** the declaration's line and the cast's key are each named once, by `declaration`, and the question `editions` names neither line

#### Scenario: A film that holds what the release asks

- **WHEN** no tracked text that the loader does not read names an old path
- **THEN** the question reports no finding

### Requirement: The command asks no edit of a film's history

A film's history and the record the engine writes of its release, its changelog, its archived OpenSpec changes and `content/release.json`, listed once in the command's module, SHALL hold no finding of the question `editions`: the command SHALL list each of their lines that names an old path under `history`, with its file, its number and the new path, and SHALL NOT fail for them, since a film keeps them as they stand.

#### Scenario: History and the release record

- **WHEN** `CHANGELOG.md`, a file below `openspec/changes/archive/` and `content/release.json` each name `content/film-script.json`, and no other text names an old path
- **THEN** the command lists each of their lines under `history` with its file, its number and the new path, the question `editions` reports no finding, and the command does not fail for them
