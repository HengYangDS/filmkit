# picture-gates Specification

## Purpose

Audit an edition's picture through all its speech, and keep a render from starting while a gated finding remains.

## Requirements

### Requirement: The frame audit measures balance and cover through speech

The frame audit SHALL measure, in every voiced frame it exercises, the box around every lit mark and legible name in the content band. It SHALL report per scene each run of 2 seconds or more of speech in which that box stands more than 12% of the frame's width or height off the content centre, or covers less than a tenth of the content band, with the run's start, end and worst value.

#### Scenario: A picture that stands off centre through a thought

- **WHEN** a scene's lit picture stands 13% above the content centre through 2.5 seconds of speech
- **THEN** the audit reports one off-centre run for that scene with its start, its end and its largest offset

#### Scenario: A brief excursion is not a run

- **WHEN** the lit picture stands 13% off for 1.5 seconds of speech and then returns within 12%
- **THEN** the audit reports no off-centre run

#### Scenario: Quiet does not count

- **WHEN** the lit picture covers less than a tenth of the band only while no one speaks
- **THEN** the audit reports no thin run

### Requirement: An edition's picture is checked before it renders

`check-picture` SHALL run the frame audit over every frame of the edition's timeline at one thirtieth of a second, the sync audit on that audit's trace and marks, and the motion audit at 30 frames per second, on the current composition and timeline. It SHALL write a gate record naming the composition's and the timeline's SHA-256, the engine version, each audit's report and every gated finding, and SHALL refuse when a gated finding exists.

#### Scenario: A clean picture passes

- **WHEN** no audit reports a gated finding
- **THEN** `check-picture` writes a passing record and exits 0

#### Scenario: A gated finding refuses

- **WHEN** the frame audit reports an overlap or an off-centre run
- **THEN** `check-picture` writes a refused record, names each gated finding and exits with a refusal

### Requirement: A render waits for a passing gate record

`render-picture` SHALL refuse an edition before it starts the renderer unless the edition's gate record passed and names the current composition's and timeline's SHA-256 and the running engine version.

#### Scenario: The composition changed after its check

- **WHEN** `picture/film.js` changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: An edition that was never checked

- **WHEN** the edition has no gate record
- **THEN** `render-picture` refuses before the renderer starts

### Requirement: The frame audit measures how text lines up

The frame audit SHALL measure the settled names and marks of the content band in every voiced frame it exercises, and SHALL report per scene each text-layout defect that lasts 1 second or more, with its start, its end, its texts and its measured offsets.

#### Scenario: A row of names on two baselines

- **WHEN** two names of one size stand side by side through 2 seconds of speech with baselines 6 px apart
- **THEN** the audit reports one ragged row for that scene with its start, its end, both texts and both baselines

#### Scenario: A passing misalignment is not reported

- **WHEN** the two names stand on different baselines for half a second and then share one
- **THEN** the audit reports no ragged row

#### Scenario: Lines and columns that do not line up

- **WHEN** the lines of one left-aligned block start 5 px apart, or a line's ink stands 4 px below the ink of the line above it
- **THEN** the audit reports a ragged column or crammed lines for that scene with the texts and the offsets

#### Scenario: Measures that rest on estimated widths

- **WHEN** like marks stand at uneven pitch under names at equal gaps, or a name comes within 3 px of a mark's stroke
- **THEN** the audit reports an uneven pitch or a touching mark, measured on the stroke's points rather than its bounding box

#### Scenario: A heading at the top of a tall card

- **WHEN** a name stands at the top of a card more than three of its lines tall
- **THEN** the audit reports no card-centre finding for it

### Requirement: The picture gate refuses text that does not line up

`check-picture` SHALL refuse the text-layout findings that rest on exact anchors, sizes and baselines, `ragged_rows`, `ragged_columns`, `crammed_lines` and `off_card_centre`, and SHALL record `uneven_pitch` and `touching_marks` in the gate record without refusing them.

#### Scenario: A ragged row refuses

- **WHEN** the frame audit reports a ragged row
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: An uneven pitch is recorded

- **WHEN** the frame audit reports an uneven pitch and no gated finding
- **THEN** `check-picture` writes a passing record that lists the uneven pitch
