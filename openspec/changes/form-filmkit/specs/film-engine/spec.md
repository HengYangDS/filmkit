## Purpose

Build any film from its own declaration and content: the engine finds the film it runs in and takes every film-specific value from that film, never from itself.

## ADDED Requirements

### Requirement: The engine finds the film it builds

The engine SHALL build the film whose declaration `content/film.toml` lies in the folder that `FILMKIT_ROOT` names or, when it is unset, in the nearest folder at or above the working directory. It SHALL find the film's npm packages in the nearest `node_modules` folder at or above the film. It SHALL refuse to start when no declaration is found, naming the folder where the search began.

#### Scenario: A film is found from a folder below it

- **WHEN** an engine command runs in a folder below a film's root and `FILMKIT_ROOT` is unset
- **THEN** it reads that film's sources and writes only below that film's `build/`

#### Scenario: Outside any film the engine refuses

- **WHEN** an engine command runs in a folder with no declaration at or above it and `FILMKIT_ROOT` is unset
- **THEN** it refuses before any work and names the folder where the search began

### Requirement: A film declares its parameters

A film SHALL declare, in one declaration, its file prefix, delivery folder, entry page, source manifest, each edition's sources folder, cover and caption terms, the fonts its picture uses, and its review prompt, floors, scored dimensions and listening-plan readings. The engine SHALL refuse an invalid or incomplete declaration before any work, naming each failing field.

#### Scenario: An invalid declaration refuses before work

- **WHEN** the declaration omits an edition, names a font or another file that is missing, gives a malformed file prefix or a review floor outside 0 to 100
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

The engine SHALL NOT contain any film's title, identity, script, voice, source, player page, review policy or picture composition. It SHALL take them from the film it builds.

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
