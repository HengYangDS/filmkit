# film-engine Specification

## MODIFIED Requirements

### Requirement: A film declares its parameters

A film SHALL declare, in one declaration, its file prefix, delivery folder, entry page, source manifest, each edition's sources folder, cover and caption terms, the fonts its picture uses, and its review prompt, floors, scored dimensions and listening-plan readings. The engine SHALL refuse an invalid or incomplete declaration before any work, naming each failing field; a cover may be absent until the engine paints it.

#### Scenario: An invalid declaration refuses before work

- **WHEN** the declaration omits an edition, names a font or another file that is missing other than a cover, gives a malformed file prefix or a review floor outside 0 to 100
- **THEN** the engine refuses when it loads, before any synthesis, and names each failing field

#### Scenario: The declared fonts are staged in their declared order

- **WHEN** the engine stages a film's picture
- **THEN** the stage holds each declared font, and no other font, below `fonts/` in the declared order

#### Scenario: The listening plan takes the film's own readings

- **WHEN** the listening plan is derived for a film that declares its readings
- **THEN** each English heteronym occurrence takes the part of speech the film records for it
- **AND** an occurrence the film records no part of speech for, or a recorded one that names no current occurrence, refuses the plan

## ADDED Requirements

### Requirement: A film paints its covers from its picture

The engine SHALL paint each edition's cover from the edition's staged picture and compare it with the tracked cover. A film MAY name covers before it paints them; packaging SHALL refuse an edition whose cover is missing, naming the cover's field. A painted cover with no tracked cover to compare SHALL be written and reported as uncompared, and SHALL NOT pass the cover check.

#### Scenario: A new film narrates before it paints its covers

- **WHEN** a film's declaration names covers that do not exist yet
- **THEN** the engine loads the declaration, narrates and stages the picture
- **AND** packaging refuses each edition whose cover is missing and names `editions.<code>.cover`

#### Scenario: A first cover is painted with nothing to compare

- **WHEN** the cover check paints an edition's cover and the tracked cover does not exist
- **THEN** it writes the painted cover and reports that no tracked cover was compared
- **AND** it fails until the painted cover is tracked and identical to a new painting
