## 1. Runtime

- [x] 1.1 Replace the 0.2.0-alpha.29 declaration in `.config/mise/config.toml` with the one
      published with 0.2.0-beta.8, checked against the release's `SHA256SUMS` and asset digests,
      and lock it again with native `mise lock`; done when the lock holds 0.2.0-beta.8 for every
      platform it held 0.2.0-alpha.29 for and no 0.2.0-alpha.29 entry remains. The release read back
      with all five platforms; the lock holds 0.2.0-beta.8 for the same six platform entries, keeps
      `lockfile_version = 3` and has no 0.2.0-alpha.29 entry.
- [x] 1.2 Bind the repository family to the 0.2.0-beta.8 runtime with the locked console's
      `hook install`, keeping 0.2.0-alpha.29 as the rollback; done when the manifest of `CURRENT`
      names 0.2.0-beta.8 and that of `ROLLBACK` 0.2.0-alpha.29. `CURRENT` names 0.2.0-beta.8 with
      source commit `9bf5bdda7`, and `ROLLBACK` 0.2.0-alpha.29.
- [x] 1.3 Remove the retired declaration fields with `ethos lane repair-paradigm --apply`; done when
      `.ethos/release.toml` names neither `forge_repository` nor a local command, the repair reports
      `conforming` and `ethos status` reports the lane ready under the 0.2.0-beta.8 runtime. The
      repair removed six lines: `forge_repository` in both peers, both local commands, the emptied
      `[publication]` header and a blank line; its next preview reports `conforming`.
- [x] 1.4 Generate the pipelines again from the 0.2.0-beta.8 common model; done when
      `ethos lane project --check --json` reports both projections conforming. The regenerated
      GitHub workflow moves only `jdx/mise-action` to v5.2.7 (`b44d12e7`); the check reports
      `conforming`.
- [x] 1.5 Record the move under Changed in the Changelog; done when the repository check passes.
      The Changed bullet names 0.2.0-beta.8 and `jdx/mise-action` 5.2.7.
