# Proposal

## Why

The owner asked that every governed repository move its supply to the latest stable releases. On 1 November 2026 filmkit declares older releases of its renderer, its speech engine, its browser driver and its tools: HyperFrames 0.8.150 against 0.8.225, mlx-audio 0.5.8 against 0.6.3, puppeteer-core 25.12.0 against 25.16.0, and Node, uv, Mise in CI, Pydantic, hatchling, coverage and pytest one release or more behind. The npm lock also holds zod 3.25.76, which GHSA-mrhx-c7xc-m3w5 affects.

## What Changes

- Raise the npm packages to HyperFrames 0.8.225, puppeteer-core 25.16.0 and @puppeteer/browsers 3.2.6, and the engine's renderer pin with them. HyperFrames 0.8.225 still pins Chrome Headless Shell 152.0.7977.30, so the browser pin stays.
- Override `undici` to 7.30.1 in `package.json`. HyperFrames 0.8.225 pins 7.25.0 exactly, which 29 advisories affect, and no HyperFrames release accepts a fixed one.
- Raise mlx-audio to 0.6.3, Pydantic to 2.14.2, hatchling to 1.33.0, coverage to 7.17.0 and pytest to 9.2.0, and refresh `uv.lock` on the Python 3.12 line.
- Raise Node to 26.13.0 and uv to 0.13.6 in the Mise declaration, and Mise to 2026.10.25 in CI, and regenerate the CI projection.
- State the new versions in the README and `NOTICE`, and record the move in the Changelog.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The engine's contract is unchanged, so `.openspec.yaml` sets `skip_specs: true`. A new renderer and speech engine change the frames and narration a film renders. `ddwg-film` and `ethos-film` therefore keep filmkit v0.1.1 until an edition is produced, narrated, reviewed and accepted on the new engine. Moving their pin is not a routine update.

## Impact

`package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock`, `.config/mise/`, `.config/ci/verification.toml`, `.github/workflows/ci.yml`, `src/filmkit/picture/rendering.py`, the comments in two narration modules that name the speech engine's version, `README.md`, `NOTICE` and `CHANGELOG.md`. The change lands on the local `dev` only; publication of this repository waits for the user's approval. `tasks.md` is the sole progress ledger.
