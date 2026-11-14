## 1. Runtime

- [x] 1.1 Replace the 0.2.0-beta.9 declaration in `.config/mise/config.toml` with the one published
      with 0.2.0-beta.10, checked against the release's `SHA256SUMS` and asset digests, and lock it
      again with native `mise lock`; done when the lock holds 0.2.0-beta.10 for every platform it
      held 0.2.0-beta.9 for, no 0.2.0-beta.9 entry remains and it keeps `lockfile_version = 3`. The
      declaration is the release's own file (`sha256:2163ceaa…`), read back against `SHA256SUMS` and
      the five asset digests; the lock holds 0.2.0-beta.10 for every platform it held 0.2.0-beta.9
      for, no 0.2.0-beta.9 entry remains and `lockfile_version = 3` holds.
- [x] 1.2 Bind the repository family to the 0.2.0-beta.10 runtime with the locked console's
      `hook install`, keeping 0.2.0-beta.9 as the rollback; done when `ethos status` reports the
      lane ready under the 0.2.0-beta.10 runtime. CURRENT names the 0.2.0-beta.10 runtime
      `526c2ebafeba` and ROLLBACK the 0.2.0-beta.9 runtime `9427601ab2b1`; with this Change named,
      `ethos status` reports pass in the lane.
- [x] 1.3 Check both pipelines against the 0.2.0-beta.10 common model; done when
      `ethos lane project --check --json` reports both projections conforming. Under the
      0.2.0-beta.10 runtime `ethos lane project --check --json` reports both projections conforming.
- [x] 1.4 Record the move under Changed in the Changelog; done when the repository check passes. The
      Changelog's 0.21.3 section, which the release Change of this lane writes, names the move; the
      repository check passes.

## 2. Hosted Mise

- [x] 2.1 Move `[supply] mise_version` to Mise 2026.11.8 and generate the pipelines again; done when
      `ethos lane project --check --json` reports both projections conforming. One occurrence moved
      in `.config/ci/verification.toml`, the GitHub workflow came from `ethos lane project --apply`,
      and the check reports both projections conforming.
