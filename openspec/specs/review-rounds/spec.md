# review-rounds Specification

## Purpose

Prepare each independent review round of a film's two editions: set the packages of the previous build aside before the next render, and write each edition's reviewer prompt.

## Requirements

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

### Requirement: An unreviewed build is set aside by its consumer's copies

`set-aside --unreviewed --consumer <dir>` SHALL move each edition's films, package record and rendered pictures into `build/artifacts/film/superseded/<label>/<code>/` with the manifest, move and readback of a reviewed round, labelled `round-<n>` or by `--label`. Before anything moves it SHALL refuse unless `<dir>/<code>/` holds each of the edition's films byte-identical, and it SHALL record that folder as their consumer.

#### Scenario: A preview the owner watched

- **WHEN** an unreviewed build whose films the preview folder holds byte-identical is set aside with that folder as its consumer
- **THEN** each edition's members move below the label's folder and are read back by their hashes, and each manifest names the edition's preview folder as the consumer

#### Scenario: A copy that differs

- **WHEN** one edition's copy in the consumer folder differs from its film
- **THEN** the set-aside refuses, naming the copy and the film, and moves nothing

### Requirement: A set-aside moves the editions and pictures it names

A set-aside, reviewed or not, SHALL move only the edition that `--language` names when it names one, and SHALL leave the rendered picture in place for each edition that `--without-picture` names, or for every edition when it names none.

#### Scenario: One edition rebuilt

- **WHEN** an unreviewed build is set aside with `--language en --without-picture en`
- **THEN** only the English films and package record move, and the English picture and the whole Chinese edition stay in place

#### Scenario: Every picture kept

- **WHEN** a reviewed round is set aside with `--without-picture` and no edition
- **THEN** each edition's films and package record move and both pictures stay

### Requirement: A round's prompts require a disposition of every previous finding

A round prepared with a previous round SHALL require `--dispositions <file>`. The file gives each finding of the previous round's reviews one disposition: fixed, with the evidence that its reverification holds; declared, with the design section that keeps it; or deferred, with its owner and reason. The command SHALL refuse a finding without a disposition, a disposition for a finding the previous round does not hold, and a disposition without its evidence or reason.

#### Scenario: A note left without a disposition

- **WHEN** the previous round holds 28 findings and the dispositions file names 27
- **THEN** the command refuses and names the finding without a disposition

### Requirement: The prompts state each disposition

The prompts SHALL state the dispositions in three groups, fixed, declared and deferred, so that the reviewers re-verify each fixed finding by its reverification line and judge the others.

#### Scenario: Every finding disposed

- **WHEN** each finding has a disposition with its evidence or reason
- **THEN** the prompts state the dispositions in their three groups

### Requirement: A bound build is set aside before it is rebuilt

Assembling a soundtrack, and refreshing an edition's captions, SHALL refuse while a review round's prompts bind the edition's current films and that round has not been set aside. The refusal SHALL name the round and the set-aside command.

#### Scenario: Assembling over a reviewed build

- **WHEN** round 7's prompts bind the edition's current films and round 7 has not been set aside
- **THEN** assembly refuses before it writes anything and names round 7 and `review.round set-aside --round 7`

#### Scenario: A set-aside round

- **WHEN** the round that bound the edition's films has been set aside
- **THEN** assembly proceeds

### Requirement: A film declares its review levels

A film MAY declare `[review.levels]` in `content/film.toml`: the three levels `信`, `达` and `雅`, each with what it asks of the whole film and the review dimensions it holds. The declaration SHALL be refused unless every declared dimension stands in exactly one level and every dimension a level names is declared.

#### Scenario: A dimension in no level

- **WHEN** the levels hold four of the film's five declared dimensions
- **THEN** the declaration is refused and names the dimension without a level

#### Scenario: An unknown dimension

- **WHEN** a level names a dimension the film does not declare
- **THEN** the declaration is refused and names that dimension

### Requirement: The prompts state the levels

For a film that declares levels, a round's preparation SHALL fill `{levels}` with each level, what it asks and, under it, each of its dimensions with what that dimension asks, and SHALL refuse a template that does not cite `{levels}` and `{sentences}`. A film without levels SHALL keep its prompts.

#### Scenario: A film with levels

- **WHEN** the prompts are written for a film whose levels hold its six dimensions
- **THEN** each prompt states 信, 达 and 雅 with what each asks and each dimension under its level

#### Scenario: A template without the field

- **WHEN** a film declares levels and its template does not cite `{levels}`
- **THEN** the command refuses and writes no prompt

### Requirement: A review passes level by level

For a film that declares levels, each review SHALL give every level a verdict, pass or fail, with the findings in it, and each finding SHALL name its level. `review.round record` and the verifier SHALL refuse a review that misses a level, whose level fails, or whose level passes while a dimension it holds is below the floor or a material finding remains in it, besides today's floors.

#### Scenario: A level passed by averaging

- **WHEN** the overall score is 96 but a dimension of 雅 scores 93 and the review passes 雅
- **THEN** `review.round record` refuses and names 雅 and the dimension

#### Scenario: A level that fails

- **WHEN** a review fails 达
- **THEN** the record is refused and the verifier refuses a record that holds it

#### Scenario: A finding without its level

- **WHEN** a finding names no level
- **THEN** the record is refused and names the finding

### Requirement: The prompts name every sentence a viewer hears

A round's preparation SHALL write, for each edition, every sentence of every thought, split at 。？！ in Chinese and . ? ! in English with quotations kept whole, each with its id `segment.thought.sentence`, its text and its start and end in the timeline, and SHALL name the file in `{sentences}`.

#### Scenario: A thought of two sentences

- **WHEN** thought 02.3 holds two sentences
- **THEN** the file lists 02.3.1 and 02.3.2 with their texts and the times of their first and last words

#### Scenario: A quoted sentence

- **WHEN** a sentence quotes “Done. All tests pass.”
- **THEN** the quotation stays in one sentence

### Requirement: A review judges every sentence

For a film that declares levels, each review SHALL give every sentence id of its edition a verdict, `ok` or the ids of the findings that concern it. `review.round record` and the verifier SHALL refuse a review that misses a sentence, names an unknown one or names a finding the review does not hold.

#### Scenario: A sentence left out

- **WHEN** a review gives verdicts for all but sentence 05.2.1
- **THEN** `review.round record` refuses and names 05.2.1

### Requirement: A set-aside moves the films its build made

A set-aside, reviewed or not, SHALL move each edition's films with captions, its films without captions and its uncaptioned picture when they are in place, its package record and, unless kept, its pictures, so a build packaged before the films without captions existed is set aside by its two films and its captioned picture, bound by the review or the consumer copies of those films.

#### Scenario: A round reviewed before 0.13.0

- **WHEN** a round whose reviews bind each edition's two films with captions is set aside
- **THEN** each edition's two films, package record and captioned picture move, and the set-aside names no missing film

### Requirement: A round is prepared by one command

`review.round prepare` SHALL write a round's directory: the register report, the binding of the members a delivery would hold, the readback of their players with its screenshots, the listening plan, the measurements, each edition's sentences and prompt, and the changes note and dispositions it was given. It SHALL check what it reads before it derives anything, write the note and the dispositions first, the register report next and the prompts last, and refuse a round's number below zero.

#### Scenario: A build that is ready

- **WHEN** round 19 is prepared with the previous round and a disposition of each of its findings
- **THEN** the round's directory holds the register report, the binding, the readback, the listening plan, the measurements, both editions' sentences and prompts, the changes note and the dispositions
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

### Requirement: A round is prepared only for films that passed the still scan

`review.round prepare` SHALL ask, among the checks that only read and before it derives or writes anything, that each edition's film record meets what the delivery's verification requires of it, and SHALL refuse in one line with that requirement's own reason, so that no round reviews a film the verifier would refuse for a still picture.

#### Scenario: An edition that was never scanned

- **WHEN** a round is prepared and the Chinese edition has no film record
- **THEN** the command refuses, naming the edition and `scan-film`, and the round's directory does not exist

#### Scenario: A film that stands still under speech

- **WHEN** the English edition's film record lists a still run with 3.5 s of speech or more
- **THEN** the command refuses, naming the run's time and speech, derives nothing and writes neither edition's prompt

### Requirement: A set-aside moves a film's still scan record with the film

A set-aside, reviewed or not, SHALL move an edition's film record with the edition's films when that record is in place, name it in the manifest with its hash and read it back as it does each member, whatever the record says: it is the films' scan record, and a set-aside asks no reader of it. An edition whose build holds no film record SHALL be set aside without one.

#### Scenario: A reviewed build with its record

- **WHEN** a round's films are set aside and the Chinese edition holds a film record
- **THEN** `film-stills.json` moves into the edition's set-aside folder with its films and package record, and the edition holds no film record until its next scan

#### Scenario: A build of an engine before the scan

- **WHEN** an edition holds no film record
- **THEN** its films, package record and pictures are set aside as before, and the set-aside names no missing record

### Requirement: A round carries the register report

A round's preparation SHALL write the register check's report of every edition into the round and SHALL fill the template's `{register}` field with the report's path and the rules R1 to R6 as the `formal-register` capability states them. A template that does not cite `{register}` SHALL be refused before anything is written, naming the field.

#### Scenario: A prepared round

- **WHEN** a round is prepared
- **THEN** it holds the register report, with each warning's place and form and each exception applied with its text and its reason, and each prompt names it with the rules and names no part of the report that the report does not hold

#### Scenario: A template without the field

- **WHEN** a film's prompt template does not cite `{register}`
- **THEN** the preparation refuses before it writes anything and names the field

### Requirement: A round is refused with the register check

A round's preparation SHALL ask the register check once, before it derives anything, and SHALL refuse the round in one
line, making no directory, when the check refuses the film's words or cannot run the Vale the release record states.

#### Scenario: Words the check refuses

- **WHEN** a round is prepared for a film whose words hold an error-level form that the film does not excuse
- **THEN** the preparation refuses in one line that names each place and form, and the round's directory does not exist

#### Scenario: No pinned Vale

- **WHEN** a round is prepared where no Vale is on the path
- **THEN** the preparation refuses in one line that names the version the check runs, and the round's directory does
  not exist

### Requirement: A template cites no field with a conversion or a format specification

A round's preparation SHALL refuse, before it derives anything, a template that cites a field with a conversion or a
format specification, naming each such field as the template writes it: the engine fills a field with the text a
reviewer reads whole.

#### Scenario: A field cited with a conversion or a format specification

- **WHEN** the film's template cites `{register:.0}` or `{levels!r}`
- **THEN** the preparation refuses in one line that names each such field as the template writes it, and the round's
  directory does not exist

### Requirement: Each prompt names its edition's files and every other edition by fields

A round's preparation SHALL fill `{editions}` with every edition's script, timeline and folder of delivered files, the prompt's own edition first and the others in the declared order; `{others}` with the other editions by name and code, or with the statement that there is none; and each policy and clarity field with every edition's value in the declared order. It SHALL fill `{other}` and `{other_language}` no longer.

#### Scenario: The Chinese prompt of a film of two editions

- **WHEN** a round is prepared for a film that declares Chinese, then English
- **THEN** the Chinese prompt's `{others}` reads "the English (en) edition", and its `{editions}` names the Chinese script and timeline first and the English ones after them

#### Scenario: A film of three editions

- **WHEN** the film declares Chinese, English and a third edition `xb`, in that order
- **THEN** the English prompt's `{others}` names the Chinese and the `xb` editions, in that order

#### Scenario: A film of one edition

- **WHEN** the film declares one edition
- **THEN** its prompt's `{others}` states that the film has no other edition

#### Scenario: A template of the former fields

- **WHEN** the template cites `{other}` or `{other_language}`
- **THEN** the engine refuses at load, before the preparation writes anything, and names `{others}`

### Requirement: A round is prepared only on records that verify

A round's preparation SHALL run `filmkit verify` before it writes anything, and SHALL refuse with each of its lines when it refuses. A node that is only stale SHALL refuse nothing here.

#### Scenario: A package changed by no declared writer

- **WHEN** an edition's 1080p captioned film is changed after its `package-film` record by a command that is no declared writer of it, and a round is prepared
- **THEN** the preparation refuses, naming that film and the node, and writes no prompt

#### Scenario: A round after a repair

- **WHEN** a round is prepared after `repair-pictures` rendered a picture again and `package-film` ran on it
- **THEN** the preparation proceeds as it does today
