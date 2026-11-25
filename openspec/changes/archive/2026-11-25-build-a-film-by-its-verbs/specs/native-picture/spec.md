## MODIFIED Requirements

### Requirement: A render draws the staged composition on a native canvas

`render-picture`, `render-picture-uncaptioned` in its native way, `render-draft` and `qualify-renderer` SHALL draw a stage with the engine's own Node module on a canvas of the `@napi-rs/canvas` package that the film's npm packages install, running the staged composition unchanged, with the canvas's text renderer set to `system` and each face the stage's record names registered from the staged fonts. No render SHALL start a browser.

#### Scenario: A picture is rendered

- **WHEN** `render-picture` runs on an edition's current stage
- **THEN** its command starts Node on the engine's module with the stage, and no browser process is started

#### Scenario: A face that does not register

- **WHEN** a staged font that the stage's record names cannot be registered
- **THEN** the render fails, naming the family, and its receipt records the exit

#### Scenario: A stage that names no faces, or holds a font none registers

- **WHEN** a stage's record names no faces, as a stage of an earlier engine, or the stage holds a font file that no face of its record registers
- **THEN** the render fails before it draws, asking for the picture to be staged again or naming the font

#### Scenario: Another canvas version

- **WHEN** the film's npm packages install another version of the canvas package than the engine draws with, or none
- **THEN** staging, rendering and the engine's tools stop before the renderer or a tool starts, naming both versions as a tool the host lacks, and the command exits 2
