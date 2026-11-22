## ADDED Requirements

### Requirement: A round carries the register report

A round's preparation SHALL write the register check's report of both editions into the round and SHALL fill the
template's `{register}` field with the report's path and the rules R1 to R6 as the `formal-register` capability states
them. A template that does not cite `{register}` SHALL be refused before anything is written, naming the field.

#### Scenario: A prepared round

- **WHEN** a round is prepared
- **THEN** it holds the register report, with each warning's place and form and each exception applied with its
  text and its reason, and each prompt names it with the rules

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

### Requirement: A template cites each field by its name alone

A round's preparation SHALL refuse, before it derives anything, a template that cites a field with a conversion or a
format specification, naming each such field as the template writes it: the engine fills a field with the text a
reviewer reads whole.

#### Scenario: A field cited with a conversion or a format specification

- **WHEN** the film's template cites `{register:.0}` or `{levels!r}`
- **THEN** the preparation refuses in one line that names each such field as the template writes it, and the round's
  directory does not exist

## MODIFIED Requirements

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

### Requirement: The prompts state the levels

For a film that declares levels, a round's preparation SHALL fill `{levels}` with each level, what it asks and, under it, each of its dimensions with what that dimension asks, and SHALL refuse a template that does not cite `{levels}` and `{sentences}`. A film without levels SHALL keep its prompts.

#### Scenario: A film with levels

- **WHEN** the prompts are written for a film whose levels hold its six dimensions
- **THEN** each prompt states 信, 达 and 雅 with what each asks and each dimension under its level

#### Scenario: A template without the field

- **WHEN** a film declares levels and its template does not cite `{levels}`
- **THEN** the command refuses and writes no prompt
