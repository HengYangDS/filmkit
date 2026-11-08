## MODIFIED Requirements

### Requirement: The frame audit measures still states off centre

The frame audit SHALL report per scene each run of 2 seconds or more in which that box stands more than 50 px off while its left and right edges stay within 4 px, with its start, its end and its largest offset in px. It SHALL leave out a run whose next frame, after no stage cut, holds a wider box of the same scene that contains it, and SHALL report as finished a run whose next frame shows another scene or follows a stage cut of its scene.

#### Scenario: A settled composition off centre

- **WHEN** a scene's finished picture stands still 60 px right of centre for 2.5 seconds
- **THEN** the audit reports one off-centre settled run for that scene with its offset of 60 px

#### Scenario: A still state the next part grows from

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and then widens to the right while it keeps every part it showed
- **THEN** the audit reports no settled run

#### Scenario: A build-up within its limit

- **WHEN** the lit picture stands 70 px off for 3 seconds while its right edge grows by 40 px
- **THEN** the audit reports no settled run and no build-up

#### Scenario: A still state that a stage cut replaces

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and the next frame, after a stage cut the composition declares for its scene, holds a wider box that contains it
- **THEN** the audit reports one finished run for that scene with its offset of 70 px and no settled run

#### Scenario: A still state that another scene replaces

- **WHEN** the lit picture stands still 70 px off for 2.5 seconds and the next frame shows the next scene's picture
- **THEN** the audit reports one finished run and no settled run

### Requirement: The picture gate refuses a picture off the reviewers' balance

`check-picture` SHALL refuse `off_centre_builds` and `off_centre_finished` and SHALL record `off_centre_settled` in the gate record without refusing it.

#### Scenario: An off-centre build-up refuses

- **WHEN** the frame audit reports an off-centre build-up
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal

#### Scenario: A still state off centre is recorded

- **WHEN** the frame audit reports an off-centre settled run and no gated finding
- **THEN** `check-picture` writes a passing record that lists the settled run

#### Scenario: A finished composition off centre refuses

- **WHEN** the frame audit reports an off-centre finished run
- **THEN** `check-picture` writes a refused record that names it and exits with a refusal
