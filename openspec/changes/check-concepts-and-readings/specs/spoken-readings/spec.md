## ADDED Requirements

### Requirement: Every watched Chinese character resolves to a declared reading

For a pronunciation contract of schema version 2, every occurrence in the Chinese narration of a character on the engine's watch list SHALL resolve to one declared reading: by the longest declared word that covers it, or, for a character of the default class, by the film's declared default. An occurrence that does not resolve SHALL be refused with its segment, thought, position and surrounding text, and all such occurrences SHALL be reported together.

#### Scenario: A strict character outside any declared word

- **WHEN** 重 occurs in 去重 and no declared word covers that occurrence
- **THEN** the check refuses and names the segment, thought, position and the text around it

#### Scenario: A default character without a default

- **WHEN** 还 occurs outside every declared word and the film declares no default reading for 还
- **THEN** the check refuses and names the occurrence

#### Scenario: A version 1 contract

- **WHEN** the pronunciation contract declares schema version 1
- **THEN** the readings check does not apply and narration proceeds as before

### Requirement: Declared readings are dictionary readings

Each declared word's reading SHALL divide into one dictionary reading per character, written with or without spaces between syllables, and each default SHALL be a dictionary reading of its character. Where the dictionary's contextual reading of an occurrence differs from its declared reading, the declaring word SHALL record a reason; a default SHALL never resolve an occurrence the dictionary reads otherwise.

#### Scenario: A reading the dictionary does not hold

- **WHEN** a declared word gives a character a reading that is not among its dictionary readings
- **THEN** the check refuses and names the word and the character

#### Scenario: A declared reading the dictionary contradicts

- **WHEN** an occurrence's declared reading differs from the dictionary's contextual reading and its word records no reason
- **THEN** the check refuses and names the occurrence, the declared reading and the dictionary's reading

#### Scenario: A default that the context overrides

- **WHEN** a default would resolve an occurrence that the dictionary reads otherwise in context
- **THEN** the check refuses and names the occurrence, so the word that reads otherwise is declared

### Requirement: Every name has one declared spoken form

For a pronunciation contract of schema version 2, every Latin word in the Chinese narration SHALL be declared among its embedded English targets, and every English narration word written with two or more capital letters SHALL be declared among the English targets.

#### Scenario: An undeclared name in the Chinese narration

- **WHEN** the Chinese narration says ETHOS and no embedded English target declares it
- **THEN** the check refuses and names the word and its segments

#### Scenario: An undeclared name in the English narration

- **WHEN** the English narration says OpenSpec and no English target declares it
- **THEN** the check refuses and names the word and its segments

### Requirement: The resolved readings are written for review

The readings check SHALL write the occurrence plan of each edition it checks: every watched occurrence with its segment, thought, position, covering word, resolved reading, the basis of that reading and the dictionary's contextual reading. The plan SHALL be derived on every check and never read as a declaration.

#### Scenario: A passing check

- **WHEN** every watched occurrence resolves
- **THEN** the plan lists each occurrence with its reading, its basis and the dictionary's reading

### Requirement: Narration refuses unresolved readings

Narration SHALL run the readings check before any speech model loads and SHALL refuse when it refuses.

#### Scenario: Narrating with an unresolved reading

- **WHEN** narration is requested, with or without a dry run, and the readings check refuses
- **THEN** narration stops before synthesis and reports the check's refusals
