# picture-motion Specification

## Purpose

Follow every mark of an edition's picture as a viewer sees it move, refuse the motion a viewer sees as not smooth before a render, and report the motion of each edition to its reviews.

## Requirements

### Requirement: The motion audit follows every mark as a viewer sees it move

The motion audit SHALL follow each mark a scene draws at ink level 25 or more from frame to frame: by moving whole at nearly the same size, or by growing, shrinking or redrawing in place or while it moves, as the like mark of its scene, kind and words that its own motion predicts best. A text whose words change in place SHALL continue. A mark SHALL rest only where its box and its drawn pieces both stand. Speeds SHALL be measured in 1080p pixels per second.

#### Scenario: A mark drawn at new coordinates in every frame

- **WHEN** a flow's dot is drawn 10 px further along its link in each frame at 30 fps
- **THEN** the audit follows it as one mark moving at 300 px/s

#### Scenario: A mark that grows while it moves

- **WHEN** a link draws on from a mark that glides, so its box both grows and shifts in each frame
- **THEN** the audit follows the link as one mark and reports no pop for it

#### Scenario: A dot that enters and leaves by size

- **WHEN** a flow's dot shrinks to nothing at the end of its link as another grows from nothing at its start
- **THEN** the audit reports no race between them

#### Scenario: A link drawn on from a start that glides

- **WHEN** a link draws on from a start that glides and its tip turns a corner, so its box stops shifting while its start goes on
- **THEN** the audit reports no halt and no start for it

#### Scenario: A row that grows a piece at its end

- **WHEN** a row of squares glides while a square grows in at its end every ten frames
- **THEN** the audit reports no halt and no start for the row

#### Scenario: A link that turns a corner as its start rises through it

- **WHEN** a link drawn on from a rising start turns from a vertical stub into a horizontal line within one frame
- **THEN** the audit follows it as one mark and reports no pop for it

#### Scenario: Outlines that crossfade on a gliding box

- **WHEN** a box's dashed outline gives way to a solid one while the box glides
- **THEN** the audit reports no pop for either outline

### Requirement: The picture gate refuses motion a viewer sees as not smooth

`check-picture` SHALL refuse, outside a stage cut, `motion_halts`, a mark falling from 60 px/s or more to under 1.5 px/s within one frame, unless that step is under half its last; `motion_starts`, the reverse, for a mark followed two frames or more; `motion_races`, a mark at 900 px/s or more; and `motion_pops`, a mark at ink 60 or more appearing or vanishing within one frame with pieces 12 px or more across that no like mark holds. Each SHALL name its time, scene, kind, words and drawing line.

#### Scenario: A flow that halts dead at the end of a thought

- **WHEN** a dot moving at 240 px/s stands still in the next frame
- **THEN** `check-picture` writes a refused record that names the halt with its time, scene and line, and exits with a refusal

#### Scenario: An eased end

- **WHEN** a dot eases to rest, its last steps 90 px/s and then 40 px/s before it stands still
- **THEN** `check-picture` refuses no halt for it

#### Scenario: A structure that glides too fast

- **WHEN** a row re-centres at a peak of 1,900 px/s
- **THEN** `check-picture` refuses a race and names its peak speed

#### Scenario: A name that pops in

- **WHEN** a name appears at full ink within one frame while the rest of its scene stands
- **THEN** `check-picture` refuses a pop that names the text

#### Scenario: A slab that joins its stack

- **WHEN** a slab eases down onto a stack of like slabs and is then drawn as part of the stack
- **THEN** `check-picture` refuses no pop for it

### Requirement: A stage cut is the one place where marks may change at once

A frame SHALL be a stage cut for a scene when at least 35% of the scene's marks at ink level 60 or more, counted or weighed by their ink, vanish or appear within it, or when the composition declares a cut of the scene in it. The audit SHALL NOT follow a mark across a stage cut and SHALL report no pop as a scene enters or leaves the picture. A declared cut that changes less than that 35% SHALL excuse the marks it takes away and SHALL NOT excuse the marks it brings.

#### Scenario: A stage handed to the next on a word

- **WHEN** 36 of a scene's 41 firm marks vanish within one frame while a large frame of the scene stays
- **THEN** the audit reports no pop for them

#### Scenario: A cut the composition declares

- **WHEN** the composition declares a stage cut on a word where 20 of the scene's 24 firm marks give way to 18 others
- **THEN** the audit reports no pop for them

#### Scenario: A mark beside a standing picture

- **WHEN** one card appears within one frame among 30 standing marks
- **THEN** the audit reports its marks as pops

#### Scenario: A mark brought into a standing stage at a declared cut

- **WHEN** one name gives way to another at a cut the composition declares while the scene's 30 other firm marks stand
- **THEN** the audit reports the arriving name as a pop and no pop for the name that leaves

### Requirement: A finding names the scene line that drew it

Each motion finding SHALL name the line of the composition that drew its mark: the innermost line of a scene's own code on the call stack, a scene's body or a module the bundle places in a folder below `scenes/`, rather than a shared helper, or else the innermost line of the composition. Where the composition is bundled from modules, the finding SHALL also name the module.

#### Scenario: A mark drawn by a shared helper

- **WHEN** a scene module's line calls a shared drawing helper that paints a ring that pops
- **THEN** the pop names the scene module's line and module, not the helper's

### Requirement: A film declares the motion it keeps

A film MAY declare `[[picture.motion.exceptions]]` in `content/film.toml`, each with its edition, scene, source, the composition line as `film.js:<line>` or its module, kind (`halt`, `start`, `race`, `pop`, `jump` or `dash`) and reason. A finding that an exception matches SHALL be recorded with the reason and SHALL NOT refuse; an exception that matches no finding of its edition SHALL be refused.

#### Scenario: A declared beat

- **WHEN** the film declares a pop of scene 06 from the module that draws a beat ring, with its reason
- **THEN** `check-picture` records that pop with the reason and does not refuse it

#### Scenario: A stale exception

- **WHEN** an exception matches no finding of its edition
- **THEN** `check-picture` refuses and names the stale exception

### Requirement: The audit records the speeds a viewer meets

The motion audit SHALL record, for each scene, the largest speed of a glide, the motion of a mark more than 16 px across or of a text, and of a flow, the motion of a smaller mark, each with when it occurs.

#### Scenario: A scene with a flow and a glide

- **WHEN** a scene's dots flow at 240 px/s and its row glides at a peak of 520 px/s
- **THEN** the audit records a flow of 240 px/s and a glide of 520 px/s for that scene

### Requirement: The review's measurements report each edition's motion

`review.measurement` SHALL record each edition's motion from its picture gate record: the counts of halts, starts, races, pops, jumps and dash snaps, the declared ones apart, the largest speeds per scene and each finding with its time. It SHALL refuse a gate record or motion report that is not bound to the current composition and timeline.

#### Scenario: A current gate record

- **WHEN** the edition's gate record names the current composition and timeline
- **THEN** the measurement records the motion counts, speeds and findings for the reviewers

#### Scenario: A composition changed after its check

- **WHEN** the composition changed after `check-picture` wrote the record
- **THEN** the measurement refuses and names the edition's gate record

### Requirement: The marks a cut keeps go on as they went

At a stage cut the audit SHALL report a jump for a scene when its marks at ink 60 or more that the cut keeps, matched across the frame at one size, moved whole by one shift of 8 px or more beyond the shift each moved by in the frame before, to within 2 px, and hold at least half of the scene's firm ink before the cut. `check-picture` SHALL refuse a jump as `motion_jumps`, naming its time, scene, shift and marks, unless the film declares it.

#### Scenario: A field and its name moved at a cut

- **WHEN** at a declared cut a square and its heading, the scene's only firm marks, both move 354 px left within one frame
- **THEN** the audit reports one jump of 354 px for the scene and `check-picture` refuses it

#### Scenario: A cut that keeps its rail in place

- **WHEN** a cut replaces a scene's names while its rail stands where it stood
- **THEN** the audit reports no jump

#### Scenario: A stage gliding through a cut

- **WHEN** a field and its name glide 12 px a frame before, at and after a cut the composition declares
- **THEN** the audit reports no jump

#### Scenario: A heading moved while its stage is replaced

- **WHEN** at a cut a heading moves 200 px while the scene's 12 other firm marks give way to new ones
- **THEN** the audit reports no jump, since the heading holds less than half of the scene's firm ink

### Requirement: A stroke's dashes open and close over time

The headless composition SHALL record each stroke's dash pattern, and the audit SHALL report a dash snap when a stroke it follows at ink 25 or more, outside a stage cut, changes the share of its pattern that is gap by 0.25 or more within one frame. `check-picture` SHALL refuse a dash snap as `motion_dash_snaps`, naming its time, scene and line, unless the film declares it.

#### Scenario: A join that turns dashed at once

- **WHEN** a solid link turns into dashes of 8 px on and 8 px off within one frame
- **THEN** the audit reports a dash snap and `check-picture` refuses it

#### Scenario: A join that breaks over a third of a second

- **WHEN** a solid link's gaps open from 0 to 8 px of each 16 px over 0.35 s
- **THEN** the audit reports no dash snap

#### Scenario: A dashed way drawn on

- **WHEN** a dashed way of one pattern draws on along its length
- **THEN** the audit reports no dash snap

#### Scenario: A dashed outline crossfading into a solid one

- **WHEN** a dashed outline fades out while a solid one fades in on the same box
- **THEN** each continues the outline of its own pattern and the audit reports no dash snap

### Requirement: A followed mark pops by a piece it gains or loses whole

Outside a stage cut, a mark the motion audit follows SHALL also pop by each drawn piece it gains or loses within one frame, at ink 60 or more and 12 px or more across, that no piece of the other frame continues and no like mark there holds. A piece SHALL continue one drawn from or ending at its point, or a closed piece one at its centre, under the shift that pairs most pieces, or one that moves as a mark of its own. `check-picture` SHALL refuse it as `motion_pops`, naming the drawing line.

#### Scenario: Lines that join a stroke whole

- **WHEN** one stroke draws three links whose first inks in over 0.3 s, and its second link joins the stroke whole at full ink in one frame while the first stands
- **THEN** `check-picture` refuses a pop for the second link that names the stroke's drawing line

#### Scenario: A piece drawn on

- **WHEN** a stroke's second link draws on from its first point, under 12 px long in its first frame
- **THEN** the audit reports no pop for it

#### Scenario: A piece that turns a corner

- **WHEN** a link drawn on from a rising start turns from a vertical stub into a horizontal line within one frame
- **THEN** the audit continues its piece from its first point and reports no pop for it

#### Scenario: A path split at a gap

- **WHEN** a path stroke splits into two pieces where a station's gap opens, the second piece ending where the path ended
- **THEN** the audit continues the second piece from that end and reports no pop for it

#### Scenario: A tick that moves on its own inside one stroke

- **WHEN** one stroke draws a ruler and a tick that slides along it, the tick moving by more than the ruler's shift
- **THEN** the audit continues the tick as a piece that moves with a mark of its own and reports no pop for it
