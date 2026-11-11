## ADDED Requirements

### Requirement: A film declares how its picture is captured

A film MAY declare `[picture] capture` as `fast` or `screenshot`; a film that declares none captures `fast`. Every render of its picture SHALL pass the renderer's fast capture explicitly on for `fast`, as earlier releases did, and explicitly off for `screenshot`. Each render receipt SHALL record the mode, and validation SHALL refuse a picture whose receipt records another mode than the declaration, reading a receipt that records none by its command.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture renders its captioned or uncaptioned picture
- **THEN** the renderer command is, element for element, the command that filmkit 0.19.0 runs, and the receipt records `fast`

#### Scenario: A film that declares screenshot capture

- **WHEN** a film declares `capture = "screenshot"` and renders its pictures and its draft
- **THEN** each command passes `--experimental-fast-capture=false` where `fast` passes `--experimental-fast-capture`, and each receipt records `screenshot`

#### Scenario: Another capture value

- **WHEN** the declaration gives `capture = "drawelement"`
- **THEN** the engine refuses when it loads, naming `picture.capture`

#### Scenario: A picture rendered in another mode

- **WHEN** a film declares screenshot capture and its picture's receipt records `fast`
- **THEN** validation refuses the picture, naming both modes

#### Scenario: A receipt written before the declaration

- **WHEN** a receipt records no mode and its command passes `--experimental-fast-capture`
- **THEN** validation reads it as `fast`, and the picture validates for a film that declares no capture
