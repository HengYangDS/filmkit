## ADDED Requirements

### Requirement: A composition declares the strokes that only frame a stage

A composition MAY declare a stroke drawn only to frame a stage, a declared frame stroke, by setting `window.__paintRole` to `"frame"` while it strokes it and back to `null` after. The headless audits SHALL record the role on each paint as they record its scene. The frame audit SHALL report as an error a role of another value, and a role in effect while `fill`, `fillText` or `fillRect` is called. The renderer SHALL draw a declared frame stroke as any other stroke.

#### Scenario: A declared rail

- **WHEN** a composition strokes two rails with `window.__paintRole` set to `"frame"` and its names with it `null`
- **THEN** the rails' paints carry the role `frame` and the names' paints carry none

#### Scenario: A misspelt role

- **WHEN** a composition sets `window.__paintRole` to `"frmae"` while it paints
- **THEN** the frame audit reports an error naming the value, and `check-picture` refuses

#### Scenario: A rail drawn as a fill

- **WHEN** a composition calls `fillRect`, or `fill` on a rectangular path, with `window.__paintRole` set to `"frame"`
- **THEN** the frame audit reports an error that only a stroke can be a declared frame stroke, and `check-picture` refuses

#### Scenario: The picture does not change

- **WHEN** the same stage is rendered with and without its frame strokes declared
- **THEN** both renders state the same drawn-frame digest

### Requirement: The frame audit records the declared frame strokes

The frame audit SHALL record per scene the declared frame strokes it leaves out of the reviewers' box, with their number and the box they span, and the picture gate SHALL refuse nothing for them.

#### Scenario: Two declared rails

- **WHEN** a scene strokes two rails declared as frames
- **THEN** the frame report records two declared frame strokes for that scene with the box they span, and `check-picture` refuses nothing for them

### Requirement: The other frame measures count what they counted

Every measure of the frame audit other than the reviewers' box runs, the vertical runs and the mass SHALL count declared frame strokes and paints outside every scene as any other paint.

#### Scenario: A declared rail and the cover

- **WHEN** the same stage is audited with its rails declared as frames and with them undeclared
- **THEN** both reports state the same `thin_lit` and `sparse_runs`

### Requirement: The mass audit reads a lit cell as the reviewers do

The mass audit SHALL reduce each frame it draws to a 480 × 270 grey, each cell the full-range BT.709 luma (0 to 255) of the mean colour of the 4 × 4 pixels of the 1920 × 1080 frame it covers, and SHALL take as lit each cell of rows 30 to 229 whose grey is above 60.

#### Scenario: The grey of a lit cell

- **WHEN** a frame holds a uniform cell of luma 61 and another of luma 59
- **THEN** the first is lit and the second is not

### Requirement: The mass audit weighs each frame's lit scene paints

The mass audit SHALL draw the edition's uncaptioned stage on the renderer's native canvas at 1920 × 1080 every 0.25 s with the renderer's text renderer, drawing the ground the composition lays with `fillRect` and every paint of the scene being drawn, and leaving out every paint of no scene and every declared frame stroke. A frame of 40 lit cells or more SHALL have a mass centre, the mean of its lit cells' centres; one of fewer has none.

#### Scenario: A thin line over the ground

- **WHEN** a scene's 2 px line in the line colour, of luma 115, covers half of a cell over the composition's ground of luma 20
- **THEN** the cell reads as the line over the ground, luma 67, and is lit, as in the rendered picture, not as over the canvas's starting black, which would read 57

#### Scenario: A filled square

- **WHEN** a frame shows only a filled square of the ink from x 200 to 600
- **THEN** its mass centre stands at x 400 within 4 px

#### Scenario: Bands outside the content

- **WHEN** a running head above row 120 is added to a frame
- **THEN** its lit cells and its mass centre do not change

#### Scenario: Credits are not weighed

- **WHEN** the credits are drawn with no scene for 3 s
- **THEN** those frames have no mass centre and the mass audit reports no run for them

#### Scenario: A picture too faint to weigh

- **WHEN** a frame has 39 lit cells
- **THEN** it has no mass centre

#### Scenario: A declared frame stroke is not weighed

- **WHEN** a frame shows a filled square from x 200 to 600 and a rail at x 1720 declared as a frame
- **THEN** its mass centre stands at x 400 within 4 px

#### Scenario: A film that declares no frame

- **WHEN** the same rail at x 1720 is not declared
- **THEN** the rail's lit cells count, and the mass centre moves toward it

### Requirement: The mass audit reports where the weight leans

The mass audit SHALL report per scene drawn each run of 1.5 s or more through which that scene is drawn and the mass centre stands more than 90 px off x 960, moving or not, with its start, its end and its largest signed offset in px; a frame in which another scene is drawn, a frame without a mass centre and a gap in the samples SHALL each end a run.

#### Scenario: An undeclared frame around content that leans left

- **WHEN** a scene draws two undeclared rails 4 px wide at x 200 and 1720 from row 120 to row 919, and names whose lit cells outnumber the rails' two to one and whose own mass stands 150 px left of x 960 stand still for 3 s
- **THEN** the frame audit reports no off-centre box run for the scene, and the mass audit reports one run for it with its span and an offset beyond −90 px

#### Scenario: A declared frame around content that leans left

- **WHEN** the same rails are declared as frames
- **THEN** the mass audit reports one run for the scene with an offset of −150 px within 4 px

#### Scenario: The same names centred

- **WHEN** the same scene's names stand with their mass on x 960 between the same rails for 3 s
- **THEN** the mass audit reports no run for the scene

#### Scenario: The outgoing scene drawn into the next segment

- **WHEN** the next segment's timeline starts while the composition still draws the outgoing scene for 1.25 s, until the incoming scene's cut, and the outgoing scene's mass stands 120 px left from 0.5 s before the segment starts to its cut
- **THEN** the mass audit reports one run for the outgoing scene, 1.75 s long, spanning the segment's start

#### Scenario: A brief lean is not a run

- **WHEN** the mass stands 120 px left for 1.2 s and then within 90 px
- **THEN** the mass audit reports no run

#### Scenario: A lean of exactly 90 px

- **WHEN** the mass stands exactly 90 px off for 3 s
- **THEN** the mass audit reports no run

#### Scenario: A frame without a mass inside a lean

- **WHEN** a frame without a mass centre falls 1.25 s into 2.5 s through which the mass stands 120 px left
- **THEN** the mass audit reports no run, since neither part lasts 1.5 s

### Requirement: The mass audit summarises each scene's weight

The mass audit SHALL report for every scene drawn the frames it measured, the mass centre's median offsets from (960, 510) and its share of frames within 90 px of x 960.

#### Scenario: The scene's summary

- **WHEN** the mass audit has measured a scene
- **THEN** its report states the scene's frames measured, its median horizontal and vertical offsets and its share of frames within 90 px

### Requirement: The frame audit measures still states off the vertical centre

The frame audit SHALL report per scene drawn each run of 2 s or more through which the box of that scene's lit paints, declared frame strokes left out, keeps its four edges within 4 px of where they began and its centre more than 50 px above or below y 510, with its span and largest signed offset in px. A declared stage cut, a frame drawing another scene, a frame without a lit scene box and a gap in the samples SHALL each end a run.

#### Scenario: A still stage that sits low

- **WHEN** a scene's lit box stands still with its centre at y 590 for 2.5 s
- **THEN** the frame audit reports one vertical run for that scene with its span and an offset of 80 px

#### Scenario: A row that grows sideways

- **WHEN** a row of names at y 600 grows sideways, one name after another, for 3 s
- **THEN** the frame audit reports no vertical run

#### Scenario: A stage that grows downward

- **WHEN** a scene's box stands more than 50 px below y 510 for 3 s while its bottom edge grows by 40 px
- **THEN** the frame audit reports no vertical run

#### Scenario: A stage cut ends the run

- **WHEN** a box centre stands at y 590 for 1.5 s, a stage cut the composition declares for the scene falls, and it stands there 1.5 s more
- **THEN** the frame audit reports no vertical run

#### Scenario: Credits sit low

- **WHEN** the credits, drawn with no scene, stand still with their box centre at y 584 for 3 s
- **THEN** the frame audit reports no vertical run

### Requirement: The picture gate refuses a picture whose content stands off centre

`check-picture` SHALL refuse each run of the mass audit and each vertical run of the frame audit, naming its scene, span and offset. The mass audit's summary of each scene SHALL refuse nothing.

#### Scenario: A mass run refuses

- **WHEN** the mass audit reports a run and no audit reports another gated finding
- **THEN** `check-picture` writes a refused record that names the run and exits with a refusal

#### Scenario: A vertical run refuses

- **WHEN** the frame audit reports a vertical run
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: A summary alone

- **WHEN** a scene's mass stands 60 px left at its median, no run is reported and no other finding exists
- **THEN** `check-picture` passes and its record binds the mass report that states the median

## MODIFIED Requirements

### Requirement: An edition's picture is checked before it renders

On the edition's current composition and timeline, `check-picture` SHALL run the frame audit over every frame at 1/30 s, the sync audit on its trace and marks, the motion audit at 30 fps and the detail audit at 60, and the mass audit on the uncaptioned stage. Its record SHALL name the SHA-256 of the composition, timeline, stylesheet, each declared font and the uncaptioned stage's record, the engine version, each report and every gated finding, and it SHALL refuse when a gated finding exists.

#### Scenario: A clean picture passes

- **WHEN** no audit reports a gated finding
- **THEN** `check-picture` writes a passing record and exits 0

#### Scenario: A gated finding refuses

- **WHEN** the frame audit reports an overlap or an off-centre run
- **THEN** `check-picture` writes a refused record, names each gated finding and exits with a refusal

#### Scenario: The record binds the detail audit's report

- **WHEN** `check-picture` passes
- **THEN** its record names the detail audit's report with its SHA-256 beside the frame, sync, text and motion reports

#### Scenario: An uncaptioned stage not yet staged

- **WHEN** the edition's uncaptioned stage has no record and `check-picture` runs
- **THEN** `check-picture` refuses before any audit starts, naming the stage and `stage-picture-uncaptioned`, and writes no record

#### Scenario: A stale uncaptioned stage

- **WHEN** the composition changed after the uncaptioned stage was staged, and only the captioned picture was staged again
- **THEN** `check-picture` refuses before any audit starts, naming what differs, and writes no record

#### Scenario: The record binds the mass audit's report and its stage

- **WHEN** `check-picture` passes
- **THEN** its record names the mass audit's report beside the other reports, and the SHA-256 of the uncaptioned stage's record

### Requirement: A render waits for a passing gate record

`render-picture` SHALL refuse an edition before it starts the renderer unless the edition's gate record passed and names the current composition's, timeline's, stylesheet's, declared fonts' and uncaptioned stage record's SHA-256 and the running engine version.

#### Scenario: The composition changed after its check

- **WHEN** `picture/film.js` changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: A font changed after its check

- **WHEN** a declared font changed after `check-picture` passed
- **THEN** `render-picture` refuses and names `check-picture` as the step to run again

#### Scenario: An edition that was never checked

- **WHEN** the edition has no gate record
- **THEN** `render-picture` refuses before the renderer starts

#### Scenario: The uncaptioned stage was staged again after its check

- **WHEN** the uncaptioned stage was staged again with other bytes after `check-picture` passed
- **THEN** `render-picture` refuses, names the stage's binding and `check-picture` as the step to run again

### Requirement: The frame audit measures balance as the reviewers do

The frame audit SHALL take, in every frame it exercises, the box of every paint whose colour mixed over the ground at its opacity is brighter than grey 60 within rows 120–919, leaving out each declared frame stroke, and its horizontal offset from x 960, and SHALL report per scene each run of 1.5 seconds or more in which that box stands more than 90 px off, with its start, its end and its largest offset in px.

#### Scenario: A build-up that stands off centre

- **WHEN** a scene's lit picture stands 120 px left of centre for 1.6 seconds while its parts arrive, then is centred
- **THEN** the audit reports one off-centre build-up for that scene with its start, its end and its offset of 120 px

#### Scenario: A brief state is not a build-up run

- **WHEN** the lit picture stands 200 px off for 1.4 seconds and then within 90 px
- **THEN** the audit reports no off-centre build-up

#### Scenario: A lone centred mark

- **WHEN** a single mark stands centred on x 960 before the rest of its scene arrives
- **THEN** the audit reports no run for it

#### Scenario: A declared frame around content that leans left

- **WHEN** a scene declares its two full-height rails at x 200 and 1720 as frames, its names' box stands still 150 px left of x 960 for 3 s, and the next scene's picture then replaces it
- **THEN** the audit reports an off-centre build-up and an off-centre finished run for that scene, each with an offset of −150 px

#### Scenario: The same rails undeclared

- **WHEN** the same rails are not declared
- **THEN** the audit reports no off-centre build-up and no off-centre still run for the scene

### Requirement: The frame audit measures runs far off centre

The frame audit SHALL report, in every frame, spoken or not, each run of 0.5 s or more within one scene through which the reviewers' box, declared frame strokes left out, stands more than 400 px off x 960 on one side, with its span and its largest offset. The picture gate SHALL refuse each such run that the film does not declare.

#### Scenario: A first mark alone at the far left

- **WHEN** the lit box of a scene stands 624 px left of centre for 1 s while a build's first mark stands alone
- **THEN** the frame audit reports the run with its span and -624 px, and the gate refuses it

#### Scenario: A shorter run, or one at 400 px

- **WHEN** the box stands 624 px off for 0.4 s, or exactly 400 px off for longer
- **THEN** the frame audit reports no far run

#### Scenario: A box that crosses to the other side

- **WHEN** the box stands 500 px left for 1 s and then 500 px right for 0.3 s
- **THEN** the frame audit reports the run on the left and none on the right

#### Scenario: A run that two scenes share

- **WHEN** the box stands 500 px left through the last 0.4 s of one scene and the first 0.4 s of the next
- **THEN** the frame audit reports no far run

#### Scenario: A declared run

- **WHEN** a film declares the far runs on the left of one scene of an edition with a reason
- **THEN** the gate records that scene's runs on the left with the reason and still refuses a run on its right

#### Scenario: A first mark inside a declared frame

- **WHEN** a build's first mark stands alone 624 px left of centre for 1 s inside two rails declared as frames
- **THEN** the frame audit reports the run with -624 px, as without the rails
