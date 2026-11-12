# film-engine Specification

## Purpose

Build any film from its own declaration and content: the engine finds the film it runs in and takes every film-specific value from that film, never from itself.

## Requirements

### Requirement: The engine finds the film it builds

The engine SHALL build the film whose declaration `content/film.toml` lies in the folder that `FILMKIT_ROOT` names or, when it is unset, in the nearest folder at or above the working directory. It SHALL find the film's npm packages in the nearest `node_modules` folder at or above the film. It SHALL refuse to start when no declaration is found, naming the folder where the search began.

#### Scenario: A film is found from a folder below it

- **WHEN** an engine command runs in a folder below a film's root and `FILMKIT_ROOT` is unset
- **THEN** it reads that film's sources and writes only below that film's `build/`

#### Scenario: Outside any film the engine refuses

- **WHEN** an engine command runs in a folder with no declaration at or above it and `FILMKIT_ROOT` is unset
- **THEN** it refuses before any work and names the folder where the search began

### Requirement: A film declares its parameters

A film SHALL declare, in one declaration, its file prefix, delivery folder, entry page, source manifest, each edition's sources folder, cover and caption terms, the fonts its picture uses, and its review prompt, floors, scored dimensions and listening-plan readings. The engine SHALL refuse an invalid or incomplete declaration before any work, naming each failing field; a cover may be absent until the engine paints it.

#### Scenario: An invalid declaration refuses before work

- **WHEN** the declaration omits an edition, names a font or another file that is missing other than a cover, gives a malformed file prefix or a review floor outside 0 to 100
- **THEN** the engine refuses when it loads, before any synthesis, and names each failing field

#### Scenario: The declared fonts are staged in their declared order

- **WHEN** the engine stages a film's picture
- **THEN** the stage holds each declared font, and no other font, below `fonts/` in the declared order

#### Scenario: The listening plan takes the film's own readings

- **WHEN** the listening plan is derived for a film that declares its readings
- **THEN** each English heteronym occurrence takes the part of speech the film records for it
- **AND** an occurrence the film records no part of speech for, or a recorded one that names no current occurrence, refuses the plan

### Requirement: Each script declares its edition

Each edition's script SHALL declare the edition's title, author, language, duration, frame rate, chapters and pronunciation contract. The engine SHALL refuse, before any work, scripts that disagree on the film's duration, author or chapter count, or that declare a frame rate other than the 60 fps it encodes.

#### Scenario: Scripts that disagree refuse before work

- **WHEN** the editions' scripts declare different durations, authors or chapter counts, or a frame rate other than 60 fps
- **THEN** the engine refuses when it loads and names the value

### Requirement: The engine carries no film's content

The engine SHALL NOT contain any film's title, identity, script, voice, source, player prose, review policy or picture composition. It SHALL take them from the film it builds; the player's structure and interface text are the engine's own.

#### Scenario: The engine names no film

- **WHEN** the engine's sources are scanned for the sample film's file prefix, delivery folder, source repository, titles, author and chapter titles
- **THEN** none is found

### Requirement: The Node tools run with the film's packages

The engine SHALL run its Node tools for a film through an engine command that resolves the browser automation package from the film's npm packages, wherever the engine is installed. The engine SHALL refuse to stage, render or check a picture with a renderer whose installed version differs from the version the engine supports, naming both versions.

#### Scenario: A Node tool runs from an installed engine

- **WHEN** a film runs the geometry check through the engine command with the engine installed outside the film
- **THEN** the check runs with the film's npm packages and writes its report where the film asks

#### Scenario: Another renderer version refuses

- **WHEN** the film's installed renderer reports a version other than the one the engine supports
- **THEN** the engine refuses before the renderer runs and names both versions

### Requirement: A film paints its covers from its picture

The engine SHALL paint each edition's cover from the edition's staged picture and compare it with the tracked cover. A film MAY name covers before it paints them; packaging SHALL refuse an edition whose cover is missing, naming the cover's field. A painted cover with no tracked cover to compare SHALL be written and reported as uncompared, and SHALL NOT pass the cover check.

#### Scenario: A new film narrates before it paints its covers

- **WHEN** a film's declaration names covers that do not exist yet
- **THEN** the engine loads the declaration, narrates and stages the picture
- **AND** packaging refuses each edition whose cover is missing and names `editions.<code>.cover`

#### Scenario: A first cover is painted with nothing to compare

- **WHEN** the cover check paints an edition's cover and the tracked cover does not exist
- **THEN** it writes the painted cover and reports that no tracked cover was compared
- **AND** it fails until the painted cover is tracked and identical to a new painting

### Requirement: A film declares how its picture is captured

A film MAY declare `[picture] capture` as `fast`, `screenshot` or `software`; one that declares none captures `fast`. Every render of its picture SHALL pass the renderer's browser and capture flags of the declared mode explicitly. Each render receipt SHALL record the mode, and validation SHALL refuse a picture whose receipt records another mode than the declaration, reading a receipt that records none by its command.

#### Scenario: A film that declares no capture

- **WHEN** a film that declares no capture renders its captioned or uncaptioned picture
- **THEN** the renderer command is, element for element, the command that filmkit 0.19.0 runs, and the receipt records `fast`

#### Scenario: A film that declares screenshot capture

- **WHEN** a film declares `capture = "screenshot"` and renders its pictures and its draft
- **THEN** each command passes `--experimental-fast-capture=false` where `fast` passes `--experimental-fast-capture`, and each receipt records `screenshot`

#### Scenario: A film that declares software capture

- **WHEN** a film declares `capture = "software"` and renders its pictures and its draft
- **THEN** each command passes `--no-browser-gpu` where `fast` passes `--browser-gpu` and `--experimental-fast-capture=false` where `fast` passes `--experimental-fast-capture`, and each receipt records `software`

#### Scenario: Another capture value

- **WHEN** the declaration gives `capture = "drawelement"`
- **THEN** the engine refuses when it loads, naming `picture.capture`

#### Scenario: A picture rendered in another mode

- **WHEN** a film declares screenshot capture and its picture's receipt records `fast`
- **THEN** validation refuses the picture, naming both modes

#### Scenario: A receipt written before the declaration

- **WHEN** a receipt records no mode and its command passes `--experimental-fast-capture`
- **THEN** validation reads it as `fast`, and the picture validates for a film that declares no capture
