# review-rounds Specification

## Purpose

Prepare each independent review round of a film's two editions: set the packages of the previous build aside before the next render, and write each edition's reviewer prompt.

## Requirements

### Requirement: A first production review gets its prompts

`filmkit.review.round prompts` SHALL write each edition's prompt without a previous round, its `{previous_review}` stating that no earlier production review exists and citing no previous review. With a previous round, `{previous_review}` SHALL cite that round's review files and findings. A template that cites `{previous}` or `{findings}` SHALL be filled only from a previous round and refused without one, before any prompt is written.

#### Scenario: A film's first production review

- **WHEN** a round's prompts are written without `--previous` from a template that cites `{previous_review}`
- **THEN** each prompt states that no earlier production review exists and names no previous review file

#### Scenario: A later round

- **WHEN** the prompts are written with `--previous` naming the round before
- **THEN** `{previous_review}` cites that round's review files with their findings and asks the reviewer to verify each repair

#### Scenario: A template that cites the previous review itself

- **WHEN** a template cites `{previous}` and `{findings}` and no previous round is named
- **THEN** the command refuses, naming both fields and `{previous_review}`, and writes no prompt
- **AND** with `--previous` the same template is filled as before

### Requirement: An unreviewed build is set aside by its consumer's copies

`set-aside --unreviewed --consumer <dir>` SHALL move each edition's films, package record and rendered picture into `build/artifacts/film/superseded/<label>/<code>/` with the manifest, move and readback of a reviewed round, labelled `round-<n>` or by `--label`. Before anything moves it SHALL refuse unless `<dir>/<code>/` holds both films byte-identical, and it SHALL record that folder as their consumer.

#### Scenario: A preview the owner watched

- **WHEN** an unreviewed build whose films the preview folder holds byte-identical is set aside with that folder as its consumer
- **THEN** each edition's members move below the label's folder and are read back by their hashes, and each manifest names the edition's preview folder as the consumer

#### Scenario: A copy that differs

- **WHEN** one edition's copy in the consumer folder differs from its film
- **THEN** the set-aside refuses, naming the copy and the film, and moves nothing

### Requirement: A set-aside moves the editions and pictures it names

A set-aside, reviewed or not, SHALL move only the edition that `--language` names when it names one, and SHALL leave the rendered picture in place for each edition that `--without-picture` names, or for every edition when it names none.

#### Scenario: One edition rebuilt

- **WHEN** an unreviewed build is set aside with `--language en --without-picture en`
- **THEN** only the English films and package record move, and the English picture and the whole Chinese edition stay in place

#### Scenario: Every picture kept

- **WHEN** a reviewed round is set aside with `--without-picture` and no edition
- **THEN** each edition's films and package record move and both pictures stay
