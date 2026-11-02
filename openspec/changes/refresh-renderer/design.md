# Design

## Context

See [proposal.md](proposal.md). The engine refuses a renderer whose installed version differs from `RENDERER_VERSION`, and `filmkit.supply` installs the browser build that the locked renderer pins and checks its executable against `BROWSER_SHA256`. The engine calls `hyperframes render` for the staged picture and muxes its own soundtrack, so the release notes between 0.8.225 and 0.9.3 matter where they touch local rendering, capture or the staged page.

## Goals / Non-Goals

**Goals:**

- The renderer stands at its latest stable release.
- The sample film builds and verifies end to end on it, in both editions.

**Non-Goals:**

- Changing the engine's contract, any declaration field or a film's pin.
- Tagging or releasing this repository.

## Decisions

### Only the renderer moves

A currency audit on 2 November 2026 found every other declared package and tool at its latest stable release. The Mise floors and the Python 3.12 line stay by their standing decisions.

### The notes are read against the engine's use

The Plan v1 removal in 0.9.0 touches `@hyperframes/producer/distributed` and the Lambda and Cloud Run adapters, none of which the engine imports. The fixes that could reach a local render are the release of a WebGL context when a scene ends (0.9.2) and the static-frame verification budget (0.8.226). The peak limiter of 0.8.228 acts on the renderer's audio export, which the engine does not use. The sample build is the check of all of them.

### The override stays

0.9.3 still pins `undici` 7.25.0 exactly, so the override's removal condition has not been met.

## Risks / Trade-offs

- [The new renderer changes a film's frames] → The films pin filmkit by tag and move only after they rebuild, compare and accept an edition, as `CONTRIBUTING.md` requires.
- [HyperFrames ships several releases a day, so 0.9.3 will soon not be the latest] → The next supply recheck moves it again; each move stays one small Change.

## Migration Plan

Raise the package, lock it, audit the locks, set the pins, run the checks, build the sample film, prove the archived head, land, close out and publish `dev` and `main` to both peers. To roll back, revert the Change's commits; no film reads this head until a release carries it.
