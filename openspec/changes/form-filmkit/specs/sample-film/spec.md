## ADDED Requirements

### Requirement: The repository builds a sample film

The repository SHALL carry a short bilingual sample film whose tracked sources and declared supply let the engine build it end to end on Apple-silicon macOS, offline after the supply step, writing only below the sample's `build/` folder.

#### Scenario: The sample film builds and verifies

- **WHEN** the supply step and then the sample's build run on Apple silicon
- **THEN** both editions' recordings, soundtracks, captions, pictures and packaged films are produced below the sample's `build/`
- **AND** the technical verification of both editions passes

### Requirement: The engine's tests load only the sample film

The engine's tests SHALL load the sample film as the film the engine builds, and no test SHALL read another film's sources.

#### Scenario: The suites run without another film

- **WHEN** the engine's Python and Node suites run in a checkout of this repository alone
- **THEN** every test that loads a film loads the sample film, and the suites pass
