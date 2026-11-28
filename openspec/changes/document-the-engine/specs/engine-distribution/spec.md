## MODIFIED Requirements

### Requirement: The release states what a film must provide

Each release SHALL state in the repository's documentation the folder layout the engine reads, the declaration's fields, the npm packages a film declares and the host tools a build needs; the README SHALL route to those pages and state none of them. Those packages SHALL be the ones the engine's npm manifest names as those it runs, each at the manifest's version; the documentation SHALL name the manifest as their versions' one source and restate none.

#### Scenario: A new film follows the README

- **WHEN** a film follows the README's "How to start" routes to the pages on installing the engine in a film and on a film's layout, and is laid out and declared as they state, with the npm packages and host tools they state installed
- **THEN** the engine loads it without refusal

#### Scenario: A package the engine runs takes another version

- **WHEN** the engine's manifest names another version of a package it runs in a film
- **THEN** the engine's record and its renderer state that version once the record is written again, and no sentence of the documentation changes
