## ADDED Requirements

### Requirement: The source check asks the register

`filmkit check` SHALL ask the register beside the concept contract and SHALL refuse, with every other finding of the sources, while the film's words hold an error-level form that the film does not excuse or the check cannot be run.

#### Scenario: An address of the audience before a render

- **WHEN** a thought holds 你们 and every other source passes
- **THEN** the check names the thought and the form, records the outcome `refuse` and exits 1

#### Scenario: A checker that is not the pinned one

- **WHEN** the Vale on the path reports another version than the engine's release record
- **THEN** the check names both versions and the line `mise use github:vale-cli/vale@<version>` that pins the engine's, and records the outcome `refuse`

## MODIFIED Requirements

### Requirement: A run of the entry page ends only at a block

A run of the entry page SHALL end only where a block element begins or ends; every other element SHALL be read as
inline, and a line break SHALL be read as a space inside its run. A page that cannot be read as text SHALL be refused
in one line.

#### Scenario: A form parted by an element the engine does not know

- **WHEN** an entry page writes 其 and 实 either side of a `wbr`, an `s`, a `ruby` or a custom element
- **THEN** the register check refuses 其实 and names the entry page

#### Scenario: A line break in either spelling

- **WHEN** one line of an element ends in 一 and the next begins with 下, parted by `<br>` or by `<br/>`
- **THEN** the register check reports no 一下 in either spelling, and two questions either side of the break count
  as one run's

#### Scenario: A page that is no text

- **WHEN** the entry page's bytes are not UTF-8
- **THEN** the check refuses in one line that names the page, and `filmkit check` records the outcome `refuse`
