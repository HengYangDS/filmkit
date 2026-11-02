# Tasks

## 1. Runtime

- [x] 1.1 Replace the 0.2.0-alpha.25 declaration in `.config/mise/config.toml` with the one published with 0.2.0-alpha.26 and lock it again with native `mise lock`; done when the declaration equals the published one and the lock holds 0.2.0-alpha.26 at the declared checksums for each platform it records, with no 0.2.0-alpha.25 entry left. Each platform checksum equals `SHA256SUMS` and the GitHub asset digest.
- [x] 1.2 Bind the repository family to the 0.2.0-alpha.26 runtime with the locked console's `hook install`, keeping 0.2.0-alpha.25 as the rollback; done when `ethos status` reports the lane under the 0.2.0-alpha.26 runtime. CURRENT is `6e38309cd558` and ROLLBACK `d69329d72608`.
- [x] 1.3 Regenerate the CI projection with `ethos lane project`; done when the projection check conforms and only the Mise action pin moves. The patch changes one line: `jdx/mise-action` `6be3c7ed` to `6612f0ef` (v5.2.5).
- [x] 1.4 Record the move under Unreleased in the Changelog; done when every `mise run check` command passes. `mise run check` passes 63 Node and 687 Python tests and the Markdown format check.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publish dev and main to GitHub and GitLab, and confirm that the pushes start GitHub runs on their own.
