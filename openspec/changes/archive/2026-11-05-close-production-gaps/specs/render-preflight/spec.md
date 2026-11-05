## Purpose

Report, before an expensive render, every input of the render and of the packaging after it that is stale or missing, by the owners that would refuse it later.

## ADDED Requirements

### Requirement: A pre-render check names every stale or missing input

`produce preflight` SHALL report at once, and refuse while any remains: a stage that is not the current UHD picture; a tracked cover other than the cover the current stage paints; an earlier film package record of the edition; a draft still scan that is missing, finds a still picture over its limit or binds another timeline or composition; a failing concept check; and a picture gate record that has not passed on the current inputs.

#### Scenario: Every input current

- **WHEN** the stage, the gate record and the draft scan bind the current inputs, the cover equals its painting, no package record exists and the concept check passes
- **THEN** the check reports each input current and exits 0

#### Scenario: A composition changed after its checks

- **WHEN** the composition changed after its stage, its gate record and its draft scan, an earlier package record exists and the concept check fails
- **THEN** the check names the stage, the gate record, the draft scan, the package record and the concept failures in one refusal, and paints no cover

#### Scenario: A package of the current inputs

- **WHEN** an earlier package record binds every current input
- **THEN** the check names it, since the render replaces the picture it binds

#### Scenario: A cover the composition does not paint

- **WHEN** the tracked cover differs from the painting of the current stage
- **THEN** the check names the cover, the pixels that differ and the painting to track

### Requirement: A draft's still scan binds what it judged

The still scan SHALL record the film, the timeline and the composition it judged, each with its SHA-256, and given an edition SHALL judge that edition's draft against its timeline and write the edition's draft record.

#### Scenario: An edition's draft

- **WHEN** the scan runs with `--language en` on a rendered draft
- **THEN** `build/evidence/editions/en/draft-stills.json` names the draft, the English timeline and the composition with their SHA-256

#### Scenario: A record from before a change

- **WHEN** the composition changes after the draft is scanned
- **THEN** the pre-render check names the draft record as not bound to the current composition
