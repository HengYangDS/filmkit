# render-preflight Specification

## Purpose

Report, before an expensive render, every input of the render and of the packaging after it that is stale or missing, by the owners that would refuse it later.

## Requirements

### Requirement: A pre-render check names every stale or missing input

`produce preflight` SHALL report at once, and refuse while any remains: a stage of the captioned or the uncaptioned picture that is not its current UHD picture; a tracked cover other than the cover the current stage paints; an earlier film package record of the edition; a draft still scan that is missing, finds a still picture over its limit or binds another timeline or composition; a failing concept check; and a picture gate record that has not passed on the current inputs.

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

### Requirement: One command renders and scans an edition's draft

`produce render-draft` SHALL stage the edition's captioned picture afresh at 1920x1080 over the whole film, render it at 10 fps in draft quality at niceness 10, or the caller's if higher, within its deadline, write a draft render receipt and scan the draft into the edition's draft record, the record that the pre-render check reads. It SHALL refuse a render that does not complete, scanning nothing, and a draft whose scan finds a still picture over the limit, after writing its record.

#### Scenario: A draft of the current picture

- **WHEN** `render-draft` runs for an edition whose stages, gate record, cover and concepts are current and which has no package record
- **THEN** the draft record binds the new draft, the edition's current timeline and the composition, and its receipt names the draft's command and the draft
- **AND** `preflight` reports every input of the edition current

#### Scenario: The draft renders at a lower priority

- **WHEN** `render-draft` runs the renderer
- **THEN** the renderer runs at niceness 10, or the caller's if higher, with the frame rate 10, the draft quality and otherwise the settings of the edition's picture

#### Scenario: A stage left by an earlier draft

- **WHEN** the draft's stage holds a file that the current inputs do not stage, such as a font the declaration no longer names
- **THEN** `render-draft` stages afresh and the draft's stage holds only the declared members

#### Scenario: A render that does not complete

- **WHEN** the renderer exits with a status other than 0 or reaches the deadline
- **THEN** `render-draft` refuses, its receipt records the exit and the deadline, and the edition holds no draft record, an earlier one included

#### Scenario: A draft with a still picture

- **WHEN** the draft holds a still picture over 3.5 s of speech
- **THEN** the draft record lists it and `render-draft` refuses, naming its time and its speech
