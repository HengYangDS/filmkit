## ADDED Requirements

### Requirement: A round is prepared only on records that verify

A round's preparation SHALL run `filmkit verify` before it writes anything, and SHALL refuse with each of its lines when it refuses. A node that is only stale SHALL refuse nothing here.

#### Scenario: A package changed by no declared writer

- **WHEN** an edition's 1080p captioned film is changed after its `package-film` record by a command that is no declared writer of it, and a round is prepared
- **THEN** the preparation refuses, naming that film and the node, and writes no prompt

#### Scenario: A round after a repair

- **WHEN** a round is prepared after `repair-pictures` rendered a picture again and `package-film` ran on it
- **THEN** the preparation proceeds as it does today
