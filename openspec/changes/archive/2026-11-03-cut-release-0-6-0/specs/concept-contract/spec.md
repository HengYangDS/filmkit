# concept-contract Specification

## MODIFIED Requirements

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
