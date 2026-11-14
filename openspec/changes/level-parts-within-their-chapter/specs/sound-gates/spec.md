## ADDED Requirements

### Requirement: A film declares how closely each segment keeps its chapter's level

A script's voice performance MAY declare `segment_level_tolerance_db` from 0.1 to 3.0. The assembly SHALL then move a segment whose leveled thoughts' median loudness stands farther than that from the median over its chapter's leveled thoughts to the edge of the tolerance, by one static gain of at most 2 dB that keeps the segment's peak below −1 dBFS, before it levels the chapters, and SHALL record each segment's gain. The engine SHALL refuse a value outside the range.

#### Scenario: A segment that stands under its chapter is raised

- **WHEN** a script declares a segment-level tolerance of 0.2 dB and one of a chapter's three segments stands 0.8 dB under the chapter's median
- **THEN** that segment is assembled 0.6 dB louder, its record holds the gain, and the other two segments keep their level

#### Scenario: A film that declares nothing

- **WHEN** a script declares no segment-level tolerance
- **THEN** the soundtrack and the timeline hold the bytes the previous release assembled, every record's segment gain is 0, and the receipt's policy holds no tolerance

#### Scenario: A value outside the range refuses

- **WHEN** a script declares a segment-level tolerance of 0.05 dB
- **THEN** the engine refuses the policy and names the range from 0.1 to 3.0
