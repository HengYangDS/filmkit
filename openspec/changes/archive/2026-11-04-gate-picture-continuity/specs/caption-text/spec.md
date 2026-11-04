## MODIFIED Requirements

### Requirement: The display copy sets typographic quotation marks

The display copy of captions, subtitles, transcripts and their headings, chapter titles and the films' title, comment, description and synopsis tags SHALL set each apostrophe as a right single quotation mark, and each straight double quotation mark as a left one where it begins the text or follows a space, an opening bracket or a dash, and as a right one elsewhere. It SHALL change no other character, so a cue's text, its timing and the waveform stay as they are.

#### Scenario: A quoted sentence in English

- **WHEN** a segment reads An Agent hands back one sentence: "Done. All tests pass."
- **THEN** its display copy reads An Agent hands back one sentence: “Done. All tests pass.”

#### Scenario: An apostrophe

- **WHEN** a segment reads the reviewer's notes
- **THEN** its display copy reads the reviewer’s notes

#### Scenario: A part title and the release synopsis

- **WHEN** a segment is titled "Done" and the release synopsis quotes "Done. All tests pass."
- **THEN** the transcript's heading and the player's transcript read “Done”, and the films' synopsis tag reads “Done. All tests pass.”

#### Scenario: A chapter title with an apostrophe

- **WHEN** a chapter is titled One requirement's life
- **THEN** the transcript, the chapters file, the chapter metadata and the films' chapter track read One requirement’s life

#### Scenario: A Chinese edition

- **WHEN** a Chinese script's titles and release text set only typographic quotation marks
- **THEN** its transcript, chapters and tags are the same as before
