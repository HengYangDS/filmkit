## ADDED Requirements

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
