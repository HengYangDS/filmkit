## REMOVED Requirements

### Requirement: A film declares how its picture is captured

**Reason**: the declaration set the browser and capture flags of every render and each receipt recorded the mode. A native render starts no browser and passes no such flag. "A film's declared capture decides how its uncaptioned picture is made" keeps the declaration for the one thing that still reads it.

**Migration**: a film keeps its `[picture] capture` line. A picture rendered by an earlier engine is rendered again: its receipt names no canvas, and `native-picture` refuses it at validation.

## ADDED Requirements

### Requirement: A film's declared capture decides how its uncaptioned picture is made

A film MAY declare `[picture] capture` as `fast`, `screenshot` or `software`; one that declares none declares `fast`. The declaration SHALL decide only whether the uncaptioned picture is derived from the captioned one, which `software` asks for, or drawn from its own stage. No render SHALL read it: a renderer command passes no browser or capture flag, and a receipt records no capture.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture loads
- **THEN** its capture is `fast`, and its uncaptioned picture is drawn from its own stage

#### Scenario: Another capture value

- **WHEN** the declaration gives `capture = "drawelement"`
- **THEN** the engine refuses when it loads, naming `picture.capture`

#### Scenario: Renders under each capture

- **WHEN** films that declare `fast`, `screenshot` and `software` render their captioned pictures and their drafts
- **THEN** their renderer commands are the same apart from their paths, and no receipt records a capture
