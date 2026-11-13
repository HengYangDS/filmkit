## 1. Node

- [x] 1.1 Declare node 26.13.1 in `.config/mise/config.toml` and lock it again with `mise lock`;
      done when the lock changes only node's entries for the same platforms with checksums equal to
      Node's `SHASUMS256.txt`, keeps `lockfile_version = 3`, and `mise run check` passes. The lock
      changed only node's entries for the same six platforms; four checksums equal Node's
      `SHASUMS256.txt` and the two musl builds equal the unofficial-builds sums;
      `lockfile_version = 3` held. `mise run check` passes on v26.13.1: 175 Node tests, the Markdown
      check and 1,102 Python tests.
- [x] 1.2 Build the sample film on Node 26.13.1; done when `mise run sample:build` passes.
      `mise run sample:build` passed from 09:46:40 to 09:56:51: both editions pass check-picture
      over 1,801 frames with no findings and verify.

## 2. Release

- [x] 2.1 Prepare 0.21.2 in `VERSION`, the Changelog and the README's install line; done when the
      repository check passes. `mise run check` passes with the release edits: 175 Node tests, the
      Markdown check and 1,102 Python tests, from 09:57:55 to 09:59:08.

## Workflow follow-up

- Archive this Change and prove the archived head once.
- Publish the proposal, wait for GitHub's and GitLab's macOS review jobs, land and publish `dev` and
  `main`, and observe GitLab's protected macOS job.
- Tag v0.21.2 through `ethos land --release`, publish the tag and the two Releases, and retire the
  lane.
