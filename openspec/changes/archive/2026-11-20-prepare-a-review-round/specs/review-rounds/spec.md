## ADDED Requirements

### Requirement: A round is prepared by one command

`review.round prepare` SHALL write a round's directory: the binding of the members a delivery would hold, the readback of their players with its screenshots, the listening plan, the measurements, each edition's sentences and prompt, and the changes note and dispositions it was given. It SHALL check what it reads before it derives anything, write the note and the dispositions first and the prompts last, and refuse a round's number below zero.

#### Scenario: A build that is ready

- **WHEN** round 19 is prepared with the previous round and a disposition of each of its findings
- **THEN** the round's directory holds the binding, the readback, the listening plan, the measurements, both editions' sentences and prompts, the changes note and the dispositions
- **AND** each prompt names its edition's four films with their SHA-256, and cites the round's directory for the round's inputs

#### Scenario: A refusal before anything is derived

- **WHEN** one film of an edition is missing
- **THEN** the command refuses, names the film, and the round's directory does not exist

#### Scenario: A dispositions file that is no JSON

- **WHEN** the dispositions file cannot be read as JSON
- **THEN** the command refuses in one line that names the file, and derives nothing

#### Scenario: A dispositions file in another encoding

- **WHEN** the dispositions file is JSON in UTF-16, or begins with a byte order mark
- **THEN** the command refuses in one line that names the file, and derives nothing

#### Scenario: A previous round without a report

- **WHEN** the previous round holds an edition's review and not its report
- **THEN** the command refuses in one line that names the report, and the round's directory does not exist

#### Scenario: A changes note that is no text

- **WHEN** the changes note cannot be read as UTF-8 text
- **THEN** the command refuses in one line that names the note, and the round's directory does not exist

#### Scenario: A template field the engine does not fill

- **WHEN** the film's template cites `{unknown_field}`
- **THEN** the command refuses in one line that names the field, and the round's directory does not exist

#### Scenario: Soundtracks at different program levels, or an edition without a timeline

- **WHEN** the editions' assemblies declare different program levels, or an edition of a film with levels has no timeline
- **THEN** the command refuses in one line, and the round's directory does not exist

#### Scenario: A round's number below zero

- **WHEN** round -1 is prepared
- **THEN** the command refuses in one line that states the number, and writes nothing

#### Scenario: A preparation that stops while it derives

- **WHEN** the measurement refuses an edition's records after the binding was written
- **THEN** the command refuses in one line as the measurement words it, and the round holds no prompt

### Requirement: A round is prepared again only as a preparation

A second preparation of a round SHALL replace every file of the first when the round holds nothing else, SHALL read what it was given before it removes anything, and SHALL write it back before it derives anything. `prepare` SHALL refuse, by name and without changing a file, a round that holds any entry it does not write, and a round whose label holds set-aside films, naming the next round's number.

#### Scenario: A corrected changes note

- **WHEN** a round was prepared, its changes note is corrected, the films stand as they were, and the round is prepared again
- **THEN** the prompts state the corrected note and no file of the first preparation remains

#### Scenario: A preparation run again without its note

- **WHEN** a round was prepared with a changes note and is prepared again without one
- **THEN** the round holds no changes note and the prompts state none

#### Scenario: A note read from the round itself

- **WHEN** the round's own copy of the changes note is corrected and named as the note of a second preparation
- **THEN** the prompts state the corrected note and the round holds it

#### Scenario: A second preparation that stops while it derives

- **WHEN** the round's own copies of the changes note and the dispositions are corrected and named as the sources of a second preparation, and the measurement refuses
- **THEN** the round holds both files with the bytes that were read, and no prompt

#### Scenario: A folder that bears a prepared file's name

- **WHEN** round 19 holds a folder named `prompt-zh.md` and is prepared again
- **THEN** the command refuses, names the entry, and every file of the round holds the bytes it held

#### Scenario: An image the readback does not list

- **WHEN** round 19 holds an image beside a readback that does not list it among its screenshots, and is prepared again
- **THEN** the command refuses, names the image, and every file of the round holds the bytes it held

#### Scenario: A listed file that holds other bytes

- **WHEN** round 19's readback lists as a screenshot a file of the round whose SHA-256 is not the listed one, an image changed since or a review listed by hand, and the round is prepared again
- **THEN** the command refuses, names the file, and every file of the round holds the bytes it held

#### Scenario: A listed folder

- **WHEN** round 19's readback lists as a screenshot a folder of the round, and the round is prepared again
- **THEN** the command refuses, names the folder, and removes nothing

#### Scenario: A reviewed round

- **WHEN** round 19 holds `review-zh.json` and is prepared again
- **THEN** the command refuses, names the review, and every file of the round holds the bytes it held

#### Scenario: A round whose films were set aside

- **WHEN** the films of round 19 were set aside under its label, the films were rebuilt, and round 19 is prepared
- **THEN** the command refuses and names round 20

### Requirement: A round holds the readback of its own members

A round SHALL hold the player check's receipt, with the screenshots it names, for exactly the members it binds, read in a real browser from the build's members. Its preparation SHALL be refused when a page fails, naming the page and its problems.

#### Scenario: A passing readback

- **WHEN** a round is prepared and every player passes
- **THEN** the round's readback records a verdict for each page, its binding lists the members that were read with their SHA-256, and each screenshot the readback names is a file of the round

#### Scenario: A player that fails

- **WHEN** an edition's player links a file the members do not hold
- **THEN** the preparation refuses, names the page and the link, and the round holds no prompt

#### Scenario: A readback that stops

- **WHEN** a readback's read throws, meets its deadline or is asked to end by SIGTERM after it wrote a player's screenshot
- **THEN** its receipt lists that screenshot with its SHA-256, so that the next preparation replaces it; a check that SIGTERM ended names the signal in its receipt and ends by it

#### Scenario: A check that is interrupted

- **WHEN** the player check is interrupted (SIGINT) after it wrote a player's screenshot
- **THEN** the browser's driver kills its browser and ends the check with status 130; no receipt is written, the round holds an image no receipt lists, and the next preparation refuses and names it

#### Scenario: A signal before the read begins

- **WHEN** the player check is asked to end by a signal before its read begins, while it reads the binding or launches the browser
- **THEN** it writes no receipt; no player has been read, so the round holds no image and is prepared again

#### Scenario: A check that is killed outright

- **WHEN** the host kills the player check after it wrote a player's screenshot and before it wrote its receipt
- **THEN** the round holds an image no receipt lists, and the next preparation refuses and names it

#### Scenario: Screenshots an earlier check left

- **WHEN** a check runs beside both screenshots of an earlier check and its reads stop before their screenshots
- **THEN** its receipt lists no screenshot and the folder holds none

### Requirement: A round's measurement reads the sync report its picture gate judged

The review's measurement SHALL take an edition's sound-picture sync from the sync report that the edition's picture gate record binds. It SHALL refuse a record that is not bound to the current composition and timeline and a report that differs from the one the record binds. A missing record, a record that binds no sync report and a missing report SHALL each be refused in one line that names `check-picture`.

#### Scenario: A gated edition

- **WHEN** an edition's picture gate has run on the current composition and timeline, and no separate sync record exists
- **THEN** the measurement states the edition's sync summary, findings and continuity from the gate's report

#### Scenario: A timeline that moved after the gate

- **WHEN** the edition's timeline changed after its picture gate ran
- **THEN** the measurement refuses and says that the gate record is not bound to the current timeline

#### Scenario: An edition that was never gated

- **WHEN** an edition has no picture gate record
- **THEN** the measurement refuses in one line that names `check-picture`

#### Scenario: A report cleared from the gate's work folder

- **WHEN** the gate record binds a sync report and the report's file is gone
- **THEN** the measurement refuses in one line that names `check-picture`

### Requirement: The record derives a review's overall

`review.round record` SHALL record the mean of a review's scores, rounded to one decimal as the engine rounds, as its overall, and SHALL neither require nor compare an overall that the review states.

#### Scenario: A stated overall that rounds another way

- **WHEN** a review's twelve scores have the mean 99.25 and the review states an overall of 99.3
- **THEN** the review is recorded with the overall 99.2

#### Scenario: A review that states no overall

- **WHEN** a review gives its scores and no overall
- **THEN** the review is recorded with the derived overall

### Requirement: A film declares the severities a review may hold

A film MAY declare `[review] accepted_severities`, a list that does not hold `material`, however it is cased or padded, and names no severity twice; an empty list accepts no finding. For a film that declares the list, `review.round record` and the verifier SHALL refuse a review that holds a finding of any other severity or of none. A film that does not declare it SHALL keep the verdicts it has.

#### Scenario: A minor finding in a film that accepts notes

- **WHEN** a film declares `accepted_severities = ["note"]`, and a review scores every dimension at the floor or above and holds one minor finding
- **THEN** `review.round record` refuses and names the finding and its severity

#### Scenario: A severity nobody declared

- **WHEN** the same film's review holds a finding whose severity is `minro`
- **THEN** `review.round record` refuses and names the finding and its severity

#### Scenario: A film that does not declare the list

- **WHEN** a film without `accepted_severities` has a review above its floors that holds one minor finding
- **THEN** the review is recorded

#### Scenario: A material finding in a film without the list and without levels

- **WHEN** such a film's review holds one material finding
- **THEN** `review.round record` records it and the verifier refuses the record, as before

#### Scenario: A declaration that accepts material findings

- **WHEN** a film declares `accepted_severities = ["note", "material"]`
- **THEN** the declaration is refused and names `material`

#### Scenario: A declaration that names material in another case, or a severity twice

- **WHEN** a film declares `accepted_severities = ["Material"]`, or `["note", "note"]`
- **THEN** the declaration is refused

## MODIFIED Requirements

### Requirement: A first production review gets its prompts

A round's preparation SHALL write each edition's prompt without a previous round, its `{previous_review}` stating that no earlier production review exists and citing no previous review. With a previous round, `{previous_review}` SHALL cite that round's review files and findings. A template that cites `{previous}` or `{findings}` SHALL be filled only from a previous round and refused without one, before anything is written.

#### Scenario: A film's first production review

- **WHEN** a round is prepared without `--previous` from a template that cites `{previous_review}`
- **THEN** each prompt states that no earlier production review exists and names no previous review file

#### Scenario: A later round

- **WHEN** a round is prepared with `--previous` naming the round before
- **THEN** `{previous_review}` cites that round's review files with their findings and asks the reviewer to verify each repair

#### Scenario: A template that cites the previous review itself

- **WHEN** a template cites `{previous}` and `{findings}` and no previous round is named
- **THEN** the command refuses, naming both fields and `{previous_review}`, and writes no prompt
- **AND** with `--previous` the same template is filled as before

### Requirement: A round's prompts require a disposition of every previous finding

A round prepared with a previous round SHALL require `--dispositions <file>`. The file gives each finding of the previous round's reviews one disposition: fixed, with the evidence that its reverification holds; declared, with the design section that keeps it; or deferred, with its owner and reason. The command SHALL refuse a finding without a disposition, a disposition for a finding the previous round does not hold, and a disposition without its evidence or reason.

#### Scenario: A note left without a disposition

- **WHEN** the previous round holds 28 findings and the dispositions file names 27
- **THEN** the command refuses and names the finding without a disposition

### Requirement: The prompts state the levels

For a film that declares levels, a round's preparation SHALL fill `{levels}` with each level, what it asks and, under it, each of its dimensions with what that dimension asks, and SHALL refuse a template that does not cite `{levels}` and `{sentences}`. A film without levels SHALL keep its prompts.

#### Scenario: A film with levels

- **WHEN** the prompts are written for a film whose levels hold its five dimensions
- **THEN** each prompt states 信, 达 and 雅 with what each asks and each dimension under its level

#### Scenario: A template without the field

- **WHEN** a film declares levels and its template does not cite `{levels}`
- **THEN** the command refuses and writes no prompt

### Requirement: The prompts name every sentence a viewer hears

A round's preparation SHALL write, for each edition, every sentence of every thought, split at 。？！ in Chinese and . ? ! in English with quotations kept whole, each with its id `segment.thought.sentence`, its text and its start and end in the timeline, and SHALL name the file in `{sentences}`.

#### Scenario: A thought of two sentences

- **WHEN** thought 02.3 holds two sentences
- **THEN** the file lists 02.3.1 and 02.3.2 with their texts and the times of their first and last words

#### Scenario: A quoted sentence

- **WHEN** a sentence quotes “Done. All tests pass.”
- **THEN** the quotation stays in one sentence
