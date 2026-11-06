# spoken-readings Specification

## Purpose

Give every ambiguous Chinese character in a film's narration one declared reading at each occurrence, and every name one declared spoken form, before any speech is synthesized.

## Requirements

### Requirement: Every watched Chinese character resolves to a declared reading

For a pronunciation contract of schema version 2, every occurrence in the Chinese narration of a character on the engine's watch list SHALL resolve to the reading of the longest declared word that covers it. An occurrence that does not resolve SHALL be refused with its segment, thought, position and surrounding text, and all such occurrences SHALL be reported together.

#### Scenario: An undeclared single character

- **WHEN** 还 occurs outside every declared word and the film does not declare 还
- **THEN** the check refuses and names the segment, thought, position and the text around it

#### Scenario: A version 1 contract

- **WHEN** the pronunciation contract declares schema version 1
- **THEN** the readings check does not apply and narration proceeds as before

### Requirement: A word character resolves only inside a declared word

An occurrence of a character in the watch list's word class SHALL be covered by a declared word of two or more characters. An occurrence of a character in its single-character class MAY be covered by the character's own declaration.

#### Scenario: A word character outside any declared word

- **WHEN** 重 occurs in 去重 and no declared word covers that occurrence
- **THEN** the check refuses and names the occurrence

#### Scenario: A word character covered only by its own declaration

- **WHEN** 重 is declared as a single character and occurs in 去重, which no declared word covers
- **THEN** the check refuses and names the occurrence

### Requirement: Declared readings are dictionary readings

Each declared word's reading SHALL divide into one dictionary reading per character, written with or without spaces between syllables; after a word's first character, the reading MAY be in the neutral tone. Where the dictionary's contextual reading of an occurrence differs from its declared reading, the declaring word SHALL record a reason. A declared single character SHALL NOT record a reason, so it never resolves an occurrence the dictionary reads otherwise.

#### Scenario: A reading the dictionary does not hold

- **WHEN** a declared word gives a character a reading that is not among its dictionary readings
- **THEN** the check refuses and names the word and its reading

#### Scenario: A neutral tone after the first character

- **WHEN** a word declares 还是 as háishi, with 是 in the neutral tone
- **THEN** the declaration divides into hái and shi and is accepted

#### Scenario: A declared reading the dictionary contradicts

- **WHEN** an occurrence's declared reading differs from the dictionary's contextual reading and its word records no reason
- **THEN** the check refuses and names the occurrence, the declared reading and the dictionary's reading

#### Scenario: A single character that the context overrides

- **WHEN** a declared single character covers an occurrence that the dictionary reads otherwise in context
- **THEN** the check refuses and names the occurrence, so the word that reads otherwise is declared

### Requirement: Declarations stay current

The check SHALL refuse a Chinese word declared more than once, a declared word that the Chinese narration never says, and a recorded reason that no occurrence needs, naming each.

#### Scenario: A declaration the narration no longer needs

- **WHEN** a script edit removes the last occurrence of a declared word
- **THEN** the check refuses and names the word as declared but never said

#### Scenario: A reason no occurrence needs

- **WHEN** a declared word records a dictionary disagreement and every occurrence it covers agrees with the dictionary
- **THEN** the check refuses and names the word

### Requirement: Every name has one declared spoken form

For a pronunciation contract of schema version 2, every Latin word in the Chinese narration SHALL be declared among its embedded English targets, and every English narration word written with two or more capital letters SHALL be declared among the English targets.

#### Scenario: An undeclared name in the Chinese narration

- **WHEN** the Chinese narration says ETHOS and no embedded English target declares it
- **THEN** the check refuses and names the word and its segments

#### Scenario: An undeclared name in the English narration

- **WHEN** the English narration says OpenSpec and no English target declares it
- **THEN** the check refuses and names the word and its segments

### Requirement: The resolved readings are written for review

The readings check SHALL write the occurrence plan of each edition it checks: every watched occurrence with its thought, position, character class, covering word, declared reading, the dictionary's contextual reading and the text around it. The plan SHALL be derived on every check and never read as a declaration.

#### Scenario: A passing check

- **WHEN** every watched occurrence resolves
- **THEN** the plan lists each occurrence with its covering word, its declared reading, the dictionary's reading and the text around it

### Requirement: Proposed declarations help an author declare

On request, the readings check SHALL write a proposed declaration for each watched occurrence in the Chinese narration that no declaration resolves: the dictionary's word around it, widened to two characters for a word character, with the dictionary's contextual reading, grouped by word with its occurrences and where they are said. Proposing SHALL NOT change the pronunciation contract.

#### Scenario: Proposals for an undeclared narration

- **WHEN** an author requests proposals and 去重 is said twice with no declared word covering 重
- **THEN** the proposals list 去重 with the dictionary's reading, two occurrences and the thoughts that say it, and the contract is unchanged

### Requirement: Narration refuses unresolved readings

Narration SHALL run the readings check before any speech model loads and SHALL refuse when it refuses.

#### Scenario: Narrating with an unresolved reading

- **WHEN** narration is requested, with or without a dry run, and the readings check refuses
- **THEN** narration stops before synthesis and reports the check's refusals

### Requirement: A film declares how its Latin-script terms are said

A film MAY declare terms in its declaration, outside the pronunciation contract whose hash binds every recording. Each holds the term, the spoken form that every language gives it, its pronunciation in IPA and, for each edition that says it, a reference occurrence by thought and occurrence index, whose take a person heard correct. A reference the edition's narration does not hold SHALL be refused.

#### Scenario: A stale reference

- **WHEN** the declared reference occurrence is not in the edition's narration
- **THEN** the check refuses and names the stale reference

#### Scenario: A declaration that re-records nothing

- **WHEN** a film adds a term declaration and changes nothing else
- **THEN** every recording's request, and so its fingerprint, is unchanged

### Requirement: Every language speaks a declared term by its declared form

Before any speech model loads, the readings check SHALL refuse when a language's normalization in the pronunciation contract gives a declared term a spoken form other than the declared one, or none, naming the language, the term, the contract's form and the declared form.

#### Scenario: One spelling per language

- **WHEN** ETHOS is declared with the spoken form Eethos, and the contract normalizes it to Eethos in Chinese and to `Ethos` in English
- **THEN** the readings check refuses before narration and names English, ETHOS, `Ethos` and Eethos

#### Scenario: The same spoken form everywhere

- **WHEN** every language normalizes ETHOS to Eethos
- **THEN** the check passes

### Requirement: Every occurrence of a declared term is said like its reference

An occurrence's first vowel is the median F1 and F2 of its voiced frames up to 32 % into its aligned word, from up to one aligner frame (80 ms) before its aligned start but not before the previous word's end. At selection and on an assembled soundtrack, an occurrence whose F1 exceeds 1.5 times the reference's, or whose F2 falls below 0.85 times, SHALL be refused, named with both ratios. An audition SHALL NOT propose a failing take while a qualifying one passes.

#### Scenario: An occurrence said with another vowel

- **WHEN** ETHOS is declared as /ˈiːθɒs/ with a reference whose first vowel measures F1 252 Hz and F2 2795 Hz, and one occurrence measures F1 707 Hz and F2 2042 Hz
- **THEN** the check refuses and names that occurrence with both ratios

#### Scenario: A correct occurrence with a higher first formant

- **WHEN** an occurrence measures F1 327 Hz and F2 2810 Hz against a reference of F1 243 Hz and F2 2842 Hz
- **THEN** the check passes it and records both ratios
