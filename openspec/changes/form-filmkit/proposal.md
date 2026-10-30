# Proposal

## Why

The film engine `filmkit` lives inside the `ddwg-film` repository and finds that film by its own location: the film root is two folders above the engine's source, the staged fonts are that film's four files, the pronunciation contract has a fixed path, and the Node checks run from the engine's source tree. The ETHOS introduction film needs the same engine without a copy of it, so the engine needs its own repository, release and tests that load no DDWG content.

## What Changes

- Import the engine package, its Python modules and Node tools, with the engine's tests from `ddwg-film` at `37549a9`, without history and without that film's content or its film-specific tests.
- Find the film from `FILMKIT_ROOT` or from the working directory, instead of from the engine's location, and find the film's npm packages as Node does, in the nearest `node_modules` at or above the film.
- Take the staged fonts from the film's declaration, the pronunciation contract from the scripts, and the listening plan's analyst readings, which record the part of speech of each of the film's English heteronym occurrences, from a file the film declares.
- Run the Node tools through an engine command that stages them below the film's `build/`, where they resolve the film's npm packages, and refuse a renderer whose version the engine does not support.
- Add a short bilingual sample film that the tests load and that builds end to end.
- Build the package with hatchling from `VERSION` 0.1.0 so that a film installs it from a release tag; add the README, licenses, notices, changelog, release declaration and CI projection, without publishing.
- Change no film's output bytes: a film that declares its current fonts stages, narrates, assembles and captions exactly as before.

## Capabilities

### New Capabilities

- `film-engine`: what the engine reads from the film it builds and how the film declares it.
- `engine-distribution`: how a film installs and pins an engine release, and what a release carries.
- `sample-film`: the sample film this repository builds and tests the engine with.

### Modified Capabilities

None.

## Impact

- New repository `filmkit`, governed by ETHOS `0.2.0-alpha.20`. Its forge remotes, GitHub `HengYangDS/filmkit` and GitLab `dig/misc/tools/filmkit`, are added only when the user confirms the push.
- Dependencies match `ddwg-film`: Python `mlx-audio`, `numpy`, `pillow` and `pydantic`; for the tests and the sample film, the npm renderer `hyperframes`, `puppeteer-core`, `@puppeteer/browsers` and `gsap`.
- **BREAKING** for a film that adopts the release: it declares its fonts and its listening-plan readings, runs the Node checks through the engine command, and declares the renderer's npm packages itself.
- Out of scope: publishing or tagging before the user confirms; moving `ddwg-film` onto the release, which its own Change does; the ETHOS film; any change to a film's output bytes.
