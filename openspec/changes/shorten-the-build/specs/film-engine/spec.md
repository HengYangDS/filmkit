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

## MODIFIED Requirements

### Requirement: A film declares how its picture is captured

A film MAY declare `[picture] capture` as `fast`, `screenshot` or `software`; one that declares none captures `fast`. Every render of its picture SHALL pass the renderer's browser and capture flags of the declared mode explicitly. Each render receipt SHALL record the mode, and validation SHALL refuse a picture whose receipt records another mode than the declaration, reading a receipt that records none by its command.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture renders its captioned or uncaptioned picture
- **THEN** the renderer command is the command that filmkit 0.19.0 runs but for its worker count, and the receipt records `fast`

#### Scenario: A film that declares screenshot capture

- **WHEN** a film declares `capture = "screenshot"` and renders its pictures and its draft
- **THEN** each command passes `--experimental-fast-capture=false` where `fast` passes `--experimental-fast-capture`, and each receipt records `screenshot`

#### Scenario: A film that declares software capture

- **WHEN** a film declares `capture = "software"` and renders its pictures and its draft
- **THEN** each command passes `--no-browser-gpu` where `fast` passes `--browser-gpu` and `--experimental-fast-capture=false` where `fast` passes `--experimental-fast-capture`, and each receipt records `software`

#### Scenario: Another capture value

- **WHEN** the declaration gives `capture = "drawelement"`
- **THEN** the engine refuses when it loads, naming `picture.capture`

#### Scenario: A picture rendered in another mode

- **WHEN** a film declares screenshot capture and its picture's receipt records `fast`
- **THEN** validation refuses the picture, naming both modes

#### Scenario: A receipt written before the declaration

- **WHEN** a receipt records no mode and its command passes `--experimental-fast-capture`
- **THEN** validation reads it as `fast`, and the picture validates for a film that declares no capture
