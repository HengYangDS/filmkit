## 1. Runtime

- [x] 1.1 Replace the 0.2.0-beta.8 declaration in `.config/mise/config.toml` with the one published
      with 0.2.0-beta.9, checked against the release's `SHA256SUMS` and asset digests, and lock it
      again with native `mise lock`; done when the lock holds 0.2.0-beta.9 for every platform it
      held 0.2.0-beta.8 for, no 0.2.0-beta.8 entry remains and it keeps `lockfile_version = 3`. The
      release read back with all five platforms. The lock holds 0.2.0-beta.9 for each of the six
      ETHOS platform entries that held 0.2.0-beta.8, keeps its node, python and uv entries unchanged
      and `lockfile_version = 3`, and has no 0.2.0-beta.8 entry.
- [x] 1.2 Bind the repository family to the 0.2.0-beta.9 runtime with the locked console's
      `hook install`, keeping 0.2.0-beta.8 as the rollback; done when `ethos status` reports the
      lane ready under the 0.2.0-beta.9 runtime. `CURRENT` is the 0.2.0-beta.9 runtime
      `9427601ab2b1`, whose console reports source commit `999784081` and OpenSpec 2.0.0, and
      `ROLLBACK` the 0.2.0-beta.8 runtime `5f0288e2c1d0`; status after the bind passes, dirty only
      by the lane's edits.
- [x] 1.3 Check both pipelines against the 0.2.0-beta.9 common model; done when
      `ethos lane project --check --json` reports both projections conforming. The check reports
      `conforming` under 0.2.0-beta.9, so neither pipeline changes.
- [x] 1.4 Record the move under Changed in the Changelog; done when the repository check passes. The
      Changed bullet names 0.2.0-beta.9, and the format, project, Markdown lint, prose, OpenSpec,
      configuration and registry checks pass.
