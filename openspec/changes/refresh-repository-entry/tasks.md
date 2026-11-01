# Tasks

## 1. Repository entry

- [x] 1.1 Name the GitLab peer's new address in `.ethos/release.toml`; verify that `ethos status` reports the publication topology valid and that the address answers `git ls-remote`. ETHOS's publication topology of the lane is ready with no gap, and `http://192.168.64.101:18086/dig/misc/tools/films/filmkit.git` answers `git ls-remote` with six refs.
- [x] 1.2 Link the README and NOTICE to the renamed DDWG film repository; verify that no current entry document names the old address. Only the released 0.1.0 entry still names `ddwg-film`, as the design keeps it.
- [x] 1.3 Add `CONTRIBUTING.md`, include it in the Markdown formatter's inputs in `package.json` and point the README's development section to it; verify that `mise run check` passes and that ETHOS reports no undeclared command in it. `mise run check` passes 63 Node and 639 Python tests and the Markdown check, which now includes the guide, and `ethos status` reports the committed lane ready with no gap.
- [x] 1.4 Record the guide under Unreleased in the Changelog; verify the Changelog structure that `ethos status` reports. `ethos status` reports no Changelog gap.

## Workflow follow-up

- Archive the Change, prove the archived head once, land it and close out.
- Publication waits for the user's approval of the next release.
