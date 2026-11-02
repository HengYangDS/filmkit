# Tasks

## 1. Review prompts

- [x] 1.1 Name an absent coda, inner pause cap or thought boundary ratio as not declared in the reviewer prompt context; done when a test builds the context from a voice performance without them and every `mise run check` command passes. `tests/review/test_round.py` builds the context from a Chinese performance without the three fields and reads "none declared" for each; on 2026-11-03 every check command passed, with 63 Node tests and 688 Python tests.

## 2. Supply

- [x] 2.1 Raise mlx-audio to 0.6.4 in `pyproject.toml` and refresh `uv.lock` with `uv lock --upgrade`; done when the lock resolves on the Python 3.12 line and OSV reports no advisory for any package it pins. The lock resolves 54 packages on CPython 3.12.16, moving only mlx-audio to 0.6.4 and filelock to 4.2.7, and OSV finds no issue.
- [x] 2.2 Raise `hyperframes` to 0.9.5 in `package.json`, refresh `package-lock.json` with `npm update --package-lock-only`, and set `RENDERER_VERSION` and the browser pin to what 0.9.5 declares; done when the supply installs that build at its pinned digest and OSV reports no advisory for any package the lock pins. The lock moves HyperFrames to 0.9.5 and semver to 7.8.6. HyperFrames 0.9.5 still declares Chrome Headless Shell 152.0.7977.30 and pins undici 7.25.0, so the browser pin and the undici 7.30.1 override stay; `sample:supply` installed that build and OSV finds no issue.
- [x] 2.3 Build the sample film with `mise run sample:build` on the refreshed locks; done when `sample:verify` passes for both editions. On 2026-11-03 both editions passed, each with 1,800 geometry frames drawn by HeadlessChrome/152.0.7977.30 and a soundtrack at −16.5 LUFS.

## 3. Documentation and release notes

- [ ] 3.1 Document the speech engine's decode defect, its upstream fix and how auditions and run-on retakes keep endings whole meanwhile, and bring the comments and notices that name the engine and renderer versions up to date; done when `README.md` and `NOTICE` name the new versions.
- [ ] 3.2 Record the changes under `Unreleased`, then date the notes as `[0.5.0]` with the `v0.4.0...v0.5.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.5.0; done when no tracked file outside the Changelog history names 0.4.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.5.0`, the tag's publication and the source-only Release pages.
