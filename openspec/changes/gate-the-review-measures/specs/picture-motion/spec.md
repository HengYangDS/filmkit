## ADDED Requirements

### Requirement: The motion audit records glides over the pace line and a film may gate them

The motion audit SHALL record each stretch of consecutive frames in which marks of one scene glide or flow over 450 px/s at 1080p as one finding, with its scene, start and end, peak speed and its time, and the fastest mark's line. A film MAY declare `picture.motion.pace_limit` from 450 to under 900 px/s; `check-picture` SHALL refuse a stretch whose peak exceeds the declared limit and SHALL record every other stretch.

#### Scenario: A stretch without a declared limit

- **WHEN** a name eases 320 px in 0.8 s and the film declares no pace limit
- **THEN** one stretch is recorded at 599 px/s and the picture is not refused for it

#### Scenario: A stretch over the declared limit

- **WHEN** the film declares a pace limit of 450 px/s and a price glides at up to 708 px/s
- **THEN** `check-picture` refuses, naming the scene, the time, the peak and the line that drew the mark

#### Scenario: A stage and what it carries

- **WHEN** a stage glides over the line with the marks it carries and a dot moving within it
- **THEN** one stretch is recorded, by its fastest mark

#### Scenario: A kept stretch

- **WHEN** an exception of kind pace names the stretch's scene and line with a reason
- **THEN** the stretch is recorded with the reason and not refused
