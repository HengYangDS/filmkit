## 1. Supply

- [x] 1.1 Declare `minimum_release_age = "0h"` under `[settings]` in `.config/mise/config.toml`;
      done when `mise settings get minimum_release_age` reports `0h` in the repository.
      `mise settings get minimum_release_age` reports `0h` in the lane.
- [x] 1.2 Declare uv 0.13.8 and lock it again with `mise lock`; done when only uv's entries change,
      `lockfile_version = 3` holds and `mise install --locked uv` installs 0.13.8. The lock changed
      only uv's entries, for the same six platforms, and kept `lockfile_version = 3`;
      `mise install --locked uv` installed 0.13.8.
- [x] 1.3 Move the exact pins to coverage 7.17.3 and Prettier 3.10.1 and the npm lock to the latest
      stable releases, keeping transformers at 5.22.2; done when `mise run check:dependencies`,
      `mise run check` and `npm ls --all --include=dev` pass and OSV reports no advisory in either
      lock. coverage 7.17.3 is the uv lock's only move, 1 of 54, and transformers stays at 5.22.2;
      at cutoff 2026-11-13T15:52:43Z the npm lock moved exactly @hono/node-server 2.1.8, Prettier
      3.10.1 and ws 8.23.0, 3 of 129; OSV reports no advisory in either lock;
      `npm ls --all --include=dev` reports no problem; `mise run bootstrap` with its
      `check:dependencies` and `mise run check` pass: 175 Node tests, the Markdown check with
      Prettier 3.10.1 reformatting nothing, and 1,102 Python tests.

## 2. Release

- [ ] 2.1 Prepare 0.21.3 in `VERSION`, the Changelog and the README's install line; done when the
      repository check passes.

## Deferred

- transformers 5.23.0, with mlx-audio 0.6.5 and the picture supply. Owner: the film session. Next
  action: move them in filmkit 0.22.0 and accept them by comparing the sample film's takes and
  frames before and after. Review date: 2026-11-16.

## Workflow follow-up

- Archive the lane's Changes and prove the archived head once.
- Publish the proposal, wait for GitHub's and GitLab's macOS review jobs, land and publish `dev` and
  `main`, and observe GitLab's protected macOS job.
- Tag v0.21.3 through `ethos land --release`, publish the tag and the two Releases, read them back,
  and retire the lane.
