## MODIFIED Requirements

### Requirement: An edition's picture is checked before it renders

`check-picture` SHALL run the frame audit over every frame of the edition's timeline at one thirtieth of a second, the sync audit on that audit's trace and marks, the motion audit at 30 frames per second and the detail audit at 60, on the current composition and timeline. It SHALL write a gate record naming the SHA-256 of the composition, timeline, stylesheet and each declared font, the engine version, each audit's report and every gated finding, and SHALL refuse when a gated finding exists.

#### Scenario: A clean picture passes

- **WHEN** no audit reports a gated finding
- **THEN** `check-picture` writes a passing record and exits 0

#### Scenario: A gated finding refuses

- **WHEN** the frame audit reports an overlap or an off-centre run
- **THEN** `check-picture` writes a refused record, names each gated finding and exits with a refusal

#### Scenario: The record binds the detail audit's report

- **WHEN** `check-picture` passes
- **THEN** its record names the detail audit's report with its SHA-256 beside the frame, sync, text and motion reports

## ADDED Requirements

### Requirement: The frame audit measures runs far off centre

The frame audit SHALL report, in every frame, spoken or not, each run of 0.5 s or more within one scene through which the box of every paint lit at full size in rows 120-919 stands more than 400 px off x 960 on one side, with its span and its largest offset. The picture gate SHALL refuse each such run that the film does not declare.

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
