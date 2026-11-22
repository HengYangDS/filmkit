## ADDED Requirements

### Requirement: The chapter metadata keeps every character of its values

The chapter metadata SHALL escape, in the film's title, its author, its comment and each chapter title, every mark the
metadata format reads as its own syntax (`=`, `;`, `#`, the backslash and a newline) and a carriage return, at which
FFmpeg ends a value too, so that FFmpeg reads each value from the file as the display copy sets it and a packaged
film's chapter track holds each chapter title whole.

#### Scenario: A title with a backslash

- **WHEN** a chapter is titled a\b
- **THEN** the chapter metadata writes a\\b and FFmpeg reads the chapter's title from it as a\b

#### Scenario: A comment with a semicolon

- **WHEN** the release comment holds a semicolon
- **THEN** the chapter metadata writes it escaped and FFmpeg reads the comment from it with its semicolon

#### Scenario: An author with a mark

- **WHEN** the scripts declare an author that holds one of the marks
- **THEN** the chapter metadata writes it escaped under both of its keys, and FFmpeg reads the author back as
  declared

#### Scenario: A carriage return

- **WHEN** a title, the author, the comment or a chapter title holds a carriage return
- **THEN** the chapter metadata writes a backslash before it and FFmpeg reads the value back whole

### Requirement: A value the chapter metadata cannot keep is refused

The engine SHALL refuse a film whose title, author, comment or chapter title ends in a backslash, before it writes the
edition's subtitle documents, naming the file that holds the value, the field and the value, and SHALL NOT change the
value: FFmpeg reads the line after such a value into it, whatever is written. It SHALL judge each chapter's title as
the chapter metadata would hold it.

#### Scenario: A title that ends in a backslash

- **WHEN** an edition whose title ends in a backslash is assembled, or its captions are refreshed
- **THEN** the command refuses in one line that names the file it read the title from, the script for the assembly
  and the timeline for the refresh, the field and the value, and the edition's timeline, receipt and documents stay as
  they were

#### Scenario: A chapter that returns

- **WHEN** a film's segments stand in the chapters a, b and a again, and the chapter title of the segment where a
  returns ends in a backslash
- **THEN** the engine refuses and names that segment's chapter title, the one the third chapter would be written with

#### Scenario: A script corrected after the assembly

- **WHEN** an edition was assembled on a title that ends in a backslash, its script is corrected, and its captions
  are refreshed
- **THEN** the refresh refuses the edition as not bound to its current script, and says nothing of the title
