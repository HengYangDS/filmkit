# Tasks

## 1. Repository entry

- [ ] 1.1 Name the GitLab peer's new address in `.ethos/release.toml`; verify that `ethos status` reports the publication topology valid and that the address answers `git ls-remote`.
- [ ] 1.2 Link the README and NOTICE to the renamed DDWG film repository; verify that no current entry document names the old address.
- [ ] 1.3 Add `CONTRIBUTING.md`, include it in the Markdown formatter's inputs in `package.json` and point the README's development section to it; verify that `mise run check` passes and that ETHOS reports no undeclared command in it.
- [ ] 1.4 Record the guide under Unreleased in the Changelog; verify the Changelog structure that `ethos status` reports.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publication waits for the user's approval of the next release.
