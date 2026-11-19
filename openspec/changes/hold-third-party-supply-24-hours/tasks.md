## 1. The declarations

- [ ] 1.1 Declare `minimum_release_age = "24h"` in `.config/mise/config.toml` and `min-release-age=1` in `.config/npm/npmrc`; verify under Mise that each reader states the new age and that `mise install --locked` and `mise run bootstrap` pass.
- [ ] 1.2 Declare `exclude-newer = "24 hours"` under `[tool.uv]` in `pyproject.toml` and write the uv lock again in the same commit; verify that the lock holds the packages and artifacts it held before, and that `uv lock --check --offline` and `mise run check:dependencies` pass.
- [ ] 1.3 State the age and uv's line in the Changelog; verify the repository's Markdown check.

## 2. Verification

- [ ] 2.1 Run every command of the repository's check on the lane, the whole suite as the child of a host ticket; verify that each passes.
