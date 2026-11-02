# Tasks

## 1. Review prompts

- [ ] 1.1 Name an absent coda, inner pause cap or thought boundary ratio as not declared in the reviewer prompt context; done when a test builds the context from a voice performance without them and every `mise run check` command passes.

## 2. Supply

- [ ] 2.1 Raise mlx-audio to 0.6.4 in `pyproject.toml` and refresh `uv.lock` with `uv lock --upgrade`; done when the lock resolves on the Python 3.12 line and OSV reports no advisory for any package it pins.
- [ ] 2.2 Raise `hyperframes` to 0.9.5 in `package.json`, refresh `package-lock.json` with `npm update --package-lock-only`, and set `RENDERER_VERSION` and the browser pin to what 0.9.5 declares; done when the supply installs that build at its pinned digest and OSV reports no advisory for any package the lock pins.
- [ ] 2.3 Build the sample film with `mise run sample:build` on the refreshed locks; done when `sample:verify` passes for both editions.

## 3. Documentation and release notes

- [ ] 3.1 Document the speech engine's decode defect, its upstream fix and how auditions and run-on retakes keep endings whole meanwhile, and bring the comments and notices that name the engine and renderer versions up to date; done when `README.md` and `NOTICE` name the new versions.
- [ ] 3.2 Record the changes under `Unreleased`, then date the notes as `[0.5.0]` with the `v0.4.0...v0.5.0` history link and open an empty `Unreleased`; set `VERSION` and the README pin to 0.5.0; done when no tracked file outside the Changelog history names 0.4.0 as the current version and every `mise run check` command passes.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Release follow-up: dev and main pass both peers' CI at the release head; then `ethos land --release --tag v0.5.0`, the tag's publication and the source-only Release pages.
