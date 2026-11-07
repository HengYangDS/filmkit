## ADDED Requirements

### Requirement: The sample film offers its captions on and off

The sample film's build SHALL stage, render and validate each edition's picture with and without captions, compare the two, package the four films and read the players back with the captions turned off and on.

#### Scenario: The sample film's four films

- **WHEN** the sample film is built and its players are read back
- **THEN** each edition's comparison passes, its four films verify, and each player's captions control switches between its films
