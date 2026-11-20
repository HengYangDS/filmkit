## ADDED Requirements

### Requirement: A draft's still scan settles nothing about the film

A draft record SHALL admit an edition's render and nothing after it: no command SHALL read a draft record in place of the edition's film record, which the capability `final-film-scan` requires. A draft is drawn at half the size the film's picture is drawn at, and its scan can end a still run that the film holds whole.

#### Scenario: A draft record beside no film record

- **WHEN** an edition of a film that declares drafts holds a passing draft record and no film record
- **THEN** the pre-render check reports the draft scan current, and the edition's film record is still required as `final-film-scan` states

## MODIFIED Requirements

### Requirement: A pre-render check names every stale or missing input

`produce preflight` SHALL report at once, and refuse while any remains: a stage of either picture that is not its current UHD picture; a tracked cover other than the cover the current stage paints; an earlier film package record of the edition; a failing concept check; a picture gate record that has not passed on the current inputs; and, for a film that declares drafts, a draft still scan that is missing, finds a still picture at the limit or does not answer as `final-film-scan` states.

#### Scenario: Every input current

- **WHEN** the stage, the gate records, the geometry record and the declared draft scan bind the current inputs, the cover equals its painting, no package record exists and the concept check passes
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

#### Scenario: A film that declares no drafts

- **WHEN** a film declares no drafts and holds no draft still scan
- **THEN** the check reports that the draft scan is not asked and refuses nothing for it

#### Scenario: A draft scanned with another limit

- **WHEN** a draft record written with a limit of 99 s lists a still run with 3.9 s of speech and nothing over its own limit
- **THEN** the check names the draft record as stating other rules than the engine's, with the record's limit and the engine's, and asks for a new draft scan

#### Scenario: A draft record that lists no runs

- **WHEN** a draft record lists its still runs in no form the scan writes, is cut short or lacks a field the scan writes
- **THEN** the check names the record as one that cannot be read and asks for a new draft scan, with no error of its own

#### Scenario: A draft record that contradicts itself

- **WHEN** a draft record's list of still runs is empty and its runs at the limit still name a run
- **THEN** the check names the record as one that cannot be trusted and asks for a new draft scan

#### Scenario: A draft record of an earlier engine

- **WHEN** a draft record states no rules and no frames of its phases, as an engine before this requirement wrote it
- **THEN** the check names it as one that cannot be read, and `render-draft` draws and scans the draft again

### Requirement: One command renders and scans an edition's draft

`produce render-draft` SHALL stage the edition's captioned picture afresh at 1920x1080 over the whole film, draw it at 10 fps in one process at niceness 10, or the caller's if higher, within its deadline, write a draft render receipt and scan the draft into the edition's draft record, the record that the pre-render check reads. It SHALL refuse a render that does not complete, scanning nothing, a draft not read whole, and a draft with a still picture at the limit, after writing its record.

#### Scenario: A draft of the current picture

- **WHEN** `render-draft` runs for an edition whose stages, gate record, cover and concepts are current and which has no package record
- **THEN** the draft record binds the new draft, the edition's current timeline and the composition, and its receipt names the draft's command and the draft
- **AND** `preflight` reports every input of the edition current

#### Scenario: The draft renders at a lower priority

- **WHEN** `render-draft` runs the renderer
- **THEN** the renderer runs at niceness 10, or the caller's if higher, with the frame rate 10, one span and otherwise the settings of the edition's picture

#### Scenario: A stage left by an earlier draft

- **WHEN** the draft's stage holds a file that the current inputs do not stage, such as a font the declaration no longer names
- **THEN** `render-draft` stages afresh and the draft's stage holds only the declared members

#### Scenario: A render that does not complete

- **WHEN** the renderer exits with a status other than 0 or reaches the deadline
- **THEN** `render-draft` refuses, its receipt records the exit and the deadline, and the edition holds no draft record, an earlier one included

#### Scenario: A draft with a still picture

- **WHEN** the draft holds a still picture with 3.5 s of speech or more
- **THEN** the draft record lists it and `render-draft` refuses, naming its time and its speech

#### Scenario: A draft whose decode ends early

- **WHEN** the draft decodes to fewer frames than its timeline's seconds give at the scan's rate
- **THEN** `render-draft` refuses, naming the frames read and the frames of the timeline's seconds, and the edition holds no draft record
