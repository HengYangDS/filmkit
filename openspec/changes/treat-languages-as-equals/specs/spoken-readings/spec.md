## ADDED Requirements

### Requirement: Each edition's pronunciation stands in its folder and binds only its own recordings

Each edition's pronunciation SHALL stand in `content/<code>/pronunciation.json`, with its normalization, its targets, the sources that it alone cites and its status, and its analyst readings, where the film records any, in `content/<code>/readings.json`. A recording's request SHALL bind the SHA-256 of its own edition's pronunciation and of no other. Narration SHALL refuse an edition without its pronunciation before any speech model loads, naming the file.

#### Scenario: One language's targets edited

- **WHEN** the English pronunciation gains a target and nothing else changes
- **THEN** every Chinese recording's request, and so its fingerprint, is unchanged

#### Scenario: A missing pronunciation

- **WHEN** `content/en/pronunciation.json` does not exist
- **THEN** narration refuses before any speech model loads and names it

#### Scenario: A take recorded before the split

- **WHEN** a take recorded under the digest of the whole former contract is selected after the split, its spoken text unchanged
- **THEN** the selection keeps it

### Requirement: The declaration holds the pronunciation provenance that every edition shares

The schema version, the control boundary, the acceptance criteria and each source that more than one edition cites SHALL stand once, in the declaration's `[pronunciation]` table, and SHALL bind no recording. A target's source SHALL be found in its own edition's pronunciation or in that table, or the target SHALL be refused.

#### Scenario: The shared provenance edited

- **WHEN** the acceptance criteria in the declaration's `[pronunciation]` table change
- **THEN** no recording's request changes

#### Scenario: A source cited by no list

- **WHEN** an English target cites `cmudict` and neither the English pronunciation nor the declaration's table lists it
- **THEN** the readings check refuses before narration, naming the target and the source

### Requirement: A pronunciation states nothing the engine derives

An edition's pronunciation SHALL NOT state its language, which its folder's code states, and no pronunciation SHALL hold an occurrence plan, which the readings check derives under `build/`. The engine SHALL refuse either before any speech model loads, naming the file and the key and saying to remove it.

#### Scenario: A part that states its language

- **WHEN** `content/zh/pronunciation.json` states `"language": "Chinese"`
- **THEN** narration refuses before any speech model loads, naming the file and `language`

#### Scenario: A tracked occurrence plan

- **WHEN** an edition's pronunciation holds `occurrence_plan`
- **THEN** narration refuses before any speech model loads, naming the file and `occurrence_plan`

## MODIFIED Requirements

### Requirement: A film declares how its Latin-script terms are said

A film MAY declare terms in its declaration, outside each edition's pronunciation, whose hash binds that edition's recordings. Each holds the term, the spoken form that every language gives it, its pronunciation in IPA and, for each edition that says it, a reference occurrence by thought and occurrence index, whose take a person heard correct. A reference the edition's narration does not hold SHALL be refused.

#### Scenario: A stale reference

- **WHEN** the declared reference occurrence is not in the edition's narration
- **THEN** the check refuses and names the stale reference

#### Scenario: A declaration that re-records nothing

- **WHEN** a film adds a term declaration and changes nothing else
- **THEN** every recording's request, and so its fingerprint, is unchanged
