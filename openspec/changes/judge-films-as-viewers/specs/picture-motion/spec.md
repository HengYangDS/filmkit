## Purpose

Follow every mark of an edition's picture as a viewer sees it move, refuse the motion a viewer sees as not smooth before a render, and report the motion of each edition to its reviews.

## ADDED Requirements

### Requirement: The motion audit follows every mark as a viewer sees it move

The motion audit SHALL follow each mark a scene draws at ink level 25 or more from frame to frame: by moving whole at nearly the same size, or by growing, shrinking or redrawing in place or while it moves, as the like mark of its scene, kind and words that its own motion predicts best. A text whose words change in place SHALL continue. Speeds SHALL be measured in 1080p pixels per second.

#### Scenario: A mark drawn at new coordinates in every frame

- **WHEN** a flow's dot is drawn 10 px further along its link in each frame at 30 fps
- **THEN** the audit follows it as one mark moving at 300 px/s

#### Scenario: A mark that grows while it moves

- **WHEN** a link draws on from a mark that glides, so its box both grows and shifts in each frame
- **THEN** the audit follows the link as one mark and reports no pop for it

#### Scenario: A dot that enters and leaves by size

- **WHEN** a flow's dot shrinks to nothing at the end of its link as another grows from nothing at its start
- **THEN** the audit reports no race between them

### Requirement: The picture gate refuses motion a viewer sees as not smooth

`check-picture` SHALL refuse `motion_halts`, a mark whose speed falls from 60 px/s or more to under 1.5 px/s within one frame; `motion_starts`, the reverse, for a mark followed for two frames or more; `motion_races`, a mark at 900 px/s or more; and `motion_pops`, a mark at ink level 60 or more and 12 px or more across that appears or vanishes within one frame, continuing no like mark, outside a stage cut. Each SHALL name its time, scene, kind, words and the line that drew it.

#### Scenario: A flow that halts dead at the end of a thought

- **WHEN** a dot moving at 240 px/s stands still in the next frame
- **THEN** `check-picture` writes a refused record that names the halt with its time, scene and line, and exits with a refusal

#### Scenario: A structure that glides too fast

- **WHEN** a row re-centres at a peak of 1,900 px/s
- **THEN** `check-picture` refuses a race and names its peak speed

#### Scenario: A name that pops in

- **WHEN** a name appears at full ink within one frame while the rest of its scene stands
- **THEN** `check-picture` refuses a pop that names the text

### Requirement: A stage cut is the one place where marks may change at once

A frame SHALL be a stage cut for a scene when at least 35% of the scene's marks at ink level 60 or more, counted or weighed by their ink, vanish or appear within it. The audit SHALL NOT follow a mark across a stage cut, and SHALL report no pop in it or as the scene enters or leaves the picture.

#### Scenario: A stage handed to the next on a word

- **WHEN** 36 of a scene's 41 firm marks vanish within one frame while a large frame of the scene stays
- **THEN** the audit reports no pop for them

#### Scenario: A mark beside a standing picture

- **WHEN** one card appears within one frame among 30 standing marks
- **THEN** the audit reports its marks as pops

### Requirement: A finding names the scene line that drew it

Each motion finding SHALL name the line of the composition that drew its mark: the innermost line of a scene's own code on the call stack, a scene's body or a module the bundle places in a folder below `scenes/`, rather than a shared helper, or else the innermost line of the composition. Where the composition is bundled from modules, the finding SHALL also name the module.

#### Scenario: A mark drawn by a shared helper

- **WHEN** a scene module's line calls a shared drawing helper that paints a ring that pops
- **THEN** the pop names the scene module's line and module, not the helper's

### Requirement: A film declares the motion it keeps

A film MAY declare `[[picture.motion.exceptions]]` in `content/film.toml`, each with its edition, scene, source, the composition line as `film.js:<line>` or its module, kind (`halt`, `start`, `race` or `pop`) and reason. A finding that an exception matches SHALL be recorded with the reason and SHALL NOT refuse; an exception that matches no finding of its edition SHALL be refused.

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

`review.measurement` SHALL record each edition's motion from its picture gate record: the counts of halts, starts, races and pops, the declared ones apart, the largest speeds per scene and each finding with its time. It SHALL refuse a gate record or motion report that is not bound to the current composition and timeline.

#### Scenario: A current gate record

- **WHEN** the edition's gate record names the current composition and timeline
- **THEN** the measurement records the motion counts, speeds and findings for the reviewers

#### Scenario: A composition changed after its check

- **WHEN** the composition changed after `check-picture` wrote the record
- **THEN** the measurement refuses and names the edition's gate record
