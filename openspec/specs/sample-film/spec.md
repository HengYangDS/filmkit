# sample-film Specification

## Purpose

Prove the engine end to end with a short bilingual film that the repository carries, builds and verifies, and that the engine's tests load instead of any production film.

## Requirements

### Requirement: The repository builds a sample film

The repository SHALL carry a short bilingual sample film whose tracked sources and declared supply let the engine build it end to end on Apple-silicon macOS, offline after the supply step, writing only below the sample's `build/` folder.

#### Scenario: The sample film builds and verifies

- **WHEN** the supply step and then the sample's build run on Apple silicon
- **THEN** both editions' recordings, soundtracks, captions, pictures and packaged films are produced below the sample's `build/`
- **AND** the technical verification of both editions passes

### Requirement: The engine's tests load only the sample film

The engine's tests SHALL load the sample film as the film the engine builds, and no test SHALL read another film's sources.

#### Scenario: The suites run without another film

- **WHEN** the engine's Python and Node suites run in a checkout of this repository alone
- **THEN** every test that loads a film loads the sample film, and the suites pass

### Requirement: The sample film meets the owner's text and review bars

The sample film's text SHALL line up as the frame audit measures it, and its review configuration SHALL hold the overall score and every dimension at 95 or more.

#### Scenario: The sample's picture passes the text-layout measures

- **WHEN** `check-picture` audits either edition of the sample film
- **THEN** the frame audit reports no text-layout finding, and the closing checklist's items share one left edge beside their checks

#### Scenario: The sample's review floors

- **WHEN** the sample film's review configuration is read
- **THEN** its overall and dimension minimums are 95

### Requirement: The sample film's review holds three levels

The sample film SHALL declare `[review.levels]` holding each of its review dimensions in one of 信, 达 and 雅, and its prompt SHALL cite `{levels}` and `{sentences}`.

#### Scenario: The sample's review configuration

- **WHEN** the sample film's declaration and prompt are read
- **THEN** its five dimensions stand in the three levels and its prompts state the levels and name the sentences file
