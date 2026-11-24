## ADDED Requirements

### Requirement: A language declares how a transcript's Latin-script words are heard

Each language's declaration SHALL state how a transcript's Latin-script words are heard, by their letters or by CMUdict's pronunciations; the engine SHALL refuse a declaration that states another way or none when it loads, naming the language and the field.

#### Scenario: How a language hears a transcript's Latin-script words

- **WHEN** the engine's tests declare `xb` with English's values, and its take's text holds "labelled" where the transcript holds "labeled"
- **THEN** the take differs by no unit by reading, as an English take does, and in `xa`, declared with Chinese's values, it differs by one

#### Scenario: A declaration that states no way of hearing them

- **WHEN** a language declaration names no way of hearing a transcript's Latin-script words, or one the engine does not hold
- **THEN** the engine refuses it when it loads, naming the language and the field
