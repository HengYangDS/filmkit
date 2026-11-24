## ADDED Requirements

### Requirement: A release is recorded only on records that verify

Recording a release SHALL run `filmkit verify` before it stages an asset or writes the manifest, a dry run included, and SHALL refuse with each of its lines when it refuses. A node that is only stale SHALL refuse nothing here.

#### Scenario: A soundtrack changed by no declared writer

- **WHEN** an edition's soundtrack is changed after the record of `assemble` by a command that is no declared writer of it, and the release is recorded
- **THEN** recording refuses, naming the soundtrack and the node, and no asset or manifest is written

#### Scenario: Both editions wrote the entry page

- **WHEN** the release is recorded after both editions' `package-metadata` replaced the entry page
- **THEN** recording proceeds as it does today
