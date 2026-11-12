## ADDED Requirements

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
