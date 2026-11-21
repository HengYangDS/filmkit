## ADDED Requirements

### Requirement: The chapter metadata keeps every character of its values

The chapter metadata that packaging reads SHALL escape, in the film's title, its comment and each chapter title, every
mark the metadata format reads as its own syntax (`=`, `;`, `#`, the backslash and a newline), so that the packaged
film's tags and chapter track read each value as the display copy sets it.

#### Scenario: A title with a backslash

- **WHEN** a chapter is titled a\b
- **THEN** the chapter metadata writes a\\b and the films' chapter track reads a\b

#### Scenario: A comment with a semicolon

- **WHEN** the release comment holds a semicolon
- **THEN** the chapter metadata writes it escaped and the films' comment tag reads the semicolon, with the same bytes
  as before the escape
