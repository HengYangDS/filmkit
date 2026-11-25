## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Delivery copies no film without its passing scan

`filmkit deliver` SHALL ask the verifier's requirement of each edition's film record before it copies or removes anything at the destination, in a dry run too, and SHALL refuse with that requirement's own reason, so that no order of commands delivers a film the scan has not passed.

#### Scenario: Packaging and then delivery

- **WHEN** `package-film` ran for both editions, `scan-film` did not, and the delivery command runs
- **THEN** it refuses, naming the edition and `scan-film`, and the destination is unchanged

#### Scenario: The members of another folder

- **WHEN** the delivery is asked to copy the members of a folder that is not the film the command runs in
- **THEN** it refuses, naming both folders, since the scans it reads are that film's
