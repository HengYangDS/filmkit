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
