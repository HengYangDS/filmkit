# Tasks

## 1. Declarations and locks

- [ ] 1.1 Raise HyperFrames to 0.8.225, puppeteer-core to 25.16.0 and @puppeteer/browsers to 3.2.6 in `package.json`, override `undici` to its latest fixed 7.x release, and lock them with `npm install --package-lock-only`; done when the lock holds those versions and OSV reports no advisory for any package it pins.
- [ ] 1.2 Raise mlx-audio, Pydantic, hatchling, coverage and pytest to their latest stable releases in `pyproject.toml` and refresh `uv.lock` with `uv lock --upgrade`; done when the lock resolves on the Python 3.12 line and OSV reports no advisory for any package it pins.
- [ ] 1.3 Raise Node and uv in `.config/mise/config.toml` and Mise in `.config/ci/verification.toml`, lock with native `mise lock`, and regenerate the CI projection; done when the lock holds the new versions and the projection check conforms.

## 2. Engine pins

- [ ] 2.1 Set `RENDERER_VERSION` in `src/filmkit/picture/rendering.py` to the renderer installed, and `BROWSER` and `BROWSER_SHA256` to the browser build it pins; done when the supply installs that build at that digest and the tests pass.
- [ ] 2.2 Check the narration's calls into the speech engine against the installed 0.6.3 source and bring them and their comments in line; done when the Python tests pass and the sample's Chinese cast narrates through the ICL generator.

## 3. Acceptance and records

- [ ] 3.1 Build the sample film with `mise run sample:supply` and `mise run sample:build`; done when `sample:verify` passes for both editions.
- [ ] 3.2 State the new versions in `README.md` and `NOTICE`, and record the move under Unreleased in the Changelog with the note that the films keep v0.1.1 until they accept an edition on the new engine; done when `mise run check` passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publication waits for the user's approval of a public push of this repository.
