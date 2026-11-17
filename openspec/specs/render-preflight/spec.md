# render-preflight Specification

## Purpose

Report, before an expensive render, every input of the render and of the packaging after it that is stale or missing, by the owners that would refuse it later.

## Requirements

### Requirement: A pre-render check names every stale or missing input

`produce preflight` SHALL report at once, and refuse while any remains: a stage of either picture that is not its current UHD picture; a tracked cover other than the cover the current stage paints; an earlier film package record of the edition; a failing concept check; a picture gate record that has not passed on the current inputs; and, for a film that declares drafts, a draft still scan that is missing, finds a still picture over its limit or binds another timeline or composition.

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

### Requirement: The pre-render check asks for the sound gate and the geometry record

`produce preflight` SHALL refuse an edition whose sound gate record is missing, did not pass or binds another soundtrack, timeline or engine version, and one whose geometry record the delivery's verification would refuse: a record that is missing, did not pass or is not of the whole current staged film.

#### Scenario: Captions refreshed after the sound gate

- **WHEN** the timeline changed after `check-sound` passed
- **THEN** the check names the sound gate record as bound to another timeline and `check-sound` as the step to run again

#### Scenario: A geometry record of an earlier stage

- **WHEN** the staged document changed after the geometry check passed, or the check sampled fewer frames than the verification accepts
- **THEN** the check names the geometry record and the geometry check as the step to run on the stage

### Requirement: A film declares the cues it keeps above the reading rate

`produce preflight` SHALL refuse each caption cue of the edition's current timeline that reads above the edition's reading rate unless the film declares the cue's shown text for that edition with a reason, and SHALL refuse a declared cue that no cue above the rate matches.

#### Scenario: An undeclared fast cue

- **WHEN** an English cue of 33 characters is shown for 1.2 s and the film declares no cue
- **THEN** the check names the cue's text, its 27.5 characters per second and the declaration that would keep it

#### Scenario: A declared fast cue

- **WHEN** the film declares that cue's text for the English edition with a reason
- **THEN** the check reports the caption rate current

#### Scenario: A cue that no longer reads fast

- **WHEN** a declared cue's text no longer reads above the rate, or is declared for an edition without a reading rate
- **THEN** the check refuses the declaration as stale

### Requirement: A film declares the line a single thought's clarity is judged against

A film MAY declare a margin of zero or more under its clarity floor. `produce preflight` SHALL then refuse a thought that the sound gate record reads under the floor less that margin, a thought between that line and the floor that the film does not declare by name with a reason, and a declared thought that does not read under the floor. With a margin of zero no thought MAY be declared. Without a margin it SHALL report that single thoughts are not judged.

#### Scenario: A thought under the thought line

- **WHEN** the floor is 18 dB, the margin 1.0 dB and a thought reads 16.9 dB
- **THEN** the check refuses, naming the thought, its reading and the line of 17.0 dB, whether or not the thought is declared

#### Scenario: A thought between the two lines

- **WHEN** a thought reads 17.62 dB and the film declares it with a reason
- **THEN** the check refuses nothing for it; undeclared, the check names it and the declaration that would keep it

#### Scenario: A declared thought that reads at the floor again

- **WHEN** a declared thought reads 18.4 dB after a retake
- **THEN** the check refuses the declaration as stale

#### Scenario: A margin of zero

- **WHEN** the floor is 18 dB and the margin 0
- **THEN** a thought that reads 18.0 dB passes, a thought that reads 17.99 dB is refused as under the floor to which the film holds every thought, and a declaration that names a thought to keep beside that margin is refused when it loads

#### Scenario: A film without a thought line

- **WHEN** a film declares no margin and its sound gate record lists thoughts under the floor
- **THEN** the check reports that single thoughts are not judged and refuses nothing for them
