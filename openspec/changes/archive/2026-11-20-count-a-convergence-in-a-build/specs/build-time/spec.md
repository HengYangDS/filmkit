## ADDED Requirements

### Requirement: A convergence records how long it took

`filmkit.narration.converge` SHALL write the duration record `converge` when it ends, with the seconds of its narrations, its judgments, its candidates and its count of the runtime as phases. The record SHALL say that the command completed only where the edition ends settled and is not refused. A convergence refused before its first effect SHALL write none.

#### Scenario: A convergence of two narrations

- **WHEN** a convergence narrates, judges, generates a round of candidates, narrates again and judges again
- **THEN** its record `converge` states its seconds and the phases `narration`, `judgment` and `candidates`, the first holding both narrations

#### Scenario: An edition left unsettled

- **WHEN** a convergence ends with a thought unsettled
- **THEN** its record says that the command did not complete

#### Scenario: A convergence refused before its first effect

- **WHEN** a convergence is refused for a declaration it cannot read, or for a request an earlier run left started, while a `converge` record stands from the run that narrated
- **THEN** no duration record is written and the standing one holds its bytes

### Requirement: A build counts the convergence that narrated it

Where an edition's latest whole narration started within the run of a convergence, the build SHALL start at that convergence's record `converge`. Where the convergence completed, the sum SHALL count it and list the narration as inside it without adding its seconds again. Where it did not complete, the sum SHALL leave the convergence out and count the narration.

#### Scenario: A converged edition

- **WHEN** a convergence of 343 s ran two narrations, the last of 41 s, and a render of 200 s followed
- **THEN** the build's sum holds 543 s, the narration's record is listed as inside the convergence, and the sum's line says that the build began at the convergence

#### Scenario: A convergence that did not complete

- **WHEN** a convergence of 343 s ran a narration of 41 s and ended with its edition missing the runtime, and a render of 200 s followed
- **THEN** the convergence is listed as not completed and left out, and the build's sum holds 241 s: the narration and the render

#### Scenario: A narration after an earlier convergence

- **WHEN** an edition converged in an earlier build and is now narrated whole without a convergence
- **THEN** the build starts at that narration, and the earlier convergence's record is listed as earlier and left out

## MODIFIED Requirements

### Requirement: A build starts at its whole narration's record

An edition's build SHALL start at its duration record named `narrate`, which only a narration of the whole edition that generates writes, or as "A build counts the convergence that narrated it" states. A narration of chosen segments SHALL be recorded as `narrate-<ids>` and a check-only narration as `narrate-checks`, with the ids after it when given; neither SHALL replace the whole narration's record or move the build's start. A build narrated otherwise SHALL name its start with `--since`.

#### Scenario: A check-only narration within a build

- **WHEN** an edition is narrated whole and rendered, and `narrate --skip-generation` then runs
- **THEN** the check-only run is recorded as `narrate-checks`, the record `narrate` stands byte for byte, and the build's sum still counts the narration and the render

#### Scenario: Checks of chosen segments

- **WHEN** `narrate --skip-generation --ids 06,07` runs
- **THEN** its record is `narrate-checks-06-07`

#### Scenario: A build narrated by the synthesis command

- **WHEN** a build's segments are narrated by `filmkit.narration.synthesis --ids`, which writes no duration record, and checked by `narrate --skip-generation`
- **THEN** the build wrote no `narrate` record, and its durations are printed with `--since` naming its start
