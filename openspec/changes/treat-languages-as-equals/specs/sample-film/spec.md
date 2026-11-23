## ADDED Requirements

### Requirement: The sample film lays out its editions as equals

Each of the sample's editions SHALL keep its files in the folder of its code, and its reference recording and its cover under names that carry its code; no file of one edition SHALL stand among the files that both editions share.

#### Scenario: The sample's tracked files

- **WHEN** the sample's tracked files are listed
- **THEN** each edition's script, cast, pronunciation and readings stand in `content/zh/` or `content/en/`, its reference recording in `assets/audio/zh/` or `assets/audio/en/`, and its cover's name ends in `-zh.png` or `-en.png`
- **AND** every other file below `content/` is one that both editions share: the declaration, the concept contract, the entry page, the source manifest and the review prompt

#### Scenario: The sample holds what its engine asks

- **WHEN** the engine loads the sample and `python -m filmkit.adoption` runs at it
- **THEN** the engine refuses nothing, and the command's questions `declaration` and `editions` report no finding

## MODIFIED Requirements

### Requirement: The repository builds a sample film

The repository SHALL carry a short sample film of two editions, Chinese and English, laid out as equals, whose tracked sources and declared supply let the engine build it end to end on Apple-silicon macOS, offline after the supply step, writing only below the sample's `build/` folder. Its build SHALL pass the sound gate on each edition's soundtrack before any picture is staged.

#### Scenario: The sample film builds and verifies

- **WHEN** the supply step and then the sample's build run on Apple silicon
- **THEN** both editions' recordings, soundtracks, captions, pictures and packaged films are produced below the sample's `build/`
- **AND** the technical verification of both editions passes

#### Scenario: The sample's soundtracks pass the sound gate

- **WHEN** the sample's sound stage has assembled an edition's soundtrack and written its captions
- **THEN** `check-sound` records a pass for that edition before its picture stage runs
