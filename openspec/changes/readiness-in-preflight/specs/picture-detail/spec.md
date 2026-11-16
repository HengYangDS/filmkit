## ADDED Requirements

### Requirement: The detail audit follows every frame of the film

The detail audit SHALL run the composition headlessly on the edition's timeline through every frame at 60 frames per second and SHALL report each ink drop, each stretch of a text outside scenes over the pace line, each stroke part-drawn in a quiet, each racing tip and each rail on two baselines with its clearance, with the lines it judges by: the pace line, the racing pace and the clearance of a rail.

#### Scenario: The sample film

- **WHEN** the audit runs on the sample film's English edition
- **THEN** its report covers every frame at 60 frames per second, lists no finding and states 450 px/s, 900 px/s and 48 px as its lines

#### Scenario: A malformed invocation

- **WHEN** the audit is given no timeline, a frame rate that is no number or a range that holds no frame
- **THEN** it exits with status 2 and its usage, and writes no report

### Requirement: A line that loses part of its ink within one frame is found

The audit SHALL follow, for each draw call of a scene, the pieces of its solid strokes at opacity 0.5 or more that are 8 px or longer, and SHALL report an ink drop where a piece is replaced by shorter ones and the call loses 30 px or more within one frame, while the frames before and after lose 3 px or less in that call. It SHALL count apart a loss on the frame of a stage cut the scene declares.

#### Scenario: A path that opens

- **WHEN** a 600 px line of a scene is drawn as two pieces with a 60 px gap from one frame on
- **THEN** the audit reports one ink drop at that frame, of 60 of 600 px, with the scene and the line of the composition that drew it

#### Scenario: A stroke drawn off

- **WHEN** a line shortens by 8 px in every frame, or by 40 px in each of five consecutive frames
- **THEN** the audit reports no ink drop

#### Scenario: A piece that leaves whole

- **WHEN** one of two pieces of a draw call is no longer drawn and the other stands
- **THEN** the audit reports no ink drop, since a piece that leaves whole is the motion audit's to judge

#### Scenario: A split on a declared stage cut

- **WHEN** a line splits on the frame of a stage cut that its scene declares
- **THEN** the audit reports no ink drop and counts the loss among those at cuts

### Requirement: A text outside every scene is held to the pace

The audit SHALL follow each text that no scene draws, a caption apart, at opacity above 0.2, by its words from frame to frame within 60 px, and SHALL report each stretch of two frames or more in which its centre moves over 450 px/s, with its span, its fastest speed and its way. The picture gate SHALL refuse a stretch at 900 px/s or more, and a slower one only over the pace limit the film declares.

#### Scenario: A chapter title that races to the running head

- **WHEN** a title outside the scenes travels 1,200 px in one second
- **THEN** the audit reports one stretch at 1,200 px/s and the gate refuses it whatever pace limit the film declares

#### Scenario: A title over the pace line of a film that declares a limit

- **WHEN** a title moves at 610 px/s and the film declares a pace limit of 450 px/s
- **THEN** the gate refuses the stretch; with a limit of 700 px/s, or none, the gate records it

#### Scenario: A card that fades into its running head

- **WHEN** the same words stand on a card and 500 px away in the running head while one fades into the other
- **THEN** the audit reports no stretch

### Requirement: A stroke rests whole in a quiet

The audit SHALL read the strokes a composition publishes with each frame's layout, each with its scene, its cue, the share of its way it has reached and its tip's pace. It SHALL report a stroke whose share stands between 0 and 1 at the middle of the quiet between two thoughts of a segment, and a stroke whose tip draws at 900 px/s or more. The gate SHALL record a composition that publishes none as not judged.

#### Scenario: A bracket caught part-drawn

- **WHEN** a stroke keyed on a thought's last word is three fifths drawn at the middle of the quiet after that thought
- **THEN** the audit reports it with the thought, the quiet's span, its scene, its cue and the share 0.6

#### Scenario: A tip that races

- **WHEN** a published stroke draws with its tip at 950 px/s
- **THEN** the audit reports a racing tip with its scene, its cue and 950 px/s

#### Scenario: A composition that publishes no strokes

- **WHEN** a composition publishes no drawn strokes
- **THEN** the audit reports that none are published, and the gate record says that no stroke was judged in a quiet or by its tip's pace

### Requirement: Names on a rail's two baselines keep their clearance

The audit SHALL read, at the rest of every thought, each list of names of one scene and one set that stand at opacity 0.5 or more on exactly two lines and alternate between them, and SHALL report its least clearance between consecutive names: the gap across where they stand side by side, the gap down where one reaches under the other, and the diagonal otherwise. The gate SHALL refuse a rail under 48 px.

#### Scenario: A long name that reaches under its neighbour

- **WHEN** the second of three names stands 14 px below the first and reaches 20 px under it
- **THEN** the audit reports the rail with a clearance of 14 px between those two names at that thought, and the gate refuses it

#### Scenario: A list on one row, or wrapped onto two rows

- **WHEN** the names of a list stand on one line, or two and two on two lines without alternating
- **THEN** the audit reports no rail

### Requirement: A film declares the detail findings it keeps

A film MAY declare, for an edition, a finding of the detail audit or a run far off centre by its kind, its scene and a reason, and MAY name its source within the scene. The gate SHALL record a finding that an exception of its edition names, with the reason, instead of refusing it, and SHALL refuse an exception that matches no finding of its edition. The declaration SHALL be refused without a reason or with a source its kind cannot carry.

#### Scenario: A rail kept at its narrow row

- **WHEN** a film declares the rail of one list in one scene of its Chinese edition with a reason, and the Chinese audit reports that rail at 13.8 px
- **THEN** the gate passes and its record lists the rail with the reason

#### Scenario: The same rail in the other edition

- **WHEN** the English audit reports the rail and only the Chinese edition declares it
- **THEN** the English gate refuses the rail

#### Scenario: A repaired finding

- **WHEN** a declared rail stands 50 px clear after a repair
- **THEN** the gate refuses the exception as stale

#### Scenario: A source the kind cannot carry

- **WHEN** a declaration names a source for a racing tip, or a side other than left or right for a run far off centre
- **THEN** the declaration is refused, naming the kind and the source
