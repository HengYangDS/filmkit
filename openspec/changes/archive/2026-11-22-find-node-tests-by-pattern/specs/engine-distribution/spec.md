## ADDED Requirements

### Requirement: The engine's Node tests are found by their name

The engine's Node test script SHALL run every file under `tests/` whose name ends in `.test.mjs`, found by a pattern,
and SHALL name no test file by hand.

#### Scenario: A new test file

- **WHEN** a file `tests/picture/new.test.mjs` is added
- **THEN** the Node test script runs it with no other change
