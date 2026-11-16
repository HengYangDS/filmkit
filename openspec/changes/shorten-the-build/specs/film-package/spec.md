## ADDED Requirements

### Requirement: The 1080p films are encoded in software on a forced keyframe grid

Packaging SHALL encode each 1080p film with the x264 encoder at a constant rate factor, with the keyframe interval and its minimum both set to 120 frames and scene-cut keyframes off, and with no hardware decoder or encoder, so that where its keyframes stand depends on its options alone.

#### Scenario: A 1080p film's encode command

- **WHEN** packaging builds the encode command of a 1080p film
- **THEN** the command names the encoder `libx264`, a constant rate factor, `-g` and `-keyint_min` of 120 and `-sc_threshold` of 0, and names no VideoToolbox decoder or encoder

#### Scenario: A short film encoded with those options

- **WHEN** a film of four seconds at 60 frames per second is encoded with the 1080p options
- **THEN** its keyframes stand at frames 0 and 120 and at no other frame
