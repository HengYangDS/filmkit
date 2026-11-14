## MODIFIED Requirements

### Requirement: The repository builds a sample film

The repository SHALL carry a short bilingual sample film whose tracked sources and declared supply let the engine build it end to end on Apple-silicon macOS, offline after the supply step, writing only below the sample's `build/` folder. Its build SHALL pass the sound gate on each edition's soundtrack before any picture is staged.

#### Scenario: The sample film builds and verifies

- **WHEN** the supply step and then the sample's build run on Apple silicon
- **THEN** both editions' recordings, soundtracks, captions, pictures and packaged films are produced below the sample's `build/`
- **AND** the technical verification of both editions passes

#### Scenario: The sample's soundtracks pass the sound gate

- **WHEN** the sample's sound stage has assembled an edition's soundtrack and written its captions
- **THEN** `check-sound` records a pass for that edition before its picture stage runs
