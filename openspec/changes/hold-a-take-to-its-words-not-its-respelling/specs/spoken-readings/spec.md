## ADDED Requirements

### Requirement: A Latin name respelled in other letters is a declared term

Where an edition says a name that its language's normalization respells as one Latin word of other letters, the film SHALL declare the name as a term, and the readings check, whatever the contract's schema version, SHALL refuse such a name that no declared term names, in one line that names the name, its spoken form and the thoughts that say it. A rule that only spaces or recases a name, or whose display or spoken form is not a single Latin word, SHALL ask for no term.

#### Scenario: A respelled name and no term

- **WHEN** the contract respells HyperFrames as Hyperfraims in every language, the Chinese narration says it in 03.1 and the film declares no term
- **THEN** the readings check refuses with "zh: the normalization respells HyperFrames as Hyperfraims, said in 03.1; declare HyperFrames in [[narration.terms]]"

#### Scenario: The term declared

- **WHEN** the film declares HyperFrames with the spoken form Hyperfraims and a Chinese reference occurrence in 03.1
- **THEN** the readings check passes

#### Scenario: A name only spaced

- **WHEN** the contract respells HyperFrames as Hyper Frames and the film declares no term
- **THEN** the readings check asks for no term

### Requirement: A command that loads a speech model asks for the term first

`judge`, `converge` and `audition` SHALL refuse a name that their receipt's thoughts say and that the readings check would refuse for want of a term, with the same line, before any speech model loads.

#### Scenario: A complete receipt

- **WHEN** a receipt holds every recording, so that nothing is narrated, and the film respells a name it says and declares no term
- **THEN** `judge` refuses with the readings check's line before any speech model loads
