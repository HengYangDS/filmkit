## ADDED Requirements

### Requirement: A declared caption term stays on one line whatever its case

The English caption phrasing SHALL keep each caption term the film declares on one caption line, comparing the term's words with the caption's words without regard to case; the declaration and the concept check SHALL keep each term as written.

#### Scenario: A term declared with capitals

- **WHEN** the English edition declares the caption term Work Lane and a sentence's cheapest break without the term falls between its two words
- **THEN** the caption keeps work lane on one line, as it does for the term declared in lowercase

#### Scenario: The term as the concept check names it

- **WHEN** the concept check reads the English caption terms
- **THEN** it names the term Work Lane as the declaration writes it
