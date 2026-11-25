## ADDED Requirements

### Requirement: A film is built through one command of ten verbs

The engine SHALL offer a film one console command, `filmkit`, with the verbs `supply`, `check`, `edit`, `narrate`, `plan`, `build`, `verify`, `review`, `deliver` and `release`, and no other command that a film's tasks or gates run. A refusal SHALL be one line on standard error with exit status 1, and a refusal that names a step to run SHALL name it as the verb that runs it.

#### Scenario: The surface

- **WHEN** the installed engine's commands are listed
- **THEN** `filmkit` is its one console command, and `python -m` runs no command of `filmkit.produce`, `filmkit.tools`, `filmkit.durations`, `filmkit.adoption`, `filmkit.supply`, `filmkit.delivery.verification`, `filmkit.delivery.reproduction`, `filmkit.delivery.release`, `filmkit.delivery.folder` or `filmkit.review.round`

#### Scenario: A refusal names its verb

- **WHEN** `stage-picture` is asked of an edition whose soundtrack is not assembled
- **THEN** it refuses in one line that names `filmkit build assemble:<code>`

### Requirement: A command's exit status tells a refusal from a failure to finish

Every verb SHALL exit 0 where it did what it was asked; 1 where the film or a gate said no, in one line on standard error, a declaration that the loader refuses among them; and 2 where it could not finish, an owner's exception with its traceback and a tool the host lacks in one line that names it. A command that a request ended SHALL exit with the status that names the request. A node's failure SHALL never count as its refusal.

#### Scenario: Done

- **WHEN** `filmkit supply` finds every supply as its pins state
- **THEN** it exits 0

#### Scenario: A refusal

- **WHEN** the dictionary that `filmkit supply` finds differs from its pinned SHA-256
- **THEN** it exits 1 with that one line

#### Scenario: A declaration the loader refuses

- **WHEN** a film still holds `content/release.json`, which the loader refuses, and `filmkit plan`, `filmkit build check`, `filmkit verify` or `filmkit check` runs
- **THEN** it exits 1 with the loader's problems in one line, `check` after printing each finding as its read-only mode does, and no record is written

#### Scenario: An exception

- **WHEN** an owner that a verb calls raises an exception that is no refusal of its own
- **THEN** the verb prints the traceback and exits 2

#### Scenario: A missing tool

- **WHEN** a verb or a node it runs needs a tool the host lacks: no `node`, `ffmpeg`, `ffprobe`, `exiftool` or Vale on the path, no rsync 3, no browser build where a tool drives the browser, or another canvas build than the engine draws with in the film's npm packages
- **THEN** it names the tool in one line and exits 2

#### Scenario: Outside any film

- **WHEN** a verb runs where no film's declaration stands, as with `FILMKIT_ROOT` naming an empty folder
- **THEN** it says so in one line and exits 2: no film was read, so nothing is refused

#### Scenario: A tool that crashes

- **WHEN** an engine tool of `tools.TOOLS` that a node runs, as the geometry check's, ends with an error that nothing catches, or a signal ends it
- **THEN** the tool exits 2 or by the signal, the node's run is a failure with the outcome `error`, never its refusal, and `filmkit build` exits 2; the renderer and the players' check are not yet held to this (task 8.1 of `key-outputs-by-their-inputs`)

#### Scenario: A node that fails

- **WHEN** a node's owner raises an exception that is no refusal during `filmkit build all`
- **THEN** the node's record states the outcome `error`, no node downstream of it runs, the other edition's nodes do, and the command exits 2

#### Scenario: A request to end a render

- **WHEN** `filmkit build` is sent SIGTERM while a node runs a render
- **THEN** it ends the renderer, says so in one line and exits 143

#### Scenario: A request to end a light node

- **WHEN** `filmkit build` is sent SIGTERM while a node runs that holds no renderer, no narration process and no step of `narrate`
- **THEN** SIGTERM ends the command by its default action, which a shell reports as 143, with no line and no run record written for the node

### Requirement: One command checks a film's sources at once

`filmkit check` SHALL report at once every problem of the declaration as the loader reads it and, for every edition, every finding of the concept contract, the register, the readings, the anchors and what the picture reads over the edition's derived timeline. It SHALL refuse while one stands, need no model, no browser, no dictionary, no FFmpeg and no build, and write only its record, its verdict and each edition's occurrence plan below `build/`; with `--read-only` it SHALL write no file.

#### Scenario: Every finding at once

- **WHEN** the declaration names a missing cover and a thought holds 你们
- **THEN** one run names both and exits 1

#### Scenario: A picture that does not load

- **WHEN** an edition's composition throws as it loads
- **THEN** the check reports that edition's picture reads as not judged and refuses nothing for them

#### Scenario: Where no model is supplied

- **WHEN** `filmkit check --read-only` runs where no speech model, browser or dictionary is supplied and no FFmpeg is installed
- **THEN** it runs to its verdict and writes no file

### Requirement: The source check holds the film's pins and pages to the engine's record

`filmkit check` SHALL also report every difference of the film's npm lock, Python lock and picture template from the engine's record of what it was released on, and every line of a review prompt that cites the runtime without "This edition".

#### Scenario: Another canvas in the film's lock

- **WHEN** the film's npm lock holds the canvas package at another version than the engine's record states
- **THEN** the check names both versions and refuses

#### Scenario: A prompt line that cites the runtime

- **WHEN** a review prompt's line cites `{duration}` and does not say "This edition"
- **THEN** the check names the line

### Requirement: A film's tests reach the engine through one interface

The engine SHALL offer a film's tests the module `filmkit.api` and one Node entry, `filmkit/picture/testing.mjs`, found through `filmkit.api.TEST_ENTRY`, which SHALL export `openComposition`, `openModules` and `derivedTimeline`; the last SHALL give the timeline `filmkit.api.derived_timeline` gives. A release that changes a name of either SHALL say in its note what a film does.

#### Scenario: A film's composition test

- **WHEN** a film's Node test imports the entry, takes `derivedTimeline("zh")` and opens the composition on it
- **THEN** the composition draws the edition's scenes as the source check draws them

#### Scenario: A film's module test

- **WHEN** a film's Node test opens its unbundled modules through `openModules` and renders a time
- **THEN** each paint reaches the test's callback with its scene, and the film's modules are covered as they run

#### Scenario: An internal function of the composition

- **WHEN** a film's test evaluates `wrapName("证据", 230, 26)` through the handle of `openComposition`
- **THEN** it receives the lines the composition's own function returns

#### Scenario: The engine's own tests

- **WHEN** the engine's tests of the sample open a composition
- **THEN** they import the entry and no other module of the picture

### Requirement: A film declares what its task lines passed

A film SHALL declare in `[picture]` whether its geometry check gates names that stand too close on a row (`gate_row_gaps`, false where it states none) and the editions whose uncaptioned picture is rendered from its own stage (`native_uncaptioned`, none where it states none). The loader SHALL refuse an edition there that the film does not declare.

#### Scenario: Row gaps gated

- **WHEN** a film declares `gate_row_gaps = true`
- **THEN** the geometry check of each edition gates the row gaps

#### Scenario: A native uncaptioned picture

- **WHEN** the sample declares `native_uncaptioned = ["zh"]`
- **THEN** `render-picture-uncaptioned:zh` renders its own stage and the English uncaptioned picture is derived

## MODIFIED Requirements

### Requirement: The Node tools run with the film's packages

The engine SHALL run its Node tools for a film from its nodes and checks, resolving the browser automation package from the film's npm packages, wherever the engine is installed. The engine SHALL refuse to stage, render or check a picture with a renderer whose installed version differs from the version the engine supports, naming both versions.

#### Scenario: A Node tool runs from an installed engine

- **WHEN** `filmkit build geometry-check:zh` runs with the engine installed outside the film
- **THEN** the check runs with the film's npm packages and writes its report where its node declares

#### Scenario: Another renderer version refuses

- **WHEN** the film's installed renderer reports a version other than the one the engine supports
- **THEN** the engine refuses before the renderer runs and names both versions
