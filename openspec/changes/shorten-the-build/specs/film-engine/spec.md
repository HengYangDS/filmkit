## ADDED Requirements

### Requirement: A film may make both editions' pictures with one command

A film's task list MAY call `render-picture --language all`, and nothing requires it. The command SHALL make each edition's picture by that edition's own `render-picture`, with its own receipt and duration record: two rendered pictures at the same time, with the renderer's own lock off for those two renders alone, which each receipt records, and two derived pictures one after the other. Once both have ended it SHALL fail, naming each edition whose picture was not made.

#### Scenario: Both captioned pictures

- **WHEN** `render-picture --language all` runs
- **THEN** both editions' captioned renders start before either has ended, and each edition's receipt records the renderer's lock as off

#### Scenario: Both uncaptioned pictures rendered

- **WHEN** a film that declares no capture runs `render-picture --language all --uncaptioned`
- **THEN** both editions' uncaptioned stages are rendered at the same time, each receipt recording the lock as off

#### Scenario: Both uncaptioned pictures derived

- **WHEN** a film that declares `software` capture runs `render-picture --language all --uncaptioned`
- **THEN** the English derivation starts once the Chinese one has ended, and no render's lock is changed

#### Scenario: One edition is refused

- **WHEN** the Chinese captioned render is refused while the English one runs
- **THEN** the English picture is rendered to its end, and the command then fails, naming the Chinese edition

#### Scenario: Another action

- **WHEN** `validate-picture --language all` is asked for
- **THEN** the command refuses and names `render-picture` as the one action that takes `all`
