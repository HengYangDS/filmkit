## Why

filmkit 0.22.0 renders with HyperFrames 0.9.9, published on 3 November 2026; HyperFrames 0.9.46 is
the newest stable release, published on 14 November 2026. Its release notes from 0.9.10 to 0.9.46
change no capture flag; four entries touch the capture path: no-draw seeks no longer upload graded
images, a non-deterministic `crypto.randomUUID()` lint, DrawElement's fallback on GPU-less Linux,
and fast capture on Chrome 157 and later. puppeteer-core 25.17.0, GSAP 3.15.1 and undici 7.30.2 are
the newest stable releases of the engine's other npm inputs on their current major lines. Each film
adopts a filmkit release at its next edition, so the move ships as release 0.22.1.

## What Changes

- Pin `hyperframes` 0.9.46, `puppeteer-core` 25.17.0 and `gsap` 3.15.1 in `package.json`, override
  `undici` to 7.30.2, and refresh `package-lock.json`, which also takes postcss 8.5.33.
- Set the engine's `RENDERER_VERSION` to 0.9.46. HyperFrames 0.9.46 still declares Chrome Headless
  Shell 152.0.7977.30, so the browser pin and its digest stay.
- The GSAP test reads 3.15.1; the README and `NOTICE` name the new versions and correct
  `@puppeteer/browsers` to 3.2.7, the version `package.json` has pinned since 0.21.3.
- Cut 0.22.1: `VERSION`, the dated Changelog section and the README's install line.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine's commands, declarations and outputs keep their form, so `.openspec.yaml` sets
`skip_specs: true`.

## Impact

`package.json`, `package-lock.json`, `src/filmkit/picture/rendering.py`,
`tests/picture/headless-composition.test.mjs`, `README.md`, `NOTICE`, `VERSION` and `CHANGELOG.md`.
The sample film is built at v0.22.0 and again on the new inputs, and its films are compared frame by
frame. `tasks.md` is the sole progress ledger.
