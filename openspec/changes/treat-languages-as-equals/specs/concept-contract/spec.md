## MODIFIED Requirements

### Requirement: A film may declare a concept contract

A film MAY name a concept contract in its declaration. Each concept SHALL carry its source term, its essence, its source passage, and for each declared edition one approved rendering, the forms the narration may use and the counterexamples to refuse. The engine SHALL refuse a contract that is malformed, repeats a concept id, gives a concept no rendering for a declared edition or one for an undeclared edition, or cites a document the source manifest does not pin, naming each failing entry.

#### Scenario: A malformed contract is refused

- **WHEN** a concept lacks a rendering for a declared edition, holds one for an edition the film does not declare, or two concepts share an id
- **THEN** the check refuses and names each failing entry

#### Scenario: A concept cites an unpinned document

- **WHEN** a concept's source path is not a document of the source manifest
- **THEN** the check refuses and names the concept and the path

#### Scenario: A film without a contract

- **WHEN** the film declaration names no concept contract
- **THEN** the check reports that no contract is declared, and narration proceeds as before

### Requirement: Segments name their concepts by the approved renderings

A script segment MAY declare the concepts it states. Each declared concept SHALL exist in the contract; the same segment SHALL declare the same concepts in every edition; and each declared concept SHALL appear in that segment's narration by its edition's rendering or one of its forms: as a substring in a language whose words spaces do not delimit, as Chinese, and as a whole-word phrase, ignoring case, in a language whose words spaces delimit, as English.

#### Scenario: An undeclared or unknown concept

- **WHEN** a segment declares an id the contract does not hold
- **THEN** the check refuses and names the segment and the id

#### Scenario: Editions that declare different concepts

- **WHEN** one segment declares different concepts in two of its editions
- **THEN** the check refuses and names the segment, those editions and the concepts that differ

#### Scenario: A declared concept said in other words

- **WHEN** a segment declares a concept whose rendering and forms do not appear in its narration
- **THEN** the check refuses and names the segment, the edition and the concept

### Requirement: A Latin-script term's number is carried in Chinese

A Latin-script word keeps its base form in a language that marks no grammatical number, as Chinese. Where the counterpart of such a thought, in an edition whose language marks number, uses that word only in its plural, the clause holding it SHALL hold one of its language's number words, or the concept check SHALL refuse before narration, naming the edition, thought, word, plural and clause. A film MAY declare more number words, and exceptions with a reason.

#### Scenario: A plural heard as one

- **WHEN** a Chinese thought says 可以互相替换的 Agent and its English counterpart says "interchangeable Agents"
- **THEN** the check refuses and names the thought, Agent, Agents and the clause

#### Scenario: A number carried by Chinese words

- **WHEN** the Chinese clause says 越来越多的 Agent, 两个 Agent or 那些可以互相替换的 Agent
- **THEN** the check passes it

#### Scenario: A declared generic use

- **WHEN** the film declares 运行 Agent 的应用 in a thought as a generic use, with its reason
- **THEN** the check passes it and a declaration that names no current occurrence is refused as stale
