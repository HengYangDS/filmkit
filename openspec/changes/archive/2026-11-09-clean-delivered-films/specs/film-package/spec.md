## ADDED Requirements

### Requirement: A delivered film names its author once

Every delivered film SHALL carry its author in one QuickTime key, Author, beside its item-list artist and album-artist tags, so that an index which reads every author-bearing QuickTime key lists the author once. Packaging SHALL refuse a finished film, and the verifier a delivered film, that carries a QuickTime key outside its release's keys and its creation date.

#### Scenario: A film's authors in Spotlight

- **WHEN** Spotlight imports a delivered film
- **THEN** the film's authors list Yang HENG once

#### Scenario: A film with a second author key

- **WHEN** a finished film carries the QuickTime key Artist
- **THEN** packaging refuses it as differing from the delivery contract, and the verifier refuses it once delivered

### Requirement: The 1080p films keep the master's strokes

Each 1080p film SHALL show its UHD picture averaged over blocks of 2×2 pixels, so that a stroke carries no fringe or lifted white that the master lacks.

#### Scenario: A stroke on the dark ground

- **WHEN** a frame of a 1080p film is compared with the same frame of its UHD film averaged over 2×2 blocks
- **THEN** fewer than 2 % of the ground pixels within 3 px of ink are more than 8 levels darker than the ground, and the brightest 0.5 % of its ink stands within 4 levels of the master's

### Requirement: The 1080p films hold a keyframe every 2 seconds

Each 1080p film SHALL hold a keyframe at every 120th frame from its first frame and at no other frame, and packaging and the verifier SHALL refuse a 1080p film whose keyframes fall elsewhere.

#### Scenario: The encoder's default interval

- **WHEN** a 1080p film holds a keyframe every 12 frames
- **THEN** packaging refuses it as differing from the delivery contract, and the verifier refuses it once delivered

#### Scenario: A film keyed every 2 seconds

- **WHEN** a 1080p film's keyframes stand at frames 0, 120, 240 and every 120th frame after them
- **THEN** its keyframes meet the delivery contract
