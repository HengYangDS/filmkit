## ADDED Requirements

### Requirement: A contract declares Latin-script terms with a reference occurrence

A pronunciation contract MAY declare `latin_terms`. Each holds its term, its pronunciation in IPA and, for each edition that says it, a reference occurrence by segment, thought and occurrence index, whose take a person heard correct. A reference the edition's narration does not hold SHALL be refused.

#### Scenario: A stale reference

- **WHEN** the declared reference occurrence is not in the edition's narration
- **THEN** the check refuses and names the stale reference

### Requirement: Every occurrence of a declared term is said like its reference

Each occurrence's first vowel is measured as the median first and second formants of its voiced frames over the first 32 % of its aligned word. At selection and on an assembled soundtrack it SHALL lie within 25 % of the reference's first formant and 15 % of its second, or the check SHALL refuse and name the occurrence, its formants and the reference's. An audition SHALL NOT propose a take whose occurrence fails while another qualifying take passes.

#### Scenario: An occurrence said with another vowel

- **WHEN** ETHOS is declared as /ˈiːθɒs/ with a reference whose first vowel measures F1 252 Hz and F2 2795 Hz, and one occurrence measures F1 707 Hz and F2 2042 Hz
- **THEN** the check refuses and names that occurrence with both measurements

#### Scenario: Consistent occurrences

- **WHEN** every occurrence's first vowel lies within the bounds of the reference
- **THEN** the check passes and records each occurrence's formants
