## ADDED Requirements

### Requirement: The 1080p films are encoded in software on a forced keyframe grid

Packaging SHALL encode each 1080p film with the x264 encoder at a constant rate factor, with the keyframe interval and its minimum both set to 120 frames and scene-cut keyframes off, and with no hardware decoder or encoder, so that where its keyframes stand depends on its options alone.

#### Scenario: A 1080p film's encode command

- **WHEN** packaging builds the encode command of a 1080p film
- **THEN** the command names the encoder `libx264`, a constant rate factor, `-g` and `-keyint_min` of 120 and `-sc_threshold` of 0, and names no VideoToolbox decoder or encoder

#### Scenario: A short film encoded with those options

- **WHEN** a film of four seconds at 60 frames per second is encoded with the 1080p options
- **THEN** its keyframes stand at frames 0 and 120 and at no other frame

## MODIFIED Requirements

### Requirement: Each edition delivers its films with and without captions

Each edition SHALL deliver four films: `uhd` and `1080p-captioned`, which show its captioned picture, and `uhd-uncaptioned` and `1080p-uncaptioned`, which show its uncaptioned one, with one soundtrack, chapters, release metadata and cover. The film package SHALL bind both pictures and their equivalence record, and each film SHALL name the picture it shows and the picture file its encode read: its own picture, but the captioned one, painted, for the `1080p-uncaptioned` film of a derived pair.

#### Scenario: An edition packaged

- **WHEN** an edition with both pictures compared is packaged
- **THEN** its folder holds the four films, and its package names each film's picture

#### Scenario: A derived pair packaged

- **WHEN** an edition whose uncaptioned picture is derived is packaged
- **THEN** its `1080p-uncaptioned` film is recorded as showing the uncaptioned picture and as read from the captioned picture's file, and every other film as read from the file of the picture it shows

#### Scenario: A record that names another file

- **WHEN** a film's record names another picture file than the one its encode reads as the pictures stand
- **THEN** the verifier refuses the film package
