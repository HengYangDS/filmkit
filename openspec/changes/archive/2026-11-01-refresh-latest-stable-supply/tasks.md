# Tasks

## 1. Declarations and locks

- [x] 1.1 Raise HyperFrames to 0.8.225, puppeteer-core to 25.16.0 and @puppeteer/browsers to 3.2.6 in `package.json`, override `undici` to its latest fixed 7.x release, and lock them with `npm install --package-lock-only`; done when the lock holds those versions and OSV reports no advisory for any package it pins. The lock holds them with `undici` 7.30.1 and `zod` 4.6.7; OSV reports no advisory in its 127 packages.
- [x] 1.2 Raise mlx-audio, Pydantic, hatchling, coverage and pytest to their latest stable releases in `pyproject.toml` and refresh `uv.lock` with `uv lock --upgrade`; done when the lock resolves on the Python 3.12 line and OSV reports no advisory for any package it pins. The lock resolves 53 packages, with MLX 0.32.4; OSV reports no advisory in its 52 registry packages.
- [x] 1.3 Raise Node and uv in `.config/mise/config.toml` and Mise in `.config/ci/verification.toml`, lock with native `mise lock`, and regenerate the CI projection; done when the lock holds the new versions and the projection check conforms. The lock holds Node 26.13.0 and uv 0.13.6, and the projection runs Mise 2026.10.25.

## 2. Engine pins

- [x] 2.1 Set `RENDERER_VERSION` in `src/filmkit/picture/rendering.py` to the renderer installed, and `BROWSER` and `BROWSER_SHA256` to the browser build it pins; done when the supply installs that build at that digest and the tests pass. HyperFrames 0.8.225 still pins Chrome Headless Shell 152.0.7977.30, which the supply installs at the pinned digest, and all 639 Python and 63 Node tests pass.
- [x] 2.2 Check the narration's calls into the speech engine against the installed 0.6.3 source and bring them and their comments in line; done when the Python tests pass and the sample's Chinese cast narrates through the ICL generator. 0.6.3 keeps every call's signature and still floors a public ICL penalty at 1.5, so only two comments change; the Chinese cast's receipts record its 1.05 penalty, and its narration's unit error rate is at most 0.0159.

## 3. Acceptance and records

- [x] 3.1 Build the sample film with `mise run sample:supply` and `mise run sample:build`; done when `sample:verify` passes for both editions. The supply installed the browser and the three models at their pins, the geometry checks found nothing, both covers match the tracked ones, and `sample:verify` passes for both editions.
- [x] 3.2 State the new versions in `README.md` and `NOTICE`, and record the move under Unreleased in the Changelog with the note that the films keep v0.1.1 until they accept an edition on the new engine; done when `mise run check` passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publication waits for the user's approval of a public push of this repository.
