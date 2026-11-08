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
