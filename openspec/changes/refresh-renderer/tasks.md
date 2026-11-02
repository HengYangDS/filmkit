# Tasks

## 1. Renderer

- [x] 1.1 Raise `hyperframes` to 0.9.3 in `package.json` and lock it with `npm install --package-lock-only`, keeping the `undici` override; done when the lock holds 0.9.3 and OSV reports no advisory for any package it pins. The lock holds 0.9.3 and moves no other package, and OSV reports no advisory in its 127 packages or in the 53 of `uv.lock`.
- [x] 1.2 Set `RENDERER_VERSION` to 0.9.3 and the browser pin to the build 0.9.3 declares; done when the supply installs that build at its pinned digest and every `mise run check` command passes. 0.9.3 still declares Chrome Headless Shell 152.0.7977.30, so the browser pin stays and the supply installed that build at its pinned digest. `mise run check` passes 63 Node and 687 Python tests, after the two tests that named the old pin moved to read `RENDERER_VERSION`.

## 2. Acceptance and records

- [x] 2.1 Build the sample film with `mise run sample:supply` and `mise run sample:build`; done when `sample:verify` passes for both editions. The supply installed the browser and the three models at their pins, the geometry checks found nothing over 1,800 frames in each edition, both covers match the tracked ones, and `sample:verify` passes for both editions.
- [x] 2.2 State the new version in `README.md` and `NOTICE`, and record the move under Unreleased in the Changelog; done when `mise run check` passes. `mise run check` passes, and the Markdown format check with it.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publish dev and main to GitHub and GitLab, and confirm that the pushes start GitHub runs on their own.
