## ADDED Requirements

### Requirement: A film's keywords import whole where the importer allows

Packaging SHALL write each film's QuickTime keywords as the release's keywords joined by "," with no space. Where the host has `mdimport`, the verifier SHALL read each delivered film's imported keywords and SHALL refuse a film with an imported keyword that has a leading or trailing space, no keyword while some are declared, or a declared keyword holding a Chinese character that does not import whole. Where the host has no `mdimport`, the verifier SHALL record the readback as unavailable.

#### Scenario: Chinese keywords in Spotlight

- **WHEN** a Chinese edition declares the keywords DDWG, 数据质量 and 人与人工智能的协作
- **THEN** its films carry the QuickTime keywords `DDWG,数据质量,人与人工智能的协作`, and `mdimport` imports the three keywords, each without a space at either end

#### Scenario: An English phrase in Spotlight

- **WHEN** an English edition declares the keyword "authority to act"
- **THEN** the verifier records that the importer split it into words and does not refuse the film

#### Scenario: Keywords joined with spaces

- **WHEN** a delivered film carries the QuickTime keywords `DDWG, 数据质量` and the host has `mdimport`
- **THEN** the verifier refuses the film, naming the keyword imported with a leading space

#### Scenario: Keywords the importer does not read

- **WHEN** an English edition declares the keyword "authority to act" and `mdimport` imports no keyword from its film
- **THEN** the verifier refuses the film

### Requirement: A film's author imports as the declared author alone

Where the host has `mdimport`, the verifier SHALL read each delivered film's imported authors and SHALL refuse a film whose authors are not exactly the release's declared author, once. Where the host has no `mdimport`, the verifier SHALL record the readback as unavailable.

#### Scenario: The declared author alone

- **WHEN** a delivered film's importer reads its authors as `Yang HENG`, the release's declared author
- **THEN** the verifier records the author and does not refuse the film

#### Scenario: A second author entry

- **WHEN** a delivered film carries the declared author in both its author and artist keys, so the importer reads `Yang HENG` twice and Finder shows "Yang HENG (2)"
- **THEN** the verifier refuses the film, naming the two author entries it read

### Requirement: A film or cover link opens beside the player

Each player SHALL link each delivered film and cover with `target="_blank"` and `rel="noopener"`. The browser readback SHALL click every such link and SHALL refuse a page that leaves its own address or opens no new tab holding the linked file.

#### Scenario: A film link clicked

- **WHEN** the readback clicks a player's link to its UHD film
- **THEN** a new tab opens the film, and the player stays at its own address

#### Scenario: A link that replaces the player

- **WHEN** a player's cover link has no `target`
- **THEN** the readback fails, names the page and the link, and delivery refuses
