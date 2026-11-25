## MODIFIED Requirements

### Requirement: A bound build is set aside before it is rebuilt

Assembling a soundtrack, and refreshing an edition's captions, SHALL refuse while a review round's prompts bind the edition's current films and that round has not been set aside. The refusal SHALL name the round and the set-aside command.

#### Scenario: Assembling over a reviewed build

- **WHEN** round 7's prompts bind the edition's current films and round 7 has not been set aside
- **THEN** assembly refuses before it writes anything and names round 7 and `filmkit review set-aside --round 7`

#### Scenario: A set-aside round

- **WHEN** the round that bound the edition's films has been set aside
- **THEN** assembly proceeds

### Requirement: A review passes level by level

For a film that declares levels, each review SHALL give every level a verdict, pass or fail, with the findings in it, and each finding SHALL name its level. `filmkit review record` and the verifier SHALL refuse a review that misses a level, whose level fails, or whose level passes while a dimension it holds is below the floor or a material finding remains in it, besides today's floors.

#### Scenario: A level passed by averaging

- **WHEN** the overall score is 96 but a dimension of 雅 scores 93 and the review passes 雅
- **THEN** `filmkit review record` refuses and names 雅 and the dimension

#### Scenario: A level that fails

- **WHEN** a review fails 达
- **THEN** the record is refused and the verifier refuses a record that holds it

#### Scenario: A finding without its level

- **WHEN** a finding names no level
- **THEN** the record is refused and names the finding

### Requirement: A review judges every sentence

For a film that declares levels, each review SHALL give every sentence id of its edition a verdict, `ok` or the ids of the findings that concern it. `filmkit review record` and the verifier SHALL refuse a review that misses a sentence, names an unknown one or names a finding the review does not hold.

#### Scenario: A sentence left out

- **WHEN** a review gives verdicts for all but sentence 05.2.1
- **THEN** `filmkit review record` refuses and names 05.2.1

### Requirement: The record derives a review's overall

`filmkit review record` SHALL record the mean of a review's scores, rounded to one decimal as the engine rounds, as its overall, and SHALL neither require nor compare an overall that the review states.

#### Scenario: A stated overall that rounds another way

- **WHEN** a review's twelve scores have the mean 99.25 and the review states an overall of 99.3
- **THEN** the review is recorded with the overall 99.2

#### Scenario: A review that states no overall

- **WHEN** a review gives its scores and no overall
- **THEN** the review is recorded with the derived overall

### Requirement: A film declares the severities a review may hold

A film MAY declare `[review] accepted_severities`, a list that does not hold `material`, however it is cased or padded, and names no severity twice; an empty list accepts no finding. For a film that declares the list, `filmkit review record` and the verifier SHALL refuse a review that holds a finding of any other severity or of none. A film that does not declare it SHALL keep the verdicts it has.

#### Scenario: A minor finding in a film that accepts notes

- **WHEN** a film declares `accepted_severities = ["note"]`, and a review scores every dimension at the floor or above and holds one minor finding
- **THEN** `filmkit review record` refuses and names the finding and its severity

#### Scenario: A severity nobody declared

- **WHEN** the same film's review holds a finding whose severity is `minro`
- **THEN** `filmkit review record` refuses and names the finding and its severity

#### Scenario: A film that does not declare the list

- **WHEN** a film without `accepted_severities` has a review above its floors that holds one minor finding
- **THEN** the review is recorded

#### Scenario: A material finding in a film without the list and without levels

- **WHEN** such a film's review holds one material finding
- **THEN** `filmkit review record` records it and the verifier refuses the record, as before

#### Scenario: A declaration that accepts material findings

- **WHEN** a film declares `accepted_severities = ["note", "material"]`
- **THEN** the declaration is refused and names `material`

#### Scenario: A declaration that names material in another case, or a severity twice

- **WHEN** a film declares `accepted_severities = ["Material"]`, or `["note", "note"]`
- **THEN** the declaration is refused

### Requirement: A round is prepared only for films that passed the still scan

`filmkit review prepare` SHALL ask, among the checks that only read and before it derives or writes anything, that each edition's film record meets what the delivery's verification requires of it, and SHALL refuse in one line with that requirement's own reason, so that no round reviews a film the verifier would refuse for a still picture.

#### Scenario: An edition that was never scanned

- **WHEN** a round is prepared and the Chinese edition has no film record
- **THEN** the command refuses, naming the edition and `scan-film`, and the round's directory does not exist

#### Scenario: A film that stands still under speech

- **WHEN** the English edition's film record lists a still run with 3.5 s of speech or more
- **THEN** the command refuses, naming the run's time and speech, derives nothing and writes neither edition's prompt

### Requirement: A round is prepared by one command

`filmkit review prepare` SHALL write a round's directory: the register report, the binding of the members a delivery would hold, the readback of their players with its screenshots, the listening plan, the measurements, each edition's sentences and prompt, and the changes note and dispositions it was given. It SHALL check what it reads before it derives anything, write the note and the dispositions first, the register report next and the prompts last, and refuse a round's number below zero.

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

### Requirement: A round is prepared only on records that verify

A round's preparation SHALL run `filmkit verify` before it writes anything, and SHALL refuse with each of its lines when it refuses. A node that is stale, behind or without a record SHALL refuse it too.

#### Scenario: A package changed by no declared writer

- **WHEN** an edition's 1080p captioned film is changed after its `package-film` record by a command that is no declared writer of it, and a round is prepared
- **THEN** the preparation refuses, naming that film and the node, and writes no prompt

#### Scenario: A round after a repair

- **WHEN** a round is prepared after `repair-pictures` rendered a picture again and `package-film` ran on it
- **THEN** the preparation proceeds as it does today
