## 1. Runtime

- [x] 1.1 Replace the 0.2.0-beta.10 declaration in `.config/mise/config.toml` with the one published
      with 0.2.0-beta.11, checked against the release's `SHA256SUMS` and asset digests, and lock it
      again with native `mise lock`; done when the lock holds 0.2.0-beta.11 for every platform it
      held 0.2.0-beta.10 for, no 0.2.0-beta.10 entry remains and it keeps `lockfile_version = 3`.
      The release's declaration (sha256 `af619718…`) replaced the table and its comment; `mise lock`
      kept `lockfile_version = 3`, changed only `http:ethos`, and holds 0.2.0-beta.11 for the same
      platform entries, each checksum equal to `SHA256SUMS`.
- [x] 1.2 Bind the repository family to the 0.2.0-beta.11 runtime with the locked console's
      `hook install`, keeping 0.2.0-beta.10 as the rollback; done when `ethos status` reports the
      lane ready under the 0.2.0-beta.11 runtime. CURRENT names the 0.2.0-beta.11 runtime
      `8c663b10…` and ROLLBACK the 0.2.0-beta.10 runtime `526c2eba…`; with this Change named,
      `ethos status` reports the lane ready.
- [x] 1.3 Regenerate both pipelines from the 0.2.0-beta.11 common model with
      `ethos lane project --apply` after the bind, since no proof or commit refuses the old files;
      done when `ethos lane project --check --json` reports both projections conforming and the
      change adds only the 14-day retention lines. The check first reported
      `generated_projection_drift` for both pipelines; the applied preview added one
      `retention-days: 14` line to the GitHub workflow and two `expire_in: 14 days` lines to the
      GitLab pipeline, and the check now reports both conforming.
- [x] 1.4 Record the move under Changed in the Changelog; done when the repository check passes. The
      Unreleased section records the move under Changed; the check's commands, run one at a time
      (235 Node tests, 2,085 Python tests, the Markdown check), pass.

## 2. Release

- [x] 2.1 Prepare 0.26.1 in `VERSION`, the Changelog and the README's install line, after the lane's
      other Changes are committed; done when `VERSION` reads 0.26.1, the Changelog has the dated
      0.26.1 section holding the lane's moves, the README's install line names `v0.26.1`, and the
      repository check passes. `VERSION` reads 0.26.1, the Changelog has the dated 0.26.1 section
      with the lane's moves (ETHOS 0.2.0-beta.11, Mise 2026.11.10, the 14-day retention) and its
      compare link, and the README's install line names `v0.26.1`; after `mise run bootstrap`, the
      check's commands, run one at a time, pass: 235 Node tests and 2,085 Python tests.

## Workflow follow-up

- Archive this Change and prove the archived head once.
- Publish the proposal, wait for both forges' review jobs, land, publish `dev` and `main`, and read
  the protected jobs back; then retire the lane.
