## 1. Runtime

- [ ] 1.1 Replace the 0.2.0-beta.10 declaration in `.config/mise/config.toml` with the one published
      with 0.2.0-beta.11, checked against the release's `SHA256SUMS` and asset digests, and lock it
      again with native `mise lock`; done when the lock holds 0.2.0-beta.11 for every platform it
      held 0.2.0-beta.10 for, no 0.2.0-beta.10 entry remains and it keeps `lockfile_version = 3`.
- [ ] 1.2 Bind the repository family to the 0.2.0-beta.11 runtime with the locked console's
      `hook install`, keeping 0.2.0-beta.10 as the rollback; done when `ethos status` reports the
      lane ready under the 0.2.0-beta.11 runtime.
- [ ] 1.3 Regenerate both pipelines from the 0.2.0-beta.11 common model with
      `ethos lane project --apply` after the bind, since no proof or commit refuses the old files;
      done when `ethos lane project --check --json` reports both projections conforming and the
      change adds only the 14-day retention lines.
- [ ] 1.4 Record the move under Changed in the Changelog; done when the repository check passes.

## 2. Release

- [ ] 2.1 Prepare 0.26.1 in `VERSION`, the Changelog and the README's install line, after the lane's
      other Changes are committed; done when `VERSION` reads 0.26.1, the Changelog has the dated
      0.26.1 section holding the lane's moves, the README's install line names `v0.26.1`, and the
      repository check passes.

## Workflow follow-up

- Archive this Change and prove the archived head once.
- Publish the proposal, wait for both forges' review jobs, land, publish `dev` and `main`, and read
  the protected jobs back; then retire the lane.
