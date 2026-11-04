## Purpose

Set each caption line with its whole punctuation and its quotation marks as the picture sets them, so a reader never sees a line begin with the closing quote of the line before it or a typewriter quote beside the picture's typographic ones.

## ADDED Requirements

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

The display copy of captions, subtitles and transcripts SHALL set each apostrophe as a right single quotation mark, and each straight double quotation mark as a left double quotation mark where it begins the text or follows a space, an opening bracket or a dash, and as a right double quotation mark elsewhere. It SHALL change no other character, so a cue's text, its timing and the waveform stay as they are.

#### Scenario: A quoted sentence in English

- **WHEN** a segment reads An Agent hands back one sentence: "Done. All tests pass."
- **THEN** its display copy reads An Agent hands back one sentence: “Done. All tests pass.”

#### Scenario: An apostrophe

- **WHEN** a segment reads the reviewer's notes
- **THEN** its display copy reads the reviewer’s notes
