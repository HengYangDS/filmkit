# edition-readiness Specification

## Purpose

Keep, with each pre-render check, a receipt of an edition's answers and of the inputs they were judged on, so that a later step learns whether the edition is still ready without repeating the check.

## Requirements

### Requirement: The pre-render check writes a readiness receipt

`produce preflight` SHALL write the edition's readiness receipt whether it passes or refuses: its verdict, each question's answer, the engine version, and the SHA-256 of the composition, the stylesheet, each declared font, the declaration and the film's entry page, which both editions share, and of the edition's script, cast, timeline, assembly record and soundtrack. A missing input SHALL refuse by name and leave a receipt without digests.

#### Scenario: A ready edition

- **WHEN** every question of the check answers current
- **THEN** `build/evidence/editions/<edition>/readiness.json` holds a passing verdict, each answer, the engine version and the ten digests

#### Scenario: A refused edition

- **WHEN** the check refuses a stale stage
- **THEN** the receipt holds a refused verdict and the stage's answer as the check printed it

#### Scenario: A missing cast

- **WHEN** the edition's cast file is missing
- **THEN** the check refuses, naming the file, and the receipt holds a refused verdict and no digests

### Requirement: Readiness is checked again without repeating the work

`produce admitted` SHALL run no audit and SHALL refuse unless the edition's receipt passed, was written by the running engine version and binds every input as it stands, and unless the other edition's receipt passed, was written by that version and binds the composition, the stylesheet, the fonts, the declaration and the film's entry page as they stand. A refusal SHALL name each receipt, the inputs that moved and the check to run again.

#### Scenario: Both editions ready

- **WHEN** both receipts passed and every input stands as bound
- **THEN** `admitted` reports the edition admitted and exits 0, having asked none of the check's questions again

#### Scenario: The other edition's timeline changed

- **WHEN** the English timeline changed after both receipts passed
- **THEN** the Chinese edition is still admitted, and the English edition is refused with its receipt, the timeline and `preflight --language en` named

#### Scenario: The composition changed

- **WHEN** the composition changed after both receipts passed
- **THEN** neither edition is admitted, and the refusal names both receipts and the composition

#### Scenario: Only one edition was checked

- **WHEN** the other edition has no receipt, or its receipt refused
- **THEN** the edition is refused, since a finding in either edition changes the composition both render

#### Scenario: A receipt of another engine version

- **WHEN** the edition's receipt names another engine version
- **THEN** `admitted` refuses and names the engine version among the inputs that moved

#### Scenario: An entry page changed after the check

- **WHEN** the film's entry page changes after both receipts passed
- **THEN** neither edition is admitted, and the refusal names both receipts and the entry page
