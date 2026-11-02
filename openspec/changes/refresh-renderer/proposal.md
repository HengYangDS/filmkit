# Proposal

## Why

The owner asked that every governed repository keep its supply at the latest stable releases. filmkit's renderer stands at HyperFrames 0.8.225, and the latest stable release is 0.9.3, published on 2 November 2026; every other package and tool the repository declares is current. The breaking change in 0.9.0 removes only the Plan v1 transport of distributed rendering, which the engine does not use: it renders locally with `hyperframes render`.

## What Changes

- Raise `hyperframes` to 0.9.3 in `package.json` and lock it with `npm install --package-lock-only`. The `undici` override stays at 7.30.1, because 0.9.3 still pins 7.25.0 exactly.
- Set the engine's `RENDERER_VERSION` to 0.9.3. HyperFrames 0.9.3 still declares Chrome Headless Shell 152.0.7977.30, so the browser pin stays.
- Let the two tests that named the old renderer pin read `RENDERER_VERSION`, so the next move does not edit them.
- State the new version in the README and `NOTICE`, and record the move under `Unreleased` in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine's contract is unchanged, so `.openspec.yaml` sets `skip_specs: true`. A new renderer can change the frames a film renders, so `ddwg-film`, `ethos-film` and `ddwg-essentials-film` keep their filmkit pins until each accepts an edition on a release that carries this renderer.

## Impact

`package.json`, `package-lock.json`, `src/filmkit/picture/rendering.py`, two test modules, `README.md`, `NOTICE` and `CHANGELOG.md`. The change lands on `dev` and `main` with no tag; a later release carries it. `tasks.md` is the sole progress ledger.
