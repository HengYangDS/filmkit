## ADDED Requirements

### Requirement: The picture gate refuses a whole turn the browser paints without ink

`check-picture` SHALL draw each distinct start and end of every stroked clockwise arc that sweeps a whole turn or more, less 0.00001 rad, from a start off a whole number of turns, once on a scratch canvas in the renderer's browser. It SHALL refuse a scene's line whose arc that browser paints without ink from one of its starts and record every other, naming the scene, times, start, line of `picture/film.js` and remedy: an ellipse from 0 with the start as its rotation.

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
