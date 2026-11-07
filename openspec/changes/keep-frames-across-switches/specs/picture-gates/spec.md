## ADDED Requirements

### Requirement: The picture gate refuses a whole turn the browser may not paint

`check-picture` SHALL refuse every stroked clockwise arc that sweeps a whole turn or more, less 0.00001 rad, from a start that is not a whole number of turns, since the renderer's browser computes such an arc in single precision and can paint no ink for it. The finding SHALL name the scene, its first and last time, the start angle and the line of `picture/film.js` that drew the arc, and the remedy: an ellipse from 0 with the start as its rotation.

#### Scenario: A ring that turns

- **WHEN** a scene strokes `arc(x, y, r, a, a + 2 * Math.PI)` with a start `a` that moves with time
- **THEN** `check-picture` refuses, naming the scene, the times, the start, the line that drew the arc and `ellipse(x, y, r, r, a, 0, 2 * Math.PI)`

#### Scenario: Whole turns the browser paints

- **WHEN** a scene strokes `ellipse(x, y, r, r, a, 0, 2 * Math.PI)`, `arc(x, y, r, 0, 2 * Math.PI)` or an anticlockwise arc
- **THEN** `check-picture` reports no such finding
