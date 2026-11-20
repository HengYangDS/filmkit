## ADDED Requirements

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
