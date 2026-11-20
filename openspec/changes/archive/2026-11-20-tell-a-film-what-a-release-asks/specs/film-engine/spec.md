## MODIFIED Requirements

### Requirement: A film declares its parameters

A film SHALL declare, in one declaration, its file prefix, delivery folder, entry page, source manifest, each edition's sources folder, cover and caption terms, the fonts its picture uses, and its review prompt, floors, scored dimensions and listening-plan readings. The engine SHALL refuse an invalid or incomplete declaration before any work, naming each failing field together with a key that an earlier release named otherwise; a cover may be absent until the engine paints it.

#### Scenario: An invalid declaration refuses before work

- **WHEN** the declaration omits an edition, names a font or another file that is missing other than a cover, gives a malformed file prefix or a review floor outside 0 to 100
- **THEN** the engine refuses when it loads, before any synthesis, and names each failing field

#### Scenario: Two problems of different kinds

- **WHEN** the declaration still names its delivery folder by the key an earlier release used and gives a malformed file prefix
- **THEN** one refusal names the renamed key and the file prefix, and the folder the renamed key carries is not reported as missing

#### Scenario: Missing files and a player page together

- **WHEN** a declaration whose fields load names a script that is missing and an edition's sources still hold a player page
- **THEN** one refusal names both

#### Scenario: The declared fonts are staged in their declared order

- **WHEN** the engine stages a film's picture
- **THEN** the stage holds each declared font, and no other font, below `fonts/` in the declared order

#### Scenario: The listening plan takes the film's own readings

- **WHEN** the listening plan is derived for a film that declares its readings
- **THEN** each English heteronym occurrence takes the part of speech the film records for it
- **AND** an occurrence the film records no part of speech for, or a recorded one that names no current occurrence, refuses the plan
