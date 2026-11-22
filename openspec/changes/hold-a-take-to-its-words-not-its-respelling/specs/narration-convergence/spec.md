## ADDED Requirements

### Requirement: A respelled Han word reads as its spoken form

Where a `homophone` rule of the pronunciation contract respells a Han word, the comparison of a transcript with a take's text SHALL read that word as the dictionary reads the rule's spoken form, in the text and in the transcript.

#### Scenario: A respelled word written in its own characters

- **WHEN** the contract respells 去重 as 去虫, the take's spoken text holds 去虫 and its transcript holds 去重
- **THEN** the take differs by no unit by reading

#### Scenario: A respelled word where the text holds the reading respelled against

- **WHEN** the contract respells 去重 as 去虫, the take's text holds 去众 and its transcript holds 去重
- **THEN** the take differs by one unit by reading

### Requirement: A declared term is one unit under both its forms

Where a transcript is compared with a take's text, a Latin unit that says a term the film declares, its display form or its spoken form in any case, SHALL count as that term, its possessive kept, in every edition. A Latin unit in other letters SHALL still differ in the English edition.

#### Scenario: A declared term in its display form

- **WHEN** a film declares the term NAME with the spoken form Naim, an English take's text holds "Naim's" and its transcript holds "Name's"
- **THEN** the take differs by one unit and by no unit by reading

#### Scenario: A declared term in other letters in English

- **WHEN** the same film's English take's text holds "Naim" and its transcript holds "Nime"
- **THEN** the take differs by one unit by reading

### Requirement: In Chinese speech one Latin unit of other letters may stand for a declared term

In the Chinese edition a declared term SHALL also count as the same as one Latin unit of other letters that holds a letter, says no declared term and is no other Latin unit of the edition's script. Two or more units, digits alone, a Han character and another Latin unit of the script SHALL still differ. The take's record SHALL name each unit that stood for a term, with its term.

#### Scenario: A declared term in other letters in Chinese speech

- **WHEN** the film's Chinese take's text holds "Naim 走的是另一条路。", its script's other Latin units are agent and git, and its transcript holds "Nime走的是另一条路。"
- **THEN** the take differs by no unit by reading, and its record names nime for NAME

#### Scenario: What still differs in Chinese speech

- **WHEN** that Chinese transcript holds, in the term's place, "Agent", "2024", "内姆", "Nime Nime", "Nime OK" or nothing
- **THEN** the take differs by at least one unit by reading

### Requirement: A reference without two formants stops the command in one line

Where a declared term's reference occurrence shows no two formants, on its take or as the selection aligns its segment, `judge`, `converge` and `audition` SHALL stop before they judge a thought against it or ask a candidate, with one line that names the reference and says to declare another occurrence, and with no traceback.

#### Scenario: On its take

- **WHEN** a film's reference occurrence 26.1 #0 of NAME shows no two formants on the receipt's take
- **THEN** `judge` exits with the one line "en: the NAME reference 26.1 #0 shows no two formants on its take; declare another occurrence of NAME as its en reference in [[narration.terms]]"

#### Scenario: In its segment

- **WHEN** the take alone shows two formants and the segment's alignment beside the receipt shows none at the reference
- **THEN** `judge` exits with one line that names the reference, says that the selection aligns its segment, and says to declare another occurrence, and writes no judgment record
