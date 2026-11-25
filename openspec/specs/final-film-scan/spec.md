# final-film-scan Specification

## Purpose

Hold every edition to the engine's own measure of still pictures under speech, read on the film a viewer watches: one command scans the packaged film into a record, and neither the delivery's verification nor the delivery passes an edition without that record.

## Requirements

### Requirement: One command scans an edition's packaged film

`scan-film` SHALL scan the edition's 1080p captioned film against the edition's timeline by the still scan's rules at both phases and write the edition's film record: the film, the timeline and the composition with their SHA-256, the engine's version, the rules it was written under and the frames each phase read. It SHALL refuse a film that holds a still run with 3.5 s of speech or more, after writing the record, naming each such run's time and speech.

#### Scenario: A film that keeps moving

- **WHEN** `scan-film --language zh` runs on a packaged edition whose longest still run carries 2.9 s of speech
- **THEN** `build/evidence/editions/zh/film-stills.json` names the 1080p captioned film, the Chinese timeline and the composition with their SHA-256, the engine's version, the scan's rules and each phase's frames, and the command exits 0

#### Scenario: A film that stands still under speech

- **WHEN** the film holds a still run from 842.7 to 847.4 s with 3.86 s of speech
- **THEN** the record lists the run and the command refuses, naming 842.70-847.40 s, 3.86 s of speech and the record

#### Scenario: Speech just under the limit

- **WHEN** the film's longest still run carries 3.496 s of speech
- **THEN** the record states 3.49 s, speech being cut to whole hundredths and not rounded, and the command exits 0

#### Scenario: A film that cannot be read

- **WHEN** FFmpeg reads no frame of the film
- **THEN** the command refuses, naming the failure, and the edition holds no film record, an earlier one included

#### Scenario: An input that the scan cannot read

- **WHEN** ffprobe states no frame rate that is a positive whole multiple of the scan's, the decode fails after some frames, or the timeline's words or its duration cannot be read
- **THEN** the command refuses, naming the film or the timeline, with no error of its own, and no record answers for the edition

#### Scenario: A film that changes while it is scanned

- **WHEN** the film or the timeline is replaced between the start of the decode and its end
- **THEN** the command refuses, naming both files, and the edition holds no film record

#### Scenario: A film that does not decode to its length

- **WHEN** a phase reads other frames than the seconds the timeline states, at the scan's rate
- **THEN** the command refuses, naming the frames read and the frames of the timeline's seconds, and the edition holds no film record

#### Scenario: A film that is not there

- **WHEN** the edition's 1080p captioned film, its timeline or the composition is missing
- **THEN** the command refuses, naming the missing file, and decodes nothing

### Requirement: A film record answers only for the film and the rules that stand

A film record SHALL answer for an edition only when it has every field the scan writes, of the scan's type, binds the film, the timeline, the composition and the engine as they stand, states the engine's own rules, its limit among them, read in each phase the frames of the timeline's seconds, and agrees with itself wherever it states one thing twice. Every reader of a film record SHALL read it by this one rule, SHALL say which part fails and SHALL end with no error of its own.

#### Scenario: A record cut short

- **WHEN** a film record holds half its bytes, a value of another type where the scan writes an object, or a body nested deeper than a reader follows, or lacks a field the scan writes
- **THEN** no reader ends with an error of its own: the record is named as one that cannot be read, with `scan-film`

#### Scenario: A run that no scan of the film could list

- **WHEN** a film record lists a run that ends after the film or before it starts, that carries more speech than its length, or whose figure is no finite number
- **THEN** the record is named as one that cannot be read, with `scan-film`, however its other statements agree

#### Scenario: A record of another film

- **WHEN** the edition's films were packaged again after the scan
- **THEN** the record is named as binding another movie, with `scan-film`

#### Scenario: A record written under another limit

- **WHEN** a record at the film record's place states a limit of 99 s, or of 2.5 s
- **THEN** it is named as stating other rules than the engine's, with that limit, the engine's 3.5 s and `scan-film`, whatever runs it lists

#### Scenario: Rules that change under one version

- **WHEN** a constant of the scan, a filter of its decode or the cut of a run's speech changes and the engine's version does not
- **THEN** a record written under the earlier rules does not answer

#### Scenario: A record whose runs a hand emptied

- **WHEN** the list of still runs of a refused film's record is emptied and its list of the runs at the limit still names the run
- **THEN** the record is named as one that cannot be trusted, with the statements that disagree and `scan-film`

#### Scenario: A record that states a rule twice, differently

- **WHEN** a film record's rate, its limit, a rule's wording or the number of its phases differs from what its rules state, or its frames from the frames of its phases
- **THEN** the record is named as one that cannot be trusted, with the statement that disagrees and `scan-film`

### Requirement: An unchanged film is not decoded twice

`scan-film` SHALL answer from the edition's film record, without decoding the film, when that record answers for the film as it stands, and SHALL then give the verdict the record holds. It SHALL scan again whenever the record does not answer, a damaged record included, so that the command a refusal names repairs any record. Its printed line and its run record's settings SHALL say whether the film was decoded.

#### Scenario: A build's package task run again

- **WHEN** `scan-film` runs a second time and nothing the record binds has changed
- **THEN** no frame is decoded, the line printed says `"scanned": false` with the first run's longest speech, and the exit status is the first run's

#### Scenario: A film packaged again

- **WHEN** the film, the timeline or the composition changed after the scan, or another engine version wrote the record
- **THEN** `scan-film` decodes the film and writes a record that binds what stands

#### Scenario: A damaged record

- **WHEN** the film record cannot be read or contradicts itself
- **THEN** `scan-film` decodes the film and writes a whole record, and gives the film's verdict

### Requirement: The delivery's verification requires the film's passing scan

The verifier SHALL, in both its scopes, refuse an edition whose film record does not answer for the film as it stands, saying why and naming `scan-film`, or whose film record lists a still run with 3.5 s of speech or more, naming each such run's time and speech. Its report SHALL state the film, its longest still run's speech and the limit.

#### Scenario: An edition that was never scanned

- **WHEN** the verifier runs with `--technical-only` on an edition whose build ran no `scan-film`
- **THEN** it refuses the edition as having no still scan record and names `scan-film`

#### Scenario: A still run in the record

- **WHEN** the film record lists a run from 842.7 to 847.4 s with 3.86 s of speech
- **THEN** the verifier refuses the edition, naming 842.70-847.40 s and 3.86 s of speech

#### Scenario: An edition that passed

- **WHEN** the film record answers and its longest run carries 3.49 s of speech
- **THEN** the verifier's report states the film, 3.49 s and the limit of 3.5 s

### Requirement: Delivery copies no film without its passing scan

`filmkit deliver` SHALL ask the verifier's requirement of each edition's film record before it copies or removes anything at the destination, in a dry run too, and SHALL refuse with that requirement's own reason, so that no order of commands delivers a film the scan has not passed.

#### Scenario: Packaging and then delivery

- **WHEN** `package-film` ran for both editions, `scan-film` did not, and the delivery command runs
- **THEN** it refuses, naming the edition and `scan-film`, and the destination is unchanged

#### Scenario: The members of another folder

- **WHEN** the delivery is asked to copy the members of a folder that is not the film the command runs in
- **THEN** it refuses, naming both folders, since the scans it reads are that film's

### Requirement: A draft's still scan binds what it judged

The still scan SHALL record the film, the timeline and the composition it judged, each with its SHA-256, and given an edition SHALL judge that edition's draft against its timeline and write the edition's draft record, which SHALL name the renderer that drew the draft as the draft's receipt names it. A draft of another engine's renderer SHALL leave `render-draft` stale, as its run record binds the engine.

#### Scenario: An edition's draft

- **WHEN** the scan runs with `--language en` on a rendered draft
- **THEN** `build/evidence/editions/en/draft-stills.json` names the draft, the English timeline and the composition with their SHA-256, and the canvas package, version and text renderer that drew the draft

#### Scenario: A record from before a change

- **WHEN** the composition changes after the draft is scanned
- **THEN** the plan names `render-draft` stale for the composition and the edition's renders behind it

#### Scenario: A record of a browser's draft

- **WHEN** a film adopts this engine and keeps the draft record of a draft that a browser drew, which names no renderer
- **THEN** the plan names `render-draft` stale for the engine, and `filmkit build` renders the draft again

### Requirement: The node render-draft renders and scans an edition's draft

`render-draft` SHALL stage the edition's captioned picture afresh at 1920x1080 over the whole film, draw it at 10 fps in one process at niceness 10, or the caller's if higher, within its deadline, write a draft render receipt and scan the draft into the edition's draft record, which its run record binds. It SHALL refuse a render that does not complete, scanning nothing, a draft not read whole, and a draft with a still picture at the limit, after writing its record.

#### Scenario: A draft of the current picture

- **WHEN** `render-draft` runs for an edition whose stages, gate record, cover and source check are current
- **THEN** the draft record binds the new draft, the edition's current timeline and the composition, and its receipt names the draft's command and the draft
- **AND** the plan reports `render-draft` fresh

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

### Requirement: A draft's still scan settles nothing about the film

A draft record SHALL admit an edition's render and nothing after it: no command SHALL read a draft record in place of the edition's film record, which the capability `final-film-scan` requires. A draft is drawn at half the size the film's picture is drawn at, and its scan can end a still run that the film holds whole.

#### Scenario: A draft record beside no film record

- **WHEN** an edition of a film that declares drafts holds a passing draft record and no film record
- **THEN** the plan reports `render-draft` fresh, and the edition's film record is still required as `final-film-scan` states
