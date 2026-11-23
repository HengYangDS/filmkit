## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: A round carries the register report

A round's preparation SHALL write the register check's report of every edition into the round and SHALL fill the template's `{register}` field with the report's path and the rules R1 to R6 as the `formal-register` capability states them. A template that does not cite `{register}` SHALL be refused before anything is written, naming the field.

#### Scenario: A prepared round

- **WHEN** a round is prepared
- **THEN** it holds the register report, with each warning's place and form and each exception applied with its text and its reason, and each prompt names it with the rules and names no part of the report that the report does not hold

#### Scenario: A template without the field

- **WHEN** a film's prompt template does not cite `{register}`
- **THEN** the preparation refuses before it writes anything and names the field
