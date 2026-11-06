# concept-contract Specification

## Purpose

Keep every concept a film names faithful to its canonical source: one approved rendering per edition, said wherever a segment declares the concept, and no rejected rendering anywhere a viewer meets words.

## Requirements

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

No counterexample of any concept SHALL appear in an edition's narration, segment titles, chapter titles, caption terms, player prose or release synopsis, comment and description, or in a text file of the film's picture sources. Every occurrence SHALL be named with its location, and all occurrences SHALL be reported together.

#### Scenario: A rejected rendering in the narration

- **WHEN** a Chinese segment's narration contains a counterexample of a concept
- **THEN** the check refuses and names the segment, the counterexample and its position

#### Scenario: A rejected rendering in a picture label

- **WHEN** a picture source file contains a counterexample
- **THEN** the check refuses and names the file and the line

#### Scenario: A rejected rendering in the player's description

- **WHEN** the visible prose of an edition's player names a counterexample
- **THEN** the check refuses and names the edition's player and the counterexample

#### Scenario: A rejected rendering in the release synopsis

- **WHEN** an edition's release synopsis names a counterexample
- **THEN** the check refuses and names the edition's synopsis and the counterexample

#### Scenario: Markup the player does not show

- **WHEN** a counterexample stands only in the player's script or style element
- **THEN** the check does not refuse it as player prose

### Requirement: Narration refuses a script that departs from its contract

Narration SHALL run the concept check before any speech model loads and SHALL refuse when it refuses.

#### Scenario: Narrating a departed script

- **WHEN** narration is requested, with or without a dry run, for a film whose concept check refuses
- **THEN** narration stops before synthesis and reports the check's refusals

### Requirement: Reviewers read the contract

The reviewer prompt context SHALL name the film's concept contract and the readings occurrence plan, so a film's prompt can direct reviewers to score narration against them. For a film that declares a concept contract, a review round SHALL refuse to write its prompts unless the prompt template cites the contract and the occurrence plans and the scored dimensions include concept fidelity, and SHALL name each omission before it writes anything.

#### Scenario: Prompts for a film with a contract

- **WHEN** a review round writes its prompts for a film that declares a concept contract
- **THEN** each prompt's context names the contract's path and the occurrence plan's path

#### Scenario: A review configuration that leaves out the declared contract

- **WHEN** a film declares a concept contract and its prompt template never cites the contract or the occurrence plans, or its dimensions omit `concept_fidelity`
- **THEN** the round refuses before it writes a prompt and names each omission

#### Scenario: A film without a contract

- **WHEN** a film declares no concept contract
- **THEN** the round requires neither the contract's field nor the concept fidelity dimension

### Requirement: A Latin-script term's number is carried in Chinese

A Latin-script word keeps its base form in Chinese. Where the English counterpart of a Chinese thought uses such a word only in its plural, the Chinese clause holding it SHALL hold a number word, or the concept check SHALL refuse before narration, naming the edition, thought, word, plural and clause. A film MAY declare more number words, and exceptions with a reason.

#### Scenario: A plural heard as one

- **WHEN** a Chinese thought says 可以互相替换的 Agent and its English counterpart says "interchangeable Agents"
- **THEN** the check refuses and names the thought, Agent, Agents and the clause

#### Scenario: A number carried by Chinese words

- **WHEN** the Chinese clause says 越来越多的 Agent, 两个 Agent or 那些可以互相替换的 Agent
- **THEN** the check passes it

#### Scenario: A declared generic use

- **WHEN** the film declares 运行 Agent 的应用 in a thought as a generic use, with its reason
- **THEN** the check passes it and a declaration that names no current occurrence is refused as stale
