## Purpose

Keep every concept a film names faithful to its canonical source: one approved rendering per edition, said wherever a segment declares the concept, and no rejected rendering anywhere a viewer meets words.

## ADDED Requirements

### Requirement: A film may declare a concept contract

A film MAY name a concept contract in its declaration. The engine SHALL refuse a contract that is malformed, that repeats a concept id, or whose concept cites a document the source manifest does not pin, naming each failing entry. Each concept SHALL carry its source term, its essence, its source passage, and for each edition one approved rendering, the forms the narration may use and the counterexamples to refuse.

#### Scenario: A malformed contract is refused

- **WHEN** a concept lacks a rendering for an edition, or two concepts share an id
- **THEN** the check refuses and names each failing entry

#### Scenario: A concept cites an unpinned document

- **WHEN** a concept's source path is not a document of the source manifest
- **THEN** the check refuses and names the concept and the path

#### Scenario: A film without a contract

- **WHEN** the film declaration names no concept contract
- **THEN** the check reports that no contract is declared, and narration proceeds as before

### Requirement: Quotations match the pinned source

When a local clone of the source repository is named, each concept's quotation SHALL be found in its document at the pinned commit, both compared as plain text: Markdown emphasis and code marks are ignored and runs of whitespace count as one space.

#### Scenario: A quotation that the document no longer holds

- **WHEN** a quotation is not found in its document at the pinned commit
- **THEN** the check refuses and names the concept and the document

#### Scenario: No local clone

- **WHEN** no local clone is named
- **THEN** the check reports the quotations as not checked and still checks the scripts and the picture

### Requirement: Segments name their concepts by the approved renderings

A script segment MAY declare the concepts it states. Each declared concept SHALL exist in the contract; the same segment SHALL declare the same concepts in both editions; and each declared concept SHALL appear in that segment's narration by its edition's rendering or one of its forms, as a substring in Chinese and as a whole-word phrase, ignoring case, in English.

#### Scenario: An undeclared or unknown concept

- **WHEN** a segment declares an id the contract does not hold
- **THEN** the check refuses and names the segment and the id

#### Scenario: Editions that declare different concepts

- **WHEN** one segment declares different concepts in its two editions
- **THEN** the check refuses and names the segment and the concepts that differ

#### Scenario: A declared concept said in other words

- **WHEN** a segment declares a concept whose rendering and forms do not appear in its narration
- **THEN** the check refuses and names the segment, the edition and the concept

### Requirement: Counterexamples are refused wherever a viewer meets words

No counterexample of any concept SHALL appear in an edition's narration, segment titles, chapter titles or caption terms, or in a text file of the film's picture sources. Every occurrence SHALL be named with its location, and all occurrences SHALL be reported together.

#### Scenario: A rejected rendering in the narration

- **WHEN** a Chinese segment's narration contains a counterexample of a concept
- **THEN** the check refuses and names the segment, the counterexample and its position

#### Scenario: A rejected rendering in a picture label

- **WHEN** a picture source file contains a counterexample
- **THEN** the check refuses and names the file and the line

### Requirement: Narration refuses a script that departs from its contract

Narration SHALL run the concept check before any speech model loads and SHALL refuse when it refuses.

#### Scenario: Narrating a departed script

- **WHEN** narration is requested, with or without a dry run, for a film whose concept check refuses
- **THEN** narration stops before synthesis and reports the check's refusals

### Requirement: Reviewers read the contract

The reviewer prompt context SHALL name the film's concept contract and the readings occurrence plan, so a film's prompt can direct reviewers to score narration against them.

#### Scenario: Prompts for a film with a contract

- **WHEN** a review round writes its prompts for a film that declares a concept contract
- **THEN** each prompt's context names the contract's path and the occurrence plan's path
