## MODIFIED Requirements

### Requirement: The picture gate refuses a whole turn the browser paints without ink

`check-picture` SHALL draw each distinct start and end of every stroked clockwise arc that sweeps a whole turn or more, less 0.00001 rad, from a start off a whole number of turns, once on a scratch canvas in the browser that paints the cover. It SHALL refuse a scene's line whose arc that browser paints without ink from one of its starts and record every other, naming the scene, times, start, line of `picture/film.js` and remedy: an ellipse from 0 with the start as its rotation.

#### Scenario: A start the browser paints without ink

- **WHEN** a scene strokes `arc(x, y, r, a, a + 2 * Math.PI)` from a start `a` of 1.9335 rad, which Chrome Headless Shell 152 paints without ink
- **THEN** `check-picture` refuses, naming the scene, the times, the start, the line that drew the arc and `ellipse(x, y, r, r, a, 0, 2 * Math.PI)`

#### Scenario: A ring that turns

- **WHEN** a scene strokes a ring through a whole turn whose start moves with time and reaches a start the browser paints without ink
- **THEN** `check-picture` refuses that line, naming the frames of the starts that paint no ink and how many of its starts fail, and draws each start once

#### Scenario: Starts the browser paints

- **WHEN** a scene strokes a whole turn from π, 3π/2 or −π/2, which that browser paints in full
- **THEN** `check-picture` passes and records the line with its times, its start and the ellipse that draws it from any start

#### Scenario: Whole turns it never questions

- **WHEN** a scene strokes `ellipse(x, y, r, r, a, 0, 2 * Math.PI)`, `arc(x, y, r, 0, 2 * Math.PI)` or an anticlockwise arc
- **THEN** `check-picture` reports no such finding and starts no browser for it

## ADDED Requirements

### Requirement: The geometry check takes its frame from the stage's record

The geometry check SHALL take a picture's width, height, seconds and frames a second from the record of the stage it is handed, `stage.json`, each a whole positive number, and SHALL read no rate from the stage's page. Before it opens a browser it SHALL refuse, in one line that names the file, what is wrong with it and `stage-picture`, a stage whose record is absent, holds no JSON or lacks one of the four, and a stage whose page states another width, height or seconds than its record.

#### Scenario: A stage the engine writes

- **WHEN** the check is handed a stage that `stage-picture` wrote for a film whose template states no rate
- **THEN** it inspects the frames of the record's seconds at the record's rate

#### Scenario: A workspace without a stage's record

- **WHEN** the folder holds a page and no `stage.json`, or a record that states no `fps`
- **THEN** the check exits 1 with one line that names the record and `stage-picture`, opens no browser and writes no receipt

#### Scenario: A page and a record that disagree

- **WHEN** the stage's page states a width of 3840 and its record a width of 1920
- **THEN** the check refuses, naming both figures and `stage-picture`
