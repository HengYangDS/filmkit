# caption-text Specification

## Purpose

Set each caption line with its whole punctuation and its quotation marks as the picture sets them, so a reader never sees a line begin with the closing quote of the line before it or a typewriter quote beside the picture's typographic ones.

## Requirements

### Requirement: A Chinese caption line keeps its closing marks

The Chinese caption phrasing SHALL keep each closing quotation mark or bracket that follows a punctuation mark on the line that punctuation mark closes. A closing mark after a sentence end, a semicolon, a question or an exclamation SHALL end that line, and no caption line SHALL begin with a closing mark. The lines of a passage SHALL still hold its exact text in order.

#### Scenario: A quoted sentence ends a line

- **WHEN** a passage reads 它交回一句话：“完成了。测试全部通过。”这句话，到底说明了多少？
- **THEN** a line ends with 。” and the next line begins with 这句话

#### Scenario: A brief line that ends in a closing quote

- **WHEN** a caption line shown for under a second ends with 。”
- **THEN** it takes the same early start as a brief line that ends with 。

#### Scenario: A passage without closing marks

- **WHEN** a passage holds no closing quotation mark or bracket after a punctuation mark
- **THEN** its lines are the ones the phrasing set before

### Requirement: The display copy sets typographic quotation marks

The display copy of captions, subtitles, transcripts and their headings, chapter titles and the films' title, comment, description and synopsis tags SHALL set each apostrophe as a right single quotation mark, and each straight double quotation mark as a left one where it begins the text or follows a space, an opening bracket or a dash, and as a right one elsewhere. It SHALL change no other character, so a cue's timing and the waveform stay as they are.

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

### Requirement: A declared caption term stays on one line whatever its case

The English caption phrasing SHALL keep each caption term the film declares on one caption line, comparing the term's words with the caption's words without regard to case, and SHALL prefer a layout that keeps every declared term whole to any layout that splits one, whatever its line lengths and line ends cost; a term longer than a line takes the fewest splits. The declaration and the concept check SHALL keep each term as written.

#### Scenario: A term declared with capitals

- **WHEN** the English edition declares the caption term Work Lane and a sentence's cheapest break without the term falls between its two words
- **THEN** the caption keeps work lane on one line, as it does for the term declared in lowercase

#### Scenario: The term as the concept check names it

- **WHEN** the concept check reads the English caption terms
- **THEN** it names the term Work Lane as the declaration writes it

#### Scenario: A term kept whole after a function word

- **WHEN** the English edition declares the caption term Evidence-grounded Trust for Human-Agent Operational Stewardship and a sentence reads Its name stands for Evidence-grounded Trust for Human-Agent Operational Stewardship.
- **THEN** the captions read Its name stands for and Evidence-grounded Trust for Human-Agent Operational Stewardship. on two lines

### Requirement: A short English quotation stays on one caption line

The English caption phrasing SHALL NOT end a caption sentence at a sentence mark inside an open quotation while the sentence that the quotation continues into fits on one caption line with it. A quotation opens at “ ‘ 「 or 『 and closes at its closing mark, or opens at a straight double quote and closes at the next one. A longer quotation SHALL divide at its sentences as before.

#### Scenario: A quoted reply of two sentences

- **WHEN** a segment reads An Agent hands back one sentence: "Done. All tests pass." This sentence, how much does it actually say?
- **THEN** one caption reads An Agent hands back one sentence: "Done. All tests pass." and no caption ends with "Done.

#### Scenario: A quotation longer than a line

- **WHEN** a quotation's sentences together exceed the caption limit of 66 characters
- **THEN** its captions end at its sentences as before

### Requirement: An English caption read too fast is joined, held or recorded

An English cue read faster than 25 characters per second SHALL join an adjacent cue of its segment when no sentence ends between them, they stand under 0.25 s apart and the joined line fits 66 characters; otherwise it SHALL hold into the quiet after it until it reads at 25 characters per second, never past the next cue's start. A cue still above the rate SHALL be recorded with its rate. Cue words and starts SHALL stay their own; Chinese cues SHALL be unchanged.

#### Scenario: A fast cue joins its neighbour

- **WHEN** the cue "The inference is that the vendor" of 32 characters is shown for 1.12 s, and its sentence continues in the next cue 0.05 s later with 30 characters
- **THEN** the two become one cue of 62 characters from the first cue's start to the second's end

#### Scenario: A fast cue at a sentence end

- **WHEN** a cue of 26 characters ends its sentence after 0.9 s and the next cue starts 0.6 s later
- **THEN** it keeps its text and start and ends 1.04 s after it starts

#### Scenario: A cue within the rate

- **WHEN** a cue of 40 characters is shown for 2 s
- **THEN** it is unchanged

#### Scenario: A fast cue that can neither join nor hold

- **WHEN** a cue of 32 characters is shown for 1.12 s, joining it with the next cue of its sentence would make a line of 69 characters, and the next cue starts as it ends
- **THEN** it keeps its text and times, and the edition's caption record lists it at 28.6 characters per second

### Requirement: A cue's text is its typeset display copy

Each caption cue the engine writes into a timeline SHALL hold as its text its phrase as the segment's typeset text sets it, with no separate display copy, so a segment's cues join into its typeset narration. The segment's narration, thoughts and aligned words SHALL stay as the script and the aligner wrote them, and verification SHALL refuse a cue that holds a straight apostrophe or a straight double quotation mark.

#### Scenario: A contraction, a possessive and a quotation

- **WHEN** a segment reads They don't guess at the film's state. It says "Done. All tests pass."
- **THEN** its cues read They don’t guess at the film’s state. and It says “Done. All tests pass.”, at the times and with the subtitle lines they had before
- **AND** the segment's text and words are unchanged

#### Scenario: A timeline built before

- **WHEN** an English timeline's cue reads the film's data beside the display copy the film’s data
- **THEN** verification refuses it until `refresh-captions` rewrites the cue as the film’s data

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
