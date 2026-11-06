## ADDED Requirements

### Requirement: Wrapped labels are judged at rest from their painted lines

`check-picture` SHALL read the lines of every label a film paints on more than one line from the film's own layout records, and judge them at the frames where every line stands at 0.9 opacity or more. A refusal SHALL name the scene, the label's lines, the first time they stand at rest and each rule they break.

#### Scenario: A label that is still entering

- **WHEN** a wrapped label stands below 0.9 opacity
- **THEN** its lines are not judged until it stands at rest

#### Scenario: A name standing in two places

- **WHEN** the same wrapped name stands at two places of one frame
- **THEN** each place is judged as its own label

### Requirement: A wrapped English label breaks at a phrase

`check-picture` SHALL refuse an English label whose line other than the last ends on a lead word: an article, preposition, conjunction, determiner, possessive, wh-word or auxiliary, or a lead word the film declares. It SHALL also refuse a name of three or more words whose last line holds one word.

#### Scenario: An English line ends on a preposition

- **WHEN** a rail label stands at rest as "A trade in" over "the market"
- **THEN** `check-picture` writes a refused record that names the label's lines and the line ending on "in", and exits with a refusal

#### Scenario: One word left for the last line

- **WHEN** "Bias may hide" stands over "elsewhere"
- **THEN** `check-picture` refuses the label

### Requirement: The lines of a wrapped block stay even

Among the lines of one size in a wrapped label, `check-picture` SHALL refuse a line other than the last that is narrower than the declared share of the widest (0.8 by default), and a last line narrower than the declared last share (0.6 by default).

#### Scenario: A short last line

- **WHEN** a Chinese label stands at rest as 先确认任务、要处理的对象、 over 现状和负责人, its last line 0.48 of its first
- **THEN** `check-picture` refuses the label and names its last line's share

#### Scenario: A name over its smaller gloss

- **WHEN** a name at the label size stands over a two-line gloss at the note size
- **THEN** the name and the gloss are each judged among their own lines, and the shorter gloss is not refused for its size

### Requirement: A Chinese line opens on no closing punctuation

`check-picture` SHALL refuse a wrapped Chinese label whose line after the first opens on closing punctuation.

#### Scenario: A comma at the start of a line

- **WHEN** a label's second line opens on 、
- **THEN** `check-picture` refuses the label

### Requirement: A film declares its wrapping rules and their exceptions

A film MAY declare `[picture.wrapping]` in `content/film.toml`: `line_share`, `last_share`, `lead_words` and `exceptions`, each exception the exact lines of one label with its reason. A label that matches an exception SHALL be recorded and SHALL NOT refuse. The declaration SHALL be refused for a share outside (0, 1], an exception without a reason, and an exception whose lines the film never paints.

#### Scenario: A declared exception

- **WHEN** the film declares "Stated" over "assumptions" as an exception with its reason
- **THEN** `check-picture` records that label with the reason and does not refuse it

#### Scenario: A stale exception

- **WHEN** an exception names lines that no frame of the edition paints
- **THEN** `check-picture` refuses and names the stale exception
