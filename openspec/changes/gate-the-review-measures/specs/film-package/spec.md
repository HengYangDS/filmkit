## ADDED Requirements

### Requirement: A rebuilt film that holds the published bytes is not decoded

The comparison SHALL report a rebuilt film whose size and SHA-256 equal those the release manifest records for its published film as an identical file, without decoding either film: its frame count, decoded audio and container hold, and its PSNR is reported as not measured. Such a film SHALL NOT pass without a recorded floor, and the report SHALL state that it calibrates none. A rebuilt film that differs in any byte SHALL be decoded and compared in every layer.

#### Scenario: A rebuilt film that holds the published bytes

- **WHEN** a rebuilt film has its published film's size and SHA-256 and the manifest records its floor
- **THEN** no frame or audio of it is decoded, and its report names an identical file, a PSNR that is not measured and a pass

#### Scenario: An identical file without a floor

- **WHEN** a rebuilt film holds its published film's bytes and the manifest records no floor for it
- **THEN** its report measures no minimum, states that it calibrates no floor, and the comparison does not pass

#### Scenario: A rebuilt film that differs by one byte

- **WHEN** a rebuilt film has its published film's size and one byte that differs
- **THEN** both films are decoded and every layer is compared as before
