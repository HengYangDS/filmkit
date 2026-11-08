## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: A short English quotation stays on one caption line

The English caption phrasing SHALL NOT end a caption sentence at a sentence mark inside an open quotation while the sentence that the quotation continues into fits on one caption line with it. A quotation opens at “ ‘ 「 or 『 and closes at its closing mark, or opens at a straight double quote and closes at the next one. A longer quotation SHALL divide at its sentences as before.

#### Scenario: A quoted reply of two sentences

- **WHEN** a segment reads An Agent hands back one sentence: "Done. All tests pass." This sentence, how much does it actually say?
- **THEN** one caption reads An Agent hands back one sentence: "Done. All tests pass." and no caption ends with "Done.

#### Scenario: A quotation longer than a line

- **WHEN** a quotation's sentences together exceed the caption limit of 66 characters
- **THEN** its captions end at its sentences as before
