## Purpose

Package each edition's films so that their tracks, chapters and tags describe that edition.

## ADDED Requirements

### Requirement: Every track of a delivered film carries the edition's language

The picture, narration and chapter tracks of every delivered film SHALL carry the edition's ISO 639-2 language, and packaging SHALL refuse a finished film any of whose tracks carries another before it links the film into place.

#### Scenario: A Chinese film's chapter track

- **WHEN** the Chinese edition is packaged
- **THEN** its picture, narration and chapter tracks are each tagged `zho`

#### Scenario: A track in another language

- **WHEN** the chapter track of a finished Chinese film is tagged `eng`
- **THEN** packaging refuses the film and does not link it into place
