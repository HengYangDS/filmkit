## ADDED Requirements

### Requirement: The 1080p films are encoded in software on a forced keyframe grid

Packaging SHALL encode each 1080p film with the x264 encoder at a constant rate factor, without B-frames, with the keyframe interval and its minimum both set to 120 frames and scene-cut keyframes off, and with no hardware decoder or encoder, so that where its keyframes stand depends on its options alone.

#### Scenario: A 1080p film's encode command

- **WHEN** packaging builds the encode command of a 1080p film
- **THEN** the command names the encoder `libx264`, a constant rate factor, `-bf` of 0, `-g` and `-keyint_min` of 120 and `-sc_threshold` of 0, and names no VideoToolbox decoder or encoder

#### Scenario: A short film encoded with those options

- **WHEN** a film of four seconds at 60 frames per second is encoded with the 1080p options
- **THEN** its keyframes stand at frames 0 and 120 and at no other frame

### Requirement: No picture or film holds B-frames

Every rendered picture, derived picture and delivered film SHALL hold its frames in the order they are shown, without B-frames, as every film delivered before does. The validation of a picture, packaging's check of a finished film and the verifier's check of a delivered film SHALL each refuse a picture stream for which FFprobe reports B-frames.

#### Scenario: The four films of a derived pair

- **WHEN** a captioned picture, the picture derived from it and the four films packaged from the pair are made by the engine's commands
- **THEN** FFprobe reports no B-frames in the derived picture or in any of the four films, and packaging's check and the verifier's pass each film

#### Scenario: A film encoded with B-frames

- **WHEN** a 1080p film is encoded with x264's default B-frames
- **THEN** packaging refuses the finished film and links none into place, and the verifier refuses the same file, naming B-frames

#### Scenario: A derived picture with B-frames

- **WHEN** a derived picture's stream holds B-frames
- **THEN** its validation refuses it, naming B-frames

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
