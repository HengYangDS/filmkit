# Tasks

## 1. Runtime

- [x] 1.1 Replace the 0.2.0-alpha.27 declaration in `.config/mise/config.toml` with the one published with 0.2.0-alpha.28 and lock it again with native `mise lock`; done when the declaration equals the published one and the lock holds 0.2.0-alpha.28 at the declared checksums for each platform it records, with no 0.2.0-alpha.27 entry left. Each platform checksum equals `SHA256SUMS` and the GitHub asset digest, and the lock holds no 0.2.0-alpha.27 entry.
- [x] 1.2 Bind the repository family to the 0.2.0-alpha.28 runtime with the locked console's `hook install`, keeping 0.2.0-alpha.27 as the rollback; done when `ethos status` reports the lane under the 0.2.0-alpha.28 runtime. CURRENT is `2c6bca37d1db` and ROLLBACK `f5b664cb799b`.
- [x] 1.3 Regenerate the CI projection from the common model; done when `ethos lane project --check --json` reports it conforming, with no change expected. The preview reports `conforming` with no patch.
- [x] 1.4 Record the move under Unreleased in the Changelog; done when every `mise run check` command passes. `mise run check` passes 63 Node and 687 Python tests and the Markdown format check.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publish dev and main to GitHub and GitLab, and confirm that the pushes start GitHub runs on their own.
