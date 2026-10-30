# Tasks

## 1. Import and toolchain

- [x] 1.1 Import the engine's Python modules, Node tools and engine tests from `ddwg-film` at `37549a9` without history or film-specific tests, and verify each imported file's SHA-256 equals its blob there.
- [x] 1.2 Bind the toolchain: the Mise configuration and lock for Node 26.12.1, CPython 3.12.16, uv 0.13.5 and ETHOS `0.2.0-alpha.20`, bound with its release's Mise declaration, and the uv and npm locks; verify `mise install --locked`, `uv sync --frozen` and `npm ci` succeed.
- [x] 1.3 Declare the gate registry with the portable gates, the check policies and the agent entry; verify `ethos status` passes.

## 2. Engine boundary and sample film

- [x] 2.1 Find the film from `FILMKIT_ROOT` or the working directory and its npm packages from the nearest `node_modules`; verify by `tests/test_repository.py`, which loads no film, that the engine binds the film it runs below and refuses outside any film, naming the folder where the search began.
- [x] 2.2 Write the bilingual sample film in `examples/sample-film`: declaration, scripts, casts, voice contracts, pages, covers and composition; verify that the engine loads it with `FILMKIT_ROOT` set to it.
- [x] 2.3 Read the staged fonts from the declaration, the pronunciation contract from the scripts and the listening plan's analyst readings from a file the film declares; verify by focused tests that a stage holds exactly the declared fonts in order and that the listening plan derives from the film's own contract and readings.
- [x] 2.4 Point the engine's tests at the sample film; verify both suites pass with no other film present.
- [x] 2.5 Add the tools command that stages the Node tools below the film's `build/` and runs them with the film's packages, and refuse an unsupported renderer version; verify by the suites.

## 3. Sample film build

- [x] 3.1 Build the sample film end to end after the supply step and verify both editions.
- [ ] 3.2 Replace the golden narration receipts with the sample film's own takes; verify that the speech-plan tests reproduce their fingerprints.

## 4. Distribution

- [x] 4.1 Build the package with hatchling from `VERSION` 0.1.0 with the Node tools inside; verify that a film project locks the package from a Git source at a lane commit and runs a Node tool through it.
- [x] 4.2 Write the README with the layout a film provides, `LICENSE`, `NOTICE`, `CHANGELOG.md` and `.ethos/release.toml`; verify `ethos lane repair-paradigm --json` reports no gap.
- [x] 4.3 Project the portable gates into GitHub Actions and GitLab CI, and verify the projections validate.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Add the forge remotes, push, tag `v0.1.0` and publish only after the user confirms.
