## ADDED Requirements

### Requirement: The sample build scans its packaged films

The sample film's package task SHALL run `scan-film` for each edition after it packages that edition's films, so that the sample's verification reads a film record of each edition.

#### Scenario: The sample's package task

- **WHEN** the sample film's package task runs after both editions' pictures are rendered
- **THEN** `scan-film` writes each edition's film record with no still run at the limit, and the technical verification of both editions passes

#### Scenario: The sample's durations

- **WHEN** the durations task runs after the sample film was built
- **THEN** each edition's list holds `scan-film` between `package-film` and the verification, with its seconds
